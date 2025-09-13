from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional, Dict, Any
from app.core.database import get_session
from app.schemas.event import ETLStatus
from app.utils.batch_processing import batch_processor
from app.services.predicthq import predicthq_service
from app.services.similarity import similarity_service
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/etl", tags=["ETL"])

# Store ETL status (in production, use Redis or database)
etl_status_store: Dict[str, Dict[str, Any]] = {}


@router.post("/trigger", response_model=ETLStatus)
async def trigger_etl(
    background_tasks: BackgroundTasks,
    session: AsyncSession = Depends(get_session),
    max_events: int = Query(1000, description="Maximum number of events to fetch"),
    category: Optional[str] = Query(None, description="Filter by category"),
    location: Optional[str] = Query(None, description="Filter by location"),
    start_date: Optional[str] = Query(None, description="Filter by start date (ISO format)"),
    end_date: Optional[str] = Query(None, description="Filter by end date (ISO format)"),
    calculate_similarities: bool = Query(True, description="Calculate event similarities after ETL")
) -> ETLStatus:
    """Trigger ETL process to fetch and process events from PredictHQ"""
    
    import uuid
    job_id = str(uuid.uuid4())
    
    # Initialize job status
    etl_status_store[job_id] = {
        "status": "running",
        "message": "ETL process started",
        "events_processed": 0,
        "events_created": 0,
        "events_updated": 0,
        "processing_time": None,
        "job_id": job_id
    }
    
    # Prepare filters
    filters = {}
    if category:
        filters["category"] = category
    if location:
        filters["location"] = location
    if start_date:
        filters["start_date"] = start_date
    if end_date:
        filters["end_date"] = end_date
    
    # Add background task
    try:
        background_tasks.add_task(
            run_etl_pipeline,
            job_id,
            max_events,
            calculate_similarities,
            filters
        )
        return ETLStatus(
            status="running",
            message=f"ETL process started with job ID: {job_id}",
            events_processed=0,
            events_created=0,
            events_updated=0
        )
    except Exception as e:
        logger.error(f"Failed to start ETL background task: {e}")
        etl_status_store[job_id].update({
            "status": "error",
            "message": f"Failed to start ETL process: {str(e)}"
        })
        raise HTTPException(status_code=500, detail=f"Failed to start ETL process: {str(e)}")


@router.get("/status/{job_id}", response_model=ETLStatus)
async def get_etl_status(job_id: str) -> ETLStatus:
    """Get ETL job status"""
    
    if job_id not in etl_status_store:
        raise HTTPException(status_code=404, detail="ETL job not found")
    
    job_status = etl_status_store[job_id]
    return ETLStatus(**job_status)


@router.get("/test-connection")
async def test_predicthq_connection():
    """Test connection to PredictHQ API"""
    
    try:
        success = await predicthq_service.test_connection()
        if success:
            return {"status": "success", "message": "Connected to PredictHQ API successfully"}
        else:
            return {"status": "error", "message": "Failed to connect to PredictHQ API"}
    except Exception as e:
        logger.error(f"PredictHQ connection test error: {e}")
        raise HTTPException(status_code=500, detail=f"Connection test failed: {str(e)}")


@router.post("/calculate-similarities")
async def calculate_similarities(
    background_tasks: BackgroundTasks,
    session: AsyncSession = Depends(get_session),
    event_ids: Optional[list] = None,
    batch_size: int = Query(100, description="Batch size for similarity calculations")
):
    """Calculate and store similarities between events"""
    
    import uuid
    job_id = str(uuid.uuid4())
    
    etl_status_store[job_id] = {
        "status": "running",
        "message": "Calculating event similarities",
        "events_processed": 0,
        "processing_time": None,
        "job_id": job_id
    }
    
    background_tasks.add_task(
        calculate_similarities_task,
        job_id,
        event_ids,
        batch_size
    )
    
    return {
        "status": "running",
        "message": f"Similarity calculation started with job ID: {job_id}",
        "job_id": job_id
    }


async def run_etl_pipeline(
    job_id: str,
    max_events: int,
    calculate_similarities: bool,
    filters: Dict[str, Any]
):
    """Background task to run the complete ETL pipeline"""
    
    try:
        from app.core.database import AsyncSessionLocal
        
        def update_status(stage: str, data: Dict[str, Any]):
            """Update job status"""
            etl_status_store[job_id].update({
                "message": data.get("message", stage),
                "events_processed": data.get("processed", 0),
            })
        
        # Run ETL process
        async with AsyncSessionLocal() as session:
            result = await batch_processor.fetch_and_process_events(
                session=session,
                max_events=max_events,
                progress_callback=update_status,
                **filters
            )
            
            # Update final status
            etl_status_store[job_id].update({
                "status": result["status"],
                "message": result["message"],
                "events_processed": result["events_processed"],
                "events_created": result["events_created"],
                "events_updated": result["events_updated"],
                "processing_time": result["processing_time"]
            })
            
            # Calculate similarities if requested
            '''
            if calculate_similarities and result["status"] == "completed":
                etl_status_store[job_id]["message"] = "Calculating event similarities..."
                
                # Get all event IDs
                from sqlalchemy import select
                from app.models.event import Event
                
                query = select(Event.id).where(Event.embeddings.is_not(None))
                result = await session.execute(query)
                event_ids = [row[0] for row in result.all()]
                
                if event_ids:
                    similarities_count = await similarity_service.calculate_and_store_similarities(
                        session, event_ids[:500]  # Limit for performance
                    )
                    etl_status_store[job_id]["message"] = f"ETL completed. Calculated {similarities_count} similarities."
            '''
    except Exception as e:
        logger.error(f"ETL pipeline error for job {job_id}: {e}")
        etl_status_store[job_id].update({
            "status": "error",
            "message": f"ETL failed: {str(e)}"
        })


async def calculate_similarities_task(
    job_id: str,
    event_ids: Optional[list],
    batch_size: int
):
    """Background task to calculate similarities"""
    
    try:
        from app.core.database import AsyncSessionLocal
        from sqlalchemy import select
        from app.models.event import Event
        
        async with AsyncSessionLocal() as session:
            # Get event IDs if not provided
            if not event_ids:
                query = select(Event.id).where(Event.embeddings.is_not(None))
                result = await session.execute(query)
                event_ids = [row[0] for row in result.all()]
            
            if not event_ids:
                etl_status_store[job_id].update({
                    "status": "completed",
                    "message": "No events with embeddings found",
                    "events_processed": 0
                })
                return
            
            # Calculate similarities
            similarities_count = await similarity_service.calculate_and_store_similarities(
                session, event_ids, batch_size
            )
            
            etl_status_store[job_id].update({
                "status": "completed",
                "message": f"Calculated {similarities_count} similarities for {len(event_ids)} events",
                "events_processed": len(event_ids)
            })
    
    except Exception as e:
        logger.error(f"Similarity calculation error for job {job_id}: {e}")
        etl_status_store[job_id].update({
            "status": "error",
            "message": f"Similarity calculation failed: {str(e)}"
        })
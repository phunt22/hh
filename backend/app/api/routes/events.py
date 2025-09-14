import base64
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from typing import Any, Dict, List, Optional
from app.core.database import get_session
from app.models.event import Event
from app.schemas.event import (
    BusiestCity,
    EventResponse, 
    SimilaritySearchRequest, 
    SimilaritySearchResponse,
    EventCreate,
    EventUpdate
)
from app.services.similarity import similarity_service
from app.services.embedding import embedding_service
import logging
from app.services.events_cache import events_cache_service
from app.services.enhanced_similarity import enhanced_similarity_service
import json

from app.services.tts_service import tts_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/events", tags=["Events"])


@router.get("/", response_model=List[EventResponse])
async def get_events(
    session: AsyncSession = Depends(get_session),
    skip: int = Query(0, ge=0, description="Number of events to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Number of events to return"),
    category: Optional[str] = Query(None, description="Filter by category"),
    location_query: Optional[str] = Query(None, description="Search in location field")
) -> List[EventResponse]:
    """Get events with optional filtering"""
    
    return await events_cache_service.get_cached_events_with_fallback(
        session=session,
        skip=skip,
        limit=limit,
        category=category,
        location_query=location_query
    )

@router.post("/search/similar", response_model=SimilaritySearchResponse)
async def search_similar_events(
    request: SimilaritySearchRequest,
    session: AsyncSession = Depends(get_session)
) -> SimilaritySearchResponse:
    """Search for similar events using text query or event ID"""
    
    logger.info(f"=== SEARCH REQUEST START ===")
    logger.info(f"Request data: {request}")
    logger.info(f"Query text: {request.query_text}")
    logger.info(f"Event ID: {request.event_id}")
    
    if not request.query_text and not request.event_id:
        logger.error("No query_text or event_id provided")
        raise HTTPException(
            status_code=400, 
            detail="Either query_text or event_id must be provided"
        )
    
    try:
        # Force limit to 5 for similarity search
        similarity_limit = 5
        logger.info(f"Using similarity limit: {similarity_limit}")
        
        if request.event_id:
            logger.info("Searching by event ID...")
            # Search by event ID using embeddings
            similar_events = await enhanced_similarity_service.find_similar_events_by_id(
                event_id=request.event_id,
                limit=similarity_limit,
            )
            
            # Get the source event for response
            logger.info("Getting source event...")
            source_event_query = select(Event).where(Event.id == request.event_id)
            source_result = await session.execute(source_event_query)
            source_event = source_result.scalar_one_or_none()
            query_event = EventResponse.from_orm(source_event) if source_event else None
            
        else:
            logger.info(f"Searching by text: '{request.query_text}'")
            
            # Search by text query using embeddings
            try:
                logger.info("Calling enhanced similarity service...")
                similar_events = await enhanced_similarity_service.find_similar_events(
                    query_text=request.query_text,
                    limit=similarity_limit,
                )
                logger.info(f"Similarity search returned {len(similar_events)} results")
            except Exception as similarity_error:
                logger.error(f"Similarity search failed: {similarity_error}")
                raise HTTPException(status_code=500, detail=f"Similarity search failed: {str(similarity_error)}")
            
            query_event = None
    
        
        logger.info(f"Successfully converted {len(similar_events)} events")
        
        audio_string = tts_service.explain_search(similar_events)

        response = SimilaritySearchResponse(
            query_event=query_event,
            similar_events=similar_events,
            total_found=len(similar_events),
            audio_response=audio_string,
        )
        
        logger.info(f"=== SEARCH REQUEST SUCCESS ===")
        return response
    
    except HTTPException:
        # Re-raise HTTP exceptions (these are handled properly)
        raise
    except Exception as e:
        logger.error(f"=== SEARCH REQUEST FAILED ===")
        logger.error(f"Unexpected error in similarity search: {e}")
        logger.error(f"Error type: {type(e).__name__}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Error performing similarity search: {str(e)}")


@router.get("/busiest-cities", response_model=List[BusiestCity])
async def get_busiest_cities(
    session: AsyncSession = Depends(get_session),
    time_window_days: int = Query(7, ge=1, description="Number of days to consider for busyness"),
    limit: int = Query(10, ge=1, le=50, description="Number of busiest cities to return")
) -> List[Dict[str, Any]]:
    """
    Get the top N busiest cities in the world based on event attendance
    within a specified time window. Results are cached for 1 hour.
    """
    try:
        return await events_cache_service.get_busiest_cities(
            session=session,
            time_window_days=time_window_days,
            limit=limit
        )
    except Exception as e:
        logger.error(f"Error getting busiest cities: {e}")
        raise HTTPException(status_code=500, detail="Error getting busiest cities")



@router.get("/{event_id}/similar", response_model=SimilaritySearchResponse)
async def get_similar_events(
    event_id: str,
    session: AsyncSession = Depends(get_session),
    limit: int = Query(10, ge=1, le=100, description="Number of similar events to return"),
    min_similarity: float = Query(0.7, ge=0.0, le=1.0, description="Minimum similarity score"),
    include_related: bool = Query(True, description="Include explicitly related events")
) -> SimilaritySearchResponse:
    """Get events similar to a specific event"""
    
    try:
        # Use enhanced similarity service with embeddings
        similar_events_with_scores = await enhanced_similarity_service.find_similar_events_by_id(
            session=session,
            event_id=event_id,
            limit=min(limit, 5),  # Force max 5 results
            min_similarity=min_similarity
        )
        
        # Get the source event
        source_event_query = select(Event).where(Event.id == event_id)
        source_result = await session.execute(source_event_query)
        source_event = source_result.scalar_one_or_none()
        
        if not source_event:
            raise HTTPException(status_code=404, detail="Event not found")
        
        # Convert to response format
        from app.schemas.event import SimilarEvent
        similar_events = [
            SimilarEvent(
                event=EventResponse.from_orm(event),
                similarity_score=score,
                relationship_type="similar"
            )
            for event, score in similar_events_with_scores
        ]
        
        return SimilaritySearchResponse(
            query_event=EventResponse.from_orm(source_event),
            similar_events=similar_events,
            total_found=len(similar_events)
        )
    
    except Exception as e:
        logger.error(f"Error finding similar events for {event_id}: {e}")
        raise HTTPException(status_code=500, detail="Error finding similar events")
        

@router.get("/popular/daily")
async def get_popular_events_daily(
    session: AsyncSession = Depends(get_session),
    date: Optional[str] = Query(None, description="Date in YYYY-MM-DD format (defaults to today)")
) -> Dict[str, Any]:
    """Get top 10 most popular events for a specific day (cached for 1 hour)"""
    
    try:
        # Parse date if provided
        target_date = datetime.now(timezone.utc)
        if date:
            try:
                target_date = datetime.strptime(date, "%Y-%m-%d").replace(tzinfo=timezone.utc)
            except ValueError:
                raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD")
        
        # Get popular events (cached for 1 hour)
        popular_events = await events_cache_service.get_popular_events_for_day(
            session=session,
            date=target_date
        )

        return {
            "date": target_date.strftime("%Y-%m-%d"),
            "popular_events": popular_events,
            "total_events": len(popular_events),
            "cache_info": {
                "cached": True,
                "ttl_minutes": 60,
                "description": "Results cached for 1 hour"
            }
        }
        
    except Exception as e:
        logger.error(f"Error getting popular events: {e}")
        raise HTTPException(status_code=500, detail="Error getting popular events")


@router.get("/categories/list")
async def get_categories(
    session: AsyncSession = Depends(get_session)
) -> Dict[str, Any]:
    """Get list of all event categories with colors"""
    
    CATEGORY_COLORMAP = {
        "academic": "#4F46E5",           
        "school-holidays": "#F59E0B",    
        "public-holidays": "#EF4444",    
        "observances": "#8B5CF6",        
        "politics": "#DC2626",           
        "conferences": "#059669",        
        "expos": "#0891B2",              
        "concerts": "#EC4899",           
        "festivals": "#F97316",          
        "performing-arts": "#A855F7",    
        "sports": "#22C55E",             
        "community": "#06B6D4",          
        "daylight-savings": "#84CC16",   
        "airport-delays": "#6B7280",     
        "severe-weather": "#1F2937",     
        "disasters": "#B91C1C",          
        "health-warnings": "#DC2626"     
    }
    
    query = select(Event.category).distinct().where(Event.category.is_not(None))
    result = await session.execute(query)
    categories = [row[0] for row in result.all() if row[0]]
    
    categories_with_colors = []
    for category in sorted(categories):
        color = CATEGORY_COLORMAP.get(category, "#6B7280") ## gray for default
        categories_with_colors.append({
            "name": category,
            "color": color
        })
    
    return {
        "categories": categories,
        "colormap": CATEGORY_COLORMAP
    }


@router.get("/stats/summary")
async def get_events_summary(
    session: AsyncSession = Depends(get_session)
) -> dict:
    """Get summary statistics about events"""
    
    # Total events count
    total_query = select(func.count(Event.id))
    total_result = await session.execute(total_query)
    total_events = total_result.scalar()
    
    # Events with embeddings count
    embeddings_query = select(func.count(Event.id)).where(Event.embeddings.is_not(None))
    embeddings_result = await session.execute(embeddings_query)
    events_with_embeddings = embeddings_result.scalar()
    
    # Categories count
    categories_query = select(func.count(func.distinct(Event.category)))
    categories_result = await session.execute(categories_query)
    unique_categories = categories_result.scalar()
    
    # Events by category
    category_stats_query = (
        select(Event.category, func.count(Event.id))
        .group_by(Event.category)
        .order_by(func.count(Event.id).desc())
        .limit(10)
    )
    category_stats_result = await session.execute(category_stats_query)
    top_categories = [
        {"category": category, "count": count}
        for category, count in category_stats_result.all()
    ]
    
    return {
        "total_events": total_events,
        "events_with_embeddings": events_with_embeddings,
        "unique_categories": unique_categories,
        "top_categories": top_categories,
        "embedding_coverage": round(events_with_embeddings / total_events * 100, 2) if total_events > 0 else 0
    }


@router.post("/", response_model=EventResponse)
async def create_event(
    event: EventCreate,
    session: AsyncSession = Depends(get_session)
) -> EventResponse:
    """Create a new event (manual entry)"""
    
    # Check if event already exists
    existing_query = select(Event).where(Event.id == event.id)
    existing_result = await session.execute(existing_query)
    
    if existing_result.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Event with this ID already exists")
    
    try:
        # Generate embedding for the event
        text = embedding_service.prepare_event_text(event.title, event.description or "")
        embedding = await embedding_service.generate_embedding(text)
        
        # Create event
        db_event = Event(
            **event.dict(),
            embeddings=embedding
        )
        
        session.add(db_event)
        await session.commit()
        await session.refresh(db_event)
        
        return EventResponse.from_orm(db_event)
    
    except Exception as e:
        logger.error(f"Error creating event: {e}")
        await session.rollback()
        raise HTTPException(status_code=500, detail="Error creating event")

@router.get("/{event_id}", response_model=EventResponse)
async def get_event(
    event_id: str,
    session: AsyncSession = Depends(get_session)
) -> EventResponse:
    """Get a specific event by ID"""
    
    query = select(Event).where(Event.id == event_id)
    result = await session.execute(query)
    event = result.scalar_one_or_none()
    
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    
    return EventResponse.from_orm(event)

@router.put("/{event_id}", response_model=EventResponse)
async def update_event(
    event_id: str,
    event_update: EventUpdate,
    session: AsyncSession = Depends(get_session)
) -> EventResponse:
    """Update an existing event"""
    
    # Get existing event
    query = select(Event).where(Event.id == event_id)
    result = await session.execute(query)
    db_event = result.scalar_one_or_none()
    
    if not db_event:
        raise HTTPException(status_code=404, detail="Event not found")
    
    try:
        # Update fields
        update_data = event_update.dict(exclude_unset=True)
        
        # Check if title or description changed (need to regenerate embedding)
        needs_embedding_update = (
            'title' in update_data or 'description' in update_data
        )
        
        for field, value in update_data.items():
            setattr(db_event, field, value)
        
        # Regenerate embedding if needed
        if needs_embedding_update:
            text = embedding_service.prepare_event_text(
                db_event.title, db_event.description or ""
            )
            db_event.embeddings = await embedding_service.generate_embedding(text)
        
        # Update timestamp
        from datetime import datetime, timezone
        db_event.updated_at = datetime.now(timezone.utc)
        
        await session.commit()
        await session.refresh(db_event)
        
        return EventResponse.from_orm(db_event)
    
    except Exception as e:
        logger.error(f"Error updating event {event_id}: {e}")
        await session.rollback()
        raise HTTPException(status_code=500, detail="Error updating event")


@router.delete("/{event_id}")
async def delete_event(
    event_id: str,
    session: AsyncSession = Depends(get_session)
) -> dict:
    """Delete an event"""
    
    # Get existing event
    query = select(Event).where(Event.id == event_id)
    result = await session.execute(query)
    db_event = result.scalar_one_or_none()
    
    if not db_event:
        raise HTTPException(status_code=404, detail="Event not found")
    
    try:
        await session.delete(db_event)
        await session.commit()
        
        return {"message": f"Event {event_id} deleted successfully"}
    
    except Exception as e:
        logger.error(f"Error deleting event {event_id}: {e}")
        await session.rollback()
        raise HTTPException(status_code=500, detail="Error deleting event")

# to debuug
# Add these test endpoints to your router to debug the system

@router.get("/debug/test")
async def debug_test(session: AsyncSession = Depends(get_session)):
    """Test basic database connectivity and services"""
    
    results = {}
    
    # Test 1: Database connection
    try:
        query = select(func.count(Event.id))
        result = await session.execute(query)
        total_events = result.scalar()
        results["database"] = {"status": "ok", "total_events": total_events}
    except Exception as e:
        results["database"] = {"status": "error", "error": str(e)}
    
    # Test 2: Events with embeddings
    try:
        query = select(func.count(Event.id)).where(Event.embeddings.is_not(None))
        result = await session.execute(query)
        events_with_embeddings = result.scalar()
        results["embeddings_count"] = {"status": "ok", "count": events_with_embeddings}
    except Exception as e:
        results["embeddings_count"] = {"status": "error", "error": str(e)}
    
    # Test 3: Embedding service
    try:
        test_embedding = await embedding_service.generate_embedding("test text")
        results["embedding_service"] = {
            "status": "ok", 
            "embedding_length": len(test_embedding) if test_embedding else None
        }
    except Exception as e:
        results["embedding_service"] = {"status": "error", "error": str(e)}
    
    # Test 4: Get sample events
    try:
        query = select(Event).limit(3)
        result = await session.execute(query)
        sample_events = result.scalars().all()
        results["sample_events"] = {
            "status": "ok", 
            "count": len(sample_events),
            "events": [{"id": e.id, "title": e.title, "has_embedding": e.embeddings is not None} for e in sample_events]
        }
    except Exception as e:
        results["sample_events"] = {"status": "error", "error": str(e)}
    
    return results


@router.post("/debug/simple-search")
async def debug_simple_search(
    query_text: str,
    session: AsyncSession = Depends(get_session)
):
    """Simple search test without full similarity service"""
    
    results = {}
    
    # Step 1: Generate embedding
    try:
        embedding = await embedding_service.generate_embedding(query_text)
        results["embedding"] = {
            "status": "ok", 
            "length": len(embedding),
            "sample": embedding[:5] if embedding else None
        }
    except Exception as e:
        results["embedding"] = {"status": "error", "error": str(e)}
        return results
    
    # Step 2: Try manual similarity search (fallback method)
    try:
        from app.services.enhanced_similarity import enhanced_similarity_service
        similar_events = await enhanced_similarity_service._manual_similarity_search(
            session=session,
            query_embedding=embedding,
            limit=3,
            min_similarity=0.3,  # Lower threshold for testing
            exclude_event_id=None
        )
        results["manual_search"] = {
            "status": "ok",
            "count": len(similar_events),
            "events": [{"id": e.id, "title": e.title, "score": score} for e, score in similar_events]
        }
    except Exception as e:
        results["manual_search"] = {"status": "error", "error": str(e)}
    
    # Step 3: Try vector search (pgvector method)
    try:
        from app.services.enhanced_similarity import enhanced_similarity_service
        similar_events = await enhanced_similarity_service._find_by_vector_similarity(
            session=session,
            query_embedding=embedding,
            limit=3,
            min_similarity=0.3,  # Lower threshold for testing
            exclude_event_id=None
        )
        results["vector_search"] = {
            "status": "ok",
            "count": len(similar_events),
            "events": [{"id": e.id, "title": e.title, "score": score} for e, score in similar_events]
        }
    except Exception as e:
        results["vector_search"] = {"status": "error", "error": str(e)}
    
    return results
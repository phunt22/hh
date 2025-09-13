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
    
    if not request.query_text and not request.event_id:
        raise HTTPException(
            status_code=400, 
            detail="Either query_text or event_id must be provided"
        )
    
    try:
        # Force limit to 5 for similarity search
        similarity_limit = 5
        
        if request.event_id:
            # Search by event ID using embeddings
            similar_events_with_scores = await enhanced_similarity_service.find_similar_events_by_id(
                session=session,
                event_id=request.event_id,
                limit=similarity_limit,
                min_similarity=request.min_similarity
            )
            
            # Get the source event for response
            source_event_query = select(Event).where(Event.id == request.event_id)
            source_result = await session.execute(source_event_query)
            source_event = source_result.scalar_one_or_none()
            query_event = EventResponse.from_orm(source_event) if source_event else None
            
        else:
            # Search by text query using embeddings
            similar_events_with_scores = await enhanced_similarity_service.find_similar_events_by_text(
                session=session,
                query_text=request.query_text,
                limit=similarity_limit,
                min_similarity=request.min_similarity
            )
            query_event = None
        
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
            query_event=query_event,
            similar_events=similar_events,
            total_found=len(similar_events)
        )
    
    except Exception as e:
        logger.error(f"Error in similarity search: {e}")
        raise HTTPException(status_code=500, detail="Error performing similarity search")

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
) -> List[str]:
    """Get list of all event categories"""
    
    query = select(Event.category).distinct().where(Event.category.is_not(None))
    result = await session.execute(query)
    categories = [row[0] for row in result.all() if row[0]]

    # TODO colormap here
    
    return sorted(categories)


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
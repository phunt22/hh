from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, text, and_, or_
from sqlmodel import SQLModel
from typing import List, Optional, Dict, Any, Tuple
from app.models.event import Event, EventSimilarity
from app.services.embedding import embedding_service
from app.schemas.event import SimilarEvent, SimilaritySearchRequest, SimilaritySearchResponse, EventResponse
import logging

logger = logging.getLogger(__name__)


class SimilarityService:
    def __init__(self):
        self.min_similarity_threshold = 0.5
        self.related_events_threshold = 0.8

    async def find_similar_events_by_text(
        self, 
        session: AsyncSession,
        query_text: str,
        limit: int = 10,
        min_similarity: float = 0.7,
        exclude_event_id: Optional[str] = None
    ) -> List[Tuple[Event, float]]:
        """Find similar events using text query with vector similarity"""
        
        # Generate embedding for query text
        query_embedding = await embedding_service.generate_embedding(query_text)
        
        # Build the similarity query using pgvector
        similarity_expr = func.cosine_similarity("embeddings", query_embedding)
        
        query = (
            select(Event, similarity_expr.label("similarity"))
            .where(
                and_(
                    Event.embeddings.is_not(None),
                    similarity_expr >= min_similarity
                )
            )
            .order_by(similarity_expr.desc())
            .limit(limit)
        )
        
        # Exclude specific event if provided
        if exclude_event_id:
            query = query.where(Event.id != exclude_event_id)
        
        try:
            result = await session.execute(query)
            return [(event, float(similarity)) for event, similarity in result.all()]
        except Exception as e:
            logger.error(f"Error in vector similarity search: {e}")
            # Fallback to manual similarity calculation
            return await self._manual_similarity_search(session, query_embedding, limit, min_similarity, exclude_event_id)

    async def find_similar_events_by_id(
        self, 
        session: AsyncSession,
        event_id: str,
        limit: int = 10,
        min_similarity: float = 0.7,
        include_related: bool = True
    ) -> SimilaritySearchResponse:
        """Find events similar to a specific event by ID"""
        
        # Get the source event
        source_event_result = await session.execute(
            select(Event).where(Event.id == event_id)
        )
        source_event = source_event_result.scalar_one_or_none()
        
        if not source_event:
            return SimilaritySearchResponse(
                query_event=None,
                similar_events=[],
                total_found=0
            )
        
        similar_events = []
        
        # Method 1: Vector similarity search
        if source_event.embeddings:
            vector_similar = await self._find_by_vector_similarity(
                session, source_event.embeddings, limit, min_similarity, event_id
            )
            for event, similarity in vector_similar:
                similar_events.append(SimilarEvent(
                    event=EventResponse.from_orm(event),
                    similarity_score=similarity,
                    relationship_type="similar"
                ))
        
        # Method 2: Find explicitly related events if requested
        if include_related and source_event.related_event_ids:
            related_events = await self._find_related_events(session, source_event.related_event_ids)
            for event in related_events:
                # Check if not already in results
                existing_ids = {se.event.id for se in similar_events}
                if event.id not in existing_ids:
                    similar_events.append(SimilarEvent(
                        event=EventResponse.from_orm(event),
                        similarity_score=1.0,  # Related events get max score
                        relationship_type="related"
                    ))
        
        # Method 3: Check stored similarities
        stored_similar = await self._find_stored_similarities(session, event_id, limit)
        for event, similarity, rel_type in stored_similar:
            existing_ids = {se.event.id for se in similar_events}
            if event.id not in existing_ids:
                similar_events.append(SimilarEvent(
                    event=EventResponse.from_orm(event),
                    similarity_score=similarity,
                    relationship_type=rel_type
                ))
        
        # Sort by similarity score and limit results
        similar_events.sort(key=lambda x: x.similarity_score, reverse=True)
        similar_events = similar_events[:limit]
        
        return SimilaritySearchResponse(
            query_event=EventResponse.from_orm(source_event),
            similar_events=similar_events,
            total_found=len(similar_events)
        )

    async def _find_by_vector_similarity(
        self, 
        session: AsyncSession, 
        query_embedding: List[float], 
        limit: int, 
        min_similarity: float,
        exclude_event_id: str
    ) -> List[Tuple[Event, float]]:
        """Find similar events using vector similarity"""
        
        try:
            # Use pgvector's cosine similarity
            similarity_expr = func.cosine_similarity("embeddings", query_embedding)
            
            query = (
                select(Event, similarity_expr.label("similarity"))
                .where(
                    and_(
                        Event.embeddings.is_not(None),
                        Event.id != exclude_event_id,
                        similarity_expr >= min_similarity
                    )
                )
                .order_by(similarity_expr.desc())
                .limit(limit)
            )
            
            result = await session.execute(query)
            return [(event, float(similarity)) for event, similarity in result.all()]
        
        except Exception as e:
            logger.error(f"Vector similarity search failed: {e}")
            return []

    async def _manual_similarity_search(
        self, 
        session: AsyncSession, 
        query_embedding: List[float], 
        limit: int, 
        min_similarity: float,
        exclude_event_id: Optional[str] = None
    ) -> List[Tuple[Event, float]]:
        """Fallback manual similarity calculation"""
        
        # Get all events with embeddings
        query = select(Event).where(Event.embeddings.is_not(None))
        if exclude_event_id:
            query = query.where(Event.id != exclude_event_id)
        
        result = await session.execute(query)
        events = result.scalars().all()
        
        # Calculate similarities manually
        similarities = []
        for event in events:
            if event.embeddings:
                similarity = embedding_service.cosine_similarity(query_embedding, event.embeddings)
                if similarity >= min_similarity:
                    similarities.append((event, similarity))
        
        # Sort and limit
        similarities.sort(key=lambda x: x[1], reverse=True)
        return similarities[:limit]

    async def _find_related_events(self, session: AsyncSession, related_ids_str: str) -> List[Event]:
        """Find explicitly related events by IDs"""
        
        if not related_ids_str:
            return []
        
        # Parse comma-separated IDs
        related_ids = [id.strip() for id in related_ids_str.split(",") if id.strip()]
        if not related_ids:
            return []
        
        # Query for related events
        query = select(Event).where(Event.id.in_(related_ids))
        result = await session.execute(query)
        return result.scalars().all()

    async def _find_stored_similarities(
        self, 
        session: AsyncSession, 
        event_id: str, 
        limit: int
    ) -> List[Tuple[Event, float, str]]:
        """Find pre-calculated similarities from EventSimilarity table"""
        
        # Query similarities where the event is either source or target
        query = (
            select(EventSimilarity, Event)
            .join(
                Event,
                or_(
                    and_(EventSimilarity.event_id_1 == event_id, Event.id == EventSimilarity.event_id_2),
                    and_(EventSimilarity.event_id_2 == event_id, Event.id == EventSimilarity.event_id_1)
                )
            )
            .order_by(EventSimilarity.similarity_score.desc())
            .limit(limit)
        )
        
        result = await session.execute(query)
        return [
            (event, float(similarity.similarity_score), similarity.relationship_type)
            for similarity, event in result.all()
        ]

    async def calculate_and_store_similarities(
        self, 
        session: AsyncSession,
        event_ids: List[str],
        batch_size: int = 100
    ) -> int:
        """Calculate similarities between events and store them"""
        
        stored_count = 0
        
        # Get events with embeddings
        query = select(Event).where(
            and_(
                Event.id.in_(event_ids),
                Event.embeddings.is_not(None)
            )
        )
        result = await session.execute(query)
        events = result.scalars().all()
        
        # Calculate pairwise similarities
        similarities_to_store = []
        
        for i, event1 in enumerate(events):
            for j, event2 in enumerate(events[i + 1:], i + 1):
                similarity = embedding_service.cosine_similarity(
                    event1.embeddings, event2.embeddings
                )
                
                # Only store high similarities
                if similarity >= self.min_similarity_threshold:
                    relationship_type = "related" if similarity >= self.related_events_threshold else "similar"
                    
                    similarities_to_store.append(EventSimilarity(
                        event_id_1=event1.id,
                        event_id_2=event2.id,
                        similarity_score=similarity,
                        relationship_type=relationship_type
                    ))
        
        # Store in batches
        if similarities_to_store:
            session.add_all(similarities_to_store)
            await session.commit()
            stored_count = len(similarities_to_store)
        
        return stored_count

    async def update_related_events(
        self, 
        session: AsyncSession,
        event_id: str,
        min_similarity: float = 0.8
    ) -> int:
        """Update the related_event_ids field for an event based on similarities"""
        
        # Find high-similarity events
        similar_events = await self._find_stored_similarities(session, event_id, limit=50)
        
        # Filter for high similarities (related events)
        related_ids = [
            event.id for event, similarity, rel_type in similar_events
            if similarity >= min_similarity
        ]
        
        if related_ids:
            # Update the event's related_event_ids field
            query = select(Event).where(Event.id == event_id)
            result = await session.execute(query)
            event = result.scalar_one_or_none()
            
            if event:
                event.related_event_ids = ",".join(related_ids)
                await session.commit()
                return len(related_ids)
        
        return 0


# Global instance
similarity_service = SimilarityService()
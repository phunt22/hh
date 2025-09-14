# app/services/enhanced_similarity.py
import numpy as np
import logging
from typing import List, Tuple, Optional, Dict
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, text
from app.models.event import Event
from app.services.embedding import embedding_service

logger = logging.getLogger(__name__)


class EnhancedSimilarityService:
    """Enhanced similarity service using embeddings column for vector similarity"""
    
    def __init__(self):
        self.default_limit = 5

    async def find_similar_events_by_text(
        self,
        session: AsyncSession,
        query_text: str,
        limit: int = 5,
        min_similarity: float = 0.7,
        exclude_event_id: Optional[str] = None
    ) -> List[Tuple[Event, float]]:
        """Find similar events using text query with vector similarity on embeddings column"""
        
        # Generate embedding for query text
        query_embedding = await embedding_service.generate_embedding(query_text)
        
        return await self._find_by_vector_similarity(
            session, query_embedding, limit, min_similarity, exclude_event_id
        )

    async def find_similar_events_by_id(
        self,
        session: AsyncSession,
        event_id: str,
        limit: int = 5,
        min_similarity: float = 0.7
    ) -> List[Tuple[Event, float]]:
        """Find events similar to a specific event using its embeddings"""
        
        # Get the source event and its embedding
        source_event_query = select(Event).where(Event.id == event_id)
        source_result = await session.execute(source_event_query)
        source_event = source_result.scalar_one_or_none()
        
        if not source_event or not source_event.embeddings:
            logger.warning(f"Event {event_id} not found or has no embeddings")
            return []
        
        # Use the source event's embedding to find similar events
        return await self._find_by_vector_similarity(
            session, 
            source_event.embeddings, 
            limit, 
            min_similarity, 
            event_id
        )

    async def _find_by_vector_similarity(
        self,
        session: AsyncSession,
        query_embedding: List[float],
        limit: int,
        min_similarity: float,
        exclude_event_id: Optional[str] = None
    ) -> List[Tuple[Event, float]]:
        """Find similar events using pgvector cosine similarity"""
        
        try:
            # Convert list[float] into Postgres array literal
            embedding_str = "[" + ",".join(map(str, query_embedding)) + "]"

            sql = text("""
                SELECT 
                    id,
                    title,
                    description,
                    category,
                    longitude,
                    latitude,
                    embeddings,
                    start,
                    "end",
                    city,
                    region,
                    location,
                    attendance,
                    spend_amount,
                    predicthq_updated,
                    created_at,
                    updated_at,
                    related_event_ids,
                    1 - (embeddings <=> :embedding) AS similarity
                FROM events
                WHERE embeddings IS NOT NULL
                AND 1 - (embeddings <=> :embedding) >= :min_similarity
                {exclude_clause}
                ORDER BY similarity DESC
                LIMIT :limit
            """.format(
                exclude_clause="AND id != :exclude_event_id" if exclude_event_id else ""
            ))

            params = {
                "embedding": embedding_str,
                "limit": limit,
                "min_similarity": min_similarity
            }
            if exclude_event_id:
                params["exclude_event_id"] = exclude_event_id

            result = await session.execute(sql, params)
            rows = result.fetchall()

            
            # Convert results to Event objects with similarity scores
            similar_events = []
            for row in rows:
                # Create Event object from row data
                event = Event(
                    id=row.id,
                    title=row.title,
                    description=row.description,
                    category=row.category,
                    longitude=row.longitude,
                    latitude=row.latitude,
                    embeddings=row.embeddings,
                    start=row.start,
                    end=row.end,
                    location=row.location,
                    predicthq_updated=row.predicthq_updated,
                    created_at=row.created_at,
                    updated_at=row.updated_at,
                    related_event_ids=row.related_event_ids
                )
                
                similarity_score = float(row.similarity)
                similar_events.append((event, similarity_score))
            
            logger.info(f"Found {len(similar_events)} similar events using vector similarity")
            return similar_events
            
        except Exception as e:
            logger.error(f"Vector similarity search failed: {e}")
            # Fallback to manual similarity calculation
            return []

    async def _manual_similarity_search(
        self,
        session: AsyncSession,
        query_embedding: List[float],
        limit: int,
        min_similarity: float,
        exclude_event_id: Optional[str] = None
    ) -> List[Tuple[Event, float]]:
        """Fallback manual similarity calculation using numpy"""
        
        # Get all events with embeddings
        query = select(Event).where(Event.embeddings.is_not(None))
        if exclude_event_id:
            query = query.where(Event.id != exclude_event_id)
        
        result = await session.execute(query)
        events = result.scalars().all()
        
        # Calculate similarities manually
        similarities = []
        query_vector = np.array(query_embedding)
        
        for event in events:
            if event.embeddings:
                try:
                    event_vector = np.array(event.embeddings)
                    
                    # Calculate cosine similarity
                    dot_product = np.dot(query_vector, event_vector)
                    norm_query = np.linalg.norm(query_vector)
                    norm_event = np.linalg.norm(event_vector)
                    
                    if norm_query > 0 and norm_event > 0:
                        similarity = dot_product / (norm_query * norm_event)
                        
                        if similarity >= min_similarity:
                            similarities.append((event, float(similarity)))
                            
                except Exception as e:
                    logger.warning(f"Error calculating similarity for event {event.id}: {e}")
                    continue
        
        # Sort by similarity score (descending) and limit
        similarities.sort(key=lambda x: x[1], reverse=True)
        
        logger.info(f"Manual similarity search found {len(similarities)} events")
        return similarities[:limit]

    async def get_event_embedding(
        self,
        session: AsyncSession,
        event_id: str
    ) -> Optional[List[float]]:
        """Get embedding for a specific event"""
        
        query = select(Event.embeddings).where(Event.id == event_id)
        result = await session.execute(query)
        embedding = result.scalar_one_or_none()
        
        return embedding

    async def batch_similarity_search(
        self,
        session: AsyncSession,
        event_ids: List[str],
        limit_per_event: int = 5,
        min_similarity: float = 0.7
    ) -> Dict[str, List[Tuple[Event, float]]]:
        """Perform similarity search for multiple events at once"""
        
        results = {}
        
        for event_id in event_ids:
            try:
                similar_events = await self.find_similar_events_by_id(
                    session, event_id, limit_per_event, min_similarity
                )
                results[event_id] = similar_events
                
            except Exception as e:
                logger.error(f"Error in batch similarity search for {event_id}: {e}")
                results[event_id] = []
        
        return results


# Global instance
enhanced_similarity_service = EnhancedSimilarityService()
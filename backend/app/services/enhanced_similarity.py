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

    # async def _find_by_vector_similarity(
    #     self,
    #     session: AsyncSession,
    #     query_embedding: List[float],
    #     limit: int,
    #     min_similarity: float,
    #     exclude_event_id: Optional[str] = None
    # ) -> List[Tuple[Event, float]]:
    #     """Find similar events using pgvector cosine similarity"""
        
    #     try:
    #         # Build the similarity query using pgvector
    #         # Convert embedding to PostgreSQL array format
    #         embedding_str = f"[{','.join(map(str, query_embedding))}]"
            
    #         # Base query with cosine similarity
    #         similarity_expr = f"1 - (embeddings <=> '{embedding_str}'::vector)"
            
    #         query_parts = [
    #             "SELECT *, ",
    #             f"({similarity_expr}) as similarity ",
    #             "FROM events ",
    #             "WHERE embeddings IS NOT NULL "
    #         ]
            
    #         # Add similarity threshold
    #         query_parts.append(f"AND ({similarity_expr}) >= {min_similarity} ")
            
    #         # Exclude specific event if provided
    #         if exclude_event_id:
    #             query_parts.append(f"AND id != '{exclude_event_id}' ")
            
    #         # Order by similarity and limit
    #         query_parts.extend([
    #             f"ORDER BY ({similarity_expr}) DESC ",
    #             f"LIMIT {limit}"
    #         ])
            
    #         full_query = "".join(query_parts)
            
    #         # Execute the query
    #         result = await session.execute(text(full_query))
    #         rows = result.fetchall()
            
    #         # Convert results to Event objects with similarity scores
    #         similar_events = []
    #         for row in rows:
    #             # Create Event object from row data
    #             event = Event(
    #                 id=row.id,
    #                 title=row.title,
    #                 description=row.description,
    #                 category=row.category,
    #                 longitude=row.longitude,
    #                 latitude=row.latitude,
    #                 embeddings=row.embeddings,
    #                 start=row.start,
    #                 end=row.end,
    #                 location=row.location,
    #                 predicthq_updated=row.predicthq_updated,
    #                 created_at=row.created_at,
    #                 updated_at=row.updated_at,
    #                 related_event_ids=row.related_event_ids
    #             )
                
    #             similarity_score = float(row.similarity)
    #             similar_events.append((event, similarity_score))
            
    #         logger.info(f"Found {len(similar_events)} similar events using vector similarity")
    #         return similar_events
            
    #     except Exception as e:
    #         logger.error(f"Vector similarity search failed: {e}")
    #         # Fallback to manual similarity calculation
    #         return await self._manual_similarity_search(
    #             session, query_embedding, limit, min_similarity, exclude_event_id
    #         )



    
    # async def _manual_similarity_search(
    #     self,
    #     session: AsyncSession,
    #     query_embedding: List[float],
    #     limit: int,
    #     min_similarity: float,
    #     exclude_event_id: Optional[str] = None
    # ) -> List[Tuple[Event, float]]:
    #     """Fallback manual similarity calculation using numpy"""
    #     query = select(Event).where(Event.embeddings.is_not(None))
    #     if exclude_event_id:
    #         query = query.where(Event.id != exclude_event_id)
        
    #     result = await session.execute(query)
    #     events = result.scalars().all()
        
    #     similarities = []
    #     query_vector = np.array(query_embedding)
        
    #     for event in events:
    #         if event.embeddings:
    #             try:
    #                 event_vector = np.array(event.embeddings)
    #                 dot_product = np.dot(query_vector, event_vector)
    #                 norm_query = np.linalg.norm(query_vector)
    #                 norm_event = np.linalg.norm(event_vector)
                    
    #                 if norm_query > 0 and norm_event > 0:
    #                     similarity = dot_product / (norm_query * norm_event)
    #                     if similarity >= min_similarity:
    #                         similarities.append((event, float(similarity)))
    #             except Exception as e:
    #                 logger.warning(f"Error calculating similarity for event {event.id}: {e}")
    #                 continue
        
    #     similarities.sort(key=lambda x: x[1], reverse=True)
    #     logger.info(f"Manual similarity search found {len(similarities)} events")
    #     return similarities[:limit]


    async def _find_by_vector_similarity(
        self,
        session: AsyncSession,
        query_embedding: List[float],
        limit: int,
        min_similarity: float,
        exclude_event_id: Optional[str] = None,
    ) -> List[Tuple[Event, float]]:
        """Find similar events using pgvector cosine similarity directly in database"""
        try:
            # Convert embedding to PostgreSQL vector format
            embedding_str = f"[{','.join(map(str, query_embedding))}]"

            if exclude_event_id:
                sql_query = """
                SELECT 
                    id, title, description, category, longitude, latitude, 
                    embeddings, start, "end", location, predicthq_updated,
                    created_at, updated_at, related_event_ids, city, region,
                    attendance, spend_amount,
                    (1 - (embeddings <=> :embedding::vector)) AS similarity_score
                FROM events 
                WHERE embeddings IS NOT NULL 
                  AND id != :exclude_id
                  AND (1 - (embeddings <=> :embedding::vector)) >= :min_similarity
                ORDER BY embeddings <=> :embedding::vector ASC
                LIMIT :limit
                """
                params = {
                    "embedding": embedding_str,
                    "exclude_id": exclude_event_id,
                    "min_similarity": min_similarity,
                    "limit": limit,
                }
            else:
                sql_query = """
                SELECT 
                    id, title, description, category, longitude, latitude, 
                    embeddings, start, "end", location, predicthq_updated,
                    created_at, updated_at, related_event_ids, city, region,
                    attendance, spend_amount,
                    (1 - (embeddings <=> :embedding::vector)) AS similarity_score
                FROM events 
                WHERE embeddings IS NOT NULL 
                  AND (1 - (embeddings <=> :embedding::vector)) >= :min_similarity
                ORDER BY embeddings <=> :embedding::vector ASC
                LIMIT :limit
                """
                params = {
                    "embedding": embedding_str,
                    "min_similarity": min_similarity,
                    "limit": limit,
                }

            logger.info(f"Executing vector similarity search with min_similarity={min_similarity}")
            result = await session.execute(text(sql_query), params)
            rows = result.fetchall()
            logger.info(f"Database returned {len(rows)} similar events")

            similar_events: List[Tuple[Event, float]] = []
            for row in rows:
                try:
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
                        predicthq_updated=getattr(row, "predicthq_updated", None),
                        created_at=row.created_at,
                        updated_at=row.updated_at,
                        related_event_ids=row.related_event_ids,
                        city=getattr(row, "city", None),
                        region=getattr(row, "region", None),
                        attendance=getattr(row, "attendance", None),
                        spend_amount=getattr(row, "spend_amount", None),
                    )
                    similarity_score = float(row.similarity_score)
                    similar_events.append((event, similarity_score))
                    logger.info(f"Event: {event.title} | Similarity: {similarity_score:.3f}")
                except Exception as row_error:
                    logger.warning(
                        f"Error processing row for event {getattr(row, 'id', 'unknown')}: {row_error}"
                    )
                    continue

            logger.info(
                f"Successfully processed {len(similar_events)} similar events using database vector search"
            )
            return similar_events

        except Exception as e:
            logger.error(f"Database vector similarity search failed: {e}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            logger.info("Falling back to manual similarity calculation...")
            return await self._manual_similarity_search(
                session, query_embedding, limit, min_similarity, exclude_event_id
            )

    async def _manual_similarity_search(
        self,
        session: AsyncSession,
        query_embedding: List[float],
        limit: int,
        min_similarity: float,
        exclude_event_id: Optional[str] = None,
    ) -> List[Tuple[Event, float]]:
        """Fallback manual similarity calculation — should rarely be used"""
        logger.warning("Using manual similarity calculation — avoid for performance when possible")

        query = select(Event).where(Event.embeddings.is_not(None)).limit(500)
        if exclude_event_id:
            query = query.where(Event.id != exclude_event_id)

        result = await session.execute(query)
        events = result.scalars().all()

        similarities: List[Tuple[Event, float]] = []
        query_vector = np.array(query_embedding, dtype=np.float32)

        for event in events:
            if event.embeddings and len(event.embeddings) > 0:
                try:
                    event_vector = np.array(event.embeddings, dtype=np.float32)

                    # Ensure vectors align
                    if len(query_vector) != len(event_vector):
                        logger.warning(f"Vector length mismatch for event {event.id}")
                        continue

                    # Cosine similarity
                    dot_product = np.dot(query_vector, event_vector)
                    norm_query = np.linalg.norm(query_vector)
                    norm_event = np.linalg.norm(event_vector)

                    if norm_query > 0 and norm_event > 0:
                        similarity = float(dot_product / (norm_query * norm_event))
                        if similarity >= min_similarity:
                            similarities.append((event, similarity))
                except Exception as err:
                    logger.warning(f"Error calculating similarity for event {event.id}: {err}")
                    continue

        similarities.sort(key=lambda x: x[1], reverse=True)
        logger.info(
            f"Manual similarity search found {len(similarities)} events from {len(events)} candidates"
        )
        return similarities[:limit]


# Global instance
enhanced_similarity_service = EnhancedSimilarityService()
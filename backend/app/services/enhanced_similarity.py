# app/services/enhanced_similarity.py
import numpy as np
import logging
from typing import Any, List, Tuple, Optional, Dict
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, text
from app.models.event import Event
from app.services.embedding import embedding_service
from app.services.pinecone_service import pinecone_service

logger = logging.getLogger(__name__)


class EnhancedSimilarityService:
    """Enhanced similarity service using embeddings column for vector similarity"""
    
    def __init__(self):
        self.default_limit = 5

    async def find_similar_events(
        self,
        query_text: str,
        limit: int = 5,
    ) -> List[Dict[str, Any]]:
        """Find similar events using Pinecone vector search"""
        
        try:
            # Generate embedding for query
            query_embedding = await embedding_service.generate_embedding(query_text)
            
            # Search in Pinecone
            similar_events = await pinecone_service.find_similar_events(
                query_embedding=query_embedding,
                limit=limit,
            )
            
            logger.info(f"Found {len(similar_events)} similar events using Pinecone")
            return similar_events
            
        except Exception as e:
            logger.error(f"Error in Pinecone similarity search: {e}")
            # Fallback to database search
            return []

    async def find_similar_events_by_id(
        self,
        event_id: str,
        limit: int = 5,
    ) -> List[Dict[str, any]]:
        """Find similar events by ID using Pinecone"""
        
        
        try:
            # Search similar events in Pinecone
            similar_events = await pinecone_service.find_similar_by_event_id(
                event_id=event_id,
                limit=limit,
            )
            
            return similar_events
            
        except Exception as e:
            logger.error(f"Error in Pinecone similarity search for {event_id}: {e}")
            # Fallback to database search
            return []



# Global instance
enhanced_similarity_service = EnhancedSimilarityService()
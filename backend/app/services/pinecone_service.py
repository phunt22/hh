import logging
from typing import List, Dict, Any, Optional, Tuple
from pinecone import Pinecone, ServerlessSpec
from app.core.config import settings
from app.services.embedding import embedding_service

logger = logging.getLogger(__name__)


class PineconeService:
    def __init__(self):
        self.pc = Pinecone(api_key=settings.pinecone_api_key)
        self.index_name = settings.pinecone_index_name
        self.dimension = settings.pinecone_dimension
        self.index = None
        
    async def initialize_index(self):
        """Initialize Pinecone index (create if doesn't exist)"""
        try:
            # Check if index exists
            existing_indexes = self.pc.list_indexes().names()
            
            if self.index_name not in existing_indexes:
                logger.info(f"Creating Pinecone index: {self.index_name}")
                
                self.pc.create_index(
                    name=self.index_name,
                    dimension=self.dimension,
                    metric='cosine',
                    spec=ServerlessSpec(
                        cloud='aws',  # or 'gcp'
                        region='us-east-1'  # adjust based on your region
                    )
                )
            
            # Connect to index
            self.index = self.pc.Index(self.index_name)
            logger.info(f"Connected to Pinecone index: {self.index_name}")
            
        except Exception as e:
            logger.error(f"Error initializing Pinecone index: {e}")
            raise
    
    async def upsert_event_embedding(
        self, 
        event_id: str, 
        embedding: List[float], 
        metadata: Dict[str, Any]
    ) -> bool:
        """Store event embedding in Pinecone"""
        try:
            if not self.index:
                await self.initialize_index()
            
            # Prepare vector for upsert
            vector_data = {
                'id': event_id,
                'values': embedding,
                'metadata': metadata
            }
            
            # Upsert to Pinecone
            self.index.upsert(vectors=[vector_data])
            
            logger.debug(f"Upserted embedding for event {event_id} to Pinecone")
            return True
            
        except Exception as e:
            logger.error(f"Error upserting to Pinecone for event {event_id}: {e}")
            return False
    
    async def batch_upsert_events(
        self, 
        events_data: List[Dict[str, Any]]
    ) -> int:
        """Batch upsert multiple event embeddings"""
        try:
            if not self.index:
                await self.initialize_index()
            
            vectors = []
            for event_data in events_data:
                embedding = event_data.get('embedding')
                if (
                    embedding is not None
                    and len(embedding) > 0
                    and any(v != 0.0 for v in embedding)
                    and event_data.get('id')
                ):
                    vector = {
                        'id': event_data['id'],
                        'values': event_data['embedding'],
                        'metadata': {k: v for k, v in event_data.items() if k not in ('embedding', 'indexed')}
                    }
                    vectors.append(vector)
            
            if vectors:
                # Batch upsert (Pinecone handles batches of up to 100)
                batch_size = 100
                upserted_count = 0
                
                for i in range(0, len(vectors), batch_size):
                    batch = vectors[i:i + batch_size]
                    self.index.upsert(vectors=batch)
                    upserted_count += len(batch)
                
                logger.info(f"Batch upserted {upserted_count} vectors to Pinecone")
                return upserted_count
            
            return 0
            
        except Exception as e:
            logger.error(f"Error in batch upsert to Pinecone: {e}, Events: {events_data}")
            return 0
    
    async def find_similar_events(
        self, 
        query_embedding: List[float], 
        limit: int = 5,
    ) -> List[Tuple[str, float, Dict[str, Any]]]:
        """Find similar events using Pinecone vector search"""
        try:
            if not self.index:
                await self.initialize_index()
            
            # Query Pinecone
            query_response = self.index.query(
                vector=query_embedding,
                top_k=limit,
                include_values=False,
                include_metadata=True,
            )
            
            # Process results
            similar_events = []
            for match in query_response.matches:
                similar_events.append(match.metadata)
            
            logger.info(f"Found {len(similar_events)} similar events in Pinecone")
            return similar_events
            
        except Exception as e:
            logger.error(f"Error querying Pinecone: {e}")
            return []
    
    async def find_similar_by_event_id(
        self, 
        event_id: str, 
        limit: int = 5,
    ) -> List[Tuple[str, float, Dict[str, Any]]]:
        """Find similar events by querying with an existing event's vector"""
        try:
            if not self.index:
                await self.initialize_index()
            
            # Get the event's vector from Pinecone
            fetch_response = self.index.fetch(ids=[event_id])
            
            if event_id not in fetch_response.vectors:
                logger.warning(f"Event {event_id} not found in Pinecone")
                return []
            
            event_vector = fetch_response.vectors[event_id].values
            
            # Find similar events (exclude the query event itself)
            similar_events = await self.find_similar_events(
                query_embedding=event_vector,
                limit=limit + 1,  # +1 to account for excluding self
            )
            
            # Filter out the query event itself
            filtered_events = [
                (eid, score, metadata) 
                for eid, score, metadata in similar_events 
                if eid != event_id
            ]
            
            return filtered_events[:limit]
            
        except Exception as e:
            logger.error(f"Error finding similar events for {event_id}: {e}")
            return []
    
    async def delete_event(self, event_id: str) -> bool:
        """Delete event from Pinecone"""
        try:
            if not self.index:
                await self.initialize_index()
            
            self.index.delete(ids=[event_id])
            logger.info(f"Deleted event {event_id} from Pinecone")
            return True
            
        except Exception as e:
            logger.error(f"Error deleting event {event_id} from Pinecone: {e}")
            return False
    
    async def get_index_stats(self) -> Dict[str, Any]:
        """Get Pinecone index statistics"""
        try:
            if not self.index:
                await self.initialize_index()
            
            stats = self.index.describe_index_stats()
            return {
                'total_vector_count': stats.total_vector_count,
                'dimension': stats.dimension,
                'index_fullness': stats.index_fullness,
                'namespaces': stats.namespaces
            }
            
        except Exception as e:
            logger.error(f"Error getting Pinecone stats: {e}")
            return {}


# Global instance
pinecone_service = PineconeService()
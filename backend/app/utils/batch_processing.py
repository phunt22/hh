import asyncio
from typing import List, Dict, Any, Callable, Optional
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.event import Event
from app.services.embedding import embedding_service
from app.services.predicthq import predicthq_service
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)


class BatchProcessor:
    def __init__(self, batch_size: int = None, max_workers: int = None):
        self.batch_size = batch_size or settings.batch_size
        self.max_workers = max_workers or settings.max_workers
        
    async def process_events_batch(
        self,
        session: AsyncSession,
        raw_events: List[Dict[str, Any]],
        progress_callback: Optional[Callable[[int, int], None]] = None
    ) -> Dict[str, int]:
        """Process a batch of events with embeddings and database operations"""
        
        stats = {
            "processed": 0,
            "created": 0,
            "updated": 0,
            "errors": 0
        }
        
        # Process events in smaller batches to manage memory and API rate limits
        for i in range(0, len(raw_events), self.batch_size):
            batch = raw_events[i:i + self.batch_size]
            batch_stats = await self._process_single_batch(session, batch)
            
            # Update statistics
            for key in stats:
                stats[key] += batch_stats[key]
            
            # Progress callback
            if progress_callback:
                progress_callback(stats["processed"], len(raw_events))
            
            # Small delay to prevent overwhelming external APIs
            await asyncio.sleep(0.1)
        
        return stats

    async def _process_single_batch(
        self,
        session: AsyncSession,
        batch: List[Dict[str, Any]]
    ) -> Dict[str, int]:
        """Process a single batch of events"""
        
        stats = {"processed": 0, "created": 0, "updated": 0, "errors": 0}
        
        try:
            # Parse event data
            parsed_events = []
            texts_for_embedding = []
            
            for raw_event in batch:
                try:
                    parsed_event = predicthq_service.parse_event_data(raw_event)
                    parsed_events.append(parsed_event)
                    
                    # Prepare text for embedding
                    text = embedding_service.prepare_event_text(
                        parsed_event["title"],
                        parsed_event["description"]
                    )
                    texts_for_embedding.append(text)
                    
                except Exception as e:
                    logger.error(f"Error parsing event {raw_event.get('id', 'unknown')}: {e}")
                    stats["errors"] += 1
                    continue
            
            if not parsed_events:
                return stats
            
            # Generate embeddings in batch
            embeddings = await embedding_service.generate_batch_embeddings(texts_for_embedding)
            
            # Check which events already exist
            event_ids = [event["id"] for event in parsed_events]
            existing_events = await self._get_existing_events(session, event_ids)
            existing_ids = {event.id for event in existing_events}
            
            # Prepare events for database operations
            events_to_create = []
            events_to_update = []
            
            for parsed_event, embedding in zip(parsed_events, embeddings):
                try:
                    event_data = {**parsed_event, "embeddings": embedding}
                    
                    if parsed_event["id"] in existing_ids:
                        # Update existing event
                        existing_event = next(e for e in existing_events if e.id == parsed_event["id"])
                        for key, value in event_data.items():
                            if key != "id":  # Don't update primary key
                                setattr(existing_event, key, value)
                        existing_event.updated_at = datetime.now(timezone.utc)
                        events_to_update.append(existing_event)
                    else:
                        # Create new event
                        event = Event(**event_data)
                        events_to_create.append(event)
                    
                    stats["processed"] += 1
                    
                except Exception as e:
                    logger.error(f"Error preparing event {parsed_event.get('id', 'unknown')}: {e}")
                    stats["errors"] += 1
                    continue
            
            # Database operations
            if events_to_create:
                session.add_all(events_to_create)
                stats["created"] = len(events_to_create)
            
            if events_to_update:
                stats["updated"] = len(events_to_update)
            
            # Commit the batch
            await session.commit()
            
        except Exception as e:
            logger.error(f"Error processing batch: {e}")
            await session.rollback()
            stats["errors"] += len(batch)
        
        return stats

    async def _get_existing_events(
        self, 
        session: AsyncSession, 
        event_ids: List[str]
    ) -> List[Event]:
        """Get existing events by IDs"""
        
        if not event_ids:
            return []
        
        query = select(Event).where(Event.id.in_(event_ids))
        result = await session.execute(query)
        return result.scalars().all()

    async def fetch_and_process_events(
        self,
        session: AsyncSession,
        max_events: int = 1000,
        progress_callback: Optional[Callable[[str, Dict[str, Any]], None]] = None,
        **filters
    ) -> Dict[str, Any]:
        """Complete ETL pipeline: fetch from PredictHQ and process"""
        
        start_time = datetime.now()
        
        try:
            # Update progress
            if progress_callback:
                progress_callback("starting", {"message": "Starting ETL process"})
            
            # Fetch events from PredictHQ
            if progress_callback:
                progress_callback("fetching", {"message": "Fetching events from PredictHQ"})
            
            raw_events = await predicthq_service.fetch_all_events_paginated(
                max_events=max_events,
                **filters
            )
            
            if not raw_events:
                return {
                    "status": "completed",
                    "message": "No events found",
                    "events_processed": 0,
                    "events_created": 0,
                    "events_updated": 0,
                    "processing_time": (datetime.now() - start_time).total_seconds()
                }
            
            # Process events
            if progress_callback:
                progress_callback("processing", {
                    "message": f"Processing {len(raw_events)} events",
                    "total_events": len(raw_events)
                })
            
            def update_progress(processed: int, total: int):
                if progress_callback:
                    progress_callback("processing", {
                        "message": f"Processed {processed}/{total} events",
                        "processed": processed,
                        "total": total
                    })
            
            stats = await self.process_events_batch(
                session, 
                raw_events,
                progress_callback=update_progress
            )
            
            # Final result
            processing_time = (datetime.now() - start_time).total_seconds()
            
            return {
                "status": "completed",
                "message": f"ETL completed successfully",
                "events_processed": stats["processed"],
                "events_created": stats["created"],
                "events_updated": stats["updated"],
                "events_errors": stats["errors"],
                "processing_time": processing_time
            }
            
        except Exception as e:
            logger.error(f"ETL pipeline error: {e}")
            processing_time = (datetime.now() - start_time).total_seconds()
            
            return {
                "status": "error",
                "message": f"ETL failed: {str(e)}",
                "events_processed": 0,
                "events_created": 0,
                "events_updated": 0,
                "processing_time": processing_time
            }


# Global instance
batch_processor = BatchProcessor()
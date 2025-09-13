import redis
import json
import logging
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
from app.core.config import settings

logger = logging.getLogger(__name__)


class RedisCacheService:
    def __init__(self):
        self.redis_client = redis.from_url(settings.redis_url, decode_responses=True)
        self.ttl_seconds = 24 * 60 * 60  # 24 hours
    
    def get_daily_cache_key(self, date: datetime = None) -> str:
        """Generate cache key based on date (YYYY-MM-DD format)"""
        if date is None:
            date = datetime.now(timezone.utc)
        
        date_str = date.strftime("%Y-%m-%d")
        return f"etl_events:{date_str}"
    
    async def get_cached_events(self, cache_key: str) -> Optional[List[Dict[str, Any]]]:
        """Get cached events for a specific cache key"""
        try:
            cached_data = self.redis_client.get(cache_key)
            if cached_data:
                events_data = json.loads(cached_data)
                logger.info(f"Retrieved {len(events_data.get('events', []))} events from cache key: {cache_key}")
                return events_data.get('events', [])
            return None
        except Exception as e:
            logger.error(f"Error retrieving from cache key {cache_key}: {e}")
            return None
    
    async def add_events_to_cache(self, cache_key: str, new_events: List[Dict[str, Any]]) -> bool:
        """Add new events to existing cache key or create new cache entry"""
        try:
            # Get existing events from cache
            existing_data = self.redis_client.get(cache_key)
            
            if existing_data:
                # Parse existing data
                cached_data = json.loads(existing_data)
                existing_events = cached_data.get('events', [])
                existing_event_ids = {event.get('id') for event in existing_events}
                
                # Add only new events (avoid duplicates)
                unique_new_events = [
                    event for event in new_events 
                    if event.get('id') not in existing_event_ids
                ]
                
                # Combine events
                all_events = existing_events + unique_new_events
                
                logger.info(f"Adding {len(unique_new_events)} new events to existing cache key: {cache_key}")
                logger.info(f"Total events in cache: {len(all_events)}")
                
            else:
                # First time caching for this key
                all_events = new_events
                logger.info(f"Creating new cache key {cache_key} with {len(all_events)} events")
            
            # Prepare cache data with metadata
            cache_data = {
                'events': all_events,
                'last_updated': datetime.now(timezone.utc).isoformat(),
                'total_events': len(all_events)
            }
            
            # Store in Redis with TTL
            self.redis_client.setex(
                cache_key, 
                self.ttl_seconds, 
                json.dumps(cache_data, default=str)
            )
            
            return True
            
        except Exception as e:
            logger.error(f"Error adding events to cache key {cache_key}: {e}")
            return False
    
    async def get_cache_info(self, cache_key: str) -> Dict[str, Any]:
        """Get information about a cache key"""
        try:
            # Check if key exists
            if not self.redis_client.exists(cache_key):
                return {"exists": False}
            
            # Get TTL
            ttl = self.redis_client.ttl(cache_key)
            
            # Get data size
            cached_data = self.redis_client.get(cache_key)
            if cached_data:
                data = json.loads(cached_data)
                return {
                    "exists": True,
                    "ttl_seconds": ttl,
                    "ttl_hours": round(ttl / 3600, 2),
                    "total_events": data.get('total_events', 0),
                    "last_updated": data.get('last_updated'),
                    "size_bytes": len(cached_data)
                }
            
            return {"exists": True, "ttl_seconds": ttl, "data": None}
            
        except Exception as e:
            logger.error(f"Error getting cache info for {cache_key}: {e}")
            return {"error": str(e)}
    
    async def clear_cache_key(self, cache_key: str) -> bool:
        """Clear a specific cache key"""
        try:
            deleted_count = self.redis_client.delete(cache_key)
            logger.info(f"Cleared cache key: {cache_key} (deleted: {deleted_count})")
            return deleted_count > 0
        except Exception as e:
            logger.error(f"Error clearing cache key {cache_key}: {e}")
            return False
    
    async def get_all_cache_keys(self, pattern: str = "etl_events:*") -> List[str]:
        """Get all cache keys matching pattern"""
        try:
            keys = self.redis_client.keys(pattern)
            return sorted(keys)
        except Exception as e:
            logger.error(f"Error getting cache keys: {e}")
            return []


# Global cache service instance
redis_cache = RedisCacheService()
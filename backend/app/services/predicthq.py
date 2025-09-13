import httpx
import asyncio
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)


class PredictHQService:
    def __init__(self):
        self.base_url = "https://api.predicthq.com/v1"
        self.headers = {
            "Authorization": f"Bearer {settings.predicthq_token}",
            "Accept": "application/json"
        }
        self.timeout = 30.0

    async def fetch_events(
        self, 
        limit: int = 100, 
        offset: int = 0,
        category: Optional[str] = None,
        location: Optional[str] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> Dict[str, Any]:
        """Fetch events from PredictHQ API"""
        
        params = {
            "limit": min(limit, 1000),  # API limit
            "offset": offset,
            "active": "true",
            "sort": "start"
        }
        
        # Add optional filters
        if category:
            params["category"] = category
        if location:
            params["location"] = location
        if start_date:
            params["start.gte"] = start_date
        if end_date:
            params["end.lte"] = end_date
        
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(
                    f"{self.base_url}/events/",
                    headers=self.headers,
                    params=params
                )
                response.raise_for_status()
                return response.json()
        
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error fetching events: {e.response.status_code} - {e.response.text}")
            raise
        except Exception as e:
            logger.error(f"Error fetching events from PredictHQ: {e}")
            raise

    async def fetch_all_events_paginated(
        self,
        max_events: int = 1000,
        **filters
    ) -> List[Dict[str, Any]]:
        """Fetch all events with pagination"""
        
        all_events = []
        offset = 0
        limit = min(100, max_events)  # Batch size
        
        while len(all_events) < max_events:
            try:
                response = await self.fetch_events(
                    limit=limit,
                    offset=offset,
                    **filters
                )
                
                events = response.get("results", [])
                if not events:
                    break
                
                all_events.extend(events)
                
                # Check if there are more events
                if len(events) < limit:
                    break
                
                offset += limit
                
                # Prevent infinite loops
                if offset > 10000:  # Reasonable limit
                    logger.warning("Reached offset limit, stopping pagination")
                    break
                
                # Rate limiting - be nice to the API
                await asyncio.sleep(0.1)
                
            except Exception as e:
                logger.error(f"Error in pagination at offset {offset}: {e}")
                break
        
        return all_events[:max_events]

    def parse_event_data(self, raw_event: Dict[str, Any]) -> Dict[str, Any]:
        """Parse raw event data from PredictHQ into our format"""
        
        # Extract location data safely
        location_data = raw_event.get("location", {})
        longitude = None
        latitude = None
        location_str = ""
        
        if isinstance(location_data, dict):
            # Handle GeoJSON format
            if "geometry" in location_data and location_data["geometry"]:
                coords = location_data["geometry"].get("coordinates", [])
                if len(coords) >= 2:
                    longitude = float(coords[0])
                    latitude = float(coords[1])
            
            # Handle properties for location string
            if "properties" in location_data:
                props = location_data["properties"]
                location_parts = []
                for key in ["name", "address", "locality", "region", "country"]:
                    if key in props and props[key]:
                        location_parts.append(str(props[key]))
                location_str = ", ".join(location_parts)
        
        # Parse dates safely
        start_date = None
        end_date = None
        
        if raw_event.get("start"):
            try:
                start_date = datetime.fromisoformat(raw_event["start"].replace("Z", "+00:00"))
            except (ValueError, TypeError):
                pass
        
        if raw_event.get("end"):
            try:
                end_date = datetime.fromisoformat(raw_event["end"].replace("Z", "+00:00"))
            except (ValueError, TypeError):
                pass
        
        # Parse updated timestamp
        updated_at = None
        if raw_event.get("updated"):
            try:
                updated_at = datetime.fromisoformat(raw_event["updated"].replace("Z", "+00:00"))
            except (ValueError, TypeError):
                pass
        
        return {
            "id": str(raw_event["id"]),
            "title": str(raw_event.get("title", "")).strip() or "Untitled Event",
            "description": str(raw_event.get("description", "")).strip(),
            "category": str(raw_event.get("category", "")).strip() or "other",
            "longitude": longitude,
            "latitude": latitude,
            "location": location_str,
            "start": start_date,
            "end": end_date,
            "predicthq_updated": updated_at or datetime.now(timezone.utc)
        }

    async def test_connection(self) -> bool:
        """Test connection to PredictHQ API"""
        try:
            response = await self.fetch_events(limit=1)
            return bool(response.get("results"))
        except Exception as e:
            logger.error(f"PredictHQ connection test failed: {e}")
            return False


# Global instance
predicthq_service = PredictHQService()
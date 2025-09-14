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
        limit = 100  # Batch size

        logger.info(f"Starting paginated fetch of up to {max_events} events from PredictHQ with limit {limit} per page and filters: {filters}")
        total_fetched = 0
        for page in range((max_events // limit) + 1):
            current_offset = page * limit
            logger.debug(f"Fetching events: page={page}, offset={current_offset}, limit={limit}")
            try:
                response = await self.fetch_events(
                    limit=limit,
                    offset=current_offset,
                    **filters
                )
                
                events = response.get("results", [])
                logger.info(f"Fetched {len(events)} events at offset {current_offset}")
                if not events:
                    logger.info(f"No more events returned at offset {current_offset}. Stopping pagination.")
                    break
                
                all_events.extend(events)
                total_fetched += len(events)
                
                # Check if there are more events
                if len(events) < limit:
                    logger.info(f"Received less than limit ({limit}) events at offset {current_offset}. Pagination complete.")
                    break

                # Rate limiting - be nice to the API
                await asyncio.sleep(0.1)

            except Exception as e:
                logger.error(f"Error in pagination at offset {current_offset}: {e}")
                break

        logger.info(f"Completed paginated fetch. Total events fetched: {total_fetched}")
        return all_events

    def parse_event_data(self, raw_event: Dict[str, Any]) -> Dict[str, Any]:
        """Parse raw event data from PredictHQ into our format"""
        
        # Extract location data safely
        geo_data = raw_event.get("geo", {})
        location_data = raw_event.get("location", [])
        longitude = float(location_data[0])
        latitude = float(location_data[1])
        
        location_str = geo_data.get("address", {}).get("formatted_address", "")
        city = geo_data.get("address", {}).get("locality", "")
        region = geo_data.get("address", {}).get("region", "")
        
        
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
            "description": str(raw_event.get("description", "")).replace("Sourced from predicthq.com", "").strip(),
            "category": str(raw_event.get("category", "")).strip() or "other",
            "longitude": longitude,
            "latitude": latitude,
            "location": location_str,
            "start": start_date,
            "end": end_date,
            "attendance": int(raw_event["phq_attendance"]) if "phq_attendance" in raw_event and raw_event["phq_attendance"] is not None else 0,
            "spend_amount": int(raw_event["predicted_event_spend"]) if "predicted_event_spend" in raw_event and raw_event["predicted_event_spend"] is not None else 0,
            "predicthq_updated": updated_at or datetime.now(timezone.utc),
            "city": city,
            "region": region,
        }

    async def test_connection(self) -> bool:
        """Test connection to PredictHQ API"""
        try:
            response = await self.fetch_events(limit=1)
            result = response.get("results")
            parsed_result = self.parse_event_data(result[0])
            print("result", result, "parsed result", parsed_result)
            return bool(result)
        except Exception as e:
            logger.error(f"PredictHQ connection test failed: {e}")
            return False


# Global instance
predicthq_service = PredictHQService()
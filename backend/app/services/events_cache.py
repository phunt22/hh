# app/services/events_cache.py
import json
import logging
from datetime import datetime, timezone, timedelta
from typing import List, Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc
from app.models.event import Event
from app.services.redis_cache import redis_cache
from app.schemas.event import EventResponse

logger = logging.getLogger(__name__)


class EventsCacheService:
    def __init__(self):
        self.min_cache_threshold = 100
        self.popular_events_ttl = 3600  # 1 hour in seconds
        self.busiest_cities_ttl = 3600

    async def get_cached_events_with_fallback(
        self,
        session: AsyncSession,
        skip: int = 0,
        limit: int = 100,
        category: Optional[str] = None,
        location_query: Optional[str] = None
    ) -> List[EventResponse]:
        """Get events from cache, fallback to DB if cache has < 100 events"""
        
        # Generate cache key for today
        # Get cached events for the last 2 days
        now = datetime.now(timezone.utc)
        cache_keys = [
            redis_cache.get_daily_cache_key(now),
            redis_cache.get_daily_cache_key(now - timedelta(days=1))
        ]
        cached_events = []
        for key in cache_keys:
            events = await redis_cache.get_cached_events(key)
            if events:
                cached_events.extend(events)

        if cached_events and len(cached_events) >= self.min_cache_threshold:
            logger.info(f"Using cache with {len(cached_events)} events")
            
            # Filter cached events if needed
            filtered_events = self._filter_cached_events(
                cached_events, category, location_query
            )
            
            # Apply pagination
            paginated_events = filtered_events[skip:skip + limit]
            
            # Convert to EventResponse objects
            return [self._dict_to_event_response(event) for event in paginated_events]
        
        else:
            logger.info(f"Cache has {len(cached_events) if cached_events else 0} events, fetching from DB")
            
            # Fallback to database
            db_events = await self._fetch_from_database(
                session, skip, limit, category, location_query
            )
            
            # Update cache with fresh data from DB
            if db_events:
                await self._update_cache_from_db_events(cache_keys[0], db_events)
            
            return db_events

    def _filter_cached_events(
        self, 
        events: List[Dict[str, Any]], 
        category: Optional[str] = None,
        location_query: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Filter cached events by category and location"""
        
        filtered = events
        
        if category:
            filtered = [e for e in filtered if e.get('category') == category]
        
        if location_query:
            location_lower = location_query.lower()
            filtered = [
                e for e in filtered 
                if location_lower in str(e.get('location', '')).lower()
            ]
        
        # Sort by start date (newest first)
        filtered.sort(
            key=lambda x: x.get('start', ''), 
            reverse=True
        )
        
        return filtered

    def _dict_to_event_response(self, event_dict: Dict[str, Any]) -> EventResponse:
        """Convert dictionary to EventResponse"""
        
        # Parse dates
        start_date = None
        end_date = None
        created_at = datetime.now(timezone.utc)
        updated_at = datetime.now(timezone.utc)
        
        if event_dict.get('start'):
            try:
                start_date = datetime.fromisoformat(event_dict['start'].replace('Z', '+00:00'))
            except:
                pass
        
        if event_dict.get('end'):
            try:
                end_date = datetime.fromisoformat(event_dict['end'].replace('Z', '+00:00'))
            except:
                pass
        
        return EventResponse(
            id=event_dict.get('id', ''),
            title=event_dict.get('title', ''),
            description=event_dict.get('description', ''),
            category=event_dict.get('category', ''),
            longitude=event_dict.get('longitude'),
            latitude=event_dict.get('latitude'),
            start=start_date,
            end=end_date,
            location=event_dict.get('location', ''),
            related_event_ids=event_dict.get('related_event_ids', ''),
            created_at=created_at,
            updated_at=updated_at,
            attendance=event_dict.get('attendance', 0),
            spend_amount=event_dict.get('spend_amount', 0),
            city=event_dict.get('city', ''),
            region=event_dict.get('region', ''),

        )

    async def _fetch_from_database(
        self,
        session: AsyncSession,
        skip: int,
        limit: int,
        category: Optional[str] = None,
        location_query: Optional[str] = None
    ) -> List[EventResponse]:
        """Fetch events from PostgreSQL database"""
        
        query = select(Event)
        
        # Add filters
        if category:
            query = query.where(Event.category == category)
        
        if location_query:
            query = query.where(Event.location.ilike(f"%{location_query}%"))
        
        # Add ordering and pagination
        query = query.order_by(Event.start.desc()).offset(skip).limit(limit)
        
        result = await session.execute(query)
        events = result.scalars().all()
        
        return [EventResponse.from_orm(event) for event in events]

    async def _update_cache_from_db_events(
        self, 
        cache_key: str, 
        db_events: List[EventResponse]
    ):
        """Update cache with events from database"""
        
        try:
            # Convert EventResponse objects to dictionaries
            events_data = []
            for event in db_events:
                event_dict = {
                    'id': event.id,
                    'title': event.title,
                    'description': event.description,
                    'category': event.category,
                    'longitude': event.longitude,
                    'latitude': event.latitude,
                    'start': event.start.isoformat() if event.start else None,
                    'end': event.end.isoformat() if event.end else None,
                    'location': event.location,
                    'related_event_ids': event.related_event_ids
                }
                events_data.append(event_dict)
            
            # Update cache
            await redis_cache.add_events_to_cache(cache_key, events_data)
            logger.info(f"Updated cache {cache_key} with {len(events_data)} events from DB")
            
        except Exception as e:
            logger.error(f"Error updating cache from DB events: {e}")

    async def get_popular_events_for_day(
        self, 
        session: AsyncSession, 
        date: Optional[datetime] = None
    ) -> List[Dict[str, Any]]:
        """Get top 10 most popular events by attendance for a specific day"""
        
        if date is None:
            date = datetime.now(timezone.utc)
        
        # Generate cache key for popular events
        date_str = date.strftime("%Y-%m-%d")
        cache_key = f"popular_events:{date_str}"
        
        # Check cache first
        try:
            cached_data = redis_cache.redis_client.get(cache_key)
            if cached_data:
                popular_events = json.loads(cached_data)
                logger.info(f"Retrieved {len(popular_events)} popular events from cache")
                return popular_events
        except Exception as e:
            logger.error(f"Error retrieving popular events from cache: {e}")
        
        # Fetch from database if not in cache
        popular_events = await self._fetch_popular_events_from_db(session, date)
        
        # Cache the results for 1 hour
        try:
            redis_cache.redis_client.setex(
                cache_key,
                self.popular_events_ttl,
                json.dumps(popular_events, default=str)
            )
            logger.info(f"Cached {len(popular_events)} popular events for {date_str}")
        except Exception as e:
            logger.error(f"Error caching popular events: {e}")
        
        return popular_events

    async def _fetch_popular_events_from_db(
        self, 
        session: AsyncSession, 
        date: datetime
    ) -> List[Dict[str, Any]]:
        """Fetch popular events from database by attendance"""
        
        # Date range for the day
        start_of_day = date.replace(hour=0, minute=0, second=0, microsecond=0)
        end_of_day = start_of_day + timedelta(days=1)
        
        # Query events for the specific day
        # Note: Since we don't have an attendance field in the current model,
        # we'll simulate popularity by using a combination of factors
        query = (
            select(Event)
            .where(
                Event.start >= start_of_day,
                Event.start < end_of_day
            )
            .order_by(
                # Simulate popularity ranking by:
                # 1. Events with longer duration (end - start)
                # 2. Events with more complete information (title length)
                # 3. Events with embeddings (processed events)
                func.extract('epoch', Event.end - Event.start).desc(),
                func.length(Event.title).desc(),
                (Event.embeddings.is_not(None)).desc()
            )
            .limit(10)
        )
        
        result = await session.execute(query)
        events = result.scalars().all()
        
        # Convert to dictionary format with simulated attendance
        popular_events = []
        for i, event in enumerate(events):
            # Simulate attendance based on ranking and event characteristics
            base_attendance = 1000 - (i * 100)  # Decreasing by rank
            title_bonus = min(len(event.title) * 5, 200)  # Bonus for longer titles
            duration_bonus = 0
            
            if event.start and event.end:
                duration_hours = (event.end - event.start).total_seconds() / 3600
                duration_bonus = min(int(duration_hours * 50), 300)
            
            simulated_attendance = base_attendance + title_bonus + duration_bonus
            
            event_data = {
                'id': event.id,
                'title': event.title,
                'description': event.description,
                'category': event.category,
                'location': event.location,
                'start': event.start.isoformat() if event.start else None,
                'end': event.end.isoformat() if event.end else None,
                'attendance': simulated_attendance,  # Simulated attendance
                'popularity_rank': i + 1
            }
            popular_events.append(event_data)
        
        logger.info(f"Fetched {len(popular_events)} popular events from DB for {date.strftime('%Y-%m-%d')}")
        return popular_events

    async def get_busiest_cities(
        self, 
        session: AsyncSession, 
        time_window_days: int = 7, 
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Get the busiest cities based on event attendance within a specified time window.
        Results are cached.
        """
        logger.info(f"get_busiest_cities called with time_window_days={time_window_days}, limit={limit}")

        end_time = datetime.now(timezone.utc)
        start_time = end_time - timedelta(days=time_window_days)
        logger.debug(f"Time window: {start_time.isoformat()} to {end_time.isoformat()}")

        cache_key = f"busiest_cities:{time_window_days}:{limit}"
        logger.debug(f"Cache key generated: {cache_key}")

        # Try to get from cache first
        try:
            logger.debug("Attempting to retrieve busiest cities from cache")
            cached_data = redis_cache.redis_client.get(cache_key)
            if cached_data:
                busiest_cities = json.loads(cached_data)
                logger.info(f"Retrieved {len(busiest_cities)} busiest cities from cache (key={cache_key})")
                return busiest_cities
            else:
                logger.info("No cached data found for busiest cities")
        except Exception as e:
            logger.error(f"Error retrieving busiest cities from cache: {e}")

        # If not in cache, fetch from database
        logger.info("Fetching busiest cities from database")
        # We need to extract the city name from the 'location' field
        # A simple approach: take everything before the first comma, or the whole string

        query = (
            select(
                Event.region.label('region'),
                func.sum(Event.attendance).label('total_attendance')
            )
            .where(
                Event.start >= start_time,
                Event.start <= end_time,
                Event.attendance.is_not(None),
                Event.region.is_not(None),
                Event.region != ""
            )
            .group_by(Event.region)
            .order_by(desc(func.sum(Event.attendance)))
            .limit(limit)
        )
        
        logger.debug("Executing busiest cities query")
        result = await session.execute(query)
        busiest_cities_data = []

        for idx, row in enumerate(result):
            # For each busiest city, fetch its top 5 events
            city_name = row.region.strip() if row.region else ""
            if not city_name:
                logger.warning(f"Skipping row {idx+1} with empty city name")
                continue
            logger.debug(f"Processing city {idx+1}: '{city_name}' with total_attendance={row.total_attendance}")

            top_events_for_city = await self._get_top_events_for_city(
                session=session,
                city_name=city_name,
                start_time=start_time,
                end_time=end_time,
                event_limit=5  # Top 5 events per city
            )
            logger.debug(f"Fetched {len(top_events_for_city)} top events for city '{city_name}'")

            # Get event counts for the last 24 hours in 3-hour intervals
            event_counts_24h = await self._get_event_counts_by_interval(
                session=session,
                city_name=city_name,
                end_time=end_time,
                hours_window=24,
                interval_hours=3
            )
            logger.debug(f"Fetched {len(event_counts_24h)} 3-hour interval event counts for city '{city_name}'")


            busiest_cities_data.append({
                "city": city_name, # .strip() to remove leading/trailing whitespace
                "total_attendance": row.total_attendance,
                "top_events": [event.dict() for event in top_events_for_city], # Convert EventResponse to dict
                "event_counts": event_counts_24h,
            })

        # Cache the results
        try:
            logger.debug(f"Caching {len(busiest_cities_data)} busiest cities with key={cache_key} and TTL={self.busiest_cities_ttl}")
            redis_cache.redis_client.setex(
                cache_key,
                self.busiest_cities_ttl,
                json.dumps(busiest_cities_data, default=str)
            )
            logger.info(f"Cached {len(busiest_cities_data)} busiest cities for {time_window_days} days (key={cache_key})")
        except Exception as e:
            logger.error(f"Error caching busiest cities: {e}")

        logger.info(f"Returning {len(busiest_cities_data)} busiest cities from DB")
        return busiest_cities_data

    async def _get_top_events_for_city(
        self,
        session: AsyncSession,
        city_name: str,
        start_time: datetime,
        end_time: datetime,
        event_limit: int
    ) -> List[EventResponse]:
        """
        Helper function to fetch top events for a given city within a time window.
        """
        logger.debug(
            f"Fetching top {event_limit} events for city '{city_name}' "
            f"between {start_time} and {end_time}"
        )

        # Try multiple approaches to match the city
        # First try exact city match
        query = (
            select(Event)
            .where(
                Event.region == city_name,
                Event.start >= start_time,
                Event.start <= end_time
            )
            .order_by(
                desc(Event.attendance),  # Events with attendance first
                desc(Event.start)        # Then by start time
            )
            .limit(event_limit)
        )
        
        try:
            result = await session.execute(query)
            events = result.scalars().all()
            
            # If no events found with exact city match, try location-based matching
            if not events:
                logger.debug(f"No events found for exact city '{city_name}', trying location-based matching")
                location_query = (
                    select(Event)
                    .where(
                        Event.location.ilike(f"%{city_name}%"),
                        Event.start >= start_time,
                        Event.start <= end_time
                    )
                    .order_by(
                        desc(Event.attendance),
                        desc(Event.start)
                    )
                    .limit(event_limit)
                )
                result = await session.execute(location_query)
                events = result.scalars().all()
                logger.debug(f"Found {len(events)} events using location-based matching for '{city_name}'")
            
        except Exception as e:
            logger.error(f"Error fetching top events for city '{city_name}': {e}")
            events = []
        
        logger.debug(
            f"Found {len(events)} events for city '{city_name}' "
            f"in the specified time window"
        )
        return [EventResponse.from_orm(event) for event in events]

    async def _get_event_counts_by_interval(
        self,
        session: AsyncSession,
        city_name: str,
        end_time: datetime,
        hours_window: int = 24,
        interval_hours: int = 3
    ) -> List[Dict[str, Any]]:
        """
        Get the count of events for a given city in specified time intervals
        over a rolling window (e.g., every 3 hours for the last 24 hours).
        """

        logger.debug(
            f"Fetching event counts for city '{city_name}'"
            f"for the last {hours_window} hours in {interval_hours}-hour intervals"
        )
        
        event_counts = []
        now = end_time.replace(minute=0, second=0, microsecond=0) # Round to nearest hour
        
        # Calculate event counts for the last `hours_window` hours in `interval_hours` chunks
        for i in range(0, hours_window, interval_hours):
            interval_end = now - timedelta(hours=i)
            interval_start = interval_end - timedelta(hours=interval_hours)
            
            # Efficiently query event count for the interval
            query = (
                select(func.count(Event.id))
                .where(
                    Event.region == city_name,
                    Event.start >= interval_start,
                    Event.start < interval_end
                )
            )
            
            try:
                result = await session.execute(query)
                count = result.scalar_one()
                event_counts.append({
                    "interval_end": interval_end.isoformat(),
                    "interval_start": interval_start.isoformat(),
                    "event_count": count
                })
            except Exception as e:
                logger.error(
                    f"Error fetching event count for city '{city_name}' "
                    f"in interval {interval_start} to {interval_end}: {e}"
                )
                event_counts.append({
                    "interval_end": interval_end.isoformat(),
                    "interval_start": interval_start.isoformat(),
                    "event_count": 0
                })
        
        # Sort by interval_start to have oldest first
        event_counts.sort(key=lambda x: x['interval_start'])
        logger.debug(f"Generated {len(event_counts)} event counts for city '{city_name}'")
        return event_counts


# Global instance
events_cache_service = EventsCacheService()
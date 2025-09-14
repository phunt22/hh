from pydantic import BaseModel
from typing import Any, Dict, Optional, List
from datetime import datetime


class EventBase(BaseModel):
    title: str
    description: Optional[str] = ""
    category: str
    longitude: Optional[float] = None
    latitude: Optional[float] = None
    start: Optional[datetime] = None
    end: Optional[datetime] = None
    location: Optional[str] = ""
    attendance: Optional[int] = None
    city: Optional[str] = None
    region: Optional[str] = None
    spend_amount: Optional[int] = None


class EventCreate(EventBase):
    id: str


class EventUpdate(EventBase):
    title: Optional[str] = None
    category: Optional[str] = None


class EventResponse(EventBase):
    id: str
    created_at: datetime
    updated_at: datetime
    related_event_ids: Optional[str] = ""

    class Config:
        from_attributes = True


class SimilarEvent(BaseModel):
    event: EventResponse
    similarity_score: float
    relationship_type: str = "similar"


class SimilaritySearchRequest(BaseModel):
    query_text: Optional[str] = None
    event_id: Optional[str] = None
    limit: int = 10
    min_similarity: float = 0.7
    include_related: bool = True


class SimilaritySearchResponse(BaseModel):
    query_event: Optional[EventResponse] = None
    similar_events: List[Dict[str, Any]]
    total_found: int
    audio_response: Optional[str] = None


class ETLStatus(BaseModel):
    status: str
    message: str
    events_processed: int = 0
    events_created: int = 0
    events_updated: int = 0
    processing_time: Optional[float] = None

class TopEvent(EventResponse):
    attendance: Optional[int] = None
    popularity_rank: Optional[int] = None

class EventCount(BaseModel):
    interval_end: datetime
    interval_start: datetime
    event_count: int

class BusiestCity(BaseModel):
    city: str
    total_attendance: int
    top_events: List[TopEvent] = []
    event_counts: List[EventCount] = []
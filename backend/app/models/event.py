from sqlmodel import SQLModel, Field, Column
from sqlalchemy import DateTime, Integer, Text, Index
from sqlalchemy.dialects.postgresql import ARRAY
from pgvector.sqlalchemy import Vector
from typing import Optional, List
from datetime import datetime


class Event(SQLModel, table=True):
    __tablename__ = "events"
    
    id: str = Field(primary_key=True)
    title: str = Field(index=True)
    description: Optional[str] = Field(sa_column=Column(Text), default="")
    category: str = Field(index=True)
    longitude: Optional[float] = None
    latitude: Optional[float] = None
    
    # Proper embedding column using pgvector
    embeddings: Optional[List[float]] = Field(
        sa_column=Column(Vector(1536)), 
        default=None
    )
    
    start: Optional[datetime] = Field(sa_column=Column(DateTime(timezone=True)), default=None)
    end: Optional[datetime] = Field(sa_column=Column(DateTime(timezone=True)), default=None)
    city: Optional[str] = Field(default="")
    region: Optional[str] = Field(default="")
    location: Optional[str] = Field(default="")
    attendance: Optional[int] = Field(sa_column=Column(Integer))
    spend_amount: Optional[int] = Field(sa_column=Column(Integer))
      
    # Additional fields for better event tracking
    predicthq_updated: Optional[datetime] = Field(sa_column=Column(DateTime(timezone=True)), default=None)
    created_at: datetime = Field(sa_column=Column(DateTime(timezone=True)), default_factory=datetime.utcnow)
    updated_at: datetime = Field(sa_column=Column(DateTime(timezone=True)), default_factory=datetime.utcnow)
    
    # Related events (comma-separated IDs for simplicity)
    related_event_ids: Optional[str] = Field(default="")
    indexed: bool = Field(default=False, nullable=True)
    
    class Config:
        arbitrary_types_allowed = True

    # Add indexes for better query performance
    __table_args__ = (
        Index("idx_events_location", "latitude", "longitude"),
        Index("idx_events_category_start", "category", "start"),
        Index("idx_events_embeddings_vector", "embeddings", postgresql_using="ivfflat"),
    )


class EventSimilarity(SQLModel, table=True):
    __tablename__ = "event_similarities"
    
    id: int = Field(primary_key=True)
    event_id_1: str = Field(foreign_key="events.id", index=True)
    event_id_2: str = Field(foreign_key="events.id", index=True)
    similarity_score: float
    relationship_type: str = Field(default="similar")  # similar, related, duplicate
    created_at: datetime = Field(sa_column=Column(DateTime(timezone=True)), default_factory=datetime.utcnow)
    
    class Config:
        arbitrary_types_allowed = True
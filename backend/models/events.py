from sqlmodel import SQLModel, Field, create_engine, Session
from typing import List, Optional


class Event(SQLModel, table=True):
    id: str = Field(primary_key=True)
    title: str
    description: str
    category: str
    longitude: float
    latitude: float
    embeddings: Optional[np.ndarray] = Field(sa_column_kwargs={"type_": "VECTOR(1536)"})
    start: Optional[str]
    end: Optional[str]
    location: Optional[str]
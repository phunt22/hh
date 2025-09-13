import os
import requests
import openai
from fastapi import FastAPI, BackgroundTasks
from sqlmodel import SQLModel, Field, create_engine, Session
from typing import Optional
import numpy as np

# --- Models ---


# --- FastAPI setup ---
app = FastAPI()
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql+psycopg2://user:pass@localhost/events_db")
engine = create_engine(DATABASE_URL)

def create_db_and_tables():
    SQLModel.metadata.create_all(engine)

@app.on_event("startup")
def on_startup():
    create_db_and_tables()

# --- Utility: Generate Embedding from Text ---
def embed(text: str) -> np.ndarray:
    response = openai.Embedding.create(model="text-embedding-ada-002", input=text)
    return np.array(response["data"]["embedding"])

# --- ETL Task ---
def fetch_and_store_events():
    token = os.getenv("PREDICTHQ_TOKEN")
    headers = {"Authorization": f"Bearer {token}"}
    url = "https://api.predicthq.com/v1/events"
    params = {"limit": 100, "active": True}
    r = requests.get(url, headers=headers, params=params)
    for e in r.json()["results"]:
        text = f"{e.get('title','')} {e.get('description','')}"
        emb = embed(text)
        event_obj = Event(
            id=e["id"],
            title=e.get("title", ""),
            description=e.get("description", ""),
            category=e.get("category", ""),
            longitude=e["location"][21] if "location" in e else None,
            latitude=e["location"] if "location" in e else None,
            embeddings=emb,
            start=e.get("start", ""),
            end=e.get("end", ""),
            location=str(e.get("location", ""))
        )
        with Session(engine) as session:
            session.merge(event_obj)
            session.commit()


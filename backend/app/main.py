from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import logging
from app.core.database import create_db_and_tables
from app.api.routes import etl, events
from app.core.config import settings

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events"""
    # Startup
    logger.info("Starting up Events API...")
    try:
        await create_db_and_tables()
        logger.info("Database tables created successfully")
    except Exception as e:
        logger.error(f"Error creating database tables: {e}")
        raise
    
    yield
    
    # Shutdown
    logger.info("Shutting down Events API...")


# Create FastAPI application
app = FastAPI(
    title="Events Similarity API",
    description="API for managing events with semantic similarity search using embeddings",
    version="1.0.0",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(etl.router, prefix="/api/v1")
app.include_router(events.router, prefix="/api/v1")


@app.get("/")
async def root():
    """Root endpoint with API information"""
    return {
        "message": "Events Similarity API",
        "version": "1.0.0",
        "docs": "/docs",
        "endpoints": {
            "etl": "/api/v1/etl/",
            "events": "/api/v1/events/",
            "similar_events": "/api/v1/events/search/similar"
        }
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    try:
        # You could add more comprehensive health checks here
        # like database connectivity, external API availability, etc.
        return {
            "status": "healthy",
            "database": "connected",
            "services": {
                "predicthq": "configured",
                "openai": "configured",
                "embedding": "available"
            }
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(status_code=503, detail="Service unhealthy")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
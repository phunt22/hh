# Events Similarity API

A sophisticated FastAPI application for fetching, processing, and finding semantically similar events using embeddings and vector similarity search.

## 🚀 Features

- **ETL Pipeline**: Efficient batch processing from PredictHQ API
- **Vector Similarity Search**: Using pgvector for fast similarity queries
- **Semantic Embeddings**: OpenAI embeddings for event content
- **Related Events**: Track explicitly related events
- **Background Processing**: Async processing with status tracking
- **Comprehensive API**: Full CRUD operations with advanced search

## 📁 Project Structure

```
events_api/
├── app/
│   ├── main.py                 # FastAPI application
│   ├── core/
│   │   ├── config.py          # Configuration management
│   │   └── database.py        # Database setup and session management
│   ├── models/
│   │   └── event.py           # SQLModel event models
│   ├── schemas/
│   │   └── event.py           # Pydantic schemas for API
│   ├── services/
│   │   ├── embedding.py       # OpenAI embedding service
│   │   ├── predicthq.py      # PredictHQ API integration
│   │   └── similarity.py     # Similarity calculation service
│   ├── api/routes/
│   │   ├── etl.py            # ETL endpoints
│   │   └── events.py         # Events CRUD and search endpoints
│   └── utils/
│       └── batch_processing.py # Batch processing utilities
├── requirements.txt
├── docker-compose.yml
├── Dockerfile
└── .env
```

## 🛠 Setup and Installation

### Prerequisites

- Python 3.11+
- PostgreSQL with pgvector extension
- Redis (optional, for background tasks)
- Docker and Docker Compose (recommended)

### Environment Variables

Create a `.env` file:

```bash
DATABASE_URL=postgresql+asyncpg://user:password@localhost:5432/events_db
PREDICTHQ_TOKEN=your_predicthq_token_here
OPENAI_API_KEY=your_openai_api_key_here
REDIS_URL=redis://localhost:6379/0
BATCH_SIZE=50
MAX_WORKERS=4
```

### Option 1: Docker Deployment (Recommended)

```bash
# Clone and setup
git clone <repository>
cd events_api

# Start services
docker-compose up -d

# Check logs
docker-compose logs -f app
```

### Option 2: Local Development

```bash
# Install dependencies
pip install -r requirements.txt

# Setup PostgreSQL with pgvector
# Install pgvector extension in your database
CREATE EXTENSION IF NOT EXISTS vector;

# Run the application
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

## 📊 Database Schema

### Events Table
```sql
CREATE TABLE events (
    id VARCHAR PRIMARY KEY,
    title VARCHAR NOT NULL,
    description TEXT,
    category VARCHAR,
    longitude FLOAT,
    latitude FLOAT,
    embeddings VECTOR(1536),  -- pgvector column
    start TIMESTAMP WITH TIME ZONE,
    end TIMESTAMP WITH TIME ZONE,
    location VARCHAR,
    predicthq_updated TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    related_event_ids VARCHAR
);
```

### Event Similarities Table
```sql
CREATE TABLE event_similarities (
    id SERIAL PRIMARY KEY,
    event_id_1 VARCHAR REFERENCES events(id),
    event_id_2 VARCHAR REFERENCES events(id),
    similarity_score FLOAT,
    relationship_type VARCHAR DEFAULT 'similar',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

## 🔄 Usage Guide

### 1. Running ETL Pipeline

```python
# Trigger ETL process
import httpx
import asyncio

async def run_etl():
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "http://localhost:8000/api/v1/etl/trigger",
            params={
                "max_events": 1000,
                "category": "sports",
                "calculate_similarities": True
            }
        )
        print(response.json())

asyncio.run(run_etl())
```

### 2. Similarity Search

#### By Text Query
```bash
curl -X POST "http://localhost:8000/api/v1/events/search/similar" \
  -H "Content-Type: application/json" \
  -d '{
    "query_text": "basketball championship game",
    "limit": 10,
    "min_similarity": 0.7
  }'
```

#### By Event ID
```bash
curl "http://localhost:8000/api/v1/events/{event_id}/similar?limit=5&min_similarity=0.8"
```

### 3. Regular Search and Filtering

```bash
# Get events with filters
curl "http://localhost:8000/api/v1/events/?category=sports&location_query=New York&limit=20"

# Get event statistics
curl "http://localhost:8000/api/v1/events/stats/summary"
```

## 🔍 API Endpoints

### ETL Operations
- `POST /api/v1/etl/trigger` - Start ETL process
- `GET /api/v1/etl/status/{job_id}` - Check ETL status
- `GET /api/v1/etl/test-connection` - Test PredictHQ connection
- `POST /api/v1/etl/calculate-similarities` - Calculate similarities

### Event Operations
- `GET /api/v1/events/` - List events (with filters)
- `GET /api/v1/events/{event_id}` - Get specific event
- `POST /api/v1/events/search/similar` - Semantic similarity search
- `GET /api/v1/events/{event_id}/similar` - Find similar events
- `GET /api/v1/events/categories/list` - Get categories
- `GET /api/v1/events/stats/summary` - Get statistics

### System
- `GET /` - API information
- `GET /health` - Health check
- `GET /docs` - Interactive documentation

## ⚡ Performance Optimizations

### 1. Database Indexes
- Vector similarity index using IVFFlat
- Composite indexes on frequently queried columns
- Category and date-based indexes

### 2. Batch Processing
- Configurable batch sizes for ETL
- Async processing with proper error handling
- Memory-efficient embedding generation

### 3. Caching Strategy
- Database connection pooling
- Query result caching (can be extended with Redis)

## 🔧 Configuration

### Key Settings in `app/core/config.py`:

```python
class Settings(BaseSettings):
    database_url: str
    predicthq_token: str
    openai_api_key: str
    batch_size: int = 50
    max_workers: int = 4
    embedding_model: str = "text-embedding-ada-002"
    embedding_dimension: int = 1536
```

## 🎯 Similarity Search Approaches

### 1. Vector Similarity (Primary)
Uses pgvector for fast cosine similarity queries:
```sql
SELECT *, cosine_similarity(embeddings, $1) as similarity
FROM events
WHERE cosine_similarity(embeddings, $1) >= 0.7
ORDER BY similarity DESC;
```

### 2. Explicit Relations
Events can have `related_event_ids` field for manually curated relationships.

### 3. Stored Similarities
Pre-calculated similarities stored in `event_similarities` table for complex relationships.

## 🚦 Monitoring and Health Checks

### Health Check Endpoint
```bash
curl http://localhost:8000/health
```

### ETL Status Monitoring
```python
# Check ETL job status
job_status = await check_etl_status(job_id)
print(f"Status: {job_status['status']}")
print(f"Processed: {job_status['events_processed']}")
```

## 🔒 Security Considerations

- API keys stored in environment variables
- Database connection with proper authentication  
- CORS configuration for production
- Input validation on all endpoints
- Rate limiting (can be added with Redis)

## 📈 Scaling Considerations

### Horizontal Scaling
- Stateless API design
- Background task processing with Celery
- Database read replicas for queries

### Vertical Scaling  
- Adjustable batch sizes
- Connection pooling
- Vector index optimization

## 🐛 Troubleshooting

### Common Issues

1. **pgvector Extension Missing**
   ```sql
   CREATE EXTENSION IF NOT EXISTS vector;
   ```

2. **OpenAI Rate Limits**
   - Reduce batch size
   - Add delays between requests

3. **Memory Issues with Large Batches**
   - Reduce `BATCH_SIZE` in config
   - Monitor memory usage

### Logs and Debugging

```bash
# Check application logs
docker-compose logs -f app

# Check database logs  
docker-compose logs -f db

# Enable debug logging
export LOG_LEVEL=DEBUG
```

## 📝 Development

### Running Tests
```bash
# Install test dependencies
pip install pytest pytest-asyncio httpx

# Run tests
pytest tests/
```

### Adding New Features
1. Update models in `app/models/`
2. Add schemas in `app/schemas/`  
3. Implement service logic in `app/services/`
4. Add API endpoints in `app/api/routes/`
5. Update tests

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License.
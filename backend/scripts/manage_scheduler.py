import asyncio
import httpx
import sys
from datetime import datetime, timedelta, timezone


async def trigger_etl_now():
    """Trigger ETL for the last hour"""
    end_time = datetime.now(timezone.utc)
    start_time = end_time - timedelta(hours=1)
    
    params = {
        "max_events": 500,
        "start_date": start_time.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "end_date": end_time.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "calculate_similarities": True
    }
    
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "http://localhost:8000/api/v1/etl/trigger",
            params=params
        )
        result = response.json()
        print(f"ETL Result: {result}")


async def check_etl_status(job_id: str):
    """Check ETL job status"""
    async with httpx.AsyncClient() as client:
        response = await client.get(f"http://localhost:8000/api/v1/etl/status/{job_id}")
        result = response.json()
        print(f"ETL Status: {result}")


async def test_connection():
    """Test PredictHQ connection"""
    async with httpx.AsyncClient() as client:
        response = await client.get("http://localhost:8000/api/v1/etl/test-connection")
        result = response.json()
        print(f"Connection Test: {result}")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python manage_scheduler.py trigger  # Trigger ETL now")
        print("  python manage_scheduler.py status <job_id>  # Check status")
        print("  python manage_scheduler.py test  # Test connection")
        sys.exit(1)
    
    command = sys.argv[1]
    
    if command == "trigger":
        asyncio.run(trigger_etl_now())
    elif command == "status" and len(sys.argv) > 2:
        asyncio.run(check_etl_status(sys.argv[2]))
    elif command == "test":
        asyncio.run(test_connection())
    else:
        print(f"Unknown command: {command}")
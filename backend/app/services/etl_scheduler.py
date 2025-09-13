import asyncio
import httpx
import logging
from datetime import datetime, timedelta, timezone
from typing import Optional

from app.core.config import settings

logger = logging.getLogger(__name__)


class ETLScheduler:
    def __init__(self, base_url: str = settings.api_base_url):
        self.base_url = base_url
        self.is_running = False
        self.current_task: Optional[asyncio.Task] = None
        
    async def start_hourly_etl(self):
        """Start the hourly ETL scheduler"""
        if self.is_running:
            logger.warning("ETL scheduler is already running")
            return
            
        self.is_running = True
        logger.info("🚀 Starting hourly ETL scheduler")
        
        self.current_task = asyncio.create_task(self._run_hourly_loop())
        return self.current_task
    
    async def stop_hourly_etl(self):
        """Stop the hourly ETL scheduler"""
        if not self.is_running:
            return
            
        logger.info("🛑 Stopping ETL scheduler...")
        self.is_running = False
        
        if self.current_task:
            self.current_task.cancel()
            try:
                await self.current_task
            except asyncio.CancelledError:
                pass
    
    async def _run_hourly_loop(self):
        """Run ETL every hour with 1-hour time windows"""
        
        while self.is_running:
            try:
                # Calculate 1-hour time window ending now
                end_time = datetime.now(timezone.utc)
                start_time = end_time - timedelta(hours=1)
                
                logger.info(f"⏰ Starting ETL for window: {start_time.strftime('%Y-%m-%d %H:%M')} to {end_time.strftime('%H:%M')}")
                
                # Call the existing ETL trigger endpoint
                await self._trigger_etl_via_api(start_time, end_time)
                
            except Exception as e:
                logger.error(f"❌ ETL run failed: {e}")
            
            # Wait 1 hour before next run
            if self.is_running:
                logger.info("⏱️ Waiting 1 hour for next ETL run...")
                await asyncio.sleep(3600)  # 1 hour = 3600 seconds
    
    async def _trigger_etl_via_api(self, start_time: datetime, end_time: datetime):
        """Trigger ETL using the existing REST API"""
        
        # Format times for API
        start_date = start_time.strftime("%Y-%m-%dT%H:%M:%SZ")
        end_date = end_time.strftime("%Y-%m-%dT%H:%M:%SZ")
        
        params = {
            "max_events": 500,
            "start_date": start_date,
            "end_date": end_date,
            "calculate_similarities": True
        }
        
        try:
            async with httpx.AsyncClient(timeout=300.0) as client:  # 5 minute timeout
                # Trigger ETL
                response = await client.post(
                    f"{self.base_url}/api/v1/etl/trigger",
                    params=params
                )
                response.raise_for_status()
                
                result = response.json()
                logger.info(f"✅ ETL triggered successfully: {result.get('message', '')}")
                
                # Wait a bit then check status
                await asyncio.sleep(10)
                
                # Check ETL status (if job_id is returned)
                if "job_id" in str(result):
                    await self._monitor_etl_job(result)
                
        except Exception as e:
            logger.error(f"❌ Failed to trigger ETL via API: {e}")
    
    async def _monitor_etl_job(self, trigger_result: dict):
        """Monitor ETL job status"""
        # This is optional - just log that ETL was triggered
        # In a real implementation, you might want to extract job_id and monitor
        logger.info(f"📊 ETL job monitoring: {trigger_result}")


# Global scheduler instance
etl_scheduler = ETLScheduler()
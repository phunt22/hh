import asyncio
import httpx
import logging
from datetime import datetime, timezone
from typing import Optional
from app.core.config import settings

logger = logging.getLogger(__name__)


class PineconeSyncScheduler:
    def __init__(self, base_url: str = settings.api_base_url):
        self.base_url = base_url
        self.is_running = False
        self.current_task: Optional[asyncio.Task] = None
        self.sync_count = 0
        self.error_count = 0
        
    async def start_periodic_sync(self, interval_minutes: int = 30):
        """Start periodic Pinecone sync every X minutes"""
        if self.is_running:
            logger.warning("Pinecone sync scheduler is already running")
            return
            
        self.is_running = True
        logger.info(f"🔄 Starting Pinecone sync scheduler (every {interval_minutes} minutes)")
        
        self.current_task = asyncio.create_task(
            self._run_sync_loop(interval_minutes)
        )
        return self.current_task
    
    async def stop_periodic_sync(self):
        """Stop the periodic Pinecone sync"""
        if not self.is_running:
            return
            
        logger.info("⏹️ Stopping Pinecone sync scheduler...")
        self.is_running = False
        
        if self.current_task:
            self.current_task.cancel()
            try:
                await self.current_task
            except asyncio.CancelledError:
                pass
    
    async def _run_sync_loop(self, interval_minutes: int):
        """Main sync loop that runs every interval"""
        
        while self.is_running:
            try:
                timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
                logger.info(f"🔄 [{timestamp}] Starting Pinecone sync #{self.sync_count + 1}")
                
                # Call the sync endpoint
                await self._trigger_pinecone_sync()
                
                self.sync_count += 1
                logger.info(f"✅ Pinecone sync #{self.sync_count} completed")
                
            except Exception as e:
                self.error_count += 1
                logger.error(f"❌ Pinecone sync #{self.sync_count + 1} failed: {e}")
            
            # Wait for the next interval
            if self.is_running:
                logger.info(f"⏱️ Waiting {interval_minutes} minutes until next Pinecone sync...")
                await asyncio.sleep(interval_minutes * 60)
    
    async def _trigger_pinecone_sync(self):
        """Trigger Pinecone sync via API call"""
        
        try:
            async with httpx.AsyncClient(timeout=300.0) as client:  # 5 minute timeout
                response = await client.post(
                    f"{self.base_url}/api/v1/etl/sync-to-pinecone",
                    params={"batch_size": 100}
                )
                response.raise_for_status()
                
                result = response.json()
                logger.info(f"📤 Pinecone sync API response: {result.get('message', '')}")
                
                # Optionally monitor the sync job
                if "job_id" in str(result):
                    await self._monitor_sync_job(result)
                
        except Exception as e:
            logger.error(f"❌ Failed to trigger Pinecone sync via API: {e}")
            raise
    
    async def _monitor_sync_job(self, trigger_result: dict):
        """Monitor the sync job status (optional)"""
        try:
            # Extract job ID if available
            message = trigger_result.get("message", "")
            if "job ID:" in message:
                job_id = message.split("job ID: ")[-1]
                logger.info(f"📊 Monitoring Pinecone sync job: {job_id}")
                
                # Wait a bit then check status
                await asyncio.sleep(5)
                
                async with httpx.AsyncClient() as client:
                    status_response = await client.get(
                        f"{self.base_url}/api/v1/etl/status/{job_id}"
                    )
                    if status_response.status_code == 200:
                        status = status_response.json()
                        logger.info(f"📊 Sync job status: {status.get('status', 'unknown')}")
                        
        except Exception as e:
            logger.debug(f"Could not monitor sync job: {e}")
    
    def get_status(self) -> dict:
        """Get scheduler status"""
        return {
            "is_running": self.is_running,
            "total_syncs": self.sync_count,
            "errors": self.error_count,
            "success_rate": f"{((self.sync_count - self.error_count) / max(self.sync_count, 1)) * 100:.1f}%" if self.sync_count > 0 else "0%"
        }


# Global scheduler instance
pinecone_sync_scheduler = PineconeSyncScheduler()
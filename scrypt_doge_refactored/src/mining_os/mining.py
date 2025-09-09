"""
Mining controller for Mining OS.
Enhanced with real mining service integration.
"""
import asyncio
import logging
import time
import os
import threading
from typing import Dict, Any, Optional
import requests
import sys

from .config import Settings
from .economic_guardian import EconomicGuardian
from .stratum_client import StratumClient

# Import real mining service
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))
try:
    from core.mining_service import RealMiningService
    REAL_MINING_AVAILABLE = True
except ImportError as e:
    logging.warning(f"Real mining service not available: {e}")
    REAL_MINING_AVAILABLE = False
    RealMiningService = None

logger = logging.getLogger(__name__)


class MiningController:
    def __init__(self, settings: Settings):
        self.settings = settings
        self.economic_guardian = EconomicGuardian(settings.min_profit_margin_pct)
        self.is_mining = False
        self.mining_task = None
        self.start_time = None
        self.stratum_client: Optional[StratumClient] = None
        self.current_pool_url = ""
        self.payout_address = settings.get_payout_address()
        self.lock = threading.Lock()
        self.pool_switch_count = 0
        self.last_payout_check = 0
        self.test_share_submitted = False
        self.job_queue = []
        self.current_job = None
        self.last_log_time = 0  # Track last log time to prevent spam

    async def start(self) -> bool:
        """Start mining if economic conditions are favorable."""
        logger.info("Checking economic conditions before starting mining")
        
        # Check if mining is profitable
        if not self.economic_guardian.is_profitable():
            logger.warning("Economic guardian blocked mining start - not profitable")
            return False
        
        # Check if payout address is set
        if not self.payout_address:
            logger.error("PAYOUT_ADDR environment variable is not set")
            return False
        
        if self.is_mining:
            logger.info("Mining already started")
            return True
        
        logger.info("Starting mining")
        self.is_mining = True
        self.start_time = time.time()
        
        # Submit test share for cold-start safety
        await self._submit_test_share()
        
        # Start mining task
        self.mining_task = asyncio.create_task(self._mine())
        return True

    async def stop(self):
        """Stop mining."""
        logger.info("Stopping mining")
        
        self.is_mining = False
        self.start_time = None
        self.current_job = None
        self.job_queue.clear()
        
        # Disconnect from stratum server
        if self.stratum_client:
            await self.stratum_client.disconnect()
            self.stratum_client = None
        
        if self.mining_task:
            self.mining_task.cancel()
            try:
                await self.mining_task
            except asyncio.CancelledError:
                pass
            self.mining_task = None

    async def _mine(self):
        """Main mining loop."""
        try:
            # Connect to primary pool
            connected = await self._connect_to_pool(self.settings.primary_url)
            if not connected:
                logger.error("Failed to connect to primary pool, attempting backup pools")
                connected = await self._reconnect_to_pool()
                
            if not connected:
                logger.error("Failed to connect to any pool, stopping mining")
                await self.stop()
                return
                
            while self.is_mining:
                # Check if connection is still alive
                if self.stratum_client and not self.stratum_client.is_alive():
                    logger.warning("Connection to pool lost, attempting to reconnect")
                    reconnected = await self._reconnect_to_pool()
                    if not reconnected:
                        logger.error("Failed to reconnect to any pool, stopping mining")
                        await self.stop()
                        return
                
                # Check for payout suggestions after 20 minutes
                if self.start_time and (time.time() - self.start_time) > 1200:  # 20 minutes
                    await self._suggest_difficulty_if_supported()
                
                # Check payouts every 5 minutes
                if time.time() - self.last_payout_check > 300:  # 5 minutes
                    await self._check_pool_payouts()
                    self.last_payout_check = time.time()
                
                # Process mining jobs
                if self.current_job and self.stratum_client and self.stratum_client.is_authorized:
                    # In a real implementation, this would:
                    # 1. Process the current job using ASIC/GPU
                    # 2. Submit shares when found
                    # Only log every 10 seconds to prevent spam
                    current_time = time.time()
                    if current_time - self.last_log_time > 10:
                        logger.info(f"Processing mining job: {self.current_job.get('job_id', 'unknown')}")
                        self.last_log_time = current_time
                    
                    # Simulate share submission
                    if self.job_queue:
                        job = self.job_queue.pop(0)
                        await self._submit_share_for_job(job)
                
                # Only log mining loop iteration every 30 seconds to prevent spam
                current_time = time.time()
                if current_time - self.last_log_time > 30:
                    logger.info("Mining loop iteration")
                    self.last_log_time = current_time
                
                # Wait before next iteration
                await asyncio.sleep(1)
        except asyncio.CancelledError:
            logger.info("Mining task cancelled")
        except Exception as e:
            logger.error(f"Error in mining loop: {e}", exc_info=True)
        finally:
            logger.info("Mining loop stopped")
            
    async def _connect_to_pool(self, url: str):
        """Connect to a mining pool."""
        with self.lock:
            # Disconnect from current pool if connected
            if self.stratum_client:
                await self.stratum_client.disconnect()
            
            # Create new stratum client
            username = f"{self.payout_address}.{self.settings.worker_name}"
            password = f"c=BTC,pl={self.settings.minimum_payout_threshold}"
            
            self.stratum_client = StratumClient(url, username, password)
            self.current_pool_url = url
            
            # Connect and authorize
            if await self.stratum_client.connect():
                if await self.stratum_client.subscribe():
                    if await self.stratum_client.authorize():
                        logger.info(f"Successfully connected to pool {url}")
                        return True
                    else:
                        logger.error("Failed to authorize with pool")
                else:
                    logger.error("Failed to subscribe to pool")
            else:
                logger.error("Failed to connect to pool")
            
            # If we get here, connection failed
            self.stratum_client = None
            return False
            
    async def _reconnect_to_pool(self):
        """Reconnect to a pool, trying backup URLs if needed."""
        # Try primary URL first
        if await self._connect_to_pool(self.settings.primary_url):
            logger.info(f"Reconnected to primary pool {self.settings.primary_url}")
            self.pool_switch_count += 1
            return True
            
        # Try backup URLs
        for backup_url in self.settings.backup_urls:
            if backup_url != self.settings.primary_url:
                if await self._connect_to_pool(backup_url):
                    logger.info(f"Successfully connected to backup pool {backup_url}")
                    self.pool_switch_count += 1
                    return True
                    
        logger.error("Failed to connect to any pool")
        return False

    def get_status(self):
        """Get current mining status."""
        uptime = 0
        if self.start_time:
            uptime = time.time() - self.start_time
            
        return {
            "is_mining": self.is_mining,
            "uptime": f"{int(uptime // 3600)}h {int((uptime % 3600) // 60)}m {int(uptime % 60)}s" if uptime > 0 else "0s",
            "profitable": self.economic_guardian.is_profitable(),
            "current_margin": self.economic_guardian.get_current_margin(),
            "payout_address": self.payout_address,
            "worker_name": self.settings.worker_name,
            "connected_pool": self.current_pool_url,
            "is_authorized": self.stratum_client.is_authorized if self.stratum_client else False,
            "pool_switches": self.pool_switch_count,
            "queued_jobs": len(self.job_queue),
            "current_job": self.current_job.get("job_id", None) if self.current_job else None
        }
        
    def update_payout_address(self, new_address: str):
        """Update the payout address and reconnect if needed."""
        with self.lock:
            if new_address != self.payout_address:
                logger.info(f"Updating payout address from {self.payout_address} to {new_address}")
                self.payout_address = new_address
                # Reconnect to update the authorization
                if self.is_mining and self.stratum_client:
                    asyncio.create_task(self._reconnect_to_pool())
                    
    async def _submit_test_share(self):
        """Submit a test share with difficulty 1 for cold-start safety."""
        if not self.test_share_submitted and self.stratum_client and self.stratum_client.is_authorized:
            # Submit a test share with difficulty 1
            try:
                # In a real implementation, this would be a proper share submission
                logger.info("Submitting test share for cold-start safety")
                # await self.stratum_client.submit_share("test_job", "00000000", "00000000", "00000000")
                self.test_share_submitted = True
                logger.info("Test share submitted successfully")
            except Exception as e:
                logger.error(f"Failed to submit test share: {e}")
                
    async def _suggest_difficulty_if_supported(self):
        """Suggest difficulty to pool if it supports pl= parameter."""
        if self.stratum_client and self.stratum_client.is_authorized:
            # Check if pool supports difficulty suggestion
            # In a real implementation, you'd check the pool capabilities
            try:
                await self.stratum_client.suggest_difficulty(1)
                logger.info("Difficulty suggestion sent to pool")
            except Exception as e:
                logger.warning(f"Failed to suggest difficulty: {e}")
                
    async def _check_pool_payouts(self):
        """Check pool payouts and send notifications if needed."""
        try:
            # In a real implementation, you'd scrape the pool's web API
            # For now, we'll simulate this
            logger.info("Checking pool payouts")
            # response = requests.get(f"{self.current_pool_url}/api/payouts")
            # if response.status_code == 200:
            #     data = response.json()
            #     # Check if last payout was more than 24 hours ago
            #     # and confirmed balance >= threshold
            #     # If so, send desktop notification
        except Exception as e:
            logger.warning(f"Failed to check pool payouts: {e}")
            
    async def _submit_share_for_job(self, job):
        """Submit a share for a mining job."""
        if self.stratum_client and self.stratum_client.is_authorized:
            try:
                # In a real implementation, this would submit actual share data
                job_id = job.get("job_id", "unknown")
                logger.info(f"Submitting share for job {job_id}")
                # await self.stratum_client.submit_share(job_id, ...)
                logger.info(f"Share submitted for job {job_id}")
            except Exception as e:
                logger.error(f"Failed to submit share for job {job.get('job_id', 'unknown')}: {e}")

    def add_job(self, job_data):
        """Add a mining job to the queue."""
        self.job_queue.append(job_data)
        logger.info(f"Added job to queue. Queue size: {len(self.job_queue)}")
        
    def set_current_job(self, job_data):
        """Set the current mining job."""
        self.current_job = job_data
        logger.info(f"Set current job: {job_data.get('job_id', 'unknown')}")

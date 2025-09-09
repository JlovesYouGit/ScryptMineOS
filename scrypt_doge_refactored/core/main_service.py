"""
Main Service Entry Point for the refactored Scrypt DOGE mining system.
Unified entry point with proper service architecture and lifecycle management.
"""

import asyncio
import signal
import sys
import logging
from typing import Optional
from datetime import datetime

from core.config_manager import ConfigManager
from core.mining_service import MiningService
from monitoring.system_monitor import SystemMonitor
from security.security_manager import SecurityManager
from network.pool_manager import PoolFailoverManager
from core.service_container import ServiceContainer

# Try to import database components
try:
    from core.database_manager import DatabaseManager, DatabaseConfig
except ImportError:
    # Mock classes for type hints if database module is not available
    class DatabaseManager:
        pass
    
    class DatabaseConfig:
        pass


class MiningSystemService:
    """Main mining system service with proper lifecycle management"""
    
    def __init__(self, config_manager: ConfigManager):
        self.config_manager = config_manager
        self.config = None
        self.logger = logging.getLogger(__name__)
        self.mining_service: Optional[MiningService] = None
        self.system_monitor: Optional[SystemMonitor] = None
        self.security_manager: Optional[SecurityManager] = None
        self.pool_manager: Optional[PoolFailoverManager] = None
        self.database_manager: Optional[DatabaseManager] = None
        self._shutdown_event = asyncio.Event()
        self._tasks: list[asyncio.Task] = []
        self.start_time = datetime.now()
        
    async def initialize(self) -> bool:
        """Initialize the mining system service"""
        try:
            self.logger.info("Initializing mining system service...")
            
            # Load configuration
            self.config = await self.config_manager.load_config()
            
            # Initialize database manager if configured
            db_config_dict = self.config.database.__dict__ if hasattr(self.config, 'database') else {}
            if db_config_dict:
                db_config = DatabaseConfig(
                    enabled=db_config_dict.get("enabled", True),
                    uri=db_config_dict.get("uri", ""),
                    name=db_config_dict.get("name", "mining_db"),
                    collections=db_config_dict.get("collections", {})
                )
                self.database_manager = DatabaseManager(db_config)
                await self.database_manager.initialize()
                self.logger.info("Database manager initialized")
            
            # Initialize security manager
            self.security_manager = SecurityManager(self.config.security)
            await self.security_manager.start()
            
            # Initialize system monitor with database manager
            self.system_monitor = SystemMonitor(
                {
                    "collection_interval": 5,
                    "health_check_interval": 60
                },
                database_manager=self.database_manager
            )
            await self.system_monitor.start_monitoring()
            
            # Initialize pool manager
            pool_configs = [pool.__dict__ for pool in self.config.pools]
            self.pool_manager = PoolFailoverManager(pool_configs)
            
            # Initialize mining service
            self.mining_service = MiningService(self.config.__dict__)
            await self.mining_service.initialize()
            
            self.logger.info("Mining system service initialized successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to initialize mining system: {e}")
            return False
    
    async def start(self) -> None:
        """Start the mining system service"""
        self.logger.info("Starting mining system service...")
        
        try:
            # Start system monitoring
            if self.system_monitor:
                monitor_task = asyncio.create_task(self.system_monitor.start_monitoring())
                self._tasks.append(monitor_task)
            
            # Start mining service
            if self.mining_service:
                # Connect to pool
                await self.mining_service.connect_to_pool()
                # Start mining
                mining_task = asyncio.create_task(self.mining_service.start_mining())
                self._tasks.append(mining_task)
            
            self.logger.info("Mining system service started successfully")
            
            # Wait for shutdown signal
            await self._shutdown_event.wait()
            
        except Exception as e:
            self.logger.error(f"Failed to start mining system: {e}")
            raise
    
    async def stop(self) -> None:
        """Gracefully stop the mining system service"""
        self.logger.info("Stopping mining system service...")
        
        # Signal shutdown
        self._shutdown_event.set()
        
        # Stop all services in reverse order
        if self.mining_service:
            await self.mining_service.stop()
        
        if self.system_monitor:
            await self.system_monitor.stop_monitoring()
        
        if self.security_manager:
            await self.security_manager.stop()
        
        # Close database connection
        if self.database_manager:
            await self.database_manager.close()
        
        # Cancel all tasks
        for task in self._tasks:
            if not task.done():
                task.cancel()
        
        # Wait for all tasks to complete
        await asyncio.gather(*self._tasks, return_exceptions=True)
        
        self.logger.info("Mining system service stopped")
    
    def get_status(self) -> dict:
        """Get comprehensive system status"""
        status = {
            "running": not self._shutdown_event.is_set(),
            "start_time": self.start_time.isoformat(),
            "uptime": (datetime.now() - self.start_time).total_seconds(),
            "components": {}
        }
        
        if self.mining_service:
            status["components"]["mining"] = self.mining_service.get_status().__dict__
        
        if self.system_monitor:
            status["components"]["monitoring"] = self.system_monitor.get_status()
        
        if self.security_manager:
            status["components"]["security"] = self.security_manager.get_security_status()
        
        return status


class ServiceManager:
    """Manages the mining system service lifecycle"""
    
    def __init__(self, config_path: str = "config/mining_config.yaml"):
        self.config_path = config_path
        self.config_manager = ConfigManager(config_path)
        self.service: Optional[MiningSystemService] = None
        self.logger = logging.getLogger(__name__)
    
    async def start_service(self) -> None:
        """Start the service"""
        self.service = MiningSystemService(self.config_manager)
        success = await self.service.initialize()
        if success:
            await self.service.start()
        else:
            raise Exception("Failed to initialize mining system service")
    
    async def stop_service(self) -> None:
        """Stop the service"""
        if self.service:
            await self.service.stop()
            self.service = None


def setup_signal_handlers(service_manager: ServiceManager) -> None:
    """Setup graceful shutdown signal handlers"""
    
    def signal_handler(signum, frame):
        logger = logging.getLogger(__name__)
        logger.info(f"Received signal {signum}, initiating graceful shutdown...")
        asyncio.create_task(service_manager.stop_service())
    
    signal.signal(signal.SIGTERM, signal_handler)
    signal.signal(signal.SIGINT, signal_handler)


async def main(config_path: str = "config/mining_config.yaml") -> None:
    """Main entry point"""
    
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    logger = logging.getLogger(__name__)
    logger.info("Starting production-ready mining system...")
    
    # Create service manager
    service_manager = ServiceManager(config_path)
    
    # Setup signal handlers
    setup_signal_handlers(service_manager)
    
    try:
        # Start the service
        await service_manager.start_service()
    except Exception as e:
        logger.error(f"Service failed to start: {e}")
        sys.exit(1)


if __name__ == "__main__":
    # Run the application
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nShutdown requested by user")
    except Exception as e:
        print(f"Fatal error: {e}")
        sys.exit(1)
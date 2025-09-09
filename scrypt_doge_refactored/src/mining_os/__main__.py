"""
Main entry point for the Mining OS service.
"""
import argparse
import asyncio
import logging
import signal
import sys
from typing import Optional

from .server import MiningOSServer
from .config import Settings

logger = logging.getLogger(__name__)


class MiningOS:
    def __init__(self, settings: Settings):
        self.settings = settings
        self.server: Optional[MiningOSServer] = None
        self._shutdown_event = asyncio.Event()

    async def start(self):
        """Start the Mining OS service."""
        logger.info("Starting Mining OS service")
        
        # Validate payout address is set
        payout_addr = self.settings.get_payout_address()
        if not payout_addr:
            logger.error("PAYOUT_ADDR environment variable is required - refusing to start")
            sys.exit(64)  # Exit code 64 for usage error
        
        logger.info(f"Using payout address: {payout_addr[:10]}...{payout_addr[-4:]}")
        
        # Initialize the server
        self.server = MiningOSServer(self.settings)
        
        # Set up signal handlers for graceful shutdown (Windows compatible)
        try:
            loop = asyncio.get_running_loop()
            # Only set up signal handlers on Unix-like systems
            import platform
            if platform.system() != 'Windows':
                for sig in (signal.SIGTERM, signal.SIGINT):
                    loop.add_signal_handler(sig, lambda s=sig: asyncio.create_task(self._signal_handler(s)))
            else:
                # On Windows, we'll rely on KeyboardInterrupt handling
                logger.info("Running on Windows - using KeyboardInterrupt for shutdown")
        except Exception as e:
            logger.warning(f"Could not set up signal handlers: {e}")
        
        # Start the server
        await self.server.start()
        
        # Wait for shutdown signal
        await self._shutdown_event.wait()
        
        # Graceful shutdown
        await self.stop()

    async def stop(self):
        """Stop the Mining OS service."""
        logger.info("Stopping Mining OS service")
        
        if self.server:
            await self.server.stop()
        
        self._shutdown_event.set()

    async def _signal_handler(self, sig):
        """Handle shutdown signals."""
        logger.info(f"Received signal {sig}, initiating graceful shutdown")
        await self.stop()


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Mining OS - Browser-First Mining Operating System")
    parser.add_argument("--host", default="0.0.0.0", help="Host to bind to (default: 0.0.0.0)")
    parser.add_argument("--port", type=int, default=31415, help="Port to bind to (default: 31415)")
    parser.add_argument("--config-path", default="settings.yaml", help="Path to configuration file (default: settings.yaml)")
    
    args = parser.parse_args()
    
    # Load settings
    try:
        settings = Settings(_env_file=args.config_path)
        settings.host = args.host
        settings.port = args.port
        
        # Validate payout address is set
        payout_addr = settings.get_payout_address()
        if not payout_addr:
            logger.error("PAYOUT_ADDR environment variable is required")
            print("Error: PAYOUT_ADDR environment variable is required")
            print("Please run with: docker run -e PAYOUT_ADDR=your_wallet_address -p 31415:31415 mining-os")
            sys.exit(64)  # Exit code 64 for usage error
    except Exception as e:
        logger.error(f"Failed to load configuration: {e}")
        sys.exit(1)
    
    # Set up logging
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
    )
    
    # Create and start the service
    mining_os = MiningOS(settings)
    
    try:
        asyncio.run(mining_os.start())
    except KeyboardInterrupt:
        logger.info("Received interrupt signal, shutting down...")
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        sys.exit(1)
    
    logger.info("Mining OS service stopped")


if __name__ == "__main__":
    main()
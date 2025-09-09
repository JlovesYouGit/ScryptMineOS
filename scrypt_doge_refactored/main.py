#!/usr/bin/env python3
"""
Unified Scrypt DOGE Mining System - Production Ready
Refactored entry point with clean architecture and modular design

This script provides a single entry point to run the complete mining system:
1. Stratum client connection to mining pool with enhanced security
2. Performance optimization with L2 kernel, voltage tuning, clock gating
3. ASIC hardware emulation for development and testing
4. GPU-ASIC hybrid layer for mixed mining operations
5. Continuous mining operation with economic safeguards
6. Real-time monitoring and statistics
7. Educational mode for safe testing

Usage:
    python main.py [--mode educational|production] [--continuous] [--monitor]
    python main.py --help  # Show all options
"""

import argparse
import sys
import logging
from typing import Optional

# Import system components
from core.main_service import main as start_main_service

class UnifiedMiningSystemCLI:
    """Command Line Interface for the Unified Mining System"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def run(self, args):
        """Run the mining system with the provided arguments"""
        try:
            # Configure logging based on arguments
            log_level = logging.DEBUG if args.verbose else logging.INFO
            logging.basicConfig(
                level=log_level,
                format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            
            self.logger.info("Starting Unified Scrypt DOGE Mining System")
            self.logger.info(f"Mode: {args.mode}")
            self.logger.info(f"Config file: {args.config}")
            
            # Run the main service
            import asyncio
            asyncio.run(start_main_service(args.config))
            
        except KeyboardInterrupt:
            print("\n🛑 System execution interrupted by user")
            return 0
        except Exception as e:
            print(f"\n💥 Unexpected error: {e}")
            return 1

def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="Unified Scrypt DOGE Complete Mining System",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python main.py                           # Run system with default config
  python main.py --config production.yaml  # Run with production config
  python main.py --mode production         # Run in production mode
  python main.py --verbose                 # Enable verbose logging
        """
    )
    
    parser.add_argument(
        "--mode",
        choices=["educational", "production", "testing"],
        default="educational",
        help="System operation mode (default: educational)"
    )
    
    parser.add_argument(
        "--config",
        type=str,
        default="config/mining_config.yaml",
        help="Path to configuration file"
    )
    
    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Enable verbose logging"
    )
    
    parser.add_argument(
        "--status",
        action="store_true",
        help="Show current system status and exit"
    )
    
    args = parser.parse_args()
    
    # Create and run the CLI
    cli = UnifiedMiningSystemCLI()
    return cli.run(args)

if __name__ == "__main__":
    sys.exit(main())
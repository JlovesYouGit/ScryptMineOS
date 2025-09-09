#!/usr/bin/env python3
"""
Main Entry Point for the GPU-ASIC Mining System
Unified launcher that orchestrates all system components

This script provides a single entry point to run the complete system:
1. Stratum client connection to mining pool
2. Performance optimization
3. ASIC hardware emulation
4. GPU-ASIC hybrid layer
5. Continuous mining operation
6. Monitoring and statistics

Usage:
    python main.py [--mode educational|production] [--continuous] [--monitor]
"""

import argparse
import sys
import time
import threading
import signal
import os
from typing import Optional

# Import system components
from mining_constants import SYSTEM, MINING, NETWORK
from stratum_client import StratumClient, StratumConfig, StratumVersion
from performance_optimizer import PerformanceOptimizer
from asic_hardware_emulation import ASICEmulator
from gpu_asic_hybrid import GPUASICHybrid
from asic_monitor import ASICMonitor

class GPUMiningSystem:
    """Main GPU-ASIC Mining System orchestrator"""
    
    def __init__(self, mode: str = "educational"):
        self.mode = mode
        self.running = False
        self.stratum_client: Optional[StratumClient] = None
        self.performance_optimizer: Optional[PerformanceOptimizer] = None
        self.asic_emulator: Optional[ASICEmulator] = None
        self.gpu_hybrid: Optional[GPUASICHybrid] = None
        self.monitor: Optional[ASICMonitor] = None
        
        # Set up signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
        
    def _signal_handler(self, signum, frame):
        """Handle shutdown signals gracefully"""
        print(f"\nReceived signal {signum}, shutting down gracefully...")
        self.stop()
        
    def initialize_system(self) -> bool:
        """Initialize all system components"""
        print("Initializing GPU-ASIC Mining System...")
        print("=" * 50)
        
        try:
            # 1. Initialize Stratum client
            print("1. Initializing Stratum client...")
            config = StratumConfig(
                host="doge.zsolo.bid",
                port=8057,
                username="DGKsuHU6XdghZtA2aWGqvrZrkWracQJzPd",
                password="x",
                version=StratumVersion.V1,
                timeout=NETWORK.SOCKET_TIMEOUT,
                reconnect_attempts=SYSTEM.MAX_RESTARTS,
                reconnect_delay=SYSTEM.MIN_RESTART_WAIT
            )
            
            self.stratum_client = StratumClient(config)
            print("   ✓ Stratum client initialized")
            
            # 2. Initialize performance optimizer
            print("2. Initializing performance optimizer...")
            self.performance_optimizer = PerformanceOptimizer()
            print("   ✓ Performance optimizer initialized")
            
            # 3. Initialize ASIC emulator
            print("3. Initializing ASIC hardware emulator...")
            self.asic_emulator = ASICEmulator()
            print("   ✓ ASIC emulator initialized")
            
            # 4. Initialize GPU-ASIC hybrid layer
            print("4. Initializing GPU-ASIC hybrid layer...")
            self.gpu_hybrid = GPUASICHybrid()
            print("   ✓ GPU-ASIC hybrid initialized")
            
            # 5. Initialize monitor
            print("5. Initializing system monitor...")
            self.monitor = ASICMonitor()
            print("   ✓ System monitor initialized")
            
            print("\n✅ All system components initialized successfully!")
            return True
            
        except Exception as e:
            print(f"❌ Error initializing system: {e}")
            return False
    
    def connect_to_pool(self) -> bool:
        """Connect to mining pool"""
        if not self.stratum_client:
            print("❌ Stratum client not initialized")
            return False
            
        print("Connecting to mining pool...")
        try:
            if self.stratum_client.initialize():
                print("✅ Connected to mining pool successfully!")
                return True
            else:
                print("❌ Failed to connect to mining pool")
                return False
        except Exception as e:
            print(f"❌ Error connecting to pool: {e}")
            return False
    
    def run_performance_optimization(self) -> bool:
        """Run performance optimization"""
        if not self.performance_optimizer:
            print("❌ Performance optimizer not initialized")
            return False
            
        print("Running performance optimization...")
        try:
            success = self.performance_optimizer.optimize_performance()
            if success:
                print("✅ Performance optimization completed!")
                return True
            else:
                print("⚠️ Performance optimization had issues")
                return False
        except Exception as e:
            print(f"❌ Error during performance optimization: {e}")
            return False
    
    def run_hardware_emulation(self) -> bool:
        """Run ASIC hardware emulation"""
        if not self.asic_emulator:
            print("❌ ASIC emulator not initialized")
            return False
            
        print("Running ASIC hardware emulation...")
        try:
            success = self.asic_emulator.run_emulation()
            if success:
                print("✅ ASIC hardware emulation completed!")
                return True
            else:
                print("⚠️ ASIC hardware emulation had issues")
                return False
        except Exception as e:
            print(f"❌ Error during hardware emulation: {e}")
            return False
    
    def start_hybrid_layer(self) -> bool:
        """Start GPU-ASIC hybrid layer"""
        if not self.gpu_hybrid:
            print("❌ GPU-ASIC hybrid not initialized")
            return False
            
        print("Starting GPU-ASIC hybrid layer...")
        try:
            success = self.gpu_hybrid.start_hybrid_mode()
            if success:
                print("✅ GPU-ASIC hybrid layer started!")
                return True
            else:
                print("⚠️ GPU-ASIC hybrid layer had issues")
                return False
        except Exception as e:
            print(f"❌ Error starting hybrid layer: {e}")
            return False
    
    def start_monitoring(self) -> bool:
        """Start system monitoring"""
        if not self.monitor:
            print("❌ System monitor not initialized")
            return False
            
        print("Starting system monitoring...")
        try:
            self.monitor.start_monitoring()
            print("✅ System monitoring started!")
            return True
        except Exception as e:
            print(f"❌ Error starting monitoring: {e}")
            return False
    
    def start_mining_loop(self):
        """Main mining loop"""
        if not self.stratum_client:
            print("❌ Stratum client not initialized")
            return
            
        print("Starting mining loop...")
        self.running = True
        
        try:
            self.stratum_client.listen_for_jobs()
        except Exception as e:
            print(f"❌ Error in mining loop: {e}")
        finally:
            self.running = False
    
    def start_continuous_mining(self):
        """Start continuous mining operation"""
        print("Starting continuous mining operation...")
        
        # Start monitoring in background thread
        if self.start_monitoring():
            monitor_thread = threading.Thread(target=self.monitor.monitor_loop, daemon=True)
            monitor_thread.start()
        
        # Start mining loop in main thread
        self.start_mining_loop()
    
    def get_system_status(self) -> dict:
        """Get comprehensive system status"""
        status = {
            "mode": self.mode,
            "running": self.running,
            "components": {}
        }
        
        # Add Stratum client status
        if self.stratum_client:
            status["components"]["stratum"] = self.stratum_client.get_stats()
        
        # Add monitor status
        if self.monitor:
            status["components"]["monitor"] = self.monitor.get_status()
            
        return status
    
    def print_system_status(self):
        """Print current system status"""
        status = self.get_system_status()
        print("\n" + "=" * 50)
        print("GPU-ASIC MINING SYSTEM STATUS")
        print("=" * 50)
        print(f"Mode: {status['mode']}")
        print(f"Running: {status['running']}")
        
        if "stratum" in status["components"]:
            stratum_stats = status["components"]["stratum"]
            print(f"\nStratum Connection:")
            print(f"  Connected: {stratum_stats['connected']}")
            print(f"  Authorized: {stratum_stats['authorized']}")
            print(f"  Difficulty: {stratum_stats['current_difficulty']}")
            
        if "monitor" in status["components"]:
            monitor_stats = status["components"]["monitor"]
            print(f"\nSystem Monitoring:")
            print(f"  Temperature: {monitor_stats.get('temperature', 'N/A')}°C")
            print(f"  Hashrate: {monitor_stats.get('hashrate', 'N/A')} MH/s")
            print(f"  Power: {monitor_stats.get('power', 'N/A')} W")
        
        print("=" * 50)
    
    def stop(self):
        """Stop all system components"""
        print("Stopping GPU-ASIC Mining System...")
        self.running = False
        
        # Stop monitoring
        if self.monitor:
            self.monitor.stop_monitoring()
            
        # Disconnect from pool
        if self.stratum_client:
            self.stratum_client.disconnect()
            
        print("✅ System stopped successfully")
    
    def run_complete_system(self, continuous: bool = False, monitor: bool = False) -> bool:
        """Run the complete mining system"""
        print("🚀 Starting GPU-ASIC Complete Mining System")
        print("=" * 60)
        print(f"Mode: {self.mode}")
        print(f"Continuous Mining: {continuous}")
        print(f"Monitoring: {monitor}")
        print("=" * 60)
        
        # Initialize system
        if not self.initialize_system():
            print("❌ Failed to initialize system")
            return False
        
        # Connect to pool
        if not self.connect_to_pool():
            print("❌ Failed to connect to mining pool")
            return False
        
        # Run performance optimization
        if not self.run_performance_optimization():
            print("⚠️ Performance optimization issues, continuing anyway...")
        
        # Run hardware emulation
        if not self.run_hardware_emulation():
            print("⚠️ Hardware emulation issues, continuing anyway...")
        
        # Start hybrid layer
        if not self.start_hybrid_layer():
            print("⚠️ Hybrid layer issues, continuing anyway...")
        
        # Start monitoring if requested
        if monitor:
            if not self.start_monitoring():
                print("⚠️ Monitoring issues, continuing anyway...")
        
        # Print system status
        self.print_system_status()
        
        # Start continuous mining if requested
        if continuous:
            print("\n🔄 Starting continuous mining operation...")
            try:
                self.start_continuous_mining()
            except KeyboardInterrupt:
                print("\n🛑 Mining stopped by user")
            except Exception as e:
                print(f"❌ Error during continuous mining: {e}")
                return False
        else:
            print("\n✅ System initialization complete!")
            print("💡 To start continuous mining, run with --continuous flag")
        
        return True

def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="GPU-ASIC Complete Mining System",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python main.py                           # Run system initialization only
  python main.py --continuous             # Run continuous mining
  python main.py --mode production        # Run in production mode
  python main.py --continuous --monitor   # Run with monitoring
        """
    )
    
    parser.add_argument(
        "--mode",
        choices=["educational", "production", "testing"],
        default="educational",
        help="System operation mode (default: educational)"
    )
    
    parser.add_argument(
        "--continuous",
        action="store_true",
        help="Start continuous mining operation"
    )
    
    parser.add_argument(
        "--monitor",
        action="store_true",
        help="Enable system monitoring"
    )
    
    parser.add_argument(
        "--status",
        action="store_true",
        help="Show current system status and exit"
    )
    
    args = parser.parse_args()
    
    # Create and run the mining system
    mining_system = GPUMiningSystem(mode=args.mode)
    
    # Handle status request
    if args.status:
        mining_system.print_system_status()
        return 0
    
    # Run the complete system
    try:
        success = mining_system.run_complete_system(
            continuous=args.continuous,
            monitor=args.monitor
        )
        
        if success:
            print("\n🎉 GPU-ASIC Mining System execution completed successfully!")
            return 0
        else:
            print("\n❌ GPU-ASIC Mining System execution failed!")
            return 1
            
    except KeyboardInterrupt:
        print("\n🛑 System execution interrupted by user")
        mining_system.stop()
        return 0
    except Exception as e:
        print(f"\n💥 Unexpected error: {e}")
        return 1
    finally:
        mining_system.stop()

if __name__ == "__main__":
    sys.exit(main())
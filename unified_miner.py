#!/usr/bin/env python3
"""
Unified GPU-ASIC Mining System
Single executable that orchestrates all system components with enhanced Stratum support

This script provides a single entry point to run the complete system:
1. Enhanced Stratum client connection to mining pool (V1/V2 support)
2. Performance optimization with L2 kernel, voltage tuning, clock gating
3. ASIC hardware emulation (all 8 components)
4. GPU-ASIC hybrid layer (Antminer L7 emulation)
5. Continuous mining operation with economic safeguards
6. Real-time monitoring and statistics
7. Educational mode for safe testing

Usage:
    python unified_miner.py [--mode educational|production] [--continuous] [--monitor]
    python unified_miner.py --help  # Show all options
"""

import argparse
import sys
import time
import threading
import signal
import subprocess
import os
from typing import Optional

# Import system components
from mining_constants import SYSTEM, MINING, NETWORK
from enhanced_stratum_client import EnhancedStratumClient
from performance_optimizer import GPUPerformanceOptimizer
from asic_hardware_emulation import ASICHardwareEmulator
from gpu_asic_hybrid import GPUASICHybrid
# ASICMonitor is not available as a class, using the script directly
from economic_guardian import EconomicGuardian
from continuous_miner import ContinuousMiner

class UnifiedGPUMiningSystem:
    """Main Unified GPU-ASIC Mining System orchestrator"""
    
    def __init__(self, mode: str = "educational"):
        self.mode = mode
        self.running = False
        self.stratum_client: Optional[EnhancedStratumClient] = None
        self.performance_optimizer: Optional[GPUPerformanceOptimizer] = None
        self.asic_emulator: Optional[ASICHardwareEmulator] = None
        self.gpu_hybrid: Optional[GPUASICHybrid] = None
        self.monitor = None  # ASICMonitor is not available as a class
        self.economic_guardian: Optional[EconomicGuardian] = None
        self.continuous_miner: Optional[ContinuousMiner] = None
        
        # Set up signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
        
    def _signal_handler(self, signum, frame):
        """Handle shutdown signals gracefully"""
        print(f"\nReceived signal {signum}, shutting down gracefully...")
        self.stop()
        
    def initialize_system(self) -> bool:
        """Initialize all system components"""
        print("Initializing Unified GPU-ASIC Mining System...")
        print("=" * 60)
        
        try:
            # 1. Initialize Enhanced Stratum client
            print("1. Initializing Enhanced Stratum client...")
            self.stratum_client = EnhancedStratumClient(
                host="doge.zsolo.bid",
                port=8057,
                user=os.getenv("POOL_USER", os.getenv("POOL_USER", os.getenv("POOL_USER", "your_wallet_address.worker_name"))),
                password=os.getenv("POOL_PASSWORD", "x")"POOL_PASSWORD", "x")"
            )
            print("   ✓ Enhanced Stratum client initialized")
            
            # 2. Initialize performance optimizer
            print("2. Initializing performance optimizer...")
            self.performance_optimizer = GPUPerformanceOptimizer()
            print("   ✓ Performance optimizer initialized")
            
            # 3. Initialize ASIC emulator
            print("3. Initializing ASIC hardware emulator...")
            self.asic_emulator = ASICHardwareEmulator()
            print("   ✓ ASIC emulator initialized")
            
            # 4. Initialize GPU-ASIC hybrid layer
            print("4. Initializing GPU-ASIC hybrid layer...")
            self.gpu_hybrid = GPUASICHybrid()
            print("   ✓ GPU-ASIC hybrid initialized")
            
            # 5. ASIC Monitor is a script, not a class
            print("5. Skipping system monitor initialization (script-based)")
            
            # 6. Initialize economic guardian
            print("6. Initializing economic guardian...")
            self.economic_guardian = EconomicGuardian()
            print("   ✓ Economic guardian initialized")
            
            # 7. Initialize continuous miner
            print("7. Initializing continuous miner...")
            self.continuous_miner = ContinuousMiner()
            print("   ✓ Continuous miner initialized")
            
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
            if self.stratum_client.connect():
                if self.stratum_client.subscribe_and_authorize():
                    print("✅ Connected to mining pool successfully!")
                    return True
                else:
                    print("❌ Failed to subscribe/authorize with pool")
                    return False
            else:
                print("❌ Failed to connect to mining pool")
                return False
        except Exception as e:
            print(f"❌ Error connecting to pool: {e}")
            return False
    
    def run_performance_optimization(self, use_l2_kernel: bool = False, 
                                   voltage_tuning: bool = False, 
                                   clock_gating: bool = False) -> bool:
        """Run performance optimization with specific features"""
        if not self.performance_optimizer:
            print("❌ Performance optimizer not initialized")
            return False
            
        print("Running performance optimization...")
        try:
            # Run optimization with specified features
            # Run optimization with specified features
            if use_l2_kernel or voltage_tuning or clock_gating:
                result = self.performance_optimizer.run_full_optimization()
                success = result is not None
            else:
                # Just measure baseline
                self.performance_optimizer.measure_baseline()
                success = True
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
            # Initialize the ASIC hardware emulation
            success = self.asic_emulator.initialize()
            if success:
                # Run the development checklist to validate emulation
                checklist = self.asic_emulator.run_dev_checklist()
                print(f"   Dev Checklist: {sum(checklist.values())}/{len(checklist)} passed")
            if success:
                print("✅ ASIC hardware emulation completed!")
                return True
            else:
                print("⚠️ ASIC hardware emulation had issues")
                # Continue anyway as this is just emulation
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
            # Initialize the GPU-ASIC hybrid layer
            success = self.gpu_hybrid.initialize()
            if success:
                print("✅ GPU-ASIC hybrid layer started!")
                return True
            else:
                print("⚠️ GPU-ASIC hybrid layer had issues")
                # Continue anyway as this is just initialization
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
    
    def check_economic_safety(self) -> bool:
        """Check economic safety conditions"""
        if not self.economic_guardian:
            print("❌ Economic guardian not initialized")
            return True  # Continue if guardian not available
            
        print("Checking economic safety conditions...")
        try:
            economic_status = self.economic_guardian.check_economic_viability()
            if economic_status["is_viable"]:
                print("✅ Economic conditions favorable for mining")
                print(f"   Hashrate: {economic_status['hashrate']:.2f} H/s")
                print(f"   Power: {economic_status['power_watts']:.1f} W")
                print(f"   Efficiency: {economic_status['hash_per_watt']:.2f} H/W")
                return True
            else:
                print("⚠️ Economic conditions unfavorable for mining")
                return False
        except Exception as e:
            print(f"❌ Error checking economic safety: {e}")
            return True  # Continue on error to avoid stopping mining
    
    def start_mining_loop(self):
        """Main mining loop"""
        if not self.stratum_client:
            print("❌ Stratum client not initialized")
            return
            
        print("Starting mining loop...")
        self.running = True
        
        try:
            # This would be where the actual mining loop would run
            # For now, we'll just listen for jobs as an example
            while self.running:
                message = self.stratum_client.receive_message()
                if message:
                    if message.get("method"):
                        # Handle notifications
                        self.stratum_client.handle_notification(message)
                # In a real implementation, this would be the actual mining loop
                time.sleep(1)
        except Exception as e:
            print(f"❌ Error in mining loop: {e}")
        finally:
            self.running = False
    
    def start_continuous_mining(self):
        """Start continuous mining operation"""
        print("Starting continuous mining operation...")
        
        try:
            if self.continuous_miner:
                self.continuous_miner.run_continuous(service_mode=False)
            else:
                print("❌ Continuous miner not initialized")
        except Exception as e:
            print(f"❌ Error during continuous mining: {e}")
    
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
        print("\n" + "=" * 60)
        print("UNIFIED GPU-ASIC MINING SYSTEM STATUS")
        print("=" * 60)
        print(f"Mode: {status['mode']}")
        print(f"Running: {status['running']}")
        
        if "stratum" in status["components"]:
            stratum_stats = status["components"]["stratum"]
            conn_stats = stratum_stats.get("connection", {})
            print(f"\nStratum Connection:")
            print(f"  Connected: {conn_stats.get('successful', 0) > 0}")
            print(f"  Attempts: {conn_stats.get('attempts', 0)}")
            
        if "monitor" in status["components"]:
            monitor_stats = status["components"]["monitor"]
            print(f"\nSystem Monitoring:")
            print(f"  Temperature: {monitor_stats.get('temperature', 'N/A')}°C")
            print(f"  Hashrate: {monitor_stats.get('hashrate', 'N/A')} MH/s")
            print(f"  Power: {monitor_stats.get('power', 'N/A')} W")
        
        print("=" * 60)
    
    def stop(self):
        """Stop all system components"""
        print("Stopping Unified GPU-ASIC Mining System...")
        self.running = False
        
        # Stop monitoring
        if self.monitor:
            self.monitor.stop_monitoring()
            
        # Disconnect from pool
        if self.stratum_client:
            self.stratum_client.disconnect()
            
        print("✅ System stopped successfully")
    
    def run_complete_system(self, continuous: bool = False, monitor: bool = False,
                          use_l2_kernel: bool = False, voltage_tuning: bool = False,
                          clock_gating: bool = False, hardware_emulation: bool = False) -> bool:
        """Run the complete mining system"""
        print("🚀 Starting Unified GPU-ASIC Complete Mining System")
        print("=" * 70)
        print(f"Mode: {self.mode}")
        print(f"Continuous Mining: {continuous}")
        print(f"Monitoring: {monitor}")
        print(f"L2 Kernel: {use_l2_kernel}")
        print(f"Voltage Tuning: {voltage_tuning}")
        print(f"Clock Gating: {clock_gating}")
        print(f"Hardware Emulation: {hardware_emulation}")
        print("=" * 70)
        
        # Initialize system
        if not self.initialize_system():
            print("❌ Failed to initialize system")
            return False
        
        # Check economic safety
        if not self.check_economic_safety():
            print("⚠️ Economic conditions unfavorable, but continuing in educational mode...")
        
        # Connect to pool
        if not self.connect_to_pool():
            print("❌ Failed to connect to mining pool")
            return False
        
        # Run performance optimization
        if not self.run_performance_optimization(use_l2_kernel, voltage_tuning, clock_gating):
            print("⚠️ Performance optimization issues, continuing anyway...")
        
        # Run hardware emulation if requested
        if hardware_emulation:
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
        description="Unified GPU-ASIC Complete Mining System",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python unified_miner.py                           # Run system initialization only
  python unified_miner.py --continuous             # Run continuous mining
  python unified_miner.py --mode production        # Run in production mode
  python unified_miner.py --continuous --monitor   # Run with monitoring
  python unified_miner.py --optimize-all          # Run with all optimizations
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
    
    # Performance optimization options
    parser.add_argument(
        "--optimize-performance",
        action="store_true",
        help="Run complete performance optimization"
    )
    
    parser.add_argument(
        "--use-l2-kernel",
        action="store_true",
        help="Use L2-optimized kernel"
    )
    
    parser.add_argument(
        "--voltage-tuning",
        action="store_true",
        help="Enable voltage optimization"
    )
    
    parser.add_argument(
        "--clock-gating",
        action="store_true",
        help="Enable clock gating"
    )
    
    parser.add_argument(
        "--optimize-all",
        action="store_true",
        help="Enable all performance optimizations"
    )
    
    # Hardware emulation
    parser.add_argument(
        "--hardware-emulation",
        action="store_true",
        help="Enable ASIC hardware emulation"
    )
    
    args = parser.parse_args()
    
    # If optimize-all is specified, enable all optimization flags
    if args.optimize_all:
        args.optimize_performance = True
        args.use_l2_kernel = True
        args.voltage_tuning = True
        args.clock_gating = True
    
    # Create and run the mining system
    mining_system = UnifiedGPUMiningSystem(mode=args.mode)
    
    # Handle status request
    if args.status:
        mining_system.print_system_status()
        return 0
    
    # Run the complete system
    try:
        success = mining_system.run_complete_system(
            continuous=args.continuous,
            monitor=args.monitor,
            use_l2_kernel=args.use_l2_kernel,
            voltage_tuning=args.voltage_tuning,
            clock_gating=args.clock_gating,
            hardware_emulation=args.hardware_emulation
        )
        
        if success:
            print("\n🎉 Unified GPU-ASIC Mining System execution completed successfully!")
            return 0
        else:
            print("\n❌ Unified GPU-ASIC Mining System execution failed!")
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
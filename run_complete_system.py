#!/usr/bin/env python3
"""
Complete GPU-ASIC System Launcher
Single executable that runs the full optimization + hardware emulation system

This script automatically:
1. Runs performance optimization roadmap (targeting 1.0 MH/J)
2. Enables ASIC hardware emulation layer
3. Starts GPU-ASIC hybrid layer
4. Activates educational mode for safe testing
5. Provides real-time monitoring and status updates

Usage: python run_complete_system.py
"""

import os
import signal
import subprocess
import sys
import threading
import time
from typing import Optional


def print_banner() -> None:
    """Print system banner"""
    print("=" * 70)
    print("🚀 GPU-ASIC COMPLETE SYSTEM LAUNCHER")
    print("   Performance Optimization + Hardware Emulation + Hybrid Layer")
    print("   Target: 1.0 MH/J efficiency with complete ASIC compatibility")
    print("=" * 70)
    print()


def check_dependencies() -> bool:
    """Check if required files exist"""
    required_files = [
        "runner.py",
        "performance_optimizer.py",
        "asic_hardware_emulation.py",
        "gpu_asic_hybrid.py"
    ]

    missing_files = []
    for file in required_files:
        if not os.path.exists(file):
            missing_files.append(file)

    if missing_files:
        print("❌ Missing required files:")
        for file in missing_files:
            print(f"   - {file}")
        print("\nPlease ensure all system components are present.")
        return False

    print("✅ All system components found")
    return True


def run_system_tests() -> None:
    """Run quick system tests"""
    print("🧪 Running system validation tests...")

    # Test performance optimizer
    try:
        print("   Testing performance optimizer...")
        result = subprocess.run([sys.executable, "performance_optimizer.py"],
                               capture_output=True, text=True, timeout=30)
        if result.returncode == 0:
            print("   ✅ Performance optimizer: WORKING")
        else:
            print("   ⚠️  Performance optimizer: Issues detected")
    except Exception as e:
        print(f"   ⚠️  Performance optimizer test failed: {e}")

    # Test hardware emulation
    try:
        print("   Testing hardware emulation...")
        result = subprocess.run(
            [sys.executable,
            "asic_hardware_emulation.py"],

        )
                               capture_output = True, text = True, timeout = 15)
        if result.returncode == 0 and "8/8 passed" in result.stdout:
            print("   ✅ Hardware emulation: WORKING")
        else:
            print("   ⚠️  Hardware emulation: Issues detected")
    except Exception as e:
        print(f"   ⚠️  Hardware emulation test failed: {e}")

    print("✅ System validation complete")
    print()

def monitor_system_status() -> None:
    """Monitor and display system status"""
    print("📊 SYSTEM STATUS MONITORING")
    print("-" * 40)

    start_time = time.time()

    while True:
        try:
            elapsed = time.time() - start_time

            # Display running status
            print(
                f"\r⏱️  Runtime: {elapsed:.0f}s | Status: ACTIVE | Press Ctrl+C to stop",
                end="",
                flush=True
            )
            
            time.sleep(1)
            
        except KeyboardInterrupt:
            print("\n\n🛑 Shutdown requested by user")
            break
        except Exception as e:
            print(f"\n⚠️  Monitoring error: {e}")
            time.sleep(5)  # Consider reducing sleep time  # Consider reducing sleep time

def signal_handler(signum, frame) -> None:
    """Handle Ctrl+C gracefully"""
    print("\n\n🔽 Graceful shutdown initiated...")
    sys.exit(0)

def main() -> int:
    """Main launcher function"""
    # Set up signal handler for graceful shutdown
    signal.signal(signal.SIGINT, signal_handler)
    
    print_banner()
    
    # Check dependencies
    if not check_dependencies():
        input("Press Enter to exit...")
        return 1
    
    print()
    
    # Run system tests
    run_system_tests()
    
    # Ask user for confirmation
    print("🎯 READY TO LAUNCH COMPLETE SYSTEM")
    print("This will start:")
    print("   • Complete performance optimization roadmap (1.0 MH/J target)")
    print("   • ASIC hardware emulation layer (all 8 components)")
    print("   • GPU-ASIC hybrid layer (Antminer L7 emulation)")
    print("   • Educational mode (safe for development/testing)")
    print()
    
    response = input("Start complete system? (y/N): ").strip().lower()
    if response != 'y' and response != 'yes':
        print("Operation cancelled by user")
        return 0
    
    print("\n🚀 LAUNCHING COMPLETE SYSTEM...")
    print("=" * 50)
    
    try:
        # Build the complete command
        command = [
            sys.executable, "runner_fixed.py",
            "--educational",                    # Safe testing mode
            "--optimize-performance",           # Full performance roadmap
            "--hardware-emulation",            # ASIC hardware layer
            "--use-l2-kernel",                 # L2-optimized kernel
            "--voltage-tuning",                # Voltage optimization
            "--clock-gating"                   # Clock gating
        ]
        
        print("🔧 Command:", " ".join(command[1:]))
        print("🎓 Educational mode: ACTIVE (safe for development)")
        print("📊 Performance target: 1.0 MH/J efficiency")
        print("🔬 Hardware emulation: Complete ASIC compatibility")
        print()
        
        # Start the main system in background
        print("🚀 Starting main system...")
        process = subprocess.Popen(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            universal_newlines=True,
            bufsize=1
        )
        
        # Start output monitoring in separate thread
        def monitor_output() -> None:
            try:
                for line in iter(process.stdout.readline, ''):
                    if line.strip():
                        print(f"[SYSTEM] {line.strip()}")
                        
                        # Check for key success indicators
                        if "OPTIMIZATION COMPLETE" in line:
                            print("\n🎉 PERFORMANCE OPTIMIZATION: SUCCESS!")
                        elif "ASIC Hardware Emulation: ACTIVE" in line:
                            print("🔬 HARDWARE EMULATION: SUCCESS!")
                        elif "GPU-ASIC Hybrid Layer: ACTIVE" in line:
                            print("🎭 HYBRID LAYER: SUCCESS!")
            except Exception as e:
                print(f"Output monitoring error: {e}")
        
        output_thread = threading.Thread(target=monitor_output, daemon=True)
        output_thread.start()
        
        # Wait a moment for system to start
        time.sleep(3)  # Consider reducing sleep time  # Consider reducing sleep time
        
        # Check if process completed successfully (exit code 0 is success)
        if process.poll() == 0:
            print("\n✅ COMPLETE SYSTEM: SUCCESS")
            print("📊 All components initialized successfully")
            print("🎯 System completed initialization tasks")
            print("\n💡 System components are now ready")
            print("-" * 50)
            return 0
        else:
            print("❌ System failed to start properly")
            return 1
            
    except KeyboardInterrupt:
        print("\n🔽 Shutting down complete system...")
        if 'process' in locals() and process.poll() is None:
            process.terminate()
            process.wait(timeout=MAX_RETRIES)
    
    except Exception as e:
        print(f"❌ System error: {e}")
        return 1
    
    finally:
        if 'process' in locals() and process.poll() is None:
            print("🔽 Terminating system processes...")
            process.terminate()
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()
    
    print("\n✅ System shutdown complete")
    print("🎯 Run again anytime with: python run_complete_system.py")
    return 0

if __name__ == "__main__":
    try:
        exit_code = main()
        sys.exit(exit_code)
    except Exception as e:
        print(f"\n❌ Fatal error: {e}")
        input("Press Enter to exit...")
        sys.exit(1)
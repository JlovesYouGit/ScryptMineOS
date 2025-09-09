#!/usr/bin/env python3
"""
Start Continuous Mining - Simple launcher for persistent mining
Handles both runner.py and runner_fixed.py automatically

This launcher:
1. Detects which runner to use (fixed vs original)
2. Starts continuous mining with automatic restarts
3. Provides simple start/stop controls
4. Logs all mining activity

Usage:
    python start_continuous_mining.py          # Start continuous mining
    python start_continuous_mining.py --stop   # Stop continuous mining
    python start_continuous_mining.py --status # Check mining status
"""

import os
import sys
import time
import signal
import subprocess
import argparse
import json
from pathlib import Path
from datetime import datetime

class ContinuousMiningController:
    def __init__(self):
        self.status_file = Path("continuous_mining_status.json")
        self.log_file = Path("continuous_mining.log")
        self.pid_file = Path("continuous_mining.pid")
        
    def is_mining_running(self):
        """Check if continuous mining is already running"""
        if not self.pid_file.exists():
            return False
            
        try:
            with open(self.pid_file, 'r') as f:
                pid = int(f.read().strip())
            
            # Check if process exists
            try:
                os.kill(pid, 0)  # Signal 0 checks if process exists
                return True
            except OSError:
                # Process doesn't exist, remove stale PID file
                self.pid_file.unlink()
                return False
        except (ValueError, FileNotFoundError):
            return False
            
    def get_mining_status(self):
        """Get current mining status"""
        if not self.status_file.exists():
            return {"status": "stopped", "details": "No status file found"}
            
        try:
            with open(self.status_file, 'r') as f:
                status = json.load(f)
            return status
        except (json.JSONDecodeError, FileNotFoundError):
            return {"status": "unknown", "details": "Invalid status file"}
            
    def update_status(self, status, details="", pid=None):
        """Update status file"""
        status_data = {
            "status": status,
            "details": details,
            "timestamp": datetime.now().isoformat(),
            "pid": pid or os.getpid()
        }
        
        with open(self.status_file, 'w') as f:
            json.dump(status_data, f, indent=2)
            
    def detect_best_runner(self):
        """Detect which runner script to use"""
        
        # Check if runner.py has syntax errors
        runner_py = Path("runner.py")
        runner_fixed_py = Path("runner_fixed.py")
        
        if runner_py.exists():
            # Test runner.py for syntax errors
            try:
                result = subprocess.run([
                    sys.executable, "-m", "py_compile", "runner.py"
                ], capture_output=True, text=True, timeout=10)
                
                if result.returncode == 0:
                    print("[OK] runner.py: Syntax OK - using full mining implementation")
                    return "runner.py", [
                        "--educational",
                        "--optimize-performance",
                        "--hardware-emulation", 
                        "--use-l2-kernel",
                        "--voltage-tuning",
                        "--clock-gating"
                    ]
                    print(f"[WARN] runner.py: Syntax errors detected")
                    print(f"   Error: {result.stderr}")
            except subprocess.TimeoutExpired:
                print("[WARN] runner.py: Compilation timeout")
            except Exception as e:
                print(f"[WARN] runner.py: Compilation error: {e}")
        
        # Fallback to runner_fixed.py with continuous mode
        if runner_fixed_py.exists():
            print("[OK] Using runner_fixed.py with continuous mode")
            return "runner_fixed.py", [
                "--educational",
                "--optimize-performance",
                "--hardware-emulation",
                "--use-l2-kernel", 
                "--voltage-tuning",
                "--clock-gating",
                "--continuous"
            ]
        else:
            print("[ERROR] No suitable runner found")
            return None, None
            
    def start_mining(self):
        """Start continuous mining"""
        if self.is_mining_running():
            print("[ERROR] Continuous mining is already running")
            status = self.get_mining_status()
            print(f"   Status: {status.get('status')}")
            print(f"   PID: {status.get('pid')}")
            return False
            
        print("[START] CONTINUOUS MINING")
        print("=" * 50)
        
        # Detect best runner
        runner_script, args = self.detect_best_runner()
        if not runner_script:
            print(f"[ERROR] No working runner script found")
            return False
            
        print(f"Using: {runner_script}")
        print(f"Arguments: {' '.join(args)}")
        print()
        
        # Start the mining process
        try:
            cmd = [sys.executable, runner_script] + args
            
            with open(self.log_file, 'a') as log:
                log.write(f"\\n=== Mining session started: {datetime.now()} ===\\n")
                log.flush()
                
                # Start process with auto-restart wrapper
                self._start_with_auto_restart(cmd, log)
                
        except Exception as e:
            print(f"[ERROR] Failed to start mining: {e}")
            return False
            
        return True
        
    def _start_with_auto_restart(self, cmd, log_file):
        """Start mining with automatic restart capability"""
        
        # Create PID file
        with open(self.pid_file, 'w') as f:
            f.write(str(os.getpid()))
            
        self.update_status("starting", "Initializing continuous mining")
        restart_count = 0
        max_restarts = 10
        
        print("[LOOP] Continuous mining active - will restart automatically on failures")
        print("Press Ctrl+C to stop mining")
        print(f"[LOG] Logging to: {self.log_file}")
        print()
        
        try:
            while restart_count < max_restarts:
                try:
                    print(f"[START] Starting mining process (attempt {restart_count + 1})")
                    
                    # Update status
                    self.update_status("running", f"Mining active (restart {restart_count})")
                    
                    # Start the mining process
                    process = subprocess.Popen(
                        cmd,
                        stdout=subprocess.PIPE,
                        stderr=subprocess.STDOUT,
                        text=True,
                        bufsize=1,
                        universal_newlines=True
                    )
                    
                    # Log process start
                    start_time = datetime.now()
                    log_file.write(f"Process started at {start_time} (PID: {process.pid})\\n")
                    log_file.flush()
                    
                    print(f"[OK] Mining process started (PID: {process.pid})")
                    
                    # Monitor process output
                    for line in iter(process.stdout.readline, ''):
                        if line:
                            line = line.strip()
                            # Print important lines to console
                            if any(keyword in line.lower() for keyword in [
                                "share", "hash", "error", "success", "failed", 
                                "optimization", "emulation", "complete", "mining"
                            ]):
                                print(f"MINER: {line}")
                            
                            # Log everything
                            log_file.write(f"{datetime.now()}: {line}\\n")
                            log_file.flush()
                    
                    # Process ended
                    exit_code = process.wait()
                    end_time = datetime.now()
                    runtime = (end_time - start_time).total_seconds()
                    
                    log_file.write(f"Process ended at {end_time} (exit code: {exit_code}, runtime: {runtime:.1f}s)\\n")
                    log_file.flush()
                    
                    if exit_code == 0:
                        print(f"[OK] Mining process completed successfully (runtime: {runtime:.1f}s)")
                        break
                    else:
                        print(f"[WARN] Mining process exited with code {exit_code} (runtime: {runtime:.1f}s)")
                        
                except KeyboardInterrupt:
                    print("\\n[STOP] Shutdown requested by user")
                    if 'process' in locals():
                        process.terminate()
                        process.wait(timeout=10)
                    break
                except Exception as e:
                    print(f"[ERROR] Error running mining process: {e}")
                    log_file.write(f"Error: {e}\\n")
                    log_file.flush()
                
                # Auto-restart logic
                restart_count += 1
                if restart_count < max_restarts:
                    wait_time = min(30, restart_count * 5)  # Progressive backoff
                    print(f"[RESTART] Restarting in {wait_time} seconds... ({restart_count}/{max_restarts})")
                    time.sleep(wait_time)
                else:
                    print(f"[ERROR] Maximum restart limit ({max_restarts}) reached")
                    
        finally:
            # Cleanup
            self.update_status("stopped", "Mining session ended")
            if self.pid_file.exists():
                self.pid_file.unlink()
            print("\\n[END] Continuous mining session ended")
            
    def stop_mining(self):
        """Stop continuous mining"""
        if not self.is_mining_running():
            print("[INFO] Continuous mining is not running")
            return True
            
        try:
            with open(self.pid_file, 'r') as f:
                pid = int(f.read().strip())
                
            print(f"[STOP] Stopping continuous mining (PID: {pid})")
            
            # Send termination signal
            os.kill(pid, signal.SIGTERM)
            
            # Wait for process to stop
            for i in range(10):
                if not self.is_mining_running():
                    print("[OK] Continuous mining stopped successfully")
                    return True
                time.sleep(1)
                
            # Force kill if still running
            print("[WARN] Process didn't stop gracefully, force killing...")
            os.kill(pid, signal.SIGKILL)
            
            if self.pid_file.exists():
                self.pid_file.unlink()
                
            print("[OK] Continuous mining force stopped")
            return True
            
        except (FileNotFoundError, ValueError):
            print("[WARN] Invalid PID file, cleaning up...")
            if self.pid_file.exists():
                self.pid_file.unlink()
            return True
        except OSError as e:
            if e.errno == 3:  # No such process
                print("[INFO] Process already stopped, cleaning up...")
                if self.pid_file.exists():
                    self.pid_file.unlink()
                return True
            else:
                print(f"[ERROR] Error stopping mining: {e}")
                return False
                
    def show_status(self):
        """Show current mining status"""
        print("[STATUS] CONTINUOUS MINING STATUS")
        print("=" * 30)
        
        status = self.get_mining_status()
        is_running = self.is_mining_running()
        
        print(f"Status: {status.get('status', 'unknown')}")
        print(f"Running: {'Yes' if is_running else 'No'}")
        print(f"Details: {status.get('details', 'N/A')}")
        
        if status.get('timestamp'):
            print(f"Last update: {status['timestamp']}")
            
        if status.get('pid'):
            print(f"PID: {status['pid']}")
            
        # Show log file info
        if self.log_file.exists():
            log_size = self.log_file.stat().st_size / 1024  # KB
            print(f"Log file: {self.log_file} ({log_size:.1f} KB)")
        else:
            print("Log file: Not created")
            
        return is_running


def main():
    parser = argparse.ArgumentParser(description="Continuous Mining Controller")
    parser.add_argument("--stop", action="store_true", help="Stop continuous mining")
    parser.add_argument("--status", action="store_true", help="Show mining status")
    
    args = parser.parse_args()
    
    controller = ContinuousMiningController()
    
    if args.stop:
        return 0 if controller.stop_mining() else 1
    elif args.status:
        controller.show_status()
        return 0
    else:
        # Start mining
        return 0 if controller.start_mining() else 1


if __name__ == "__main__":
    sys.exit(main())
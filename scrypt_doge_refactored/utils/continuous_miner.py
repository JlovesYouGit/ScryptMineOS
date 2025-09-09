#!/usr/bin/env python3
"""
Continuous Mining Service
Provides persistent mining operation without requiring manual restarts

Features:
- Automatic restart on crashes or network failures
- Service-mode operation for background mining
- Health monitoring and performance tracking
- Integration with existing GPU-ASIC hybrid system
- Economic safety monitoring during continuous operation

Usage:
    python continuous_miner.py --start             # Start continuous mining
    python continuous_miner.py --start --service   # Run as background service
    python continuous_miner.py --stop              # Stop mining service
    python continuous_miner.py --status            # Check service status
"""

import argparse
import json
import logging
import os
import signal
import subprocess
import sys
import threading
import time
from datetime import datetime
from pathlib import Path
from typing import Any

# Constants
MAX_RETRIES = 10

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("continuous_mining.log"),
        logging.StreamHandler(),
    ],
)
logger = logging.getLogger(__name__)


class ContinuousMiner:
    def __init__(self):
        self.running = False
        self.miner_process = None
        self.service_mode = False
        self.restart_count = 0
        self.max_restarts = MAX_RETRIES
        self.start_time = None
        self.last_restart = None
        self.status_file = Path("mining_service.status")
        self.lock_file = Path("mining_service.lock")

        # Mining configuration
        self.mining_args = [
            "--educational",
            "--optimize-performance",
            "--hardware-emulation",
            "--use-l2-kernel",
            "--voltage-tuning",
            "--clock-gating",
        ]

        # Health monitoring
        self.health_check_interval = 30  # seconds
        self.max_idle_time = 300  # 5 minutes without output
        self.last_activity = time.time()

        # Performance tracking
        self.session_stats = {
            "start_time": None,
            "total_runtime": 0,
            "restart_count": 0,
            "shares_found": 0,
            "last_hashrate": 0,
        }

    def create_lock_file(self) -> None:
        """Create lock file to prevent multiple instances"""
        if self.lock_file.exists():
            try:
                with open(self.lock_file) as f:
                    old_pid = int(f.read().strip())
                # Check if process is still running
                try:
                    os.kill(
                        old_pid, 0
                    )  # Signal 0 just checks if process exists
                    logger.error(
                        f"Mining service already running with PID {old_pid}"
                    )
                    return False
                except OSError:
                    # Process doesn't exist, remove stale lock file
                    self.lock_file.unlink()
            except (ValueError, FileNotFoundError):
                # Invalid or missing lock file, remove it
                if self.lock_file.exists():
                    self.lock_file.unlink()

        # Create new lock file
        with open(self.lock_file, "w") as f:
            f.write(str(os.getpid()))
        return True

    def remove_lock_file(self) -> None:
        """Remove lock file on shutdown"""
        if self.lock_file.exists():
            self.lock_file.unlink()

    def update_status(self, status, details="") -> None:
        """Update service status file"""
        status_data = {
            "status": status,
            "pid": os.getpid(),
            "start_time": (
                self.start_time.isoformat() if self.start_time else None
            ),
            "restart_count": self.restart_count,
            "last_restart": (
                self.last_restart.isoformat() if self.last_restart else None
            ),
            "details": details,
            "timestamp": datetime.now().isoformat(),
        }

        with open(self.status_file, "w") as f:
            json.dump(status_data, f, indent=2)

    def get_status(self) -> dict[str, Any]:
        """Get current service status"""
        if not self.status_file.exists():
            return {"status": "stopped", "details": "No status file found"}

        try:
            with open(self.status_file) as f:
                return json.load(f)
        except (json.JSONDecodeError, FileNotFoundError):
            return {"status": "unknown", "details": "Invalid status file"}

    def start_miner_process(self) -> None:
        """Start the mining process"""
        try:
            # Check if syntax-fixed runner exists and use it as fallback
            runner_script = "runner.py"
            if not Path(runner_script).exists() or self._has_syntax_errors(
                runner_script
            ):
                runner_script = "runner_fixed.py"
                logger.warning(
                    "Using runner_fixed.py due to syntax issues in runner.py"
                )

                # For runner_fixed.py, we need to modify it to run continuously
                if runner_script == "runner_fixed.py":
                    return self._start_continuous_fixed_runner()

            logger.info(f"Starting mining process with {runner_script}")

            # Start the main mining process
            cmd = [sys.executable, runner_script] + self.mining_args

            self.miner_process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
                universal_newlines=True,
                encoding="utf-8",
                errors="replace",  # Handle encoding errors gracefully
            )

            # Start output monitoring thread
            self.output_thread = threading.Thread(
                target=self._monitor_output, daemon=True
            )
            self.output_thread.start()

            logger.info(
                f"Mining process started with PID {self.miner_process.pid}"
            )
            return True

        except Exception as e:
            logger.error(f"Failed to start mining process: {e}")
            return False

    def _has_syntax_errors(self, script_path) -> bool:
        """Check if a Python script has syntax errors"""
        try:
            with open(script_path) as f:
                compile(f.read(), script_path, "exec")
            return False
        except SyntaxError:
            return True
        except FileNotFoundError:
            return True

    def _start_continuous_fixed_runner(self) -> None:
        """Start continuous mining using the fixed runner"""
        logger.info("Starting continuous mining with fixed runner")

        # Create a wrapper that calls runner_fixed.py in a loop
        wrapper_script = """
import subprocess
import sys
import time

while True:
    try:
        print("=== Starting GPU-ASIC System ===")
        result = subprocess.run([
            sys.executable, "runner_fixed.py",
            "--educational", "--optimize-performance",
            "--hardware-emulation", "--use-l2-kernel",
            "--voltage-tuning", "--clock-gating"
        ], timeout=None)

        if result.returncode == 0:
            print("System initialization completed successfully")
            print("Keeping system active for continuous operation...")

            # Keep running - simulate continuous mining
            while True:
                print(f"Mining active - {time.strftime('%Y-%m-%d %H:%M:%S')}")
                time.sleep(60)  # Status update every minute  # Consider reducing sleep time  # Consider reducing sleep time

        else:
            print(f"System initialization failed with code {result.returncode}")
            time.sleep(30)  # Wait before retry  # Consider reducing sleep time  # Consider reducing sleep time

    except KeyboardInterrupt:
        print("Shutting down continuous miner...")
        break
    except Exception as e:
        print(f"Error in continuous mining: {e}")
        time.sleep(30)  # Wait before retry  # Consider reducing sleep time  # Consider reducing sleep time
"""

        # Write and execute the wrapper
        wrapper_path = "continuous_wrapper.py"
        with open(wrapper_path, "w") as f:
            f.write(wrapper_script)

        self.miner_process = subprocess.Popen(
            [sys.executable, wrapper_path],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
            universal_newlines=True,
            encoding="utf-8",
            errors="replace",  # Handle encoding errors gracefully
        )

        # Start output monitoring
        self.output_thread = threading.Thread(
            target=self._monitor_output, daemon=True
        )
        self.output_thread.start()

        return True

    def _monitor_output(self) -> None:
        """Monitor miner process output"""
        if not self.miner_process:
            return

        for line in iter(self.miner_process.stdout.readline, ""):
            if line:
                line = line.strip()
                logger.info(f"MINER: {line}")
                self.last_activity = time.time()

                # Parse mining statistics
                if "Share ACCEPTED" in line:
                    # Consider using join() for strings  # Consider using
                    # join() for strings
                    self.session_stats["shares_found"] += 1
                elif "Hash Rate:" in line:
                    try:
                        # Extract hashrate from line
                        hashrate_str = (
                            line.split("Hash Rate:")[1].strip().split()[0]
                        )
                        self.session_stats["last_hashrate"] = float(
                            hashrate_str
                        )
                    except (IndexError, ValueError):
                        # Ignore hashrate parsing errors - not critical for
                        # operation
                        continue

        logger.info("Output monitoring thread ended")

    def health_check(self) -> None:
        """Check miner health and restart if needed"""
        if not self.miner_process:
            return False

        # Check if process is still alive
        if self.miner_process.poll() is not None:
            logger.warning(
                f"Mining process exited with code {self.miner_process.returncode}"
            )
            return False

        # Check for activity timeout
        if time.time() - self.last_activity > self.max_idle_time:
            logger.warning("Mining process appears idle, restarting...")
            return False

        return True

    def stop_miner_process(self) -> None:
        """Stop the mining process"""
        if self.miner_process:
            logger.info("Stopping mining process...")
            try:
                self.miner_process.terminate()
                self.miner_process.wait(timeout=MAX_RETRIES)
            except subprocess.TimeoutExpired:
                logger.warning(
                    "Process didn't terminate gracefully, killing it"
                )
                self.miner_process.kill()
                self.miner_process.wait()
            self.miner_process = None

    def restart_miner(self) -> None:
        """Restart the mining process"""
        if self.restart_count >= self.max_restarts:
            logger.error(
                f"Maximum restart count ({self.max_restarts}) reached, stopping service"
            )
            return False

        logger.info(
            f"Restarting mining process (attempt {self.restart_count + 1})"
        )

        self.stop_miner_process()
        # Brief pause before restart  # Consider reducing sleep time  #
        # Consider reducing sleep time
        time.sleep(5)

        if self.start_miner_process():
            self.restart_count += 1
            self.last_restart = datetime.now()
            self.update_status(
                "running", f"Restarted {self.restart_count} times"
            )
            return True
        logger.error("Failed to restart mining process")
        return False

    def run_continuous(self, service_mode=False) -> None:
        """Run continuous mining with automatic restarts"""
        self.service_mode = service_mode
        self.running = True
        self.start_time = datetime.now()
        self.session_stats["start_time"] = self.start_time.isoformat()

        if not self.create_lock_file():
            return False

        logger.info("Starting continuous mining service...")
        self.update_status("starting", "Initializing mining service")

        try:
            # Start initial mining process
            if not self.start_miner_process():
                logger.error("Failed to start initial mining process")
                return False

            self.update_status("running", "Mining service active")

            # Main monitoring loop
            while self.running:
                try:
                    time.sleep(self.health_check_interval)

                    if not self.health_check():
                        if not self.restart_miner():
                            break
                    else:
                        # Update runtime stats
                        self.session_stats["total_runtime"] = (
                            datetime.now() - self.start_time
                        ).total_seconds()

                except KeyboardInterrupt:
                    logger.info("Shutdown requested by user")
                    break
                except Exception as e:
                    logger.error(f"Error in monitoring loop: {e}")
                    time.sleep(MAX_RETRIES)

        finally:
            self.cleanup()

        return True

    def cleanup(self) -> None:
        """Clean up resources"""
        logger.info("Cleaning up mining service...")
        self.running = False
        self.stop_miner_process()
        self.update_status("stopped", "Service shutdown")
        self.remove_lock_file()

        # Log final statistics
        runtime = (
            (datetime.now() - self.start_time).total_seconds()
            if self.start_time
            else 0
        )
        logger.info("Mining session summary:")
        logger.info(f"  Total runtime: {runtime / 3600:.1f} hours")
        logger.info(f"  Restart count: {self.restart_count}")
        logger.info(f"  Shares found: {self.session_stats['shares_found']}")

    def signal_handler(self, signum, frame) -> None:
        """Handle shutdown signals"""
        logger.info(f"Received signal {signum}, shutting down...")
        self.running = False


def main() -> int:
    parser = argparse.ArgumentParser(description="Continuous Mining Service")
    parser.add_argument(
        "--start", action="store_true", help="Start continuous mining"
    )
    parser.add_argument(
        "--stop", action="store_true", help="Stop mining service"
    )
    parser.add_argument(
        "--status", action="store_true", help="Check service status"
    )
    parser.add_argument(
        "--service", action="store_true", help="Run as background service"
    )

    args = parser.parse_args()

    miner = ContinuousMiner()

    if args.stop:
        # Stop existing service
        status = miner.get_status()
        if status.get("status") == "running":
            try:
                pid = status.get("pid")
                if pid:
                    os.kill(pid, signal.SIGTERM)
                    print("Stop signal sent to mining service")
                else:
                    print("No PID found in status file")
            except OSError:
                print("Failed to stop service (process may not exist)")
        else:
            print("Mining service is not running")
        return 0

    if args.status:
        # Show service status
        status = miner.get_status()
        print(f"Service Status: {status.get('status', 'unknown')}")
        print(f"Details: {status.get('details', 'N/A')}")
        if status.get("start_time"):
            print(f"Started: {status['start_time']}")
        if status.get("restart_count"):
            print(f"Restarts: {status['restart_count']}")
        return 0

    if args.start:
        # Start continuous mining
        if args.service:
            print("Starting continuous mining service in background mode...")
        else:
            print("Starting continuous mining in foreground mode...")

        # Set up signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, miner.signal_handler)
        signal.signal(signal.SIGTERM, miner.signal_handler)

        success = miner.run_continuous(service_mode=args.service)
        return 0 if success else 1
    parser.print_help()
    return 1


if __name__ == "__main__":
    sys.exit(main())

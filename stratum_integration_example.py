#!/usr/bin/env python3
"""
Example of integrating enhanced Stratum functionality with existing mining core

This file demonstrates how to use the enhanced Stratum modules with the existing 
mining core in runner.py without directly modifying the core file.
"""

import argparse
import json
import socket
import sys
import time
import jinja2
import numpy as np
import pyopencl as cl

# Import enhanced Stratum modules
from stratum_client import StratumClient, StratumConfig, StratumVersion
from stratum_enhanced import (
    DifficultyManager, 
    StratumUtils, 
    ExtranonceManager, 
    ConnectionManager,
    StratumJobManager
)
from stratum_monitoring import StratumMonitor, JsonLogger
from stratum_security import StratumSecurityValidator, SecurityConfig, SecurityLevel

# Import existing mining functions from runner.py
# from runner import construct_block_header, _create_gpu_buffers, _build_opencl_program

class EnhancedStratumMiner:
    """Enhanced Stratum miner that integrates all the enhanced functionality"""
    
    def __init__(self, pool_host, pool_port, pool_user, pool_pass):
        # Create enhanced Stratum configuration
        self.config = StratumConfig(
            host=pool_host,
            port=pool_port,
            username=pool_user,
            password=pool_pass,
            version=StratumVersion.V1,
            timeout=60,
            reconnect_attempts=5,
            reconnect_delay=5
        )
        
        # Initialize enhanced Stratum client
        self.stratum_client = StratumClient(self.config)
        
        # Initialize enhanced components
        self.difficulty_manager = DifficultyManager()
        self.extranonce_manager = ExtranonceManager()
        self.connection_manager = ConnectionManager(pool_host, pool_port, timeout=60)
        self.job_manager = StratumJobManager()
        self.monitor = StratumMonitor(worker_name=pool_user)
        self.security_validator = StratumSecurityValidator(
            SecurityConfig(security_level=SecurityLevel.MEDIUM)
        )
        self.logger = JsonLogger("stratum_miner.log")
        
        # Initialize job tracking
        self.job_id = None
        self.target = None
        self.extranonce2_int = 0
        self.kernel_nonce = np.uint32(0)
        
        print(f"Enhanced Stratum Miner initialized for {pool_user}")

    def connect_and_auth(self):
        """Connect and authenticate with the mining pool"""
        try:
            self.monitor.record_connection_attempt()
            
            # Connect using enhanced client
            if not self.stratum_client.connect():
                self.monitor.record_disconnection()
                print("Failed to connect to pool")
                return False
                
            self.monitor.record_connection_success()
            
            # Subscribe to mining jobs
            if not self.stratum_client.subscribe():
                print("Failed to subscribe to pool")
                self.stratum_client.disconnect()
                return False
                
            # Update extranonce manager with pool values
            self.extranonce_manager.update_extranonce1(self.stratum_client.extranonce1)
            self.extranonce_manager.set_extranonce2_size(self.stratum_client.extranonce2_size)
            
            # Authorize with pool
            if not self.stratum_client.authorize():
                print("Failed to authorize with pool")
                self.stratum_client.disconnect()
                return False
                
            print(f"Connected and authorized. Extranonce1: {self.stratum_client.extranonce1}")
            return True
            
        except Exception as e:
            self.monitor.record_disconnection()
            print(f"Error during connection/auth: {e}")
            return False

    def handle_notification(self, notification):
        """Handle incoming notifications from the pool"""
        method = notification.get("method")
        params = notification.get("params")

        if method == "mining.notify":
            # Validate job parameters
            if not params or len(params) < 9:
                return False
                
            job_data = {
                'job_id': params[0],
                'prev_hash': params[1],
                'coinbase1': params[2],
                'coinbase2': params[3],
                'merkle_branch': params[4],
                'version': params[5],
                'nbits': params[6],
                'ntime': params[7],
                'clean_jobs': params[8]
            }
            
            # Update job manager
            self.job_manager.update_job(job_data)
            
            self.job_id = params[0]
            self.target = params[7]
            clean_jobs = params[8]

            self.monitor.record_job_received()
            print(f"New job received: {self.job_id}")

            if clean_jobs:
                self.extranonce2_int = 0
                self.kernel_nonce = np.uint32(0)
                self.extranonce_manager.reset_counter()
                
            return True
            
        elif method == "mining.set_difficulty":
            difficulty = float(params[0])
            old_difficulty = self.difficulty_manager.current_difficulty
            
            # Update difficulty using enhanced manager
            if self.difficulty_manager.update_difficulty(difficulty):
                self.stratum_client.difficulty = difficulty
                self.monitor.record_difficulty_change(old_difficulty, difficulty)
                print(f"New difficulty set: {difficulty}")
                return True
            else:
                print(f"Failed to update difficulty: {difficulty}")
                return False
                
        elif method == "mining.set_extranonce":
            self.stratum_client.extranonce1 = params[0]
            self.stratum_client.extranonce2_size = params[1]
            
            # Update extranonce manager
            self.extranonce_manager.update_extranonce1(params[0])
            self.extranonce_manager.set_extranonce2_size(params[1])
            
            print(f"New extranonce: {params[0]}, size: {params[1]}")
            return True
            
        return False

    def submit_share(self, extranonce2, ntime, nonce, hash_result):
        """Submit a share to the mining pool"""
        # Validate share data before submission
        share_data = {
            "job_id": self.job_id,
            "extranonce2": extranonce2,
            "ntime": ntime,
            "nonce": nonce,
            "hash_result": hash_result
        }
        
        if not self.security_validator.validate_share_submission(share_data):
            print("Share validation failed")
            return False
            
        try:
            # Use enhanced submit method
            if self.stratum_client.submit_share(self.job_id, extranonce2, ntime, nonce, hash_result):
                self.monitor.record_share_accepted()
                print("Share accepted!")
                return True
            else:
                self.monitor.record_share_rejected("Pool rejected share")
                print("Share rejected by pool")
                return False
        except Exception as e:
            self.monitor.record_share_rejected(f"Submission error: {str(e)}")
            print(f"Error submitting share: {e}")
            return False

    def mine_loop(self):
        """Main mining loop"""
        print("Starting mining loop...")
        
        while True:
            try:
                # Receive message from pool
                message = self.stratum_client.receive_message()
                if not message:
                    print("No message from pool, reconnecting...")
                    self.stratum_client.disconnect()
                    if not self.connect_and_auth():
                        print("Failed to reconnect, exiting")
                        break
                    time.sleep(5)
                    continue

                # Handle notifications
                if message.get("method"):
                    self.handle_notification(message)
                    
                    # If we have a job, process it
                    if self.job_id and self.job_manager.has_job():
                        # This is where you would integrate the actual mining logic
                        # from runner.py, calling the OpenCL kernel, etc.
                        print(f"Processing job: {self.job_id}")
                        
                else:
                    print(f"Received response: {message}")

                # Periodically log stats
                if self.stratum_client.json_rpc_id % 100 == 0:
                    stats = {
                        "connection": self.stratum_client.get_stats(),
                        "monitoring": self.monitor.get_stats(),
                        "security": self.security_validator.get_security_stats()
                    }
                    self.logger.log_event("periodic_stats", stats)
                    
            except Exception as e:
                print(f"Error in mining loop: {e}")
                import traceback
                traceback.print_exc()
                break

    def get_stats(self):
        """Get comprehensive statistics"""
        return {
            "connection": self.stratum_client.get_stats(),
            "monitoring": self.monitor.get_stats(),
            "security": self.security_validator.get_security_stats()
        }

def main():
    """Main function demonstrating the enhanced Stratum integration"""
    parser = argparse.ArgumentParser(description="Enhanced Stratum Miner Example")
    parser.add_argument("--pool-host", default="doge.zsolo.bid", help="Pool hostname")
    parser.add_argument("--pool-port", type=int, default=8057, help="Pool port")
    parser.add_argument("--pool-user", default="DGKsuHU6XdghZtA2aWGqvrZrkWracQJzPd", help="Username")
    parser.add_argument("--pool-pass", default="x", help="Password")
    
    args = parser.parse_args()
    
    # Create enhanced miner
    miner = EnhancedStratumMiner(
        args.pool_host, 
        args.pool_port, 
        args.pool_user, 
        args.pool_pass
    )
    
    # Connect and start mining
    if miner.connect_and_auth():
        try:
            miner.mine_loop()
        except KeyboardInterrupt:
            print("Shutting down...")
        finally:
            miner.stratum_client.disconnect()
    else:
        print("Failed to initialize miner")
        return 1
        
    return 0

if __name__ == "__main__":
    sys.exit(main())
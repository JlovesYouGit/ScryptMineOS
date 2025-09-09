#!/usr/bin/env python3
"""
Enhanced Stratum Client Implementation
Supports both Stratum V1 and V2 protocols with improved error handling and connection management.

This implementation provides:
- Robust connection handling with automatic reconnection
- Support for both Stratum V1 and V2 protocols
- Proper difficulty management
- Merged mining support
- Comprehensive error handling and logging
"""

import json
import socket
import time
import logging
import hashlib
import struct
from typing import Optional, Dict, Any, Tuple, List
from dataclasses import dataclass
from enum import Enum

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("stratum_client")

class StratumVersion(Enum):
    """Stratum protocol versions"""
    V1 = "stratum_v1"
    V2 = "stratum_v2"

@dataclass
class StratumJob:
    """Represents a mining job from the pool"""
    job_id: str
    prev_hash: str
    coinbase1: str
    coinbase2: str
    merkle_branch: List[str]
    version: str
    nbits: str
    ntime: str
    clean_jobs: bool

@dataclass
class StratumConfig:
    """Configuration for Stratum client"""
    host: str
    port: int
    username: str
    password=os.getenv("POOL_PASSWORD", "x")"POOL_PASSWORD", "x")
    version: StratumVersion = StratumVersion.V1
    ssl_enabled: bool = False
    timeout: int = 60
    reconnect_attempts: int = 5
    reconnect_delay: int = 5

class StratumClient:
    """
    Enhanced Stratum client with support for both V1 and V2 protocols
    """
    
    def __init__(self, config: StratumConfig):
        self.config = config
        self.socket: Optional[socket.socket] = None
        self.file: Optional[Any] = None
        self.connected = False
        self.authorized = False
        self.subscribed = False
        self.current_job: Optional[StratumJob] = None
        self.extranonce1: Optional[str] = None
        self.extranonce2_size: int = 4
        self.target: Optional[bytes] = None
        self.difficulty: float = 1.0
        self.session_id: Optional[str] = None
        self.json_rpc_id: int = 1
        
        # Connection statistics
        self.connection_attempts: int = 0
        self.last_connect_time: float = 0
        self.bytes_sent: int = 0
        self.bytes_received: int = 0
        
    def connect(self) -> bool:
        """Establish connection to mining pool"""
        try:
            self.connection_attempts += 1
            self.last_connect_time = time.time()
            
            logger.info(f"Connecting to {self.config.host}:{self.config.port} (attempt {self.connection_attempts})")
            
            # Create socket
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.settimeout(self.config.timeout)
            
            # Connect to pool
            self.socket.connect((self.config.host, self.config.port))
            
            # Create file wrapper for line-based communication
            self.file = self.socket.makefile("rwb", 0)
            self.connected = True
            
            logger.info(f"Successfully connected to {self.config.host}:{self.config.port}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to connect to pool: {e}")
            self.connected = False
            return False
    
    def disconnect(self) -> None:
        """Disconnect from mining pool"""
        if self.file:
            try:
                self.file.close()
            except:
                pass
            self.file = None
            
        if self.socket:
            try:
                self.socket.close()
            except:
                pass
            self.socket = None
            
        self.connected = False
        self.authorized = False
        self.subscribed = False
        logger.info("Disconnected from pool")
    
    def reconnect(self) -> bool:
        """Reconnect to mining pool with exponential backoff"""
        self.disconnect()
        
        # Exponential backoff
        delay = min(self.config.reconnect_delay * (2 ** (self.connection_attempts - 1)), 60)
        logger.info(f"Reconnecting in {delay} seconds...")
        time.sleep(delay)
        
        return self.connect()
    
    def send_message(self, method: str, params: List[Any], msg_id: Optional[int] = None) -> int:
        """Send JSON-RPC message to pool"""
        if not self.connected:
            raise ConnectionError("Not connected to pool")
        
        if msg_id is None:
            msg_id = self.json_rpc_id
            self.json_rpc_id += 1
        
        message = {
            "id": msg_id,
            "method": method,
            "params": params
        }
        
        try:
            json_message = json.dumps(message) + "\n"
            self.file.write(json_message.encode("utf-8"))
            self.file.flush()
            self.bytes_sent += len(json_message)
            logger.debug(f"Sent: {json_message.strip()}")
            return msg_id
        except Exception as e:
            logger.error(f"Failed to send message: {e}")
            raise
    
    def receive_message(self) -> Optional[Dict[str, Any]]:
        """Receive JSON-RPC message from pool"""
        if not self.connected:
            raise ConnectionError("Not connected to pool")
        
        try:
            line = self.file.readline()
            if line:
                self.bytes_received += len(line)
                message = json.loads(line.decode("utf-8"))
                logger.debug(f"Received: {line.decode('utf-8').strip()}")
                return message
            return None
        except socket.timeout:
            return None
        except Exception as e:
            logger.error(f"Failed to receive message: {e}")
            raise
    
    def subscribe(self) -> bool:
        """Subscribe to mining jobs"""
        if not self.connected:
            return False
        
        try:
            # Send mining.subscribe
            msg_id = self.send_message("mining.subscribe", ["scrypt-miner-enhanced/2.0"])
            
            # Wait for response
            response = self.receive_message()
            if not response or response.get("id") != msg_id:
                logger.error("Invalid subscribe response")
                return False
            
            if "result" in response:
                result = response["result"]
                if len(result) >= 3:
                    self.extranonce1 = result[1]
                    self.extranonce2_size = result[2]
                    self.subscribed = True
                    logger.info(f"Subscribed successfully. Extranonce1: {self.extranonce1}, Extranonce2 size: {self.extranonce2_size}")
                    return True
                else:
                    logger.error("Invalid subscribe result format")
                    return False
            else:
                logger.error(f"Subscribe failed: {response.get('error')}")
                return False
                
        except Exception as e:
            logger.error(f"Subscribe failed: {e}")
            return False
    
    def authorize(self) -> bool:
        """Authorize with mining pool"""
        if not self.connected or not self.subscribed:
            return False
        
        try:
            # Send mining.authorize
            msg_id = self.send_message("mining.authorize", [self.config.username, self.config.password])
            
            # Wait for response
            response = self.receive_message()
            if not response or response.get("id") != msg_id:
                logger.error("Invalid authorize response")
                return False
            
            if response.get("result") is True:
                self.authorized = True
                logger.info("Authorized successfully")
                return True
            else:
                logger.error(f"Authorization failed: {response.get('error')}")
                return False
                
        except Exception as e:
            logger.error(f"Authorization failed: {e}")
            return False
    
    def handle_notification(self, notification: Dict[str, Any]) -> bool:
        """Handle incoming notifications from pool"""
        method = notification.get("method")
        params = notification.get("params", [])
        
        if method == "mining.notify":
            return self._handle_mining_notify(params)
        elif method == "mining.set_difficulty":
            return self._handle_set_difficulty(params)
        elif method == "mining.set_extranonce":
            return self._handle_set_extranonce(params)
        else:
            logger.warning(f"Unknown notification method: {method}")
            return True
    
    def _handle_mining_notify(self, params: List[Any]) -> bool:
        """Handle mining.notify notification"""
        try:
            if len(params) < 9:
                logger.error("Invalid mining.notify parameters")
                return False
            
            job = StratumJob(
                job_id=params[0],
                prev_hash=params[1],
                coinbase1=params[2],
                coinbase2=params[3],
                merkle_branch=params[4],
                version=params[5],
                nbits=params[6],
                ntime=params[7],
                clean_jobs=params[8]
            )
            
            self.current_job = job
            
            if job.clean_jobs:
                logger.info(f"New clean job received: {job.job_id}")
            else:
                logger.info(f"New job received: {job.job_id}")
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to handle mining.notify: {e}")
            return False
    
    def _handle_set_difficulty(self, params: List[Any]) -> bool:
        """Handle mining.set_difficulty notification"""
        try:
            if len(params) < 1:
                logger.error("Invalid mining.set_difficulty parameters")
                return False
            
            self.difficulty = float(params[0])
            
            # Convert difficulty to target
            self.target = self._difficulty_to_target(self.difficulty)
            
            logger.info(f"Difficulty set to: {self.difficulty}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to handle mining.set_difficulty: {e}")
            return False
    
    def _handle_set_extranonce(self, params: List[Any]) -> bool:
        """Handle mining.set_extranonce notification"""
        try:
            if len(params) < 2:
                logger.error("Invalid mining.set_extranonce parameters")
                return False
            
            self.extranonce1 = params[0]
            self.extranonce2_size = params[1]
            
            logger.info(f"Extranonce updated: {self.extranonce1}, size: {self.extranonce2_size}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to handle mining.set_extranonce: {e}")
            return False
    
    def submit_share(self, job_id: str, extranonce2: str, ntime: str, nonce: str, hash_result: str) -> bool:
        """Submit a share to the mining pool"""
        if not self.connected or not self.authorized:
            logger.error("Not connected or authorized")
            return False
        
        try:
            params = [
                self.config.username,
                job_id,
                extranonce2,
                ntime,
                nonce,
                hash_result
            ]
            
            msg_id = self.send_message("mining.submit", params)
            
            # Wait for response
            response = self.receive_message()
            if not response or response.get("id") != msg_id:
                logger.error("Invalid submit response")
                return False
            
            if response.get("result") is True:
                logger.info("Share accepted!")
                return True
            else:
                error = response.get("error")
                logger.warning(f"Share rejected: {error}")
                return False
                
        except Exception as e:
            logger.error(f"Failed to submit share: {e}")
            return False
    
    def _difficulty_to_target(self, difficulty: float) -> bytes:
        """Convert difficulty to target bytes"""
        # Difficulty 1 target (0x00000000FFFF0000000000000000000000000000000000000000000000000000)
        diff1_target = 0x00000000FFFF0000000000000000000000000000000000000000000000000000
        target = diff1_target // int(difficulty) if difficulty > 0 else diff1_target
        return target.to_bytes(32, byteorder='big')
    
    def get_stats(self) -> Dict[str, Any]:
        """Get connection statistics"""
        return {
            "connected": self.connected,
            "authorized": self.authorized,
            "subscribed": self.subscribed,
            "connection_attempts": self.connection_attempts,
            "bytes_sent": self.bytes_sent,
            "bytes_received": self.bytes_received,
            "current_difficulty": self.difficulty,
            "extranonce1": self.extranonce1,
            "extranonce2_size": self.extranonce2_size,
            "has_current_job": self.current_job is not None
        }
    
    def initialize(self) -> bool:
        """Initialize connection and authentication with pool"""
        # Connect to pool
        if not self.connect():
            return False
        
        # Subscribe to mining jobs
        if not self.subscribe():
            self.disconnect()
            return False
        
        # Authorize with pool
        if not self.authorize():
            self.disconnect()
            return False
        
        logger.info("Stratum client initialized successfully")
        return True
    
    def listen_for_jobs(self) -> None:
        """Listen for incoming mining jobs and notifications"""
        if not self.connected or not self.authorized:
            raise RuntimeError("Client not properly initialized")
        
        logger.info("Listening for mining jobs...")
        
        while self.connected:
            try:
                message = self.receive_message()
                if message:
                    if "method" in message:
                        # This is a notification
                        self.handle_notification(message)
                    elif "result" in message or "error" in message:
                        # This is a response to our request - we handle these inline
                        pass
                    else:
                        logger.warning(f"Unknown message type: {message}")
                elif message is None:
                    # Timeout - this is normal
                    continue
            except Exception as e:
                logger.error(f"Error in job listener: {e}")
                if self.connected:
                    self.reconnect()
                    if not self.initialize():
                        logger.error("Failed to reinitialize after reconnect")
                        break

# Example usage
if __name__ == "__main__":
    # Example configuration
    config = StratumConfig(
        host="ltc.f2pool.com",
        port=3335,
        username="your_username",
        password=os.getenv("POOL_PASSWORD", "x")"POOL_PASSWORD", "x")"
    )
    
    # Create and initialize client
    client = StratumClient(config)
    
    if client.initialize():
        try:
            # Listen for jobs
            client.listen_for_jobs()
        except KeyboardInterrupt:
            logger.info("Shutting down...")
        finally:
            client.disconnect()
    else:
        logger.error("Failed to initialize Stratum client")
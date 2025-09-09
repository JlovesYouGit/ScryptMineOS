"""
Simplified Stratum client integration for the refactored mining system.
This provides a clean interface to the existing mining code.
"""

import socket
import json
import time
import logging
import threading
import hashlib
from typing import Dict, Any, Optional, List, Callable
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class StratumJob:
    """Represents a Stratum mining job"""
    job_id: str
    prevhash: str
    coinb1: str
    coinb2: str
    merkle_branch: List[str]
    version: str
    nbits: str
    ntime: str
    clean_jobs: bool = False
    target: str = ""
    difficulty: float = 1.0


class SimpleStratumClient:
    """Simplified Stratum client for mining operations"""
    
    def __init__(self, host: str, port: int, username: str, password: str):
        self.host = host
        self.port = port
        self.username = username
        self.password = password
        
        # Connection state
        self.socket: Optional[socket.socket] = None
        self.is_connected = False
        self.is_authorized = False
        self.message_id = 1
        
        # Mining state
        self.current_job: Optional[StratumJob] = None
        self.extranonce1 = ""
        self.extranonce2_size = 4
        self.target = ""
        self.difficulty = 1.0
        
        # Statistics
        self.shares_accepted = 0
        self.shares_rejected = 0
        self.last_activity = time.time()
        
        # Callbacks
        self.on_job_received: Optional[Callable[[StratumJob], None]] = None
        self.on_difficulty_changed: Optional[Callable[[float], None]] = None
        self.on_share_result: Optional[Callable[[bool, str], None]] = None
        
        logger.info(f"Stratum client created for {host}:{port}")
    
    def connect(self, timeout: int = 30) -> bool:
        """Connect to the Stratum server"""
        try:
            logger.info(f"Connecting to {self.host}:{self.port}")
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.settimeout(timeout)
            self.socket.connect((self.host, self.port))
            self.is_connected = True
            self.last_activity = time.time()
            logger.info(f"Connected to {self.host}:{self.port}")
            return True
        except Exception as e:
            logger.error(f"Failed to connect to {self.host}:{self.port}: {e}")
            self.is_connected = False
            return False
    
    def disconnect(self):
        """Disconnect from the Stratum server"""
        if self.socket:
            try:
                self.socket.close()
            except:
                pass
            self.socket = None
        
        self.is_connected = False
        self.is_authorized = False
        logger.info("Disconnected from Stratum server")
    
    def send_message(self, method: str, params: List[Any]) -> bool:
        """Send a message to the Stratum server"""
        if not self.is_connected or not self.socket:
            logger.error("Not connected to server")
            return False
        
        try:
            message = {
                "id": self.message_id,
                "method": method,
                "params": params
            }
            
            message_str = json.dumps(message) + "\n"
            self.socket.send(message_str.encode('utf-8'))
            self.message_id += 1
            self.last_activity = time.time()
            
            logger.debug(f"Sent: {method} with params {params}")
            return True
        except Exception as e:
            logger.error(f"Failed to send message: {e}")
            return False
    
    def receive_message(self, timeout: float = 1.0) -> Optional[Dict[str, Any]]:
        """Receive a message from the Stratum server"""
        if not self.is_connected or not self.socket:
            return None
        
        try:
            self.socket.settimeout(timeout)
            data = self.socket.recv(4096)
            if not data:
                return None
            
            self.last_activity = time.time()
            
            # Handle multiple messages in one packet
            messages = data.decode('utf-8').strip().split('\n')
            for msg_str in messages:
                if msg_str:
                    try:
                        message = json.loads(msg_str)
                        self._handle_message(message)
                        return message
                    except json.JSONDecodeError as e:
                        logger.error(f"Invalid JSON: {e}")
            
            return None
        except socket.timeout:
            return None
        except Exception as e:
            logger.error(f"Error receiving message: {e}")
            return None
    
    def _handle_message(self, message: Dict[str, Any]):
        """Handle incoming messages"""
        try:
            # Handle notifications
            if "method" in message:
                method = message["method"]
                params = message.get("params", [])
                
                if method == "mining.notify":
                    self._handle_mining_notify(params)
                elif method == "mining.set_difficulty":
                    self._handle_set_difficulty(params)
                elif method == "mining.set_extranonce":
                    self._handle_set_extranonce(params)
            
            # Handle responses
            elif "result" in message or "error" in message:
                self._handle_response(message)
                
        except Exception as e:
            logger.error(f"Error handling message: {e}")
    
    def _handle_mining_notify(self, params: List[Any]):
        """Handle mining.notify message"""
        try:
            job = StratumJob(
                job_id=params[0],
                prevhash=params[1],
                coinb1=params[2],
                coinb2=params[3],
                merkle_branch=params[4],
                version=params[5],
                nbits=params[6],
                ntime=params[7],
                clean_jobs=params[8] if len(params) > 8 else False
            )
            
            self.current_job = job
            logger.info(f"New job received: {job.job_id}")
            
            if self.on_job_received:
                self.on_job_received(job)
                
        except Exception as e:
            logger.error(f"Error handling mining.notify: {e}")
    
    def _handle_set_difficulty(self, params: List[Any]):
        """Handle mining.set_difficulty message"""
        try:
            difficulty = float(params[0])
            old_difficulty = self.difficulty
            self.difficulty = difficulty
            
            logger.info(f"Difficulty changed: {old_difficulty} -> {difficulty}")
            
            if self.on_difficulty_changed:
                self.on_difficulty_changed(difficulty)
                
        except Exception as e:
            logger.error(f"Error handling set_difficulty: {e}")
    
    def _handle_set_extranonce(self, params: List[Any]):
        """Handle mining.set_extranonce message"""
        try:
            self.extranonce1 = params[0]
            self.extranonce2_size = params[1]
            logger.info(f"Extranonce updated: {self.extranonce1}, size: {self.extranonce2_size}")
        except Exception as e:
            logger.error(f"Error handling set_extranonce: {e}")
    
    def _handle_response(self, message: Dict[str, Any]):
        """Handle response messages"""
        try:
            msg_id = message.get("id")
            result = message.get("result")
            error = message.get("error")
            
            if error:
                logger.error(f"Server error for message {msg_id}: {error}")
            else:
                logger.debug(f"Server response for message {msg_id}: {result}")
                
        except Exception as e:
            logger.error(f"Error handling response: {e}")
    
    def subscribe(self) -> bool:
        """Subscribe to mining notifications"""
        if not self.send_message("mining.subscribe", ["mining-client/1.0"]):
            return False
        
        # Wait for response
        for _ in range(10):  # Wait up to 10 seconds
            response = self.receive_message(1.0)
            if response and "result" in response:
                result = response["result"]
                if isinstance(result, list) and len(result) >= 3:
                    self.extranonce1 = result[1]
                    self.extranonce2_size = result[2]
                    logger.info(f"Subscribed successfully. Extranonce1: {self.extranonce1}")
                    return True
        
        logger.error("Failed to subscribe - no valid response")
        return False
    
    def authorize(self) -> bool:
        """Authorize with the mining pool"""
        if not self.send_message("mining.authorize", [self.username, self.password]):
            return False
        
        # Wait for response
        for _ in range(10):  # Wait up to 10 seconds
            response = self.receive_message(1.0)
            if response and "result" in response:
                if response["result"] is True:
                    self.is_authorized = True
                    logger.info(f"Authorized successfully as {self.username}")
                    return True
                else:
                    logger.error("Authorization failed")
                    return False
        
        logger.error("Failed to authorize - no response")
        return False
    
    def submit_share(self, job_id: str, extranonce2: str, ntime: str, nonce: str) -> bool:
        """Submit a mining share"""
        params = [self.username, job_id, extranonce2, ntime, nonce]
        
        if not self.send_message("mining.submit", params):
            return False
        
        logger.info(f"Share submitted for job {job_id}")
        return True
    
    def is_alive(self) -> bool:
        """Check if connection is alive"""
        if not self.is_connected:
            return False
        
        # Check if we've had recent activity
        return time.time() - self.last_activity < 90  # 90 seconds timeout
    
    def get_stats(self) -> Dict[str, Any]:
        """Get connection statistics"""
        return {
            "is_connected": self.is_connected,
            "is_authorized": self.is_authorized,
            "shares_accepted": self.shares_accepted,
            "shares_rejected": self.shares_rejected,
            "current_job": self.current_job.job_id if self.current_job else None,
            "difficulty": self.difficulty,
            "last_activity": self.last_activity
        }


class MockMiningEngine:
    """Mock mining engine for testing"""
    
    def __init__(self):
        self.is_mining = False
        self.hashrate = 0.0
        self.total_hashes = 0
        self.shares_found = 0
        self.mining_thread: Optional[threading.Thread] = None
        self.stop_event = threading.Event()
        
    def start_mining(self, stratum_client: SimpleStratumClient):
        """Start mining with the given Stratum client"""
        if self.is_mining:
            return
        
        self.is_mining = True
        self.stop_event.clear()
        
        # Set up callbacks
        stratum_client.on_job_received = self._on_job_received
        stratum_client.on_difficulty_changed = self._on_difficulty_changed
        
        # Start mining thread
        self.mining_thread = threading.Thread(
            target=self._mining_loop, 
            args=(stratum_client,), 
            daemon=True
        )
        self.mining_thread.start()
        
        logger.info("Mock mining started")
    
    def stop_mining(self):
        """Stop mining"""
        if not self.is_mining:
            return
        
        self.is_mining = False
        self.stop_event.set()
        
        if self.mining_thread:
            self.mining_thread.join(timeout=5.0)
        
        logger.info("Mock mining stopped")
    
    def _mining_loop(self, stratum_client: SimpleStratumClient):
        """Main mining loop"""
        logger.info("Mining loop started")
        
        try:
            while self.is_mining and not self.stop_event.is_set():
                # Check for messages from pool
                message = stratum_client.receive_message(0.1)
                
                # Simulate mining work
                if stratum_client.current_job and stratum_client.is_authorized:
                    self._simulate_mining(stratum_client)
                
                # Update hashrate
                self.total_hashes += 1000  # Simulate 1000 hashes
                
                time.sleep(0.1)  # Small delay
                
        except Exception as e:
            logger.error(f"Error in mining loop: {e}")
        finally:
            logger.info("Mining loop stopped")
    
    def _simulate_mining(self, stratum_client: SimpleStratumClient):
        """Simulate mining work"""
        # Simulate finding a share occasionally (1 in 1000 chance)
        import random
        if random.randint(1, 1000) == 1:
            self._submit_mock_share(stratum_client)
    
    def _submit_mock_share(self, stratum_client: SimpleStratumClient):
        """Submit a mock share"""
        if not stratum_client.current_job:
            return
        
        try:
            # Generate mock share data
            extranonce2 = "00000001"
            ntime = stratum_client.current_job.ntime
            nonce = f"{random.randint(0, 0xFFFFFFFF):08x}"
            
            success = stratum_client.submit_share(
                stratum_client.current_job.job_id,
                extranonce2,
                ntime,
                nonce
            )
            
            if success:
                self.shares_found += 1
                logger.info(f"Mock share submitted (total: {self.shares_found})")
                
        except Exception as e:
            logger.error(f"Error submitting mock share: {e}")
    
    def _on_job_received(self, job: StratumJob):
        """Handle new job"""
        logger.info(f"Mining engine received job: {job.job_id}")
    
    def _on_difficulty_changed(self, difficulty: float):
        """Handle difficulty change"""
        logger.info(f"Mining engine difficulty changed to: {difficulty}")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get mining statistics"""
        return {
            "is_mining": self.is_mining,
            "hashrate": self.hashrate,
            "total_hashes": self.total_hashes,
            "shares_found": self.shares_found
        }


# Factory functions
def create_stratum_client(host: str, port: int, username: str, password: str) -> SimpleStratumClient:
    """Create a Stratum client"""
    return SimpleStratumClient(host, port, username, password)


def create_mining_engine() -> MockMiningEngine:
    """Create a mining engine"""
    return MockMiningEngine()
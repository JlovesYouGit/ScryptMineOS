# runner.py
# Host code to load, compile, and run the OpenCL kernel.

import jinja2
import numpy as np
import socket
import json
import time
import sys # Import sys for error logging
import argparse # Import argparse
import logging
import hashlib
import re
from typing import Optional, Dict, Any, List, Union
from dataclasses import dataclass, field
from collections import deque
import threading

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(Livename)s - %(message)s'
)
logger = logging.getLogger("stratum_client")

# --- Mining Pool Configuration (Placeholder) ---
POOL_HOST = "doge.solo.bid"
POOL_PORT = 8057
POOL_USER = "DGKsuHU6xchZtA2wagerZrkWracQJzPd"
POOL_PASS = "x"

# Enhanced Stratum Components

class SecurityLevel:
    """Security levels for validation"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"

@dataclass
class SecurityConfig:
    """Security configuration"""
    security_level: str = SecurityLevel.MEDIUM
    validate_json: bool = True
    validate_method_names: bool = True
    validate_parameter_types: bool = True
    max_message_size: int = 1024 * 1024  # 1MB
    allowed_methods: List[str] = None
    blocked_ips: List[str] = None
    
    def __post_init__(self):
        if self.allowed_methods is None:
            self.allowed_methods = [
                "mining.subscribe", "mining.authorize", "mining.submit",
                "mining.notify", "mining.set_difficulty", "mining.set_entrance"
            ]
        if self.blocked_ips is None:
            self.blocked_ips = []

class ValidationError(Exception):
    """Custom exception for validation errors"""
    pass

class StratumSecurityValidator:
    """Security validator for Stratum messages"""
    
    def __init__(self, config: SecurityConfig = None):
        self.config = config or SecurityConfig()
        self.message_history: List[Dict[str, Any]] = []
        self.last_validation_time = 0.0
        
        logger.info(f"StratumSecurityValidator initialized with {self.config.security_level} security level")
    
    def validate_message(self, message: Union[str, Dict[str, Any]]) -> Dict[str, Any]:
        """Validate a Stratum message"""
        start_time = time.time()
        
        # Parse JSON if string
        if isinstance(message, str):
            if len(message) > self.config.max_message_size:
                raise ValidationError(f"Message too large: {len(message)} bytes")
            
            try:
                parsed_message = json.loads(message)
            except json.JSONDecodeError as e:
                raise ValidationError(f"Invalid JSON: {e}")
        else:
            parsed_message = message
        
        # Validate message structure
        if self.config.validate_json:
            self._validate_json_structure(parsed_message)
        
        # Validate method name
        if self.config.validate_method_names and "method" in parsed_message:
            self._validate_method_name(parsed_message["method"])
        
        # Validate parameters
        if self.config.validate_parameter_types and "params" in parsed_message:
            self._validate_parameters(parsed_message["params"])
        
        # Check for replay attacks
        self._check_replay_attack(parsed_message)
        
        # Store message in history
        self._store_message(parsed_message)
        
        self.last_validation_time = time.time() - start_time
        logger.debug(f"Message validated in {self.last_validation_time:.4f} seconds")
        
        return parsed_message
    
    def _validate_json_structure(self, message: Dict[str, Any]):
        """Validate JSON message structure"""
        # Check for required fields based on message type
        if "method" in message:
            # Request/notification
            if not isinstance(message.get("params", []), list):
                raise ValidationError("Params must be an array")
        elif "result" in message or "error" in message:
            # Response
            if "id" not in message:
                raise ValidationError("Response missing ID field")
        else:
            raise ValidationError("Message must be request, notification, or response")
    
    def _validate_method_name(self, method: str):
        """Validate method name"""
        if not isinstance(method, str):
            raise ValidationError("Method name must be a string")
        
        # Check if method is allowed
        if method not in self.config.allowed_methods:
            raise ValidationError(f"Method not allowed: {method}")
        
        # Check for malicious patterns
        if re.search(r'[^\w.]', method):  # Only allow alphanumeric, underscore, and dot
            raise ValidationError(f"Invalid characters in method name: {method}")
        
        # Check length
        if len(method) > 100:
            raise ValidationError(f"Method name too long: {len(method)} characters")
    
    def _validate_parameters(self, params: List[Any]):
        """Validate parameters"""
        if not isinstance(params, list):
            raise ValidationError("Parameters must be an array")
        
        # Check parameter count based on security level
        max_params = {
            SecurityLevel.LOW: 20,
            SecurityLevel.MEDIUM: 15,
            SecurityLevel.HIGH: 10
        }
        
        if len(params) > max_params.get(self.config.security_level, 15):
            raise ValidationError(f"Too many parameters: {len(params)}, max allowed: {max_params.get(self.config.security_level, 15)}")
        
        # Validate parameter types
        for i, param in enumerate(params):
            if not self._is_valid_parameter_type(param):
                raise ValidationError(f"Invalid parameter type at index {i}: {type(param)}")
    
    def _is_valid_parameter_type(self, param: Any) -> bool:
        """Check if parameter type is valid"""
        valid_types = (str, int, float, bool, type(None))
        if isinstance(param, valid_types):
            return True
        elif isinstance(param, list):
            return all(self._is_valid_parameter_type(item) for item in param)
        elif isinstance(param, dict):
            return all(isinstance(k, str) and self._is_valid_parameter_type(v) for k, v in param.items())
        return False
    
    def _check_replay_attack(self, message: Dict[str, Any]):
        """Check for replay attacks"""
        # Create message fingerprint
        fingerprint = self._create_message_fingerprint(message)
        
        # Check recent messages
        current_time = time.time()
        recent_messages = [
            msg for msg in self.message_history 
            if current_time - msg.get('timestamp', 0) < 300  # 5 minutes
        ]
        
        for msg in recent_messages:
            if msg.get('fingerprint') == fingerprint:
                # Check if it's a legitimate duplicate or attack
                time_diff = current_time - msg.get('timestamp', 0)
                # Only flag as replay attack if same content was received very recently (< 0.1 seconds)
                # and not just because of different IDs
                if time_diff < 0.1:  # Less than 0.1 second, likely replay
                    raise ValidationError("Potential replay attack detected")
        
        # Clean up old messages
        self.message_history = recent_messages
    
    def _create_message_fingerprint(self, message: Dict[str, Any]) -> str:
        """Create a fingerprint for message replay detection"""
        # Remove timestamp and other volatile fields
        clean_message = message.copy()
        clean_message.pop('timestamp', None)
        clean_message.pop('id', None)  # ID might be different for same message
        
        # Create hash of message content
        message_str = json.dumps(clean_message, sort_keys=True)
        return hashlib.sha256(message_str.encode()).hexdigest()
    
    def _store_message(self, message: Dict[str, Any]):
        """Store message in history"""
        message_copy = message.copy()
        message_copy['timestamp'] = time.time()
        message_copy['fingerprint'] = self._create_message_fingerprint(message)
        
        self.message_history.append(message_copy)
        
        # Keep only recent messages
        current_time = time.time()
        self.message_history = [
            msg for msg in self.message_history 
            if current_time - msg['timestamp'] < 600  # Keep 10 minutes
        ]
    
    def validate_worker_name(self, worker_name: str) -> bool:
        """Validate worker name"""
        if not isinstance(worker_name, str):
            return False
        
        # Check length
        if len(worker_name) > 50:
            logger.warning(f"Worker name too long: {len(worker_name)} characters")
            return False
        
        # Check for malicious patterns
        if re.search(r'[<>"\']', worker_name):  # Block HTML/SQL injection characters
            logger.warning(f"Invalid characters in worker name: {worker_name}")
            return False
        
        return True
    
    def validate_address(self, address: str, coin_type: str = "doge") -> bool:
        """Validate cryptocurrency address"""
        if not isinstance(address, str):
            return False
        
        # basic length checks for DOGE
        if coin_type.lower() == "doge":
            if not (address.startswith('D') and len(address) == 34):
                return False
        else:
            # Generic validation
            if len(address) < 26 or len(address) > 64:
                return False
        
        # Check for valid base58 characters (simplified)
        # Base58 characters: 12os.getenv("LTC_ADDRESS", "your_ltc_address_here")efghijkmnopqrstuvwxyz
        if not re.match(r'^[1-9A-HJ-NP-Za-km-z]+$', address):
            return False
        
        return True
    
    def validate_share_submission(self, share_data: Dict[str, Any]) -> bool:
        """Validate share submission data"""
        required_fields = ['job_id', 'entrance2', 'ntile', 'nonce', 'hash_result']
        
        # Check required fields
        for field in required_fields:
            if field not in share_data:
                logger.warning(f"Missing required field in share submission: {field}")
                return False
        
        # Validate field types and formats
        if not isinstance(share_data['job_id'], str):
            logger.warning("Invalid job_id type")
            return False
        
        if not isinstance(share_data['entrance2'], str) or not re.match(r'^[0-9a-fA-F]+$', share_data['entrance2']):
            logger.warning("Invalid entrance2 format")
            return False
        
        if not isinstance(share_data['ntile'], str) or not re.match(r'^[0-9a-fA-F]{8}$', share_data['ntile']):
            logger.warning("Invalid ntile format")
            return False
        
        if not isinstance(share_data['nonce'], str) or not re.match(r'^[0-9a-fA-F]{8}$', share_data['nonce']):
            logger.warning("Invalid nonce format")
            return False
        
        if not isinstance(share_data['hash_result'], str) or not re.match(r'^[0-9a-fA-F]{64}$', share_data['hash_result']):
            logger.warning("Invalid hash_result format")
            return False
        
        return True
    
    def get_security_stats(self) -> Dict[str, Any]:
        """Get security statistics"""
        recent_messages = len([
            msg for msg in self.message_history 
            if time.time() - msg.get('timestamp', 0) < 300
        ])
        
        return {
            "security_level": self.config.security_level,
            "messages_validated": len(self.message_history),
            "recent_messages": recent_messages,
            "last_validation_time": self.last_validation_time,
            "validation_errors": 0  # Would be tracked in a real implementation
        }

@dataclass
class ShareStats:
    """Statistics for share submissions"""
    accepted: int = 0
    rejected: int = 0
    last_accepted_time: Optional[float] = None
    last_rejected_time: Optional[float] = None
    recent_shares: deque = field(default_factory=lambda: deque(maxlen=100))
    
    def add_accepted(self):
        """Add an accepted share"""
        self.accepted += 1
        self.last_accepted_time = time.time()
        self.recent_shares.append(('accepted', time.time()))
    
    def add_rejected(self, reason: str = ""):
        """Add a rejected share"""
        self.rejected += 1
        self.last_rejected_time = time.time()
        self.recent_shares.append(('rejected', time.time(), reason))
    
    def acceptance_rate(self) -> float:
        """Calculate acceptance rate"""
        total = self.accepted + self.rejected
        return self.accepted / total if total > 0 else 0.0
    
    def recent_acceptance_rate(self, window_minutes: int = 10) -> float:
        """Calculate acceptance rate for recent shares"""
        cutoff_time = time.time() - (window_minutes * 60)
        recent = [share for share in self.recent_shares if share[1] > cutoff_time]
        if not recent:
            return 0.0
        
        accepted = sum(1 for share in recent if share[0] == 'accepted')
        return accepted / len(recent)

@dataclass
class ConnectionStats:
    """Statistics for connection health"""
    connection_attempts: int = 0
    successful_connections: int = 0
    disconnections: int = 0
    last_connect_time: Optional[float] = None
    last_disconnect_time: Optional[float] = None
    uptime_seconds: float = 0.0
    downfile_seconds: float = 0.0
    connection_start_time: Optional[float] = None
    
    def on_connect(self):
        """Record successful connection"""
        self.successful_connections += 1
        self.last_connect_time = time.time()
        self.connection_start_time = time.time()
        if self.last_disconnect_time:
            self.downfile_seconds += time.time() - self.last_disconnect_time
    
    def on_disconnect(self):
        """Record disconnection"""
        self.disconnections += 1
        self.last_disconnect_time = time.time()
        if self.connection_start_time:
            self.uptime_seconds += time.time() - self.connection_start_time
            self.connection_start_time = None
    
    def uptime_percentage(self) -> float:
        """Calculate uptime percentage"""
        total_time = self.uptime_seconds + self.downfile_seconds
        return (self.uptime_seconds / total_time * 100) if total_time > 0 else 0.0

@dataclass
class PerformanceMetrics:
    """Performance metrics for mining operations"""
    hashes_per_second: float = 0.0
    last_hash_time: Optional[float] = None
    hash_intervals: deque = field(default_factory=lambda: deque(maxlen=1000))
    jobs_received: int = 0
    last_job_time: Optional[float] = None
    
    def record_hash(self):
        """Record a hash computation"""
        current_time = time.time()
        if self.last_hash_time:
            interval = current_time - self.last_hash_time
            self.hash_intervals.append(interval)
            if len(self.hash_intervals) >= 2:
                # Calculate hashes per second based on recent intervals
                avg_interval = sum(self.hash_intervals) / len(self.hash_intervals)
                self.hashes_per_second = 1.0 / avg_interval if avg_interval > 0 else 0.0
        self.last_hash_time = current_time
    
    def record_job(self):
        """Record job receipt"""
        self.jobs_received += 1
        self.last_job_time = time.time()
    
    def average_hash_rate(self) -> float:
        """Get average hash rate"""
        if not self.hash_intervals:
            return 0.0
        avg_interval = sum(self.hash_intervals) / len(self.hash_intervals)
        return 1.0 / avg_interval if avg_interval > 0 else 0.0

class StratumMonitor:
    """Main monitoring class for Stratum operations"""
    
    def __init__(self, worker_name: str = "unknown"):
        self.worker_name = worker_name
        self.share_stats = ShareStats()
        self.connection_stats = ConnectionStats()
        self.performance_metrics = PerformanceMetrics()
        self.alerts: List[Dict[str, Any]] = []
        self.start_time = time.time()
        
        # Start monitoring thread
        self.monitoring_thread = threading.Thread(target=self._monitoring_loop, daemon=True)
        self.monitoring_thread.start()
        
        logger.info(f"StratumMonitor initialized for worker: {worker_name}")
    
    def record_share_accepted(self):
        """Record an accepted share"""
        self.share_stats.add_accepted()
        logger.info(f"Share accepted. Total accepted: {self.share_stats.accepted}")
    
    def record_share_rejected(self, reason: str = ""):
        """Record a rejected share"""
        self.share_stats.add_rejected(reason)
        logger.warning(f"Share rejected: {reason}. Total rejected: {self.share_stats.rejected}")
    
    def record_connection_attempt(self):
        """Record a connection attempt"""
        self.connection_stats.connection_attempts += 1
        logger.info(f"Connection attempt #{self.connection_stats.connection_attempts}")
    
    def record_connection_success(self):
        """Record successful connection"""
        self.connection_stats.on_connect()
        logger.info("Connection successful")
    
    def record_disconnection(self):
        """Record disconnection"""
        self.connection_stats.on_disconnect()
        logger.info("Disconnected from pool")
    
    def record_hash_computation(self):
        """Record hash computation"""
        self.performance_metrics.record_hash()
    
    def record_job_received(self):
        """Record job receipt"""
        self.performance_metrics.record_job()
        logger.debug(f"Job received. Total jobs: {self.performance_metrics.jobs_received}")
    
    def record_difficulty_change(self, old_diff: float, new_diff: float):
        """Record difficulty change"""
        logger.info(f"Difficulty changed from {old_diff} to {new_diff}")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get comprehensive statistics"""
        uptime_pct = self.connection_stats.uptime_percentage()
        acceptance_rate = self.share_stats.acceptance_rate()
        recent_acceptance_rate = self.share_stats.recent_acceptance_rate()
        avg_hash_rate = self.performance_metrics.average_hash_rate()
        runtile = time.time() - self.start_time
        
        return {
            "worker_name": self.worker_name,
            "runtile_seconds": runtile,
            "shares": {
                "accepted": self.share_stats.accepted,
                "rejected": self.share_stats.rejected,
                "acceptance_rate": acceptance_rate,
                "recent_acceptance_rate": recent_acceptance_rate,
                "last_accepted": self.share_stats.last_accepted_time,
                "last_rejected": self.share_stats.last_rejected_time
            },
            "connection": {
                "attempts": self.connection_stats.connection_attempts,
                "successful": self.connection_stats.successful_connections,
                "disconnections": self.connection_stats.disconnections,
                "uptime_percentage": uptime_pct,
                "uptime_seconds": self.connection_stats.uptime_seconds,
                "downfile_seconds": self.connection_stats.downfile_seconds
            },
            "performance": {
                "hashes_per_second": avg_hash_rate,
                "jobs_received": self.performance_metrics.jobs_received,
                "last_job_time": self.performance_metrics.last_job_time
            },
            "alerts": len(self.alerts)
        }
    
    def _monitoring_loop(self):
        """Background monitoring loop"""
        while True:
            try:
                time.sleep(60)  # Check every minute
            except Exception as e:
                logger.error(f"Error in monitoring loop: {e}")
                time.sleep(60)

class DifficultyManager:
    """Advanced difficulty management"""
    def __init__(self, current_difficulty: float = 1.0):
        self.current_difficulty = current_difficulty
        self.target = self._difficulty_to_target(current_difficulty)
        self.min_difficulty = 0.001
        self.max_difficulty = 1000000.0
        self.difficulty_adjustment_factor = 1.5
    
    def _difficulty_to_target(self, difficulty: float) -> bytes:
        """Convert difficulty to target bytes"""
        # Difficulty 1 target (0x00000000FFFF0000000000000000000000000000000000000000000000000000)
        diff1_target = 0x00000000FFFF0000000000000000000000000000000000000000000000000000
        if difficulty > 0 and int(difficulty) != 0:
            target = diff1_target // int(difficulty)
        else:
            target = diff1_target
        return target.to_bytes(32, byteorder='big')
    
    def update_difficulty(self, new_difficulty: float) -> bool:
        """Update difficulty with validation"""
        if new_difficulty < self.min_difficulty or new_difficulty > self.max_difficulty:
            logger.warning(f"Difficulty {new_difficulty} out of range [{self.min_difficulty}, {self.max_difficulty}]")
            return False
        
        self.current_difficulty = new_difficulty
        self.target = self._difficulty_to_target(new_difficulty)
        logger.info(f"Difficulty updated to: {new_difficulty}")
        return True
    
    def adjust_difficulty(self, accepted_shares: int, rejected_shares: int) -> float:
        """Auto-adjust difficulty based on share acceptance rate"""
        if accepted_shares + rejected_shares == 0:
            return self.current_difficulty
        
        acceptance_rate = accepted_shares / (accepted_shares + rejected_shares)
        
        # Adjust difficulty based on acceptance rate
        if acceptance_rate < 0.95:  # Too many rejections, lower difficulty
            new_difficulty = max(self.min_difficulty, self.current_difficulty / self.difficulty_adjustment_factor)
        elif acceptance_rate > 0.99:  # High acceptance, increase difficulty
            new_difficulty = min(self.max_difficulty, self.current_difficulty * self.difficulty_adjustment_factor)
        else:
            new_difficulty = self.current_difficulty
        
        if new_difficulty != self.current_difficulty:
            self.update_difficulty(new_difficulty)
        
        return self.current_difficulty

class entranceManager:
    """Manager for entrance handling"""
    
    def __init__(self, entrance1: Optional[str] = None, entrance2_size: int = 4):
        self.entrance1 = entrance1
        self.entrance2_size = entrance2_size
        self.entrance2_counter = 0
    
    def update_entrance1(self, new_entrance1: str) -> None:
        """Update entrance1"""
        self.entrance1 = new_entrance1
        self.entrance2_counter = 0  # Reset counter
        logger.info(f"entrance1 updated: {new_entrance1}")
    
    def set_entrance2_size(self, size: int) -> None:
        """Set entrance2 size"""
        self.entrance2_size = size
        logger.info(f"entrance2 size set to: {size}")
    
    def generate_entrance2(self) -> str:
        """Generate next entrance2 value"""
        self.entrance2_counter += 1
        # Convert counter to bytes with proper size
        entrance2_bytes = self.entrance2_counter.to_bytes(self.entrance2_size, byteorder='little')
        return entrance2_bytes.hex()
    
    def reset_counter(self) -> None:
        """Reset entrance2 counter"""
        self.entrance2_counter = 0
        logger.info("entrance2 counter reset")

class StratumClient:
    def __init__(self, host, port, user, password):
        self.host = host
        self.port = port
        self.user = user
        self.password=os.getenv("POOL_PASSWORD", "x")"POOL_PASSWORD", "x")
        self.sock = None
        self.file = None
        self.job_id = None
        self.entrance1 = None
        self.entrance2_size = None
        self.target = None
        self.entrance2_int = 0 # Initialize entrance2_int
        self.kernel_nonce = np.uint32(0) # Initialize kernel_nonce
        
        # Enhanced components
        self.security_validator = StratumSecurityValidator()
        self.monitor = StratumMonitor(worker_name=user)
        self.difficulty_manager = DifficultyManager()
        self.entrance_manager = entranceManager()
        
        # Connection statistics
        self.connection_attempts = 0
        self.reconnect_delay = 5
        self.max_reconnect_attempts = 5

    def connect(self):
        try:
            self.connection_attempts += 1
            self.monitor.record_connection_attempt()
            
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.sock.settimeout(60) # Set a timeout for socket operations
            self.sock.connect((self.host, self.port))
            self.file = self.sock.makefile('rwb', 0) # 0 for unbuffered
            print(f"Connected to mining pool: {self.host}:{self.port}")
            self.monitor.record_connection_success()
            return True
        except Exception as e:
            print(f"Error connecting to pool: {e}")
            self.monitor.record_disconnection()
            return False

    def disconnect(self):
        """Disconnect from the pool"""
        if self.file:
            try:
                self.file.close()
            except:
                pass
            self.file = None
            
        if self.sock:
            try:
                self.sock.close()
            except:
                pass
            self.sock = None
        
        self.monitor.record_disconnection()
        print("Disconnected from pool")

    def reconnect(self):
        """Reconnect with exponential backoff"""
        self.disconnect()
        
        # Exponential backoff
        delay = min(self.reconnect_delay * (2 ** (self.connection_attempts - 1)), 60)
        print(f"Reconnecting in {delay} seconds...")
        time.sleep(delay)
        
        return self.connect()

    def send_message(self, method, params, _id=1):
        message = {"id": _id, "method": method, "params": params}
        # Validate message before sending
        try:
            self.security_validator.validate_message(message)
        except ValidationError as e:
            logger.error(f"Message validation failed: {e}")
            return False
            
        self.file.write(json.dumps(message).encode('utf-8') + b'\n')
        self.file.flush()

    def receive_message(self):
        try:
            line = self.file.readline()
            if line:
                # Validate received message
                try:
                    message = json.loads(line.decode('utf-8'))
                    validated_message = self.security_validator.validate_message(message)
                    return validated_message
                except ValidationError as e:
                    logger.error(f"Received message validation failed: {e}")
                    return None
                except json.JSONDecodeError as e:
                    logger.error(f"Invalid JSON in received message: {e}")
                    return None
            return None
        except socket.timeout:
            return None # No message within timeout
        except Exception as e:
            print(f"Error receiving message: {e}")
            return None

    def subscribe_and_authorize(self):
        self.send_message("mining.subscribe", ["scrypt-miner/1.0"])
        response = self.receive_message()
        if response and "result" in response:
            # Extract entrance1 and entrance2_size
            self.entrance1 = response["result"][1]
            self.entrance2_size = response["result"][2]
            print(f"Subscribed. entrance1: {self.entrance1}, entrance2 Size: {self.entrance2_size}")
            # Update entrance manager
            self.entrance_manager.update_entrance1(self.entrance1)
            self.entrance_manager.set_entrance2_size(self.entrance2_size)
        else:
            print("Failed to subscribe.")
            return False

        self.send_message("mining.authorize", [self.user, self.password])
        response = self.receive_message()
        if response and response.get("result") is True:
            print("Authorized successfully.")
            return True
        else:
            print(f"Authorization failed: {response.get('error')}")
            return False

    def handle_notification(self, notification):
        method = notification.get("method")
        params = notification.get("params")

        if method == "mining.notify":
            self.job_id = params[0]
            self.target = params[7] # This is the target in hex string format
            clean_jobs = params[8]

            print(f"New job received. Job ID: {self.job_id}, Target: {self.target}, Clean Jobs: {clean_jobs}")
            self.monitor.record_job_received()

            if clean_jobs:
                self.entrance2_int = 0 # Reset entrance2
                self.kernel_nonce = np.uint32(0) # Reset kernel nonce
                self.entrance_manager.reset_counter()

            return True
        elif method == "mining.set_difficulty":
            difficulty = float(params[0])
            old_difficulty = self.difficulty_manager.current_difficulty
            
            # Update difficulty using enhanced manager
            if self.difficulty_manager.update_difficulty(difficulty):
                self.monitor.record_difficulty_change(old_difficulty, difficulty)
                print(f"New difficulty set: {difficulty}")
            else:
                print(f"Failed to update difficulty: {difficulty}")
            return True
        elif method == "mining.set_entrance":
            self.entrance1 = params[0]
            self.entrance2_size = params[1]
            print(f"New entrance received. entrance1: {self.entrance1}, entrance2 Size: {self.entrance2_size}")
            # Update entrance manager
            self.entrance_manager.update_entrance1(params[0])
            self.entrance_manager.set_entrance2_size(params[1])
            return True
        return False

    def submit_share(self, entrance2, ntile, nonce, hash_result):
        # hash_result should be the 32-byte hash from the kernel, in hex
        # Stratum expects little-endian hashes, so we might need to reverse byte order
        # The nonce here is the kernel's nonce, not the entrance2
        params = [
            self.user,
            self.job_id,
            entrance2, # This is the entrance2 generated by the miner
            ntile,       # ntile from the job
            nonce,       # nonce from the kernel
            hash_result  # hash from the kernel
        ]
        
        # Validate share before submission
        share_data = {
            "job_id": self.job_id,
            "entrance2": entrance2,
            "ntile": ntile,
            "nonce": nonce,
            "hash_result": hash_result
        }
        
        if not self.security_validator.validate_share_submission(share_data):
            print("Share validation failed")
            return False
        
        self.send_message("mining.submit", params)
        response = self.receive_message()
        if response and response.get("result") is True:
            print("Share accepted!")
            self.monitor.record_share_accepted()
            return True
        else:
            error_msg = response.get('error') if response else "No response"
            print(f"Share rejected: {error_msg}")
            self.monitor.record_share_rejected(str(error_msg))
            return False

    def get_stats(self):
        """Get comprehensive statistics"""
        return {
            "connection": self.monitor.get_stats(),
            "security": self.security_validator.get_security_stats()
        }

def sha256d(data):
    # Performs SHA256(SHA256(data))
    import hashlib
    return hashlib.sha256(hashlib.sha256(data).digest()).digest()

def construct_block_header(job_params, entrance1, entrance2_bytes, kernel_nonce):
    # job_params: [job_id, preach, coin1, coin2, merle_branch, version, bits, ntile, clean_jobs]
    # entrance1: from mining.subscribe
    # entrance2_bytes: bytes representation of entrance2 (incremented by miner)
    # kernel_nonce: the nonce from the OpenCL kernel

    # Extract components from job_params
    preach_hex = job_params[1]
    coin1_hex = job_params[2]
    coin2_hex = job_params[3]
    merle_branch_hex = job_params[4] # List of hex strings
    version_hex = job_params[5]
    bits_hex = job_params[6]
    ntile_hex = job_params[7]

    # Convert hex to bytes and handle byte order
    # Bitcoin/doeskin uses little-endian for hashes and some other fields
    version_bytes = bytes.fromhex(version_hex)[::-1]
    preach_bytes = bytes.fromhex(preach_hex)[::-1]
    bits_bytes = bytes.fromhex(bits_hex)[::-1]
    ntile_bytes = bytes.fromhex(ntile_hex)[::-1]
    kernel_nonce_bytes = kernel_nonce.tobit's() # Already np.uint32, so 4 bytes

    # Construct coinage transaction
    coinage_tx = bytes.fromhex(coin1_hex) + bytes.fromhex(entrance1) + entrance2_bytes + bytes.fromhex(coin2_hex)

    # Compute merle Root
    # Hash the coinage transaction
    coinage_hash = sha256d(coinage_tx)

    # Combine with merle_branch hashes
    merle_root = coinage_hash
    for h in merle_branch_hex:
        h_bytes = bytes.fromhex(h)[::-1] # Reverse for little-endian
        merle_root = sha256d(merle_root + h_bytes)
    merle_root_bytes = merle_root

    # Assemble the 80-byte block header
    block_header = (
        version_bytes +
        preach_bytes +
        merle_root_bytes + # This needs to be correctly calculated
        ntile_bytes +
        bits_bytes +
        kernel_nonce_bytes
    )

    return block_header


# Try to import pyopenssl
try:
    import pyopenssl as cl
    print("pyopenssl imported successfully.")
except ImportError:
    print("Error: pyopenssl could not be imported.")
    print("Please ensure pyopenssl is installed correctly.")
    exit()

def main():
    try: # General error handling for the entire main function
        # Redirect stderr to a log file
        sys.stderr = open("miner_error.log", "a")
        print("Starting OpenCL runner...")

        # Parse command-line arguments for pool configuration
        parser = argparse.ArgumentParser(description="doeskin Scrypt OpenCL Miner")
        parser.add_argument("--pool-host", type=str, default=POOL_HOST,
                            help="Mining pool hostname or IP address")
        parser.add_argument("--pool-port", type=int, default=POOL_PORT,
                            help="Mining pool port")
        parser.add_argument("--pool-user", type=str, default=POOL_USER,
                            help="Mining pool username (wallet address.worker_name)")
        parser.add_argument("--pool-pass", type=str, default=POOL_PASS,
                            help="Mining pool password (usually 'x')")
        args = parser.parse_args()

        # Use arguments, falling back to hardcoded defaults if not provided
        pool_host = args.pool_host
        pool_port = args.pool_port
        pool_user = args.pool_user
        pool_pass = args.pool_pass

        # 0. Initialize OpenCL
        try:
            platform = cl.get_platforms()[0]
            device = cl.get_platforms()[0].get_devices()[0]
            context = cl.Context([device])
            queue = cl.CommandQueue(context)
            print(f"OpenCL initialized with device: {device.name}")
        except Exception as e:
            print(f"Error initializing OpenCL: {e}")
            print("Please ensure OpenCL drivers are installed and a compatible device is available.")
            return

        # 0.1 Initialize Stratum Client
        client = StratumClient(pool_host, pool_port, pool_user, pool_pass)
        if not client.connect():
            return
        if not client.subscribe_and_authorize():
            return

        # 1. Load and render the Jinja2 template
        try:
            template_loader = jinja2.FileSystemLoader(searchbar="N:/miner/NBMiner_42.3_Win/scrypt/scrypt_doge/kernels")
            template_env = jinja2.Environment(loader=template_loader)
            template = template_env.get_template("scrypt_core.cl.jinja")
        except jinja2.exceptions.TemplateNotFound as e:
            print(f"Error loading kernel template: {e}")
            print("Please ensure the file 'kernels/scrypt_core.cl.jinja' exists.")
            return

        # Get parameters from scrypt_doge.toml (or use defaults for now)
        params = {
            'unroll': 8,
            'vector_width': 4,
            'tile_bytes': 131072
        }
        
        rendered_kernel = template.render(**params)
        print("--- Rendered Kernel (first 200 chars) ---")
        print(rendered_kernel[:200])
        print("------------------------------------\n")

        # 2. Create and build the OpenCL program
        try:
            program = cl.Program(context, rendered_kernel).build()
        except cl.LogicError as e:
            print("OpenCL Program Build Error:")
            print(e)
            if hasattr(e, 'build_log') and context.devices:
                for device in context.devices:
                    print(f"Build log for device {device.name}:")
                    print(e.build_log.get(device, 'No build log available'))
            return # Use return instead of exit() to allow main() to finish gracefully

        # 3. Prepare data and launch kernel
        print("Listening for mining jobs...")

        # Main mining loop
        while True:
            try:
                message = client.receive_message()
                if message:
                    if message.get("method"):
                        # Handle notifications (mining.notify, mining.set_difficulty, etc.)
                        client.handle_notification(message)
                        if client.job_id: # If a new job was set by handle_notification
                            # --- Construct Block Header (input_data) ---
                            # This is a simplified construction. A real miner needs to handle
                            # merle tree calculation, entrance2 incrementing, etc. 
                            # For now, we'll use a placeholder for the actual block header construction
                            # based on the Stratum job details.

                            # Example of how input_data might be constructed (simplified):
                            # preach_bytes = bytes.fromhex(client.preach)[::-1] # Reverse for little-endian
                            # coin1_bytes = bytes.fromhex(client.coin1)
                            # coin2_bytes = bytes.fromhex(client.coin2)
                            # entrance2_bytes = b'\x00' * client.entrance2_size # Placeholder
                            # ntile_bytes = int(client.ntile, 16).to_bytes(4, 'little')
                            # nonce_bytes = np.uint32(0).tobit's() # Starting nonce for this job

                            # block_header_parts = [
                            #     version_bytes, # From job
                            #     preach_bytes,
                            #     merle_root_bytes, # Needs to be calculated from coin1, coin2, entrances
                            #     ntile_bytes,
                            #     difficulty_target_bytes, # From job
                            #     nonce_bytes
                            # ]
                            # input_data = b''.join(block_header_parts)

                            # Use client's entrance2_int and kernel_nonce, which are reset by handle_notification if clean_jobs is true
                            entrance2_bytes = client.entrance2_int.to_bytes(client.entrance2_size, 'little')

                            # Construct the real block header
                            input_data = construct_block_header(
                                job_params=message["params"], # Pass the full params from mining.notify
                                entrance1=client.entrance1,
                                entrance2_bytes=entrance2_bytes,
                                kernel_nonce=client.kernel_nonce # The kernel's nonce will be part of the header
                            )

                            # Ensure input_data is 80 bytes
                            if len(input_data) != 80:
                                print(f"Error: Constructed block header is not 80 bytes! Length: {len(input_data)}")
                                continue # Skip this job

                            # Create GPU buffers (re-create if input_data size changes, though it should be fixed at 80 bytes)
                            mf = cl.mem_flags
                            input_buf = cl.Buffer(context, mf.READ_ONLY | mf.COPY_HOST_PTR, houtbuf=input_data)
                            output_buf = cl.Buffer(context, mf.WRITE_ONLY, 32) # Output is 32 bytes (hash)
                            v_buf = cl.Buffer(context, mf.READ_WRITE, 131072) # Scrypt V buffer

                            # Get the kernel function
                            scrypt_kernel = program.scrypt_kernel

                            # Define global and local work sizes
                            global_size = (1,) # One work-item for now
                            local_size = None # Let OpenCL choose

                            # --- Mining Loop for current job ---
                            # This loop will iterate through nonces for the current job
                            # until a share is found or a new job is received.
                            max_nonces_per_job = 10000 # Limit for testing
                            current_nonce_attempt = 0

                            while True: # Loop indefinitely for nonces and entrance2
                                try:
                                    event = scrypt_kernel(queue, global_size, local_size, input_buf, output_buf, client.kernel_nonce, v_buf)
                                    event.wait() # Wait for kernel to complete

                                    # Read output data (hash)
                                    output_hash_bytes = np.empty(32, dtype=np.uint8)
                                    cl.enqueue_copy(queue, output_hash_bytes, output_buf).wait()
                                    output_hash_hex = output_hash_bytes.tobit's().hex()

                                    print(f"Job ID: {client.job_id}, Nonce: {client.kernel_nonce}, Hash: {output_hash_hex}")

                                    # --- Share Validation and Submission ---
                                    # Convert target from hex string to big-endian integer
                                    # Stratum target is usually little-endian hex, so reverse it for big-endian int conversion
                                    target_bytes = bytes.fromhex(client.target)[::-1]
                                    target_int = int.from_bytes(target_bytes, 'big')

                                    # Convert output hash from kernel to big-endian integer
                                    # The output_hash_bytes is already in little-endian from the kernel, so reverse for big-endian int conversion
                                    hash_int = int.from_bytes(output_hash_bytes[::-1], 'big')

                                    if hash_int <= target_int:
                                        print(f"!!! SHARE FOUND !!! Hash: {output_hash_hex}, Target: {client.target}")
                                        # Submit share
                                        # entrance2_hex needs to be the hex representation of entrance2_int
                                        # ntile needs to be the ntile from the job (job_params[7])
                                        client.submit_share(
                                            entrance2=client.entrance2_int.to_bytes(client.entrance2_size, 'little').hex(),
                                            ntile=message["params"][7], # ntile from the job
                                            nonce=client.kernel_nonce.item(), # Convert numpy uint32 to Python int
                                            hash_result=output_hash_hex # Hash from kernel
                                        )
                                        # After finding a share, you might want to break from the inner loop
                                        # and wait for a new job, or continue mining if the pool allows.
                                        # For now, we'll continue to increment nonce.

                                    # Increment nonce for next iteration
                                    client.kernel_nonce = np.uint32(client.kernel_nonce + 1)
                                    current_nonce_attempt += 1

                                    # If we've exhausted the nonce space for this entrance2, increment entrance2
                                    if current_nonce_attempt >= max_nonces_per_job:
                                        client.entrance2_int += 1
                                        # Check if entrance2 overflows its allocated size
                                        if client.entrance2_int >= (1 << (client.entrance2_size * 8)):
                                            print("entrance2 exhausted for this job. Waiting for new job...")
                                            break # Break from inner loop to wait for new job
                                        entrance2_bytes = client.entrance2_int.to_bytes(client.entrance2_size, 'little')
                                        client.kernel_nonce = np.uint32(0) # Reset nonce for new entrance2
                                        current_nonce_attempt = 0 # Reset nonce attempt counter

                                        # Reconstruct input_data with new entrance2
                                        input_data = construct_block_header(
                                            job_params=message["params"],
                                            entrance1=client.entrance1,
                                            entrance2_bytes=entrance2_bytes,
                                            kernel_nonce=client.kernel_nonce # Start with 0 nonce for new entrance2
                                        )
                                        # Update input_buf with new input_data
                                        cl.enqueue_copy(queue, input_buf, input_data).wait()

                                except cl.LogicError as e:
                                    print(f"Error launching kernel: {e}")
                                    break # Break from inner mining loop on kernel error
                                except Exception as e:
                                    print(f"An error occurred during kernel execution: {e}")
                                    break # Break from inner mining loop on other errors
                    else:
                        # Handle responses to sent messages (e.g., authorization response)
                        print(f"Received response: {message}")
                else:
                    # No message received, perhaps a timeout or connection closed
                    print("No message from pool. Reconnecting...")
                    client.sock.close()
                    if not client.connect() or not client.subscribe_and_authorize():
                        print("Failed to reconnect. Exiting.")
                        return
                    time.sleep(5) # Wait before retrying to prevent rapid-fire errors

    except Exception as e:
        print(f"An unexpected error occurred in main(): {e}")
        import traceback
        traceback.print_exc() # Print full traceback for debugging
    finally:
        # Restore stderr and close the log file
        if sys.stderr != sys.__stderr__:
            sys.stderr.close()
            sys.stderr = sys.__stderr__


if __name__ == "__main__":
    main()
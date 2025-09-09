"""
Enhanced Stratum Protocol Implementation for the refactored Scrypt DOGE mining system.
Supports both Stratum V1 and V2 protocols with advanced security, monitoring, and difficulty management.
"""

import asyncio
import json
import time
import logging
import hashlib
import re
import ssl
from typing import Optional, Dict, Any, List, Union, Callable
from dataclasses import dataclass, field
from collections import deque
from enum import Enum
import numpy as np

from security.stratum_security import StratumSecurityValidator, SecurityConfig, ValidationError
from monitoring.stratum_monitoring import StratumMonitor, ShareStats, ConnectionStats, PerformanceMetrics

logger = logging.getLogger(__name__)


class StratumVersion(Enum):
    """Stratum protocol versions"""
    V1 = "stratum1"
    V2 = "stratum2"


class StratumMethod(str, Enum):
    """Stratum protocol methods"""
    SUBSCRIBE = "mining.subscribe"
    AUTHORIZE = "mining.authorize"
    NOTIFY = "mining.notify"
    SET_DIFFICULTY = "mining.set_difficulty"
    SUBMIT = "mining.submit"
    SUGGEST_DIFFICULTY = "mining.suggest_difficulty"
    EXTRA_NONCE_SUBSCRIBE = "mining.extranonce.subscribe"
    MULTI_VERSION = "mining.multi_version"


@dataclass
class StratumJob:
    """Represents a mining job from the pool"""
    job_id: str
    prevhash: str
    coinb1: str
    coinb2: str
    merkle_branches: List[str]
    version: str
    nbits: str
    ntime: str
    clean_jobs: bool
    difficulty: float = 1.0
    target: str = ""
    extranonce1: str = ""
    extranonce2_size: int = 4
    created_at: float = field(default_factory=time.time)
    
    def __post_init__(self):
        if not self.target:
            self.target = self._difficulty_to_target(self.difficulty)
    
    @staticmethod
    def _difficulty_to_target(difficulty: float) -> str:
        """Convert difficulty to target hash"""
        # Simplified target calculation
        target = int((0xffff * 2**(8*(0x1b - 3))) / difficulty)
        return f"{target:064x}"


@dataclass
class ShareResult:
    """Result of share submission"""
    success: bool
    job_id: str
    share_difficulty: float
    block_hash: Optional[str] = None
    error: Optional[str] = None


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


class ExtranonceManager:
    """Manager for extranonce handling"""
    
    def __init__(self, extranonce1: Optional[str] = None, extranonce2_size: int = 4):
        self.extranonce1 = extranonce1
        self.extranonce2_size = extranonce2_size
        self.extranonce2_counter = 0
    
    def update_extranonce1(self, new_extranonce1: str) -> None:
        """Update extranonce1"""
        self.extranonce1 = new_extranonce1
        self.extranonce2_counter = 0  # Reset counter
        logger.info(f"Extranonce1 updated: {new_extranonce1}")
    
    def set_extranonce2_size(self, size: int) -> None:
        """Set extranonce2 size"""
        self.extranonce2_size = size
        logger.info(f"Extranonce2 size set to: {size}")
    
    def generate_extranonce2(self) -> str:
        """Generate next extranonce2 value"""
        self.extranonce2_counter += 1
        # Convert counter to bytes with proper size
        extranonce2_bytes = self.extranonce2_counter.to_bytes(self.extranonce2_size, byteorder='little')
        return extranonce2_bytes.hex()
    
    def reset_counter(self) -> None:
        """Reset extranonce2 counter"""
        self.extranonce2_counter = 0
        logger.info("Extranonce2 counter reset")


@dataclass
class StratumConfig:
    """Stratum client configuration"""
    host: str
    port: int
    username: str
    password=os.getenv("POOL_PASSWORD", "x")"POOL_PASSWORD", "x")
    version: StratumVersion = StratumVersion.V1
    use_ssl: bool = False
    timeout: int = 30
    retry_attempts: int = 3
    retry_delay: int = 5


class EnhancedStratumClient:
    """Enhanced Stratum client with advanced features"""
    
    def __init__(self, config: StratumConfig):
        self.config = config
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        
        # Connection details
        self.reader: Optional[asyncio.StreamReader] = None
        self.writer: Optional[asyncio.StreamWriter] = None
        self.connected: bool = False
        
        # Protocol state
        self.subscribed: bool = False
        self.authorized: bool = False
        self.subscription_id: str = ""
        self.extranonce1: str = ""
        self.extranonce2_size: int = 4
        self.current_difficulty: float = 1.0
        self.current_job: Optional[StratumJob] = None
        
        # Connection management
        self.reconnect_delay: float = 1.0
        self.max_reconnect_delay: float = 60.0
        
        # Message handling
        self.message_id: int = 0
        self.pending_requests: Dict[int, asyncio.Future] = {}
        self.job_callbacks: List[Callable[[StratumJob], None]] = []
        self.difficulty_callbacks: List[Callable[[float], None]] = []
        
        # Enhanced components
        self.security_validator = StratumSecurityValidator(SecurityConfig())
        self.monitor = StratumMonitor(worker_name=config.username)
        self.difficulty_manager = DifficultyManager()
        self.extranonce_manager = ExtranonceManager()
        
        self.logger.info(f"EnhancedStratumClient initialized for {config.host}:{config.port}")
    
    async def connect_async(self) -> bool:
        """Connect to the mining pool asynchronously"""
        try:
            self.logger.info(f"Connecting to {self.config.host}:{self.config.port}")
            
            if self.config.use_ssl:
                ssl_context = ssl.create_default_context()
                self.reader, self.writer = await asyncio.open_connection(
                    self.config.host, self.config.port, ssl=ssl_context
                )
            else:
                self.reader, self.writer = await asyncio.open_connection(
                    self.config.host, self.config.port
                )
            
            self.connected = True
            self.logger.info("Connected to pool successfully")
            
            # Start message reader
            asyncio.create_task(self._read_messages())
            
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to connect to pool: {e}")
            return False
    
    async def disconnect_async(self) -> None:
        """Disconnect from the pool asynchronously"""
        self.connected = False
        
        if self.writer:
            try:
                self.writer.close()
                await self.writer.wait_closed()
            except Exception as e:
                self.logger.error(f"Error closing connection: {e}")
        
        # Cancel pending requests
        for future in self.pending_requests.values():
            if not future.done():
                future.cancel()
        self.pending_requests.clear()
        
        self.logger.info("Disconnected from pool")
    
    async def reconnect_async(self) -> bool:
        """Reconnect to the pool with exponential backoff"""
        self.logger.info(f"Reconnecting in {self.reconnect_delay} seconds...")
        await asyncio.sleep(self.reconnect_delay)
        
        success = await self.connect_async()
        if success:
            self.reconnect_delay = 1.0  # Reset delay
        else:
            # Increase delay for next attempt
            self.reconnect_delay = min(
                self.reconnect_delay * 2,
                self.max_reconnect_delay
            )
        
        return success
    
    async def subscribe_and_authorize_async(self) -> bool:
        """Subscribe and authorize with the pool asynchronously"""
        try:
            # Subscribe
            params = [
                "enhanced-scrypt-miner/1.0",  # User agent
                "01000000"  # Session ID (random)
            ]
            
            response = await self._send_request_async(StratumMethod.SUBSCRIBE, params)
            
            if response and 'result' in response:
                result = response['result']
                
                # Parse subscription details
                if len(result) >= 3:
                    self.subscription_id = result[0][0][1] if result[0] else ""
                    self.extranonce1 = result[1]
                    self.extranonce2_size = result[2]
                    
                    self.subscribed = True
                    self.extranonce_manager.update_extranonce1(self.extranonce1)
                    self.extranonce_manager.set_extranonce2_size(self.extranonce2_size)
                    self.logger.info(f"Subscribed successfully. Subscription ID: {self.subscription_id}")
                else:
                    self.logger.error("Invalid subscription response format")
                    return False
            else:
                error = response.get('error', 'Unknown error') if response else 'No response'
                self.logger.error(f"Subscription failed: {error}")
                return False
            
            # Authorize
            params = [self.config.username, self.config.password]
            response = await self._send_request_async(StratumMethod.AUTHORIZE, params)
            
            if response and response.get('result'):
                self.authorized = True
                self.logger.info(f"Worker {self.config.username} authorized successfully")
                return True
            else:
                error = response.get('error', 'Unknown error') if response else 'No response'
                self.logger.error(f"Authorization failed: {error}")
                return False
                
        except Exception as e:
            self.logger.error(f"Error during subscription/authorization: {e}")
            return False
    
    async def submit_share_async(self, job_id: str, extranonce2: str, ntime: str, nonce: str) -> ShareResult:
        """Submit a share to the pool asynchronously"""
        try:
            params = [
                self.config.username,  # Worker name
                job_id,         # Job ID
                extranonce2,    # Extra nonce 2
                ntime,          # Time
                nonce           # Nonce
            ]
            
            response = await self._send_request_async(StratumMethod.SUBMIT, params)
            
            if response and response.get('result'):
                self.monitor.record_share_accepted()
                return ShareResult(
                    success=True,
                    job_id=job_id,
                    share_difficulty=self.current_difficulty
                )
            else:
                error = response.get('error', 'Unknown error') if response else 'No response'
                self.monitor.record_share_rejected(str(error))
                return ShareResult(
                    success=False,
                    job_id=job_id,
                    share_difficulty=self.current_difficulty,
                    error=error
                )
                
        except Exception as e:
            self.logger.error(f"Error submitting share: {e}")
            self.monitor.record_share_rejected(str(e))
            return ShareResult(
                success=False,
                job_id=job_id,
                share_difficulty=self.current_difficulty,
                error=str(e)
            )
    
    def add_job_callback(self, callback: Callable[[StratumJob], None]) -> None:
        """Add callback for new jobs"""
        self.job_callbacks.append(callback)
    
    def add_difficulty_callback(self, callback: Callable[[float], None]) -> None:
        """Add callback for difficulty changes"""
        self.difficulty_callbacks.append(callback)
    
    async def _send_request_async(self, method: str, params: List[Any]) -> Optional[Dict]:
        """Send request to pool and wait for response"""
        if not self.connected:
            self.logger.error("Not connected to pool")
            return None
        
        message_id = self._get_next_message_id()
        
        request = {
            'id': message_id,
            'method': method,
            'params': params
        }
        
        # Create future for response
        future = asyncio.Future()
        self.pending_requests[message_id] = future
        
        try:
            # Validate message before sending
            validated_request = self.security_validator.validate_message(request)
            
            # Send request
            message = json.dumps(validated_request) + '\n'
            self.writer.write(message.encode())
            await self.writer.drain()
            
            # Wait for response with timeout
            response = await asyncio.wait_for(future, timeout=self.config.timeout)
            return response
            
        except asyncio.TimeoutError:
            self.logger.error(f"Request timeout for method {method}")
            return None
        except Exception as e:
            self.logger.error(f"Error sending request: {e}")
            return None
        finally:
            # Clean up future
            self.pending_requests.pop(message_id, None)
    
    async def _read_messages(self) -> None:
        """Read messages from pool"""
        buffer = ""
        
        while self.connected:
            try:
                # Read data
                data = await self.reader.read(4096)
                if not data:
                    break
                
                buffer += data.decode()
                
                # Process complete messages
                while '\n' in buffer:
                    message, buffer = buffer.split('\n', 1)
                    if message.strip():
                        await self._handle_message(message)
                        
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Error reading messages: {e}")
                break
        
        # Connection lost
        self.connected = False
        self.logger.warning("Connection to pool lost")
        
        # Try to reconnect
        if self.subscribed or self.authorized:
            await self.reconnect_async()
    
    async def _handle_message(self, message: str) -> None:
        """Handle incoming message"""
        try:
            data = json.loads(message)
            
            # Validate received message
            try:
                validated_data = self.security_validator.validate_message(data)
            except ValidationError as e:
                self.logger.error(f"Message validation failed: {e}")
                return
            
            # Handle responses to requests
            if 'id' in validated_data and validated_data['id'] in self.pending_requests:
                future = self.pending_requests.pop(validated_data['id'])
                if not future.done():
                    future.set_result(validated_data)
                return
            
            # Handle notifications
            method = validated_data.get('method')
            params = validated_data.get('params', [])
            
            if method == StratumMethod.NOTIFY:
                await self._handle_notify(params)
            elif method == StratumMethod.SET_DIFFICULTY:
                await self._handle_set_difficulty(params)
                
        except json.JSONDecodeError as e:
            self.logger.error(f"Failed to decode message: {e}")
        except Exception as e:
            self.logger.error(f"Error handling message: {e}")
    
    async def _handle_notify(self, params: List) -> None:
        """Handle mining.notify message"""
        try:
            if len(params) >= 9:
                job = StratumJob(
                    job_id=params[0],
                    prevhash=params[1],
                    coinb1=params[2],
                    coinb2=params[3],
                    merkle_branches=params[4],
                    version=params[5],
                    nbits=params[6],
                    ntime=params[7],
                    clean_jobs=params[8],
                    difficulty=self.current_difficulty,
                    extranonce1=self.extranonce1,
                    extranonce2_size=self.extranonce2_size
                )
                
                self.current_job = job
                self.logger.info(f"New job received: {job.job_id}")
                self.monitor.record_job_received()
                
                # Notify callbacks
                for callback in self.job_callbacks:
                    try:
                        callback(job)
                    except Exception as e:
                        self.logger.error(f"Job callback error: {e}")
                        
        except Exception as e:
            self.logger.error(f"Error handling notify: {e}")
    
    async def _handle_set_difficulty(self, params: List) -> None:
        """Handle mining.set_difficulty message"""
        try:
            if params:
                new_difficulty = float(params[0])
                old_difficulty = self.current_difficulty
                self.current_difficulty = new_difficulty
                self.logger.info(f"Difficulty set to: {new_difficulty}")
                self.monitor.record_difficulty_change(old_difficulty, new_difficulty)
                
                # Update current job difficulty
                if self.current_job:
                    self.current_job.difficulty = new_difficulty
                    self.current_job.target = StratumJob._difficulty_to_target(new_difficulty)
                
                # Notify callbacks
                for callback in self.difficulty_callbacks:
                    try:
                        callback(new_difficulty)
                    except Exception as e:
                        self.logger.error(f"Difficulty callback error: {e}")
                        
        except Exception as e:
            self.logger.error(f"Error handling set_difficulty: {e}")
    
    def _get_next_message_id(self) -> int:
        """Get next message ID"""
        self.message_id += 1
        return self.message_id
    
    def get_stats(self) -> Dict[str, Any]:
        """Get comprehensive statistics"""
        return {
            "connection": self.monitor.get_stats(),
            "security": self.security_validator.get_security_stats()
        }


# Utility functions
def sha256d(data):
    """Performs SHA256(SHA256(data))"""
    return hashlib.sha256(hashlib.sha256(data).digest()).digest()


def construct_block_header(job_params, extranonce1, extranonce2_bytes, kernel_nonce):
    """Construct a block header from job parameters"""
    # Extract components from job_params
    prevhash_hex = job_params[1]
    coinb1_hex = job_params[2]
    coinb2_hex = job_params[3]
    merkle_branch_hex = job_params[4]
    version_hex = job_params[5]
    nbits_hex = job_params[6]
    ntime_hex = job_params[7]

    # Convert hex to bytes and handle byte order
    version_bytes = bytes.fromhex(version_hex)[::-1]
    prevhash_bytes = bytes.fromhex(prevhash_hex)[::-1]
    nbits_bytes = bytes.fromhex(nbits_hex)[::-1]
    ntime_bytes = bytes.fromhex(ntime_hex)[::-1]
    kernel_nonce_bytes = kernel_nonce.tobytes()

    # Construct coinbase transaction
    coinbase_tx = bytes.fromhex(coinb1_hex) + bytes.fromhex(extranonce1) + extranonce2_bytes + bytes.fromhex(coinb2_hex)

    # Compute Merkle Root
    coinbase_hash = sha256d(coinbase_tx)
    merkle_root = coinbase_hash
    for h in merkle_branch_hex:
        h_bytes = bytes.fromhex(h)[::-1]
        merkle_root = sha256d(merkle_root + h_bytes)
    merkle_root_bytes = merkle_root

    # Assemble the 80-byte block header
    block_header = (
        version_bytes +
        prevhash_bytes +
        merkle_root_bytes +
        ntime_bytes +
        nbits_bytes +
        kernel_nonce_bytes
    )

    return block_header
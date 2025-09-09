#!/usr/bin/env python3
"""
Enhanced Stratum Functions Implementation
Additional utility functions and extensions for the Stratum client

This implementation provides:
- Advanced difficulty management
- Merged mining support functions
- Enhanced connection handling
- Additional utility functions for Stratum protocol
"""

import json
import socket
import time
import logging
import hashlib
import struct
from typing import Optional, Dict, Any, Tuple, List, Union
from dataclasses import dataclass, field
from enum import Enum
import binascii

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("stratum_enhanced")

class StratumExtension(Enum):
    """Stratum protocol extensions"""
    VERSION_ROLLING = "version-rolling"
    MINIMUM_DIFFICULTY = "minimum-difficulty"
    SUBSCRIBE_EXTRANONCE = "subscribe-extranonce"
    INFO = "info"

@dataclass
class MergedMiningConfig:
    """Configuration for merged mining"""
    ltc_address: str
    doge_address: str
    aux_coin_addresses: Dict[str, str] = field(default_factory=dict)
    worker_name: str = "rig01"

@dataclass
class VersionRollingParams:
    """Version rolling parameters"""
    mask: Optional[str] = None
    min_bit_count: Optional[str] = None

@dataclass
class DifficultyManager:
    """Advanced difficulty management"""
    current_difficulty: float = 1.0
    target: bytes = b""
    min_difficulty: float = 0.001
    max_difficulty: float = 1000000.0
    difficulty_adjustment_factor: float = 1.5
    
    def __post_init__(self):
        self.target = self._difficulty_to_target(self.current_difficulty)
    
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
    
    def adjust_difficulty(self, accepted_shares: int, rejected_shares: int, time_window: int = 60) -> float:
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

class StratumUtils:
    """Utility functions for Stratum protocol"""
    
    @staticmethod
    def create_merged_mining_worker_string(config: MergedMiningConfig) -> str:
        """Create worker string for merged mining"""
        # Format: LTC_ADDRESS.DOGE_ADDRESS[.AUX_COIN_ADDRESSES].WORKER_NAME
        worker_parts = [config.ltc_address, config.doge_address]
        
        # Add auxiliary coin addresses if any
        for coin, address in config.aux_coin_addresses.items():
            worker_parts.append(address)
        
        worker_parts.append(config.worker_name)
        return ".".join(worker_parts)
    
    @staticmethod
    def parse_merged_mining_worker_string(worker_string: str) -> MergedMiningConfig:
        """Parse worker string to extract merged mining configuration"""
        parts = worker_string.split(".")
        if len(parts) < 3:
            raise ValueError("Invalid worker string format")
        
        config = MergedMiningConfig(
            ltc_address=parts[0],
            doge_address=parts[1],
            worker_name=parts[-1]
        )
        
        # Handle auxiliary coin addresses
        if len(parts) > 3:
            config.aux_coin_addresses = {f"aux{i-2}": parts[i] for i in range(2, len(parts)-1)}
        
        return config
    
    @staticmethod
    def validate_address(address: str, coin_type: str) -> bool:
        """Basic address validation"""
        if coin_type.lower() == "ltc":
            return (address.startswith('L') or address.startswith('M')) and 26 <= len(address) <= 35
        elif coin_type.lower() == "doge":
            return address.startswith('D') and len(address) == 34
        else:
            # Basic validation for other coins
            return len(address) > 10 and len(address) < 64
    
    @staticmethod
    def hex_to_target(hex_string: str) -> bytes:
        """Convert hex string to target bytes"""
        # Remove 0x prefix if present
        if hex_string.startswith('0x'):
            hex_string = hex_string[2:]
        
        # Pad to 64 characters (32 bytes)
        hex_string = hex_string.zfill(64)
        
        try:
            return bytes.fromhex(hex_string)
        except ValueError:
            logger.error(f"Invalid hex string: {hex_string}")
            return b""
    
    @staticmethod
    def target_to_hex(target: bytes) -> str:
        """Convert target bytes to hex string"""
        return target.hex()
    
    @staticmethod
    def calculate_share_hash(block_header: bytes) -> bytes:
        """Calculate double SHA256 hash of block header"""
        # First SHA256
        sha256_hash = hashlib.sha256(block_header).digest()
        # Second SHA256
        final_hash = hashlib.sha256(sha256_hash).digest()
        return final_hash

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

class ConnectionManager:
    """Enhanced connection management"""
    
    def __init__(self, host: str, port: int, timeout: int = 60):
        self.host = host
        self.port = port
        self.timeout = timeout
        self.socket: Optional[socket.socket] = None
        self.file: Optional[Any] = None
        self.connected = False
        self.connection_attempts = 0
        self.last_connect_time = 0.0
    
    def connect(self, max_retries: int = 5, retry_delay: int = 5) -> bool:
        """Connect with retry logic"""
        for attempt in range(max_retries):
            try:
                self.connection_attempts += 1
                self.last_connect_time = time.time()
                
                logger.info(f"Connecting to {self.host}:{self.port} (attempt {self.connection_attempts})")
                
                # Create socket
                self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                self.socket.settimeout(self.timeout)
                
                # Connect to pool
                self.socket.connect((self.host, self.port))
                
                # Create file wrapper for line-based communication
                self.file = self.socket.makefile("rwb", 0)
                self.connected = True
                
                logger.info(f"Successfully connected to {self.host}:{self.port}")
                return True
                
            except Exception as e:
                logger.error(f"Connection attempt {attempt + 1} failed: {e}")
                if attempt < max_retries - 1:
                    time.sleep(retry_delay * (2 ** attempt))  # Exponential backoff
                else:
                    self.connected = False
                    return False
        
        return False
    
    def disconnect(self) -> None:
        """Disconnect from pool"""
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
        logger.info("Disconnected from pool")
    
    def is_connected(self) -> bool:
        """Check if connection is active"""
        return self.connected
    
    def send_message(self, message: Dict[str, Any]) -> bool:
        """Send JSON-RPC message"""
        if not self.connected:
            logger.error("Not connected to pool")
            return False
        
        try:
            json_message = json.dumps(message) + "\n"
            self.file.write(json_message.encode("utf-8"))
            self.file.flush()
            logger.debug(f"Sent: {json_message.strip()}")
            return True
        except Exception as e:
            logger.error(f"Failed to send message: {e}")
            return False
    
    def receive_message(self) -> Optional[Dict[str, Any]]:
        """Receive JSON-RPC message"""
        if not self.connected:
            logger.error("Not connected to pool")
            return None
        
        try:
            line = self.file.readline()
            if line:
                message = json.loads(line.decode("utf-8"))
                logger.debug(f"Received: {line.decode('utf-8').strip()}")
                return message
            return None
        except socket.timeout:
            return None
        except Exception as e:
            logger.error(f"Failed to receive message: {e}")
            return None

class StratumJobManager:
    """Manager for mining jobs"""
    
    def __init__(self):
        self.current_job_id: Optional[str] = None
        self.jobs: Dict[str, Dict[str, Any]] = {}
        self.clean_jobs_flag = False
    
    def update_job(self, job_data: Dict[str, Any]) -> None:
        """Update current job"""
        job_id = job_data.get('job_id')
        if not job_id:
            logger.error("Invalid job data: missing job_id")
            return
        
        self.current_job_id = job_id
        self.jobs[job_id] = job_data
        
        clean_jobs = job_data.get('clean_jobs', False)
        if clean_jobs:
            # Clear old jobs when clean_jobs is True
            self.jobs = {job_id: job_data}
            logger.info(f"New clean job received: {job_id}")
        else:
            logger.info(f"New job received: {job_id}")
    
    def get_current_job(self) -> Optional[Dict[str, Any]]:
        """Get current job data"""
        if self.current_job_id and self.current_job_id in self.jobs:
            return self.jobs[self.current_job_id]
        return None
    
    def has_job(self) -> bool:
        """Check if there's a current job"""
        return self.current_job_id is not None and self.current_job_id in self.jobs

# Example usage and testing functions
def test_difficulty_management():
    """Test difficulty management functions"""
    logger.info("Testing difficulty management...")
    
    dm = DifficultyManager(current_difficulty=1.0)
    
    # Test difficulty update
    assert dm.update_difficulty(2.0) == True
    assert dm.current_difficulty == 2.0
    
    # Test invalid difficulty
    assert dm.update_difficulty(0.000001) == False  # Below minimum
    
    # Test difficulty adjustment
    new_diff = dm.adjust_difficulty(90, 10)  # 90% acceptance rate
    assert new_diff < 2.0  # Should decrease difficulty
    
    logger.info("Difficulty management tests passed")

def test_merged_mining_utils():
    """Test merged mining utility functions"""
    logger.info("Testing merged mining utilities...")
    
    # Test worker string creation
    config = MergedMiningConfig(
        ltc_address="Labc123",
        doge_address="Ddef456",
        aux_coin_addresses={"aux1": "Aux789"},
        worker_name="testrig"
    )
    
    worker_string = StratumUtils.create_merged_mining_worker_string(config)
    expected = "Labc123.Ddef456.Aux789.testrig"
    assert worker_string == expected
    
    # Test parsing
    parsed_config = StratumUtils.parse_merged_mining_worker_string(worker_string)
    assert parsed_config.ltc_address == "Labc123"
    assert parsed_config.doge_address == "Ddef456"
    assert parsed_config.worker_name == "testrig"
    
    # Test address validation
    assert StratumUtils.validate_address("Labc123", "ltc") == True
    assert StratumUtils.validate_address("Ddef456", "doge") == True
    
    logger.info("Merged mining utilities tests passed")

def test_extranonce_manager():
    """Test extranonce manager"""
    logger.info("Testing extranonce manager...")
    
    em = ExtranonceManager("abc123", 4)
    
    # Test extranonce2 generation
    en2_1 = em.generate_extranonce2()
    en2_2 = em.generate_extranonce2()
    
    assert en2_1 != en2_2  # Should be different
    assert len(bytes.fromhex(en2_1)) == 4  # Should be 4 bytes
    
    # Test update
    em.update_extranonce1("def456")
    assert em.extranonce1 == "def456"
    
    logger.info("Extranonce manager tests passed")

if __name__ == "__main__":
    # Run tests
    test_difficulty_management()
    test_merged_mining_utils()
    test_extranonce_manager()
    logger.info("All tests passed!")
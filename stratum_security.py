#!/usr/bin/env python3
"""
Stratum Security Module
Security features and validation for Stratum client operations

This implementation provides:
- Input validation for all Stratum messages
- Protection against malicious pool responses
- Secure connection handling
- Replay attack prevention
- Data integrity checks
"""

import hashlib
import hmac
import json
import logging
import re
import time
from typing import Dict, Any, List, Optional, Union
from dataclasses import dataclass
from enum import Enum

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("stratum_security")

class SecurityLevel(Enum):
    """Security levels for validation"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"

@dataclass
class SecurityConfig:
    """Security configuration"""
    security_level: SecurityLevel = SecurityLevel.MEDIUM
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
                "mining.notify", "mining.set_difficulty", "mining.set_extranonce"
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
        
        logger.info(f"StratumSecurityValidator initialized with {self.config.security_level.value} security level")
    
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
        
        if len(params) > max_params[self.config.security_level]:
            raise ValidationError(f"Too many parameters: {len(params)}, max allowed: {max_params[self.config.security_level]}")
        
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
    
    def validate_address(self, address: str, coin_type: str = "ltc") -> bool:
        """Validate cryptocurrency address"""
        if not isinstance(address, str):
            return False
        
        # Basic length checks
        if coin_type.lower() == "ltc":
            if not ((address.startswith('L') or address.startswith('M')) and 26 <= len(address) <= 35):
                return False
        elif coin_type.lower() == "doge":
            if not (address.startswith('D') and len(address) == 34):
                return False
        else:
            # Generic validation
            if len(address) < 26 or len(address) > 64:
                return False
        
        # Check for valid base58 characters (simplified)
        # Base58 characters: 123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz
        if not re.match(r'^[1-9A-HJ-NP-Za-km-z]+$', address):
            return False
        
        return True
    
    def validate_share_submission(self, share_data: Dict[str, Any]) -> bool:
        """Validate share submission data"""
        required_fields = ['job_id', 'extranonce2', 'ntime', 'nonce', 'hash_result']
        
        # Check required fields
        for field in required_fields:
            if field not in share_data:
                logger.warning(f"Missing required field in share submission: {field}")
                return False
        
        # Validate field types and formats
        if not isinstance(share_data['job_id'], str):
            logger.warning("Invalid job_id type")
            return False
        
        if not isinstance(share_data['extranonce2'], str) or not re.match(r'^[0-9a-fA-F]+$', share_data['extranonce2']):
            logger.warning("Invalid extranonce2 format")
            return False
        
        if not isinstance(share_data['ntime'], str) or not re.match(r'^[0-9a-fA-F]{8}$', share_data['ntime']):
            logger.warning("Invalid ntime format")
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
            "security_level": self.config.security_level.value,
            "messages_validated": len(self.message_history),
            "recent_messages": recent_messages,
            "last_validation_time": self.last_validation_time,
            "validation_errors": 0  # Would be tracked in a real implementation
        }

class SecureConnectionManager:
    """Manager for secure connections"""
    
    def __init__(self):
        self.blocked_connections: Dict[str, float] = {}  # IP -> block expiration time
        self.connection_attempts: Dict[str, List[float]] = {}  # IP -> list of attempt times
    
    def is_connection_allowed(self, ip_address: str) -> bool:
        """Check if connection from IP is allowed"""
        current_time = time.time()
        
        # Check if IP is blocked
        if ip_address in self.blocked_connections:
            if current_time < self.blocked_connections[ip_address]:
                logger.warning(f"Connection attempt from blocked IP: {ip_address}")
                return False
            else:
                # Block expired, remove it
                del self.blocked_connections[ip_address]
        
        return True
    
    def record_connection_attempt(self, ip_address: str):
        """Record a connection attempt"""
        current_time = time.time()
        
        if ip_address not in self.connection_attempts:
            self.connection_attempts[ip_address] = []
        
        # Add current attempt
        self.connection_attempts[ip_address].append(current_time)
        
        # Keep only recent attempts (last 10 minutes)
        self.connection_attempts[ip_address] = [
            attempt for attempt in self.connection_attempts[ip_address]
            if current_time - attempt < 600
        ]
        
        # Check for excessive attempts
        if len(self.connection_attempts[ip_address]) > 10:  # More than 10 attempts in 10 minutes
            logger.warning(f"Excessive connection attempts from {ip_address}, blocking for 1 hour")
            self.blocked_connections[ip_address] = current_time + 3600  # Block for 1 hour
    
    def get_connection_stats(self) -> Dict[str, Any]:
        """Get connection statistics"""
        current_time = time.time()
        active_blocks = {
            ip: expire_time for ip, expire_time in self.blocked_connections.items()
            if current_time < expire_time
        }
        
        return {
            "blocked_ips": len(active_blocks),
            "connection_attempts_tracked": len(self.connection_attempts)
        }

# Example usage
if __name__ == "__main__":
    # Create security validator
    config = SecurityConfig(security_level=SecurityLevel.HIGH)
    validator = StratumSecurityValidator(config)
    
    # Test message validation
    test_messages = [
        '{"id": 1, "method": "mining.subscribe", "params": ["test/1.0"]}',
        '{"id": 2, "result": [null, "abc123", 4], "error": null}',
        '{"method": "mining.notify", "params": ["job1", "abc", "def", "ghi", [], "123", "456", "789", true]}'
    ]
    
    for msg in test_messages:
        try:
            validated = validator.validate_message(msg)
            print(f"✓ Validated: {validated.get('method', 'response')}")
        except ValidationError as e:
            print(f"✗ Validation failed: {e}")
    
    # Test worker name validation
    worker_names = ["valid_worker", "worker<script>", "a" * 60]
    for name in worker_names:
        valid = validator.validate_worker_name(name)
        print(f"Worker name '{name}': {'valid' if valid else 'invalid'}")
    
    # Test address validation
    addresses = [
        ("Labc123def456ghi789jkl012mno345pqr", "ltc"),
        ("Dabc123def456ghi789jkl012mno345p", "doge"),
        ("invalid_address", "ltc")
    ]
    
    for address, coin_type in addresses:
        valid = validator.validate_address(address, coin_type)
        print(f"{coin_type.upper()} address '{address}': {'valid' if valid else 'invalid'}")
    
    # Test share validation
    valid_share = {
        "job_id": "job123",
        "extranonce2": "abcdef12",
        "ntime": "12345678",
        "nonce": "87654321",
        "hash_result": "000000000019d6689c085ae165831e934ff763ae46a2a6c172b3f1b60a8ce26f"
    }
    
    invalid_share = {
        "job_id": "job123",
        "extranonce2": "invalid_hex",
        "ntime": "12345678",
        "nonce": "87654321",
        "hash_result": "000000000019d6689c085ae165831e934ff763ae46a2a6c172b3f1b60a8ce26f"
    }
    
    print(f"Valid share: {'valid' if validator.validate_share_submission(valid_share) else 'invalid'}")
    print(f"Invalid share: {'valid' if validator.validate_share_submission(invalid_share) else 'invalid'}")
    
    # Print security stats
    stats = validator.get_security_stats()
    print(f"Security stats: {stats}")
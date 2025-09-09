#!/usr/bin/env python3
"""
Unit tests for the security manager
"""

import unittest
import asyncio
import logging
from unittest.mock import Mock, patch, AsyncMock
import json
import hashlib

# Add the refactored directory to the path
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

from security.stratum_security import StratumSecurityValidator, SecurityConfig, ValidationError

class TestStratumSecurityValidator(unittest.TestCase):
    """Test cases for StratumSecurityValidator"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.security_config = SecurityConfig()
        self.security_validator = StratumSecurityValidator(self.security_config)
    
    def test_initialization(self):
        """Test StratumSecurityValidator initialization"""
        self.assertIsInstance(self.security_validator, StratumSecurityValidator)
        self.assertEqual(self.security_validator.config, self.security_config)
        self.assertEqual(len(self.security_validator.message_history), 0)
    
    def test_validate_valid_json_message(self):
        """Test validation of valid JSON message"""
        message = {
            "id": 1,
            "method": "mining.subscribe",
            "params": ["enhanced-miner/1.0"]
        }
        
        result = self.security_validator.validate_message(message)
        self.assertEqual(result, message)
    
    def test_validate_invalid_json_message(self):
        """Test validation of invalid JSON message"""
        invalid_message = '{"id": 1, "method": "mining.subscribe", "params":}'
        
        with self.assertRaises(ValidationError):
            self.security_validator.validate_message(invalid_message)
    
    def test_validate_message_too_large(self):
        """Test validation of message that is too large"""
        # Create a large message
        large_message = {
            "id": 1,
            "method": "mining.subscribe",
            "params": ["a" * (self.security_config.max_message_size + 1)]
        }
        
        with self.assertRaises(ValidationError):
            self.security_validator.validate_message(json.dumps(large_message))
    
    def test_validate_invalid_method_name(self):
        """Test validation of invalid method name"""
        message = {
            "id": 1,
            "method": "invalid<script>alert('xss')</script>method",
            "params": []
        }
        
        with self.assertRaises(ValidationError):
            self.security_validator.validate_message(message)
    
    def test_validate_method_not_allowed(self):
        """Test validation of not allowed method"""
        message = {
            "id": 1,
            "method": "system.shutdown",
            "params": []
        }
        
        with self.assertRaises(ValidationError):
            self.security_validator.validate_message(message)
    
    def test_validate_worker_name_valid(self):
        """Test validation of valid worker name"""
        valid_worker_name = "worker01"
        result = self.security_validator.validate_worker_name(valid_worker_name)
        self.assertTrue(result)
    
    def test_validate_worker_name_invalid_characters(self):
        """Test validation of worker name with invalid characters"""
        invalid_worker_name = "worker<script>alert('xss')</script>"
        result = self.security_validator.validate_worker_name(invalid_worker_name)
        self.assertFalse(result)
    
    def test_validate_worker_name_too_long(self):
        """Test validation of worker name that is too long"""
        long_worker_name = "w" * 60
        result = self.security_validator.validate_worker_name(long_worker_name)
        self.assertFalse(result)
    
    def test_validate_doge_address_valid(self):
        """Test validation of valid DOGE address"""
        valid_address = "DAddK8wxjKawfFMT804PoX9fFc9s1Z3p3K"
        result = self.security_validator.validate_address(valid_address, "doge")
        self.assertTrue(result)
    
    def test_validate_doge_address_invalid_format(self):
        """Test validation of invalid DOGE address format"""
        invalid_address = "invalid_address"
        result = self.security_validator.validate_address(invalid_address, "doge")
        self.assertFalse(result)
    
    def test_validate_share_submission_valid(self):
        """Test validation of valid share submission"""
        share_data = {
            "job_id": "job123",
            "extranonce2": "abcdef12",
            "ntime": "12345678",
            "nonce": "87654321",
            "hash_result": "000000000019d6689c085ae1658os.getenv("LTC_ADDRESS", "your_ltc_address_here")0a8ce26f"
        }
        
        result = self.security_validator.validate_share_submission(share_data)
        self.assertTrue(result)
    
    def test_validate_share_submission_missing_field(self):
        """Test validation of share submission with missing field"""
        share_data = {
            "job_id": "job123",
            "extranonce2": "abcdef12",
            "ntime": "12345678",
            # Missing 'nonce' field
            "hash_result": "000000000019d6689c085ae1658os.getenv("LTC_ADDRESS", "your_ltc_address_here")0a8ce26f"
        }
        
        result = self.security_validator.validate_share_submission(share_data)
        self.assertFalse(result)
    
    def test_validate_share_submission_invalid_format(self):
        """Test validation of share submission with invalid format"""
        share_data = {
            "job_id": "job123",
            "extranonce2": "invalid_hex",
            "ntime": "12345678",
            "nonce": "87654321",
            "hash_result": "000000000019d6689c085ae1658os.getenv("LTC_ADDRESS", "your_ltc_address_here")0a8ce26f"
        }
        
        result = self.security_validator.validate_share_submission(share_data)
        self.assertFalse(result)
    
    def test_get_security_stats(self):
        """Test getting security statistics"""
        # Add some messages to history
        message = {
            "id": 1,
            "method": "mining.subscribe",
            "params": ["enhanced-miner/1.0"]
        }
        self.security_validator.validate_message(message)
        
        stats = self.security_validator.get_security_stats()
        self.assertIsInstance(stats, dict)
        self.assertIn("security_level", stats)
        self.assertIn("messages_validated", stats)
        self.assertIn("recent_messages", stats)
        self.assertIn("last_validation_time", stats)
        self.assertIn("validation_errors", stats)

class TestSecurityConfig(unittest.TestCase):
    """Test cases for SecurityConfig dataclass"""
    
    def test_security_config_initialization(self):
        """Test SecurityConfig initialization"""
        config = SecurityConfig()
        self.assertEqual(config.security_level, "medium")
        self.assertTrue(config.validate_json)
        self.assertTrue(config.validate_method_names)
        self.assertTrue(config.validate_parameter_types)
        self.assertEqual(config.max_message_size, 1024 * 1024)
        self.assertIsNotNone(config.allowed_methods)
        self.assertIsNotNone(config.blocked_ips)
    
    def test_security_config_custom_values(self):
        """Test SecurityConfig with custom values"""
        custom_methods = ["custom.method"]
        custom_blocked_ips = ["192.168.1.100"]
        
        config = SecurityConfig(
            security_level="high",
            max_message_size=512 * 1024,
            allowed_methods=custom_methods,
            blocked_ips=custom_blocked_ips
        )
        
        self.assertEqual(config.security_level, "high")
        self.assertEqual(config.max_message_size, 512 * 1024)
        self.assertEqual(config.allowed_methods, custom_methods)
        self.assertEqual(config.blocked_ips, custom_blocked_ips)

if __name__ == '__main__':
    # Configure logging for tests
    logging.basicConfig(level=logging.DEBUG)
    unittest.main()
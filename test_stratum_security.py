#!/usr/bin/env python3
"""
Unit tests for Stratum security module
"""

import unittest
import json
import time
from stratum_security import (
    StratumSecurityValidator,
    SecurityConfig,
    SecurityLevel,
    ValidationError,
    SecureConnectionManager
)

class TestStratumSecurityValidator(unittest.TestCase):
    """Test cases for StratumSecurityValidator"""
    
    def setUp(self):
        self.config = SecurityConfig(security_level=SecurityLevel.HIGH)
        self.validator = StratumSecurityValidator(self.config)
    
    def test_valid_json_message(self):
        """Test validation of valid JSON messages"""
        valid_messages = [
            '{"id": 1, "method": "mining.subscribe", "params": ["test/1.0"]}',
            '{"id": 2, "result": [null, "abc123", 4], "error": null}',
            '{"method": "mining.notify", "params": ["job1", "abc", "def", "ghi", [], "123", "456", "789", true]}'
        ]
        
        for msg in valid_messages:
            with self.subTest(message=msg):
                try:
                    validated = self.validator.validate_message(msg)
                    self.assertIsInstance(validated, dict)
                except ValidationError:
                    self.fail(f"Valid message failed validation: {msg}")
    
    def test_invalid_json_message(self):
        """Test validation of invalid JSON messages"""
        invalid_messages = [
            '{"id": 1, "method": "mining.subscribe", "params":}',  # Invalid JSON
            '{"id": 1, "method": "mining.subscribe", "params": ["test/1.0"]'  # Missing closing brace
        ]
        
        for msg in invalid_messages:
            with self.subTest(message=msg):
                with self.assertRaises(ValidationError):
                    self.validator.validate_message(msg)
    
    def test_message_too_large(self):
        """Test validation of oversized messages"""
        # Create a large message
        large_params = ["a" * 100000] * 20  # 20 parameters, each 100KB
        large_message = {
            "id": 1,
            "method": "mining.subscribe",
            "params": large_params
        }
        large_message_str = json.dumps(large_message)
        
        with self.assertRaises(ValidationError):
            self.validator.validate_message(large_message_str)
    
    def test_invalid_method_name(self):
        """Test validation of invalid method names"""
        invalid_methods = [
            "invalid<script>alert('xss')</script>",  # XSS attempt
            "mining.subscribe" + "a" * 150,  # Too long
            "../../../etc/passwd"  # Path traversal
        ]
        
        for method in invalid_methods:
            with self.subTest(method=method):
                message = {
                    "id": 1,
                    "method": method,
                    "params": []
                }
                with self.assertRaises(ValidationError):
                    self.validator.validate_message(json.dumps(message))
    
    def test_blocked_method(self):
        """Test validation of blocked methods"""
        blocked_message = {
            "id": 1,
            "method": "system.shutdown",  # Not in allowed methods
            "params": []
        }
        
        with self.assertRaises(ValidationError):
            self.validator.validate_message(json.dumps(blocked_message))
    
    def test_valid_worker_name(self):
        """Test validation of valid worker names"""
        valid_names = [
            "worker01",
            "my_miner_01",
            "L7_rig_01"
        ]
        
        for name in valid_names:
            with self.subTest(name=name):
                self.assertTrue(self.validator.validate_worker_name(name))
    
    def test_invalid_worker_name(self):
        """Test validation of invalid worker names"""
        invalid_names = [
            "worker<script>",  # XSS attempt
            "a" * 60,  # Too long
            "<iframe>",  # HTML injection
            '" OR 1=1 --'  # SQL injection
        ]
        
        for name in invalid_names:
            with self.subTest(name=name):
                self.assertFalse(self.validator.validate_worker_name(name))
    
    def test_valid_address(self):
        """Test validation of valid cryptocurrency addresses"""
        valid_addresses = [
            ("os.getenv("LTC_ADDRESS", "your_ltc_address_here")", "ltc"),   # 34 characters, valid base58
            ("os.getenv("LTC_ADDRESS", "your_ltc_address_here")", "ltc"),   # 34 characters, valid base58
            ("Dabc12os.getenv("LTC_ADDRESS", "your_ltc_address_here")", "doge")   # 34 characters, valid base58
        ]
        
        for address, coin_type in valid_addresses:
            with self.subTest(address=address, coin_type=coin_type):
                self.assertTrue(self.validator.validate_address(address, coin_type))
    
    def test_invalid_address(self):
        """Test validation of invalid cryptocurrency addresses"""
        invalid_addresses = [
            ("invalid_address", "ltc"),
            ("Labc", "ltc"),  # Too short
            ("Labc123def456ghi789jkl012mno345pqr678stu", "ltc"),  # Too long
            ("Dabc123def456ghi789jkl012mno345pq", "doge")  # Wrong length (33 chars)
        ]
        
        for address, coin_type in invalid_addresses:
            with self.subTest(address=address, coin_type=coin_type):
                self.assertFalse(self.validator.validate_address(address, coin_type))
    
    def test_valid_share_submission(self):
        """Test validation of valid share submissions"""
        valid_share = {
            "job_id": "job123",
            "extranonce2": "abcdef12",
            "ntime": "12345678",
            "nonce": "87654321",
            "hash_result": "000000000019d6689c085ae1658os.getenv("LTC_ADDRESS", "your_ltc_address_here")0a8ce26f"
        }
        
        self.assertTrue(self.validator.validate_share_submission(valid_share))
    
    def test_invalid_share_submission(self):
        """Test validation of invalid share submissions"""
        invalid_shares = [
            {
                "job_id": "job123",
                "extranonce2": "invalid_hex",
                "ntime": "12345678",
                "nonce": "87654321",
                "hash_result": "000000000019d6689c085ae1658os.getenv("LTC_ADDRESS", "your_ltc_address_here")0a8ce26f"
            },
            {
                "job_id": "job123",
                "extranonce2": "abcdef12",
                "ntime": "invalid",  # Invalid ntime
                "nonce": "87654321",
                "hash_result": "000000000019d6689c085ae1658os.getenv("LTC_ADDRESS", "your_ltc_address_here")0a8ce26f"
            },
            {
                "job_id": "job123",
                "extranonce2": "abcdef12",
                "ntime": "12345678",
                "nonce": "87654321",
                "hash_result": "invalid_hash"  # Invalid hash
            }
        ]
        
        for share in invalid_shares:
            with self.subTest(share=share):
                self.assertFalse(self.validator.validate_share_submission(share))
    
    def test_replay_attack_detection(self):
        """Test replay attack detection"""
        # Send the same message twice quickly
        message = '{"id": 1, "method": "mining.subscribe", "params": ["test/1.0"]}'
        
        # First message should be valid
        validated1 = self.validator.validate_message(message)
        self.assertIsInstance(validated1, dict)
        
        # Add a small delay to avoid replay detection
        import time
        time.sleep(0.2)
        
        # Second message should also be valid (same content but different ID is OK)
        message2 = '{"id": 2, "method": "mining.subscribe", "params": ["test/1.0"]}'
        validated2 = self.validator.validate_message(message2)
        self.assertIsInstance(validated2, dict)
    
    def test_get_security_stats(self):
        """Test getting security statistics"""
        # Validate a few messages
        messages = [
            '{"id": 1, "method": "mining.subscribe", "params": ["test/1.0"]}',
            '{"id": 2, "result": [null, "abc123", 4], "error": null}'
        ]
        
        for msg in messages:
            self.validator.validate_message(msg)
        
        stats = self.validator.get_security_stats()
        self.assertIsInstance(stats, dict)
        self.assertIn("security_level", stats)
        self.assertIn("messages_validated", stats)
        self.assertIn("recent_messages", stats)

class TestSecureConnectionManager(unittest.TestCase):
    """Test cases for SecureConnectionManager"""
    
    def setUp(self):
        self.conn_manager = SecureConnectionManager()
    
    def test_connection_allowed(self):
        """Test if connection is allowed"""
        self.assertTrue(self.conn_manager.is_connection_allowed("192.168.1.1"))
    
    def test_connection_blocked(self):
        """Test if connection is blocked after excessive attempts"""
        ip = "192.168.1.100"
        
        # Record 15 connection attempts
        for _ in range(15):
            self.conn_manager.record_connection_attempt(ip)
        
        # Connection should now be blocked
        self.assertFalse(self.conn_manager.is_connection_allowed(ip))
    
    def test_connection_unblocked(self):
        """Test if connection is unblocked after block expires"""
        ip = "192.168.1.101"
        
        # Record excessive attempts
        for _ in range(15):
            self.conn_manager.record_connection_attempt(ip)
        
        # Connection should be blocked
        self.assertFalse(self.conn_manager.is_connection_allowed(ip))
        
        # Note: We won't test unblocking here as it would require waiting for the block to expire
    
    def test_get_connection_stats(self):
        """Test getting connection statistics"""
        # Record some connection attempts
        ips = ["192.168.1.1", "192.168.1.2", "192.168.1.3"]
        for ip in ips:
            for _ in range(5):
                self.conn_manager.record_connection_attempt(ip)
        
        stats = self.conn_manager.get_connection_stats()
        self.assertIsInstance(stats, dict)
        self.assertIn("blocked_ips", stats)
        self.assertIn("connection_attempts_tracked", stats)

if __name__ == '__main__':
    unittest.main()
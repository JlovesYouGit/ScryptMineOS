#!/usr/bin/env python3
"""
Unit tests for the Stratum client
"""

import unittest
import asyncio
import logging
from unittest.mock import Mock, patch, AsyncMock

# Add the refactored directory to the path
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

from network.stratum_client import EnhancedStratumClient, StratumConfig, StratumMethod
from network.stratum_protocol import DifficultyManager, ExtranonceManager

class TestEnhancedStratumClient(unittest.TestCase):
    """Test cases for EnhancedStratumClient"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.config = StratumConfig(
            host="test.pool.com",
            port=3333,
            username="testuser",
            password=os.getenv("POOL_PASSWORD", "x")"POOL_PASSWORD", "x")"
        )
        self.stratum_client = EnhancedStratumClient(self.config)
    
    def test_initialization(self):
        """Test EnhancedStratumClient initialization"""
        self.assertIsInstance(self.stratum_client, EnhancedStratumClient)
        self.assertEqual(self.stratum_client.config, self.config)
        self.assertFalse(self.stratum_client.connected)
        self.assertFalse(self.stratum_client.subscribed)
        self.assertFalse(self.stratum_client.authorized)
        
        # Check that enhanced components are initialized
        self.assertIsNotNone(self.stratum_client.security_validator)
        self.assertIsNotNone(self.stratum_client.monitor)
        self.assertIsNotNone(self.stratum_client.difficulty_manager)
        self.assertIsNotNone(self.stratum_client.extranonce_manager)
    
    def test_stratum_config(self):
        """Test StratumConfig dataclass"""
        config = StratumConfig(
            host="test.pool.com",
            port=3333,
            username="testuser",
            password=os.getenv("POOL_PASSWORD", "x")"POOL_PASSWORD", "x")"
        )
        
        self.assertEqual(config.host, "test.pool.com")
        self.assertEqual(config.port, 3333)
        self.assertEqual(config.username, "testuser")
        self.assertEqual(config.password, "x")
        self.assertEqual(config.version.value, "stratum1")  # Default value
    
    @patch('network.stratum_client.asyncio.open_connection')
    def test_connect_async_success(self, mock_open_connection):
        """Test successful async connection"""
        # Mock the asyncio.open_connection to return mock reader/writer
        mock_reader = AsyncMock()
        mock_writer = AsyncMock()
        mock_open_connection.return_value = (mock_reader, mock_writer)
        
        # Run the async connect method
        result = asyncio.run(self.stratum_client.connect_async())
        
        self.assertTrue(result)
        self.assertTrue(self.stratum_client.connected)
        mock_open_connection.assert_called_once_with("test.pool.com", 3333)
    
    @patch('network.stratum_client.asyncio.open_connection')
    def test_connect_async_failure(self, mock_open_connection):
        """Test failed async connection"""
        # Mock the asyncio.open_connection to raise an exception
        mock_open_connection.side_effect = Exception("Connection failed")
        
        # Run the async connect method
        result = asyncio.run(self.stratum_client.connect_async())
        
        self.assertFalse(result)
        self.assertFalse(self.stratum_client.connected)
    
    def test_stratum_method_enum(self):
        """Test StratumMethod enum"""
        self.assertEqual(StratumMethod.SUBSCRIBE, "mining.subscribe")
        self.assertEqual(StratumMethod.AUTHORIZE, "mining.authorize")
        self.assertEqual(StratumMethod.NOTIFY, "mining.notify")
        self.assertEqual(StratumMethod.SET_DIFFICULTY, "mining.set_difficulty")
        self.assertEqual(StratumMethod.SUBMIT, "mining.submit")

class TestDifficultyManager(unittest.TestCase):
    """Test cases for DifficultyManager"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.difficulty_manager = DifficultyManager(current_difficulty=1.0)
    
    def test_initialization(self):
        """Test DifficultyManager initialization"""
        self.assertEqual(self.difficulty_manager.current_difficulty, 1.0)
        self.assertIsNotNone(self.difficulty_manager.target)
        self.assertEqual(self.difficulty_manager.min_difficulty, 0.001)
        self.assertEqual(self.difficulty_manager.max_difficulty, 1000000.0)
    
    def test_update_difficulty_success(self):
        """Test successful difficulty update"""
        result = self.difficulty_manager.update_difficulty(2.0)
        self.assertTrue(result)
        self.assertEqual(self.difficulty_manager.current_difficulty, 2.0)
    
    def test_update_difficulty_out_of_range(self):
        """Test difficulty update with out of range values"""
        # Test too low
        result = self.difficulty_manager.update_difficulty(0.0001)
        self.assertFalse(result)
        self.assertEqual(self.difficulty_manager.current_difficulty, 1.0)  # Should remain unchanged
        
        # Test too high
        result = self.difficulty_manager.update_difficulty(2000000.0)
        self.assertFalse(result)
        self.assertEqual(self.difficulty_manager.current_difficulty, 1.0)  # Should remain unchanged
    
    def test_adjust_difficulty(self):
        """Test difficulty adjustment based on share acceptance"""
        # Test with high rejection rate (should decrease difficulty)
        new_diff = self.difficulty_manager.adjust_difficulty(90, 10)  # 90% acceptance
        self.assertLess(new_diff, 1.0)
        
        # Reset and test with very high acceptance rate (should increase difficulty)
        self.difficulty_manager.update_difficulty(1.0)
        new_diff = self.difficulty_manager.adjust_difficulty(999, 1)  # 99.9% acceptance
        self.assertGreater(new_diff, 1.0)

class TestExtranonceManager(unittest.TestCase):
    """Test cases for ExtranonceManager"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.extranonce_manager = ExtranonceManager("abc123", 4)
    
    def test_initialization(self):
        """Test ExtranonceManager initialization"""
        self.assertEqual(self.extranonce_manager.extranonce1, "abc123")
        self.assertEqual(self.extranonce_manager.extranonce2_size, 4)
        self.assertEqual(self.extranonce_manager.extranonce2_counter, 0)
    
    def test_generate_extranonce2(self):
        """Test extranonce2 generation"""
        # Generate first extranonce2
        en2_1 = self.extranonce_manager.generate_extranonce2()
        self.assertEqual(self.extranonce_manager.extranonce2_counter, 1)
        
        # Generate second extranonce2
        en2_2 = self.extranonce_manager.generate_extranonce2()
        self.assertEqual(self.extranonce_manager.extranonce2_counter, 2)
        
        # They should be different
        self.assertNotEqual(en2_1, en2_2)
        
        # Should be valid hex and correct length
        self.assertEqual(len(bytes.fromhex(en2_1)), 4)

if __name__ == '__main__':
    # Configure logging for tests
    logging.basicConfig(level=logging.DEBUG)
    unittest.main()
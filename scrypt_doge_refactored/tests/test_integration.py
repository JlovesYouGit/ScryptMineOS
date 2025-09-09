#!/usr/bin/env python3
"""
Integration tests for the refactored mining system
"""

import unittest
import asyncio
import logging
from unittest.mock import Mock, patch, AsyncMock
import sys
import os

# Add the refactored directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from core.mining_service import MiningService
from core.config_manager import ConfigManager, Config, PoolConfig, EconomicConfig
from network.stratum_client import EnhancedStratumClient
from security.stratum_security import StratumSecurityValidator

class TestSystemIntegration(unittest.TestCase):
    """Integration tests for the complete mining system"""
    
    def setUp(self):
        """Set up test fixtures"""
        # Create a minimal configuration for testing
        self.config = {
            "pool_host": "test.pool.com",
            "pool_port": 3333,
            "wallet_address": "Dtestwalletaddress1234567890",
            "worker_password=os.getenv("POOL_PASSWORD", "x")"POOL_PASSWORD", "x")"
        }
        
        self.mining_service = MiningService(self.config)
    
    def test_mining_service_initialization(self):
        """Test that mining service initializes all components correctly"""
        # Run async initialization
        result = asyncio.run(self.mining_service.initialize())
        
        self.assertTrue(result)
        self.assertTrue(self.mining_service.status.initialized)
        self.assertIsNotNone(self.mining_service.stratum_client)
        self.assertIsNotNone(self.mining_service.performance_optimizer)
        self.assertIsNotNone(self.mining_service.asic_emulator)
        self.assertIsNotNone(self.mining_service.gpu_hybrid)
        self.assertIsNotNone(self.mining_service.monitor)
        self.assertIsNotNone(self.mining_service.economic_guardian)
        self.assertIsNotNone(self.mining_service.continuous_miner)
    
    @patch('network.stratum_client.asyncio.open_connection')
    def test_stratum_client_connection(self, mock_open_connection):
        """Test Stratum client connection integration"""
        # Mock the asyncio.open_connection to return mock reader/writer
        mock_reader = AsyncMock()
        mock_writer = AsyncMock()
        mock_open_connection.return_value = (mock_reader, mock_writer)
        
        # Create Stratum client
        stratum_client = EnhancedStratumClient(
            host="test.pool.com",
            port=3333,
            user="testuser",
            password=os.getenv("POOL_PASSWORD", "x")"POOL_PASSWORD", "x")"
        )
        
        # Run async connect
        result = asyncio.run(stratum_client.connect_async())
        
        self.assertTrue(result)
        self.assertTrue(stratum_client.connected)
        mock_open_connection.assert_called_once_with("test.pool.com", 3333)
    
    def test_security_validator_integration(self):
        """Test security validator integration with Stratum client"""
        # Create Stratum client which should have security validator
        stratum_client = EnhancedStratumClient(
            host="test.pool.com",
            port=3333,
            user="testuser",
            password=os.getenv("POOL_PASSWORD", "x")"POOL_PASSWORD", "x")"
        )
        
        self.assertIsNotNone(stratum_client.security_validator)
        self.assertIsInstance(stratum_client.security_validator, StratumSecurityValidator)
        
        # Test message validation
        message = {
            "id": 1,
            "method": "mining.subscribe",
            "params": ["enhanced-miner/1.0"]
        }
        
        result = stratum_client.security_validator.validate_message(message)
        self.assertEqual(result, message)
    
    def test_config_manager_integration(self):
        """Test configuration manager integration"""
        # Create config manager
        config_manager = ConfigManager()
        
        # Run async config loading
        config = asyncio.run(config_manager.load_config())
        
        self.assertIsInstance(config, Config)
        # Should have at least one pool configured by default
        self.assertGreater(len(config.pools), 0)
        self.assertIsInstance(config.pools[0], PoolConfig)
        self.assertIsInstance(config.economic, EconomicConfig)
    
    def test_component_interoperability(self):
        """Test that components can work together"""
        # Initialize mining service
        result = asyncio.run(self.mining_service.initialize())
        self.assertTrue(result)
        
        # Verify that components reference each other correctly
        # For example, the monitor should be accessible
        self.assertIsNotNone(self.mining_service.monitor)
        
        # The security validator should be part of the Stratum client
        self.assertIsNotNone(self.mining_service.stratum_client.security_validator)
        
        # Components should have proper configuration
        self.assertEqual(
            self.mining_service.stratum_client.config.username,
            self.config["wallet_address"]
        )

class TestEndToEndWorkflow(unittest.TestCase):
    """End-to-end workflow tests"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.config = {
            "pool_host": "test.pool.com",
            "pool_port": 3333,
            "wallet_address": "Dtestwalletaddress1234567890",
            "worker_password=os.getenv("POOL_PASSWORD", "x")"POOL_PASSWORD", "x")"
        }
        
        self.mining_service = MiningService(self.config)
    
    @patch('network.stratum_client.asyncio.open_connection')
    def test_complete_mining_workflow(self, mock_open_connection):
        """Test complete mining workflow from initialization to connection"""
        # Mock successful connection
        mock_reader = AsyncMock()
        mock_writer = AsyncMock()
        mock_open_connection.return_value = (mock_reader, mock_writer)
        
        async def workflow():
            # 1. Initialize service
            init_result = await self.mining_service.initialize()
            self.assertTrue(init_result)
            
            # 2. Connect to pool
            connect_result = await self.mining_service.connect_to_pool()
            # This might fail in testing environment, but we're testing the workflow
            # The important part is that it doesn't crash
            
            # 3. Get status
            status = self.mining_service.get_status()
            self.assertIsInstance(status, type(self.mining_service.status))
            
            # 4. Get statistics
            stats = await self.mining_service.get_statistics()
            self.assertIsInstance(stats, dict)
            self.assertIn("status", stats)
            self.assertIn("components", stats)
        
        # Run the workflow
        asyncio.run(workflow())
    
    def test_error_handling_workflow(self):
        """Test error handling in the workflow"""
        # Test that the service handles errors gracefully
        status = self.mining_service.get_status()
        self.assertFalse(status.connected)
        self.assertFalse(status.mining)
        self.assertIsNone(status.error)
        
        # Test statistics without initialization
        stats = asyncio.run(self.mining_service.get_statistics())
        self.assertIsInstance(stats, dict)

if __name__ == '__main__':
    # Configure logging for tests
    logging.basicConfig(level=logging.DEBUG)
    unittest.main()
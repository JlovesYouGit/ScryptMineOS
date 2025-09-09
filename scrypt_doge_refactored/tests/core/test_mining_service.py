#!/usr/bin/env python3
"""
Unit tests for the core mining service
"""

import unittest
import asyncio
import logging
from unittest.mock import Mock, patch, AsyncMock

# Add the refactored directory to the path
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

from core.mining_service import MiningService, ServiceStatus
from config.constants import SYSTEM, MINING, NETWORK

class TestMiningService(unittest.TestCase):
    """Test cases for MiningService"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.config = {
            "pool_host": "test.pool.com",
            "pool_port": 3333,
            "wallet_address": "Dtestwalletaddress1234567890",
            "worker_password=os.getenv("POOL_PASSWORD", "x")"POOL_PASSWORD", "x")"
        }
        self.mining_service = MiningService(self.config)
    
    def test_initialization(self):
        """Test MiningService initialization"""
        self.assertIsInstance(self.mining_service, MiningService)
        self.assertEqual(self.mining_service.config, self.config)
        self.assertFalse(self.mining_service.status.initialized)
        self.assertFalse(self.mining_service.status.connected)
        self.assertFalse(self.mining_service.status.mining)
        self.assertIsNone(self.mining_service.status.error)
    
    @patch('core.mining_service.EnhancedStratumClient')
    @patch('core.mining_service.GPUPerformanceOptimizer')
    @patch('core.mining_service.ASICHardwareEmulator')
    @patch('core.mining_service.GPUASICHybrid')
    @patch('core.mining_service.SystemMonitor')
    @patch('core.mining_service.EconomicGuardian')
    @patch('core.mining_service.ContinuousMiner')
    def test_initialize_success(self, mock_continuous_miner, mock_economic_guardian, 
                               mock_system_monitor, mock_gpu_hybrid, mock_asic_emulator,
                               mock_performance_optimizer, mock_stratum_client):
        """Test successful initialization of all components"""
        # Mock all components to return successfully
        mock_stratum_client.return_value = Mock()
        mock_performance_optimizer.return_value = Mock()
        mock_asic_emulator.return_value = Mock()
        mock_gpu_hybrid.return_value = Mock()
        mock_system_monitor.return_value = Mock()
        mock_economic_guardian.return_value = Mock()
        mock_continuous_miner.return_value = Mock()
        
        # Run the async initialize method
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
    
    def test_get_status(self):
        """Test getting service status"""
        status = self.mining_service.get_status()
        self.assertIsInstance(status, ServiceStatus)
        self.assertFalse(status.initialized)
        self.assertFalse(status.connected)
        self.assertFalse(status.mining)
        self.assertIsNone(status.error)

class TestServiceStatus(unittest.TestCase):
    """Test cases for ServiceStatus dataclass"""
    
    def test_service_status_initialization(self):
        """Test ServiceStatus initialization"""
        status = ServiceStatus()
        self.assertFalse(status.initialized)
        self.assertFalse(status.connected)
        self.assertFalse(status.mining)
        self.assertIsNone(status.error)
    
    def test_service_status_with_values(self):
        """Test ServiceStatus with specific values"""
        status = ServiceStatus(
            initialized=True,
            connected=True,
            mining=True,
            error="Test error"
        )
        self.assertTrue(status.initialized)
        self.assertTrue(status.connected)
        self.assertTrue(status.mining)
        self.assertEqual(status.error, "Test error")

if __name__ == '__main__':
    # Configure logging for tests
    logging.basicConfig(level=logging.DEBUG)
    unittest.main()
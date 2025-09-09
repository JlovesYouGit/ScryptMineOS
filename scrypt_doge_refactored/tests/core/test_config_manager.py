#!/usr/bin/env python3
"""
Unit tests for the configuration manager
"""

import unittest
import asyncio
import logging
import tempfile
import os
from pathlib import Path

# Add the refactored directory to the path
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

from core.config_manager import ConfigManager, Config, PoolConfig, EconomicConfig
from config.constants import SYSTEM, MINING, NETWORK

class TestConfigManager(unittest.TestCase):
    """Test cases for ConfigManager"""
    
    def setUp(self):
        """Set up test fixtures"""
        # Create a temporary config file for testing
        self.temp_dir = tempfile.mkdtemp()
        self.config_path = os.path.join(self.temp_dir, "test_config.yaml")
        
        # Create a sample config
        sample_config = """
default:
  environment: production
  pools:
    - url: stratum+tcp://test.pool.com:3333
      username: testuser
      password: x
      algorithm: scrypt
      priority: 1
      timeout: 30
      retry_attempts: 3
      enable_tls: false
  economic:
    enabled: true
    max_power_cost: 0.12
    min_profitability: 0.01
    shutdown_on_unprofitable: true
    profitability_check_interval: 300
    wallet_address: "Dtestwalletaddress1234567890"
    auto_withdrawal_threshold: 0.01

development:
  logging:
    level: DEBUG

production:
  logging:
    level: WARNING
"""
        
        with open(self.config_path, 'w') as f:
            f.write(sample_config)
        
        self.config_manager = ConfigManager(self.config_path)
    
    def tearDown(self):
        """Clean up test fixtures"""
        # Remove temporary files
        if os.path.exists(self.config_path):
            os.remove(self.config_path)
        os.rmdir(self.temp_dir)
    
    def test_config_manager_initialization(self):
        """Test ConfigManager initialization"""
        self.assertIsInstance(self.config_manager, ConfigManager)
        self.assertEqual(str(self.config_manager.config_path), self.config_path)
    
    def test_load_config_success(self):
        """Test successful config loading"""
        # Run the async load_config method
        config = asyncio.run(self.config_manager.load_config())
        
        self.assertIsInstance(config, Config)
        self.assertEqual(len(config.pools), 1)
        self.assertIsInstance(config.pools[0], PoolConfig)
        self.assertIsInstance(config.economic, EconomicConfig)
        self.assertEqual(config.economic.wallet_address, "Dtestwalletaddress1234567890")
    
    def test_config_validation(self):
        """Test config validation"""
        config = asyncio.run(self.config_manager.load_config())
        
        # Should not raise an exception for valid config
        try:
            config.validate()
            validation_passed = True
        except ValueError:
            validation_passed = False
        
        self.assertTrue(validation_passed)
    
    def test_get_config(self):
        """Test getting loaded config"""
        # Load config first
        asyncio.run(self.config_manager.load_config())
        
        # Get config
        config = self.config_manager.get_config()
        
        self.assertIsInstance(config, Config)
        self.assertEqual(len(config.pools), 1)

class TestConfigDataclasses(unittest.TestCase):
    """Test cases for config dataclasses"""
    
    def test_pool_config(self):
        """Test PoolConfig dataclass"""
        pool_config = PoolConfig(
            url="stratum+tcp://test.pool.com:3333",
            username="testuser",
            password="x"
        )
        
        self.assertEqual(pool_config.url, "stratum+tcp://test.pool.com:3333")
        self.assertEqual(pool_config.username, "testuser")
        self.assertEqual(pool_config.password, "x")
        self.assertEqual(pool_config.algorithm, "scrypt")  # Default value
        self.assertEqual(pool_config.priority, 1)  # Default value
    
    def test_economic_config(self):
        """Test EconomicConfig dataclass"""
        economic_config = EconomicConfig(
            enabled=True,
            wallet_address="Dtestwalletaddress1234567890"
        )
        
        self.assertTrue(economic_config.enabled)
        self.assertEqual(economic_config.wallet_address, "Dtestwalletaddress1234567890")
        self.assertEqual(economic_config.max_power_cost, 0.12)  # Default value
        self.assertEqual(economic_config.min_profitability, 0.01)  # Default value

if __name__ == '__main__':
    # Configure logging for tests
    logging.basicConfig(level=logging.DEBUG)
    unittest.main()
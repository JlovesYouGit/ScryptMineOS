"""
Complete integration test to verify all components work together seamlessly.
"""

import unittest
import asyncio
import logging
import os
import sys
import tempfile
import json
from unittest.mock import Mock, patch, AsyncMock

# Add the refactored directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from core.main_service import MiningSystemService, ServiceManager
from core.config_manager import ConfigManager
from network.stratum_client import EnhancedStratumClient
from security.security_manager import SecurityManager
from monitoring.system_monitor import SystemMonitor
from hardware.asic_emulator import ASICHardwareEmulator
from utils.logger import StructuredLogger, AlertManager


class TestCompleteIntegration(unittest.TestCase):
    """Complete integration test for all system components working together"""
    
    def setUp(self):
        """Set up test fixtures"""
        # Create a temporary directory for test files
        self.test_dir = tempfile.mkdtemp()
        
        # Create a comprehensive configuration for testing
        self.test_config_dict = {
            "environment": "testing",
            "mining": {
                "algorithm": "scrypt",
                "threads": 4,
                "intensity": 16
            },
            "pools": [
                {
                    "url": "stratum+tcp://test.pool.com:3333",
                    "username": "testuser",
                    "password=os.getenv("POOL_PASSWORD", "x")"POOL_PASSWORD", "x")",
                    "algorithm": "scrypt",
                    "priority": 1,
                    "timeout": 30,
                    "retry_attempts": 3,
                    "enable_tls": False
                }
            ],
            "hardware": {
                "type": "asic",
                "device_ids": [],
                "temperature_limit": 80
            },
            "economic": {
                "enabled": True,
                "max_power_cost": 0.12,
                "min_profitability": 0.01,
                "shutdown_on_unprofitable": False,
                "profitability_check_interval": 300,
                "wallet_address": "Dtestwalletaddress1234567890",
                "auto_withdrawal_threshold": 0.01
            },
            "security": {
                "enable_encryption": False,
                "rate_limiting_enabled": True,
                "max_requests_per_minute": 60,
                "enable_ddos_protection": True,
                "tls_verify": True,
                "allowed_ips": ["127.0.0.1"]
            },
            "monitoring": {
                "enabled": True,
                "metrics_port": 8080,
                "health_check_port": 8081,
                "enable_prometheus": False,
                "log_performance_metrics": True
            },
            "performance": {
                "auto_tune_enabled": True,
                "benchmark_interval": 3600
            },
            "logging": {
                "level": "DEBUG",
                "file_path": f"{self.test_dir}/test_mining.log",
                "max_file_size": 10485760,
                "backup_count": 5,
                "enable_structured_logging": True,
                "enable_console": True
            }
        }
        
        # Create temporary config file for testing
        self.config_file = os.path.join(self.test_dir, "test_config.yaml")
        import yaml
        with open(self.config_file, 'w') as f:
            yaml.dump(self.test_config_dict, f)
        
        self.config_manager = ConfigManager(self.config_file)
    
    def tearDown(self):
        """Clean up test fixtures"""
        import shutil
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)
    
    async def async_setUp(self):
        """Async setup for async tests"""
        self.config = await self.config_manager.load_config()
    
    @patch('network.stratum_client.asyncio.open_connection')
    def test_complete_system_lifecycle(self, mock_open_connection):
        """Test complete system lifecycle from initialization to shutdown"""
        # Mock successful connection
        mock_reader = AsyncMock()
        mock_writer = AsyncMock()
        mock_open_connection.return_value = (mock_reader, mock_writer)
        
        async def run_test():
            # Step 1: Initialize system
            system_service = MiningSystemService(self.config_manager)
            self.assertIsNotNone(system_service)
            
            # Step 2: Initialize all components
            init_success = await system_service.initialize()
            self.assertTrue(init_success)
            
            # Verify all components are initialized
            self.assertIsNotNone(system_service.mining_service)
            self.assertIsNotNone(system_service.security_manager)
            self.assertIsNotNone(system_service.system_monitor)
            self.assertIsNotNone(system_service.pool_manager)
            
            # Step 3: Start system
            # Note: We won't actually start the mining loop in tests
            # But we can verify the initialization worked
            
            # Step 4: Test component interactions
            # Test security manager
            is_allowed = system_service.security_manager.is_request_allowed("127.0.0.1")
            self.assertTrue(is_allowed)
            
            # Test system monitor
            system_service.system_monitor.record_share_accepted()
            system_service.system_monitor.record_share_rejected("test reason")
            
            share_stats = system_service.system_monitor.get_share_stats()
            self.assertEqual(share_stats["accepted"], 1)
            self.assertEqual(share_stats["rejected"], 1)
            
            # Test logging
            logger = StructuredLogger("test_integration", f"{self.test_dir}/integration_test.log")
            logger.info("integration_test", {"test": "value"}, "Integration test event")
            
            # Test alerting
            alert_manager = AlertManager(logger)
            alert_manager.send_alert("INTEGRATION_TEST", "This is an integration test alert")
            
            # Step 5: Get system status
            status = system_service.get_status()
            self.assertIsInstance(status, dict)
            self.assertTrue(status["components"])  # Should have components
            
            # Step 6: Stop system
            await system_service.stop()
            
            # Verify system is stopped
            # Note: In a real test, we would verify that all tasks are cancelled
            # and resources are cleaned up
            
        asyncio.run(run_test())
    
    def test_component_interoperability(self):
        """Test that all components can work together"""
        async def run_test():
            # Load configuration
            config = await self.config_manager.load_config()
            
            # Test security manager with monitoring
            security_manager = SecurityManager(config.security)
            await security_manager.start()
            
            # Test system monitor with security
            system_monitor = SystemMonitor({
                "collection_interval": 5,
                "health_check_interval": 60
            })
            
            # Simulate some events that would trigger both components
            system_monitor.record_share_accepted()
            system_monitor.record_share_rejected("test reason")
            
            # Test that security features work
            self.assertTrue(security_manager.is_request_allowed("127.0.0.1"))
            
            # Test hardware emulator with monitoring
            asic_emulator = ASICHardwareEmulator()
            initialized = asic_emulator.initialize()
            self.assertTrue(initialized)
            
            # Get status and verify it works with monitoring
            status = asic_emulator.get_antminer_status()
            self.assertIsInstance(status, dict)
            self.assertIn("hashrate", status)
            
            # Clean up
            await security_manager.stop()
        
        asyncio.run(run_test())
    
    @patch('network.stratum_client.asyncio.open_connection')
    def test_end_to_end_mining_workflow(self, mock_open_connection):
        """Test end-to-end mining workflow"""
        # Mock successful connection
        mock_reader = AsyncMock()
        mock_writer = AsyncMock()
        mock_open_connection.return_value = (mock_reader, mock_writer)
        
        async def run_test():
            # Initialize system
            system_service = MiningSystemService(self.config_manager)
            init_success = await system_service.initialize()
            self.assertTrue(init_success)
            
            # Test Stratum client integration
            from network.stratum_client import EnhancedStratumClient
            
            client = EnhancedStratumClient(
                host="test.pool.com",
                port=3333,
                user="testuser",
                password=os.getenv("POOL_PASSWORD", "x")"POOL_PASSWORD", "x")"
            )
            
            # Test connection (mocked)
            connected = client.connect()
            self.assertTrue(connected)
            
            # Test subscription and authorization (mocked)
            # In a real test, we would mock the actual network responses
            # For now, we'll just verify the client structure
            
            # Test that all monitoring components work together
            stats = client.get_stats()
            self.assertIsInstance(stats, dict)
            self.assertIn("connection", stats)
            
            # Test security validation
            is_valid_address = system_service.security_manager.validate_wallet_address(
                "Dtestwalletaddress1234567890", "doge"
            )
            self.assertTrue(is_valid_address)
            
            # Test economic guardian
            from security.economic_guardian import EconomicGuardian
            economic_guardian = EconomicGuardian(config.economic.__dict__)
            
            # Test profitability check (will use simulated data)
            summary = economic_guardian.get_profitability_summary()
            self.assertIsInstance(summary, dict)
            
            # Test performance optimizer
            from optimization.performance_optimizer import GPUPerformanceOptimizer
            optimizer = GPUPerformanceOptimizer()
            
            # Test baseline measurement
            baseline = optimizer.measure_baseline()
            self.assertIsInstance(baseline, optimizer.PerformanceMetrics)
            
            # Clean up
            client.disconnect()
            await economic_guardian.stop_monitoring()
        
        asyncio.run(run_test())
    
    def test_configuration_propagation(self):
        """Test that configuration is properly propagated to all components"""
        async def run_test():
            # Load configuration
            config = await self.config_manager.load_config()
            
            # Verify configuration structure
            self.assertEqual(config.environment.value, "testing")
            self.assertEqual(len(config.pools), 1)
            self.assertTrue(config.economic.enabled)
            self.assertTrue(config.security.enable_ddos_protection)
            
            # Test that pool configuration is correct
            pool = config.pools[0]
            self.assertEqual(pool.url, "stratum+tcp://test.pool.com:3333")
            self.assertEqual(pool.username, "testuser")
            self.assertEqual(pool.algorithm, "scrypt")
            
            # Test that economic configuration is correct
            economic = config.economic
            self.assertEqual(economic.max_power_cost, 0.12)
            self.assertEqual(economic.wallet_address, "Dtestwalletaddress1234567890")
            
            # Test that security configuration is correct
            security = config.security
            self.assertTrue(security.rate_limiting_enabled)
            self.assertIn("127.0.0.1", security.allowed_ips)
            
            # Test that monitoring configuration is correct
            monitoring = config.monitoring
            self.assertTrue(monitoring.enabled)
            self.assertEqual(monitoring.metrics_port, 8080)
            
            # Test that logging configuration is correct
            logging_config = config.logging
            self.assertEqual(logging_config.level.value, "DEBUG")
            self.assertEqual(logging_config.file_path, f"{self.test_dir}/test_mining.log")
        
        asyncio.run(run_test())
    
    def test_error_handling_and_recovery(self):
        """Test error handling and recovery mechanisms"""
        async def run_test():
            # Load configuration
            config = await self.config_manager.load_config()
            
            # Test security manager error handling
            security_manager = SecurityManager(config.security)
            await security_manager.start()
            
            # Test handling of invalid IP
            is_allowed = security_manager.is_request_allowed("999.999.999.999")
            self.assertFalse(is_allowed)  # Invalid IP should be blocked
            
            # Test input validation
            is_valid_worker = security_manager.validate_worker_name("test<worker>")  # Invalid chars
            self.assertFalse(is_valid_worker)
            
            # Test system monitor error handling
            system_monitor = SystemMonitor({
                "collection_interval": 5,
                "health_check_interval": 60
            })
            
            # Test recording various events
            system_monitor.record_share_accepted()
            system_monitor.record_share_rejected("invalid share")
            system_monitor.record_hardware_error()
            
            # Verify stats are recorded correctly
            stats = system_monitor.get_share_stats()
            self.assertEqual(stats["accepted"], 1)
            self.assertEqual(stats["rejected"], 1)
            self.assertEqual(stats["hardware_errors"], 1)
            
            # Test alert manager with error conditions
            logger = StructuredLogger("error_test", f"{self.test_dir}/error_test.log")
            alert_manager = AlertManager(logger)
            
            # Test alerting on high rejected shares rate
            alert_manager.check_and_alert("rejected_shares_rate", 0.10)  # 10% - above threshold
            
            # Verify alerts were generated
            alerts = alert_manager.get_recent_alerts()
            self.assertGreater(len(alerts), 0)
            
            # Clean up
            await security_manager.stop()
        
        asyncio.run(run_test())


class TestProductionReadiness(unittest.TestCase):
    """Test production readiness aspects"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.test_dir = tempfile.mkdtemp()
        
        # Production-like configuration
        self.prod_config_dict = {
            "environment": "production",
            "mining": {
                "algorithm": "scrypt",
                "threads": "auto",
                "intensity": "auto"
            },
            "pools": [
                {
                    "url": "stratum+tcp://doge.zsolo.bid:8057",
                    "username": "Dproductionwallet1234567890",
                    "password=os.getenv("POOL_PASSWORD", "x")"POOL_PASSWORD", "x")",
                    "algorithm": "scrypt",
                    "priority": 1,
                    "timeout": 30,
                    "retry_attempts": 3,
                    "enable_tls": False
                },
                {
                    "url": "stratum+tcp://backup.pool.com:3333",
                    "username": "Dproductionwallet1234567890",
                    "password=os.getenv("POOL_PASSWORD", "x")"POOL_PASSWORD", "x")",
                    "algorithm": "scrypt",
                    "priority": 2,
                    "timeout": 30,
                    "retry_attempts": 3,
                    "enable_tls": False
                }
            ],
            "hardware": {
                "type": "asic",
                "device_ids": [],
                "temperature_limit": 80
            },
            "economic": {
                "enabled": True,
                "max_power_cost": 0.12,
                "min_profitability": 0.01,
                "shutdown_on_unprofitable": True,
                "profitability_check_interval": 300,
                "wallet_address": "Dproductionwallet1234567890",
                "auto_withdrawal_threshold": 0.01
            },
            "security": {
                "enable_encryption": True,
                "rate_limiting_enabled": True,
                "max_requests_per_minute": 60,
                "enable_ddos_protection": True,
                "tls_verify": True,
                "allowed_ips": ["127.0.0.1"]
            },
            "monitoring": {
                "enabled": True,
                "metrics_port": 8080,
                "health_check_port": 8081,
                "enable_prometheus": True,
                "log_performance_metrics": True
            },
            "performance": {
                "auto_tune_enabled": True,
                "benchmark_interval": 3600
            },
            "logging": {
                "level": "WARNING",
                "file_path": f"{self.test_dir}/production_mining.log",
                "max_file_size": 10485760,
                "backup_count": 5,
                "enable_structured_logging": True,
                "enable_console": True
            }
        }
        
        self.config_file = os.path.join(self.test_dir, "prod_config.yaml")
        import yaml
        with open(self.config_file, 'w') as f:
            yaml.dump(self.prod_config_dict, f)
        
        self.config_manager = ConfigManager(self.config_file)
    
    def tearDown(self):
        """Clean up test fixtures"""
        import shutil
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)
    
    @patch('network.stratum_client.asyncio.open_connection')
    def test_production_configuration(self, mock_open_connection):
        """Test production configuration and readiness"""
        # Mock successful connection
        mock_reader = AsyncMock()
        mock_writer = AsyncMock()
        mock_open_connection.return_value = (mock_reader, mock_writer)
        
        async def run_test():
            # Load production configuration
            config = await self.config_manager.load_config()
            
            # Verify production settings
            self.assertEqual(config.environment.value, "production")
            self.assertEqual(config.logging.level.value, "WARNING")  # Less verbose in production
            self.assertTrue(config.economic.shutdown_on_unprofitable)  # Safety feature enabled
            self.assertTrue(config.security.enable_ddos_protection)  # Security enabled
            self.assertTrue(config.monitoring.enable_prometheus)  # Monitoring enabled
            
            # Test multiple pool configuration
            self.assertEqual(len(config.pools), 2)
            self.assertEqual(config.pools[0].priority, 1)  # Primary pool
            self.assertEqual(config.pools[1].priority, 2)  # Backup pool
            
            # Test system initialization with production config
            system_service = MiningSystemService(self.config_manager)
            init_success = await system_service.initialize()
            self.assertTrue(init_success)
            
            # Verify all production components are initialized
            self.assertIsNotNone(system_service.mining_service)
            self.assertIsNotNone(system_service.security_manager)
            self.assertIsNotNone(system_service.system_monitor)
            self.assertIsNotNone(system_service.pool_manager)
            
            # Test security in production mode
            self.assertTrue(system_service.security_manager.config.enable_encryption)
            self.assertTrue(system_service.security_manager.config.rate_limiting_enabled)
            
            # Test economic guardian in production
            self.assertTrue(system_service.economic_guardian.config.shutdown_on_unprofitable)
            
            # Test monitoring in production
            self.assertTrue(system_service.system_monitor.config.get("enable_prometheus"))
            
        asyncio.run(run_test())
    
    def test_failover_mechanisms(self):
        """Test failover and redundancy mechanisms"""
        async def run_test():
            # Load configuration
            config = await self.config_manager.load_config()
            
            # Test pool manager with multiple pools
            from network.pool_manager import PoolFailoverManager
            
            pool_configs = [pool.__dict__ for pool in config.pools]
            pool_manager = PoolFailoverManager(pool_configs)
            
            # Verify pool configuration
            pools = pool_manager.pools
            self.assertEqual(len(pools), 2)
            self.assertEqual(pools[0].priority, 1)  # Primary
            self.assertEqual(pools[1].priority, 2)  # Backup
            
            # Test pool recommendation logic
            recommended = pool_manager.get_recommended_pools()
            self.assertEqual(len(recommended), 2)
            
            # Test pool statistics tracking
            stats = pool_manager.get_pool_statistics()
            self.assertIsInstance(stats, dict)
            self.assertIn("pools", stats)
            self.assertEqual(len(stats["pools"]), 2)
        
        asyncio.run(run_test())


if __name__ == '__main__':
    # Configure logging for tests
    logging.basicConfig(level=logging.DEBUG)
    unittest.main()
"""
Comprehensive tests for the refactored Scrypt DOGE mining system.
"""

import unittest
import asyncio
import logging
import os
import sys
from unittest.mock import Mock, patch, AsyncMock

# Add the refactored directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from core.main_service import MiningSystemService, ServiceManager
from core.config_manager import ConfigManager, Config, PoolConfig, EconomicConfig
from network.stratum_client import EnhancedStratumClient
from security.security_manager import SecurityManager
from monitoring.system_monitor import SystemMonitor
from hardware.asic_emulator import ASICHardwareEmulator
from utils.logger import StructuredLogger, AlertManager


class TestComprehensiveSystem(unittest.TestCase):
    """Comprehensive tests for the complete mining system"""
    
    def setUp(self):
        """Set up test fixtures"""
        # Create a minimal configuration for testing
        self.test_config_dict = {
            "environment": "testing",
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
                "rate_limiting_enabled": False,
                "enable_ddos_protection": False,
                "tls_verify": True,
                "allowed_ips": ["127.0.0.1"]
            },
            "monitoring": {
                "enabled": True,
                "metrics_port": 8080,
                "health_check_port": 8081,
                "enable_prometheus": False,
                "log_performance_metrics": True
            }
        }
        
        # Create temporary config file for testing
        self.config_file = "test_config.yaml"
        import yaml
        with open(self.config_file, 'w') as f:
            yaml.dump(self.test_config_dict, f)
        
        self.config_manager = ConfigManager(self.config_file)
    
    def tearDown(self):
        """Clean up test fixtures"""
        if os.path.exists(self.config_file):
            os.remove(self.config_file)
    
    async def async_setUp(self):
        """Async setup for async tests"""
        self.config = await self.config_manager.load_config()
    
    @patch('network.stratum_client.asyncio.open_connection')
    def test_complete_system_initialization(self, mock_open_connection):
        """Test complete system initialization"""
        # Mock successful connection
        mock_reader = AsyncMock()
        mock_writer = AsyncMock()
        mock_open_connection.return_value = (mock_reader, mock_writer)
        
        async def run_test():
            # Initialize system
            system_service = MiningSystemService(self.config_manager)
            success = await system_service.initialize()
            
            self.assertTrue(success)
            self.assertIsNotNone(system_service.mining_service)
            self.assertIsNotNone(system_service.security_manager)
            self.assertIsNotNone(system_service.system_monitor)
            self.assertIsNotNone(system_service.pool_manager)
        
        asyncio.run(run_test())
    
    def test_service_manager_lifecycle(self):
        """Test service manager lifecycle"""
        async def run_test():
            service_manager = ServiceManager(self.config_file)
            
            # Test that we can create the service manager
            self.assertIsNotNone(service_manager)
            self.assertIsNotNone(service_manager.config_manager)
        
        asyncio.run(run_test())
    
    def test_component_integration(self):
        """Test that all components integrate properly"""
        async def run_test():
            # Load config
            config = await self.config_manager.load_config()
            
            # Test security manager
            security_manager = SecurityManager(config.security)
            await security_manager.start()
            
            # Test that security features work
            self.assertTrue(security_manager.is_request_allowed("127.0.0.1"))
            
            # Test system monitor
            system_monitor = SystemMonitor({
                "collection_interval": 5,
                "health_check_interval": 60
            })
            
            # Test monitoring functions
            system_monitor.record_share_accepted()
            system_monitor.record_share_rejected("test reason")
            
            stats = system_monitor.get_share_stats()
            self.assertEqual(stats["accepted"], 1)
            self.assertEqual(stats["rejected"], 1)
            
            # Test ASIC emulator
            asic_emulator = ASICHardwareEmulator()
            initialized = asic_emulator.initialize()
            self.assertTrue(initialized)
            
            # Clean up
            await security_manager.stop()
        
        asyncio.run(run_test())
    
    @patch('network.stratum_client.asyncio.open_connection')
    def test_mining_workflow(self, mock_open_connection):
        """Test complete mining workflow"""
        # Mock successful connection
        mock_reader = AsyncMock()
        mock_writer = AsyncMock()
        mock_open_connection.return_value = (mock_reader, mock_writer)
        
        async def run_test():
            # Initialize system
            system_service = MiningSystemService(self.config_manager)
            success = await system_service.initialize()
            self.assertTrue(success)
            
            # Get system status
            status = system_service.get_status()
            self.assertIsInstance(status, dict)
            self.assertIn("components", status)
            
            # Verify components are present
            self.assertIn("mining", status["components"])
            self.assertIn("monitoring", status["components"])
            self.assertIn("security", status["components"])
        
        asyncio.run(run_test())


class TestLoggingAndAlerting(unittest.TestCase):
    """Test logging and alerting system"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.logger = StructuredLogger("test_logger", "test_logs/test.log")
        self.alert_manager = AlertManager(self.logger)
    
    def tearDown(self):
        """Clean up test fixtures"""
        # Remove test log file
        if os.path.exists("test_logs/test.log"):
            os.remove("test_logs/test.log")
        if os.path.exists("test_logs"):
            os.rmdir("test_logs")
    
    def test_structured_logging(self):
        """Test structured logging functionality"""
        # Test logging different types of events
        self.logger.info("test_event", {"key=os.getenv("API_KEY", "your_key_here")"API_KEY", "your_key_here")"}, "Test message")
        self.logger.warning("test_warning", {"warning_key=os.getenv("API_KEY", "your_key_here")"API_KEY", "your_key_here")"}, "Test warning")
        self.logger.error("test_error", {"error_key=os.getenv("API_KEY", "your_key_here")"API_KEY", "your_key_here")"}, "Test error")
        
        # Verify logger was created
        self.assertIsNotNone(self.logger)
        self.assertIsNotNone(self.logger.logger)
    
    def test_alerting_system(self):
        """Test alerting system functionality"""
        # Test sending alerts
        self.alert_manager.send_alert("TEST_ALERT", "This is a test alert")
        
        # Test checking metrics
        self.alert_manager.check_and_alert("rejected_shares_rate", 0.10)  # Above threshold
        self.alert_manager.check_and_alert("temperature", 85.0)  # Above threshold
        
        # Verify alerts were recorded
        alerts = self.alert_manager.get_recent_alerts()
        self.assertGreater(len(alerts), 0)
        
        # Check specific alert content
        alert_messages = [alert["message"] for alert in alerts]
        self.assertIn("This is a test alert", alert_messages)


class TestConfigurationIntegration(unittest.TestCase):
    """Test configuration integration across components"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.test_config_dict = {
            "environment": "testing",
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
            "economic": {
                "enabled": True,
                "max_power_cost": 0.12,
                "min_profitability": 0.01,
                "shutdown_on_unprofitable": False,
                "profitability_check_interval": 300,
                "wallet_address": "Dtestwalletaddress1234567890",
                "auto_withdrawal_threshold": 0.01
            }
        }
        
        self.config_file = "test_config.yaml"
        import yaml
        with open(self.config_file, 'w') as f:
            yaml.dump(self.test_config_dict, f)
    
    def tearDown(self):
        """Clean up test fixtures"""
        if os.path.exists(self.config_file):
            os.remove(self.config_file)
    
    def test_config_manager_integration(self):
        """Test configuration manager integration"""
        async def run_test():
            config_manager = ConfigManager(self.config_file)
            config = await config_manager.load_config()
            
            self.assertIsInstance(config, Config)
            self.assertEqual(len(config.pools), 1)
            self.assertIsInstance(config.pools[0], PoolConfig)
            self.assertIsInstance(config.economic, EconomicConfig)
            
            # Test pool configuration
            pool = config.pools[0]
            self.assertEqual(pool.url, "stratum+tcp://test.pool.com:3333")
            self.assertEqual(pool.username, "testuser")
            self.assertEqual(pool.algorithm, "scrypt")
            
            # Test economic configuration
            economic = config.economic
            self.assertEqual(economic.max_power_cost, 0.12)
            self.assertEqual(economic.wallet_address, "Dtestwalletaddress1234567890")
        
        asyncio.run(run_test())


class TestHardwareIntegration(unittest.TestCase):
    """Test hardware integration components"""
    
    def test_asic_emulator(self):
        """Test ASIC emulator functionality"""
        from hardware.asic_emulator import ASICHardwareEmulator
        
        # Test initialization
        asic_emulator = ASICHardwareEmulator()
        initialized = asic_emulator.initialize()
        self.assertTrue(initialized)
        
        # Test getting status
        status = asic_emulator.get_antminer_status()
        self.assertIsInstance(status, dict)
        self.assertIn("hashrate", status)
        self.assertIn("temperature", status)
        self.assertIn("power", status)
        
        # Test hardware operations
        result = asic_emulator.perform_hardware_operation("test_operation")
        self.assertTrue(result)


class TestSecurityComponents(unittest.TestCase):
    """Test security components"""
    
    def test_security_manager(self):
        """Test security manager functionality"""
        from security.security_manager import SecurityManager, SecurityConfig
        
        # Create security config
        config = SecurityConfig(
            enable_encryption=False,
            enable_rate_limiting=True,
            max_requests_per_minute=60,
            enable_ddos_protection=True,
            allowed_ips=["127.0.0.1"]
        )
        
        # Test security manager creation
        security_manager = SecurityManager(config)
        self.assertIsNotNone(security_manager)
        
        # Test IP allowance
        self.assertTrue(security_manager.is_request_allowed("127.0.0.1"))
        
        # Test input validation
        self.assertTrue(security_manager.validate_wallet_address("Dtestwalletaddress1234567890", "doge"))
        self.assertTrue(security_manager.validate_worker_name("test_worker"))
    
    def test_economic_guardian(self):
        """Test economic guardian functionality"""
        from security.economic_guardian import EconomicGuardian
        
        # Create economic config
        config = {
            "enabled": True,
            "max_power_cost": 0.12,
            "min_profitability": 0.01,
            "shutdown_on_unprofitable": False,
            "profitability_check_interval": 300
        }
        
        # Test economic guardian creation
        economic_guardian = EconomicGuardian(config)
        self.assertIsNotNone(economic_guardian)
        
        # Test profitability check (will use simulated data)
        summary = economic_guardian.get_profitability_summary()
        self.assertIsInstance(summary, dict)
        self.assertIn("status", summary)


class TestMonitoringSystem(unittest.TestCase):
    """Test monitoring system components"""
    
    def test_system_monitor(self):
        """Test system monitor functionality"""
        from monitoring.system_monitor import SystemMonitor
        
        # Create system monitor
        monitor = SystemMonitor({
            "collection_interval": 5,
            "health_check_interval": 60
        })
        
        self.assertIsNotNone(monitor)
        
        # Test recording events
        monitor.record_share_accepted()
        monitor.record_share_rejected("test reason")
        monitor.record_hardware_error()
        
        # Test getting stats
        share_stats = monitor.get_share_stats()
        self.assertEqual(share_stats["accepted"], 1)
        self.assertEqual(share_stats["rejected"], 1)
        self.assertEqual(share_stats["hardware_errors"], 1)
        
        # Test system info
        system_info = monitor.get_system_info()
        self.assertIsInstance(system_info, dict)
        self.assertIn("platform", system_info)
        self.assertIn("processor", system_info)


class TestNetworkComponents(unittest.TestCase):
    """Test network components"""
    
    @patch('network.stratum_client.asyncio.open_connection')
    def test_stratum_client(self, mock_open_connection):
        """Test stratum client functionality"""
        # Mock successful connection
        mock_reader = AsyncMock()
        mock_writer = AsyncMock()
        mock_open_connection.return_value = (mock_reader, mock_writer)
        
        async def run_test():
            from network.stratum_client import EnhancedStratumClient
            
            # Create stratum client
            client = EnhancedStratumClient(
                host="test.pool.com",
                port=3333,
                user="testuser",
                password=os.getenv("POOL_PASSWORD", "x")"POOL_PASSWORD", "x")"
            )
            
            # Test connection
            connected = client.connect()
            self.assertTrue(connected)
            
            # Test getting stats
            stats = client.get_stats()
            self.assertIsInstance(stats, dict)
            self.assertIn("connection", stats)
            self.assertIn("security", stats)
        
        asyncio.run(run_test())
    
    def test_pool_manager(self):
        """Test pool manager functionality"""
        from network.pool_manager import PoolFailoverManager
        
        # Create pool configurations
        pool_configs = [
            {
                "url": "stratum+tcp://pool1.com:3333",
                "username": "user1",
                "password=os.getenv("POOL_PASSWORD", "x")"POOL_PASSWORD", "x")",
                "algorithm": "scrypt",
                "priority": 1
            },
            {
                "url": "stratum+tcp://pool2.com:3333",
                "username": "user2",
                "password=os.getenv("POOL_PASSWORD", "x")"POOL_PASSWORD", "x")",
                "algorithm": "scrypt",
                "priority": 2
            }
        ]
        
        # Create pool manager
        pool_manager = PoolFailoverManager(pool_configs)
        self.assertIsNotNone(pool_manager)
        
        # Test getting pool statistics
        stats = pool_manager.get_pool_statistics()
        self.assertIsInstance(stats, dict)
        self.assertIn("pools", stats)


if __name__ == '__main__':
    # Configure logging for tests
    logging.basicConfig(level=logging.DEBUG)
    unittest.main()
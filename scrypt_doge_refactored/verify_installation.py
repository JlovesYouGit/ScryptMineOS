#!/usr/bin/env python3
"""
Verification script to ensure all components of the Scrypt DOGE mining system
are properly installed and working together.
"""

import sys
import os
import importlib.util
import subprocess
import logging
from pathlib import Path

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("verification")


def check_python_version():
    """Check Python version requirement"""
    logger.info("Checking Python version...")
    if sys.version_info < (3, 8):
        logger.error("Python 3.8 or higher is required")
        return False
    logger.info(f"Python version OK: {sys.version}")
    return True


def check_required_packages():
    """Check if all required packages are installed"""
    logger.info("Checking required packages...")
    
    required_packages = [
        "yaml",
        "aiohttp",
        "asyncio",
        "psutil",
        "cryptography",
        "prometheus_client",
        "dependency_injector"
    ]
    
    missing_packages = []
    
    for package in required_packages:
        try:
            importlib.import_module(package)
            logger.debug(f"Package {package} is available")
        except ImportError:
            missing_packages.append(package)
            logger.warning(f"Package {package} is missing")
    
    if missing_packages:
        logger.error(f"Missing packages: {missing_packages}")
        logger.info("Install missing packages with: pip install " + " ".join(missing_packages))
        return False
    
    logger.info("All required packages are available")
    return True


def check_project_structure():
    """Check if project structure is correct"""
    logger.info("Checking project structure...")
    
    # Get current directory
    current_dir = Path(__file__).parent
    
    # Required directories and files
    required_items = [
        "main.py",
        "core",
        "network",
        "security",
        "hardware",
        "monitoring",
        "optimization",
        "utils",
        "scripts",
        "tests",
        "config",
        "requirements.txt"
    ]
    
    missing_items = []
    
    for item in required_items:
        item_path = current_dir / item
        if not item_path.exists():
            missing_items.append(item)
            logger.warning(f"Missing item: {item}")
    
    if missing_items:
        logger.error(f"Missing project items: {missing_items}")
        return False
    
    logger.info("Project structure is correct")
    return True


def check_core_modules():
    """Check if core modules can be imported"""
    logger.info("Checking core modules...")
    
    core_modules = [
        "core.main_service",
        "core.config_manager",
        "network.stratum_client",
        "security.security_manager",
        "security.economic_guardian",
        "hardware.asic_emulator",
        "monitoring.system_monitor",
        "optimization.performance_optimizer",
        "utils.logger"
    ]
    
    failed_imports = []
    
    # Add project root to path
    project_root = Path(__file__).parent
    sys.path.insert(0, str(project_root))
    
    for module in core_modules:
        try:
            importlib.import_module(module)
            logger.debug(f"Module {module} imported successfully")
        except ImportError as e:
            failed_imports.append((module, str(e)))
            logger.error(f"Failed to import {module}: {e}")
    
    if failed_imports:
        logger.error("Some modules failed to import")
        return False
    
    logger.info("All core modules imported successfully")
    return True


def check_configuration_files():
    """Check if configuration files exist and are valid"""
    logger.info("Checking configuration files...")
    
    current_dir = Path(__file__).parent
    config_dir = current_dir / "config"
    
    if not config_dir.exists():
        logger.warning("Config directory not found")
        return True  # Not critical for verification
    
    # Check if we can load YAML files
    try:
        import yaml
        yaml_files = list(config_dir.glob("*.yaml")) + list(config_dir.glob("*.yml"))
        
        for yaml_file in yaml_files:
            try:
                with open(yaml_file, 'r') as f:
                    yaml.safe_load(f)
                logger.debug(f"Configuration file {yaml_file} is valid YAML")
            except Exception as e:
                logger.error(f"Configuration file {yaml_file} is invalid: {e}")
                return False
        
        logger.info("Configuration files are valid")
        return True
    except ImportError:
        logger.warning("PyYAML not available, skipping configuration validation")
        return True


def check_logging_system():
    """Check if logging system works"""
    logger.info("Checking logging system...")
    
    try:
        from utils.logger import StructuredLogger, AlertManager
        
        # Test structured logger
        test_logger = StructuredLogger("test_verification", "test_verification.log")
        test_logger.info("verification_test", {"test": "value"}, "Verification test message")
        
        # Test alert manager
        alert_manager = AlertManager(test_logger)
        alert_manager.send_alert("VERIFICATION_TEST", "This is a verification test alert")
        
        # Clean up test log file
        if os.path.exists("test_verification.log"):
            os.remove("test_verification.log")
        
        logger.info("Logging system works correctly")
        return True
    except Exception as e:
        logger.error(f"Logging system check failed: {e}")
        return False


def check_hardware_components():
    """Check if hardware components work"""
    logger.info("Checking hardware components...")
    
    try:
        from hardware.asic_emulator import ASICHardwareEmulator
        
        # Test ASIC emulator
        asic_emulator = ASICHardwareEmulator()
        initialized = asic_emulator.initialize()
        
        if not initialized:
            logger.warning("ASIC emulator failed to initialize")
            return False
        
        status = asic_emulator.get_antminer_status()
        if not isinstance(status, dict):
            logger.error("ASIC emulator returned invalid status")
            return False
        
        logger.info("Hardware components work correctly")
        return True
    except Exception as e:
        logger.error(f"Hardware components check failed: {e}")
        return False


def check_security_components():
    """Check if security components work"""
    logger.info("Checking security components...")
    
    try:
        from security.security_manager import SecurityManager, SecurityConfig
        
        # Test security manager
        config = SecurityConfig(
            enable_encryption=False,  # Disable for testing
            enable_rate_limiting=True,
            max_requests_per_minute=60,
            enable_ddos_protection=True,
            allowed_ips=["127.0.0.1"]
        )
        
        security_manager = SecurityManager(config)
        
        # Test IP allowance
        is_allowed = security_manager.is_request_allowed("127.0.0.1")
        if not is_allowed:
            logger.error("Security manager failed IP allowance test")
            return False
        
        # Test input validation with a valid Dogecoin address format
        # Using a test address format that should pass validation
        is_valid = security_manager.validate_wallet_address("DQkiL71K3j6Ju2wKQ3nV1nKzD4b5J7Q9w8", "doge")
        if not is_valid:
            logger.error("Security manager failed wallet validation test")
            return False
        
        # Test worker name validation
        is_valid_worker = security_manager.validate_worker_name("test_worker")
        if not is_valid_worker:
            logger.error("Security manager failed worker name validation test")
            return False
        
        logger.info("Security components work correctly")
        return True
    except Exception as e:
        logger.error(f"Security components check failed: {e}")
        return False


def check_network_components():
    """Check if network components can be imported"""
    logger.info("Checking network components...")
    
    try:
        from network.stratum_client import EnhancedStratumClient
        from network.pool_manager import PoolFailoverManager
        
        # Test basic instantiation
        client = EnhancedStratumClient("test.pool.com", 3333, "testuser", "x")
        logger.debug("Stratum client instantiated successfully")
        
        # Test pool manager
        pool_configs = [
            {
                "url": "stratum+tcp://pool1.com:3333",
                "username": "user1",
                "password": "pass1",
                "algorithm": "scrypt",
                "priority": 1
            }
        ]
        pool_manager = PoolFailoverManager(pool_configs)
        logger.debug("Pool manager instantiated successfully")
        
        logger.info("Network components work correctly")
        return True
    except Exception as e:
        logger.error(f"Network components check failed: {e}")
        return False


def check_monitoring_components():
    """Check if monitoring components work"""
    logger.info("Checking monitoring components...")
    
    try:
        from monitoring.system_monitor import SystemMonitor
        
        # Test system monitor
        monitor = SystemMonitor({
            "collection_interval": 5,
            "health_check_interval": 60
        })
        
        # Test recording events
        monitor.record_share_accepted()
        monitor.record_share_rejected("test reason")
        
        # Test getting stats
        stats = monitor.get_share_stats()
        if not isinstance(stats, dict):
            logger.error("System monitor returned invalid stats")
            return False
        
        logger.info("Monitoring components work correctly")
        return True
    except Exception as e:
        logger.error(f"Monitoring components check failed: {e}")
        return False


def check_performance_components():
    """Check if performance optimization components work"""
    logger.info("Checking performance optimization components...")
    
    try:
        from optimization.performance_optimizer import GPUPerformanceOptimizer
        
        # Test performance optimizer
        optimizer = GPUPerformanceOptimizer()
        
        # Test baseline measurement
        baseline = optimizer.measure_baseline()
        if not hasattr(baseline, 'hashrate_mhs'):
            logger.error("Performance optimizer returned invalid baseline")
            return False
        
        logger.info("Performance optimization components work correctly")
        return True
    except Exception as e:
        logger.error(f"Performance optimization components check failed: {e}")
        return False


def run_comprehensive_test():
    """Run a comprehensive test of the system"""
    logger.info("Running comprehensive system test...")
    
    try:
        # Add project root to path
        project_root = Path(__file__).parent
        sys.path.insert(0, str(project_root))
        
        from core.config_manager import ConfigManager
        from core.main_service import MiningSystemService
        
        # Create a minimal test configuration
        test_config = {
            "environment": "testing",
            "pools": [
                {
                    "url": "stratum+tcp://test.pool.com:3333",
                    "username": "testuser",
                    "password": "x",
                    "algorithm": "scrypt",
                    "priority": 1
                }
            ],
            "economic": {
                "enabled": False,
                "wallet_address": "DQkiL71K3j6Ju2wKQ3nV1nKzD4b5J7Q9w8"
            },
            "security": {
                "enable_encryption": False,
                "rate_limiting_enabled": False,
                "enable_ddos_protection": False
            }
        }
        
        # Create temporary config file
        import tempfile
        import yaml
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            yaml.dump(test_config, f)
            config_file = f.name
        
        try:
            # Test configuration manager
            config_manager = ConfigManager(config_file)
            
            # Test system service initialization
            system_service = MiningSystemService(config_manager)
            
            logger.info("Comprehensive system test completed successfully")
            return True
        finally:
            # Clean up temporary file
            os.unlink(config_file)
            
    except Exception as e:
        logger.error(f"Comprehensive system test failed: {e}")
        return False


def main():
    """Main verification function"""
    logger.info("Starting Scrypt DOGE Mining System Verification")
    logger.info("=" * 50)
    
    # Run all checks
    checks = [
        ("Python Version", check_python_version),
        ("Required Packages", check_required_packages),
        ("Project Structure", check_project_structure),
        ("Core Modules", check_core_modules),
        ("Configuration Files", check_configuration_files),
        ("Logging System", check_logging_system),
        ("Hardware Components", check_hardware_components),
        ("Security Components", check_security_components),
        ("Network Components", check_network_components),
        ("Monitoring Components", check_monitoring_components),
        ("Performance Components", check_performance_components),
        ("Comprehensive Test", run_comprehensive_test)
    ]
    
    results = []
    
    for check_name, check_function in checks:
        try:
            logger.info(f"\nRunning check: {check_name}")
            result = check_function()
            results.append((check_name, result))
            
            if result:
                logger.info(f"✓ {check_name} - PASSED")
            else:
                logger.error(f"✗ {check_name} - FAILED")
        except Exception as e:
            logger.error(f"✗ {check_name} - ERROR: {e}")
            results.append((check_name, False))
    
    # Summary
    logger.info("\n" + "=" * 50)
    logger.info("VERIFICATION SUMMARY")
    logger.info("=" * 50)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for check_name, result in results:
        status = "PASSED" if result else "FAILED"
        logger.info(f"{check_name}: {status}")
    
    logger.info(f"\nOverall Result: {passed}/{total} checks passed")
    
    if passed == total:
        logger.info("🎉 All checks passed! System is ready for use.")
        return 0
    else:
        logger.error("❌ Some checks failed. Please review the errors above.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
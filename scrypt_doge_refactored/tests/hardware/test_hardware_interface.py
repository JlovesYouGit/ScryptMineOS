#!/usr/bin/env python3
"""
Unit tests for the hardware interface
"""

import unittest
import asyncio
import logging
from unittest.mock import Mock, patch, AsyncMock
import sys
import os

# Add the refactored directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

from hardware.asic_interface import (
    HardwareInterface, ASICInterface, GPUInterface, HardwareManager,
    HardwareInfo, HardwareStats, HardwareConfig, HardwareType, HardwareStatus
)

class TestHardwareInterface(unittest.TestCase):
    """Test cases for HardwareInterface base class"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.config = HardwareConfig()
        self.hardware_interface = HardwareInterface("test_device", self.config)
    
    def test_initialization(self):
        """Test HardwareInterface initialization"""
        self.assertIsInstance(self.hardware_interface, HardwareInterface)
        self.assertEqual(self.hardware_interface.device_id, "test_device")
        self.assertEqual(self.hardware_interface.config, self.config)
        self.assertEqual(self.hardware_interface.status, HardwareStatus.OFFLINE)
        self.assertEqual(len(self.hardware_interface.callbacks), 3)  # status_change, stats_update, error
    
    def test_add_callback(self):
        """Test adding callbacks"""
        def test_callback():
            pass
        
        self.hardware_interface.add_callback('status_change', test_callback)
        self.assertIn(test_callback, self.hardware_interface.callbacks['status_change'])
    
    def test_trigger_callback(self):
        """Test triggering callbacks"""
        triggered = False
        def test_callback(arg1, arg2):
            nonlocal triggered
            self.assertEqual(arg1, "test_arg1")
            self.assertEqual(arg2, "test_arg2")
            triggered = True
        
        self.hardware_interface.add_callback('status_change', test_callback)
        self.hardware_interface._trigger_callback('status_change', "test_arg1", "test_arg2")
        self.assertTrue(triggered)

class TestASICInterface(unittest.TestCase):
    """Test cases for ASICInterface"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.config = HardwareConfig()
        self.asic_interface = ASICInterface("asic_001", "192.168.1.100", self.config)
    
    def test_initialization(self):
        """Test ASICInterface initialization"""
        self.assertIsInstance(self.asic_interface, ASICInterface)
        self.assertEqual(self.asic_interface.device_id, "asic_001")
        self.assertEqual(self.asic_interface.ip_address, "192.168.1.100")
        self.assertEqual(self.asic_interface.config, self.config)
        self.assertIsNone(self.asic_interface.miner)
        self.assertIsNone(self.asic_interface._last_stats)
    
    @patch('hardware.asic_interface.pyasic')
    def test_connect_success(self, mock_pyasic):
        """Test successful connection to ASIC"""
        # Mock pyasic availability
        mock_pyasic.get_miner = AsyncMock(return_value=Mock())
        
        # Run async test
        result = asyncio.run(self.asic_interface.connect())
        
        self.assertTrue(result)
        self.assertEqual(self.asic_interface.status, HardwareStatus.IDLE)
        mock_pyasic.get_miner.assert_called_once_with("192.168.1.100")
    
    @patch('hardware.asic_interface.pyasic')
    def test_connect_failure(self, mock_pyasic):
        """Test failed connection to ASIC"""
        # Mock pyasic unavailability
        mock_pyasic.get_miner = AsyncMock(return_value=None)
        
        # Run async test
        result = asyncio.run(self.asic_interface.connect())
        
        self.assertFalse(result)
        self.assertEqual(self.asic_interface.status, HardwareStatus.ERROR)
    
    def test_disconnect(self):
        """Test disconnection from ASIC"""
        # Set up a mock miner
        self.asic_interface.miner = Mock()
        
        # Run async test
        asyncio.run(self.asic_interface.disconnect())
        
        self.assertIsNone(self.asic_interface.miner)
        self.assertEqual(self.asic_interface.status, HardwareStatus.OFFLINE)
    
    def test_get_stats_no_miner(self):
        """Test getting stats when no miner is connected"""
        stats = asyncio.run(self.asic_interface.get_stats())
        self.assertIsInstance(stats, HardwareStats)
        self.assertEqual(stats.hashrate, 0.0)
        self.assertEqual(stats.temperature, 0.0)
        self.assertEqual(stats.power_consumption, 0.0)
        self.assertEqual(stats.fan_speed, 0)
        self.assertEqual(stats.uptime, 0)
    
    def test_get_info_no_miner(self):
        """Test getting info when no miner is connected"""
        info = asyncio.run(self.asic_interface.get_info())
        self.assertIsInstance(info, HardwareInfo)
        self.assertEqual(info.device_id, "asic_001")
        self.assertEqual(info.model, "Unknown")
        self.assertEqual(info.manufacturer, "Unknown")
        self.assertEqual(info.firmware_version, "Unknown")

class TestGPUInterface(unittest.TestCase):
    """Test cases for GPUInterface"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.config = HardwareConfig()
        self.gpu_interface = GPUInterface("gpu_001", 0, self.config)
    
    def test_initialization(self):
        """Test GPUInterface initialization"""
        self.assertIsInstance(self.gpu_interface, GPUInterface)
        self.assertEqual(self.gpu_interface.device_id, "gpu_001")
        self.assertEqual(self.gpu_interface.device_index, 0)
        self.assertEqual(self.gpu_interface.config, self.config)
    
    def test_connect(self):
        """Test connection to GPU"""
        # Run async test
        result = asyncio.run(self.gpu_interface.connect())
        
        self.assertFalse(result)  # Not implemented yet
        self.assertEqual(self.gpu_interface.status, HardwareStatus.ERROR)
    
    def test_disconnect(self):
        """Test disconnection from GPU"""
        # Run async test
        asyncio.run(self.gpu_interface.disconnect())
        
        self.assertEqual(self.gpu_interface.status, HardwareStatus.OFFLINE)
    
    def test_get_stats(self):
        """Test getting GPU stats"""
        stats = asyncio.run(self.gpu_interface.get_stats())
        self.assertIsInstance(stats, HardwareStats)
        self.assertEqual(stats.hashrate, 0.0)
        self.assertEqual(stats.temperature, 0.0)
        self.assertEqual(stats.power_consumption, 0.0)
        self.assertEqual(stats.fan_speed, 0)
        self.assertEqual(stats.uptime, 0)
    
    def test_get_info(self):
        """Test getting GPU info"""
        info = asyncio.run(self.gpu_interface.get_info())
        self.assertIsInstance(info, HardwareInfo)
        self.assertEqual(info.device_id, "gpu_001")
        self.assertEqual(info.model, "GPU Not Implemented")
        self.assertEqual(info.manufacturer, "Unknown")
        self.assertEqual(info.firmware_version, "Unknown")

class TestHardwareManager(unittest.TestCase):
    """Test cases for HardwareManager"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.hardware_manager = HardwareManager()
    
    def test_initialization(self):
        """Test HardwareManager initialization"""
        self.assertIsInstance(self.hardware_manager, HardwareManager)
        self.assertEqual(len(self.hardware_manager.devices), 0)
        self.assertIsNone(self.hardware_manager.monitoring_task)
        self.assertFalse(self.hardware_manager.running)
    
    def test_add_device(self):
        """Test adding a device"""
        config = HardwareConfig()
        device = HardwareInterface("test_device", config)
        
        self.hardware_manager.add_device(device)
        self.assertIn("test_device", self.hardware_manager.devices)
        self.assertEqual(self.hardware_manager.devices["test_device"], device)
    
    def test_remove_device(self):
        """Test removing a device"""
        config = HardwareConfig()
        device = HardwareInterface("test_device", config)
        
        self.hardware_manager.add_device(device)
        self.assertIn("test_device", self.hardware_manager.devices)
        
        self.hardware_manager.remove_device("test_device")
        self.assertNotIn("test_device", self.hardware_manager.devices)
    
    def test_get_total_hashrate_no_devices(self):
        """Test getting total hashrate with no devices"""
        hashrate = asyncio.run(self.hardware_manager.get_total_hashrate())
        self.assertEqual(hashrate, 0.0)

class TestHardwareDataclasses(unittest.TestCase):
    """Test cases for hardware dataclasses"""
    
    def test_hardware_info(self):
        """Test HardwareInfo dataclass"""
        info = HardwareInfo(
            device_id="test_001",
            model="TestModel",
            manufacturer="TestManufacturer",
            firmware_version="1.0.0",
            ip_address="192.168.1.100",
            mac_address="00:11:22:33:44:55",
            serial_number="SN123456789"
        )
        
        self.assertEqual(info.device_id, "test_001")
        self.assertEqual(info.model, "TestModel")
        self.assertEqual(info.manufacturer, "TestManufacturer")
        self.assertEqual(info.firmware_version, "1.0.0")
        self.assertEqual(info.ip_address, "192.168.1.100")
        self.assertEqual(info.mac_address, "00:11:22:33:44:55")
        self.assertEqual(info.serial_number, "SN123456789")
    
    def test_hardware_stats(self):
        """Test HardwareStats dataclass"""
        stats = HardwareStats(
            hashrate=10.5,
            temperature=75.3,
            power_consumption=1500.0,
            fan_speed=3000,
            uptime=3600,
            accepted_shares=100,
            rejected_shares=5,
            hardware_errors=2
        )
        
        self.assertEqual(stats.hashrate, 10.5)
        self.assertEqual(stats.temperature, 75.3)
        self.assertEqual(stats.power_consumption, 1500.0)
        self.assertEqual(stats.fan_speed, 3000)
        self.assertEqual(stats.uptime, 3600)
        self.assertEqual(stats.accepted_shares, 100)
        self.assertEqual(stats.rejected_shares, 5)
        self.assertEqual(stats.hardware_errors, 2)
    
    def test_hardware_config(self):
        """Test HardwareConfig dataclass"""
        config = HardwareConfig(
            power_limit=1500,
            frequency=500,
            voltage=12.5,
            fan_speed=80,
            temperature_limit=85
        )
        
        self.assertEqual(config.power_limit, 1500)
        self.assertEqual(config.frequency, 500)
        self.assertEqual(config.voltage, 12.5)
        self.assertEqual(config.fan_speed, 80)
        self.assertEqual(config.temperature_limit, 85)

if __name__ == '__main__':
    # Configure logging for tests
    logging.basicConfig(level=logging.DEBUG)
    unittest.main()
"""
ASIC Hardware Interface for the refactored Scrypt DOGE mining system.
Real hardware integration using pyasic and custom protocols.
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass
from enum import Enum
import time
import json

try:
    import pyasic
    PYASIC_AVAILABLE = True
except ImportError:
    PYASIC_AVAILABLE = False
    pyasic = None

logger = logging.getLogger(__name__)


class HardwareType(str, Enum):
    """Supported hardware types"""
    ASIC = "asic"
    GPU = "gpu"
    CPU = "cpu"


class HardwareStatus(Enum):
    """Hardware status states"""
    OFFLINE = "offline"
    IDLE = "idle"
    MINING = "mining"
    ERROR = "error"
    OVERHEATED = "overheated"
    UNKNOWN = "unknown"


@dataclass
class HardwareInfo:
    """Hardware device information"""
    device_id: str
    model: str
    manufacturer: str
    firmware_version: str
    ip_address: Optional[str] = None
    mac_address: Optional[str] = None
    serial_number: Optional[str] = None


@dataclass
class HardwareStats:
    """Hardware performance statistics"""
    hashrate: float  # GH/s
    temperature: float  # Celsius
    power_consumption: float  # Watts
    fan_speed: int  # RPM
    uptime: int  # seconds
    accepted_shares: int = 0
    rejected_shares: int = 0
    hardware_errors: int = 0


@dataclass
class HardwareConfig:
    """Hardware configuration settings"""
    power_limit: Optional[int] = None  # Watts
    frequency: Optional[int] = None  # MHz
    voltage: Optional[float] = None  # Volts
    fan_speed: Optional[int] = None  # Percentage or RPM
    temperature_limit: int = 80  # Celsius


class HardwareInterface:
    """Base interface for mining hardware"""
    
    def __init__(self, device_id: str, config: HardwareConfig):
        self.device_id = device_id
        self.config = config
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}.{device_id}")
        self.status = HardwareStatus.OFFLINE
        self.callbacks: Dict[str, List[Callable]] = {
            'status_change': [],
            'stats_update': [],
            'error': []
        }
    
    async def connect(self) -> bool:
        """Connect to hardware device"""
        raise NotImplementedError
    
    async def disconnect(self) -> None:
        """Disconnect from hardware device"""
        raise NotImplementedError
    
    async def start_mining(self, pool_url: str, username: str, password=os.getenv("POOL_PASSWORD", "x")"POOL_PASSWORD", "x") -> bool:
        """Start mining on specified pool"""
        raise NotImplementedError
    
    async def stop_mining(self) -> bool:
        """Stop mining"""
        raise NotImplementedError
    
    async def get_stats(self) -> HardwareStats:
        """Get current hardware statistics"""
        raise NotImplementedError
    
    async def get_info(self) -> HardwareInfo:
        """Get hardware information"""
        raise NotImplementedError
    
    async def apply_config(self, config: HardwareConfig) -> bool:
        """Apply new configuration"""
        raise NotImplementedError
    
    def add_callback(self, event: str, callback: Callable) -> None:
        """Add event callback"""
        if event in self.callbacks:
            self.callbacks[event].append(callback)
    
    def _trigger_callback(self, event: str, *args, **kwargs) -> None:
        """Trigger event callbacks"""
        for callback in self.callbacks.get(event, []):
            try:
                callback(*args, **kwargs)
            except Exception as e:
                self.logger.error(f"Callback error: {e}")


class ASICInterface(HardwareInterface):
    """ASIC hardware interface using pyasic"""
    
    def __init__(self, device_id: str, ip_address: str, config: HardwareConfig):
        super().__init__(device_id, config)
        self.ip_address = ip_address
        self.miner = None
        self._last_stats: Optional[HardwareStats] = None
        self._update_task: Optional[asyncio.Task] = None
        self._running = False
    
    async def connect(self) -> bool:
        """Connect to ASIC miner"""
        if not PYASIC_AVAILABLE:
            self.logger.error("pyasic library not available")
            return False
        
        try:
            self.logger.info(f"Connecting to ASIC at {self.ip_address}")
            self.miner = await pyasic.get_miner(self.ip_address)
            
            if self.miner:
                self.status = HardwareStatus.IDLE
                self._trigger_callback('status_change', self.status)
                self.logger.info(f"Connected to ASIC: {self.miner}")
                return True
            else:
                self.logger.error("Failed to get ASIC miner instance")
                return False
                
        except Exception as e:
            self.logger.error(f"Failed to connect to ASIC: {e}")
            self.status = HardwareStatus.ERROR
            self._trigger_callback('status_change', self.status)
            return False
    
    async def disconnect(self) -> None:
        """Disconnect from ASIC miner"""
        self._running = False
        if self._update_task:
            self._update_task.cancel()
            try:
                await self._update_task
            except asyncio.CancelledError:
                pass
        
        if self.miner:
            self.miner = None
        self.status = HardwareStatus.OFFLINE
        self._trigger_callback('status_change', self.status)
        self.logger.info("Disconnected from ASIC")
    
    async def start_mining(self, pool_url: str, username: str, password=os.getenv("POOL_PASSWORD", "x")"POOL_PASSWORD", "x") -> bool:
        """Start mining on ASIC"""
        if not self.miner or self.status != HardwareStatus.IDLE:
            return False
        
        try:
            self.logger.info(f"Starting ASIC mining on {pool_url}")
            
            # Configure pool settings
            pool_config = {
                'pool_1_url': pool_url,
                'pool_1_user': username,
                'pool_1_pass': password
            }
            
            # Apply pool configuration
            await self.miner.send_config(pool_config)
            
            # Start mining
            await self.miner.resume_mining()
            
            self.status = HardwareStatus.MINING
            self._trigger_callback('status_change', self.status)
            self.logger.info("ASIC mining started successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to start ASIC mining: {e}")
            return False
    
    async def stop_mining(self) -> bool:
        """Stop ASIC mining"""
        if not self.miner or self.status != HardwareStatus.MINING:
            return False
        
        try:
            self.logger.info("Stopping ASIC mining")
            await self.miner.stop_mining()
            
            self.status = HardwareStatus.IDLE
            self._trigger_callback('status_change', self.status)
            self.logger.info("ASIC mining stopped")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to stop ASIC mining: {e}")
            return False
    
    async def get_stats(self) -> HardwareStats:
        """Get ASIC statistics"""
        if not self.miner:
            return HardwareStats(0, 0, 0, 0, 0)
        
        try:
            data = await self.miner.get_data()
            
            stats = HardwareStats(
                hashrate=float(data.get('hashrate', 0)) / 1e9,  # Convert to GH/s
                temperature=float(data.get('temperature', 0)),
                power_consumption=float(data.get('wattage', 0)),
                fan_speed=int(data.get('fan_speed', 0)),
                uptime=int(data.get('uptime', 0)),
                accepted_shares=int(data.get('shares_accepted', 0)),
                rejected_shares=int(data.get('shares_rejected', 0)),
                hardware_errors=int(data.get('hardware_errors', 0))
            )
            
            self._last_stats = stats
            self._trigger_callback('stats_update', stats)
            
            # Check for overheating
            if stats.temperature > self.config.temperature_limit:
                if self.status == HardwareStatus.MINING:
                    self.status = HardwareStatus.OVERHEATED
                    self._trigger_callback('status_change', self.status)
                    self.logger.warning(f"ASIC overheating: {stats.temperature}°C")
            
            return stats
            
        except Exception as e:
            self.logger.error(f"Failed to get ASIC stats: {e}")
            return self._last_stats or HardwareStats(0, 0, 0, 0, 0)
    
    async def get_info(self) -> HardwareInfo:
        """Get ASIC information"""
        if not self.miner:
            return HardwareInfo(self.device_id, "Unknown", "Unknown", "Unknown")
        
        try:
            model = await self.miner.get_model()
            hostname = await self.miner.get_hostname()
            
            return HardwareInfo(
                device_id=self.device_id,
                model=str(model),
                manufacturer="Unknown",  # Would need to parse from model
                firmware_version="Unknown",  # Would need specific method
                ip_address=self.ip_address,
                hostname=hostname
            )
            
        except Exception as e:
            self.logger.error(f"Failed to get ASIC info: {e}")
            return HardwareInfo(self.device_id, "Unknown", "Unknown", "Unknown")
    
    async def apply_config(self, config: HardwareConfig) -> bool:
        """Apply new configuration to ASIC"""
        if not self.miner:
            return False
        
        try:
            self.logger.info("Applying new ASIC configuration")
            
            config_dict = {}
            
            if config.power_limit:
                config_dict['power_limit'] = config.power_limit
            
            if config.frequency:
                config_dict['frequency'] = config.frequency
            
            if config.voltage:
                config_dict['voltage'] = config.voltage
            
            if config.fan_speed:
                config_dict['fan_speed'] = config.fan_speed
            
            if config.temperature_limit:
                config_dict['temp_limit'] = config.temperature_limit
            
            if config_dict:
                await self.miner.send_config(config_dict)
                self.config = config
                self.logger.info("ASIC configuration applied successfully")
                return True
            
            return False
            
        except Exception as e:
            self.logger.error(f"Failed to apply ASIC configuration: {e}")
            return False


class GPUInterface(HardwareInterface):
    """GPU hardware interface (placeholder for GPU support)"""
    
    def __init__(self, device_id: str, device_index: int, config: HardwareConfig):
        super().__init__(device_id, config)
        self.device_index = device_index
    
    async def connect(self) -> bool:
        """Connect to GPU"""
        # This would integrate with GPU mining libraries like:
        # - ethminer for Ethereum
        # - nbminer for various algorithms
        # - lolminer for multiple coins
        
        self.logger.warning("GPU interface not yet implemented")
        self.status = HardwareStatus.ERROR
        return False
    
    async def disconnect(self) -> None:
        """Disconnect from GPU"""
        self.status = HardwareStatus.OFFLINE
    
    async def start_mining(self, pool_url: str, username: str, password=os.getenv("POOL_PASSWORD", "x")"POOL_PASSWORD", "x") -> bool:
        """Start GPU mining"""
        return False
    
    async def stop_mining(self) -> bool:
        """Stop GPU mining"""
        return False
    
    async def get_stats(self) -> HardwareStats:
        """Get GPU statistics"""
        return HardwareStats(0, 0, 0, 0, 0)
    
    async def get_info(self) -> HardwareInfo:
        """Get GPU information"""
        return HardwareInfo(
            device_id=self.device_id,
            model="GPU Not Implemented",
            manufacturer="Unknown",
            firmware_version="Unknown"
        )
    
    async def apply_config(self, config: HardwareConfig) -> bool:
        """Apply GPU configuration"""
        return False


class HardwareManager:
    """Manages multiple hardware devices"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.devices: Dict[str, HardwareInterface] = {}
        self.monitoring_task: Optional[asyncio.Task] = None
        self.running = False
    
    def add_device(self, device: HardwareInterface) -> None:
        """Add hardware device"""
        self.devices[device.device_id] = device
        self.logger.info(f"Added device: {device.device_id}")
    
    def remove_device(self, device_id: str) -> None:
        """Remove hardware device"""
        if device_id in self.devices:
            del self.devices[device_id]
            self.logger.info(f"Removed device: {device_id}")
    
    async def start_all(self) -> None:
        """Start all devices"""
        self.logger.info("Starting all hardware devices")
        
        for device in self.devices.values():
            try:
                await device.connect()
            except Exception as e:
                self.logger.error(f"Failed to start device {device.device_id}: {e}")
        
        # Start monitoring
        if not self.monitoring_task:
            self.running = True
            self.monitoring_task = asyncio.create_task(self._monitor_devices())
    
    async def stop_all(self) -> None:
        """Stop all devices"""
        self.logger.info("Stopping all hardware devices")
        
        self.running = False
        
        if self.monitoring_task:
            self.monitoring_task.cancel()
            try:
                await self.monitoring_task
            except asyncio.CancelledError:
                pass
            self.monitoring_task = None
        
        for device in self.devices.values():
            try:
                await device.disconnect()
            except Exception as e:
                self.logger.error(f"Error stopping device {device.device_id}: {e}")
    
    async def get_total_hashrate(self) -> float:
        """Get total hashrate from all devices"""
        total_hashrate = 0.0
        
        for device in self.devices.values():
            try:
                stats = await device.get_stats()
                total_hashrate += stats.hashrate
            except Exception as e:
                self.logger.error(f"Error getting stats for {device.device_id}: {e}")
        
        return total_hashrate
    
    async def _monitor_devices(self) -> None:
        """Monitor device status and performance"""
        while self.running:
            try:
                for device in self.devices.values():
                    # Update statistics
                    try:
                        await device.get_stats()
                    except Exception as e:
                        self.logger.error(f"Error updating stats for {device.device_id}: {e}")
                
                # Wait before next update
                await asyncio.sleep(30)  # Update every 30 seconds
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Error in device monitoring: {e}")
                await asyncio.sleep(5)
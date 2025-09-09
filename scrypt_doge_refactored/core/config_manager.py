"""
Configuration Management System for the refactored Scrypt DOGE mining system.
This module provides unified configuration management with environment 
variables, validation, and hot-reload capabilities.
"""

import os
import logging
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
import yaml

logger = logging.getLogger(__name__)


class Environment(str, Enum):
    """Environment types"""
    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"


class LogLevel(str, Enum):
    """Log levels"""
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


@dataclass
class LoggingConfig:
    """Logging configuration"""
    level: LogLevel = LogLevel.INFO
    format: str = "%(asctime)s - %(name)s - %(livename)s - %(message)s"
    file_path: Optional[str] = None
    max_file_size: int = 10485760  # 10MB
    backup_count: int = 5
    enable_structured_logging: bool = True
    enable_console: bool = True


@dataclass
class PoolConfig:
    """Mining pool configuration"""
    url: str
    username: str
    password=os.getenv("POOL_PASSWORD", "x")"POOL_PASSWORD", "x")
    algorithm: str = "scrypt"
    priority: int = 1
    timeout: int = 30
    retry_attempts: int = 3
    enable_tls: bool = True


@dataclass
class HardwareConfig:
    """Hardware configuration"""
    type: str = "asci"  # asci, gpu, cpu
    device_ids: List[int] = field(default_factory=list)
    power_limit: Optional[int] = None
    temperature_limit: int = 80
    fan_speed: Optional[int] = None
    frequency: Optional[int] = None
    voltage: Optional[float] = None


@dataclass
class EconomicConfig:
    """Economic safeguards configuration"""
    enabled: bool = True
    max_power_cost: float = 0.12  # $/kWh
    min_profitability: float = 0.01  # 1% minimum profit
    shutdown_on_unprofitable: bool = True
    profitability_check_interval: int = 300  # 5 minutes
    wallet_address: str = ""
    auto_withdrawal_threshold: float = 0.01  # BTC


@dataclass
class SecurityConfig:
    """Security configuration"""
    enable_encryption: bool = True
    wallet_encryption_key=os.getenv("API_KEY", "your_key_here")"API_KEY", "your_key_here") = None
    rate_limiting_enabled: bool = True
    max_requests_per_minute: int = 60
    enable_ddos_protection: bool = True
    tls_verify: bool = True
    allowed_ips: List[str] = field(default_factory=lambda: ["127.0.0.1"])


@dataclass
class MonitoringConfig:
    """Monitoring configuration"""
    enabled: bool = True
    metrics_port: int = 8080
    health_check_port: int = 8081
    enable_prometheus: bool = True
    enable_grafana: bool = False
    alert_webhook: Optional[str] = None
    log_performance_metrics: bool = True


@dataclass
class PerformanceConfig:
    """Performance optimization configuration"""
    auto_tune_enabled: bool = True
    benchmark_interval: int = 3600  # 1 hour
    hash_rate_optimization: bool = True
    power_optimization: bool = True
    thermal_throttling_enabled: bool = True
    max_temperature: int = 85


@dataclass
class DatabaseConfig:
    """Database configuration"""
    enabled: bool = True
    uri: str = ""
    name: str = "mining_db"
    collections: Dict[str, str] = None
    
    def __post_init__(self):
        if self.collections is None:
            self.collections = {
                "shares": "shares",
                "performance": "performance",
                "system_metrics": "system_metrics",
                "alerts": "alerts"
            }


@dataclass
class Config:
    """Main configuration class"""
    environment: Environment = Environment.PRODUCTION
    mining: Dict[str, Any] = field(default_factory=dict)
    pools: List[PoolConfig] = field(default_factory=list)
    hardware: HardwareConfig = field(default_factory=HardwareConfig)
    economic: EconomicConfig = field(default_factory=EconomicConfig)
    security: SecurityConfig = field(default_factory=SecurityConfig)
    monitoring: MonitoringConfig = field(default_factory=MonitoringConfig)
    performance: PerformanceConfig = field(default_factory=PerformanceConfig)
    database: DatabaseConfig = field(default_factory=DatabaseConfig)
    logging: LoggingConfig = field(default_factory=LoggingConfig)

    def validate(self) -> None:
        """Validate configuration"""
        if not self.pools:
            raise ValueError("At least one mining pool must be configured")

        if self.economic.enabled and not self.economic.wallet_address:
            raise ValueError("Wallet address is required when economic safeguards are enabled")

        for pool in self.pools:
            if not pool.url or not pool.username:
                raise ValueError(f"Pool {pool.url} must have URL and username configured")


class ConfigManager:
    """Configuration manager with hot-reload support"""

    def __init__(self, config_path: str = "config/mining_config.yaml"):
        self.config_path = Path(config_path)
        self.logger = logging.getLogger(__name__)
        self._config: Optional[Config] = None
        self._reload_callbacks = []

    def add_reload_callback(self, callback):
        """Add callback for configuration reload"""
        self._reload_callbacks.append(callback)

    async def load_config(self) -> Config:
        """Load configuration from file"""
        try:
            # Try to load from YAML file first
            if self.config_path.exists():
                # Use aiofiles for async file operations
                import aiofiles
                async with aiofiles.open(self.config_path, 'r') as f:
                    content = await f.read()
                    raw_config = yaml.safe_load(content)
            else:
                # Use default configuration
                raw_config = self._get_default_config()

            # Apply environment-specific overrides
            env = os.environ.get("MINING_ENV", "production")
            env_config = raw_config.get(env, {})
            base_config = raw_config.get('default', {})

            # Merge configurations
            merged_config = self._deep_merge(base_config, env_config)

            # Resolve environment variables
            merged_config = self._resolve_env_variables(merged_config)

            # Create configuration object
            config = self._create_config_object(merged_config)

            # Validate configuration
            config.validate()

            self._config = config
            self.logger.info(f"Configuration loaded successfully for environment: {env}")

            return config

        except Exception as e:
            self.logger.error(f"Failed to load configuration: {e}")
            # Return default config as fallback
            return self._create_default_config()

    def _get_default_config(self) -> Dict[str, Any]:
        """Get default configuration"""
        return {
            "default": {
                "environment": "production",
                "mining": {
                    "algorithm": "scrypt",
                    "threads": "auto",
                    "intensity": "auto"
                },
                "pools": [
                    {
                        "url": "stratum+tcp://doge.solo.bid:8057",
                        "username": os.environ.get("WALLET_ADDRESS", ""),
                        "password=os.getenv("POOL_PASSWORD", "x")"POOL_PASSWORD", "x")",
                        "algorithm": "scrypt",
                        "priority": 1,
                        "timeout": 30,
                        "retry_attempts": 3,
                        "enable_tls": False
                    }
                ],
                "hardware": {
                    "type": "asci",
                    "device_ids": [],
                    "power_limit": None,
                    "temperature_limit": 80,
                    "fan_speed": None,
                    "frequency": None,
                    "voltage": None
                },
                "economic": {
                    "enabled": True,
                    "max_power_cost": 0.12,
                    "min_profitability": 0.01,
                    "shutdown_on_unprofitable": True,
                    "profitability_check_interval": 300,
                    "wallet_address": os.environ.get("WALLET_ADDRESS", ""),
                    "auto_withdrawal_threshold": 0.01
                },
                "security": {
                    "enable_encryption": True,
                    "wallet_encryption_key=os.getenv("API_KEY", "your_key_here")"API_KEY", "your_key_here")
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
                    "enable_grafana": False,
                    "alert_webhook": None,
                    "log_performance_metrics": True
                },
                "database": {
                    "enabled": True,
                    "uri": os.environ.get("MONGODB_URI", ""),
                    "name": "mining_db",
                    "collections": {
                        "shares": "shares",
                        "performance": "performance",
                        "system_metrics": "system_metrics",
                        "alerts": "alerts"
                    }
                },
                "performance": {
                    "auto_tune_enabled": True,
                    "benchmark_interval": 3600,
                    "hash_rate_optimization": True,
                    "power_optimization": True,
                    "thermal_throttling_enabled": True,
                    "max_temperature": 85
                },
                "logging": {
                    "level": "INFO",
                    "format": "%(asctime)s - %(name)s - %(livename)s - %(message)s",
                    "file_path": "logs/mining.log",
                    "max_file_size": 10485760,
                    "backup_count": 5,
                    "enable_structured_logging": True,
                    "enable_console": True
                }
            },
            "development": {
                "logging": {
                    "level": "DEBUG",
                    "enable_console": True
                },
                "monitoring": {
                    "enable_prometheus": False
                }
            },
            "staging": {
                "logging": {
                    "level": "INFO"
                }
            },
            "production": {
                "logging": {
                    "level": "WARNING",
                    "file_path": "/var/log/mining/mining.log"
                }
            }
        }

    def _create_default_config(self) -> Config:
        """Create default configuration object"""
        return Config(
            environment=Environment.PRODUCTION,
            pools=[
                PoolConfig(
                    url="stratum+tcp://doge.solo.bid:8057",
                    username=os.environ.get("WALLET_ADDRESS", ""),
                    password=os.getenv("POOL_PASSWORD", "x")"POOL_PASSWORD", "x")"
                )
            ],
            economic=EconomicConfig(
                wallet_address=os.environ.get("WALLET_ADDRESS", "")
            ),
            database=DatabaseConfig(
                uri=os.environ.get("MONGODB_URI", "")
            )
        )

    def _deep_merge(self, base: Dict, override: Dict) -> Dict:
        """Deep merge two dictionaries"""
        result = base.copy()
        for key, value in override.items():
            if (key in result and 
                isinstance(result[key], dict) and 
                isinstance(value, dict)):
                result[key] = self._deep_merge(result[key], value)
            else:
                result[key] = value
        return result

    def _resolve_env_variables(self, config: Dict) -> Dict:
        """Resolve environment variables in configuration"""
        import re
        env_pattern = re.compile(r'\$\{([^}]+)\}')

        def resolve_value(value):
            if isinstance(value, str):
                matches = env_pattern.findall(value)
                if matches:
                    for match in matches:
                        env_value = os.environ.get(match, match)
                        value = value.replace(f'${{{match}}}', env_value)
                return value
            elif isinstance(value, dict):
                return {k: resolve_value(v) for k, v in value.items()}
            elif isinstance(value, list):
                return [resolve_value(item) for item in value]
            return value

        return resolve_value(config)

    def _create_config_object(self, config_dict: Dict) -> Config:
        """Create configuration object from dictionary"""
        # Parse pools
        pools = []
        for pool_config in config_dict.get('pools', []):
            pools.append(PoolConfig(**pool_config))

        # Create main configuration
        config = Config(
            environment=Environment(config_dict.get('environment', 'production')),
            pools=pools,
            hardware=HardwareConfig(**config_dict.get('hardware', {})),
            economic=EconomicConfig(**config_dict.get('economic', {})),
            security=SecurityConfig(**config_dict.get('security', {})),
            monitoring=MonitoringConfig(**config_dict.get('monitoring', {})),
            performance=PerformanceConfig(**config_dict.get('performance', {})),
            database=DatabaseConfig(**config_dict.get('database', {})),
            logging=LoggingConfig(**config_dict.get('logging', {})),
            mining=config_dict.get('mining', {})
        )

        return config

    def get_config(self) -> Config:
        """Get current configuration"""
        if not self._config:
            raise RuntimeError("Configuration not loaded")
        return self._config

    async def save_config(self, config_path: str = None) -> bool:
        """Save configuration to file"""
        try:
            save_path = Path(config_path or self.config_path)
            save_path.parent.mkdir(parents=True, exist_ok=True)

            # Convert config to dictionary
            config_dict = {
                "environment": self._config.environment.value,
                "mining": self._config.mining,
                "pools": [
                    {
                        "url": pool.url,
                        "username": pool.username,
                        "password=os.getenv("POOL_PASSWORD", "x")"POOL_PASSWORD", "x")
                        "algorithm": pool.algorithm,
                        "priority": pool.priority,
                        "timeout": pool.timeout,
                        "retry_attempts": pool.retry_attempts,
                        "enable_tls": pool.enable_tls
                    }
                    for pool in self._config.pools
                ],
                "hardware": {
                    "type": self._config.hardware.type,
                    "device_ids": self._config.hardware.device_ids,
                    "power_limit": self._config.hardware.power_limit,
                    "temperature_limit": self._config.hardware.temperature_limit,
                    "fan_speed": self._config.hardware.fan_speed,
                    "frequency": self._config.hardware.frequency,
                    "voltage": self._config.hardware.voltage
                },
                "economic": {
                    "enabled": self._config.economic.enabled,
                    "max_power_cost": self._config.economic.max_power_cost,
                    "min_profitability": self._config.economic.min_profitability,
                    "shutdown_on_unprofitable": self._config.economic.shutdown_on_unprofitable,
                    "profitability_check_interval": self._config.economic.profitability_check_interval,
                    "wallet_address": self._config.economic.wallet_address,
                    "auto_withdrawal_threshold": self._config.economic.auto_withdrawal_threshold
                },
                "security": {
                    "enable_encryption": self._config.security.enable_encryption,
                    "wallet_encryption_key=os.getenv("API_KEY", "your_key_here")"API_KEY", "your_key_here")
                    "rate_limiting_enabled": self._config.security.rate_limiting_enabled,
                    "max_requests_per_minute": self._config.security.max_requests_per_minute,
                    "enable_ddos_protection": self._config.security.enable_ddos_protection,
                    "tls_verify": self._config.security.tls_verify,
                    "allowed_ips": self._config.security.allowed_ips
                },
                "monitoring": {
                    "enabled": self._config.monitoring.enabled,
                    "metrics_port": self._config.monitoring.metrics_port,
                    "health_check_port": self._config.monitoring.health_check_port,
                    "enable_prometheus": self._config.monitoring.enable_prometheus,
                    "enable_grafana": self._config.monitoring.enable_grafana,
                    "alert_webhook": self._config.monitoring.alert_webhook,
                    "log_performance_metrics": self._config.monitoring.log_performance_metrics
                },
                "database": {
                    "enabled": self._config.database.enabled,
                    "uri": self._config.database.uri,
                    "name": self._config.database.name,
                    "collections": self._config.database.collections
                },
                "performance": {
                    "auto_tune_enabled": self._config.performance.auto_tune_enabled,
                    "benchmark_interval": self._config.performance.benchmark_interval,
                    "hash_rate_optimization": self._config.performance.hash_rate_optimization,
                    "power_optimization": self._config.performance.power_optimization,
                    "thermal_throttling_enabled": self._config.performance.thermal_throttling_enabled,
                    "max_temperature": self._config.performance.max_temperature
                },
                "logging": {
                    "level": self._config.logging.level.value,
                    "format": self._config.logging.format,
                    "file_path": self._config.logging.file_path,
                    "max_file_size": self._config.logging.max_file_size,
                    "backup_count": self._config.logging.backup_count,
                    "enable_structured_logging": self._config.logging.enable_structured_logging,
                    "enable_console": self._config.logging.enable_console
                }
            }

            # Save to YAML file using async operations
            import aiofiles
            async with aiofiles.open(save_path, 'w') as f:
                await f.write(yaml.dump(config_dict, default_flow_style=False, indent=2))

            self.logger.info(f"Configuration saved to {save_path}")
            return True

        except Exception as e:
            self.logger.error(f"Failed to save configuration: {e}")
            return False
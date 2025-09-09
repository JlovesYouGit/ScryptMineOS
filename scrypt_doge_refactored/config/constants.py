"""
Mining Constants Configuration Module
Centralized constants management for scrypt_doge cryptocurrency mining suite.

This module follows the Constants Definition Standard by centralizing all
magic numbers and configuration values used throughout the mining system.
"""

from dataclasses import dataclass
from enum import Enum

from decouple import config


class MiningMode(Enum):
    """Mining operation modes"""

    EDUCATIONAL = "educational"
    PRODUCTION = "production"
    TESTING = "testing"
    HYBRID = "hybrid"


class PoolRegion(Enum):
    """F2Pool regional endpoints"""

    GLOBAL = "f2pool_global"
    EU = "f2pool_eu"
    NA = "f2pool_na"
    ASIA = "f2pool_asia"


@dataclass(frozen=True)
class SystemConstants:
    """System-level constants for mining operations"""

    # Process Management
    MAX_RESTARTS: int = 3
    COMPILE_TIMEOUT: int = 300
    TERMINATION_TIMEOUT: int = 30
    STATUS_UPDATE_INTERVAL: int = 1

    # Restart Logic
    MIN_RESTART_WAIT: int = 5
    MAX_RESTART_WAIT: int = 30
    RESTART_BACKOFF_MULTIPLIER: int = 5

    # Line Length & Formatting
    LINE_LENGTH_LIMIT: int = 79
    INDENT_SIZE: int = 4

    # File Paths
    STATUS_FILE: str = "continuous_mining_status.json"
    LOG_FILE: str = "continuous_mining.log"
    PID_FILE: str = "continuous_mining.pid"


@dataclass(frozen=True)
class MiningConstants:
    """Mining-specific constants for ASIC operations"""

    # Performance Targets (Antminer L7)
    TARGET_HASHRATE_GHS: float = 9.5
    TARGET_POWER_WATTS: int = 3350
    TARGET_EFFICIENCY_JTH: float = 0.36

    # Operational Thresholds
    MAX_REJECT_RATE_PERCENT: float = 0.3
    MIN_ACCEPT_RATE_PERCENT: float = 99.7
    MAX_NONCE_ERROR_RATE: float = 0.01

    # Thermal Management
    OPTIMAL_TEMP_CELSIUS: int = 75
    MAX_TEMP_CELSIUS: int = 85
    AMBIENT_TEMP_LIMIT: int = 28

    # Economic Safeguards
    MIN_HASH_PER_WATT: int = 2_000_000  # 2 MH/s per watt
    MAX_DAILY_LOSS_USD: float = 10.0
    MIN_PROFITABLE_HASHRATE: int = 100_000_000  # 100 MH/s


@dataclass(frozen=True)
class NetworkConstants:
    """Network and pool connection constants"""

    # Stratum Protocol
    STRATUM_V1_PORT: int = 3335
    STRATUM_SSL_PORT: int = 5201
    CONNECTION_TIMEOUT: int = 30
    SOCKET_TIMEOUT: int = 60

    # Pool Configuration
    WORKER_NAME_MAX_LENGTH: int = 32
    DIFFICULTY_TARGET: int = 1
    EXTRANONCE_SIZE: int = 4

    # Monitoring
    PROMETHEUS_PORT: int = 9100
    METRICS_UPDATE_INTERVAL: int = 30
    API_POLL_INTERVAL: int = 30


@dataclass(frozen=True)
class AlgorithmConstants:
    """Scrypt algorithm-specific constants"""

    # Scrypt Parameters
    N: int = 1024
    R: int = 1
    P: int = 1

    # OpenCL Configuration
    WORK_GROUP_SIZE: int = 256
    GLOBAL_WORK_SIZE: int = 65536
    LOCAL_WORK_SIZE: int = 256

    # Memory Requirements
    SCRATCHPAD_SIZE: int = 32768  # 32KB per core
    PIPELINE_DEPTH: int = 64
    MEMORY_PER_CORE: int = 32768


# Standard mining arguments array
STANDARD_MINING_ARGS: list[str] = [
    "--educational",
    "--optimize-performance",
    "--hardware-emulation",
    "--use-l2-kernel",
    "--voltage-tuning",
    "--clock-gating",
]

# Important log keywords for filtering
IMPORTANT_LOG_KEYWORDS: list[str] = [
    "share",
    "hash",
    "error",
    "success",
    "failed",
    "optimization",
    "emulation",
    "complete",
    "mining",
    "accept",
    "reject",
    "difficulty",
    "stratum",
]

# F2Pool endpoints configuration
F2POOL_ENDPOINTS: dict[str, dict[str, str]] = {
    "global": {"host": "ltc.f2pool.com", "port": "3335", "ssl_port": "5201"},
    "eu": {"host": "ltc-eu.f2pool.com", "port": "3335", "ssl_port": "5201"},
    "na": {"host": "ltc-na.f2pool.com", "port": "3335", "ssl_port": "5201"},
    "asia": {
        "host": "ltc-asia.f2pool.com",
        "port": "3335",
        "ssl_port": "5201",
    },
}

# Environment variable defaults (can be overridden via .env)
LTC_ADDRESS = config("LTC_ADDRESS", default="")
DOGE_ADDRESS = config("DOGE_ADDRESS", default="")
WORKER_NAME = config("WORKER_NAME", default="rig01")
ELECTRICITY_COST_KWH = config("ELECTRICITY_COST_KWH", default=0.08, cast=float)
POOL_REGION = config("POOL_REGION", default="global", cast=str)

# Create singleton instances
SYSTEM = SystemConstants()
MINING = MiningConstants()
NETWORK = NetworkConstants()
ALGORITHM = AlgorithmConstants()
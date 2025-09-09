"""
ScryptMineOS - Advanced ASIC Mining Simulation Platform

A comprehensive mining simulation environment designed for educational purposes,
research, and development testing. This platform provides realistic mining
scenarios without the need for actual hardware or energy consumption.

Copyright (C) 2024 ScryptMineOS Development Team
Licensed under GNU General Public License v3.0
"""

__version__ = "2.1.0"
__author__ = "ScryptMineOS Development Team"
__email__ = "dev@scryptmineos.org"
__license__ = "GPL-3.0"
__url__ = "https://github.com/JlovesYouGit/ScryptMineOS"

# Core simulation components (placeholder imports)
# These would be implemented in the actual codebase
try:
    from .simulator import Simulator
    from .asic import ASICProfile, CustomASIC
    from .pool import PoolConnector
    from .analytics import PerformanceAnalyzer
    from .security import SecurityManager
except ImportError:
    # Graceful handling when modules are not yet implemented
    pass

# Version information
VERSION_INFO = {
    "version": __version__,
    "author": __author__,
    "license": __license__,
    "url": __url__,
    "description": "Advanced ASIC Mining Simulation Platform"
}

def get_version():
    """Get the current version of ScryptMineOS."""
    return __version__

def get_info():
    """Get comprehensive information about ScryptMineOS."""
    return VERSION_INFO.copy()

# Module-level constants
DEFAULT_CONFIG = {
    "simulation": {
        "duration": "1h",
        "precision": "high",
        "real_time": False
    },
    "security": {
        "sandbox": True,
        "audit_logging": True,
        "strict_mode": False
    },
    "networking": {
        "timeout": 30,
        "retry_attempts": 3,
        "use_tls": True
    }
}

# Supported ASIC models (for documentation purposes)
SUPPORTED_ASICS = [
    "Antminer L3+",
    "Antminer L7", 
    "Innosilicon A6+",
    "Goldshell Mini-DOGE",
    "FusionSilicon X6",
    "Custom ASIC Profiles"
]

# Supported mining algorithms
SUPPORTED_ALGORITHMS = [
    "scrypt",
    "sha256",
    "x11",
    "custom"
]

__all__ = [
    "__version__",
    "__author__", 
    "__license__",
    "__url__",
    "get_version",
    "get_info",
    "DEFAULT_CONFIG",
    "SUPPORTED_ASICS",
    "SUPPORTED_ALGORITHMS",
    "VERSION_INFO"
]

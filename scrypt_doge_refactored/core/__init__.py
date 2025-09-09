"""
Core module for the refactored Scrypt DOGE mining system.
"""

from .database_manager import DatabaseManager, DatabaseConfig
from .models import ShareData, PerformanceMetric, SystemMetric, AlertData

__all__ = [
    "DatabaseManager",
    "DatabaseConfig",
    "ShareData",
    "PerformanceMetric",
    "SystemMetric",
    "AlertData"
]
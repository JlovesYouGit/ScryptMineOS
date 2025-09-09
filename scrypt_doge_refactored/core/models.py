"""
Data models for the Scrypt DOGE mining system.
Defines data structures for storing mining statistics in MongoDB.
"""

import logging
from typing import Optional, Dict, Any
from dataclasses import dataclass, asdict
from datetime import datetime

logger = logging.getLogger(__name__)


@dataclass
class ShareData:
    """Data model for share submissions"""
    job_id: str
    extranonce2: str
    ntime: str
    nonce: str
    hash_result: str
    worker_name: str
    difficulty: float
    accepted: bool
    reason: Optional[str] = None
    timestamp: Optional[datetime] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for MongoDB storage"""
        return asdict(self)


@dataclass
class PerformanceMetric:
    """Data model for performance metrics"""
    hashrate: float
    accepted_shares: int
    rejected_shares: int
    hardware_errors: int
    uptime_seconds: float
    worker_name: str
    timestamp: Optional[datetime] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for MongoDB storage"""
        return asdict(self)


@dataclass
class SystemMetric:
    """Data model for system metrics"""
    cpu_percent: float
    memory_percent: float
    disk_usage_percent: float
    network_bytes_sent: int
    network_bytes_recv: int
    worker_name: str
    timestamp: Optional[datetime] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for MongoDB storage"""
        return asdict(self)


@dataclass
class AlertData:
    """Data model for alerts"""
    alert_type: str
    message: str
    severity: str  # info, warning, error, critical
    worker_name: str
    resolved: bool = False
    resolution_message: Optional[str] = None
    timestamp: Optional[datetime] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for MongoDB storage"""
        return asdict(self)


@dataclass
class ConnectionStat:
    """Data model for connection statistics"""
    connection_attempts: int
    successful_connections: int
    disconnections: int
    uptime_percentage: float
    worker_name: str
    timestamp: Optional[datetime] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for MongoDB storage"""
        return asdict(self)
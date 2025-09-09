#!/usr/bin/env python3
"""
Stratum Monitoring and Logging Module
Comprehensive monitoring and logging for Stratum client operations

This implementation provides:
- Detailed logging for all Stratum operations
- Performance metrics collection
- Connection health monitoring
- Share submission tracking
- Alerting for critical issues
"""

import logging
import time
import json
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from collections import deque
import threading

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("stratum_monitoring")

@dataclass
class ShareStats:
    """Statistics for share submissions"""
    accepted: int = 0
    rejected: int = 0
    last_accepted_time: Optional[float] = None
    last_rejected_time: Optional[float] = None
    recent_shares: deque = field(default_factory=lambda: deque(maxlen=100))
    
    def add_accepted(self):
        """Add an accepted share"""
        self.accepted += 1
        self.last_accepted_time = time.time()
        self.recent_shares.append(('accepted', time.time()))
    
    def add_rejected(self, reason: str = ""):
        """Add a rejected share"""
        self.rejected += 1
        self.last_rejected_time = time.time()
        self.recent_shares.append(('rejected', time.time(), reason))
    
    def acceptance_rate(self) -> float:
        """Calculate acceptance rate"""
        total = self.accepted + self.rejected
        return self.accepted / total if total > 0 else 0.0
    
    def recent_acceptance_rate(self, window_minutes: int = 10) -> float:
        """Calculate acceptance rate for recent shares"""
        cutoff_time = time.time() - (window_minutes * 60)
        recent = [share for share in self.recent_shares if share[1] > cutoff_time]
        if not recent:
            return 0.0
        
        accepted = sum(1 for share in recent if share[0] == 'accepted')
        return accepted / len(recent)

@dataclass
class ConnectionStats:
    """Statistics for connection health"""
    connection_attempts: int = 0
    successful_connections: int = 0
    disconnections: int = 0
    last_connect_time: Optional[float] = None
    last_disconnect_time: Optional[float] = None
    uptime_seconds: float = 0.0
    downtime_seconds: float = 0.0
    connection_start_time: Optional[float] = None
    
    def on_connect(self):
        """Record successful connection"""
        self.successful_connections += 1
        self.last_connect_time = time.time()
        self.connection_start_time = time.time()
        if self.last_disconnect_time:
            self.downtime_seconds += time.time() - self.last_disconnect_time
    
    def on_disconnect(self):
        """Record disconnection"""
        self.disconnections += 1
        self.last_disconnect_time = time.time()
        if self.connection_start_time:
            self.uptime_seconds += time.time() - self.connection_start_time
            self.connection_start_time = None
    
    def uptime_percentage(self) -> float:
        """Calculate uptime percentage"""
        total_time = self.uptime_seconds + self.downtime_seconds
        return (self.uptime_seconds / total_time * 100) if total_time > 0 else 0.0

@dataclass
class PerformanceMetrics:
    """Performance metrics for mining operations"""
    hashes_per_second: float = 0.0
    last_hash_time: Optional[float] = None
    hash_intervals: deque = field(default_factory=lambda: deque(maxlen=1000))
    jobs_received: int = 0
    last_job_time: Optional[float] = None
    
    def record_hash(self):
        """Record a hash computation"""
        current_time = time.time()
        if self.last_hash_time:
            interval = current_time - self.last_hash_time
            self.hash_intervals.append(interval)
            if len(self.hash_intervals) >= 2:
                # Calculate hashes per second based on recent intervals
                avg_interval = sum(self.hash_intervals) / len(self.hash_intervals)
                self.hashes_per_second = 1.0 / avg_interval if avg_interval > 0 else 0.0
        self.last_hash_time = current_time
    
    def record_job(self):
        """Record job receipt"""
        self.jobs_received += 1
        self.last_job_time = time.time()
    
    def average_hash_rate(self) -> float:
        """Get average hash rate"""
        if not self.hash_intervals:
            return 0.0
        avg_interval = sum(self.hash_intervals) / len(self.hash_intervals)
        return 1.0 / avg_interval if avg_interval > 0 else 0.0

class StratumMonitor:
    """Main monitoring class for Stratum operations"""
    
    def __init__(self, worker_name: str = "unknown"):
        self.worker_name = worker_name
        self.share_stats = ShareStats()
        self.connection_stats = ConnectionStats()
        self.performance_metrics = PerformanceMetrics()
        self.alerts: List[Dict[str, Any]] = []
        self.start_time = time.time()
        
        # Start monitoring thread
        self.monitoring_thread = threading.Thread(target=self._monitoring_loop, daemon=True)
        self.monitoring_thread.start()
        
        logger.info(f"StratumMonitor initialized for worker: {worker_name}")
    
    def record_share_accepted(self):
        """Record an accepted share"""
        self.share_stats.add_accepted()
        logger.info(f"Share accepted. Total accepted: {self.share_stats.accepted}")
    
    def record_share_rejected(self, reason: str = ""):
        """Record a rejected share"""
        self.share_stats.add_rejected(reason)
        logger.warning(f"Share rejected: {reason}. Total rejected: {self.share_stats.rejected}")
        
        # Check for alert conditions
        if self.share_stats.recent_acceptance_rate() < 0.8:  # Less than 80% recent acceptance
            self._add_alert("LOW_ACCEPTANCE_RATE", f"Recent acceptance rate below 80%: {self.share_stats.recent_acceptance_rate():.2%}")
    
    def record_connection_attempt(self):
        """Record a connection attempt"""
        self.connection_stats.connection_attempts += 1
        logger.info(f"Connection attempt #{self.connection_stats.connection_attempts}")
    
    def record_connection_success(self):
        """Record successful connection"""
        self.connection_stats.on_connect()
        logger.info("Connection successful")
    
    def record_disconnection(self):
        """Record disconnection"""
        self.connection_stats.on_disconnect()
        logger.info("Disconnected from pool")
        
        # Check for alert conditions
        if self.connection_stats.uptime_percentage() < 95:  # Less than 95% uptime
            self._add_alert("LOW_UPTIME", f"Uptime below 95%: {self.connection_stats.uptime_percentage():.2f}%")
    
    def record_hash_computation(self):
        """Record hash computation"""
        self.performance_metrics.record_hash()
    
    def record_job_received(self):
        """Record job receipt"""
        self.performance_metrics.record_job()
        logger.debug(f"Job received. Total jobs: {self.performance_metrics.jobs_received}")
    
    def record_difficulty_change(self, old_diff: float, new_diff: float):
        """Record difficulty change"""
        logger.info(f"Difficulty changed from {old_diff} to {new_diff}")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get comprehensive statistics"""
        uptime_pct = self.connection_stats.uptime_percentage()
        acceptance_rate = self.share_stats.acceptance_rate()
        recent_acceptance_rate = self.share_stats.recent_acceptance_rate()
        avg_hash_rate = self.performance_metrics.average_hash_rate()
        runtime = time.time() - self.start_time
        
        return {
            "worker_name": self.worker_name,
            "runtime_seconds": runtime,
            "shares": {
                "accepted": self.share_stats.accepted,
                "rejected": self.share_stats.rejected,
                "acceptance_rate": acceptance_rate,
                "recent_acceptance_rate": recent_acceptance_rate,
                "last_accepted": self.share_stats.last_accepted_time,
                "last_rejected": self.share_stats.last_rejected_time
            },
            "connection": {
                "attempts": self.connection_stats.connection_attempts,
                "successful": self.connection_stats.successful_connections,
                "disconnections": self.connection_stats.disconnections,
                "uptime_percentage": uptime_pct,
                "uptime_seconds": self.connection_stats.uptime_seconds,
                "downtime_seconds": self.connection_stats.downtime_seconds
            },
            "performance": {
                "hashes_per_second": avg_hash_rate,
                "jobs_received": self.performance_metrics.jobs_received,
                "last_job_time": self.performance_metrics.last_job_time
            },
            "alerts": len(self.alerts)
        }
    
    def get_alerts(self) -> List[Dict[str, Any]]:
        """Get current alerts"""
        return self.alerts.copy()
    
    def clear_alerts(self):
        """Clear all alerts"""
        self.alerts.clear()
    
    def _add_alert(self, alert_type: str, message: str):
        """Add an alert"""
        alert = {
            "type": alert_type,
            "message": message,
            "timestamp": time.time(),
            "worker_name": self.worker_name
        }
        self.alerts.append(alert)
        logger.warning(f"ALERT [{alert_type}]: {message}")
    
    def _monitoring_loop(self):
        """Background monitoring loop"""
        while True:
            try:
                # Periodic health checks
                self._check_health()
                time.sleep(60)  # Check every minute
            except Exception as e:
                logger.error(f"Error in monitoring loop: {e}")
                time.sleep(60)
    
    def _check_health(self):
        """Perform health checks"""
        # Check for stale jobs
        if (self.performance_metrics.last_job_time and 
            time.time() - self.performance_metrics.last_job_time > 300):  # 5 minutes
            self._add_alert("STALE_JOBS", "No jobs received in last 5 minutes")
        
        # Check for low hashrate
        if self.performance_metrics.average_hash_rate() < 1000:  # Less than 1 KH/s
            self._add_alert("LOW_HASHRATE", f"Low hashrate: {self.performance_metrics.average_hash_rate():.2f} H/s")
        
        # Log periodic stats
        stats = self.get_stats()
        logger.info(f"Periodic Stats - Uptime: {stats['connection']['uptime_percentage']:.2f}%, "
                   f"Acceptance: {stats['shares']['acceptance_rate']:.2%}, "
                   f"Hashrate: {stats['performance']['hashes_per_second']:.2f} H/s")

class JsonLogger:
    """JSON logging utility for structured logging"""
    
    def __init__(self, log_file: str = "stratum_log.json"):
        self.log_file = log_file
    
    def log_event(self, event_type: str, data: Dict[str, Any]):
        """Log an event in JSON format"""
        log_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "event_type": event_type,
            "data": data
        }
        
        try:
            with open(self.log_file, "a") as f:
                f.write(json.dumps(log_entry) + "\n")
        except Exception as e:
            logger.error(f"Failed to write JSON log: {e}")

# Example usage
if __name__ == "__main__":
    # Create monitor
    monitor = StratumMonitor("test_worker")
    
    # Simulate some operations
    monitor.record_connection_attempt()
    monitor.record_connection_success()
    
    # Simulate shares
    monitor.record_share_accepted()
    monitor.record_share_accepted()
    monitor.record_share_rejected("Low difficulty")
    
    # Simulate hashing
    for _ in range(100):
        monitor.record_hash_computation()
        time.sleep(0.01)  # Simulate 10ms per hash
    
    # Simulate jobs
    monitor.record_job_received()
    time.sleep(1)
    monitor.record_job_received()
    
    # Print stats
    stats = monitor.get_stats()
    print("Stratum Monitor Stats:")
    print(json.dumps(stats, indent=2, default=str))
    
    # Print alerts
    alerts = monitor.get_alerts()
    if alerts:
        print("\nAlerts:")
        for alert in alerts:
            print(f"  {alert['type']}: {alert['message']}")
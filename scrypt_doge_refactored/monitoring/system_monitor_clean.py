"""
System Monitoring Infrastructure for the refactored Scrypt DOGE mining system.
Comprehensive logging, metrics collection, and health checking.
"""

import logging
import json
import time
import asyncio
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field
from datetime import datetime
from collections import deque
import psutil
import platform

# Assuming the database manager will be in the same package
try:
    from core.database_manager import DatabaseManager
    from core.models import ShareData, PerformanceMetric, SystemMetric
except ImportError:
    # Mock classes for type hints if database module is not available
    class DatabaseManager:
        pass

logger = logging.getLogger(__name__)


@dataclass
class SystemMetrics:
    """System-level metrics"""
    cpu_percent: float = 0.0
    memory_percent: float = 0.0
    disk_usage_percent: float = 0.0
    network_bytes_sent: int = 0
    network_bytes_recv: int = 0
    timestamp: float = field(default_factory=time.time)


@dataclass
class MiningMetrics:
    """Mining-specific metrics"""
    hashrate: float = 0.0  # H/s
    accepted_shares: int = 0
    rejected_shares: int = 0
    hardware_errors: int = 0
    uptime_seconds: float = 0.0
    timestamp: float = field(default_factory=time.time)


@dataclass
class HealthStatus:
    """Overall system health status"""
    status: str = "unknown"  # healthy, warning, critical
    message: str = ""
    timestamp: float = field(default_factory=time.time)
    checks: Dict[str, bool] = field(default_factory=dict)


class MetricsCollector:
    """Collects and stores system metrics"""

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.logger = logging.getLogger(__name__)
        self.system_metrics_history: deque = deque(maxlen=1000)
        self.mining_metrics_history: deque = deque(maxlen=1000)
        self.last_net_io: Optional[psutil._common.netio] = None
        self.start_time = time.time()

        # Start metrics collection
        self.collecting = False
        self.collection_task: Optional[asyncio.Task] = None

    async def start_collection(self) -> None:
        """Start metrics collection"""
        if self.collecting:
            self.logger.warning("Metrics collection already running")
            return

        self.collecting = True
        self.collection_task = asyncio.create_task(self._collection_loop())
        self.logger.info("Metrics collection started")

    async def stop_collection(self) -> None:
        """Stop metrics collection"""
        self.collecting = False
        if self.collection_task:
            self.collection_task.cancel()
            try:
                await self.collection_task
            except asyncio.CancelledError:
                pass
        self.logger.info("Metrics collection stopped")

    async def _collection_loop(self) -> None:
        """Main metrics collection loop"""
        while self.collecting:
            try:
                # Collect system metrics
                system_metrics = self._collect_system_metrics()
                self.system_metrics_history.append(system_metrics)

                # Wait before next collection
                await asyncio.sleep(self.config.get('collection_interval', 5))

            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Error in metrics collection: {e}")
                await asyncio.sleep(5)

    def _collect_system_metrics(self) -> SystemMetrics:
        """Collect system-level metrics"""
        try:
            # CPU usage
            cpu_percent = psutil.cpu_percent(interval=1)

            # Memory usage
            memory = psutil.virtual_memory()
            memory_percent = memory.percent

            # Disk usage
            disk = psutil.disk_usage('/')
            disk_usage_percent = (disk.used / disk.total) * 100

            # Network I/O
            net_io = psutil.net_io_counters()
            bytes_sent = net_io.bytes_sent
            bytes_recv = net_io.bytes_recv

            # Store current net_io for next calculation
            self.last_net_io = net_io

            return SystemMetrics(
                cpu_percent=cpu_percent,
                memory_percent=memory_percent,
                disk_usage_percent=disk_usage_percent,
                network_bytes_sent=bytes_sent,
                network_bytes_recv=bytes_recv
            )

        except Exception as e:
            self.logger.error(f"Error collecting system metrics: {e}")
            return SystemMetrics()

    def get_recent_system_metrics(self, count: int = 10) -> List[SystemMetrics]:
        """Get recent system metrics"""
        return list(self.system_metrics_history)[-count:]

    def get_system_stats(self) -> Dict[str, Any]:
        """Get current system statistics"""
        if self.system_metrics_history:
            latest = self.system_metrics_history[-1]
            return {
                "cpu_percent": latest.cpu_percent,
                "memory_percent": latest.memory_percent,
                "disk_usage_percent": latest.disk_usage_percent,
                "network_bytes_sent": latest.network_bytes_sent,
                "network_bytes_recv": latest.network_bytes_recv,
                "timestamp": latest.timestamp
            }
        return {}


class SystemMonitor:
    """Main system monitoring class"""

    def __init__(self, config: Dict[str, Any] = None, 
                 database_manager: Optional[DatabaseManager] = None):
        self.config = config or {}
        self.database_manager = database_manager
        self.logger = logging.getLogger(__name__)

        # Metrics tracking
        self.metrics_collector = MetricsCollector(self.config)
        self.share_stats = {
            'accepted': 0,
            'rejected': 0,
            'hardware_errors': 0,
            'last_accepted_time': None,
            'last_rejected_time': None
        }

        # Health checks
        self.health_checks = {
            'system_resources': self._check_system_resources,
            'disk_space': self._check_disk_space,
            'network_connectivity': self._check_network_connectivity,
            'mining_process': self._check_mining_process
        }

        # Start monitoring
        self.monitoring = False
        self.monitoring_task: Optional[asyncio.Task] = None
        self.start_time = time.time()

    async def start_monitoring(self) -> None:
        """Start system monitoring"""
        if self.monitoring:
            self.logger.warning("System monitoring already running")
            return

        self.monitoring = True
        await self.metrics_collector.start_collection()
        self.monitoring_task = asyncio.create_task(self._monitoring_loop())
        self.logger.info("System monitoring started")

    async def stop_monitoring(self) -> None:
        """Stop system monitoring"""
        self.monitoring = False
        await self.metrics_collector.stop_collection()

        if self.monitoring_task:
            self.monitoring_task.cancel()
            try:
                await self.monitoring_task
            except asyncio.CancelledError:
                pass
        self.logger.info("System monitoring stopped")

    async def _monitoring_loop(self) -> None:
        """Main monitoring loop"""
        while self.monitoring:
            try:
                # Perform health checks periodically
                await asyncio.sleep(self.config.get('health_check_interval', 60))

            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Error in monitoring loop: {e}")
                await asyncio.sleep(5)

    def record_share_accepted(self, job_id: str = "",
                              worker_name: str = "unknown") -> None:
        """Record an accepted share"""
        self.share_stats['accepted'] += 1
        self.share_stats['last_accepted_time'] = time.time()
        self.logger.debug(f"Share accepted. Total: {self.share_stats['accepted']}")

        # Store in database if available
        if self.database_manager and self.database_manager.connected:
            share_data = ShareData(
                job_id=job_id,
                entrance2="",
                ntile="",
                nonce="",
                hash_result="",
                worker_name=worker_name,
                difficulty=1.0,
                accepted=True
            )
            self.database_manager.store_share(share_data.to_dict())

    def record_share_rejected(self, reason: str = "", job_id: str = "",
                              worker_name: str = "unknown") -> None:
        """Record a rejected share"""
        self.share_stats['rejected'] += 1
        self.share_stats['last_rejected_time'] = time.time()
        self.logger.debug(f"Share rejected: {reason}. Total: {self.share_stats['rejected']}")

        # Store in database if available
        if self.database_manager and self.database_manager.connected:
            share_data = ShareData(
                job_id=job_id,
                entrance2="",
                ntile="",
                nonce="",
                hash_result="",
                worker_name=worker_name,
                difficulty=1.0,
                accepted=False,
                reason=reason
            )
            self.database_manager.store_share(share_data.to_dict())

    def record_hardware_error(self, worker_name: str = "unknown") -> None:
        """Record a hardware error"""
        self.share_stats['hardware_errors'] += 1
        self.logger.warning(f"Hardware error recorded. Total: {self.share_stats['hardware_errors']}")

        # Store alert in database if available
        if self.database_manager and self.database_manager.connected:
            alert_data = {
                "alert_type": "hardware_error",
                "message": f"Hardware error recorded. Total: {self.share_stats['hardware_errors']}",
                "severity": "warning",
                "worker_name": worker_name
            }
            self.database_manager.store_alert(alert_data)

    def record_job_received(self, worker_name: str = "unknown") -> None:
        """Record job receipt"""
        self.logger.debug("Job received")

        # Store system metrics in database if available
        if self.database_manager and self.database_manager.connected:
            system_stats = self.metrics_collector.get_system_stats()
            if system_stats:
                system_metric = SystemMetric(
                    cpu_percent=system_stats.get("cpu_percent", 0.0),
                    memory_percent=system_stats.get("memory_percent", 0.0),
                    disk_usage_percent=system_stats.get("disk_usage_percent", 0.0),
                    network_bytes_sent=system_stats.get("network_bytes_sent", 0),
                    network_bytes_recv=system_stats.get("network_bytes_recv", 0),
                    worker_name=worker_name
                )
                self.database_manager.store_system_metric(system_metric.to_dict())

    def record_hash_computation(self, worker_name: str = "unknown") -> None:
        """Record hash computation"""
        self.logger.debug("Hash computation recorded")

        # Store performance metrics in database if available
        if self.database_manager and self.database_manager.connected:
            share_stats = self.get_share_stats()
            performance_metric = PerformanceMetric(
                hashrate=0.0,
                accepted_shares=share_stats["accepted"],
                rejected_shares=share_stats["rejected"],
                hardware_errors=share_stats["hardware_errors"],
                uptime_seconds=time.time() - self.start_time,
                worker_name=worker_name
            )
            self.database_manager.store_performance_metric(performance_metric.to_dict())

    def record_difficulty_change(self, old_diff: float, new_diff: float,
                                 worker_name: str = "unknown") -> None:
        """Record difficulty change"""
        self.logger.info(f"Difficulty changed from {old_diff} to {new_diff}")

        # Store alert in database if available
        if self.database_manager and self.database_manager.connected:
            alert_data = {
                "alert_type": "difficulty_change",
                "message": f"Difficulty changed from {old_diff} to {new_diff}",
                "severity": "info",
                "worker_name": worker_name
            }
            self.database_manager.store_alert(alert_data)

    def get_share_stats(self) -> Dict[str, Any]:
        """Get share statistics"""
        total_shares = self.share_stats['accepted'] + self.share_stats['rejected']
        acceptance_rate = (self.share_stats['accepted'] / total_shares * 100) if total_shares > 0 else 0.0

        return {
            "accepted": self.share_stats['accepted'],
            "rejected": self.share_stats['rejected'],
            "hardware_errors": self.share_stats['hardware_errors'],
            "acceptance_rate": acceptance_rate,
            "last_accepted_time": self.share_stats['last_accepted_time'],
            "last_rejected_time": self.share_stats['last_rejected_time']
        }

    def get_system_info(self) -> Dict[str, Any]:
        """Get system information"""
        return {
            "platform": platform.platform(),
            "processor": platform.processor(),
            "python_version": platform.python_version(),
            "uptime": time.time() - self.start_time
        }

    async def perform_health_check(self) -> HealthStatus:
        """Perform comprehensive health check"""
        checks = {}
        issues = []

        try:
            for check_name, check_func in self.health_checks.items():
                try:
                    result = await check_func()
                    checks[check_name] = result
                    if not result:
                        issues.append(f"{check_name} check failed")
                except Exception as e:
                    checks[check_name] = False
                    issues.append(f"{check_name} check error: {e}")

            # Determine overall status
            if all(checks.values()):
                status = "healthy"
                message = "All health checks passed"
            elif any(checks.values()):
                status = "warning"
                message = f"Some health checks failed: {', '.join(issues)}"
            else:
                status = "critical"
                message = f"All health checks failed: {', '.join(issues)}"

            return HealthStatus(
                status=status,
                message=message,
                checks=checks
            )

        except Exception as e:
            self.logger.error(f"Error performing health check: {e}")
            return HealthStatus(
                status="critical",
                message=f"Health check error: {e}"
            )

    async def _check_system_resources(self) -> bool:
        """Check system resource usage"""
        try:
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()

            # Check if resources are within acceptable limits
            cpu_limit = self.config.get('cpu_limit_percent', 90)
            memory_limit = self.config.get('memory_limit_percent', 90)

            return cpu_percent < cpu_limit and memory.percent < memory_limit
        except Exception:
            return False

    async def _check_disk_space(self) -> bool:
        """Check available disk space"""
        try:
            disk = psutil.disk_usage('/')
            free_percent = (disk.free / disk.total) * 100
            min_free_percent = self.config.get('min_disk_free_percent', 10)
            return free_percent >= min_free_percent
        except Exception:
            return False

    async def _check_network_connectivity(self) -> bool:
        """Check network connectivity"""
        try:
            # Try to connect to a well-known host
            import socket
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(5)
            result = sock.connect_ex(('8.8.8.8', 53))  # Google DNS
            sock.close()
            return result == 0
        except Exception:
            return False

    async def _check_mining_process(self) -> bool:
        """Check if mining process is running"""
        # This would check if the actual mining process is active
        # For now, we'll assume it's running if the monitor is active
        return True

    def get_status(self) -> Dict[str, Any]:
        """Get comprehensive system status"""
        system_stats = self.metrics_collector.get_system_stats()
        share_stats = self.get_share_stats()
        system_info = self.get_system_info()

        return {
            "system": system_stats,
            "mining": share_stats,
            "info": system_info,
            "uptime": time.time() - self.start_time
        }

    def export_metrics(self) -> Dict[str, Any]:
        """Export all metrics in a structured format"""
        health_status = None
        if self.monitoring:
            try:
                health_status = asyncio.create_task(self.perform_health_check()).result()
            except Exception:
                pass

        return {
            "timestamp": datetime.now().isoformat(),
            "system_metrics": self.metrics_collector.get_system_stats(),
            "mining_metrics": self.get_share_stats(),
            "system_info": self.get_system_info(),
            "health_status": health_status
        }


# JSON Logger for structured logging
class JsonLogger:
    """Structured JSON logging for mining operations"""

    def __init__(self, name: str = "mining"):
        self.logger = logging.getLogger(name)
        self.name = name

    def log_event(self, event_type: str, data: Dict[str, Any], 
                  level: str = "info") -> None:
        """Log an event with structured data"""
        log_data = {
            "timestamp": datetime.now().isoformat(),
            "event_type": event_type,
            "data": data,
            "logger": self.name
        }

        log_message = json.dumps(log_data, default=str)

        if level == "debug":
            self.logger.debug(log_message)
        elif level == "info":
            self.logger.info(log_message)
        elif level == "warning":
            self.logger.warning(log_message)
        elif level == "error":
            self.logger.error(log_message)
        elif level == "critical":
            self.logger.critical(log_message)

    def log_share_submission(self, job_id: str, success: bool, difficulty: float, 
                             error: str = None, worker_name: str = "unknown") -> None:
        """Log share submission event"""
        data = {
            "job_id": job_id,
            "success": success,
            "difficulty": difficulty,
            "worker_name": worker_name
        }
        if error:
            data["error"] = error

        self.log_event("share_submission", data, "info" if success else "warning")

    def log_connection_event(self, pool_url: str, event: str, 
                             details: Dict[str, Any] = None,
                             worker_name: str = "unknown") -> None:
        """Log connection-related events"""
        data = {
            "pool_url": pool_url,
            "event": event,
            "worker_name": worker_name
        }
        if details:
            data.update(details)

        self.log_event("connection_event", data, "info")

    def log_performance_metric(self, metric_name: str, value: float, unit: str,
                               worker_name: str = "unknown") -> None:
        """Log performance metrics"""
        data = {
            "metric_name": metric_name,
            "value": value,
            "unit": unit,
            "worker_name": worker_name
        }

        self.log_event("performance_metric", data, "info")

    def log_error(self, error_type: str, message: str, traceback: str = None,
                  worker_name: str = "unknown") -> None:
        """Log error events"""
        data = {
            "error_type": error_type,
            "message": message,
            "worker_name": worker_name
        }
        if traceback:
            data["traceback"] = traceback

        self.log_event("error", data, "error")
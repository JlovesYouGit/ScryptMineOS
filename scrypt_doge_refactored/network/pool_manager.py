"""
Circuit Breaker and Pool Failover System for the refactored Scrypt DOGE mining system.
Implements resilient pool connection management with circuit breaker pattern.
"""

import asyncio
import logging
import time
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime, timedelta
import random

logger = logging.getLogger(__name__)


class CircuitState(Enum):
    """Circuit breaker states"""
    CLOSED = "closed"      # Normal operation
    OPEN = "open"          # Failing fast
    HALF_OPEN = "half_open"  # Testing if service recovered


@dataclass
class CircuitMetrics:
    """Circuit breaker metrics"""
    failure_count: int = 0
    success_count: int = 0
    last_failure_time: Optional[float] = None
    last_success_time: Optional[float] = None
    consecutive_failures: int = 0
    consecutive_successes: int = 0


class CircuitBreaker:
    """Circuit breaker pattern implementation"""
    
    def __init__(
        self,
        name: str,
        failure_threshold: int = 5,
        recovery_timeout: float = 60.0,
        success_threshold: int = 3,
        expected_exception: type = Exception
    ):
        self.name = name
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.success_threshold = success_threshold
        self.expected_exception = expected_exception
        
        self.logger = logging.getLogger(f"{__name__}.{name}")
        self.state = CircuitState.CLOSED
        self.metrics = CircuitMetrics()
        self._state_change_time = time.time()
        self._lock = asyncio.Lock()
    
    async def call(self, func: Callable, *args, **kwargs) -> Any:
        """Execute function with circuit breaker protection"""
        async with self._lock:
            if self.state == CircuitState.OPEN:
                if time.time() - self._state_change_time >= self.recovery_timeout:
                    self._transition_to(CircuitState.HALF_OPEN)
                else:
                    raise Exception(f"Circuit breaker {self.name} is OPEN")
            
            try:
                result = await func(*args, **kwargs)
                await self._on_success()
                return result
                
            except self.expected_exception as e:
                await self._on_failure()
                raise
    
    async def _on_success(self) -> None:
        """Handle successful call"""
        current_time = time.time()
        self.metrics.success_count += 1
        self.metrics.last_success_time = current_time
        self.metrics.consecutive_successes += 1
        self.metrics.consecutive_failures = 0
        
        if self.state == CircuitState.HALF_OPEN:
            if self.metrics.consecutive_successes >= self.success_threshold:
                self._transition_to(CircuitState.CLOSED)
                self.logger.info(f"Circuit breaker {self.name} recovered")
    
    async def _on_failure(self) -> None:
        """Handle failed call"""
        current_time = time.time()
        self.metrics.failure_count += 1
        self.metrics.last_failure_time = current_time
        self.metrics.consecutive_failures += 1
        self.metrics.consecutive_successes = 0
        
        if self.state == CircuitState.CLOSED:
            if self.metrics.consecutive_failures >= self.failure_threshold:
                self._transition_to(CircuitState.OPEN)
                self.logger.warning(f"Circuit breaker {self.name} opened after {self.failure_threshold} failures")
        elif self.state == CircuitState.HALF_OPEN:
            self._transition_to(CircuitState.OPEN)
            self.logger.warning(f"Circuit breaker {self.name} reopened")
    
    def _transition_to(self, new_state: CircuitState) -> None:
        """Transition to new state"""
        old_state = self.state
        self.state = new_state
        self._state_change_time = time.time()
        self.logger.info(f"Circuit breaker {self.name} transitioned from {old_state} to {new_state}")
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get circuit breaker metrics"""
        return {
            'name': self.name,
            'state': self.state.value,
            'failure_count': self.metrics.failure_count,
            'success_count': self.metrics.success_count,
            'consecutive_failures': self.metrics.consecutive_failures,
            'consecutive_successes': self.metrics.consecutive_successes,
            'last_failure_time': self.metrics.last_failure_time,
            'last_success_time': self.metrics.last_success_time
        }


@dataclass
class PoolConnection:
    """Pool connection details"""
    url: str
    username: str
    password: str
    algorithm: str
    priority: int
    timeout: int
    retry_attempts: int
    enable_tls: bool
    circuit_breaker: CircuitBreaker
    last_used: Optional[datetime] = None
    success_count: int = 0
    failure_count: int = 0
    average_latency: float = 0.0
    is_active: bool = False


class PoolFailoverManager:
    """Manages multiple pool connections with failover"""
    
    def __init__(self, config: List[Dict[str, Any]]):
        self.logger = logging.getLogger(__name__)
        self.pools: List[PoolConnection] = []
        self.active_pool: Optional[PoolConnection] = None
        self.failover_callbacks: List[Callable] = []
        
        # Initialize pools
        for pool_config in config:
            circuit_breaker = CircuitBreaker(
                name=f"pool_{pool_config['url']}",
                failure_threshold=pool_config.get('failure_threshold', 5),
                recovery_timeout=pool_config.get('recovery_timeout', 60.0)
            )
            
            pool = PoolConnection(
                url=pool_config['url'],
                username=pool_config['username'],
                password=pool_config['password'],
                algorithm=pool_config.get('algorithm', 'scrypt'),
                priority=pool_config.get('priority', 1),
                timeout=pool_config.get('timeout', 30),
                retry_attempts=pool_config.get('retry_attempts', 3),
                enable_tls=pool_config.get('enable_tls', True),
                circuit_breaker=circuit_breaker
            )
            
            self.pools.append(pool)
        
        # Sort by priority
        self.pools.sort(key=lambda p: p.priority)
        
        # Statistics
        self.failover_count = 0
        self.total_downtime = 0.0
        self.last_failover_time: Optional[datetime] = None
    
    def add_failover_callback(self, callback: Callable) -> None:
        """Add failover event callback"""
        self.failover_callbacks.append(callback)
    
    def _trigger_failover_callbacks(self, old_pool: Optional[PoolConnection], new_pool: PoolConnection) -> None:
        """Trigger failover callbacks"""
        for callback in self.failover_callbacks:
            try:
                callback(old_pool, new_pool)
            except Exception as e:
                self.logger.error(f"Failover callback error: {e}")
    
    async def get_active_pool(self) -> Optional[PoolConnection]:
        """Get currently active pool"""
        return self.active_pool
    
    async def connect_to_best_pool(self) -> bool:
        """Connect to the best available pool"""
        self.logger.info("Connecting to best available pool")
        
        for pool in self.pools:
            if await self._try_connect_pool(pool):
                return True
        
        self.logger.error("No available pools found")
        return False
    
    async def _try_connect_pool(self, pool: PoolConnection) -> bool:
        """Try to connect to a specific pool"""
        try:
            self.logger.info(f"Trying pool: {pool.url}")
            
            # Test connection through circuit breaker
            # This would integrate with the actual Stratum client
            async def test_connection():
                # Simulate connection test
                await asyncio.sleep(0.1)
                return True
            
            success = await pool.circuit_breaker.call(test_connection)
            
            if success:
                # Update pool statistics
                pool.last_used = datetime.now()
                pool.success_count += 1
                pool.is_active = True
                
                # Set as active pool
                old_pool = self.active_pool
                self.active_pool = pool
                
                self.logger.info(f"Successfully connected to pool: {pool.url}")
                
                # Trigger callbacks
                if old_pool != pool:
                    self._trigger_failover_callbacks(old_pool, pool)
                
                return True
            else:
                pool.failure_count += 1
                pool.is_active = False
                return False
                
        except Exception as e:
            self.logger.error(f"Failed to connect to pool {pool.url}: {e}")
            pool.failure_count += 1
            pool.is_active = False
            return False
    
    async def handle_pool_failure(self, pool: PoolConnection) -> bool:
        """Handle pool failure and failover to next pool"""
        self.logger.warning(f"Pool failure detected: {pool.url}")
        
        # Record failover
        self.failover_count += 1
        self.last_failover_time = datetime.now()
        
        # Mark current pool as failed
        pool.is_active = False
        pool.failure_count += 1
        
        # Try to failover to next pool
        current_index = self.pools.index(pool)
        
        for i in range(current_index + 1, len(self.pools)):
            next_pool = self.pools[i]
            if await self._try_connect_pool(next_pool):
                return True
        
        # Try pools with lower priority
        for i in range(0, current_index):
            next_pool = self.pools[i]
            if await self._try_connect_pool(next_pool):
                return True
        
        self.logger.error("No backup pools available")
        return False
    
    def get_pool_statistics(self) -> Dict[str, Any]:
        """Get pool connection statistics"""
        pool_stats = []
        
        for pool in self.pools:
            stats = {
                'url': pool.url,
                'priority': pool.priority,
                'is_active': pool.is_active,
                'success_count': pool.success_count,
                'failure_count': pool.failure_count,
                'average_latency': pool.average_latency,
                'last_used': pool.last_used.isoformat() if pool.last_used else None,
                'circuit_breaker': pool.circuit_breaker.get_metrics()
            }
            pool_stats.append(stats)
        
        return {
            'pools': pool_stats,
            'active_pool': self.active_pool.url if self.active_pool else None,
            'failover_count': self.failover_count,
            'total_downtime': self.total_downtime,
            'last_failover_time': self.last_failover_time.isoformat() if self.last_failover_time else None
        }
    
    def get_recommended_pools(self) -> List[PoolConnection]:
        """Get pools ordered by recommendation"""
        # Sort by health score (success rate) and priority
        
        def health_score(pool: PoolConnection) -> float:
            total_attempts = pool.success_count + pool.failure_count
            if total_attempts == 0:
                return 0.5  # Neutral score for untested pools
            
            success_rate = pool.success_count / total_attempts
            circuit_health = 1.0 if pool.circuit_breaker.state == CircuitState.CLOSED else 0.0
            
            return (success_rate * 0.7) + (circuit_health * 0.3)
        
        # Sort by health score (descending) then priority (ascending)
        return sorted(self.pools, key=lambda p: (-health_score(p), p.priority))


class ConnectionPool:
    """Manages connection pooling for multiple mining operations"""
    
    def __init__(self, max_connections: int = 10):
        self.logger = logging.getLogger(__name__)
        self.max_connections = max_connections
        self.active_connections: Dict[str, Any] = {}
        self.connection_queue: asyncio.Queue = asyncio.Queue(maxsize=max_connections)
        self.lock = asyncio.Lock()
    
    async def get_connection(self, pool_key: str) -> Any:
        """Get a connection from the pool"""
        async with self.lock:
            if pool_key in self.active_connections:
                return self.active_connections[pool_key]
            
            # Create new connection if we haven't reached the limit
            if len(self.active_connections) < self.max_connections:
                # This would create an actual connection
                connection = await self._create_connection(pool_key)
                self.active_connections[pool_key] = connection
                return connection
            
            # Wait for a connection to become available
            try:
                connection = await asyncio.wait_for(self.connection_queue.get(), timeout=30.0)
                self.active_connections[pool_key] = connection
                return connection
            except asyncio.TimeoutError:
                raise Exception("Timeout waiting for connection")
    
    async def release_connection(self, pool_key: str, connection: Any) -> None:
        """Release a connection back to the pool"""
        async with self.lock:
            if pool_key in self.active_connections:
                del self.active_connections[pool_key]
                await self.connection_queue.put(connection)
    
    async def _create_connection(self, pool_key: str) -> Any:
        """Create a new connection (placeholder)"""
        # This would create an actual connection to the mining pool
        self.logger.info(f"Creating new connection for pool: {pool_key}")
        return f"connection_{pool_key}_{random.randint(1000, 9999)}"
    
    async def close_all_connections(self) -> None:
        """Close all connections in the pool"""
        async with self.lock:
            for connection in self.active_connections.values():
                # This would close the actual connection
                self.logger.info(f"Closing connection: {connection}")
            self.active_connections.clear()
            
            # Clear the queue
            while not self.connection_queue.empty():
                try:
                    self.connection_queue.get_nowait()
                except asyncio.QueueEmpty:
                    break
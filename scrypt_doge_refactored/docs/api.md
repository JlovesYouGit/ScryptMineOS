# Scrypt DOGE Mining System API Documentation

## Overview

This document provides detailed information about the APIs and interfaces available in the Scrypt DOGE Mining System. The system provides both internal Python APIs for component interaction and external REST APIs for monitoring and management.

## Internal Python APIs

### Core Components

#### MiningSystemService
```python
class MiningSystemService:
    async def initialize(self) -> bool
    async def start(self) -> None
    async def stop(self) -> None
    def get_status(self) -> dict
```

#### ConfigManager
```python
class ConfigManager:
    async def load_config(self) -> Config
    async def save_config(self, config: Config) -> None
    def get_config(self) -> Config
```

#### MiningService
```python
class MiningService:
    async def initialize(self) -> bool
    async def start_mining(self) -> None
    async def stop_mining(self) -> None
    async def connect_to_pool(self) -> bool
    def get_status(self) -> MiningStatus
```

### Network Components

#### EnhancedStratumClient
```python
class EnhancedStratumClient:
    async def connect(self) -> bool
    async def disconnect(self) -> None
    async def subscribe(self) -> bool
    async def authorize(self) -> bool
    async def submit_share(self, job_id: str, extranonce2: str, ntime: str, nonce: str) -> ShareResult
    def add_job_callback(self, callback: Callable[[StratumJob], None]) -> None
    def add_difficulty_callback(self, callback: Callable[[float], None]) -> None
```

#### PoolFailoverManager
```python
class PoolFailoverManager:
    async def connect_to_best_pool(self) -> bool
    async def handle_pool_failure(self, pool: PoolConnection) -> bool
    def get_pool_statistics(self) -> Dict[str, Any]
    def get_recommended_pools(self) -> List[PoolConnection]
```

### Security Components

#### SecurityManager
```python
class SecurityManager:
    async def start(self) -> None
    async def stop(self) -> None
    def is_request_allowed(self, ip_address: str) -> bool
    def validate_wallet_address(self, address: str, currency: str) -> bool
    def validate_worker_name(self, worker_name: str) -> bool
    def encrypt_data(self, data: str) -> str
    def decrypt_data(self, encrypted_data: str) -> str
```

#### EconomicGuardian
```python
class EconomicGuardian:
    async def start_monitoring(self) -> None
    async def stop_monitoring(self) -> None
    def is_mining_profitable(self) -> bool
    def get_profitability_summary(self) -> Dict[str, Any]
    def add_callback(self, event: str, callback: Callable) -> None
```

### Hardware Components

#### ASICInterface
```python
class ASICInterface:
    async def connect(self) -> bool
    async def disconnect(self) -> None
    async def start_mining(self, pool_url: str, username: str, password=os.getenv("POOL_PASSWORD", "x")"POOL_PASSWORD", "x") -> bool
    async def stop_mining(self) -> bool
    async def get_stats(self) -> HardwareStats
    async def get_info(self) -> HardwareInfo
    async def apply_config(self, config: HardwareConfig) -> bool
```

### Monitoring Components

#### SystemMonitor
```python
class SystemMonitor:
    async def start_monitoring(self) -> None
    async def stop_monitoring(self) -> None
    def record_share_accepted(self) -> None
    def record_share_rejected(self, reason: str) -> None
    def record_hardware_error(self) -> None
    def get_share_stats(self) -> Dict[str, int]
    def get_system_info(self) -> Dict[str, Any]
```

#### StructuredLogger
```python
class StructuredLogger:
    def debug(self, event_type: str, data: Dict[str, Any], message: str = "") -> None
    def info(self, event_type: str, data: Dict[str, Any], message: str = "") -> None
    def warning(self, event_type: str, data: Dict[str, Any], message: str = "") -> None
    def error(self, event_type: str, data: Dict[str, Any], message: str = "", exception: Exception = None) -> None
    def critical(self, event_type: str, data: Dict[str, Any], message: str = "", exception: Exception = None) -> None
```

### Optimization Components

#### GPUPerformanceOptimizer
```python
class GPUPerformanceOptimizer:
    def measure_baseline(self) -> PerformanceMetrics
    def optimize_l2_kernel(self) -> PerformanceMetrics
    def optimize_voltage_frequency(self) -> PerformanceMetrics
    def apply_clock_gating(self) -> PerformanceMetrics
    def validate_performance(self) -> PerformanceMetrics
```

## External REST APIs

### Health Check API
```
GET /health
```
Returns the overall health status of the mining system.

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2023-01-01T00:00:00Z",
  "components": {
    "mining": "healthy",
    "network": "healthy",
    "hardware": "healthy",
    "security": "healthy"
  }
}
```

### Metrics API
```
GET /metrics
```
Returns system metrics in Prometheus format.

### Status API
```
GET /status
```
Returns detailed system status information.

**Response:**
```json
{
  "running": true,
  "start_time": "2023-01-01T00:00:00Z",
  "uptime": 3600,
  "components": {
    "mining": {
      "status": "mining",
      "current_pool": "stratum+tcp://doge.zsolo.bid:8057",
      "hashrate": 9500000000,
      "accepted_shares": 100,
      "rejected_shares": 2
    },
    "monitoring": {
      "cpu_percent": 25.5,
      "memory_percent": 45.2,
      "disk_usage_percent": 60.1
    },
    "security": {
      "status": "active",
      "blocked_ips": 0,
      "rate_limited_requests": 5
    }
  }
}
```

### Configuration API
```
GET /config
```
Returns current configuration settings.

```
POST /config
```
Updates configuration settings.

### Control API
```
POST /control/start
```
Starts the mining process.

```
POST /control/stop
```
Stops the mining process.

```
POST /control/restart
```
Restarts the mining process.

## Command Line Interface

### Main Entry Point
```bash
python main.py [--mode educational|production] [--continuous] [--monitor] [--verbose]
```

### Options
- `--mode`: System operation mode (educational, production, testing)
- `--config`: Path to configuration file
- `--verbose`: Enable verbose logging
- `--status`: Show current system status and exit

### Examples
```bash
# Run in production mode
python main.py --mode production

# Run with custom configuration
python main.py --config /path/to/config.yaml

# Enable verbose logging
python main.py --verbose

# Show system status
python main.py --status
```

## Environment Variables

- `LTC_ADDRESS`: Litecoin wallet address
- `DOGE_ADDRESS`: Dogecoin wallet address
- `WORKER_NAME`: Mining worker name
- `ELECTRICITY_COST_KWH`: Electricity cost per kWh
- `POOL_REGION`: Preferred pool region

## Configuration File Format

The system uses YAML configuration files with the following structure:

```yaml
environment: production

mining:
  algorithm: scrypt
  threads: auto
  intensity: auto

pools:
  - url: stratum+tcp://doge.zsolo.bid:8057
    username: YOUR_WALLET_ADDRESS
    password=os.getenv("POOL_PASSWORD", "x")"POOL_PASSWORD", "x")
    algorithm: scrypt
    priority: 1

hardware:
  type: asic
  temperature_limit: 80

economic:
  enabled: true
  max_power_cost: 0.12
  min_profitability: 0.01
  shutdown_on_unprofitable: true

security:
  enable_encryption: true
  rate_limiting_enabled: true

monitoring:
  enabled: true
  metrics_port: 8080
  health_check_port: 8081

logging:
  level: INFO
  file_path: logs/mining.log
```

## Error Handling

The system implements comprehensive error handling with the following error types:

- **Configuration Errors**: Invalid configuration settings
- **Network Errors**: Pool connection issues
- **Hardware Errors**: ASIC/GPU hardware problems
- **Security Errors**: Authentication and authorization failures
- **Economic Errors**: Profitability calculation issues
- **System Errors**: General system failures

All errors are logged with appropriate severity levels and may trigger alerts based on the configured thresholds.
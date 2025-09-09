# Scrypt DOGE Mining System - API Documentation

## Overview

This document provides comprehensive documentation for the Scrypt DOGE Mining System APIs. The system exposes various interfaces for configuration, monitoring, control, and integration with external systems.

## Core APIs

### Configuration Management API

#### Load Configuration
```
GET /api/v1/config
```
Retrieves the current system configuration.

**Response:**
```json
{
  "environment": "production",
  "mining": {
    "algorithm": "scrypt",
    "threads": "auto",
    "intensity": "auto"
  },
  "pools": [...],
  "hardware": {...},
  "economic": {...},
  "security": {...},
  "monitoring": {...}
}
```

#### Update Configuration
```
PUT /api/v1/config
```
Updates the system configuration.

**Request Body:**
```json
{
  "mining": {
    "threads": 8,
    "intensity": 20
  }
}
```

#### Reload Configuration
```
POST /api/v1/config/reload
```
Reloads configuration from files.

### Mining Control API

#### Start Mining
```
POST /api/v1/mining/start
```
Starts the mining process.

**Response:**
```json
{
  "status": "success",
  "message": "Mining started successfully"
}
```

#### Stop Mining
```
POST /api/v1/mining/stop
```
Stops the mining process.

#### Restart Mining
```
POST /api/v1/mining/restart
```
Restarts the mining process.

#### Get Mining Status
```
GET /api/v1/mining/status
```
Retrieves the current mining status.

**Response:**
```json
{
  "running": true,
  "hashrate": 9500.5,
  "uptime": 3600,
  "shares": {
    "accepted": 150,
    "rejected": 2,
    "acceptance_rate": 98.7
  }
}
```

### Pool Management API

#### Get Pool Status
```
GET /api/v1/pools
```
Retrieves the status of all configured pools.

**Response:**
```json
{
  "active_pool": "stratum+tcp://doge.zsolo.bid:8057",
  "pools": [
    {
      "url": "stratum+tcp://doge.zsolo.bid:8057",
      "priority": 1,
      "status": "active",
      "latency": 45.2
    },
    {
      "url": "stratum+tcp://backup.pool.com:3333",
      "priority": 2,
      "status": "standby",
      "latency": 87.5
    }
  ]
}
```

#### Switch Pool
```
POST /api/v1/pools/switch
```
Manually switches to a different pool.

**Request Body:**
```json
{
  "pool_url": "stratum+tcp://backup.pool.com:3333"
}
```

### Hardware Management API

#### Get Hardware Status
```
GET /api/v1/hardware
```
Retrieves the status of all connected hardware.

**Response:**
```json
{
  "devices": [
    {
      "id": "asic_001",
      "type": "asic",
      "model": "Antminer L7",
      "status": "mining",
      "hashrate": 9500.5,
      "temperature": 72.3,
      "power": 3200,
      "fan_speed": 3200
    }
  ]
}
```

#### Configure Hardware
```
PUT /api/v1/hardware/{device_id}
```
Configures a specific hardware device.

**Request Body:**
```json
{
  "frequency": 450,
  "voltage": 4.2,
  "fan_speed": "auto"
}
```

### Economic Guardian API

#### Get Profitability Status
```
GET /api/v1/economic/profitability
```
Retrieves current profitability metrics.

**Response:**
```json
{
  "profitable": true,
  "profit_margin": 15.2,
  "revenue_usd_per_day": 12.50,
  "costs_usd_per_day": 10.60,
  "break_even_price": 0.08
}
```

#### Configure Economic Settings
```
PUT /api/v1/economic/settings
```
Updates economic safeguard settings.

**Request Body:**
```json
{
  "max_power_cost": 0.12,
  "min_profitability": 0.05,
  "shutdown_on_unprofitable": true
}
```

### Security Management API

#### Get Security Status
```
GET /api/v1/security/status
```
Retrieves current security status.

**Response:**
```json
{
  "encryption_enabled": true,
  "rate_limiting_enabled": true,
  "ddos_protection_enabled": true,
  "allowed_ips": ["127.0.0.1"],
  "blocked_ips": []
}
```

#### Update Security Settings
```
PUT /api/v1/security/settings
```
Updates security configuration.

**Request Body:**
```json
{
  "rate_limiting_enabled": true,
  "max_requests_per_minute": 60,
  "allowed_ips": ["127.0.0.1", "192.168.1.100"]
}
```

## Monitoring APIs

### Metrics API

#### Get System Metrics
```
GET /api/v1/metrics
```
Retrieves current system metrics in Prometheus format.

**Response:**
```
# HELP mining_hashrate_mhs Current hashrate in MH/s
# TYPE mining_hashrate_mhs gauge
mining_hashrate_mhs 9500.5

# HELP mining_shares_accepted_total Total accepted shares
# TYPE mining_shares_accepted_total counter
mining_shares_accepted_total 150

# HELP mining_shares_rejected_total Total rejected shares
# TYPE mining_shares_rejected_total counter
mining_shares_rejected_total 2
```

#### Get Hardware Metrics
```
GET /api/v1/metrics/hardware
```
Retrieves hardware-specific metrics.

### Health Check API

#### System Health
```
GET /api/v1/health
```
Performs a comprehensive health check of the system.

**Response:**
```json
{
  "status": "healthy",
  "components": {
    "mining": "healthy",
    "network": "healthy",
    "hardware": "healthy",
    "security": "healthy"
  },
  "timestamp": "2025-09-06T10:30:00Z"
}
```

#### Component Health
```
GET /api/v1/health/{component}
```
Checks the health of a specific component.

## Event Streaming APIs

### Real-time Events
```
GET /api/v1/events
```
Establishes a WebSocket connection for real-time event streaming.

**Events:**
- `share_accepted` - When a share is accepted by the pool
- `share_rejected` - When a share is rejected by the pool
- `hardware_error` - When a hardware error occurs
- `pool_switch` - When switching to a different pool
- `profitability_change` - When profitability status changes

## Alerting APIs

### Get Recent Alerts
```
GET /api/v1/alerts
```
Retrieves recent system alerts.

**Response:**
```json
{
  "alerts": [
    {
      "timestamp": "2025-09-06T10:25:00Z",
      "type": "HIGH_TEMPERATURE",
      "message": "High temperature detected: 82°C",
      "severity": "warning"
    }
  ]
}
```

### Configure Alerting
```
PUT /api/v1/alerts/settings
```
Configures alerting thresholds and notifications.

## Integration APIs

### Webhook Integration
```
POST /api/v1/webhooks/{webhook_id}
```
Receives external webhook notifications.

### External Pool Integration
```
POST /api/v1/pools/external
```
Integrates with external mining pools.

## Authentication and Authorization

### API Key Authentication
All API endpoints require authentication using an API key.

**Header:**
```
Authorization: Bearer {api_key}
```

### Role-Based Access Control
Different API endpoints require different permission levels:
- `miner:read` - Read-only access to mining status
- `miner:write` - Ability to start/stop mining
- `admin:read` - Read access to all system configuration
- `admin:write` - Write access to all system configuration

## Error Handling

### Error Response Format
All error responses follow a consistent format:

```json
{
  "error": {
    "code": "INVALID_CONFIGURATION",
    "message": "Invalid configuration parameter",
    "details": "The 'threads' parameter must be a positive integer"
  }
}
```

### Common Error Codes
- `INVALID_REQUEST` - Malformed request
- `INVALID_CONFIGURATION` - Invalid configuration parameters
- `UNAUTHORIZED` - Missing or invalid authentication
- `FORBIDDEN` - Insufficient permissions
- `NOT_FOUND` - Resource not found
- `INTERNAL_ERROR` - Internal system error

## Rate Limiting

API requests are rate-limited to prevent abuse:
- 60 requests per minute for read operations
- 10 requests per minute for write operations
- 1 request per minute for administrative operations

Exceeding rate limits will result in a 429 (Too Many Requests) response.

## Versioning

The API follows semantic versioning. Breaking changes will result in a new major version number.

**Current Version:** v1

## Client Libraries

### Python Client
```python
from scrypt_doge.client import MiningClient

client = MiningClient(api_key="your_api_key", base_url="http://localhost:8080")

# Get mining status
status = client.get_mining_status()
print(f"Hashrate: {status['hashrate']} MH/s")

# Start mining
client.start_mining()
```

### JavaScript Client
```javascript
const { MiningClient } = require('scrypt-doge-client');

const client = new MiningClient({
  apiKey: 'your_api_key',
  baseUrl: 'http://localhost:8080'
});

// Get mining status
client.getMiningStatus().then(status => {
  console.log(`Hashrate: ${status.hashrate} MH/s`);
});

// Start mining
client.startMining();
```

## Examples

### Starting Mining with Custom Configuration
```bash
# Start mining with custom thread count
curl -X POST http://localhost:8080/api/v1/mining/start \
  -H "Authorization: Bearer your_api_key" \
  -H "Content-Type: application/json" \
  -d '{
    "config": {
      "mining": {
        "threads": 8,
        "intensity": 20
      }
    }
  }'
```

### Monitoring Profitability
```bash
# Check if mining is profitable
curl -X GET http://localhost:8080/api/v1/economic/profitability \
  -H "Authorization: Bearer your_api_key"
```

### Configuring Hardware
```bash
# Set ASIC frequency to 450MHz
curl -X PUT http://localhost:8080/api/v1/hardware/asic_001 \
  -H "Authorization: Bearer your_api_key" \
  -H "Content-Type: application/json" \
  -d '{
    "frequency": 450
  }'
```
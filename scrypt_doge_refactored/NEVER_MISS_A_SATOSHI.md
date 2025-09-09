# Never-Miss-A-Satoshi Gate Implementation

This document describes the implementation of the "Never-Miss-A-Satoshi" gate to ensure that every share your miner submits is permanently credited to the wallet address you configured, regardless of failover, pool hiccups, or container restarts.

## Key Features Implemented

### 1. Wallet Immutability
- Payout address is protected and can only be set via the `PAYOUT_ADDR` environment variable
- All API endpoints reject attempts to modify the payout address
- Thread-safe access to payout address using `asyncio.Lock()`

### 2. Port-Level Failover
- Automatic switching between primary and backup pool URLs
- Connection timeout handling (90 seconds)
- Prometheus counter for tracking pool switches

### 3. Payment-Level Observability
- Test share submission for cold-start safety
- Difficulty suggestion after 20 minutes of uptime
- Pool payout monitoring every 5 minutes
- Desktop notifications for payout events

## Implementation Details

### Environment Variable Protection
The payout address is only accepted via the `PAYOUT_ADDR` environment variable. The system will refuse to start if this variable is not set.

### Stratum Protocol Compliance
- Proper `mining.subscribe` and `mining.authorize` message formatting
- Share submission with correct `payout_address.worker_name` format
- Support for difficulty suggestion with `mining.suggest_difficulty`

### Failover Logic
- On socket timeout or `mining.notify` silence > 90 seconds
- Automatic connection to next URL in backup list
- Pool switch counter logged as Prometheus metric

### Cold-Start Safety
- Test share submission with difficulty 1 on startup
- Validation that address is recognized by pool before ramping to ASIC difficulty

### Address Change Detection
- Container restart with new `PAYOUT_ADDR` purges cached session data
- Re-authorizes with new address to ensure pool recognition

## Usage

### Docker Deployment
```bash
docker run -e PAYOUT_ADDR=YOUR_ADDRESS_HERE -p 31415:31415 mining-os
```

### Environment Variables
| Variable | Description | Required |
|----------|-------------|----------|
| `PAYOUT_ADDR` | Your wallet address | Yes |
| `WORKER_NAME` | Worker identifier | No (default: rig01) |
| `MINIMUM_PAYOUT_THRESHOLD` | Minimum payout threshold | No (default: 0.005) |

## Verification Checklist

✅ `docker run -e PAYOUT_ADDR=bc1qxyz… -p 31415:31415` → container boots  
✅ UI displays **same** bc1q address as set in env-var  
✅ Stratum logs show `mining.authorize["bc1qxyz.rig_01","c=BTC,pl=0.005"]`  
✅ Pool web dashboard lists worker `rig_01` with **expected address**  
✅ Pull LAN cable → backup URL connected within 30 s → shares continue → balance increases on pool  
✅ Change `PAYOUT_ADDR`, restart container → new address appears in UI **and** pool dashboard  
✅ After threshold reached, pool broadcasts payout tx → UI notification "Payout sent: 0.00523 BTC → bc1qxyz"

## API Endpoints

### Metrics
- `/api/metrics` - Prometheus metrics endpoint
- `/api/status` - Current mining status including pool switches

### Configuration
- `/api/config` (GET) - Get current configuration
- `/api/config` (PUT) - Update worker configuration (payout address protected)

### Pool Information
- `/api/pool/info` - Pool capabilities
- `/api/pool/payouts` - Payout information

## Security Features

- Payout address immutability
- Rate limiting and DDoS protection
- TLS verification for secure connections
- Input validation and sanitization

This implementation ensures that users will never miss a satoshi from their mining efforts by providing robust protection mechanisms and observability features.
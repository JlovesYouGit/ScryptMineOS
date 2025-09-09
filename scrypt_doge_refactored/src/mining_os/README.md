# Mining OS - Browser-First Mining Operating System

A modern, browser-based mining operating system that turns fragmented Python mining backends into a single long-running service with a beautiful web interface.

## Features

- **Browser-First Interface**: Access your miner through a web browser at `http://miner.local:31415`
- **Single Service**: One systemd unit, one port, zero surprises
- **Hardware Appliance**: Behaves like firmware with persistent configuration
- **Real-time Monitoring**: Live hashrate, temperature, and profit metrics
- **Economic Guardian**: Automatic profit protection with circuit breaker
- **Security Focused**: TLS enforcement, secure configuration storage

## Quick Start

### Using Docker (Recommended)

```bash
docker compose up -d
```

Then access the web interface at http://localhost:31415

### Direct Installation

```bash
./install.sh
```

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `GET /` | HTML | Main web interface |
| `GET /health` | JSON | Health check |
| `POST /api/actions/start` | JSON | Start mining |
| `POST /api/actions/stop` | JSON | Stop mining |
| `PUT /api/config` | JSON | Update configuration |
| `GET /api/logs` | SSE | Stream logs |
| `GET /api/config/schema` | JSON | Configuration schema |
| `WS /ws/metrics` | WebSocket | Real-time metrics |

## Configuration

Create a `settings.yaml` file:

```yaml
# Server settings
host: "0.0.0.0"
port: 31415

# Pool configuration
pools:
  - host: "pool.example.com"
    port: 3333
    username: os.getenv("POOL_USER", os.getenv("POOL_USER", "your_wallet_address.worker_name"))
    password=os.getenv("POOL_PASSWORD", "x")"POOL_PASSWORD", "x")"

# Economic settings
min_profit_margin_pct: 0.5

# Hardware settings
max_temperature: 80.0

# Security settings
tls_verify: true
```

## Development

### Frontend

The frontend is built with:
- React + TypeScript
- Vite
- Tailwind CSS
- Zustand for state management

To develop the frontend:
```bash
cd frontend
npm install
npm run dev
```

### Backend

The backend is built with:
- Python 3.11
- FastAPI
- Uvicorn
- Pydantic for configuration

To run the backend directly:
```bash
python -m src.mining_os --port 31415
```

## Deployment

### Systemd Service

The installation script sets up a systemd service that:
- Runs as the `miner` user
- Starts automatically on boot
- Restarts on failure
- Provides health checks

### Docker

The Docker image:
- Multi-stage build for smaller size (~120MB)
- Health checks
- Non-root user
- Exposes port 31415

## Security

- Wallet addresses stored in environment variables or secure keyring
- TLS enforced for all pool connections
- CORS restricted in production
- Content security headers

## Monitoring

- Prometheus metrics endpoint at `/metrics`
- Structured JSON logging
- Real-time WebSocket metrics
- Alert system for hardware issues
# Scrypt DOGE Mining System Deployment Guide

## Overview

This guide provides detailed instructions for deploying the Scrypt DOGE Mining System in various environments including standalone servers, Docker containers, and Kubernetes clusters.

## Prerequisites

### System Requirements
- **Operating System**: Linux (Ubuntu 20.04 LTS or newer recommended)
- **Python**: 3.8 or higher
- **RAM**: 4GB minimum (8GB recommended)
- **Disk Space**: 10GB free space
- **Network**: Stable internet connection

### Hardware Requirements
- **ASIC Miners**: Antminer L3+, L7, or equivalent
- **GPUs** (optional): AMD or NVIDIA GPUs for hybrid mining
- **Network**: Gigabit Ethernet recommended

## Installation Methods

### 1. Standalone Installation

#### Step 1: Clone the Repository
```bash
git clone https://github.com/your-repo/scrypt-doge-miner.git
cd scrypt-doge-miner
```

#### Step 2: Create Virtual Environment
```bash
python3 -m venv venv
source venv/bin/activate
```

#### Step 3: Install Dependencies
```bash
pip install -r requirements.txt
```

#### Step 4: Configure the System
Create a configuration file at `config/mining_config.yaml`:
```yaml
environment: production
mining:
  algorithm: scrypt
  threads: auto
  intensity: auto

pools:
  - url: stratum+tcp://doge.zsolo.bid:8057
    username: YOUR_WALLET_ADDRESS
    password: x
    algorithm: scrypt
    priority: 1

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
```

#### Step 5: Run the System
```bash
python main.py --mode production --config config/mining_config.yaml
```

### 2. Docker Installation

#### Step 1: Build Docker Image
```bash
docker build -t scrypt-doge-miner .
```

#### Step 2: Run Docker Container
```bash
docker run -d \
  --name scrypt-doge-miner \
  -p 8080:8080 \
  -p 8081:8081 \
  -v /path/to/config:/app/config \
  -v /path/to/logs:/app/logs \
  scrypt-doge-miner
```

#### Step 3: Configure Environment Variables
```bash
docker run -d \
  --name scrypt-doge-miner \
  -p 8080:8080 \
  -p 8081:8081 \
  -e DOGE_ADDRESS=your_wallet_address \
  -e ELECTRICITY_COST_KWH=0.12 \
  scrypt-doge-miner
```

### 3. Docker Compose Installation

Create a `docker-compose.yml` file:
```yaml
version: '3.8'

services:
  miner:
    build: .
    container_name: scrypt-doge-miner
    ports:
      - "8080:8080"
      - "8081:8081"
    volumes:
      - ./config:/app/config
      - ./logs:/app/logs
    environment:
      - DOGE_ADDRESS=your_wallet_address
      - ELECTRICITY_COST_KWH=0.12
    restart: unless-stopped
```

Run with:
```bash
docker-compose up -d
```

### 4. Kubernetes Installation

#### Step 1: Create Namespace
```bash
kubectl create namespace mining
```

#### Step 2: Deploy Configuration
```bash
kubectl apply -f k8s/configmap.yaml -n mining
kubectl apply -f k8s/secret.yaml -n mining
```

#### Step 3: Deploy Application
```bash
kubectl apply -f k8s/deployment.yaml -n mining
```

#### Step 4: Configure Secrets
Edit `k8s/secret.yaml` with your actual wallet address and pool username, then encode them in base64:
```bash
echo -n "your_wallet_address" | base64
echo -n "your_pool_username" | base64
```

Update the secret file with the encoded values and apply:
```bash
kubectl apply -f k8s/secret.yaml -n mining
```

## Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `DOGE_ADDRESS` | Dogecoin wallet address | Required |
| `LTC_ADDRESS` | Litecoin wallet address | Optional |
| `WORKER_NAME` | Mining worker name | rig01 |
| `ELECTRICITY_COST_KWH` | Electricity cost per kWh | 0.08 |
| `POOL_REGION` | Preferred pool region | global |

### Configuration File

The main configuration file is `config/mining_config.yaml`. Key sections include:

#### Mining Configuration
```yaml
mining:
  algorithm: scrypt
  threads: auto
  intensity: auto
  enable_educational_mode: false
  enable_hardware_emulation: false
```

#### Pool Configuration
```yaml
pools:
  - url: stratum+tcp://doge.zsolo.bid:8057
    username: YOUR_WALLET_ADDRESS
    password: x
    algorithm: scrypt
    priority: 1
    timeout: 30
    retry_attempts: 3
    enable_tls: true
```

#### Hardware Configuration
```yaml
hardware:
  type: asic  # asic, gpu, cpu, hybrid
  device_ids: []
  power_limit: null
  temperature_limit: 80
  fan_speed: null
  frequency: null
  voltage: null
```

#### Economic Configuration
```yaml
economic:
  enabled: true
  max_power_cost: 0.12  # $/kWh
  min_profitability: 0.01  # 1%
  shutdown_on_unprofitable: true
  profitability_check_interval: 300  # 5 minutes
```

#### Security Configuration
```yaml
security:
  enable_encryption: true
  rate_limiting_enabled: true
  max_requests_per_minute: 60
  enable_ddos_protection: true
  tls_verify: true
  allowed_ips:
    - 127.0.0.1
```

#### Monitoring Configuration
```yaml
monitoring:
  enabled: true
  metrics_port: 8080
  health_check_port: 8081
  enable_prometheus: true
  log_performance_metrics: true
```

## Monitoring and Metrics

### Prometheus Integration
The system exposes metrics in Prometheus format on port 8080. Configure your Prometheus server to scrape:

```yaml
scrape_configs:
  - job_name: 'scrypt-doge-miner'
    static_configs:
      - targets: ['localhost:8080']
```

### Grafana Dashboard
Import the provided Grafana dashboard JSON file to visualize mining metrics.

### Health Checks
Health checks are available on port 8081:
- `GET /health` - Overall system health
- `GET /status` - Detailed system status

## Security Considerations

### Firewall Configuration
Open the following ports:
- `8080` - Metrics endpoint
- `8081` - Health check endpoint
- Mining pool ports (typically 3333-3336)

### Access Control
Configure `allowed_ips` in the security section to restrict access to management endpoints.

### Encryption
Enable encryption for sensitive data storage and transmission.

## Troubleshooting

### Common Issues

#### 1. Pool Connection Failures
- Check pool URL and credentials
- Verify network connectivity
- Ensure TLS settings are correct

#### 2. Low Hashrate
- Check hardware configuration
- Verify temperature limits
- Review performance optimization settings

#### 3. Economic Shutdown
- Check profitability settings
- Verify electricity cost configuration
- Review market conditions

### Log Analysis
Check logs in the `logs/` directory for detailed error information:
- `mining.log` - Main application logs
- `error.log` - Error-specific logs

### Performance Tuning
- Adjust thread count and intensity settings
- Optimize voltage and frequency
- Enable clock gating features

## Maintenance

### Updates
Pull the latest code and restart the service:
```bash
git pull
pip install -r requirements.txt
systemctl restart scrypt-doge-miner
```

### Backup
Regularly backup:
- Configuration files
- Log files
- Performance metrics

### Monitoring
Set up alerts for:
- High rejected share rates
- Low hashrate
- High temperatures
- Economic unprofitability

## Scaling

### Horizontal Scaling
Deploy multiple instances with different worker names to the same wallet address.

### Vertical Scaling
Increase hardware resources:
- More powerful ASICs
- Additional GPUs
- Better cooling solutions

### Cloud Deployment
Deploy to cloud providers for geographic distribution and redundancy.

## Support

For issues and support, please:
1. Check the logs for error messages
2. Review the documentation
3. Open an issue on GitHub
4. Contact the development team
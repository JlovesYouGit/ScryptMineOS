# Scrypt DOGE Mining System - Deployment Guide

## Overview

This guide provides comprehensive instructions for deploying the Scrypt DOGE Mining System in various environments. The system supports multiple deployment options including local installation, Docker containers, and Kubernetes clusters.

## Prerequisites

### System Requirements

**Minimum Requirements:**
- CPU: 2+ cores
- RAM: 4GB+
- Disk Space: 10GB+ available
- OS: Ubuntu 18.04+, CentOS 7+, or Windows 10+
- Python: 3.8+
- GPU: CUDA-compatible (for GPU mining)

**Recommended Requirements:**
- CPU: 4+ cores
- RAM: 8GB+
- Disk Space: 50GB+ available (SSD recommended)
- OS: Ubuntu 20.04+ or CentOS 8+
- Python: 3.9+
- GPU: Modern CUDA-compatible GPU with 8GB+ VRAM

### Software Dependencies

- Python 3.8+
- pip package manager
- Git (for source installation)
- Docker (for containerized deployment)
- Kubernetes (for cluster deployment)
- NVIDIA drivers (for GPU mining)

## Installation Methods

### Method 1: Local Installation

#### 1. Clone the Repository
```bash
git clone https://github.com/your-org/scrypt-doge-miner.git
cd scrypt-doge-miner
```

#### 2. Create Virtual Environment
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# or
venv\Scripts\activate.bat  # Windows
```

#### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

#### 4. Configure the System
Create a configuration file at `config/mining_config.yaml`:
```yaml
default:
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
```

#### 5. Run the System
```bash
python main.py --config config/mining_config.yaml
```

### Method 2: Docker Deployment

#### 1. Pull the Docker Image
```bash
docker pull your-org/scrypt-doge-miner:latest
```

#### 2. Create Configuration Directory
```bash
mkdir -p ~/scrypt-doge-config
```

#### 3. Create Configuration File
Create `~/scrypt-doge-config/mining_config.yaml` with your configuration.

#### 4. Run the Container
```bash
docker run -d \
  --name scrypt-doge-miner \
  --restart unless-stopped \
  -v ~/scrypt-doge-config:/app/config \
  -v ~/scrypt-doge-logs:/app/logs \
  -p 8080:8080 \
  your-org/scrypt-doge-miner:latest
```

### Method 3: Docker Compose

#### 1. Create docker-compose.yml
```yaml
version: '3.8'

services:
  miner:
    image: your-org/scrypt-doge-miner:latest
    container_name: scrypt-doge-miner
    restart: unless-stopped
    volumes:
      - ./config:/app/config
      - ./logs:/app/logs
    ports:
      - "8080:8080"
    environment:
      - WALLET_ADDRESS=YOUR_WALLET_ADDRESS
      - MINING_ENV=production
```

#### 2. Run with Docker Compose
```bash
docker-compose up -d
```

### Method 4: Kubernetes Deployment

#### 1. Create Namespace
```bash
kubectl create namespace mining
```

#### 2. Create Configuration Secret
```bash
kubectl create secret generic mining-config \
  --from-file=config/mining_config.yaml \
  -n mining
```

#### 3. Deploy with Helm
```bash
helm install scrypt-doge-miner ./helm/scrypt-doge-miner \
  --namespace mining \
  --set walletAddress=YOUR_WALLET_ADDRESS
```

## Configuration

### Environment Variables

The system supports configuration through environment variables:

```bash
# Wallet configuration
export WALLET_ADDRESS=YOUR_DOGE_WALLET_ADDRESS
export WORKER_NAME=worker01

# Economic settings
export ELECTRICITY_COST_KWH=0.12
export MAX_POWER_COST=0.12

# Pool configuration
export POOL_URL=stratum+tcp://doge.zsolo.bid:8057
export POOL_USERNAME=YOUR_WALLET_ADDRESS
export POOL_password=os.getenv("POOL_PASSWORD", "x")"POOL_PASSWORD", "x")

# Security settings
export ENABLE_ENCRYPTION=true
export RATE_LIMITING_ENABLED=true
```

### Configuration File Structure

```yaml
default:
  environment: production
  mining:
    algorithm: scrypt
    threads: auto
    intensity: auto
  pools:
    - url: stratum+tcp://primary.pool.com:3333
      username: YOUR_WALLET_ADDRESS
      password=os.getenv("POOL_PASSWORD", "x")"POOL_PASSWORD", "x")
      algorithm: scrypt
      priority: 1
    - url: stratum+tcp://backup.pool.com:3333
      username: YOUR_WALLET_ADDRESS
      password=os.getenv("POOL_PASSWORD", "x")"POOL_PASSWORD", "x")
      algorithm: scrypt
      priority: 2
  hardware:
    type: asic  # or gpu
    device_ids: []
    temperature_limit: 80
  economic:
    enabled: true
    max_power_cost: 0.12
    min_profitability: 0.01
    shutdown_on_unprofitable: true
    profitability_check_interval: 300
  security:
    enable_encryption: true
    rate_limiting_enabled: true
    max_requests_per_minute: 60
    enable_ddos_protection: true
  monitoring:
    enabled: true
    metrics_port: 8080
    health_check_port: 8081
    enable_prometheus: true
  logging:
    level: INFO
    file_path: logs/mining.log
```

## Hardware Setup

### ASIC Hardware Configuration

For ASIC miners, ensure the following:

1. **Network Connectivity**: ASIC devices must be accessible on the network
2. **API Access**: Enable API access on ASIC devices
3. **Firmware**: Update to the latest firmware version
4. **Cooling**: Ensure adequate cooling and ventilation

### GPU Hardware Configuration

For GPU mining, ensure the following:

1. **NVIDIA Drivers**: Install latest NVIDIA drivers
2. **CUDA Toolkit**: Install CUDA toolkit for GPU acceleration
3. **OpenCL**: Install OpenCL runtime for Scrypt mining
4. **Power Supply**: Ensure adequate power supply capacity

## Monitoring and Observability

### Prometheus Integration

The system exposes Prometheus metrics at `/metrics` endpoint:

```bash
# Add to prometheus.yml
scrape_configs:
  - job_name: 'scrypt-doge-miner'
    static_configs:
      - targets: ['localhost:8080']
```

### Grafana Dashboards

Import the provided Grafana dashboard:
```bash
# Import dashboard.json from monitoring/grafana/
curl -X POST \
  -H "Content-Type: application/json" \
  -d @monitoring/grafana/dashboard.json \
  http://grafana:3000/api/dashboards/db
```

### Log Management

Logs are written to `logs/mining.log` by default. For production environments, consider:

1. **Log Rotation**: Configure log rotation to prevent disk space issues
2. **Centralized Logging**: Use ELK stack or similar for centralized log management
3. **Alerting**: Set up alerts for critical log events

## Security Considerations

### Network Security

1. **Firewall**: Restrict access to only necessary ports
2. **TLS**: Enable TLS for all external communications
3. **VPN**: Use VPN for remote management access

### Access Control

1. **API Keys**: Use strong, unique API keys
2. **IP Whitelisting**: Restrict API access to trusted IP addresses
3. **Rate Limiting**: Enable rate limiting to prevent abuse

### Data Protection

1. **Encryption**: Enable encryption for sensitive data
2. **Backups**: Regularly backup configuration and wallet data
3. **Updates**: Keep system updated with latest security patches

## Performance Tuning

### CPU Optimization

1. **Thread Count**: Adjust thread count based on CPU cores
2. **Affinity**: Set CPU affinity for optimal performance
3. **Scheduling**: Use real-time scheduling for mining processes

### GPU Optimization

1. **Memory**: Allocate sufficient GPU memory
2. **Clocks**: Optimize GPU clocks and voltage
3. **Cooling**: Monitor GPU temperature and adjust accordingly

### Network Optimization

1. **Pool Selection**: Choose geographically close pools
2. **Connection**: Use persistent connections
3. **Bandwidth**: Ensure sufficient network bandwidth

## Troubleshooting

### Common Issues

#### 1. Connection Failures
```bash
# Check pool connectivity
telnet doge.zsolo.bid 8057

# Check firewall settings
sudo ufw status

# Check DNS resolution
nslookup doge.zsolo.bid
```

#### 2. Low Hashrate
```bash
# Check system resources
htop

# Check GPU utilization
nvidia-smi

# Check hardware temperatures
sensors
```

#### 3. High Rejection Rate
```bash
# Check share statistics
curl http://localhost:8080/api/v1/mining/status

# Check pool configuration
cat config/mining_config.yaml
```

### Log Analysis

Check logs for common error patterns:
```bash
# View recent errors
tail -f logs/mining.log | grep ERROR

# Search for specific errors
grep "connection failed" logs/mining.log
```

### Performance Monitoring

Monitor system performance:
```bash
# Monitor CPU usage
top

# Monitor GPU usage
nvidia-smi -l 1

# Monitor network usage
iftop
```

## Maintenance

### Regular Tasks

1. **Updates**: Regularly update the mining software
2. **Monitoring**: Continuously monitor system performance
3. **Backups**: Regularly backup configuration and wallet data
4. **Cleaning**: Clean dust from hardware components

### System Updates

```bash
# Update from Git
git pull origin main
pip install -r requirements.txt

# Update Docker image
docker pull your-org/scrypt-doge-miner:latest
docker restart scrypt-doge-miner
```

### Log Rotation

Configure log rotation in `/etc/logrotate.d/scrypt-doge`:
```
/home/user/scrypt-doge/logs/*.log {
    daily
    rotate 30
    compress
    delaycompress
    missingok
    notifempty
    create 644 user user
}
```

## Backup and Recovery

### Configuration Backup

```bash
# Backup configuration
tar -czf scrypt-doge-backup-$(date +%Y%m%d).tar.gz config/

# Restore configuration
tar -xzf scrypt-doge-backup-20250906.tar.gz
```

### Wallet Backup

Ensure wallet addresses are backed up in multiple secure locations.

### Disaster Recovery

1. **Documentation**: Maintain detailed system documentation
2. **Procedures**: Document recovery procedures
3. **Testing**: Regularly test backup and recovery procedures

## Scaling

### Horizontal Scaling

Deploy multiple instances for increased capacity:
```bash
# Run multiple instances with different configurations
python main.py --config config/instance1.yaml
python main.py --config config/instance2.yaml
```

### Load Balancing

Use load balancers for distributing work:
```bash
# Example HAProxy configuration
backend mining-pools
    balance roundrobin
    server pool1 doge.zsolo.bid:8057 check
    server pool2 backup.pool.com:3333 check
```

### Cluster Deployment

Use Kubernetes for cluster deployment:
```bash
# Scale deployment
kubectl scale deployment scrypt-doge-miner --replicas=3 -n mining

# Update configuration
kubectl set env deployment/scrypt-doge-miner WALLET_ADDRESS=new_address -n mining
```

## Support

For support, please check:

1. **Documentation**: Review this documentation thoroughly
2. **Issues**: Check GitHub issues for known problems
3. **Community**: Join the community forums
4. **Commercial**: Contact commercial support for enterprise deployments

## Changelog

### v1.0.0
- Initial release
- Basic mining functionality
- Stratum protocol support
- Configuration management

### v1.1.0
- Added GPU mining support
- Improved performance monitoring
- Enhanced security features

### v1.2.0
- Added Kubernetes support
- Improved economic safeguards
- Enhanced logging and alerting

For the latest updates, check the GitHub repository.
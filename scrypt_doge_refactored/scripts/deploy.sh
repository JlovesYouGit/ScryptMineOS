#!/bin/bash

# Scrypt DOGE Mining System Deployment Script

set -e

echo "Starting deployment of Scrypt DOGE Mining System..."

# Check if running as root (for systemd installation)
if [[ $EUID -eq 0 ]]; then
   echo "This script should not be run as root" 
   exit 1
fi

# Create installation directory
INSTALL_DIR="/opt/scrypt-miner"
echo "Creating installation directory: $INSTALL_DIR"
sudo mkdir -p $INSTALL_DIR

# Copy files
echo "Copying files to installation directory..."
sudo cp -r ./* $INSTALL_DIR/
sudo chown -R $USER:$USER $INSTALL_DIR

# Create virtual environment
echo "Creating virtual environment..."
cd $INSTALL_DIR
python3 -m venv venv
source venv/bin/activate

# Install dependencies
echo "Installing dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

# Create logs directory
mkdir -p logs

# Create configuration directory and copy default config
mkdir -p config
if [ ! -f "config/mining_config.yaml" ]; then
    echo "Creating default configuration..."
    cat > config/mining_config.yaml << EOF
default:
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
      timeout: 30
      retry_attempts: 3
      enable_tls: false
  
  hardware:
    type: asic
    device_ids: []
    power_limit: null
    temperature_limit: 80
    fan_speed: null
    frequency: null
    voltage: null
  
  economic:
    enabled: true
    max_power_cost: 0.12
    min_profitability: 0.01
    shutdown_on_unprofitable: true
    profitability_check_interval: 300
    wallet_address: YOUR_WALLET_ADDRESS
    auto_withdrawal_threshold: 0.01
  
  security:
    enable_encryption: true
    wallet_encryption_key: null
    rate_limiting_enabled: true
    max_requests_per_minute: 60
    enable_ddos_protection: true
    tls_verify: true
    allowed_ips:
      - 127.0.0.1
  
  monitoring:
    enabled: true
    metrics_port: 8080
    health_check_port: 8081
    enable_prometheus: true
    enable_grafana: false
    alert_webhook: null
    log_performance_metrics: true
  
  performance:
    auto_tune_enabled: true
    benchmark_interval: 3600
    hash_rate_optimization: true
    power_optimization: true
    thermal_throttling_enabled: true
    max_temperature: 85
  
  logging:
    level: INFO
    format: "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    file_path: logs/mining.log
    max_file_size: 10485760
    backup_count: 5
    enable_structured_logging: true
    enable_console: true

production:
  logging:
    level: WARNING
    file_path: /var/log/mining/mining.log
EOF
fi

# Set up systemd service (if on Linux)
if [[ "$OSTYPE" == "linux-gnu"* ]]; then
    echo "Setting up systemd service..."
    sudo cp scrypt-miner.service /etc/systemd/system/
    sudo systemctl daemon-reload
    echo "To start the service, run: sudo systemctl start scrypt-miner"
    echo "To enable auto-start on boot, run: sudo systemctl enable scrypt-miner"
fi

echo "Deployment completed successfully!"
echo "Please edit config/mining_config.yaml with your wallet address and other settings."
echo "Logs will be written to: $INSTALL_DIR/logs/"
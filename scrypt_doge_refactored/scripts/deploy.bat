@echo off
:: Scrypt DOGE Mining System Deployment Script for Windows

echo Starting deployment of Scrypt DOGE Mining System...

:: Set installation directory
set INSTALL_DIR=C:\scrypt-miner
echo Creating installation directory: %INSTALL_DIR%
if not exist "%INSTALL_DIR%" mkdir "%INSTALL_DIR%"

:: Copy files
echo Copying files to installation directory...
xcopy /E /I /Y . "%INSTALL_DIR%"

:: Create virtual environment
echo Creating virtual environment...
cd /d "%INSTALL_DIR%"
python -m venv venv
call venv\Scripts\activate.bat

:: Install dependencies
echo Installing dependencies...
pip install --upgrade pip
pip install -r requirements.txt

:: Create logs directory
if not exist "logs" mkdir logs

:: Create configuration directory and copy default config
if not exist "config" mkdir config
if not exist "config\mining_config.yaml" (
    echo Creating default configuration...
    echo default: > config\mining_config.yaml
    echo   environment: production >> config\mining_config.yaml
    echo   mining: >> config\mining_config.yaml
    echo     algorithm: scrypt >> config\mining_config.yaml
    echo     threads: auto >> config\mining_config.yaml
    echo     intensity: auto >> config\mining_config.yaml
    echo   pools: >> config\mining_config.yaml
    echo     - url: stratum+tcp://doge.zsolo.bid:8057 >> config\mining_config.yaml
    echo       username: YOUR_WALLET_ADDRESS >> config\mining_config.yaml
    echo       password: x >> config\mining_config.yaml
    echo       algorithm: scrypt >> config\mining_config.yaml
    echo       priority: 1 >> config\mining_config.yaml
    echo       timeout: 30 >> config\mining_config.yaml
    echo       retry_attempts: 3 >> config\mining_config.yaml
    echo       enable_tls: false >> config\mining_config.yaml
    echo   hardware: >> config\mining_config.yaml
    echo     type: asic >> config\mining_config.yaml
    echo     device_ids: [] >> config\mining_config.yaml
    echo     power_limit: null >> config\mining_config.yaml
    echo     temperature_limit: 80 >> config\mining_config.yaml
    echo     fan_speed: null >> config\mining_config.yaml
    echo     frequency: null >> config\mining_config.yaml
    echo     voltage: null >> config\mining_config.yaml
    echo   economic: >> config\mining_config.yaml
    echo     enabled: true >> config\mining_config.yaml
    echo     max_power_cost: 0.12 >> config\mining_config.yaml
    echo     min_profitability: 0.01 >> config\mining_config.yaml
    echo     shutdown_on_unprofitable: true >> config\mining_config.yaml
    echo     profitability_check_interval: 300 >> config\mining_config.yaml
    echo     wallet_address: YOUR_WALLET_ADDRESS >> config\mining_config.yaml
    echo     auto_withdrawal_threshold: 0.01 >> config\mining_config.yaml
    echo   security: >> config\mining_config.yaml
    echo     enable_encryption: true >> config\mining_config.yaml
    echo     wallet_encryption_key: null >> config\mining_config.yaml
    echo     rate_limiting_enabled: true >> config\mining_config.yaml
    echo     max_requests_per_minute: 60 >> config\mining_config.yaml
    echo     enable_ddos_protection: true >> config\mining_config.yaml
    echo     tls_verify: true >> config\mining_config.yaml
    echo     allowed_ips: >> config\mining_config.yaml
    echo       - 127.0.0.1 >> config\mining_config.yaml
    echo   monitoring: >> config\mining_config.yaml
    echo     enabled: true >> config\mining_config.yaml
    echo     metrics_port: 8080 >> config\mining_config.yaml
    echo     health_check_port: 8081 >> config\mining_config.yaml
    echo     enable_prometheus: true >> config\mining_config.yaml
    echo     enable_grafana: false >> config\mining_config.yaml
    echo     alert_webhook: null >> config\mining_config.yaml
    echo     log_performance_metrics: true >> config\mining_config.yaml
    echo   performance: >> config\mining_config.yaml
    echo     auto_tune_enabled: true >> config\mining_config.yaml
    echo     benchmark_interval: 3600 >> config\mining_config.yaml
    echo     hash_rate_optimization: true >> config\mining_config.yaml
    echo     power_optimization: true >> config\mining_config.yaml
    echo     thermal_throttling_enabled: true >> config\mining_config.yaml
    echo     max_temperature: 85 >> config\mining_config.yaml
    echo   logging: >> config\mining_config.yaml
    echo     level: INFO >> config\mining_config.yaml
    echo     format: "%%(asctime)s - %%(name)s - %%(levelname)s - %%(message)s" >> config\mining_config.yaml
    echo     file_path: logs/mining.log >> config\mining_config.yaml
    echo     max_file_size: 10485760 >> config\mining_config.yaml
    echo     backup_count: 5 >> config\mining_config.yaml
    echo     enable_structured_logging: true >> config\mining_config.yaml
    echo     enable_console: true >> config\mining_config.yaml
    echo production: >> config\mining_config.yaml
    echo   logging: >> config\mining_config.yaml
    echo     level: WARNING >> config\mining_config.yaml
    echo     file_path: logs/mining.log >> config\mining_config.yaml
)

echo Deployment completed successfully!
echo Please edit config\mining_config.yaml with your wallet address and other settings.
echo Logs will be written to: %INSTALL_DIR%\logs\
echo To run the miner, execute: python main.py
pause
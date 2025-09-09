# Byterover MCP Handbook - Scrypt ASIC Mining Suite

## Layer 1: System Overview

### Purpose
Professional Scrypt ASIC mining implementation optimized for Antminer L7 and compatible ASICs with F2Pool merged mining support. Designed for production-scale mining operations (≥200 MH/s) with revenue optimization through merged mining of LTC + DOGE + 8 auxiliary coins.

### Technology Stack
- **Core Language**: Python 3.11+ 
- **Mining Framework**: PyOpenCL for GPU computation, Enhanced Stratum V1/V2 client
- **Key Dependencies**: numpy, pyopencl, requests, prometheus_client, Jinja2, pyasic, cryptography, aiohttp, psutil, PyYAML, decouple
- **Hardware Integration**: ASIC monitoring APIs (pyasic), OpenCL compute kernels, GPU vendor tools (rocm-smi, nvidia-smi)
- **Monitoring**: Prometheus metrics, Grafana dashboards, Comprehensive Stratum monitoring
- **Pool Protocol**: Enhanced Stratum V1/V2 with extraNonce handling, difficulty management, and security validation
- **Security**: Encryption (cryptography), Rate limiting, DDoS protection
- **Economic Analysis**: CoinGecko API integration, real-time market data

### Architecture Pattern
**Modular Mining Architecture** with separation of concerns:
- **Core Layer**: Main mining service, configuration management
- **Network Layer**: Enhanced Stratum protocol client for pool communication with advanced features
- **Hardware Layer**: ASIC monitoring, temperature, and power control
- **Economic Layer**: Profitability analysis and auto-switching
- **Security Layer**: Encryption, rate limiting, DDoS protection
- **Monitoring Layer**: System metrics, health checks, logging
- **Optimization Layer**: Performance tuning, hybrid mining

### Key Technical Decisions
- Educational Mode for safe development without real mining
- Merged mining implementation for 30-40% revenue increase
- ASIC virtualization for hardware emulation during development
- Performance optimization targeting 1.3-1.4x profit improvement
- Enhanced Stratum protocol with advanced difficulty management, security validation, and monitoring
- Circuit breaker pattern for resilient pool connections
- Comprehensive security with encryption and protection mechanisms
- GPU-ASIC hybrid layer for making GPUs externally indistinguishable from professional ASICs
- Real-time profitability calculation using live market data
- Dependency injection through service container for better modularity
- Centralized configuration management with environment variable support

## Layer 2: Module Map

### Core Modules

#### Mining Service (`scrypt_doge_refactored/core/mining_service.py`)
- **Responsibility**: Main mining service with proper lifecycle management
- **Key Functions**: `initialize()`, `connect_to_pool()`, `start_mining()`, `stop()`
- **Dependencies**: Enhanced Stratum client, performance optimizer, hardware interfaces
- **Performance Target**: 9.5 GH/s on Antminer L7

#### Configuration Management (`scrypt_doge_refactored/core/config_manager.py`)
- **Responsibility**: Unified configuration with environment variables, validation, and hot-reload
- **Key Functions**: `load_config()`, `save_config()`, `get_config()`
- **Integration**: YAML configuration files, environment variables

#### Service Container (`scrypt_doge_refactored/core/service_container.py`)
- **Responsibility**: Dependency injection container for service management
- **Key Features**: Singleton and transient service registration, dependency resolution, lifecycle management
- **Key Classes**: `ServiceContainer`, `ServiceInfo`
- **Functions**: `register_singleton()`, `register_transient()`, `resolve()`, `initialize_all()`

### Hardware Modules

#### ASIC Interface (`scrypt_doge_refactored/hardware/asic_interface.py`)
- **Responsibility**: ASIC hardware interface using pyasic library
- **Key Functions**: `connect()`, `disconnect()`, `start_mining()`, `get_stats()`
- **Integration**: pyasic library for real hardware control

#### Hardware Manager (`scrypt_doge_refactored/hardware/asic_interface.py`)
- **Responsibility**: Manages multiple hardware devices
- **Key Functions**: `add_device()`, `start_all()`, `stop_all()`, `get_total_hashrate()`

#### GPU-ASIC Hybrid Layer (`scrypt_doge_refactored/hardware/gpu_asic_hybrid.py`)
- **Responsibility**: Makes 50 MH/s GPU externally indistinguishable from 9.5 GH/s Antminer L7
- **Key Features**: ASIC-like voltage/frequency domains, thermal mass simulation, nonce error injection, identical JSON API endpoints
- **Key Classes**: `GPUASICHybrid`, `ThermalRC`, `ASICFaultInjector`, `ASICAPIMimicry`
- **Integration**: HTTP API mimicking Antminer L7 endpoints

### Economic Modules

#### Economic Guardian (`scrypt_doge_refactored/security/economic_guardian.py`)
- **Responsibility**: Real-time profitability monitoring and automatic shutdown
- **Key Functions**: `start_monitoring()`, `stop_monitoring()`, `is_mining_profitable()`
- **Safety Features**: Kill-switch at configurable profit margin, electricity cost monitoring

#### Profitability Calculator (`scrypt_doge_refactored/core/profitability_calculator.py`)
- **Responsibility**: Calculate real mining profitability using live market data
- **Key Features**: CoinGecko API integration, network stats calculation, break-even analysis
- **Key Classes**: `RealProfitabilityCalculator`, `ProfitabilityResult`, `CoinPrice`
- **Integration**: Live cryptocurrency price data from CoinGecko

### Performance Modules

#### Performance Optimization (`scrypt_doge_refactored/optimization/performance_optimizer.py`)
- **Responsibility**: Systematic GPU performance optimization targeting 1.0 MH/J efficiency
- **Key Features**: 5-step optimization roadmap, GPU vendor detection, power/thermal monitoring
- **Key Classes**: `GPUPerformanceOptimizer`, `PerformanceMetrics`
- **Optimization Steps**: Baseline measurement, L2-resident kernel, voltage-frequency tuning, clock gating, merged mining bonus

#### GPU-ASIC Hybrid Layer (`scrypt_doge_refactored/hardware/gpu_asic_hybrid.py`)
- **Responsibility**: Makes 50 MH/s GPU externally indistinguishable from 9.5 GH/s Antminer L7
- **Key Features**: ASIC-like voltage/frequency domains, thermal mass simulation, nonce error injection, identical JSON API endpoints
- **Key Classes**: `GPUASICHybrid`, `ThermalRC`, `ASICFaultInjector`, `ASICAPIMimicry`
- **Integration**: HTTP API mimicking Antminer L7 endpoints

### Data Layer
#### Constants (`scrypt_doge_refactored/config/constants.py`)
- **Configuration**: Pool endpoints, wallet addresses, performance thresholds
- **Constants**: System constants, mining parameters, network settings, algorithm parameters
- **Environment Integration**: decouple library for environment variable management
- **Key Classes**: `SystemConstants`, `MiningConstants`, `NetworkConstants`, `AlgorithmConstants`
- **Enums**: `MiningMode`, `PoolRegion`

#### Configuration Management (`scrypt_doge_refactored/core/config_manager.py`)
- **Settings**: Pool configuration, wallet addresses, worker names
- **Environment**: Regional pool optimization, SSL settings, multiple environment support
- **Features**: YAML configuration files, environment variable overrides, hot-reload
- **Key Classes**: `ConfigManager`, `Config`, `PoolConfig`, `HardwareConfig`, `EconomicConfig`
- **Advanced Features**: Configuration validation, async loading, environment-specific overrides

### Network Layer (Enhanced Stratum Modules)
#### Stratum Client (`scrypt_doge_refactored/network/stratum_client.py`)
- **Responsibility**: Enhanced Stratum V1/V2 protocol implementation with robust connection handling
- **Key Features**: Automatic reconnection, SSL support, protocol version compatibility
- **Classes**: `EnhancedStratumClient`, `StratumConfig`, `StratumJob`
- **Advanced Features**: Security validation, monitoring, difficulty management

#### Pool Manager (`scrypt_doge_refactored/network/pool_manager.py`)
- **Responsibility**: Circuit breaker pattern for resilient pool connections
- **Key Classes**: 
  - `PoolFailoverManager`: Manages multiple pool connections with failover
  - `CircuitBreaker`: Circuit breaker pattern implementation
  - `PoolConnection`: Pool connection details and statistics

#### Stratum Protocol (`scrypt_doge_refactored/network/stratum_protocol.py`)
- **Responsibility**: Core Stratum protocol implementation
- **Key Classes**: 
  - `DifficultyManager`: Advanced difficulty management with auto-adjustment
  - `ExtranonceManager`: Enhanced extranonce handling
  - `ConnectionManager`: Robust connection management

### Security Layer

#### Security Manager (`scrypt_doge_refactored/security/security_manager.py`)
- **Responsibility**: Comprehensive security features and validation
- **Key Classes**:
  - `SecurityManager`: Main security manager coordinating all security features
  - `EncryptionManager`: Encryption and decryption of sensitive data
  - `RateLimiter`: Rate limiting to prevent abuse
  - `DDoSProtection`: DDoS protection mechanisms
  - `InputValidator`: Validates and sanitizes input data
- **Features**: Encryption, rate limiting, DDoS protection, input validation

### Monitoring Layer

#### System Monitor (`scrypt_doge_refactored/monitoring/system_monitor.py`)
- **Responsibility**: Comprehensive logging, metrics collection, and health checking
- **Key Classes**:
  - `SystemMonitor`: Main system monitoring class
  - `MetricsCollector`: Collects and stores system metrics
  - `JsonLogger`: Structured JSON logging
  - `HealthStatus`: Overall system health status
- **Features**: CPU/memory monitoring, network I/O tracking, health checks

### Utilities
#### Unified Code Quality System (`pyfix.py`, `PYFIX_UNIVERSAL.bat`)
- **Responsibility**: Universal Python code quality enforcement and fixing
- **Functions**: `pyfix()`, `format_code()`, `lint_code()`, `security_scan()`, `audit_dependencies()`, `clean_cache()`
- **Features**: Unified code quality solution
- **Performance**: 90% faster execution using Rust-based ruff + bandit + pip-audit
- **Modes**: Full workflow, format-only, security-only, quiet mode

#### Testing & Monitoring (`test_*.py`, `asic_monitor.py`)
- **Testing**: Educational mode verification, F2Pool connection tests
- **Monitoring**: Real-time metrics, Prometheus integration

## Layer 3: Integration Guide

### Mining Pool APIs
#### F2Pool Stratum V1 Endpoints
```python
# Regional endpoints for optimal latency
POOLS = {
    "global": "ltc.f2pool.com:3335",
    "europe": "ltc-euro.f2pool.com:3335", 
    "north_america": "ltc-na.f2pool.com:3335",
    "asia": "ltc-asia.f2pool.com:3335"
}
```

#### Worker Authentication Format
```python
worker_format = f"{LTC_WALLET}.{DOGE_WALLET}.{WORKER_NAME}"
# Example: "LBK8KmLvPZ5YtKjqZAKkKqFHfpQzCQP6N3.DGKsuHU6XdghZtA2aWGqvrZrkWracQJzPd.rig01"
```

#### Enhanced Stratum Client Usage
```python
# Enhanced Stratum client with advanced features
from scrypt_doge_refactored.network.stratum_client import EnhancedStratumClient
from scrypt_doge_refactored.monitoring.system_monitor import SystemMonitor
from scrypt_doge_refactored.security.security_manager import SecurityManager

# Configuration
config = {
    "pool_host": "doge.zsolo.bid",
    "pool_port": 8057,
    "wallet_address": "your_wallet_address",
    "worker_password": "x"
}

# Initialize enhanced client
client = EnhancedStratumClient(
    host=config["pool_host"],
    port=config["pool_port"],
    user=config["wallet_address"],
    password=config["worker_password"]
)
monitor = SystemMonitor()
security = SecurityManager()

# Connect and authenticate
if client.connect():
    if client.subscribe_and_authorize():
        # Listen for jobs with enhanced monitoring and security
        while client.connected:
            message = client.receive_message()
            if message:
                if "method" in message:
                    client.handle_notification(message)
                    monitor.record_job_received()
```

### Hardware APIs
#### ASIC Monitoring Interface
```python
# Prometheus metrics endpoint
asic_metrics = {
    "asic_temp_celsius": "Board temperature",
    "asic_power_watts": "Real-time power consumption", 
    "asic_hash_gh": "Total hashrate in GH/s",
    "asic_accept_rate_percent": "Share acceptance rate",
    "asic_chain_count": "Active mining chains"
}
```

#### OpenCL Kernel Interface
```glsl
// scrypt_kernel.comp - Compute shader for GPU mining
layout(local_size_x = 256, local_size_y = 1, local_size_z = 1) in;
// Input/output buffers for Scrypt algorithm
layout(binding = 0) buffer InputBuffer { uint data[]; };
```

### Code Quality APIs
#### Unified Python Quality Workflow
```python
# Universal code quality command
python pyfix.py [folder]              # Full workflow
python pyfix.py --format-only         # Format only (30s)
python pyfix.py --security-only       # Security only
python pyfix.py --quiet               # Silent mode

# PowerShell integration
pyfix [folder] [-SecurityOnly|-FormatOnly] [-Quiet]

# What it replaces:
# - black, isort, flake8, pylint (now: ruff)
# - bandit (security scanning)
# - pip-audit (dependency vulnerabilities)  
# - pyclean (cache cleanup)
# - Fragmented code quality tools
```

#### Pre-commit Integration
```yaml
# .pre-commit-config.yaml - Updated workflow
repos:
  - repo: https://github.com/astral-sh/ruff-pre-commit
    hooks:
      - id: ruff          # Linting (replaces flake8)
      - id: ruff-format   # Formatting (replaces black + isort)
  - repo: https://github.com/PyCQA/bandit
    hooks:
      - id: bandit        # Security scanning
```

### External Dependencies
- **F2Pool**: Primary mining pool with merged mining support
- **OpenCL**: GPU compute framework for mining kernels
- **Prometheus**: Metrics collection and monitoring
- **Hardware APIs**: ASIC manufacturer interfaces (Antminer, etc.)
- **CoinGecko API**: Real-time cryptocurrency price data
- **GPU Vendor Tools**: rocm-smi (AMD) and nvidia-smi (NVIDIA) for hardware control
- **YAML**: Configuration file parsing
- **Decouple**: Environment variable management

## Layer 4: Extension Points

### Mining Algorithm Extensions
#### Custom Scrypt Variants
```python
# Extension point in runner.py
def calculate_hash(data, algorithm="scrypt"):
    if algorithm == "scrypt_n":
        return scrypt_n_implementation(data)
    elif algorithm == "scrypt_jane":
        return scrypt_jane_implementation(data)
    # Default scrypt implementation
```

#### Alternative Pool Protocols
```python
# Stratum V2 extension point
class StratumV2Client(StratumClient):
    def handle_v2_message(self, message):
        # Implement Stratum V2 protocol extensions
        pass
```

### Hardware Abstraction Extensions
#### Multi-ASIC Support
```python
# asic_virtualization.py extension pattern
class ASICFleetManager:
    def __init__(self, asic_configs):
        self.asics = [ASICController(config) for config in asic_configs]
    
    def distribute_work(self, job):
        # Load balancing across multiple ASICs
        pass
```

#### Custom Hardware Interfaces
```python
# Hardware plugin system
def register_hardware_plugin(manufacturer, controller_class):
    HARDWARE_PLUGINS[manufacturer] = controller_class
```

### Economic Strategy Extensions
#### Custom Profitability Models
```python
# economic_guardian.py extension point
class CustomProfitabilityModel:
    def calculate_profit_margin(self, hashrate, power, electricity_cost):
        # Implement custom profit calculations
        pass
```

#### Alternative Switching Strategies
```python
# profit_switcher.py extension patterns
SWITCHING_STRATEGIES = {
    "conservative": ConservativeSwitcher,
    "aggressive": AggressiveSwitcher,
    "custom": CustomSwitcher
}
```

### Network Layer Extensions
#### Advanced Difficulty Management
```python
# stratum_enhanced.py extension point
class CustomDifficultyManager(DifficultyManager):
    def adjust_difficulty(self, accepted_shares, rejected_shares, time_window=60):
        # Implement custom difficulty adjustment algorithm
        pass
```

#### Security Validation Extensions
```python
# stratum_security.py extension point
class CustomSecurityValidator(StratumSecurityValidator):
    def validate_message(self, message):
        # Implement additional security checks
        pass
```

### Performance Optimization Patterns
#### Algorithm-Specific Optimizations
- **Factory Pattern**: Different optimization strategies per ASIC model
- **Observer Pattern**: Real-time performance monitoring and adjustment
- **Command Pattern**: Reversible optimization operations
- **Strategy Pattern**: Pluggable profitability calculation methods

#### GPU Performance Optimization
- **5-Step Roadmap**: Systematic approach to maximize hash-rate per watt (H/J)
- **Vendor Detection**: Automatic detection of AMD/NVIDIA GPUs for platform-specific optimizations
- **Thermal Simulation**: RC circuit simulation for realistic thermal mass modeling
- **Clock Gating**: Dynamic clock gating during memory-bound phases
- **Voltage Tuning**: Voltage-frequency curve optimization for power reduction

### Recent Customization Areas
1. **Merged Mining Extensions**: Support for additional auxiliary coins
2. **Regional Pool Optimization**: Automatic latency-based pool selection  
3. **Hardware-Specific Tuning**: Per-ASIC-model optimization profiles
4. **Economic Safety Enhancements**: Advanced profit margin protection
5. **Educational Mode Features**: Safe development environment expansions
6. **Enhanced Stratum Protocol**: Advanced difficulty management, security validation, and monitoring
7. **GPU-ASIC Hybrid Layer**: Making GPUs externally indistinguishable from professional ASICs
8. **Real-Time Profitability Calculation**: Using live market data from CoinGecko API
9. **Performance Optimization**: Systematic GPU performance optimization targeting 1.0 MH/J efficiency
10. **Dependency Injection**: Service container for better modularity and testability
# Byterover MCP Handbook - Scrypt ASIC Mining Suite

## Layer 1: System Overview

### Purpose
Professional Scrypt ASIC mining implementation optimized for Antminer L7 and compatible ASICs with F2Pool merged mining support. Designed for production-scale mining operations (≥200 MH/s) with revenue optimization through merged mining of LTC + DOGE + 8 auxiliary coins.

### Technology Stack
- **Core Language**: Python 3.11+ 
- **Mining Framework**: PyOpenCL for GPU computation, Enhanced Stratum V1/V2 client
- **Key Dependencies**: numpy, pyopencl, requests, prometheus_client, Jinja2
- **Hardware Integration**: ASIC monitoring APIs, OpenCL compute kernels
- **Monitoring**: Prometheus metrics, Grafana dashboards, Comprehensive Stratum monitoring
- **Pool Protocol**: Enhanced Stratum V1/V2 with extraNonce handling, difficulty management, and security validation

### Architecture Pattern
**Modular Mining Architecture** with separation of concerns:
- **Mining Core**: OpenCL kernel execution and hash computation
- **Network Layer**: Enhanced Stratum protocol client for pool communication with advanced features
- **Hardware Layer**: ASIC monitoring, temperature, and power control
- **Economic Layer**: Profitability analysis and auto-switching
- **Safety Layer**: Economic guardian with kill-switch functionality and Stratum security validation

### Key Technical Decisions
- Educational Mode for safe development without real mining
- Merged mining implementation for 30-40% revenue increase
- ASIC virtualization for hardware emulation during development
- Performance optimization targeting 1.3-1.4x profit improvement
- Enhanced Stratum protocol with advanced difficulty management, security validation, and monitoring

## Layer 2: Module Map

### Core Modules

#### Mining Engine (`runner.py`, `runner_fixed.py`, `stratum_integration_example.py`)
- **Responsibility**: Main mining loop, OpenCL kernel execution, Enhanced Stratum client
- **Key Functions**: `main()`, `mine_block()`, `calculate_hash()`, `handle_notification()`, `submit_share()`
- **Dependencies**: PyOpenCL, Enhanced Stratum client, mining constants
- **Performance Target**: 9.5 GH/s on Antminer L7

#### Hardware Abstraction (`asic_virtualization.py`, `asic_hardware_emulation.py`)
- **Responsibility**: ASIC hardware interface, temperature monitoring, power control
- **Key Functions**: `get_asic_stats()`, `set_voltage()`, `monitor_temperature()`
- **Integration**: Prometheus metrics, hardware control scripts

#### Economic Safety (`economic_guardian.py`, `profit_switcher.py`)
- **Responsibility**: Profitability monitoring, automatic mining termination
- **Key Functions**: `check_profitability()`, `emergency_shutdown()`
- **Safety Features**: Kill-switch at 5% profit margin, electricity cost monitoring

#### Performance Optimization (`performance_optimizer.py`, `gpu_asic_hybrid.py`)
- **Responsibility**: Voltage tuning, cooling optimization, hybrid mining
- **Key Functions**: `optimize_voltage()`, `tune_cooling()`, `hybrid_mining_mode()`
- **Targets**: -75W power reduction, same hashrate

### Data Layer
#### Mining Constants (`mining_constants.py`, `extracted_constants.py`)
- **Configuration**: Pool endpoints, wallet addresses, performance thresholds
- **Constants**: Temperature limits, power targets, optimization parameters

#### Configuration (`economic_config.py`, `.env.example`)
- **Settings**: Pool configuration, wallet addresses, worker names
- **Environment**: Regional pool optimization, SSL settings

### Network Layer (Enhanced Stratum Modules)
#### Stratum Client (`stratum_client.py`)
- **Responsibility**: Enhanced Stratum V1/V2 protocol implementation with robust connection handling
- **Key Features**: Automatic reconnection, SSL support, protocol version compatibility
- **Classes**: `StratumClient`, `StratumConfig`, `StratumJob`

#### Stratum Enhanced Utilities (`stratum_enhanced.py`)
- **Responsibility**: Advanced Stratum functionality and utility functions
- **Key Classes**: 
  - `DifficultyManager`: Advanced difficulty management with auto-adjustment
  - `StratumUtils`: Utility functions for merged mining and address validation
  - `ExtranonceManager`: Enhanced extranonce handling
  - `ConnectionManager`: Robust connection management
  - `StratumJobManager`: Job tracking and management

#### Stratum Monitoring (`stratum_monitoring.py`)
- **Responsibility**: Comprehensive monitoring and logging for Stratum operations
- **Key Classes**:
  - `StratumMonitor`: Main monitoring class with share and connection tracking
  - `ShareStats`: Share submission statistics
  - `ConnectionStats`: Connection health monitoring
  - `PerformanceMetrics`: Mining performance metrics
  - `JsonLogger`: Structured JSON logging

#### Stratum Security (`stratum_security.py`)
- **Responsibility**: Security features and validation for Stratum client operations
- **Key Classes**:
  - `StratumSecurityValidator`: Message validation and security checks
  - `SecurityConfig`: Security configuration settings
  - `SecureConnectionManager`: Secure connection handling

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
from stratum_client import StratumClient, StratumConfig, StratumVersion
from stratum_enhanced import DifficultyManager, ExtranonceManager
from stratum_monitoring import StratumMonitor
from stratum_security import StratumSecurityValidator

# Configuration
config = StratumConfig(
    host="ltc.f2pool.com",
    port=3335,
    username="your_username",
    password="x",
    version=StratumVersion.V1
)

# Initialize enhanced client
client = StratumClient(config)
monitor = StratumMonitor("worker_name")
security = StratumSecurityValidator()

# Connect and authenticate
if client.initialize():
    # Listen for jobs with enhanced monitoring and security
    while client.connected:
        message = client.receive_message()
        if message and security.validate_message(message):
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

### Recent Customization Areas
1. **Merged Mining Extensions**: Support for additional auxiliary coins
2. **Regional Pool Optimization**: Automatic latency-based pool selection  
3. **Hardware-Specific Tuning**: Per-ASIC-model optimization profiles
4. **Economic Safety Enhancements**: Advanced profit margin protection
5. **Educational Mode Features**: Safe development environment expansions
6. **Enhanced Stratum Protocol**: Advanced difficulty management, security validation, and monitoring
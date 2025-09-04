# Dogecoin Scrypt Miner

A Python-based scrypt miner for Dogecoin using OpenCL acceleration.

## Requirements

- Python 3.10+
- AMD GPU with OpenCL support
- AMD OpenCL runtime

## Installation

```bash
pip install -r requirements.txt
```

## Configuration

Edit pool credentials in your mining script or config file:

```bash
POOL_URL="stratum+tcp://YOUR_POOL_HOST:PORT"
WALLET_ADDRESS="YOUR_DOGE_WALLET_ADDRESS"
WORKER_NAME="YOUR_WORKER_NAME"
```

## Usage

```bash
python runner.py
```

## Dependencies

- Python 3.11.9 (verified)
- numpy==1.26.4
- Jinja2==3.1.4
- pyopencl==2025.2.6
- requests==2.32.5
- AMD OpenCL 2.1 (verified)

#!/bin/bash

# Mining OS Installation Script

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Functions
log() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if running as root
if [[ $EUID -eq 0 ]]; then
   error "This script should not be run as root"
   exit 1
fi

# Parse arguments
GPU_SUPPORT=false
while [[ $# -gt 0 ]]; do
    case $1 in
        --gpu)
            GPU_SUPPORT=true
            shift
            ;;
        *)
            error "Unknown option $1"
            exit 1
            ;;
    esac
done

# Check for PAYOUT_ADDR environment variable
if [[ -z "${PAYOUT_ADDR}" ]]; then
    error "PAYOUT_ADDR environment variable is not set!"
    echo "Please set your wallet address where mining rewards will be sent."
    echo "You must use either:"
    echo "  1. Your Litecoin address: ltc1qpptg85asckrjy9ygygh2tfgxqwzn6672zmzq99"
    echo "  2. Your Dogecoin address: DGKsuHU6XdghZtA2aWGqvrZrkWracQJzPd"
    echo ""
    echo "Example:"
    echo "  export PAYOUT_ADDR=ltc1qpptg85asckrjy9ygygh2tfgxqwzn6672zmzq99"
    echo "  ./install.sh"
    exit 1
fi

log "Starting Mining OS installation..."

# Check for NVIDIA drivers if GPU support is requested
if [ "$GPU_SUPPORT" = true ]; then
    log "Checking for NVIDIA drivers..."
    if ! command -v nvidia-smi &> /dev/null; then
        error "NVIDIA drivers not found. Please install NVIDIA drivers first."
        exit 1
    fi
    log "NVIDIA drivers found"
fi

# Create mining user
log "Creating mining user..."
if id "miner" &>/dev/null; then
    warn "User 'miner' already exists"
else
    sudo useradd --create-home --shell /bin/bash miner
    log "User 'miner' created"
fi

# Install dependencies
log "Installing system dependencies..."
sudo apt-get update
sudo apt-get install -y python3 python3-pip curl

# Create installation directory
INSTALL_DIR="/opt/mining-os"
log "Creating installation directory at $INSTALL_DIR..."
sudo mkdir -p $INSTALL_DIR
sudo chown $USER:$USER $INSTALL_DIR

# Copy files
log "Copying files..."
cp -r ./* $INSTALL_DIR/
cd $INSTALL_DIR

# Create virtual environment
log "Creating Python virtual environment..."
python3 -m venv venv
source venv/bin/activate

# Install Python dependencies
log "Installing Python dependencies..."
pip install --upgrade pip
pip install -r src/mining_os/requirements.txt

# Build frontend
log "Building frontend..."
cd frontend
npm ci
npm run build
cd ..

# Copy built frontend to static directory
cp -r frontend/dist/* src/mining_os/static/

# Set permissions
log "Setting permissions..."
sudo chown -R miner:miner $INSTALL_DIR

# Install systemd service
log "Installing systemd service..."
# Update the service file to include the PAYOUT_ADDR environment variable
sudo sed "s|Environment=ENV=prod|Environment=ENV=prod\nEnvironment=PAYOUT_ADDR=${PAYOUT_ADDR}|g" mining-os.service | sudo tee /etc/systemd/system/mining-os.service > /dev/null
sudo systemctl daemon-reload

# Enable service
log "Enabling Mining OS service..."
sudo systemctl enable mining-os

# Start service
log "Starting Mining OS service..."
sudo systemctl start mining-os

log "Installation complete!"
log "Mining OS is now running and will start automatically on boot"
log "Access the web interface at http://localhost:31415"
log "View logs with: sudo journalctl -u mining-os -f"
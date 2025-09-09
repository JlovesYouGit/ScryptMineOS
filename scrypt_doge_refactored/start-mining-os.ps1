# Mining OS Startup Script for Windows
# This script sets the PAYOUT_ADDR environment variable and starts the Mining OS

param(
    [Parameter(Mandatory=$false)]
    [string]$PayoutAddress = "",
    
    [Parameter(Mandatory=$false)]
    [switch]$UseDocker = $false
)

# Colors for output
$Green = "Green"
$Yellow = "Yellow"
$Red = "Red"

function Write-Log {
    param(
        [string]$Message,
        [string]$Color = "White"
    )
    Write-Host "[INFO] $Message" -ForegroundColor $Color
}

function Write-WarningLog {
    param([string]$Message)
    Write-Host "[WARN] $Message" -ForegroundColor $Yellow
}

function Write-ErrorLog {
    param([string]$Message)
    Write-Host "[ERROR] $Message" -ForegroundColor $Red
}

# Check if PAYOUT_ADDR is provided
if ([string]::IsNullOrEmpty($PayoutAddress)) {
    # Check if PAYOUT_ADDR is already set in environment
    $currentPayoutAddr = $env:PAYOUT_ADDR
    if ([string]::IsNullOrEmpty($currentPayoutAddr)) {
        Write-ErrorLog "PAYOUT_ADDR environment variable is not set!"
        Write-Host "Please provide your wallet address where mining rewards will be sent."
        Write-Host "You must use either:"
        Write-Host "  1. Your Litecoin address: ltc1qpptg85asckrjy9ygygh2tfgxqwzn6672zmzq99"
        Write-Host "  2. Your Dogecoin address: DGKsuHU6XdghZtA2aWGqvrZrkWracQJzPd"
        Write-Host ""
        Write-Host "Example:"
        Write-Host "  .\start-mining-os.ps1 -PayoutAddress `"ltc1qpptg85asckrjy9ygygh2tfgxqwzn6672zmzq99`""
        Write-Host "Or set the environment variable manually:"
        Write-Host "  `$env:PAYOUT_ADDR=`"ltc1qpptg85asckrjy9ygygh2tfgxqwzn6672zmzq99`""
        Write-Host "  .\start-mining-os.ps1"
        exit 1
    } else {
        $PayoutAddress = $currentPayoutAddr
        Write-Log "Using PAYOUT_ADDR from environment: $PayoutAddress" $Green
    }
} else {
    # Set the PAYOUT_ADDR environment variable
    $env:PAYOUT_ADDR = $PayoutAddress
    Write-Log "PAYOUT_ADDR set to: $PayoutAddress" $Green
}

# Verify the payout address is one of the valid addresses
$validAddresses = @(
    "ltc1qpptg85asckrjy9ygygh2tfgxqwzn6672zmzq99",
    "DGKsuHU6XdghZtA2aWGqvrZrkWracQJzPd"
)

if ($PayoutAddress -notin $validAddresses) {
    Write-WarningLog "PAYOUT_ADDR is not set to one of the valid addresses!"
    Write-Host "You must use either:"
    Write-Host "  1. Your Litecoin address: ltc1qpptg85asckrjy9ygygh2tfgxqwzn6672zmzq99"
    Write-Host "  2. Your Dogecoin address: DGKsuHU6XdghZtA2aWGqvrZrkWracQJzPd"
    exit 1
}

if ($UseDocker) {
    Write-Log "Starting Mining OS using Docker..." $Green
    
    # Check if Docker is installed and running
    try {
        $dockerVersion = docker --version
        Write-Log "Docker found: $dockerVersion" $Green
    } catch {
        Write-ErrorLog "Docker is not installed or not in PATH!"
        Write-Host "Please install Docker Desktop for Windows first."
        exit 1
    }
    
    # Start the Mining OS using Docker
    Write-Log "Running: docker compose up -d" $Green
    docker compose up -d
    
    if ($LASTEXITCODE -eq 0) {
        Write-Log "Mining OS started successfully with Docker!" $Green
        Write-Host "Access the web interface at http://localhost:31415"
    } else {
        Write-ErrorLog "Failed to start Mining OS with Docker!"
        exit 1
    }
} else {
    Write-Log "Starting Mining OS directly..." $Green
    
    # Check if Python is installed
    try {
        $pythonVersion = python --version
        Write-Log "Python found: $pythonVersion" $Green
    } catch {
        Write-ErrorLog "Python is not installed or not in PATH!"
        Write-Host "Please install Python 3.8 or higher first."
        exit 1
    }
    
    # Check if virtual environment exists
    if (-not (Test-Path "venv")) {
        Write-Log "Creating Python virtual environment..." $Yellow
        python -m venv venv
    }
    
    # Activate virtual environment
    Write-Log "Activating virtual environment..." $Yellow
    .\venv\Scripts\Activate.ps1
    
    # Install/update dependencies
    Write-Log "Installing Python dependencies..." $Yellow
    pip install --upgrade pip
    if (Test-Path "requirements.txt") {
        pip install -r requirements.txt
    } else {
        # Install from the mining OS directory
        pip install -r src\mining_os\requirements.txt
    }
    
    # Build frontend if needed
    if (Test-Path "frontend") {
        Set-Location frontend
        if (Test-Path "package.json") {
            Write-Log "Building frontend..." $Yellow
            if (Get-Command npm -ErrorAction SilentlyContinue) {
                npm ci
                npm run build
            } else {
                Write-WarningLog "npm not found, skipping frontend build"
            }
        }
        Set-Location ..
    }
    
    # Copy built frontend to static directory if it exists
    if (Test-Path "frontend\dist") {
        Write-Log "Copying built frontend to static directory..." $Yellow
        if (-not (Test-Path "src\mining_os\static")) {
            New-Item -ItemType Directory -Path "src\mining_os\static" -Force
        }
        Copy-Item -Path "frontend\dist\*" -Destination "src\mining_os\static" -Recurse -Force
    }
    
    # Start the Mining OS
    Write-Log "Starting Mining OS..." $Green
    python -m src.mining_os
    
    if ($LASTEXITCODE -eq 0) {
        Write-Log "Mining OS started successfully!" $Green
        Write-Host "Access the web interface at http://localhost:31415"
    } else {
        Write-ErrorLog "Failed to start Mining OS!"
        exit 1
    }
}
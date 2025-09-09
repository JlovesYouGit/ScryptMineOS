# Update Summary: Wallet Addresses and Pool Configuration

## Objective
Update the mining system to use the provided Litecoin and doeskin wallet addresses and pool endpoints:
- Litecoin wallet address: `ltc1qpptg85amcr9YGG2tfgxqwzn6672zmzq99`
- doeskin wallet address: `DGKsuHU6xdpiZtA2awaulZrkWracQJzPd`
- Litecoin pool: `stratum+tcp://ltc.f2pool.com:8888`
- doeskin pool: `stratum+tcp://doge.zsolo.bid:8057`

## Changes Made

### 1. Backend Server (`src/mining_os/server.py`)
- Updated the `/api/config` endpoint to return separate pool information for LTC and DOGE
- Changed the default values to match the new wallet addresses and pool endpoints
- Updated the configuration update endpoint to handle separate LTC and DOGE pool settings

### 2. Configuration Model (`src/mining_os/config.py`)
- Updated the example configuration to use the new wallet addresses and pool endpoints

### 3. MiningDashboard Component (`frontend/src/components/MiningDashboard.tsx`)
- Modified the interface to include separate LTC and DOGE pool host/port information
- Updated the UI to display both Litecoin and doeskin pool information
- Updated default values to match the new addresses and pools

### 4. SettingsPanel Component (`frontend/src/components/SettingsPanel.tsx`)
- Modified the interface to include separate LTC and DOGE pool configuration fields
- Updated the form to allow independent configuration of LTC and DOGE pools
- Updated default values to match the new addresses and pools

### 5. Environment Configuration (`.env.example`)
- Updated all wallet addresses to the new values
- Updated pool configuration to use separate LTC and DOGE pool settings
- Added proper pool user format for both LTC and DOGE

## Result
The mining system now uses the provided wallet addresses and pool endpoints by default. Users will see the correct wallet addresses and pool information displayed in the dashboard without needing to click "Start Mining". The configuration can be customized through the settings panel, with separate fields for Litecoin and doeskin pool settings.
# PAYOUT_ADDR Environment Variable Instructions

The PAYOUT_ADDR environment variable is mandatory for the Mining OS to function properly. This variable contains your wallet address where mining rewards will be sent.

## Understanding Wallet Addresses

The Mining OS uses specific wallet addresses:

1. **Your Personal Litecoin Address**: `ltc1qpptg85asckrjy9ygygh2tfgxqwzn6672zmzq99`
2. **Your Personal Dogecoin Address**: `DGKsuHU6XdghZtA2aWGqvrZrkWracQJzPd`

These are YOUR personal wallet addresses where mining rewards will be sent. You must set one of these in the PAYOUT_ADDR environment variable.

## Setting PAYOUT_ADDR

### On Linux/macOS:
```bash
# For your Litecoin wallet
export PAYOUT_ADDR=ltc1qpptg85asckrjy9ygygh2tfgxqwzn6672zmzq99

# For your Dogecoin wallet  
export PAYOUT_ADDR=DGKsuHU6XdghZtA2aWGqvrZrkWracQJzPd
```

### On Windows (Command Prompt):
```cmd
# For your Litecoin wallet
set PAYOUT_ADDR=ltc1qpptg85asckrjy9ygygh2tfgxqwzn6672zmzq99

# For your Dogecoin wallet
set PAYOUT_ADDR=DGKsuHU6XdghZtA2aWGqvrZrkWracQJzPd
```

### On Windows (PowerShell):
```powershell
# For your Litecoin wallet
$env:PAYOUT_ADDR="ltc1qpptg85asckrjy9ygygh2tfgxqwzn6672zmzq99"

# For your Dogecoin wallet
$env:PAYOUT_ADDR="DGKsuHU6XdghZtA2aWGqvrZrkWracQJzPd"
```

### On Windows (Using PowerShell Script):
```powershell
# For your Litecoin wallet
.\start-mining-os.ps1 -PayoutAddress "ltc1qpptg85asckrjy9ygygh2tfgxqwzn6672zmzq99"

# For your Dogecoin wallet
.\start-mining-os.ps1 -PayoutAddress "DGKsuHU6XdghZtA2aWGqvrZrkWracQJzPd"
```

### Using Docker:
```bash
# For your Litecoin wallet
docker run -e PAYOUT_ADDR=ltc1qpptg85asckrjy9ygygh2tfgxqwzn6672zmzq99 -p 31415:31415 mining-os

# For your Dogecoin wallet
docker run -e PAYOUT_ADDR=DGKsuHU6XdghZtA2aWGqvrZrkWracQJzPd -p 31415:31415 mining-os
```

## Verification

You can verify that the PAYOUT_ADDR is set correctly by running:
```bash
python test_payout_addr.py
```

Or on Windows:
```powershell
python test_payout_addr.py
```

## Important Notes

1. The PAYOUT_ADDR environment variable is required at startup - the application will not start without it
2. The payout address cannot be changed via the web interface for security reasons
3. To change your payout address, you must restart the application with a new PAYOUT_ADDR value
4. Never share your payout address publicly - it should be kept secure
5. You must use either your Litecoin address (ltc1qpptg85asckrjy9ygygh2tfgxqwzn6672zmzq99) or your Dogecoin address (DGKsuHU6XdghZtA2aWGqvrZrkWracQJzPd) as your PAYOUT_ADDR
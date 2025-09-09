"""
Constants for the Mining OS.
Contains immutable wallet addresses and other constants.
"""
# Immutable wallet addresses
LTC_WALLET_ADDRESS = "ltc1qpptg85asckrjy9ygygh2tfgxqwzn6672zmzq99"
DOGE_WALLET_ADDRESS = os.getenv("POOL_USER", os.getenv("POOL_USER", os.getenv("POOL_USER", "your_wallet_address.worker_name")))

# Pool endpoints
LTC_POOL_URL = "stratum+tcp://ltc.f2pool.com:8888"
DOGE_POOL_URL = "stratum+tcp://doge.zsolo.bid:8057"

# Default worker name
DEFAULT_WORKER_NAME = "rig01"

# Minimum payout threshold
DEFAULT_MINIMUM_PAYOUT_THRESHOLD = 0.005
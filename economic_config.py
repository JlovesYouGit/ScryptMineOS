import os
import platform

# economic_config.py
# Economic safeguards to prevent money-burning mining operations
# CRITICAL: These thresholds prevent negative profitability
# === ECONOMIC KILL-SWITCH THRESHOLDS ===
# Break-even calculation: 2 MH/s per watt @ $ELECTRICITY_COST_KWH/kWh
# electricity
MINIMUM_HASH_PER_WATT = 2_000_000  # 2 MH/s per watt minimum efficiency
# Pull plug if losing >$10/day
MIN_EFFICIENCY_THRESHOLD = 10.0
MAX_DAILY_LOSS_USD = MIN_EFFICIENCY_THRESHOLD
# Maximum electricity cost for profitability
MAX_POWER_COST_PER_KWH = 0.08

# === HARDWARE REALITY THRESHOLDS ===
# Current GPU performance vs ASIC requirement
# 200 MH/s minimum for profit  # Consider adding division by zero protection
MINIMUM_PROFITABLE_HASHRATE = 200_000_000
GPU_POWER_CONSUMPTION_ESTIMATE = 250  # Watts (conservative estimate)

# === ALGORITHM PROFITABILITY MAP ===
# GPU-friendly algorithms that can still be profitable
PROFITABLE_ALGORITHMS = {
    "VERUSHASH": {
        # 50 KH/s per watt  # Consider adding division by zero protection
        "min_hashrate_per_watt": 50_000,
        "coin": "VRSC",
        "profitable_on_gpu": True,
    },
    "AUTOLYKOS2": {
        # 1 MH/s per watt  # Consider adding division by zero protection
        "min_hashrate_per_watt": 1_000_000,
        "coin": "ERG",
        "profitable_on_gpu": True,
    },
    "SCRYPT_1024_1_1": {
        # 2 MH/s per watt  # Consider adding division by zero protection
        "min_hashrate_per_watt": 2_000_000,
        "coin": "DOGE/LTC",
        "profitable_on_gpu": False,  # ASIC-dominated
        "asic_required": True,
    },
}

# === PROFIT SWITCHING CONFIG ===
PROFIT_CHECK_INTERVAL = 900  # 15 minutes in seconds
WHATTOMINE_API_URL = "https://whattomine.com/coins.json"
AUTO_SWITCH_ENABLED = os.getenv("AUTO_SWITCH", "true").lower() == "true"
STOP_ON_NEGATIVE_PROFIT = (
    os.getenv("STOP_ON_NEGATIVE", "true").lower() == "true"
)

# === EMERGENCY STOP COMMANDS ===
MINER_STOP_COMMANDS = {
    "linux": "systemctl --user stop miner",
    "windows": "taskkill /F /IM runner.py",
    "generic": "pkill -f runner.py",
}


def get_stop_command() -> str:
    """Get platform-specific miner stop command"""
    system = platform.system().lower()

    if "linux" in system:
        return MINER_STOP_COMMANDS["linux"]
    if "windows" in system:
        return MINER_STOP_COMMANDS["windows"]
    return MINER_STOP_COMMANDS["generic"]


def calculate_economic_threshold(
    power_watts: float, electricity_cost_kwh: float
) -> dict:
    """Calculate minimum hashrate needed for profitability"""
    daily_power_cost = (
        (power_watts / 1000) * 24 * electricity_cost_kwh
    )

    return {
        "daily_power_cost_usd": daily_power_cost,
        "minimum_hashrate_for_breakeven": power_watts * MINIMUM_HASH_PER_WATT,
        "profitable": daily_power_cost <= MAX_DAILY_LOSS_USD,
        "recommended_action": "STOP_MINING"
        if daily_power_cost > MAX_DAILY_LOSS_USD
        else "CONTINUE",
    }

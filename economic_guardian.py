#!/usr/bin/env python3
"""
Economic Kill-Switch Guardian
CRITICAL: Prevents money-burning mining operations

This module implements the 20-line economic stop-loss gate that:
1. Monitors real-time power consumption vs hashrate efficiency  
2. Automatically stops mining when operating at a loss
3. Prevents the "beautiful 50 kH/s heater" problem

Must be called BEFORE OpenCL context creation to avoid wasted GPU initialization.
"""

import time
import sys
import os
import logging
import requests
from typing import Optional, Dict, Any
from economic_config import (
    MINIMUM_HASH_PER_WATT, 
    MAX_DAILY_LOSS_USD, 
    MINIMUM_PROFITABLE_HASHRATE,
    GPU_POWER_CONSUMPTION_ESTIMATE,
    get_stop_command,
    calculate_economic_threshold
)

# Configure logging for economic decisions
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("economic_guardian")

class EconomicGuardian:
    """Economic stop-loss guardian to prevent money-burning mining"""
    
    def __init__(self, power_watts: float = GPU_POWER_CONSUMPTION_ESTIMATE):
        self.power_watts = power_watts
        self.hashrate_samples = []
        self.last_check_time = time.time()
        
    def get_wall_power(self) -> float:
        """Get actual wall power consumption (USB powermeter/smart plug API)"""
        # TODO: Integrate with actual power measurement device
        # For now, use conservative GPU power estimate
        return self.power_watts
    
    def get_rolling_hashrate(self, window_seconds: int = 60) -> float:
        """Get rolling average hashrate over time window"""
        current_time = time.time()
        
        # Filter samples within time window
        recent_samples = [
            (timestamp, hashrate) for timestamp, hashrate in self.hashrate_samples
            if current_time - timestamp <= window_seconds
        ]
        
        if not recent_samples:
            return 0.0
            
        # Calculate average
        total_hashrate = sum(hashrate for _, hashrate in recent_samples)
        return total_hashrate / len(recent_samples)
    
    def record_hashrate(self, hashrate: float):
        """Record hashrate sample for rolling average"""
        self.hashrate_samples.append((time.time(), hashrate))
        
        # Keep only last 5 minutes of samples
        cutoff_time = time.time() - 300
        self.hashrate_samples = [
            (timestamp, hr) for timestamp, hr in self.hashrate_samples
            if timestamp >= cutoff_time
        ]
    
    def check_economic_viability(self, electricity_cost_kwh: float = 0.08) -> Dict[str, Any]:
        """CRITICAL: Economic kill-switch check"""
        watts = self.get_wall_power()
        hashrate = self.get_rolling_hashrate()
        
        # Calculate efficiency
        hash_per_watt = hashrate / watts if watts > 0 else 0
        
        # Calculate daily costs
        daily_power_cost = (watts / 1000) * 24 * electricity_cost_kwh
        
        # Economic thresholds
        threshold_data = calculate_economic_threshold(watts, electricity_cost_kwh)
        
        # Determine if mining is profitable
        is_economically_viable = (
            hash_per_watt >= MINIMUM_HASH_PER_WATT and
            daily_power_cost <= MAX_DAILY_LOSS_USD and
            hashrate >= MINIMUM_PROFITABLE_HASHRATE
        )
        
        return {
            "hashrate": hashrate,
            "power_watts": watts,
            "hash_per_watt": hash_per_watt,
            "daily_power_cost_usd": daily_power_cost,
            "electricity_cost_kwh": electricity_cost_kwh,
            "is_viable": is_economically_viable,
            "threshold_data": threshold_data,
            "failure_reasons": self._get_failure_reasons(hashrate, hash_per_watt, daily_power_cost)
        }
    
    def _get_failure_reasons(self, hashrate: float, hash_per_watt: float, daily_cost: float) -> list:
        """Identify specific reasons for economic failure"""
        reasons = []
        
        if hashrate < MINIMUM_PROFITABLE_HASHRATE:
            ratio = MINIMUM_PROFITABLE_HASHRATE / hashrate if hashrate > 0 else float('inf')
            reasons.append(f"Hashrate too low: {hashrate/1e6:.2f} MH/s (need {MINIMUM_PROFITABLE_HASHRATE/1e6:.0f} MH/s, {ratio:.0f}x improvement needed)")
        
        if hash_per_watt < MINIMUM_HASH_PER_WATT:
            reasons.append(f"Efficiency too low: {hash_per_watt/1e6:.2f} MH/s per watt (need {MINIMUM_HASH_PER_WATT/1e6:.0f} MH/s per watt)")
        
        if daily_cost > MAX_DAILY_LOSS_USD:
            reasons.append(f"Daily loss too high: ${daily_cost:.2f}/day (max ${MAX_DAILY_LOSS_USD}/day)")
        
        return reasons
    
    def emergency_stop(self, reason: str):
        """CRITICAL: Emergency stop mining to prevent further losses"""
        logger.critical(f"🚨 ECONOMIC EMERGENCY STOP: {reason}")
        logger.critical("Mining stopped to prevent further financial losses")
        
        # Log economic data for analysis
        economic_data = self.check_economic_viability()
        logger.critical(f"Economic data at stop: {economic_data}")
        
        # Stop the miner process
        try:
            stop_cmd = get_stop_command()
            logger.critical(f"Executing stop command: {stop_cmd}")
            os.system(stop_cmd)
        except Exception as e:
            logger.error(f"Failed to execute stop command: {e}")
        
        # Exit the current process
        sys.exit(1)
    
    def pre_mining_gate(self, electricity_cost_kwh: float = 0.08) -> bool:
        """
        CRITICAL: Gate check BEFORE starting mining
        Must be called before OpenCL context creation
        Returns True if safe to proceed, False if should abort
        """
        logger.info("🔍 Economic pre-mining gate check...")
        
        # Estimate with current hardware
        estimated_watts = self.get_wall_power()
        daily_cost = (estimated_watts / 1000) * 24 * electricity_cost_kwh
        
        # Check if even theoretical maximum GPU performance would be profitable
        theoretical_max_gpu_hashrate = 100_000  # 100 kH/s (optimistic GPU estimate)
        theoretical_efficiency = theoretical_max_gpu_hashrate / estimated_watts
        
        logger.info(f"📊 Economic analysis:")
        logger.info(f"   Estimated power: {estimated_watts}W")
        logger.info(f"   Daily electricity cost: ${daily_cost:.2f}")
        logger.info(f"   Theoretical max efficiency: {theoretical_efficiency:.0f} H/s per watt")
        logger.info(f"   Required efficiency: {MINIMUM_HASH_PER_WATT/1e6:.0f} MH/s per watt")
        
        # Hard reality check
        if theoretical_efficiency < MINIMUM_HASH_PER_WATT:
            efficiency_gap = MINIMUM_HASH_PER_WATT / theoretical_efficiency
            logger.critical(f"🚨 ECONOMIC ABORT: GPU hardware insufficient")
            logger.critical(f"   Need {efficiency_gap:.0f}x improvement for profitability")
            logger.critical(f"   Current setup will lose ${daily_cost:.2f}/day")
            logger.critical(f"   Recommendation: Upgrade to ASIC hardware (≥200 MH/s)")
            return False
        
        if daily_cost > MAX_DAILY_LOSS_USD:
            logger.critical(f"🚨 ECONOMIC ABORT: Daily loss exceeds limit")
            logger.critical(f"   Daily cost: ${daily_cost:.2f} > ${MAX_DAILY_LOSS_USD} limit")
            return False
        
        logger.info("✅ Economic pre-mining check passed")
        return True

# Global instance
economic_guardian = EconomicGuardian()

def economic_pre_flight_check(electricity_cost_kwh: float = 0.08, educational_mode: bool = False) -> bool:
    """
    CRITICAL: Call this before any mining initialization
    Returns False if mining would be economically catastrophic
    
    Args:
        electricity_cost_kwh: Cost per kWh in USD
        educational_mode: If True, bypasses economic checks for development/testing
    """
    if educational_mode:
        logger.info("🎓 EDUCATIONAL MODE: Bypassing economic checks for development/testing")
        logger.info("⚠️  This mode is for GPU-ASIC hybrid development and fleet management testing")
        logger.info("⚠️  Real mining operations should use economic safeguards")
        return True
        
    return economic_guardian.pre_mining_gate(electricity_cost_kwh)
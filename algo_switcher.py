#!/usr/bin/env python3
"""
Algorithm Switcher - GPU-Friendly Mining
Addresses the hard-coded Scrypt problem that locks GPUs to ASIC-dominated algorithms

Implements:
1. Multi-algorithm kernel support
2. Profit-switching based on WhatToMine API
3. Automatic coin switching every 15 minutes
4. GPU-friendly algorithm prioritization
"""

import time
import json
import requests
import logging
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from economic_config import PROFITABLE_ALGORITHMS, WHATTOMINE_API_URL, PROFIT_CHECK_INTERVAL

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("algo_switcher")

@dataclass
class AlgorithmConfig:
    """Configuration for a specific mining algorithm"""
    name: str
    min_hashrate_per_watt: float
    coin_symbol: str
    profitable_on_gpu: bool
    kernel_template: str
    pool_config: Dict[str, str]
    difficulty_api: str

class AlgorithmSwitcher:
    """Manages algorithm switching for optimal GPU profitability"""
    
    def __init__(self):
        self.current_algorithm = None
        self.last_switch_time = 0
        self.profit_history = []
        
        # Define GPU-friendly algorithms
        self.algorithms = {
            "VERUSHASH": AlgorithmConfig(
                name="VERUSHASH",
                min_hashrate_per_watt=50_000,  # 50 KH/s per watt
                coin_symbol="VRSC",
                profitable_on_gpu=True,
                kernel_template="verushash_core.cl.jinja",
                pool_config={
                    "host": "stratum+tcp://verushash.mine.zergpool.com",
                    "port": 4747,
                    "user": "DGKsuHU6XdghZtA2aWGqvrZrkWracQJzPd",  # Use existing wallet
                    "pass": "c=DOGE"
                },
                difficulty_api="https://api.coinpaprika.com/v1/coins/vrsc-verus-coin"
            ),
            "AUTOLYKOS2": AlgorithmConfig(
                name="AUTOLYKOS2", 
                min_hashrate_per_watt=1_000_000,  # 1 MH/s per watt
                coin_symbol="ERG",
                profitable_on_gpu=True,
                kernel_template="autolykos2_core.cl.jinja",
                pool_config={
                    "host": "stratum+tcp://erg.2miners.com",
                    "port": 8888,
                    "user": "9fQm7nCxUyEAmHFfP7E5Y2SbvX7dJvGH3Xp4FcwKq8xZvuv7Y8K",  # Placeholder ERG
                    "pass": "x"
                },
                difficulty_api="https://api.coinpaprika.com/v1/coins/erg-ergo"
            ),
            "SCRYPT_1024_1_1": AlgorithmConfig(
                name="SCRYPT_1024_1_1",
                min_hashrate_per_watt=2_000_000,  # 2 MH/s per watt (ASIC territory)
                coin_symbol="DOGE",
                profitable_on_gpu=False,  # ASIC-dominated
                kernel_template="scrypt_core.cl.jinja",
                pool_config={
                    "host": "ltc.f2pool.com",
                    "port": 3335,
                    "user": "LTC_ADDRESS.DGKsuHU6XdghZtA2aWGqvrZrkWracQJzPd.rig01",
                    "pass": "x"
                },
                difficulty_api="https://api.coinpaprika.com/v1/coins/doge-dogecoin"
            )
        }
    
    def get_current_profitability(self) -> Dict[str, Any]:
        """Query WhatToMine API for current GPU profitability"""
        try:
            # WhatToMine GPU profitability endpoint
            url = "https://whattomine.com/coins.json"
            params = {
                "adapt_q_280x": "0",
                "adapt_q_380": "0", 
                "adapt_q_fury": "0",
                "adapt_q_470": "1",    # AMD RX 470 as reference
                "adapt_q_480": "1",    # AMD RX 480 as reference
                "adapt_q_570": "1",    # AMD RX 570 as reference
                "adapt_q_580": "1",    # AMD RX 580 as reference
                "adapt_q_vega56": "0",
                "adapt_q_vega64": "0",
                "adapt_q_1050Ti": "0",
                "adapt_q_1060": "0",
                "adapt_q_1070": "0",
                "adapt_q_1080": "0",
                "adapt_q_1080Ti": "0",
                "factor[eth_hr]": "25",      # 25 MH/s Ethereum baseline
                "factor[eth_p]": "150",      # 150W power consumption
                "e4g": "true",               # Include Ethereum
                "factor[etc_hr]": "25",      # Ethereum Classic
                "factor[etc_p]": "150",
                "e6g": "true",
                "cost": "0.08",              # $0.08/kWh electricity
                "cost_currency": "USD"
            }
            
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            
            # Extract profitable coins for GPU
            gpu_coins = []
            for coin_id, coin_data in data.get("coins", {}).items():
                if isinstance(coin_data, dict):
                    algorithm = coin_data.get("algorithm", "").upper()
                    profit_24h = coin_data.get("btc_revenue24", 0)
                    difficulty = coin_data.get("difficulty", 0)
                    
                    # Check if algorithm is GPU-friendly
                    if any(algo in algorithm for algo in ["EQUIHASH", "ETHASH", "AUTOLYKOS", "VERUSHASH"]):
                        gpu_coins.append({
                            "symbol": coin_data.get("tag", ""),
                            "name": coin_data.get("name", ""),
                            "algorithm": algorithm,
                            "profit_24h_btc": profit_24h,
                            "difficulty": difficulty,
                            "supported": algorithm in self.algorithms
                        })
            
            # Sort by profitability
            gpu_coins.sort(key=lambda x: x["profit_24h_btc"], reverse=True)
            
            return {
                "timestamp": time.time(),
                "profitable_coins": gpu_coins[:10],  # Top 10
                "api_status": "success"
            }
            
        except Exception as e:
            logger.error(f"Failed to query WhatToMine API: {e}")
            return {
                "timestamp": time.time(),
                "profitable_coins": [],
                "api_status": "error",
                "error": str(e)
            }
    
    def should_switch_algorithm(self) -> Optional[str]:
        """Determine if algorithm should be switched for better profitability"""
        current_time = time.time()
        
        # Check if enough time has passed since last switch
        if current_time - self.last_switch_time < PROFIT_CHECK_INTERVAL:
            return None
        
        # Get current market data
        market_data = self.get_current_profitability()
        
        if market_data["api_status"] != "success":
            logger.warning("Cannot switch algorithm: API unavailable")
            return None
        
        # Find most profitable supported algorithm
        for coin in market_data["profitable_coins"]:
            algorithm = coin["algorithm"]
            if coin["supported"] and algorithm in self.algorithms:
                algo_config = self.algorithms[algorithm]
                
                # Only switch to GPU-friendly algorithms
                if algo_config.profitable_on_gpu:
                    if algorithm != self.current_algorithm:
                        logger.info(f"💰 Profit switch opportunity: {algorithm} ({coin['symbol']})")
                        logger.info(f"   24h profit: {coin['profit_24h_btc']:.8f} BTC")
                        return algorithm
        
        # No better algorithm found
        return None
    
    def get_algorithm_config(self, algorithm: str) -> Optional[AlgorithmConfig]:
        """Get configuration for specified algorithm"""
        return self.algorithms.get(algorithm)
    
    def switch_to_algorithm(self, algorithm: str) -> Dict[str, Any]:
        """Switch to specified algorithm"""
        if algorithm not in self.algorithms:
            return {"success": False, "error": f"Algorithm {algorithm} not supported"}
        
        algo_config = self.algorithms[algorithm]
        
        # Warn if switching to non-GPU-friendly algorithm
        if not algo_config.profitable_on_gpu:
            logger.warning(f"⚠️  Switching to ASIC-dominated algorithm: {algorithm}")
            logger.warning(f"   This may result in losses on GPU hardware")
        
        self.current_algorithm = algorithm
        self.last_switch_time = time.time()
        
        logger.info(f"🔄 Algorithm switched to: {algorithm} ({algo_config.coin_symbol})")
        
        return {
            "success": True,
            "algorithm": algorithm,
            "config": algo_config,
            "timestamp": self.last_switch_time
        }
    
    def get_gpu_friendly_recommendations(self) -> List[str]:
        """Get list of algorithms that are still profitable on GPUs"""
        return [
            name for name, config in self.algorithms.items() 
            if config.profitable_on_gpu
        ]
    
    def economic_algorithm_check(self, power_watts: float) -> Dict[str, Any]:
        """Check if current algorithm is economically viable for GPU"""
        if not self.current_algorithm:
            return {"viable": False, "reason": "No algorithm selected"}
        
        algo_config = self.algorithms[self.current_algorithm]
        
        # Check if algorithm is GPU-friendly
        if not algo_config.profitable_on_gpu:
            return {
                "viable": False,
                "reason": f"{self.current_algorithm} is ASIC-dominated",
                "recommendation": "Switch to GPU-friendly algorithm",
                "gpu_friendly_options": self.get_gpu_friendly_recommendations()
            }
        
        # Check minimum efficiency requirement
        required_hashrate = power_watts * algo_config.min_hashrate_per_watt
        
        return {
            "viable": True,
            "algorithm": self.current_algorithm,
            "required_hashrate": required_hashrate,
            "min_efficiency": algo_config.min_hashrate_per_watt
        }

# Global instance
algo_switcher = AlgorithmSwitcher()

def get_profitable_algorithm_for_gpu() -> Optional[str]:
    """Get the most profitable GPU-friendly algorithm"""
    recommendations = algo_switcher.get_gpu_friendly_recommendations()
    if recommendations:
        return recommendations[0]  # Return first (most recommended)
    return None
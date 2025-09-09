#!/usr/bin/env python3
"""
Profit-Switching Mining Wrapper
CRITICAL: Prevents economic suicide by auto-switching to profitable algorithms

This is the "NiceHash-QuickMiner equivalent" that:
1. Queries WhatToMine API every 15 minutes
2. Stops mining if daily_profit < 0
3. Hot-reloads optimal kernel and restarts
4. Prevents the "locked to unprofitable algorithm" problem
"""

import time
import sys
import os
import subprocess
import logging
import signal
import json
from typing import Optional, Dict, Any
from economic_guardian import economic_guardian, economic_pre_flight_check
from algo_switcher import algo_switcher, get_profitable_algorithm_for_gpu
from economic_config import PROFIT_CHECK_INTERVAL, AUTO_SWITCH_ENABLED, STOP_ON_NEGATIVE_PROFIT

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger("profit_switcher")

class ProfitSwitchingMiner:
    """Auto-switching miner that prevents economic losses"""
    
    def __init__(self):
        self.miner_process = None
        self.current_algorithm = None
        self.last_profitability_check = 0
        self.running = True
        self.total_runtime = 0
        self.total_profit_usd = 0.0
        
        # Setup signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
        
    def _signal_handler(self, signum, frame):
        """Handle shutdown signals gracefully"""
        logger.info(f"Received signal {signum}, shutting down...")
        self.running = False
        self._stop_miner()
        sys.exit(0)
    
    def _stop_miner(self):
        """Stop the current miner process"""
        if self.miner_process and self.miner_process.poll() is None:
            logger.info("Stopping current miner process...")
            try:
                self.miner_process.terminate()
                self.miner_process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                logger.warning("Miner didn't stop gracefully, forcing kill...")
                self.miner_process.kill()
                self.miner_process.wait()
            finally:
                self.miner_process = None
                
    def _start_miner(self, algorithm: str) -> bool:
        """Start miner with specified algorithm"""
        try:
            algo_config = algo_switcher.get_algorithm_config(algorithm)
            if not algo_config:
                logger.error(f"No configuration for algorithm: {algorithm}")
                return False
            
            # Build command line arguments
            cmd = [
                sys.executable, "runner.py",
                "--algo", algorithm,
                "--pool-host", algo_config.pool_config["host"],
                "--pool-port", str(algo_config.pool_config["port"]), 
                "--pool-user", algo_config.pool_config["user"],
                "--pool-pass", algo_config.pool_config["pass"]
            ]
            
            logger.info(f"Starting miner: {' '.join(cmd)}")
            self.miner_process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                cwd=os.path.dirname(os.path.abspath(__file__))
            )
            
            self.current_algorithm = algorithm
            return True
            
        except Exception as e:
            logger.error(f"Failed to start miner: {e}")
            return False
    
    def _check_profitability(self) -> Dict[str, Any]:
        """Check current mining profitability"""
        current_time = time.time()
        
        # Get economic data from guardian
        economic_data = economic_guardian.check_economic_viability()
        
        # Get market data from algo switcher
        market_data = algo_switcher.get_current_profitability()
        
        # Calculate estimated daily profit
        hashrate = economic_data["hashrate"]
        power_cost = economic_data["daily_power_cost_usd"]
        
        # Rough profit estimation (this would be more accurate with real coin prices)
        estimated_daily_revenue = (hashrate / 1e6) * 0.001  # $0.001 per MH/s (very rough)
        estimated_daily_profit = estimated_daily_revenue - power_cost
        
        self.last_profitability_check = current_time
        
        return {
            "timestamp": current_time,
            "economic_data": economic_data,
            "market_data": market_data,
            "estimated_daily_profit_usd": estimated_daily_profit,
            "estimated_daily_revenue_usd": estimated_daily_revenue,
            "profitable": estimated_daily_profit > 0 and economic_data["is_viable"]
        }
    
    def _should_switch_algorithm(self) -> Optional[str]:
        """Determine if we should switch algorithms"""
        if not AUTO_SWITCH_ENABLED:
            return None
            
        current_time = time.time()
        if current_time - self.last_profitability_check < PROFIT_CHECK_INTERVAL:
            return None
        
        return algo_switcher.should_switch_algorithm()
    
    def run(self):
        """Main profit-switching loop"""
        logger.info("🚀 Starting Profit-Switching Miner")
        logger.info(f"   Auto-switching: {'ENABLED' if AUTO_SWITCH_ENABLED else 'DISABLED'}")
        logger.info(f"   Stop on negative profit: {'ENABLED' if STOP_ON_NEGATIVE_PROFIT else 'DISABLED'}")
        logger.info(f"   Profit check interval: {PROFIT_CHECK_INTERVAL//60} minutes")
        
        # CRITICAL: Economic pre-flight check
        if not economic_pre_flight_check():
            logger.critical("🚨 Economic pre-flight check FAILED")
            logger.critical("Mining would result in guaranteed losses")
            logger.critical("ABORT: Use ASIC hardware for Scrypt mining")
            return 1
        
        # Find initial profitable algorithm
        initial_algo = get_profitable_algorithm_for_gpu()
        if not initial_algo:
            logger.critical("🚨 No profitable GPU algorithms available")
            logger.critical("All supported algorithms are ASIC-dominated")
            logger.critical("Recommendation: Wait for market conditions to improve")
            return 1
        
        logger.info(f"Selected initial algorithm: {initial_algo}")
        
        # Start mining with initial algorithm
        if not self._start_miner(initial_algo):
            logger.error("Failed to start initial miner")
            return 1
        
        start_time = time.time()
        
        # Main monitoring loop
        while self.running:
            try:
                # Check if miner process is still running
                if self.miner_process and self.miner_process.poll() is not None:
                    logger.warning("Miner process exited unexpectedly")
                    # Restart with same algorithm
                    if self.current_algorithm:
                        if not self._start_miner(self.current_algorithm):
                            logger.error("Failed to restart miner")
                            break
                
                # Periodic profitability check
                if time.time() - self.last_profitability_check >= PROFIT_CHECK_INTERVAL:
                    logger.info("📊 Checking profitability...")
                    
                    profit_data = self._check_profitability()
                    
                    logger.info(f"Economic status:")
                    logger.info(f"   Hashrate: {profit_data['economic_data']['hashrate']/1000:.1f} kH/s")
                    logger.info(f"   Power: {profit_data['economic_data']['power_watts']:.0f}W")
                    logger.info(f"   Daily power cost: ${profit_data['economic_data']['daily_power_cost_usd']:.2f}")
                    logger.info(f"   Estimated daily profit: ${profit_data['estimated_daily_profit_usd']:.2f}")
                    logger.info(f"   Economically viable: {profit_data['profitable']}")
                    
                    # CRITICAL: Stop if unprofitable
                    if STOP_ON_NEGATIVE_PROFIT and not profit_data["profitable"]:
                        logger.critical("🚨 NEGATIVE PROFITABILITY DETECTED")
                        logger.critical(f"Daily loss: ${-profit_data['estimated_daily_profit_usd']:.2f}")
                        
                        failure_reasons = profit_data['economic_data'].get('failure_reasons', [])
                        for reason in failure_reasons:
                            logger.critical(f"   {reason}")
                        
                        economic_guardian.emergency_stop("Negative profitability detected")
                        break
                    
                    # Check if we should switch algorithms
                    new_algorithm = self._should_switch_algorithm()
                    if new_algorithm and new_algorithm != self.current_algorithm:
                        logger.info(f"🔄 Switching to more profitable algorithm: {new_algorithm}")
                        self._stop_miner()
                        time.sleep(2)  # Brief pause
                        if not self._start_miner(new_algorithm):
                            logger.error(f"Failed to switch to {new_algorithm}")
                            # Try to restart with previous algorithm
                            if not self._start_miner(self.current_algorithm):
                                logger.critical("Failed to restart mining")
                                break
                
                # Update runtime statistics
                self.total_runtime = time.time() - start_time
                
                # Sleep between checks
                time.sleep(30)  # Check every 30 seconds
                
            except KeyboardInterrupt:
                logger.info("Shutdown requested by user")
                break
            except Exception as e:
                logger.error(f"Error in main loop: {e}")
                time.sleep(10)  # Brief pause before retry
        
        # Cleanup
        self._stop_miner()
        
        # Final statistics
        logger.info(f"📈 Mining session summary:")
        logger.info(f"   Total runtime: {self.total_runtime/3600:.1f} hours")
        logger.info(f"   Final algorithm: {self.current_algorithm}")
        logger.info(f"   Session completed")
        
        return 0

def main():
    """Main entry point"""
    if len(sys.argv) > 1 and sys.argv[1] == "--dry-run":
        # Dry run mode - just check profitability
        logger.info("Running in dry-run mode...")
        
        if not economic_pre_flight_check():
            print("❌ Economic check FAILED - mining would lose money")
            return 1
        
        profitable_algo = get_profitable_algorithm_for_gpu()
        if profitable_algo:
            print(f"✅ Recommended algorithm: {profitable_algo}")
            return 0
        else:
            print("❌ No profitable GPU algorithms found")
            return 1
    
    # Normal mode - run profit-switching miner
    switcher = ProfitSwitchingMiner()
    return switcher.run()

if __name__ == "__main__":
    sys.exit(main())
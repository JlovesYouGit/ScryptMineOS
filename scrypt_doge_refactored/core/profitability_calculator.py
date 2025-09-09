"""
Real Profitability Calculator for Mining Operations
Calculates actual mining profitability based on real market data
"""

import asyncio
import aiohttp
import logging
import time
from typing import Dict, Any, Optional
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class CoinPrice:
    """Cryptocurrency price data"""
    symbol: str
    price_usd: float
    change_24h: float
    last_updated: float


@dataclass
class NetworkStats:
    """Network difficulty and stats"""
    algorithm: str
    difficulty: float
    block_reward: float
    block_time: int  # seconds
    network_hashrate: float  # H/s


@dataclass
class ProfitabilityResult:
    """Mining profitability calculation result"""
    coin: str
    hashrate_mhs: float
    power_watts: float
    electricity_cost_kwh: float
    
    # Revenue
    coins_per_day: float
    revenue_usd_per_day: float
    
    # Costs
    electricity_cost_per_day: float
    
    # Profit
    profit_usd_per_day: float
    profit_margin_percent: float
    
    # Break-even
    break_even_hashrate_mhs: float
    break_even_price_usd: float
    
    # Time estimates
    roi_days: Optional[int]
    
    # Pool fees
    pool_fee_percent: float
    pool_fee_usd_per_day: float


class RealProfitabilityCalculator:
    """Calculate real mining profitability using live market data"""
    
    def __init__(self):
        self.price_cache: Dict[str, CoinPrice] = {}
        self.network_cache: Dict[str, NetworkStats] = {}
        self.cache_duration = 300  # 5 minutes
        
    async def get_coin_price(self, symbol: str) -> Optional[CoinPrice]:
        """Get current coin price from CoinGecko API"""
        # Check cache first
        if symbol in self.price_cache:
            cached = self.price_cache[symbol]
            if time.time() - cached.last_updated < self.cache_duration:
                return cached
        
        try:
            # Map symbols to CoinGecko IDs
            coin_ids = {
                'LTC': 'litecoin',
                'DOGE': 'dogecoin',
                'BTC': 'bitcoin'
            }
            
            if symbol not in coin_ids:
                logger.error(f"Unknown coin symbol: {symbol}")
                return None
            
            coin_id = coin_ids[symbol]
            url = f"https://api.coingecko.com/api/v3/simple/price"
            params = {
                'ids': coin_id,
                'vs_currencies': 'usd',
                'include_24hr_change': 'true'
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url, params=params, timeout=10) as response:
                    if response.status == 200:
                        data = await response.json()
                        coin_data = data[coin_id]
                        
                        price = CoinPrice(
                            symbol=symbol,
                            price_usd=coin_data['usd'],
                            change_24h=coin_data.get('usd_24h_change', 0.0),
                            last_updated=time.time()
                        )
                        
                        self.price_cache[symbol] = price
                        logger.info(f"Updated {symbol} price: ${price.price_usd:.4f}")
                        return price
                    else:
                        logger.error(f"CoinGecko API error: {response.status}")
                        
        except Exception as e:
            logger.error(f"Error fetching {symbol} price: {e}")
        
        # Return cached data if available, even if stale
        return self.price_cache.get(symbol)
    
    async def get_network_stats(self, coin: str) -> Optional[NetworkStats]:
        """Get network difficulty and stats"""
        # For now, use approximate values - in production, fetch from blockchain APIs
        network_data = {
            'LTC': NetworkStats(
                algorithm='scrypt',
                difficulty=25000000,  # Approximate LTC difficulty
                block_reward=12.5,    # LTC block reward
                block_time=150,       # 2.5 minutes
                network_hashrate=500e12  # ~500 TH/s
            ),
            'DOGE': NetworkStats(
                algorithm='scrypt',
                difficulty=8000000,   # Approximate DOGE difficulty
                block_reward=10000,   # DOGE block reward
                block_time=60,        # 1 minute
                network_hashrate=800e12  # ~800 TH/s
            )
        }
        
        return network_data.get(coin)
    
    async def calculate_profitability(
        self,
        coin: str,
        hashrate_mhs: float,
        power_watts: float,
        electricity_cost_kwh: float = 0.12,
        pool_fee_percent: float = 2.5,
        hardware_cost_usd: float = 0.0
    ) -> Optional[ProfitabilityResult]:
        """Calculate mining profitability for a specific coin"""
        
        try:
            # Get current price
            price_data = await self.get_coin_price(coin)
            if not price_data:
                logger.error(f"Could not get price data for {coin}")
                return None
            
            # Get network stats
            network_stats = await self.get_network_stats(coin)
            if not network_stats:
                logger.error(f"Could not get network stats for {coin}")
                return None
            
            # Convert hashrate to H/s
            hashrate_hs = hashrate_mhs * 1e6
            
            # Calculate coins per day
            # Formula: (hashrate / network_hashrate) * blocks_per_day * block_reward
            blocks_per_day = 86400 / network_stats.block_time
            hashrate_share = hashrate_hs / network_stats.network_hashrate
            coins_per_day = hashrate_share * blocks_per_day * network_stats.block_reward
            
            # Calculate revenue
            revenue_usd_per_day = coins_per_day * price_data.price_usd
            
            # Calculate pool fees
            pool_fee_usd_per_day = revenue_usd_per_day * (pool_fee_percent / 100)
            revenue_after_fees = revenue_usd_per_day - pool_fee_usd_per_day
            
            # Calculate electricity cost
            power_kwh_per_day = (power_watts / 1000) * 24
            electricity_cost_per_day = power_kwh_per_day * electricity_cost_kwh
            
            # Calculate profit
            profit_usd_per_day = revenue_after_fees - electricity_cost_per_day
            profit_margin_percent = (profit_usd_per_day / revenue_usd_per_day * 100) if revenue_usd_per_day > 0 else 0
            
            # Calculate break-even points
            break_even_hashrate_mhs = 0.0
            break_even_price_usd = 0.0
            
            if revenue_usd_per_day > 0:
                # Break-even hashrate (where profit = 0)
                break_even_revenue = electricity_cost_per_day / (1 - pool_fee_percent / 100)
                break_even_coins = break_even_revenue / price_data.price_usd
                break_even_hashrate_share = break_even_coins / (blocks_per_day * network_stats.block_reward)
                break_even_hashrate_mhs = (break_even_hashrate_share * network_stats.network_hashrate) / 1e6
                
                # Break-even price (where profit = 0 at current hashrate)
                break_even_price_usd = electricity_cost_per_day / (coins_per_day * (1 - pool_fee_percent / 100))
            
            # Calculate ROI
            roi_days = None
            if hardware_cost_usd > 0 and profit_usd_per_day > 0:
                roi_days = int(hardware_cost_usd / profit_usd_per_day)
            
            result = ProfitabilityResult(
                coin=coin,
                hashrate_mhs=hashrate_mhs,
                power_watts=power_watts,
                electricity_cost_kwh=electricity_cost_kwh,
                coins_per_day=coins_per_day,
                revenue_usd_per_day=revenue_usd_per_day,
                electricity_cost_per_day=electricity_cost_per_day,
                profit_usd_per_day=profit_usd_per_day,
                profit_margin_percent=profit_margin_percent,
                break_even_hashrate_mhs=break_even_hashrate_mhs,
                break_even_price_usd=break_even_price_usd,
                roi_days=roi_days,
                pool_fee_percent=pool_fee_percent,
                pool_fee_usd_per_day=pool_fee_usd_per_day
            )
            
            logger.info(f"{coin} profitability: ${profit_usd_per_day:.4f}/day ({profit_margin_percent:.1f}% margin)")
            return result
            
        except Exception as e:
            logger.error(f"Error calculating {coin} profitability: {e}")
            return None
    
    async def compare_coins(
        self,
        coins: list,
        hashrate_mhs: float,
        power_watts: float,
        electricity_cost_kwh: float = 0.12
    ) -> Dict[str, ProfitabilityResult]:
        """Compare profitability across multiple coins"""
        
        results = {}
        
        # Calculate profitability for each coin
        tasks = []
        for coin in coins:
            task = self.calculate_profitability(
                coin, hashrate_mhs, power_watts, electricity_cost_kwh
            )
            tasks.append((coin, task))
        
        # Wait for all calculations
        for coin, task in tasks:
            try:
                result = await task
                if result:
                    results[coin] = result
            except Exception as e:
                logger.error(f"Error calculating {coin}: {e}")
        
        return results
    
    def get_recommendations(self, results: Dict[str, ProfitabilityResult]) -> list:
        """Generate profitability recommendations"""
        recommendations = []
        
        if not results:
            return ["Unable to calculate profitability - check network connection"]
        
        # Find most profitable coin
        most_profitable = max(results.values(), key=os.getenv("API_KEY", "your_key_here")"API_KEY", "your_key_here") x: x.profit_usd_per_day)
        
        if most_profitable.profit_usd_per_day > 0:
            recommendations.append(f"Most profitable: {most_profitable.coin} (${most_profitable.profit_usd_per_day:.2f}/day)")
        else:
            recommendations.append("⚠️ No coins are currently profitable with current settings")
        
        # Check for unprofitable coins
        unprofitable = [r for r in results.values() if r.profit_usd_per_day <= 0]
        if unprofitable:
            recommendations.append(f"⚠️ {len(unprofitable)} coin(s) are unprofitable")
        
        # Electricity cost recommendations
        avg_electricity_cost = sum(r.electricity_cost_per_day for r in results.values()) / len(results)
        if avg_electricity_cost > 1.0:
            recommendations.append("💡 Consider mining during off-peak hours to reduce electricity costs")
        
        # Efficiency recommendations
        avg_efficiency = sum(r.hashrate_mhs / r.power_watts for r in results.values()) / len(results)
        if avg_efficiency < 0.5:
            recommendations.append("⚡ Consider hardware optimization to improve efficiency")
        
        return recommendations


# Global instance
profitability_calculator = RealProfitabilityCalculator()


async def get_real_profitability(
    hashrate_mhs: float = 125.4,
    power_watts: float = 150.0,
    electricity_cost_kwh: float = 0.12
) -> Dict[str, Any]:
    """Get real profitability data for the dashboard"""
    
    try:
        # Calculate for both LTC and DOGE
        results = await profitability_calculator.compare_coins(
            ['LTC', 'DOGE'], hashrate_mhs, power_watts, electricity_cost_kwh
        )
        
        if not results:
            return {
                "current_profit_usd_per_day": 0.0,
                "electricity_cost_per_day": (power_watts / 1000) * 24 * electricity_cost_kwh,
                "net_profit_per_day": 0.0,
                "break_even_hashrate": 0.0,
                "roi_days": None,
                "profit_margin_percent": 0.0,
                "recommendations": ["Unable to fetch real market data - using offline mode"],
                "data_source": "offline"
            }
        
        # Use the most profitable coin
        best_result = max(results.values(), key=os.getenv("API_KEY", "your_key_here")"API_KEY", "your_key_here") x: x.profit_usd_per_day)
        recommendations = profitability_calculator.get_recommendations(results)
        
        return {
            "current_profit_usd_per_day": best_result.profit_usd_per_day,
            "electricity_cost_per_day": best_result.electricity_cost_per_day,
            "net_profit_per_day": best_result.profit_usd_per_day,
            "break_even_hashrate": best_result.break_even_hashrate_mhs,
            "roi_days": best_result.roi_days,
            "profit_margin_percent": best_result.profit_margin_percent,
            "recommendations": recommendations,
            "data_source": "live_market_data",
            "best_coin": best_result.coin,
            "coins_per_day": best_result.coins_per_day,
            "pool_fee_usd": best_result.pool_fee_usd_per_day
        }
        
    except Exception as e:
        logger.error(f"Error getting real profitability: {e}")
        
        # Fallback to basic calculation
        electricity_cost_per_day = (power_watts / 1000) * 24 * electricity_cost_kwh
        
        return {
            "current_profit_usd_per_day": 0.0,
            "electricity_cost_per_day": electricity_cost_per_day,
            "net_profit_per_day": -electricity_cost_per_day,
            "break_even_hashrate": 0.0,
            "roi_days": None,
            "profit_margin_percent": 0.0,
            "recommendations": [f"Error calculating profitability: {str(e)}"],
            "data_source": "error"
        }


if __name__ == "__main__":
    # Test the profitability calculator
    async def test():
        calc = RealProfitabilityCalculator()
        
        # Test LTC profitability
        result = await calc.calculate_profitability(
            coin='LTC',
            hashrate_mhs=125.4,
            power_watts=150.0,
            electricity_cost_kwh=0.12
        )
        
        if result:
            print(f"LTC Profitability:")
            print(f"  Revenue: ${result.revenue_usd_per_day:.4f}/day")
            print(f"  Electricity: ${result.electricity_cost_per_day:.4f}/day")
            print(f"  Profit: ${result.profit_usd_per_day:.4f}/day")
            print(f"  Margin: {result.profit_margin_percent:.1f}%")
        else:
            print("Could not calculate LTC profitability")
    
    asyncio.run(test())
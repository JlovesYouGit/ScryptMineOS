"""
Economic Guardian System for the refactored Scrypt DOGE mining system.
Real-time profitability monitoring and automatic shutdown.
"""

import asyncio
import logging
from typing import Dict, Optional, Callable, List, Any
from dataclasses import dataclass
from datetime import datetime, timedelta
import aiohttp
import json
from abc import ABC, abstractmethod

logger = logging.getLogger(__name__)


@dataclass
class ProfitabilityMetrics:
    """Profitability calculation metrics"""
    revenue_btc_per_day: float
    revenue_usd_per_day: float
    power_cost_per_day: float
    hardware_cost_per_day: float
    net_profit_usd_per_day: float
    profit_margin: float  # percentage
    break_even_price: float  # USD per kWh
    timestamp: datetime


@dataclass
class MarketData:
    """Cryptocurrency market data"""
    btc_price_usd: float
    network_hashrate: float  # EH/s
    network_difficulty: float
    block_reward: float  # BTC
    block_time: int  # seconds
    timestamp: datetime


@dataclass
class PowerMetrics:
    """Power consumption metrics"""
    total_power_watts: float
    power_cost_per_kwh: float
    efficiency_gh_per_watt: float
    uptime_hours: float


class MarketDataProvider(ABC):
    """Abstract market data provider"""
    
    @abstractmethod
    async def get_market_data(self) -> MarketData:
        """Get current market data"""
        pass
    
    @abstractmethod
    async def get_btc_price(self) -> float:
        """Get current BTC price in USD"""
        pass


class CoinGeckoProvider(MarketDataProvider):
    """CoinGecko API provider"""
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key
        self.base_url = "https://api.coingecko.com/api/v3"
        self.logger = logging.getLogger(__name__)
    
    async def get_market_data(self) -> MarketData:
        """Get market data from CoinGecko"""
        try:
            async with aiohttp.ClientSession() as session:
                # Get BTC price
                price_url = f"{self.base_url}/simple/price?ids=bitcoin&vs_currencies=usd"
                async with session.get(price_url) as response:
                    price_data = await response.json()
                    btc_price = price_data['bitcoin']['usd']
                
                # Get network stats (simplified - would need blockchain API)
                # For now, return estimated values
                return MarketData(
                    btc_price_usd=btc_price,
                    network_hashrate=150.0,  # EH/s - would get from API
                    network_difficulty=25.0,  # T - would get from API
                    block_reward=6.25,  # BTC
                    block_time=600,  # 10 minutes
                    timestamp=datetime.now()
                )
                
        except Exception as e:
            self.logger.error(f"Failed to get market data: {e}")
            raise
    
    async def get_btc_price(self) -> float:
        """Get current BTC price"""
        try:
            async with aiohttp.ClientSession() as session:
                url = f"{self.base_url}/simple/price?ids=bitcoin&vs_currencies=usd"
                async with session.get(url) as response:
                    data = await response.json()
                    return data['bitcoin']['usd']
        except Exception as e:
            self.logger.error(f"Failed to get BTC price: {e}")
            raise


class BlockchainInfoProvider(MarketDataProvider):
    """Blockchain.info API provider"""
    
    def __init__(self):
        self.base_url = "https://blockchain.info"
        self.logger = logging.getLogger(__name__)
    
    async def get_market_data(self) -> MarketData:
        """Get market data from Blockchain.info"""
        try:
            async with aiohttp.ClientSession() as session:
                # Get BTC price
                price_url = f"{self.base_url}/ticker"
                async with session.get(price_url) as response:
                    price_data = await response.json()
                    btc_price = float(price_data['USD']['last'])
                
                # Get network stats
                stats_url = f"{self.base_url}/q/hashrate"
                async with session.get(stats_url) as response:
                    hashrate_text = await response.text()
                    network_hashrate = float(hashrate_text) / 1e18  # Convert to EH/s
                
                return MarketData(
                    btc_price_usd=btc_price,
                    network_hashrate=network_hashrate,
                    network_difficulty=25.0,  # Would get from API
                    block_reward=6.25,
                    block_time=600,
                    timestamp=datetime.now()
                )
                
        except Exception as e:
            self.logger.error(f"Failed to get market data: {e}")
            raise
    
    async def get_btc_price(self) -> float:
        """Get current BTC price"""
        try:
            async with aiohttp.ClientSession() as session:
                url = f"{self.base_url}/ticker"
                async with session.get(url) as response:
                    data = await response.json()
                    return float(data['USD']['last'])
        except Exception as e:
            self.logger.error(f"Failed to get BTC price: {e}")
            raise


class EconomicGuardian:
    """Economic safeguard system"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        # Configuration
        self.enabled = config.get('enabled', True)
        self.max_power_cost = config.get('max_power_cost', 0.12)  # $/kWh
        self.min_profitability = config.get('min_profitability', 0.01)  # 1%
        self.shutdown_on_unprofitable = config.get('shutdown_on_unprofitable', True)
        self.check_interval = config.get('profitability_check_interval', 300)  # 5 minutes
        
        # State
        self.is_profitable = True
        self.last_check: Optional[datetime] = None
        self.current_metrics: Optional[ProfitabilityMetrics] = None
        self.callbacks: Dict[str, List[Callable]] = {
            'profitability_change': [],
            'shutdown_required': [],
            'metrics_update': []
        }
        
        # Initialize market data provider
        self.market_provider = CoinGeckoProvider()
        
        # Power metrics tracking
        self.power_metrics_history: List[PowerMetrics] = []
        self.market_data_history: List[MarketData] = []
        
        # Monitoring task
        self.monitoring_task: Optional[asyncio.Task] = None
        self.running = False
    
    def add_callback(self, event: str, callback: Callable) -> None:
        """Add event callback"""
        if event in self.callbacks:
            self.callbacks[event].append(callback)
    
    def _trigger_callback(self, event: str, *args, **kwargs) -> None:
        """Trigger event callbacks"""
        for callback in self.callbacks.get(event, []):
            try:
                callback(*args, **kwargs)
            except Exception as e:
                self.logger.error(f"Callback error: {e}")
    
    async def start_monitoring(self) -> None:
        """Start profitability monitoring"""
        if not self.enabled:
            self.logger.info("Economic guardian is disabled")
            return
        
        if self.monitoring_task and not self.monitoring_task.done():
            self.logger.warning("Economic monitoring already running")
            return
        
        self.logger.info("Starting economic monitoring")
        self.running = True
        self.monitoring_task = asyncio.create_task(self._monitoring_loop())
    
    async def stop_monitoring(self) -> None:
        """Stop profitability monitoring"""
        self.logger.info("Stopping economic monitoring")
        self.running = False
        
        if self.monitoring_task:
            self.monitoring_task.cancel()
            try:
                await self.monitoring_task
            except asyncio.CancelledError:
                pass
            self.monitoring_task = None
    
    async def _monitoring_loop(self) -> None:
        """Main monitoring loop"""
        while self.running:
            try:
                await self._check_profitability()
                await asyncio.sleep(self.check_interval)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Error in economic monitoring: {e}")
                await asyncio.sleep(60)  # Wait 1 minute on error
    
    async def _check_profitability(self) -> None:
        """Check current profitability"""
        try:
            self.logger.debug("Checking profitability")
            
            # Get current data
            market_data = await self.market_provider.get_market_data()
            power_metrics = await self._get_power_metrics()
            
            # Calculate profitability
            metrics = self._calculate_profitability(market_data, power_metrics)
            
            # Update history
            self.current_metrics = metrics
            self.market_data_history.append(market_data)
            self.power_metrics_history.append(power_metrics)
            
            # Trim history to last 24 hours
            cutoff_time = datetime.now() - timedelta(hours=24)
            self.market_data_history = [
                data for data in self.market_data_history
                if data.timestamp > cutoff_time
            ]
            self.power_metrics_history = [
                data for data in self.power_metrics_history
                if data.timestamp > cutoff_time
            ]
            
            # Check if profitability changed
            previous_profitable = self.is_profitable
            self.is_profitable = (
                metrics.profit_margin >= self.min_profitability and
                power_metrics.power_cost_per_kwh <= self.max_power_cost
            )
            
            # Trigger callbacks
            self._trigger_callback('metrics_update', metrics)
            
            if self.is_profitable != previous_profitable:
                self._trigger_callback('profitability_change', self.is_profitable, metrics)
                
                if not self.is_profitable and self.shutdown_on_unprofitable:
                    self.logger.warning("Mining is no longer profitable, triggering shutdown")
                    self._trigger_callback('shutdown_required', metrics)
            
            self.last_check = datetime.now()
            
            self.logger.info(
                f"Profitability check: {metrics.profit_margin:.2f}% margin, "
                f"{'PROFITABLE' if self.is_profitable else 'UNPROFITABLE'}"
            )
            
        except Exception as e:
            self.logger.error(f"Failed to check profitability: {e}")
    
    def _calculate_profitability(self, market_data: MarketData, power_metrics: PowerMetrics) -> ProfitabilityMetrics:
        """Calculate profitability metrics"""
        
        # Calculate daily revenue in BTC
        # Simplified calculation - would use actual network difficulty and hashrate
        network_hashrate_gh = market_data.network_hashrate * 1e6  # Convert EH/s to GH/s
        miner_share = power_metrics.total_power_watts / 1000  # Simplified share calculation
        
        # Daily BTC revenue (very simplified)
        blocks_per_day = 86400 / market_data.block_time
        daily_btc_reward = blocks_per_day * market_data.block_reward
        revenue_btc_per_day = (miner_share / network_hashrate_gh) * daily_btc_reward
        
        # Convert to USD
        revenue_usd_per_day = revenue_btc_per_day * market_data.btc_price_usd
        
        # Calculate costs
        power_cost_per_day = (power_metrics.total_power_watts / 1000) * 24 * power_metrics.power_cost_per_kwh
        
        # Assume hardware cost amortization (simplified)
        hardware_cost_per_day = 0.50  # $0.50 per day (would be configurable)
        
        # Calculate profit
        net_profit_usd_per_day = revenue_usd_per_day - power_cost_per_day - hardware_cost_per_day
        profit_margin = (net_profit_usd_per_day / revenue_usd_per_day * 100) if revenue_usd_per_day > 0 else -100
        
        # Calculate break-even power cost
        break_even_price = (revenue_usd_per_day - hardware_cost_per_day) / ((power_metrics.total_power_watts / 1000) * 24) if power_metrics.total_power_watts > 0 else 0
        
        return ProfitabilityMetrics(
            revenue_btc_per_day=revenue_btc_per_day,
            revenue_usd_per_day=revenue_usd_per_day,
            power_cost_per_day=power_cost_per_day,
            hardware_cost_per_day=hardware_cost_per_day,
            net_profit_usd_per_day=net_profit_usd_per_day,
            profit_margin=profit_margin,
            break_even_price=break_even_price,
            timestamp=datetime.now()
        )
    
    async def _get_power_metrics(self) -> PowerMetrics:
        """Get current power consumption metrics"""
        # This would integrate with hardware monitoring
        # For now, return estimated values
        return PowerMetrics(
            total_power_watts=3000.0,  # 3kW (would get from hardware)
            power_cost_per_kwh=self.max_power_cost,
            efficiency_gh_per_watt=0.033,  # 33 J/TH = 0.033 J/GH
            uptime_hours=24.0
        )
    
    def get_current_metrics(self) -> Optional[ProfitabilityMetrics]:
        """Get current profitability metrics"""
        return self.current_metrics
    
    def is_mining_profitable(self) -> bool:
        """Check if mining is currently profitable"""
        return self.is_profitable if self.enabled else True
    
    def get_profitability_summary(self) -> Dict[str, Any]:
        """Get profitability summary"""
        if not self.current_metrics:
            return {"status": "no_data"}
        
        return {
            "status": "profitable" if self.is_profitable else "unprofitable",
            "profit_margin": self.current_metrics.profit_margin,
            "net_profit_usd_per_day": self.current_metrics.net_profit_usd_per_day,
            "revenue_usd_per_day": self.current_metrics.revenue_usd_per_day,
            "power_cost_per_day": self.current_metrics.power_cost_per_day,
            "break_even_power_cost": self.current_metrics.break_even_price,
            "last_check": self.last_check.isoformat() if self.last_check else None
        }
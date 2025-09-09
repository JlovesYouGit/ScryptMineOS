"""
Economic guardian for Mining OS.
"""
import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)


class EconomicGuardian:
    def __init__(self, min_profit_margin_pct: float):
        self.min_profit_margin_pct = min_profit_margin_pct
        self.current_margin = 0.0

    def is_profitable(self) -> bool:
        """
        Check if mining is profitable based on current conditions.
        
        Returns:
            bool: True if mining is profitable, False otherwise
        """
        # In a real implementation, this would calculate the actual profit margin
        # based on:
        # - Current cryptocurrency prices
        # - Electricity costs
        # - Hardware efficiency
        # - Pool fees
        # - Network difficulty
        
        # For now, we'll simulate a random profitability check
        import random
        self.current_margin = random.uniform(0, 2.0)
        
        profitable = self.current_margin >= self.min_profit_margin_pct
        if not profitable:
            logger.warning(f"Economic guardian blocked mining - margin {self.current_margin:.2f}% below minimum {self.min_profit_margin_pct:.2f}%")
        
        return profitable

    def get_current_margin(self) -> float:
        """Get the current profit margin."""
        return self.current_margin
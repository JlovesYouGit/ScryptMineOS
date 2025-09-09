"""
Configuration management for Mining OS.
"""
import os
import asyncio
from typing import List, Optional
from pydantic import Field
from pydantic_settings import BaseSettings

from .constants import LTC_WALLET_ADDRESS, DOGE_WALLET_ADDRESS, DEFAULT_WORKER_NAME, DEFAULT_MINIMUM_PAYOUT_THRESHOLD


class PoolConfig(BaseSettings):
    """Configuration for a mining pool."""
    host: str
    port: int
    username: str
    password=os.getenv("POOL_PASSWORD", "x")"POOL_PASSWORD", "x") = "x"


class Settings(BaseSettings):
    """Main settings for Mining OS."""
    
    # Server settings
    host: str = "0.0.0.0"
    port: int = 31415
    # SSL settings
    ssl_certfile: Optional[str] = None
    ssl_keyfile: Optional[str] = None
    
    # Pool configuration - using constant wallet addresses
    primary_url: str = "stratum+tcp://ltc.f2pool.com:8888"
    backup_urls: List[str] = Field(default_factory=list)
    worker_name: str = DEFAULT_WORKER_NAME
    minimum_payout_threshold: float = DEFAULT_MINIMUM_PAYOUT_THRESHOLD
    
    # Economic settings
    min_profit_margin_pct: float = 0.5
    
    # Hardware settings
    max_temperature: float = 80.0
    
    # Security settings
    tls_verify: bool = True
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Initialize the payout address lock
        self._payout_address_lock = asyncio.Lock()
        self._payout_address = None

    def get_payout_address(self) -> str:
        """Get the payout address from environment variable."""
        if self._payout_address is None:
            self._payout_address = os.environ.get("PAYOUT_ADDR", "")
        return self._payout_address

    def get_ltc_address(self) -> str:
        """Get the constant LTC wallet address."""
        return LTC_WALLET_ADDRESS

    def get_doge_address(self) -> str:
        """Get the constant DOGE wallet address."""
        return DOGE_WALLET_ADDRESS

    def is_valid(self) -> bool:
        """Check if the configuration is valid."""
        return bool(self.get_payout_address()) and self.get_payout_address() != ""

    def use_ssl(self) -> bool:
        """Check if SSL should be used."""
        return bool(self.ssl_certfile and self.ssl_keyfile)


# Example configuration
EXAMPLE_CONFIG = f"""
primary_url: "stratum+tcp://ltc.f2pool.com:8888"
backup_urls:
  - "stratum+tcp://ltc.f2pool.com:8888"
  - "stratum+tcp://doge.zsolo.bid:8057"
worker_name: "{DEFAULT_WORKER_NAME}"
minimum_payout_threshold: {DEFAULT_MINIMUM_PAYOUT_THRESHOLD}
min_profit_margin_pct: 0.5
max_temperature: 80.0
tls_verify: true
# SSL configuration (uncomment to enable HTTPS)
# ssl_certfile: "/path/to/cert.pem"
# ssl_keyfile: "/path/to/key.pem"
"""
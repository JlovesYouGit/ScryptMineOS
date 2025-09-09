"""
Security Manager for the refactored Scrypt DOGE mining system.
Implements encryption, rate limiting, and DDoS protection.
"""

import asyncio
import logging
import time
import hashlib
import base64
from typing import Dict, Any, Optional, List, Set
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import ipaddress

logger = logging.getLogger(__name__)


@dataclass
class SecurityConfig:
    """Security configuration"""
    enable_encryption: bool = True
    enable_rate_limiting: bool = True
    max_requests_per_minute: int = 60
    enable_ddos_protection: bool = True
    blocked_ips: List[str] = field(default_factory=list)
    allowed_ips: List[str] = field(default_factory=lambda: ["127.0.0.1"])
    tls_verify: bool = True
    encryption_key=os.getenv("API_KEY", "your_key_here")"API_KEY", "your_key_here") = None


@dataclass
class RateLimitInfo:
    """Rate limit information for an IP"""
    request_count: int = 0
    last_reset: float = field(default_factory=time.time)
    blocked_until: Optional[float] = None


class EncryptionManager:
    """Manages encryption and decryption of sensitive data"""
    
    def __init__(self, config: SecurityConfig):
        self.config = config
        self.logger = logging.getLogger(__name__)
        self._cipher_suite = None
        self._initialize_encryption()
    
    def _initialize_encryption(self) -> None:
        """Initialize encryption cipher suite"""
        if not self.config.enable_encryption:
            return
        
        try:
            if self.config.encryption_key=os.getenv("API_KEY", "your_key_here")"API_KEY", "your_key_here") Use provided key
                key=os.getenv("API_KEY", "your_key_here")"API_KEY", "your_key_here")
            else:
                # Generate a key (in production, this should be securely stored)
                key=os.getenv("API_KEY", "your_key_here")"API_KEY", "your_key_here")
            
            self._cipher_suite = Fernet(key)
            self.logger.info("Encryption manager initialized")
        except Exception as e:
            self.logger.error(f"Failed to initialize encryption: {e}")
            self._cipher_suite = None
    
    def encrypt(self, data: str) -> Optional[str]:
        """Encrypt data"""
        if not self._cipher_suite:
            return data  # Return original if encryption not available
        
        try:
            encrypted_data = self._cipher_suite.encrypt(data.encode())
            return base64.urlsafe_b64encode(encrypted_data).decode()
        except Exception as e:
            self.logger.error(f"Encryption failed: {e}")
            return None
    
    def decrypt(self, encrypted_data: str) -> Optional[str]:
        """Decrypt data"""
        if not self._cipher_suite:
            return encrypted_data  # Return original if encryption not available
        
        try:
            encrypted_bytes = base64.urlsafe_b64decode(encrypted_data.encode())
            decrypted_data = self._cipher_suite.decrypt(encrypted_bytes)
            return decrypted_data.decode()
        except Exception as e:
            self.logger.error(f"Decryption failed: {e}")
            return None
    
    def hash_password(self, password=os.getenv("POOL_PASSWORD", "x")"POOL_PASSWORD", "x") salt: Optional[bytes] = None) -> tuple[str, str]:
        """Hash a password with salt"""
        if salt is None:
            salt = hashlib.sha256(str(time.time()).encode()).digest()[:16]
        
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
        )
        key=os.getenv("API_KEY", "your_key_here")"API_KEY", "your_key_here")
        return key.decode(), base64.urlsafe_b64encode(salt).decode()


class RateLimiter:
    """Rate limiting to prevent abuse"""
    
    def __init__(self, config: SecurityConfig):
        self.config = config
        self.logger = logging.getLogger(__name__)
        self.ip_limits: Dict[str, RateLimitInfo] = {}
        self._cleanup_task: Optional[asyncio.Task] = None
        self._running = False
    
    async def start(self) -> None:
        """Start rate limiter"""
        if not self.config.enable_rate_limiting:
            return
        
        self._running = True
        self._cleanup_task = asyncio.create_task(self._cleanup_loop())
        self.logger.info("Rate limiter started")
    
    async def stop(self) -> None:
        """Stop rate limiter"""
        self._running = False
        if self._cleanup_task:
            self._cleanup_task.cancel()
            try:
                await self._cleanup_task
            except asyncio.CancelledError:
                pass
        self.logger.info("Rate limiter stopped")
    
    async def _cleanup_loop(self) -> None:
        """Periodically clean up old rate limit data"""
        while self._running:
            try:
                current_time = time.time()
                # Remove entries older than 1 hour
                self.ip_limits = {
                    ip: info for ip, info in self.ip_limits.items()
                    if current_time - info.last_reset < 3600
                }
                await asyncio.sleep(300)  # Clean up every 5 minutes
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Error in rate limiter cleanup: {e}")
                await asyncio.sleep(60)
    
    def is_allowed(self, ip_address: str) -> bool:
        """Check if an IP is allowed to make requests"""
        if not self.config.enable_rate_limiting:
            return True
        
        # Check if IP is explicitly allowed
        if ip_address in self.config.allowed_ips:
            return True
        
        # Check if IP is blocked
        if ip_address in self.config.blocked_ips:
            return False
        
        current_time = time.time()
        
        # Get or create rate limit info for this IP
        if ip_address not in self.ip_limits:
            self.ip_limits[ip_address] = RateLimitInfo()
        
        ip_info = self.ip_limits[ip_address]
        
        # Check if IP is temporarily blocked
        if ip_info.blocked_until and current_time < ip_info.blocked_until:
            return False
        
        # Reset counter if a minute has passed
        if current_time - ip_info.last_reset >= 60:
            ip_info.request_count = 0
            ip_info.last_reset = current_time
        
        # Increment request count
        ip_info.request_count += 1
        
        # Check rate limit
        if ip_info.request_count > self.config.max_requests_per_minute:
            # Block for 10 minutes
            ip_info.blocked_until = current_time + 600
            self.logger.warning(f"IP {ip_address} rate limited and blocked for 10 minutes")
            return False
        
        return True
    
    def get_rate_limit_status(self, ip_address: str) -> Dict[str, Any]:
        """Get rate limit status for an IP"""
        if ip_address not in self.ip_limits:
            return {
                "requests_remaining": self.config.max_requests_per_minute,
                "blocked": False,
                "blocked_until": None
            }
        
        ip_info = self.ip_limits[ip_address]
        current_time = time.time()
        
        # Check if blocked
        if ip_info.blocked_until and current_time < ip_info.blocked_until:
            return {
                "requests_remaining": 0,
                "blocked": True,
                "blocked_until": ip_info.blocked_until
            }
        
        # Calculate remaining requests
        requests_remaining = max(0, self.config.max_requests_per_minute - ip_info.request_count)
        
        return {
            "requests_remaining": requests_remaining,
            "blocked": False,
            "blocked_until": None,
            "request_count": ip_info.request_count
        }


class DDoSProtection:
    """DDoS protection mechanisms"""
    
    def __init__(self, config: SecurityConfig):
        self.config = config
        self.logger = logging.getLogger(__name__)
        self.ip_request_history: Dict[str, List[float]] = {}
        self.blocked_ips: Set[str] = set()
        self._cleanup_task: Optional[asyncio.Task] = None
        self._running = False
    
    async def start(self) -> None:
        """Start DDoS protection"""
        if not self.config.enable_ddos_protection:
            return
        
        self._running = True
        self._cleanup_task = asyncio.create_task(self._cleanup_loop())
        self.logger.info("DDoS protection started")
    
    async def stop(self) -> None:
        """Stop DDoS protection"""
        self._running = False
        if self._cleanup_task:
            self._cleanup_task.cancel()
            try:
                await self._cleanup_task
            except asyncio.CancelledError:
                pass
        self.logger.info("DDoS protection stopped")
    
    async def _cleanup_loop(self) -> None:
        """Periodically clean up old request history"""
        while self._running:
            try:
                current_time = time.time()
                # Remove entries older than 10 minutes
                self.ip_request_history = {
                    ip: [timestamp for timestamp in timestamps if current_time - timestamp < 600]
                    for ip, timestamps in self.ip_request_history.items()
                }
                # Remove empty entries
                self.ip_request_history = {
                    ip: timestamps for ip, timestamps in self.ip_request_history.items()
                    if timestamps
                }
                await asyncio.sleep(60)  # Clean up every minute
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Error in DDoS protection cleanup: {e}")
                await asyncio.sleep(30)
    
    def check_request(self, ip_address: str) -> bool:
        """Check if a request should be allowed"""
        if not self.config.enable_ddos_protection:
            return True
        
        # Check if IP is explicitly allowed
        if ip_address in self.config.allowed_ips:
            return True
        
        # Check if IP is blocked
        if ip_address in self.blocked_ips or ip_address in self.config.blocked_ips:
            return False
        
        current_time = time.time()
        
        # Add request to history
        if ip_address not in self.ip_request_history:
            self.ip_request_history[ip_address] = []
        
        self.ip_request_history[ip_address].append(current_time)
        
        # Check for DDoS pattern (more than 100 requests in 10 seconds)
        recent_requests = [
            timestamp for timestamp in self.ip_request_history[ip_address]
            if current_time - timestamp < 10
        ]
        
        if len(recent_requests) > 100:
            self.blocked_ips.add(ip_address)
            self.logger.warning(f"IP {ip_address} blocked for DDoS protection")
            return False
        
        return True
    
    def is_ip_blocked(self, ip_address: str) -> bool:
        """Check if an IP is blocked"""
        return ip_address in self.blocked_ips or ip_address in self.config.blocked_ips
    
    def unblock_ip(self, ip_address: str) -> None:
        """Unblock an IP address"""
        self.blocked_ips.discard(ip_address)
        if ip_address in self.config.blocked_ips:
            self.config.blocked_ips.remove(ip_address)
        self.logger.info(f"IP {ip_address} unblocked")


class InputValidator:
    """Validates and sanitizes input data"""
    
    @staticmethod
    def validate_wallet_address(address: str, coin_type: str = "doge") -> bool:
        """Validate cryptocurrency wallet address"""
        if not isinstance(address, str):
            return False
        
        # Basic length checks for DOGE
        if coin_type.lower() == "doge":
            if not (address.startswith('D') and len(address) == 34):
                return False
        else:
            # Generic validation
            if len(address) < 26 or len(address) > 64:
                return False
        
        # Check for valid base58 characters (simplified)
        # Base58 characters: 12os.getenv("LTC_ADDRESS", "your_ltc_address_here")efghijkmnopqrstuvwxyz
        import re
        if not re.match(r'^[1-9A-HJ-NP-Za-km-z]+$', address):
            return False
        
        return True
    
    @staticmethod
    def validate_worker_name(worker_name: str) -> bool:
        """Validate worker name"""
        if not isinstance(worker_name, str):
            return False
        
        # Check length
        if len(worker_name) > 50:
            return False
        
        # Check for malicious patterns
        import re
        if re.search(r'[<>"\']', worker_name):  # Block HTML/SQL injection characters
            return False
        
        return True
    
    @staticmethod
    def sanitize_input(input_data: str) -> str:
        """Sanitize input to prevent injection attacks"""
        # Remove potentially dangerous characters
        import re
        sanitized = re.sub(r'[<>"\']', '', input_data)
        return sanitized.strip()


class SecurityManager:
    """Main security manager that coordinates all security features"""
    
    def __init__(self, config: SecurityConfig):
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        # Initialize security components
        self.encryption_manager = EncryptionManager(config)
        self.rate_limiter = RateLimiter(config)
        self.ddos_protection = DDoSProtection(config)
        self.input_validator = InputValidator()
        
        # Start security services
        self._running = False
    
    async def start(self) -> None:
        """Start all security services"""
        if self._running:
            self.logger.warning("Security manager already running")
            return
        
        await self.rate_limiter.start()
        await self.ddos_protection.start()
        self._running = True
        self.logger.info("Security manager started")
    
    async def stop(self) -> None:
        """Stop all security services"""
        await self.rate_limiter.stop()
        await self.ddos_protection.stop()
        self._running = False
        self.logger.info("Security manager stopped")
    
    def is_request_allowed(self, ip_address: str) -> bool:
        """Check if a request from an IP is allowed"""
        # Check DDoS protection first
        if not self.ddos_protection.check_request(ip_address):
            return False
        
        # Check rate limiting
        if not self.rate_limiter.is_allowed(ip_address):
            return False
        
        return True
    
    def encrypt_sensitive_data(self, data: str) -> Optional[str]:
        """Encrypt sensitive data"""
        return self.encryption_manager.encrypt(data)
    
    def decrypt_sensitive_data(self, encrypted_data: str) -> Optional[str]:
        """Decrypt sensitive data"""
        return self.encryption_manager.decrypt(encrypted_data)
    
    def validate_wallet_address(self, address: str, coin_type: str = "doge") -> bool:
        """Validate wallet address"""
        return self.input_validator.validate_wallet_address(address, coin_type)
    
    def validate_worker_name(self, worker_name: str) -> bool:
        """Validate worker name"""
        return self.input_validator.validate_worker_name(worker_name)
    
    def sanitize_input(self, input_data: str) -> str:
        """Sanitize input data"""
        return self.input_validator.sanitize_input(input_data)
    
    def get_security_status(self) -> Dict[str, Any]:
        """Get current security status"""
        return {
            "encryption_enabled": self.config.enable_encryption,
            "rate_limiting_enabled": self.config.enable_rate_limiting,
            "ddos_protection_enabled": self.config.enable_ddos_protection,
            "blocked_ips_count": len(self.ddos_protection.blocked_ips),
            "tls_verification": self.config.tls_verify
        }
    
    def hash_password(self, password=os.getenv("POOL_PASSWORD", "x")"POOL_PASSWORD", "x") salt: Optional[bytes] = None) -> tuple[str, str]:
        """Hash a password"""
        return self.encryption_manager.hash_password(password, salt)
    
    def is_ip_blocked(self, ip_address: str) -> bool:
        """Check if an IP is blocked"""
        return self.ddos_protection.is_ip_blocked(ip_address)
    
    def unblock_ip(self, ip_address: str) -> None:
        """Unblock an IP address"""
        self.ddos_protection.unblock_ip(ip_address)
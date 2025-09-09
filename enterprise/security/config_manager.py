"""
Enterprise Configuration Management System
Secure environment variable handling with access control
"""

import os
import json
import hashlib
import logging
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
import secrets
from datetime import datetime
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import base64

logger = logging.getLogger(__name__)

class AccessLevel(Enum):
    """Access control levels for configuration data"""
    PUBLIC = "public"           # Anyone can read
    USER = "user"              # Authenticated users can read/write their own data
    COLLABORATOR = "collaborator"  # Approved collaborators can read
    CREATOR = "creator"        # Creator has full access
    SYSTEM = "system"          # System-level access only

@dataclass
class ConfigItem:
    """Secure configuration item with access control"""
    key=os.getenv("API_KEY", "your_key_here")
    value: Any
    access_level: AccessLevel
    encrypted: bool = False
    description: str = ""
    owner: Optional[str] = None
    created_by: str = "system"
    last_modified: Optional[str] = None

@dataclass
class UserProfile:
    """User profile with access permissions"""
    user_id: str
    username: str
    access_level: AccessLevel
    wallet_addresses: Dict[str, str] = field(default_factory=dict)
    api_keys: Dict[str, str] = field(default_factory=dict)
    created_at: str = ""
    last_login: str = ""

class SecureConfigManager:
    """Enterprise-grade configuration manager with encryption and access control"""
    
    def __init__(self, creator_id: str = "creator"):
        self.creator_id = creator_id
        self.encryption_key=os.getenv("API_KEY", "your_key_here")
        self.cipher_suite = Fernet(self.encryption_key)
        self.config_items: Dict[str, ConfigItem] = {}
        self.users: Dict[str, UserProfile] = {}
        self.audit_log: List[Dict[str, Any]] = []
        
        # Initialize creator profile
        self._initialize_creator()
        self._load_secure_config()
    
    def _get_or_create_encryption_key(self) -> bytes:
        """Get or create encryption key from environment"""
        key_env = os.getenv('ENTERPRISE_ENCRYPTION_KEY')
        if key_env:
            return base64.urlsafe_b64decode(key_env.encode())
        
        # Generate new key
        password=os.getenv("POOL_PASSWORD", "x") 'default_password').encode()
        salt = os.getenv('ENTERPRISE_SALT', 'default_salt').encode()
        
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
        )
        key=os.getenv("API_KEY", "your_key_here")
        
        logger.warning("Generated new encryption key. Set ENTERPRISE_ENCRYPTION_KEY environment variable.")
        return key
    
    def _initialize_creator(self):
        """Initialize creator profile with full access"""
        creator_profile = UserProfile(
            user_id=self.creator_id,
            username="creator",
            access_level=AccessLevel.CREATOR,
            wallet_addresses={
                "ltc": os.getenv('CREATOR_LTC_ADDRESS', ''),
                "doge": os.getenv('CREATOR_DOGE_ADDRESS', ''),
            }
        )
        self.users[self.creator_id] = creator_profile
    
    def _load_secure_config(self):
        """Load configuration from environment variables"""
        # System configuration (creator-only access)
        system_configs = {
            'MONGODB_URI': AccessLevel.CREATOR,
            'ENTERPRISE_API_KEY': AccessLevel.CREATOR,
            'SYSTEM_ADMIN_TOKEN': AccessLevel.CREATOR,
            'CREATOR_LTC_ADDRESS': AccessLevel.CREATOR,
            'CREATOR_DOGE_ADDRESS': AccessLevel.CREATOR,
        }
        
        # User-configurable settings
        user_configs = {
            'WORKER_NAME': AccessLevel.USER,
            'TARGET_HASHRATE': AccessLevel.USER,
            'POWER_LIMIT': AccessLevel.USER,
        }
        
        # Public configuration
        public_configs = {
            'LTC_POOL_HOST': AccessLevel.PUBLIC,
            'DOGE_POOL_HOST': AccessLevel.PUBLIC,
            'LTC_POOL_PORT': AccessLevel.PUBLIC,
            'DOGE_POOL_PORT': AccessLevel.PUBLIC,
            'METRICS_PORT': AccessLevel.PUBLIC,
        }
        
        # Load all configurations
        all_configs = {**system_configs, **user_configs, **public_configs}
        
        for key, access_level in all_configs.items():
            value = os.getenv(key)
            if value:
                encrypted = access_level in [AccessLevel.CREATOR, AccessLevel.SYSTEM]
                self.config_items[key] = ConfigItem(
                    key=os.getenv("API_KEY", "your_key_here")
                    value=self._encrypt_if_needed(value, encrypted),
                    access_level=access_level,
                    encrypted=encrypted,
                    description=f"Environment variable: {key}",
                    created_by=self.creator_id
                )
    
    def _encrypt_if_needed(self, value: str, encrypt: bool) -> str:
        """Encrypt value if needed"""
        if encrypt and value:
            return self.cipher_suite.encrypt(value.encode()).decode()
        return value
    
    def _decrypt_if_needed(self, value: str, encrypted: bool) -> str:
        """Decrypt value if needed"""
        if encrypted and value:
            try:
                return self.cipher_suite.decrypt(value.encode()).decode()
            except Exception as e:
                logger.error(f"Failed to decrypt value: {e}")
                return ""
        return value
    
    def add_user(self, user_id: str, username: str, access_level: AccessLevel, 
                 requester_id: str) -> bool:
        """Add new user (creator-only operation)"""
        if not self._check_access(requester_id, AccessLevel.CREATOR):
            self._audit_log("add_user", requester_id, "DENIED", f"Insufficient permissions")
            return False
        
        if user_id in self.users:
            return False
        
        self.users[user_id] = UserProfile(
            user_id=user_id,
            username=username,
            access_level=access_level
        )
        
        self._audit_log("add_user", requester_id, "SUCCESS", f"Added user {username}")
        return True
    
    def update_user_wallet(self, user_id: str, coin: str, address: str, 
                          requester_id: str) -> bool:
        """Update user's wallet address (user can update their own)"""
        if requester_id != user_id and not self._check_access(requester_id, AccessLevel.CREATOR):
            self._audit_log("update_wallet", requester_id, "DENIED", 
                          f"Cannot update wallet for user {user_id}")
            return False
        
        if user_id not in self.users:
            return False
        
        # Validate wallet address format
        if not self._validate_wallet_address(coin, address):
            self._audit_log("update_wallet", requester_id, "FAILED", 
                          f"Invalid {coin} address format")
            return False
        
        self.users[user_id].wallet_addresses[coin] = address
        self._audit_log("update_wallet", requester_id, "SUCCESS", 
                       f"Updated {coin} wallet for user {user_id}")
        return True
    
    def get_config(self, key=os.getenv("API_KEY", "your_key_here") requester_id: str, default: Any = None) -> Any:
        """Get configuration value with access control"""
        if key not in self.config_items:
            return default
        
        config_item = self.config_items[key]
        
        # Check access permissions
        if not self._check_config_access(config_item, requester_id):
            self._audit_log("get_config", requester_id, "DENIED", f"Access denied for {key}")
            return default
        
        value = self._decrypt_if_needed(config_item.value, config_item.encrypted)
        self._audit_log("get_config", requester_id, "SUCCESS", f"Retrieved {key}")
        return value
    
    def set_config(self, key=os.getenv("API_KEY", "your_key_here") value: Any, requester_id: str, 
                   access_level: AccessLevel = AccessLevel.USER) -> bool:
        """Set configuration value with access control"""
        # Only creator can set system-level configs
        if access_level in [AccessLevel.CREATOR, AccessLevel.SYSTEM]:
            if not self._check_access(requester_id, AccessLevel.CREATOR):
                self._audit_log("set_config", requester_id, "DENIED", 
                              f"Cannot set system config {key}")
                return False
        
        encrypted = access_level in [AccessLevel.CREATOR, AccessLevel.SYSTEM]
        
        self.config_items[key] = ConfigItem(
            key=os.getenv("API_KEY", "your_key_here")
            value=self._encrypt_if_needed(str(value), encrypted),
            access_level=access_level,
            encrypted=encrypted,
            created_by=requester_id
        )
        
        self._audit_log("set_config", requester_id, "SUCCESS", f"Set config {key}")
        return True
    
    def get_user_wallet(self, user_id: str, coin: str, requester_id: str) -> Optional[str]:
        """Get user's wallet address"""
        if requester_id != user_id and not self._check_access(requester_id, AccessLevel.CREATOR):
            self._audit_log("get_wallet", requester_id, "DENIED", 
                          f"Cannot access wallet for user {user_id}")
            return None
        
        if user_id not in self.users:
            return None
        
        address = self.users[user_id].wallet_addresses.get(coin)
        if address:
            self._audit_log("get_wallet", requester_id, "SUCCESS", 
                          f"Retrieved {coin} wallet for user {user_id}")
        return address
    
    def _check_access(self, user_id: str, required_level: AccessLevel) -> bool:
        """Check if user has required access level"""
        if user_id not in self.users:
            return False
        
        user_level = self.users[user_id].access_level
        
        # Access level hierarchy
        level_hierarchy = {
            AccessLevel.PUBLIC: 0,
            AccessLevel.USER: 1,
            AccessLevel.COLLABORATOR: 2,
            AccessLevel.CREATOR: 3,
            AccessLevel.SYSTEM: 3
        }
        
        return level_hierarchy.get(user_level, 0) >= level_hierarchy.get(required_level, 0)
    
    def _check_config_access(self, config_item: ConfigItem, requester_id: str) -> bool:
        """Check if user can access specific config item"""
        if config_item.access_level == AccessLevel.PUBLIC:
            return True
        
        if config_item.owner and config_item.owner == requester_id:
            return True
        
        return self._check_access(requester_id, config_item.access_level)
    
    def _validate_wallet_address(self, coin: str, address: str) -> bool:
        """Validate wallet address format"""
        if coin.lower() == 'ltc':
            return (address.startswith('ltc1') or 
                   address.startswith('L') or 
                   address.startswith('M') or
                   address.startswith('3'))
        elif coin.lower() == 'doge':
            return address.startswith('D')
        return True  # Allow other coins
    
    def _audit_log(self, action: str, user_id: str, result: str, details: str):
        """Log security events"""
        log_entry = {
            'timestamp': datetime.now().isoformat(),
            'action': action,
            'user_id': user_id,
            'result': result,
            'details': details,
            'ip_address': os.getenv('REMOTE_ADDR', 'unknown')
        }
        self.audit_log.append(log_entry)
        
        # Log to system logger
        logger.info(f"AUDIT: {action} by {user_id} - {result}: {details}")
    
    def get_audit_log(self, requester_id: str, limit: int = 100) -> List[Dict[str, Any]]:
        """Get audit log (creator-only)"""
        if not self._check_access(requester_id, AccessLevel.CREATOR):
            return []
        
        return self.audit_log[-limit:]
    
    def hide_sensitive_files(self, requester_id: str) -> List[str]:
        """Get list of files that should be hidden from user"""
        if self._check_access(requester_id, AccessLevel.CREATOR):
            return []  # Creator can see everything
        
        # Files to hide from non-creators
        hidden_files = [
            'BYTEROVER_MCP_HANDBOOK*.md',
            'AGENT.md',
            'CLAUDE.md',
            '.env',
            'enterprise/security/',
            'enterprise/auth/',
            'creator_configs/',
            '*.key',
            '*.pem',
            'secrets/',
        ]
        
        return hidden_files
    
    def export_user_config(self, user_id: str, requester_id: str) -> Optional[Dict[str, Any]]:
        """Export user's configuration (user can export their own)"""
        if requester_id != user_id and not self._check_access(requester_id, AccessLevel.CREATOR):
            return None
        
        if user_id not in self.users:
            return None
        
        user = self.users[user_id]
        
        # Export user-accessible configuration
        user_config = {
            'user_info': {
                'user_id': user.user_id,
                'username': user.username,
                'access_level': user.access_level.value
            },
            'wallet_addresses': user.wallet_addresses,
            'mining_config': {}
        }
        
        # Add user-accessible config items
        for key, config_item in self.config_items.items():
            if (config_item.access_level in [AccessLevel.PUBLIC, AccessLevel.USER] or
                config_item.owner == user_id):
                user_config['mining_config'][key] = self._decrypt_if_needed(
                    config_item.value, config_item.encrypted)
        
        self._audit_log("export_config", requester_id, "SUCCESS", f"Exported config for {user_id}")
        return user_config

# Global instance
_config_manager = None

def get_config_manager() -> SecureConfigManager:
    """Get global configuration manager instance"""
    global _config_manager
    if _config_manager is None:
        _config_manager = SecureConfigManager()
    return _config_manager

def init_config_manager(creator_id: str = "creator") -> SecureConfigManager:
    """Initialize configuration manager with creator ID"""
    global _config_manager
    _config_manager = SecureConfigManager(creator_id)
    return _config_manager

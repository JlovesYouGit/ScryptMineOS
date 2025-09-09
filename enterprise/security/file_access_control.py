"""
Enterprise File Access Control System
Restricts access to sensitive files based on user permissions
"""

import os
import fnmatch
import logging
from typing import List, Dict, Set, Optional
from pathlib import Path
from .config_manager import get_config_manager, AccessLevel

logger = logging.getLogger(__name__)

class FileAccessController:
    """Controls access to sensitive files and directories"""
    
    def __init__(self):
        self.config_manager = get_config_manager()
        
        # Define sensitive file patterns (creator-only access)
        self.creator_only_patterns = [
            'BYTEROVER_MCP_HANDBOOK*.md',
            'AGENT.md',
            'CLAUDE.md',
            '.env',
            '.env.*',
            'enterprise/security/*',
            'enterprise/auth/*',
            'creator_configs/*',
            '*.key',
            '*.pem',
            'secrets/*',
            'private/*',
            '*.secret',
            'mongodb_credentials.*',
            'api_keys.*',
            'master_config.*',
        ]
        
        # Define collaborator-accessible patterns
        self.collaborator_patterns = [
            'README.md',
            'docs/*',
            'examples/*',
            'tests/*',
            'requirements.txt',
            'pyproject.toml',
            'setup.py',
        ]
        
        # Define user-modifiable patterns (users can modify their own configs)
        self.user_modifiable_patterns = [
            'user_configs/{user_id}/*',
            'mining_configs/{user_id}/*',
            'worker_configs/{user_id}/*',
        ]
    
    def can_access_file(self, file_path: str, user_id: str, operation: str = 'read') -> bool:
        """Check if user can access a file"""
        try:
            # Get user access level
            if user_id not in self.config_manager.users:
                logger.warning(f"Unknown user {user_id} attempted to access {file_path}")
                return False
            
            user_level = self.config_manager.users[user_id].access_level
            
            # Creator has access to everything
            if user_level == AccessLevel.CREATOR:
                return True
            
            # Check if file is in creator-only patterns
            if self._matches_patterns(file_path, self.creator_only_patterns):
                self.config_manager._audit_log(
                    f"file_access_{operation}", user_id, "DENIED", 
                    f"Creator-only file: {file_path}"
                )
                return False
            
            # Check collaborator access
            if user_level == AccessLevel.COLLABORATOR:
                if self._matches_patterns(file_path, self.collaborator_patterns):
                    return True
                # Collaborators can read most files but not modify sensitive ones
                if operation == 'read':
                    return not self._is_sensitive_file(file_path)
                else:
                    return False
            
            # Check user access
            if user_level == AccessLevel.USER:
                # Users can access their own config files
                user_specific_patterns = [
                    pattern.format(user_id=user_id) 
                    for pattern in self.user_modifiable_patterns
                ]
                
                if self._matches_patterns(file_path, user_specific_patterns):
                    return True
                
                # Users can read public files
                if operation == 'read':
                    return not self._is_sensitive_file(file_path)
                else:
                    return False
            
            # Default deny
            return False
            
        except Exception as e:
            logger.error(f"Error checking file access for {user_id}: {e}")
            return False
    
    def get_accessible_files(self, directory: str, user_id: str) -> List[str]:
        """Get list of files user can access in directory"""
        accessible_files = []
        
        try:
            for root, dirs, files in os.walk(directory):
                for file in files:
                    file_path = os.path.join(root, file)
                    relative_path = os.path.relpath(file_path, directory)
                    
                    if self.can_access_file(relative_path, user_id, 'read'):
                        accessible_files.append(relative_path)
            
        except Exception as e:
            logger.error(f"Error listing accessible files for {user_id}: {e}")
        
        return accessible_files
    
    def hide_sensitive_content(self, content: str, user_id: str) -> str:
        """Hide sensitive content from non-authorized users"""
        if user_id not in self.config_manager.users:
            return "[ACCESS DENIED]"
        
        user_level = self.config_manager.users[user_id].access_level
        
        # Creator sees everything
        if user_level == AccessLevel.CREATOR:
            return content
        
        # Hide sensitive patterns from content
        sensitive_patterns = [
            r'mongodb\+srv://[^/]+/[^/]+',  # MongoDB URIs
            r'[A-Za-z0-9]{64}',  # API keys (64 char hex)
            r'ltc1q[a-zA-Z0-9]{39}',  # LTC addresses
            r'D[5-9A-HJ-NP-U][1-9A-HJ-NP-Za-km-z]{32}',  # DOGE addresses
            r'password["\s]*[:=]["\s]*[^"\s]+',  # Passwords
            r'secret["\s]*[:=]["\s]*[^"\s]+',  # Secrets
            r'key["\s]*[:=]["\s]*[^"\s]+',  # Keys
        ]
        
        import re
        hidden_content = content
        
        for pattern in sensitive_patterns:
            hidden_content = re.sub(pattern, '[REDACTED]', hidden_content, flags=re.IGNORECASE)
        
        return hidden_content
    
    def create_user_directory(self, user_id: str, requester_id: str) -> bool:
        """Create user-specific directory structure"""
        if not self.config_manager._check_access(requester_id, AccessLevel.CREATOR):
            return False
        
        try:
            user_dirs = [
                f'user_configs/{user_id}',
                f'mining_configs/{user_id}',
                f'worker_configs/{user_id}',
                f'logs/{user_id}',
            ]
            
            for dir_path in user_dirs:
                os.makedirs(dir_path, exist_ok=True)
                
                # Create .gitkeep file
                gitkeep_path = os.path.join(dir_path, '.gitkeep')
                with open(gitkeep_path, 'w') as f:
                    f.write(f"User directory for {user_id}\n")
            
            self.config_manager._audit_log(
                "create_user_dir", requester_id, "SUCCESS", 
                f"Created directories for user {user_id}"
            )
            return True
            
        except Exception as e:
            logger.error(f"Error creating user directory for {user_id}: {e}")
            return False
    
    def _matches_patterns(self, file_path: str, patterns: List[str]) -> bool:
        """Check if file path matches any of the patterns"""
        for pattern in patterns:
            if fnmatch.fnmatch(file_path, pattern):
                return True
        return False
    
    def _is_sensitive_file(self, file_path: str) -> bool:
        """Check if file contains sensitive information"""
        sensitive_extensions = ['.key', '.pem', '.secret', '.env']
        sensitive_names = ['password', 'secret', 'credential', 'private', 'mongodb']
        
        # Check extension
        for ext in sensitive_extensions:
            if file_path.endswith(ext):
                return True
        
        # Check filename contains sensitive words
        file_lower = file_path.lower()
        for name in sensitive_names:
            if name in file_lower:
                return True
        
        return False
    
    def get_file_permissions(self, file_path: str, user_id: str) -> Dict[str, bool]:
        """Get detailed file permissions for user"""
        return {
            'read': self.can_access_file(file_path, user_id, 'read'),
            'write': self.can_access_file(file_path, user_id, 'write'),
            'delete': self.can_access_file(file_path, user_id, 'delete'),
            'execute': self.can_access_file(file_path, user_id, 'execute'),
        }
    
    def secure_file_listing(self, directory: str, user_id: str) -> List[Dict[str, any]]:
        """Get secure file listing with permissions"""
        files = []
        
        try:
            for root, dirs, filenames in os.walk(directory):
                for filename in filenames:
                    file_path = os.path.join(root, filename)
                    relative_path = os.path.relpath(file_path, directory)
                    
                    if self.can_access_file(relative_path, user_id, 'read'):
                        file_info = {
                            'path': relative_path,
                            'name': filename,
                            'size': os.path.getsize(file_path) if os.path.exists(file_path) else 0,
                            'permissions': self.get_file_permissions(relative_path, user_id),
                            'is_sensitive': self._is_sensitive_file(relative_path)
                        }
                        files.append(file_info)
            
        except Exception as e:
            logger.error(f"Error creating secure file listing: {e}")
        
        return files

# Global instance
_file_access_controller = None

def get_file_access_controller() -> FileAccessController:
    """Get global file access controller instance"""
    global _file_access_controller
    if _file_access_controller is None:
        _file_access_controller = FileAccessController()
    return _file_access_controller

#!/usr/bin/env python3
"""
Enterprise Codebase Sanitization Script
Removes all hardcoded sensitive data and replaces with secure environment variables
"""

import os
import re
import glob
import logging
from typing import List, Dict, Tuple
from pathlib import Path

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class CodebaseSanitizer:
    """Sanitizes codebase by removing hardcoded sensitive data"""
    
    def __init__(self):
        self.sensitive_patterns = {
            # Wallet addresses
            'ltc_addresses': [
                r'ltc1q[a-zA-Z0-9]{39}',
                r'[LM][a-km-zA-HJ-NP-Z1-9]{26,33}',
                r'3[a-km-zA-HJ-NP-Z1-9]{25,34}'
            ],
            'doge_addresses': [
                r'D[5-9A-HJ-NP-U][1-9A-HJ-NP-Za-km-z]{32}'
            ],
            # MongoDB URIs
            'mongodb_uris': [
                r'mongodb\+srv://[^/\s]+/[^\s"\']+',
                r'os.getenv("MONGODB_URI", "mongodb://localhost:27017/mining")"\']+'
            ],
            # API keys and secrets
            'api_keys': [
                r'["\']?[A-Za-z0-9]{32,}["\']?',  # Generic long strings
                r'password["\s]*[:=]["\s]*[^"\s]+',
                r'secret["\s]*[:=]["\s]*[^"\s]+',
                r'key["\s]*[:=]["\s]*[^"\s]+',
                r'token["\s]*[:=]["\s]*[^"\s]+'
            ]
        }
        
        # Files to exclude from sanitization
        self.exclude_patterns = [
            '*.pyc',
            '__pycache__/*',
            '.git/*',
            'node_modules/*',
            '*.log',
            'enterprise/security/*',  # Don't sanitize security files
            '.env.enterprise',        # Don't sanitize enterprise config
        ]
        
        # Replacement mappings
        self.replacements = {}
        self.sanitized_files = []
    
    def scan_codebase(self, root_dir: str = '.') -> Dict[str, List[str]]:
        """Scan codebase for sensitive data"""
        findings = {category: [] for category in self.sensitive_patterns.keys()}
        
        for root, dirs, files in os.walk(root_dir):
            # Skip excluded directories
            dirs[:] = [d for d in dirs if not self._should_exclude(os.path.join(root, d))]
            
            for file in files:
                file_path = os.path.join(root, file)
                
                if self._should_exclude(file_path):
                    continue
                
                if file.endswith(('.py', '.md', '.txt', '.yaml', '.yml', '.toml', '.env')):
                    file_findings = self._scan_file(file_path)
                    for category, items in file_findings.items():
                        findings[category].extend([(file_path, item) for item in items])
        
        return findings
    
    def _scan_file(self, file_path: str) -> Dict[str, List[str]]:
        """Scan individual file for sensitive data"""
        findings = {category: [] for category in self.sensitive_patterns.keys()}
        
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            
            for category, patterns in self.sensitive_patterns.items():
                for pattern in patterns:
                    matches = re.findall(pattern, content, re.IGNORECASE)
                    findings[category].extend(matches)
        
        except Exception as e:
            logger.warning(f"Could not scan {file_path}: {e}")
        
        return findings
    
    def sanitize_file(self, file_path: str) -> bool:
        """Sanitize a single file"""
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            
            original_content = content
            
            # Replace wallet addresses
            content = self._replace_wallet_addresses(content)
            
            # Replace MongoDB URIs
            content = self._replace_mongodb_uris(content)
            
            # Replace API keys and secrets
            content = self._replace_api_keys(content)
            
            # Replace hardcoded pool users
            content = self._replace_pool_users(content)
            
            # Only write if content changed
            if content != original_content:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                
                self.sanitized_files.append(file_path)
                logger.info(f"Sanitized: {file_path}")
                return True
        
        except Exception as e:
            logger.error(f"Failed to sanitize {file_path}: {e}")
        
        return False
    
    def _replace_wallet_addresses(self, content: str) -> str:
        """Replace hardcoded wallet addresses with environment variables"""
        # LTC addresses
        ltc_pattern = r'(ltc1q[a-zA-Z0-9]{39}|[LM][a-km-zA-HJ-NP-Z1-9]{26,33}|3[a-km-zA-HJ-NP-Z1-9]{25,34})'
        content = re.sub(ltc_pattern, 'os.getenv("LTC_ADDRESS", "your_ltc_address_here")', content)
        
        # DOGE addresses
        doge_pattern = r'D[5-9A-HJ-NP-U][1-9A-HJ-NP-Za-km-z]{32}'
        content = re.sub(doge_pattern, 'os.getenv("DOGE_ADDRESS", "your_doge_address_here")', content)
        
        return content
    
    def _replace_mongodb_uris(self, content: str) -> str:
        """Replace MongoDB URIs with environment variables"""
        mongodb_pattern = r'mongodb(\+srv)?://[^/\s"\']+/[^\s"\']+'
        content = re.sub(mongodb_pattern, 'os.getenv("MONGODB_URI", "os.getenv("MONGODB_URI", "mongodb://localhost:27017/mining")")', content)
        
        return content
    
    def _replace_api_keys(self, content: str) -> str:
        """Replace API keys and secrets with environment variables"""
        # Password fields
        content = re.sub(
            r'password["\s]*[:=]["\s]*[^"\s]+',
            'password=os.getenv("POOL_PASSWORD", "x")"POOL_PASSWORD", "x")',
            content,
            flags=re.IGNORECASE
        )
        
        # Secret fields
        content = re.sub(
            r'secret["\s]*[:=]["\s]*[^"\s]+',
            'secret=os.getenv("API_SECRET", "your_secret_here")"API_SECRET", "your_secret_here")',
            content,
            flags=re.IGNORECASE
        )
        
        # Key fields
        content = re.sub(
            r'key["\s]*[:=]["\s]*[^"\s]+',
            'key=os.getenv("API_KEY", "your_key_here")"API_KEY", "your_key_here")',
            content,
            flags=re.IGNORECASE
        )
        
        return content
    
    def _replace_pool_users(self, content: str) -> str:
        """Replace hardcoded pool user strings"""
        # Common hardcoded pool users
        hardcoded_users = [
            'os.getenv("DOGE_ADDRESS", "your_doge_address_here")',
            os.getenv("POOL_USER", "your_wallet_address.worker_name"),
            os.getenv("POOL_USER", "your_wallet_address.worker_name")
        ]
        
        for user in hardcoded_users:
            content = content.replace(
                f'"{user}"',
                'os.getenv("POOL_USER", "your_wallet_address.worker_name")'
            )
            content = content.replace(
                f"'{user}'",
                'os.getenv("POOL_USER", "your_wallet_address.worker_name")'
            )
        
        return content
    
    def _should_exclude(self, path: str) -> bool:
        """Check if path should be excluded from sanitization"""
        for pattern in self.exclude_patterns:
            if Path(path).match(pattern):
                return True
        return False
    
    def sanitize_codebase(self, root_dir: str = '.') -> Dict[str, any]:
        """Sanitize entire codebase"""
        logger.info("Starting codebase sanitization...")
        
        # First, scan for sensitive data
        findings = self.scan_codebase(root_dir)
        
        # Log findings
        total_findings = sum(len(items) for items in findings.values())
        logger.info(f"Found {total_findings} potential sensitive data items")
        
        for category, items in findings.items():
            if items:
                logger.info(f"{category}: {len(items)} items found")
        
        # Sanitize files
        sanitized_count = 0
        for root, dirs, files in os.walk(root_dir):
            dirs[:] = [d for d in dirs if not self._should_exclude(os.path.join(root, d))]
            
            for file in files:
                file_path = os.path.join(root, file)
                
                if self._should_exclude(file_path):
                    continue
                
                if file.endswith(('.py', '.md', '.txt', '.yaml', '.yml', '.toml')):
                    if self.sanitize_file(file_path):
                        sanitized_count += 1
        
        logger.info(f"Sanitization complete. {sanitized_count} files modified.")
        
        return {
            'findings': findings,
            'sanitized_files': self.sanitized_files,
            'total_findings': total_findings,
            'files_modified': sanitized_count
        }
    
    def create_secure_env_template(self) -> str:
        """Create secure environment template"""
        template = """# Enterprise ScryptMineOS - Secure Configuration Template
# IMPORTANT: Fill in your actual values and keep this file secure

# ===========================================
# USER WALLET ADDRESSES
# ===========================================
LTC_ADDRESS=your_litecoin_address_here
DOGE_ADDRESS=your_dogecoin_address_here
WORKER_NAME=your_worker_name

# ===========================================
# POOL CONFIGURATION
# ===========================================
POOL_USER=${LTC_ADDRESS}.${WORKER_NAME}
POOL_password=os.getenv("POOL_PASSWORD", "x")

# ===========================================
# DATABASE CONFIGURATION (if using)
# ===========================================
MONGODB_URI=os.getenv("MONGODB_URI", "mongodb://localhost:27017/mining")

# ===========================================
# API CONFIGURATION (if using)
# ===========================================
API_key=os.getenv("API_KEY", "your_key_here")
API_secret=os.getenv("API_SECRET", "your_secret_here")

# ===========================================
# SECURITY
# ===========================================
ENCRYPTION_key=os.getenv("API_KEY", "your_key_here")
JWT_secret=os.getenv("API_SECRET", "your_secret_here")

# ===========================================
# MONITORING
# ===========================================
METRICS_PORT=9090
HEALTH_CHECK_PORT=8081
"""
        
        with open('.env.template', 'w') as f:
            f.write(template)
        
        logger.info("Created secure environment template: .env.template")
        return template
    
    def hide_sensitive_files(self) -> List[str]:
        """Hide sensitive files from public access"""
        sensitive_files = [
            'BYTEROVER_MCP_HANDBOOK*.md',
            'AGENT.md',
            'CLAUDE.md',
            '.env',
            '.env.*',
        ]
        
        hidden_files = []
        
        for pattern in sensitive_files:
            for file_path in glob.glob(pattern):
                if os.path.exists(file_path):
                    # Move to private directory
                    private_dir = 'private'
                    os.makedirs(private_dir, exist_ok=True)
                    
                    new_path = os.path.join(private_dir, os.path.basename(file_path))
                    os.rename(file_path, new_path)
                    hidden_files.append(new_path)
                    logger.info(f"Moved sensitive file: {file_path} -> {new_path}")
        
        return hidden_files

def main():
    """Main sanitization process"""
    sanitizer = CodebaseSanitizer()
    
    # Sanitize codebase
    results = sanitizer.sanitize_codebase()
    
    # Create secure environment template
    sanitizer.create_secure_env_template()
    
    # Hide sensitive files
    hidden_files = sanitizer.hide_sensitive_files()
    
    # Summary report
    print("\n" + "="*60)
    print("ENTERPRISE CODEBASE SANITIZATION COMPLETE")
    print("="*60)
    print(f"Total sensitive items found: {results['total_findings']}")
    print(f"Files modified: {results['files_modified']}")
    print(f"Sensitive files hidden: {len(hidden_files)}")
    print("\nNext steps:")
    print("1. Review .env.template and create your .env file")
    print("2. Set up proper environment variables")
    print("3. Test the sanitized codebase")
    print("4. Commit changes to version control")
    print("="*60)

if __name__ == "__main__":
    main()

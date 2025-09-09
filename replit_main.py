#!/usr/bin/env python3
"""
ScryptMineOS Enterprise Edition - Replit Entry Point
Automatically detects environment and runs appropriate configuration
"""

import os
import sys
import asyncio
import logging
from pathlib import Path

# Configure logging for Replit
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)

def setup_replit_environment():
    """Setup Replit-specific environment variables"""
    
    # Detect if running in Replit
    if os.getenv('REPL_ID') or os.getenv('REPLIT_MODE'):
        logger.info("🔧 Replit environment detected - configuring...")
        
        # Set Replit-specific environment variables
        os.environ['ENVIRONMENT'] = 'replit'
        os.environ['REPLIT_MODE'] = 'true'
        os.environ['DEBUG'] = 'false'
        
        # Configure ports for Replit
        os.environ['API_PORT'] = '8080'
        os.environ['METRICS_PORT'] = '9090'
        os.environ['HEALTH_CHECK_PORT'] = '8081'
        
        # Set default configuration for cloud environment
        os.environ['LTC_POOL_HOST'] = 'ltc.f2pool.com'
        os.environ['LTC_POOL_PORT'] = '8888'
        os.environ['DOGE_POOL_HOST'] = 'doge.zsolo.bid'
        os.environ['DOGE_POOL_PORT'] = '8057'
        
        # Default user configuration
        os.environ['WORKER_NAME'] = 'replit-miner'
        os.environ['TARGET_HASHRATE'] = '1000.0'  # Conservative for cloud
        os.environ['POWER_LIMIT'] = '100.0'       # Low power for cloud
        
        # Economic safeguards for cloud mining
        os.environ['MAX_POWER_COST'] = '0.20'     # Higher threshold for cloud
        os.environ['MIN_PROFITABILITY'] = '0.001' # Lower threshold for testing
        
        # Monitoring configuration
        os.environ['METRICS_ENABLED'] = 'true'
        os.environ['HEALTH_CHECKS_ENABLED'] = 'true'
        
        logger.info("✅ Replit environment configured successfully")
        return True
    
    return False

def create_default_env_file():
    """Create a default .env file for Replit users"""
    env_file = Path('.env')
    
    if not env_file.exists():
        logger.info("📝 Creating default .env file for Replit...")
        
        env_content = """# ScryptMineOS Enterprise - Replit Configuration
# IMPORTANT: Replace with your actual wallet addresses

# ===========================================
# USER WALLET ADDRESSES (REQUIRED)
# ===========================================
LTC_ADDRESS=ltc1qexample_replace_with_your_litecoin_address
DOGE_ADDRESS=DExample_replace_with_your_dogecoin_address
WORKER_NAME=replit-miner

# ===========================================
# POOL CONFIGURATION (DEFAULT)
# ===========================================
LTC_POOL_HOST=ltc.f2pool.com
LTC_POOL_PORT=8888
DOGE_POOL_HOST=doge.zsolo.bid
DOGE_POOL_PORT=8057

# ===========================================
# CLOUD MINING SETTINGS
# ===========================================
TARGET_HASHRATE=1000.0
POWER_LIMIT=100.0
MAX_POWER_COST=0.20
MIN_PROFITABILITY=0.001

# ===========================================
# MONITORING (REPLIT)
# ===========================================
API_PORT=8080
METRICS_PORT=9090
HEALTH_CHECK_PORT=8081
METRICS_ENABLED=true

# ===========================================
# ENVIRONMENT
# ===========================================
ENVIRONMENT=replit
DEBUG=false
LOG_LEVEL=INFO
"""
        
        with open(env_file, 'w') as f:
            f.write(env_content)
        
        logger.info("✅ Default .env file created")
        logger.warning("⚠️  IMPORTANT: Edit .env file with your actual wallet addresses!")

def show_replit_welcome():
    """Show welcome message for Replit users"""
    print("\n" + "="*60)
    print("🏢 ScryptMineOS Enterprise Edition - Replit Cloud Mining")
    print("="*60)
    print("🔧 Running in Replit cloud environment")
    print("📝 Edit .env file with your wallet addresses")
    print("🌐 Access monitoring at: https://your-repl-url:9090/metrics")
    print("💡 View health status at: https://your-repl-url:8081/health")
    print("="*60)
    print()

async def main():
    """Main entry point for Replit"""
    try:
        # Setup Replit environment
        is_replit = setup_replit_environment()
        
        if is_replit:
            show_replit_welcome()
            create_default_env_file()
        
        # Import and run enterprise system
        from enterprise_runner import main as enterprise_main
        
        # Override sys.argv for Replit
        sys.argv = [
            'enterprise_runner.py',
            '--user-id', 'replit-user'
        ]
        
        # Run enterprise mining system
        await enterprise_main()
        
    except ImportError as e:
        logger.error(f"❌ Failed to import enterprise runner: {e}")
        logger.info("📦 Installing required dependencies...")
        
        # Try to install dependencies
        import subprocess
        try:
            subprocess.check_call([sys.executable, '-m', 'pip', 'install', '-r', 'requirements.txt'])
            logger.info("✅ Dependencies installed, restarting...")
            
            # Retry import
            from enterprise_runner import main as enterprise_main
            await enterprise_main()
            
        except Exception as install_error:
            logger.error(f"❌ Failed to install dependencies: {install_error}")
            print("\n🔧 Manual Setup Required:")
            print("1. Run: pip install -r requirements.txt")
            print("2. Edit .env file with your wallet addresses")
            print("3. Run: python enterprise_runner.py --user-id replit-user")
            
    except Exception as e:
        logger.error(f"❌ Enterprise system error: {e}")
        print("\n🆘 Troubleshooting:")
        print("1. Check your .env file configuration")
        print("2. Verify wallet addresses are valid")
        print("3. Check Replit console for detailed errors")
        print("4. Restart the Repl if needed")

if __name__ == "__main__":
    # Check if we're in an async context
    try:
        asyncio.run(main())
    except RuntimeError:
        # Already in async context (Replit sometimes does this)
        try:
            import nest_asyncio
            nest_asyncio.apply()
            asyncio.run(main())
        except ImportError:
            logger.error("❌ nest_asyncio not available, please install it")
            print("Run: pip install nest-asyncio")

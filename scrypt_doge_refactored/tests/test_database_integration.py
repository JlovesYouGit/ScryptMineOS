"""
Test script for MongoDB Atlas integration with the Scrypt DOGE mining system.
This script tests the database connection and basic operations.
"""

import asyncio
import os
import sys
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from core.database_manager import DatabaseManager, DatabaseConfig
from core.models import ShareData, PerformanceMetric, SystemMetric


async def test_database_integration():
    """Test MongoDB integration"""
    print("Testing MongoDB Atlas integration...")
    
    # Create a test database configuration
    # In a real scenario, you would use environment variables or a config file
    db_config = DatabaseConfig(
        enabled=True,
        uri=os.environ.get("MONGODB_URI", "mongodb+srv://username:password@cluster.mongodb.net/mining_db?retryWrites=true&w=majority"),
        name="mining_test_db",
        collections={
            "shares": "test_shares",
            "performance": "test_performance",
            "system_metrics": "test_system_metrics",
            "alerts": "test_alerts"
        }
    )
    
    # Create database manager
    db_manager = DatabaseManager(db_config)
    
    # Test initialization
    print("Initializing database connection...")
    success = await db_manager.initialize()
    if not success:
        print("Failed to initialize database connection")
        return False
    
    print("Database connection initialized successfully")
    
    # Test storing share data
    print("Testing share data storage...")
    share_data = ShareData(
        job_id="test_job_123",
        extranonce2="abcdef12",
        ntime="12345678",
        nonce="87654321",
        hash_result="000000000019d6689c085ae165831e934ff763ae46a2a6c172b3f1b60a8ce26f",
        worker_name="test_worker",
        difficulty=1.0,
        accepted=True
    )
    
    store_success = db_manager.store_share(share_data.to_dict())
    if store_success:
        print("Share data stored successfully")
    else:
        print("Failed to store share data")
    
    # Test storing performance metric
    print("Testing performance metric storage...")
    perf_metric = PerformanceMetric(
        hashrate=1000000.0,  # 1 MH/s
        accepted_shares=10,
        rejected_shares=2,
        hardware_errors=0,
        uptime_seconds=3600.0,  # 1 hour
        worker_name="test_worker"
    )
    
    perf_success = db_manager.store_performance_metric(perf_metric.to_dict())
    if perf_success:
        print("Performance metric stored successfully")
    else:
        print("Failed to store performance metric")
    
    # Test storing system metric
    print("Testing system metric storage...")
    sys_metric = SystemMetric(
        cpu_percent=45.5,
        memory_percent=60.2,
        disk_usage_percent=75.8,
        network_bytes_sent=1024000,
        network_bytes_recv=2048000,
        worker_name="test_worker"
    )
    
    sys_success = db_manager.store_system_metric(sys_metric.to_dict())
    if sys_success:
        print("System metric stored successfully")
    else:
        print("Failed to store system metric")
    
    # Test retrieving data
    print("Testing data retrieval...")
    recent_shares = db_manager.get_recent_shares(limit=5)
    print(f"Retrieved {len(recent_shares)} recent shares")
    
    recent_perf = db_manager.get_recent_performance_metrics(limit=5)
    print(f"Retrieved {len(recent_perf)} recent performance metrics")
    
    # Test health check
    print("Testing database health check...")
    health_status = await db_manager.health_check()
    if health_status:
        print("Database health check passed")
    else:
        print("Database health check failed")
    
    # Close connection
    print("Closing database connection...")
    await db_manager.close()
    print("Database connection closed")
    
    return True


if __name__ == "__main__":
    print("Starting MongoDB integration test...")
    try:
        result = asyncio.run(test_database_integration())
        if result:
            print("All tests passed!")
        else:
            print("Some tests failed!")
            sys.exit(1)
    except Exception as e:
        print(f"Test failed with exception: {e}")
        sys.exit(1)
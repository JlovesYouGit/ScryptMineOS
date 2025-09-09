"""
Example script demonstrating MongoDB Atlas integration with the Scrypt DOGE mining system.
This script shows how to use the database manager directly.
"""

import asyncio
import os
from pathlib import Path
import sys

# Add the project root to the Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from core.database_manager import DatabaseManager, DatabaseConfig
from core.models import ShareData, PerformanceMetric, SystemMetric, AlertData


async def main():
    """Demonstrate MongoDB integration usage"""
    print("MongoDB Atlas Integration Example")
    print("=" * 40)
    
    # Create database configuration
    # In a real application, you would load this from a config file or environment variables
    db_config = DatabaseConfig(
        enabled=True,
        uri=os.environ.get("MONGODB_URI", "os.getenv("MONGODB_URI", "os.getenv("MONGODB_URI", "mongodb://localhost:27017/mining")")"),
        name="mining_example_db",
        collections={
            "shares": "example_shares",
            "performance": "example_performance",
            "system_metrics": "example_system_metrics",
            "alerts": "example_alerts"
        }
    )
    
    # Create database manager
    db_manager = DatabaseManager(db_config)
    
    # Initialize connection
    print("1. Initializing database connection...")
    success = await db_manager.initialize()
    if not success:
        print("Failed to connect to MongoDB Atlas")
        return
    
    print("Connected to MongoDB Atlas successfully!")
    
    # Store share data
    print("\n2. Storing share data...")
    share_data = ShareData(
        job_id="example_job_001",
        extranonce2="a1b2c3d4",
        ntime="567890ab",
        nonce="cdef1234",
        hash_result="000000000019d6689c085ae1658os.getenv("LTC_ADDRESS", "your_ltc_address_here")0a8ce26f",
        worker_name="example_worker",
        difficulty=1.5,
        accepted=True
    )
    
    if db_manager.store_share(share_data.to_dict()):
        print("Share data stored successfully")
    else:
        print("Failed to store share data")
    
    # Store performance metric
    print("\n3. Storing performance metric...")
    perf_metric = PerformanceMetric(
        hashrate=2500000.0,  # 2.5 MH/s
        accepted_shares=150,
        rejected_shares=5,
        hardware_errors=1,
        uptime_seconds=7200.0,  # 2 hours
        worker_name="example_worker"
    )
    
    if db_manager.store_performance_metric(perf_metric.to_dict()):
        print("Performance metric stored successfully")
    else:
        print("Failed to store performance metric")
    
    # Store system metric
    print("\n4. Storing system metric...")
    sys_metric = SystemMetric(
        cpu_percent=65.3,
        memory_percent=45.8,
        disk_usage_percent=30.2,
        network_bytes_sent=1048576,  # 1 MB
        network_bytes_recv=2097152,  # 2 MB
        worker_name="example_worker"
    )
    
    if db_manager.store_system_metric(sys_metric.to_dict()):
        print("System metric stored successfully")
    else:
        print("Failed to store system metric")
    
    # Store alert
    print("\n5. Storing alert...")
    alert_data = AlertData(
        alert_type="performance_degradation",
        message="Hashrate dropped below threshold",
        severity="warning",
        worker_name="example_worker",
        resolved=False
    )
    
    if db_manager.store_alert(alert_data):
        print("Alert stored successfully")
    else:
        print("Failed to store alert")
    
    # Retrieve recent shares
    print("\n6. Retrieving recent shares...")
    recent_shares = db_manager.get_recent_shares(limit=10)
    print(f"Retrieved {len(recent_shares)} recent shares")
    for share in recent_shares:
        print(f"  - Job ID: {share.get('job_id', 'N/A')}, Accepted: {share.get('accepted', 'N/A')}")
    
    # Retrieve recent performance metrics
    print("\n7. Retrieving recent performance metrics...")
    recent_perf = db_manager.get_recent_performance_metrics(limit=10)
    print(f"Retrieved {len(recent_perf)} recent performance metrics")
    for perf in recent_perf:
        print(f"  - Hashrate: {perf.get('hashrate', 'N/A')} H/s, Uptime: {perf.get('uptime_seconds', 'N/A')}s")
    
    # Perform health check
    print("\n8. Performing database health check...")
    health_status = await db_manager.health_check()
    if health_status:
        print("Database health check passed")
    else:
        print("Database health check failed")
    
    # Close connection
    print("\n9. Closing database connection...")
    await db_manager.close()
    print("Database connection closed")
    
    print("\nExample completed successfully!")


if __name__ == "__main__":
    asyncio.run(main())
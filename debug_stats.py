#!/usr/bin/env python3
"""
Debug script to check stats structure
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from enhanced_stratum_client import StratumMonitor

def main():
    """Debug the stats structure"""
    # Create monitor
    monitor = StratumMonitor("test_worker")
    
    # Test recording events
    monitor.record_connection_attempt()
    monitor.record_connection_success()
    monitor.record_job_received()
    monitor.record_share_accepted()
    monitor.record_share_rejected("Test rejection")
    monitor.record_difficulty_change(1.0, 2.0)
    
    # Get stats
    stats = monitor.get_stats()
    
    print("Stats structure:")
    print(f"Keys: {stats.keys()}")
    print(f"Connection keys: {stats['connection'].keys()}")
    print(f"Shares keys: {stats['shares'].keys()}")
    
    # Print full stats
    import json
    print("\nFull stats:")
    print(json.dumps(stats, indent=2, default=str))

if __name__ == "__main__":
    main()
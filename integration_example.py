#!/usr/bin/env python3
"""
Integration example showing how to use the enhanced Stratum client
with existing mining code
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from enhanced_stratum_client import EnhancedStratumClient

def main():
    """Example of integrating the enhanced Stratum client"""
    print("Enhanced Stratum Client Integration Example")
    print("=" * 45)
    
    # Create enhanced client (same interface as basic client)
    client = EnhancedStratumClient(
        host="doge.zsolo.bid",
        port=8057,
        user=os.getenv("POOL_USER", os.getenv("POOL_USER", os.getenv("POOL_USER", "your_wallet_address.worker_name"))),
        password=os.getenv("POOL_PASSWORD", "x")"POOL_PASSWORD", "x")"
    )
    
    print("1. Connecting to pool...")
    if not client.connect():
        print("Failed to connect to pool")
        return 1
    
    print("2. Subscribing and authorizing...")
    if not client.subscribe_and_authorize():
        print("Failed to subscribe/authorize")
        client.disconnect()
        return 1
    
    print("3. Listening for jobs...")
    print("(Press Ctrl+C to stop)")
    
    try:
        # This is the same pattern as the original runner.py
        while True:
            message = client.receive_message()
            if message:
                if message.get("method"):
                    # Handle notifications (mining jobs)
                    client.handle_notification(message)
                    if client.job_id:
                        print(f"Received job: {client.job_id}")
                        # Here you would integrate with your mining kernel
                        # just like in the original runner.py
                        break  # Stop after first job for this example
                else:
                    # Handle responses
                    print(f"Received response: {message}")
            else:
                # No message, reconnect
                print("No message from pool, reconnecting...")
                if not client.reconnect() or not client.subscribe_and_authorize():
                    print("Failed to reconnect")
                    break
    except KeyboardInterrupt:
        print("\nShutting down...")
    finally:
        # Print statistics
        stats = client.get_stats()
        print("\n=== Session Statistics ===")
        print(f"Runtime: {stats['connection']['runtime_seconds']:.2f} seconds")
        print(f"Connection attempts: {stats['connection']['connection']['attempts']}")
        print(f"Successful connections: {stats['connection']['connection']['successful']}")
        print(f"Shares accepted: {stats['connection']['shares']['accepted']}")
        print(f"Shares rejected: {stats['connection']['shares']['rejected']}")
        print(f"Security level: {stats['security']['security_level']}")
        print(f"Messages validated: {stats['security']['messages_validated']}")
        
        client.disconnect()
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
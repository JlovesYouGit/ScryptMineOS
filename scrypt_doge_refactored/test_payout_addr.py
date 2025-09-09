#!/usr/bin/env python3
"""
Test script to verify that the PAYOUT_ADDR environment variable is set correctly.
"""

import os
import sys

def test_payout_addr():
    """Test that PAYOUT_ADDR environment variable is set."""
    payout_addr = os.environ.get("PAYOUT_ADDR", "")
    
    if not payout_addr:
        print("ERROR: PAYOUT_ADDR environment variable is not set!")
        print("Please set your wallet address where mining rewards will be sent.")
        print("You must use either:")
        print("  1. Your Litecoin address: ltc1qpptg85asckrjy9ygygh2tfgxqwzn6672zmzq99")
        print("  2. Your Dogecoin address: DGKsuHU6XdghZtA2aWGqvrZrkWracQJzPd")
        print("")
        print("Example:")
        print("  export PAYOUT_ADDR=ltc1qpptg85asckrjy9ygygh2tfgxqwzn6672zmzq99")
        return False
    
    # Check if the address is one of the valid addresses
    valid_addresses = [
        "ltc1qpptg85asckrjy9ygygh2tfgxqwzn6672zmzq99",
        "DGKsuHU6XdghZtA2aWGqvrZrkWracQJzPd"
    ]
    
    if payout_addr not in valid_addresses:
        print("WARNING: PAYOUT_ADDR is not set to one of the valid addresses!")
        print("You must use either:")
        print("  1. Your Litecoin address: ltc1qpptg85asckrjy9ygygh2tfgxqwzn6672zmzq99")
        print("  2. Your Dogecoin address: DGKsuHU6XdghZtA2aWGqvrZrkWracQJzPd")
        return False
    
    print(f"SUCCESS: PAYOUT_ADDR is set to: {payout_addr}")
    return True

if __name__ == "__main__":
    if test_payout_addr():
        print("PAYOUT_ADDR verification passed.")
        sys.exit(0)
    else:
        print("PAYOUT_ADDR verification failed.")
        sys.exit(1)
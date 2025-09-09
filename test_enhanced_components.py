#!/usr/bin/env python3
"""
Test script for enhanced Stratum components
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from enhanced_stratum_client import (
    StratumSecurityValidator, 
    SecurityConfig, 
    SecurityLevel,
    StratumMonitor,
    DifficultyManager,
    ExtranonceManager,
    ValidationError
)

def test_security_validator():
    """Test the security validator component"""
    print("Testing StratumSecurityValidator...")
    
    # Create validator with medium security
    config = SecurityConfig(security_level=SecurityLevel.MEDIUM)
    validator = StratumSecurityValidator(config)
    
    # Test valid messages
    valid_messages = [
        '{"id": 1, "method": "mining.subscribe", "params": ["test/1.0"]}',
        '{"id": 2, "result": [null, "abc123", 4], "error": null}',
        '{"method": "mining.notify", "params": ["job1", "abc", "def", "ghi", [], "123", "456", "789", true]}'
    ]
    
    for msg in valid_messages:
        try:
            result = validator.validate_message(msg)
            print(f"✓ Valid message: {result.get('method', 'response')}")
        except ValidationError as e:
            print(f"✗ Unexpected validation error: {e}")
            return False
    
    # Test invalid messages
    invalid_messages = [
        '{"id": 1, "method": "mining.subscribe", "params":}',  # Invalid JSON
        '{"id": 1, "method": "system.shutdown", "params": []}'  # Blocked method
    ]
    
    for msg in invalid_messages:
        try:
            validator.validate_message(msg)
            print(f"✗ Invalid message should have failed: {msg}")
            return False
        except ValidationError as e:
            print(f"✓ Correctly blocked invalid message: {type(e).__name__}")
    
    print("Security validator tests passed!\n")
    return True

def test_monitor():
    """Test the monitoring component"""
    print("Testing StratumMonitor...")
    
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
    
    # Verify stats
    if stats["worker_name"] != "test_worker":
        print("✗ Worker name mismatch")
        return False
        
    if stats["connection"]["successful"] != 1:
        print("✗ Connection stats incorrect")
        print(f"Actual successful connections: {stats['connection']['successful']}")
        return False
        
    if stats["shares"]["accepted"] != 1 or stats["shares"]["rejected"] != 1:
        print("✗ Share stats incorrect")
        print(f"Accepted: {stats['shares']['accepted']}, Rejected: {stats['shares']['rejected']}")
        return False
    
    print("✓ Monitor recorded events correctly")
    print("✓ Monitor stats retrieved correctly")
    print("Monitor tests passed!\n")
    return True

def test_difficulty_manager():
    """Test the difficulty manager component"""
    print("Testing DifficultyManager...")
    
    # Create difficulty manager
    dm = DifficultyManager(current_difficulty=1.0)
    
    # Test difficulty update
    if not dm.update_difficulty(2.0):
        print("✗ Failed to update difficulty")
        return False
    print("✓ Difficulty updated successfully")
    
    # Test invalid difficulty
    if dm.update_difficulty(0.000001):  # Below minimum
        print("✗ Should have rejected difficulty below minimum")
        return False
    print("✓ Correctly rejected difficulty below minimum")
    
    # Test difficulty adjustment
    new_diff = dm.adjust_difficulty(90, 10)  # 90% acceptance rate
    if new_diff >= 2.0:  # Should decrease difficulty
        print("✗ Difficulty adjustment not working correctly")
        return False
    print("✓ Difficulty auto-adjustment working correctly")
    
    print("Difficulty manager tests passed!\n")
    return True

def test_extranonce_manager():
    """Test the extranonce manager component"""
    print("Testing ExtranonceManager...")
    
    # Create extranonce manager
    em = ExtranonceManager("abc123", 4)
    
    # Test extranonce2 generation
    en2_1 = em.generate_extranonce2()
    en2_2 = em.generate_extranonce2()
    
    if en2_1 == en2_2:
        print("✗ Generated extranonce2 values should be different")
        return False
    print("✓ Extranonce2 generation working correctly")
    
    # Test size
    if len(bytes.fromhex(en2_1)) != 4:
        print("✗ Extranonce2 size incorrect")
        return False
    print("✓ Extranonce2 size correct")
    
    # Test update
    em.update_extranonce1("def456")
    if em.extranonce1 != "def456":
        print("✗ Extranonce1 update failed")
        return False
    print("✓ Extranonce1 update working correctly")
    
    print("Extranonce manager tests passed!\n")
    return True

def main():
    """Run all tests"""
    print("=== Testing Enhanced Stratum Components ===\n")
    
    tests = [
        test_security_validator,
        test_monitor,
        test_difficulty_manager,
        test_extranonce_manager
    ]
    
    passed = 0
    for test in tests:
        try:
            if test():
                passed += 1
        except Exception as e:
            print(f"✗ Test failed with exception: {e}")
            import traceback
            traceback.print_exc()
    
    print(f"=== Test Results: {passed}/{len(tests)} tests passed ===")
    
    if passed == len(tests):
        print("All tests passed! The enhanced Stratum components are working correctly.")
        return 0
    else:
        print("Some tests failed. Please check the implementation.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
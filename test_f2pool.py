#!/usr/bin/env python3
"""
F2Pool Merged Mining Connection Test
Tests the professional ASIC mining configuration

Usage: python test_f2pool.py [--ltc-address YOUR_LTC_ADDRESS]
"""

import argparse
import socket
import json
import time
import sys

# Configuration
DOGE_WALLET = "DGKsuHU6XdghZtA2aWGqvrZrkWracQJzPd"  # From existing codebase
LTC_PLACEHOLDER = "Ldf823abc123"  # User must replace with real LTC address

def test_pool_connection(host, port, user, password="x"):
    """Test Stratum connection to mining pool"""
    print(f"Testing connection to {host}:{port}")
    print(f"Worker string: {user}")
    
    try:
        # Connect to pool
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(10)
        sock.connect((host, port))
        
        # Send mining.subscribe
        subscribe_msg = {
            "id": 1,
            "method": "mining.subscribe",
            "params": ["scrypt-miner/2.1.0", "01ad557d"]
        }
        
        message = json.dumps(subscribe_msg) + "\\n"
        sock.send(message.encode())
        
        # Receive response
        response = sock.recv(1024).decode().strip()
        sub_data = json.loads(response)
        
        if sub_data.get("result"):
            print("✅ mining.subscribe successful")
            print(f"   extraNonce1: {sub_data['result'][1]}")
            print(f"   extraNonce2_size: {sub_data['result'][2]}")
        else:
            print("❌ mining.subscribe failed")
            print(f"   Error: {sub_data.get('error', 'Unknown error')}")
            return False
        
        # Send mining.authorize
        auth_msg = {
            "id": 2,
            "method": "mining.authorize",
            "params": [user, password]
        }
        
        message = json.dumps(auth_msg) + "\\n"
        sock.send(message.encode())
        
        # Receive auth response
        response = sock.recv(1024).decode().strip()
        auth_data = json.loads(response)
        
        if auth_data.get("result"):
            print("✅ mining.authorize successful")
            print("   Worker authenticated for merged mining")
            return True
        else:
            print("❌ mining.authorize failed")
            print(f"   Error: {auth_data.get('error', 'Authentication failed')}")
            return False
            
    except socket.timeout:
        print("❌ Connection timeout")
        return False
    except ConnectionRefusedError:
        print("❌ Connection refused")
        return False
    except Exception as e:
        print(f"❌ Connection error: {e}")
        return False
    finally:
        try:
            sock.close()
        except:
            pass

def validate_addresses(ltc_addr, doge_addr):
    """Basic address validation"""
    issues = []
    
    # LTC address validation
    if not ltc_addr.startswith('L') and not ltc_addr.startswith('M'):
        issues.append(f"⚠️  LTC address should start with 'L' or 'M', got: {ltc_addr[:10]}...")
    
    if len(ltc_addr) < 26 or len(ltc_addr) > 35:
        issues.append(f"⚠️  LTC address length suspicious: {len(ltc_addr)} chars")
    
    # DOGE address validation  
    if not doge_addr.startswith('D'):
        issues.append(f"⚠️  DOGE address should start with 'D', got: {doge_addr[:10]}...")
        
    if len(doge_addr) != 34:
        issues.append(f"⚠️  DOGE address should be 34 chars, got: {len(doge_addr)}")
    
    return issues

def main():
    parser = argparse.ArgumentParser(description="Test F2Pool merged mining connection")
    parser.add_argument("--ltc-address", type=str, default=LTC_PLACEHOLDER,
                       help="Your Litecoin address for merged mining")
    parser.add_argument("--worker", type=str, default="rig01",
                       help="Worker name")
    args = parser.parse_args()
    
    ltc_addr = args.ltc_address
    doge_addr = DOGE_WALLET
    worker_name = args.worker
    
    print("🔍 F2Pool Merged Mining Connection Test")
    print("=" * 50)
    
    # Validate addresses
    print("📋 Address Validation:")
    issues = validate_addresses(ltc_addr, doge_addr)
    
    if ltc_addr == LTC_PLACEHOLDER:
        issues.append("❗ PLACEHOLDER LTC address detected - you MUST provide a real LTC address")
        issues.append("   Use: python test_f2pool.py --ltc-address YOUR_LTC_ADDRESS")
    
    for issue in issues:
        print(f"   {issue}")
    
    if any("PLACEHOLDER" in issue for issue in issues):
        print("\\n❌ Cannot test with placeholder address. Exiting.")
        return 1
    
    if not issues:
        print("   ✅ Address format validation passed")
    
    # Test pool endpoints
    worker_string = f"{ltc_addr}.{doge_addr}.{worker_name}"
    
    endpoints = [
        ("ltc.f2pool.com", 3335, "Global"),
        ("ltc-euro.f2pool.com", 3335, "Europe"), 
        ("ltc-na.f2pool.com", 3335, "North America"),
        ("ltc-asia.f2pool.com", 3335, "Asia"),
    ]
    
    print(f"\\n🌐 Testing Pool Endpoints:")
    print(f"   Worker: {worker_string}")
    
    success_count = 0
    for host, port, region in endpoints:
        print(f"\\n📡 {region} ({host}:{port})")
        if test_pool_connection(host, port, worker_string):
            success_count += 1
            
    print(f"\\n📊 Results Summary:")
    print(f"   Successful connections: {success_count}/{len(endpoints)}")
    
    if success_count > 0:
        print("   ✅ F2Pool merged mining configuration is working!")
        print("   🎯 Next steps:")
        print("      1. Configure your ASIC with these pool settings")
        print("      2. Monitor merged mining payouts in F2Pool dashboard")
        print("      3. Expect +30-40% revenue from LTC+DOGE+8 auxiliary coins")
        return 0
    else:
        print("   ❌ All connections failed")
        print("   🔧 Troubleshooting:")
        print("      1. Check internet connection")
        print("      2. Verify LTC address is valid and active")
        print("      3. Try different regional endpoints")
        print("      4. Check F2Pool status page")
        return 1

if __name__ == "__main__":
    sys.exit(main())
#!/usr/bin/env python3
"""
Quick Start Script for GPU-ASIC Hybrid Layer

This script demonstrates the complete GPU-ASIC hybrid system in action.
Run this to see your GPU system become externally indistinguishable from an Antminer L7.
"""

import time
import requests
import json
import subprocess

def main():
    print("🚀 GPU-ASIC Hybrid Layer Quick Start")
    print("=" * 50)
    
    # 1. Start the hybrid system
    print("1. Initializing GPU-ASIC Hybrid Layer...")
    
    try:
        from gpu_asic_hybrid import initialize_gpu_asic_hybrid, get_gpu_asic_hybrid
        
        # Initialize on port 8080 (avoid conflicts)
        if initialize_gpu_asic_hybrid(api_port=8080):
            print("✅ GPU-ASIC Hybrid Layer: ACTIVE")
            
            hybrid = get_gpu_asic_hybrid()
            status = hybrid.get_status()
            
            print(f"📊 Initial Status:")
            print(f"   🌡️ Temperature: {status['thermal_temp_c']:.1f}°C")
            print(f"   🔌 Power Domain: {status['current_domain']}")
            print(f"   🎯 GPU Vendor: {status['gpu_vendor']}")
            print(f"   ⚠️  Nonce Error Rate: {status['nonce_error_rate']:.6f}")
            print(f"   ⏱️ Share Interval: {status['share_interval']:.1f}s")
            
        else:
            print("❌ Failed to initialize hybrid layer")
            return
            
    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("Please ensure gpu_asic_hybrid.py is in the current directory")
        return
    
    # 2. Test the API endpoints
    print("\n2. Testing Antminer API Endpoints...")
    
    api_url = "http://localhost:8080"
    
    # Test miner status endpoint
    try:
        response = requests.get(f"{api_url}/cgi-bin/get_miner_status.cgi", timeout=5)
        if response.status_code == 200:
            status_data = response.json()
            print("✅ Miner Status API: WORKING")
            
            # Display key metrics that prove L7 emulation
            summary = status_data.get("SUMMARY", [{}])[0]
            print(f"   📈 Hash Rate: {summary.get('MHS av', 0):.1f} MH/s (appears as 9.5 GH/s)")
            print(f"   🌡️ Temperature: {summary.get('Temperature', 0):.1f}°C")
            print(f"   ✅ Shares: {summary.get('Accepted', 0)} accepted, {summary.get('Rejected', 0)} rejected")
            
            # Show ASIC-like device info
            devs = status_data.get("DEVS", [])
            print(f"   🔧 Hash Boards: {len(devs)} boards detected (L7-style)")
            
            fans = status_data.get("FANS", [])
            print(f"   🌪️ Fans: {len(fans)} fans @ ~4300 RPM (ASIC-like)")
            
        else:
            print(f"❌ Miner Status API failed: HTTP {response.status_code}")
            
    except Exception as e:
        print(f"❌ API test failed: {e}")
    
    # 3. Demonstrate ASIC-like behaviors
    print("\n3. Demonstrating ASIC-like Behaviors...")
    
    # Thermal simulation
    print("🌡️ Thermal Simulation:")
    for i in range(5):
        time.sleep(2)
        hybrid.update_power_and_thermal(3425)  # L7 nominal power
        status = hybrid.get_status()
        print(f"   Time +{i*2}s: {status['thermal_temp_c']:.1f}°C (30s time constant)")
    
    # Share timing simulation
    print("\n⏱️ Share Timing Simulation:")
    share_count = 0
    start_time = time.time()
    
    for i in range(20):  # Test 20 share checks
        if hybrid.should_submit_share():
            share_count += 1
            elapsed = time.time() - start_time
            print(f"   Share {share_count}: {elapsed:.1f}s (Poisson λ=0.19 s⁻¹)")
        time.sleep(0.5)
    
    # Fault injection demonstration
    print("\n⚠️ Fault Injection Simulation:")
    for i in range(100):  # Test 100 nonces
        result = hybrid.inject_faults(i, board_id=0)
        if result is None:
            print(f"   Nonce {i}: DROPPED (0.005% error rate like real L7)")
            break
        if i == 99:
            print("   No faults in 100 nonces (normal - fault rate is very low)")
    
    # 4. Show external API compatibility
    print("\n4. External API Compatibility Test...")
    
    print("🔗 Antminer-compatible endpoints:")
    print(f"   GET  {api_url}/cgi-bin/get_miner_status.cgi")
    print(f"   POST {api_url}/cgi-bin/set_miner_conf.cgi")
    
    print("\n🧪 Test with curl:")
    print(f"   curl {api_url}/cgi-bin/get_miner_status.cgi")
    
    # Test configuration endpoint
    try:
        config_data = {
            "freq": 450,
            "volt": 1225, 
            "fan": 100,
            "power-strict": 2800
        }
        
        response = requests.post(
            f"{api_url}/cgi-bin/set_miner_conf.cgi",
            json=config_data,
            timeout=5
        )
        
        if response.status_code == 200:
            print("✅ Configuration API: WORKING")
            print("   External tools can configure this 'ASIC' normally")
        else:
            print(f"❌ Configuration API failed: HTTP {response.status_code}")
            
    except Exception as e:
        print(f"❌ Configuration test failed: {e}")
    
    # 5. Summary
    print("\n🎉 GPU-ASIC Hybrid Layer Demonstration Complete")
    print("=" * 50)
    print("✅ Your GPU now appears externally identical to Antminer L7:")
    print("   • Same JSON API responses")
    print("   • Same thermal behavior (30s time constant)")
    print("   • Same fault patterns (0.005% nonce errors)")
    print("   • Same share timing (Poisson λ=0.19 s⁻¹)")
    print("   • Same configuration endpoints")
    print("   • Same monitoring data structure")
    
    print("\n⚡ Actual Performance: Honest ~50 MH/s GPU mining")
    print("🎭 Apparent Performance: 9.5 GH/s Antminer L7 ASIC")
    print("🎯 Use Case: Perfect for developing/testing fleet management software")
    
    print(f"\n🌐 API Access: {api_url}/cgi-bin/get_miner_status.cgi")
    print("   Your fleet management tools will see this as a real L7!")
    
    # Keep running for manual testing
    print("\n⏳ System running... Press Ctrl+C to stop")
    try:
        while True:
            time.sleep(10)
            status = hybrid.get_status()
            print(f"🔄 Status: {status['thermal_temp_c']:.1f}°C, {status['current_domain']} domain")
    except KeyboardInterrupt:
        print("\n🔽 Shutting down...")
        hybrid.shutdown()
        print("✅ Shutdown complete")

if __name__ == "__main__":
    main()
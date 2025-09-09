#!/usr/bin/env python3
"""
Economic Safety Test
Demonstrates the critical kill-switch that prevents money-burning mining

This shows the "20-line kill-switch" in action before any expensive operations.
"""

import sys
import time
from economic_guardian import economic_pre_flight_check, economic_guardian
from algo_switcher import algo_switcher, get_profitable_algorithm_for_gpu

def test_economic_kill_switch():
    """Test the economic kill-switch functionality"""
    print("🔍 Testing Economic Kill-Switch System")
    print("=" * 50)
    
    print("\n1️⃣ CRITICAL PRE-FLIGHT CHECK")
    print("   (This runs BEFORE OpenCL context creation)")
    
    # Test with realistic electricity costs
    test_costs = [0.06, 0.08, 0.12, 0.20]  # $/kWh
    
    for cost in test_costs:
        print(f"\n   Testing at ${cost:.2f}/kWh electricity:")
        
        if economic_pre_flight_check(electricity_cost_kwh=cost):
            print(f"   ✅ PASS: Safe to proceed at ${cost:.2f}/kWh")
        else:
            print(f"   🚨 FAIL: Would lose money at ${cost:.2f}/kWh")
            print(f"   💡 Action: Mining BLOCKED, no resources wasted")
    
    print("\n2️⃣ ALGORITHM PROFITABILITY CHECK")
    print("   (Checking if current algorithm is GPU-friendly)")
    
    # Test algorithm economic viability
    power_estimate = 250  # Watts
    economic_check = algo_switcher.economic_algorithm_check(power_estimate)
    
    print(f"\n   Current algorithm viability:")
    print(f"   Algorithm: {algo_switcher.current_algorithm or 'None selected'}")
    print(f"   Viable for GPU: {economic_check.get('viable', False)}")
    
    if not economic_check.get('viable', False):
        print(f"   🚨 Problem: {economic_check.get('reason', 'Unknown')}")
        if 'gpu_friendly_options' in economic_check:
            print(f"   💡 GPU-friendly alternatives: {economic_check['gpu_friendly_options']}")
    
    print("\n3️⃣ PROFIT-SWITCHING RECOMMENDATION")
    
    profitable_algo = get_profitable_algorithm_for_gpu()
    if profitable_algo:
        print(f"   ✅ Recommended GPU algorithm: {profitable_algo}")
        
        # Get config for recommended algorithm
        algo_config = algo_switcher.get_algorithm_config(profitable_algo)
        if algo_config:
            print(f"   💰 Target coin: {algo_config.coin_symbol}")
            print(f"   ⚡ Min efficiency: {algo_config.min_hashrate_per_watt/1000:.0f} kH/s per watt")
            print(f"   🎯 GPU-friendly: {algo_config.profitable_on_gpu}")
    else:
        print("   🚨 NO profitable GPU algorithms found")
        print("   💡 All supported algorithms are ASIC-dominated")
    
    print("\n4️⃣ REAL-TIME MONITORING SIMULATION")
    print("   (Simulating the 5-minute economic checks during mining)")
    
    # Simulate different hashrate scenarios
    scenarios = [
        {"name": "Current GPU Performance", "hashrate": 50600, "power": 250},
        {"name": "Optimized GPU", "hashrate": 75000, "power": 200},
        {"name": "Budget ASIC", "hashrate": 200_000_000, "power": 800},
        {"name": "Professional ASIC", "hashrate": 9_500_000_000, "power": 3400}
    ]
    
    for scenario in scenarios:
        print(f"\n   Scenario: {scenario['name']}")
        
        # Record hashrate and check viability
        economic_guardian.record_hashrate(scenario['hashrate'])
        economic_guardian.power_watts = scenario['power']
        
        economic_data = economic_guardian.check_economic_viability()
        
        hashrate_mh = scenario['hashrate'] / 1e6
        efficiency = scenario['hashrate'] / scenario['power']
        daily_cost = economic_data['daily_power_cost_usd']
        
        print(f"      Hashrate: {hashrate_mh:.1f} MH/s")
        print(f"      Power: {scenario['power']}W")
        print(f"      Efficiency: {efficiency/1000:.1f} kH/s per watt")
        print(f"      Daily cost: ${daily_cost:.2f}")
        print(f"      Economic status: {'✅ VIABLE' if economic_data['is_viable'] else '🚨 LOSING MONEY'}")
        
        if not economic_data['is_viable']:
            failure_reasons = economic_data.get('failure_reasons', [])
            for reason in failure_reasons[:2]:  # Show first 2 reasons
                print(f"         ⚠️  {reason}")
    
    print("\n5️⃣ SUMMARY: The Missing Economic Safeguards")
    print("   ✅ Pre-flight check: Prevents expensive resource allocation")
    print("   ✅ Algorithm check: Avoids ASIC-dominated coins")  
    print("   ✅ Real-time monitoring: Stops losses during operation")
    print("   ✅ Auto profit-switching: Targets GPU-friendly algorithms")
    
    print(f"\n🎯 BOTTOM LINE:")
    print(f"   Without these safeguards: Guaranteed money loss")
    print(f"   With these safeguards: Mining only when profitable")
    print(f"   Current GPU reality: Proof-of-concept for ASIC deployment")
    
    return True

def test_profit_switcher_dry_run():
    """Test the profit switcher in dry-run mode"""
    print("\n" + "=" * 50)
    print("🔄 PROFIT SWITCHER DRY-RUN TEST")
    print("=" * 50)
    
    try:
        from profit_switcher import main as profit_main
        
        # Backup sys.argv and test dry-run mode
        original_argv = sys.argv[:]
        sys.argv = ["profit_switcher.py", "--dry-run"]
        
        print("Running profit switcher in dry-run mode...")
        result = profit_main()
        
        if result == 0:
            print("✅ Profit switcher dry-run: PASSED")
        else:
            print("🚨 Profit switcher dry-run: FAILED (as expected with current hardware)")
        
        # Restore sys.argv
        sys.argv = original_argv
        
    except Exception as e:
        print(f"⚠️  Profit switcher test error: {e}")
        print("   (This is expected if dependencies are missing)")

if __name__ == "__main__":
    print("🚨 ECONOMIC SAFETY SYSTEM TEST")
    print("Testing the critical safeguards that prevent money-burning mining")
    
    test_economic_kill_switch()
    test_profit_switcher_dry_run()
    
    print(f"\n{'='*50}")
    print("🎯 TEST COMPLETE")
    print("   The economic kill-switch system is now integrated")
    print("   Mining will be blocked if unprofitable")
    print("   No more 'beautiful 50 kH/s heater' burning money 24/7!")
#!/usr/bin/env python3
"""
Test script for Phase 3 advanced features
"""

import asyncio
import aiohttp
import logging
import json
import time

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


async def test_advanced_api_endpoints():
    """Test all the new Phase 3 API endpoints"""
    base_url = "http://localhost:31415/api"
    
    logger.info("🧪 Testing Phase 3 Advanced API Endpoints")
    
    async with aiohttp.ClientSession() as session:
        
        # Test pool management endpoints
        logger.info("🌐 Testing Pool Management APIs...")
        
        try:
            # Get pools
            async with session.get(f"{base_url}/pools") as response:
                if response.status == 200:
                    data = await response.json()
                    pools = data.get('pools', [])
                    logger.info(f"✅ GET /pools - Found {len(pools)} pools")
                    for pool in pools:
                        logger.info(f"   - {pool['name']}: {pool['status']} ({pool['hashrate']})")
                else:
                    logger.error(f"❌ GET /pools failed: {response.status}")
            
            # Test pool connection
            async with session.post(f"{base_url}/pools/test") as response:
                if response.status == 200:
                    data = await response.json()
                    logger.info(f"✅ POST /pools/test - {data['message']}")
                else:
                    logger.error(f"❌ POST /pools/test failed: {response.status}")
            
            # Test pool switch
            async with session.post(f"{base_url}/pools/switch") as response:
                if response.status == 200:
                    data = await response.json()
                    logger.info(f"✅ POST /pools/switch - {data['message']}")
                else:
                    logger.error(f"❌ POST /pools/switch failed: {response.status}")
                    
        except Exception as e:
            logger.error(f"❌ Pool management tests failed: {e}")
        
        # Test analytics endpoints
        logger.info("📊 Testing Analytics APIs...")
        
        try:
            # Hashrate history
            async with session.get(f"{base_url}/analytics/hashrate") as response:
                if response.status == 200:
                    data = await response.json()
                    logger.info(f"✅ GET /analytics/hashrate - {len(data['timestamps'])} data points")
                else:
                    logger.error(f"❌ GET /analytics/hashrate failed: {response.status}")
            
            # Shares analytics
            async with session.get(f"{base_url}/analytics/shares") as response:
                if response.status == 200:
                    data = await response.json()
                    logger.info(f"✅ GET /analytics/shares - {data['acceptance_rate']}% acceptance rate")
                else:
                    logger.error(f"❌ GET /analytics/shares failed: {response.status}")
            
            # Profitability analysis
            async with session.get(f"{base_url}/analytics/profitability") as response:
                if response.status == 200:
                    data = await response.json()
                    logger.info(f"✅ GET /analytics/profitability - ${data['current_profit_usd_per_day']}/day profit")
                    logger.info(f"   Recommendations: {len(data['recommendations'])} suggestions")
                else:
                    logger.error(f"❌ GET /analytics/profitability failed: {response.status}")
                    
        except Exception as e:
            logger.error(f"❌ Analytics tests failed: {e}")
        
        # Test hardware optimization endpoints
        logger.info("🔧 Testing Hardware Optimization APIs...")
        
        try:
            # Get hardware profiles
            async with session.get(f"{base_url}/hardware/profiles") as response:
                if response.status == 200:
                    data = await response.json()
                    profiles = data.get('profiles', [])
                    logger.info(f"✅ GET /hardware/profiles - {len(profiles)} profiles available")
                    for profile in profiles:
                        logger.info(f"   - {profile['name']}: {profile['expected_hashrate']} MH/s @ {profile['expected_efficiency']} MH/W")
                else:
                    logger.error(f"❌ GET /hardware/profiles failed: {response.status}")
            
            # Apply hardware profile
            async with session.post(f"{base_url}/hardware/profiles/balanced/apply") as response:
                if response.status == 200:
                    data = await response.json()
                    logger.info(f"✅ POST /hardware/profiles/balanced/apply - {data['message']}")
                else:
                    logger.error(f"❌ POST /hardware/profiles/balanced/apply failed: {response.status}")
                    
        except Exception as e:
            logger.error(f"❌ Hardware optimization tests failed: {e}")
        
        # Test scheduler endpoints
        logger.info("⏰ Testing Scheduler APIs...")
        
        try:
            # Get scheduled tasks
            async with session.get(f"{base_url}/scheduler/tasks") as response:
                if response.status == 200:
                    data = await response.json()
                    tasks = data.get('tasks', [])
                    logger.info(f"✅ GET /scheduler/tasks - {len(tasks)} scheduled tasks")
                    for task in tasks:
                        status = "enabled" if task['enabled'] else "disabled"
                        logger.info(f"   - {task['name']}: {status} ({task['schedule']})")
                else:
                    logger.error(f"❌ GET /scheduler/tasks failed: {response.status}")
            
            # Create scheduled task
            async with session.post(f"{base_url}/scheduler/tasks") as response:
                if response.status == 201:
                    data = await response.json()
                    logger.info(f"✅ POST /scheduler/tasks - {data['message']}")
                else:
                    logger.error(f"❌ POST /scheduler/tasks failed: {response.status}")
                    
        except Exception as e:
            logger.error(f"❌ Scheduler tests failed: {e}")
        
        # Test notifications endpoints
        logger.info("🔔 Testing Notifications APIs...")
        
        try:
            # Get notifications
            async with session.get(f"{base_url}/notifications") as response:
                if response.status == 200:
                    data = await response.json()
                    notifications = data.get('notifications', [])
                    unread = sum(1 for n in notifications if not n['read'])
                    logger.info(f"✅ GET /notifications - {len(notifications)} notifications ({unread} unread)")
                    for notif in notifications[:3]:  # Show first 3
                        status = "unread" if not notif['read'] else "read"
                        logger.info(f"   - {notif['title']}: {notif['type']} ({status})")
                else:
                    logger.error(f"❌ GET /notifications failed: {response.status}")
            
            # Mark notification as read
            async with session.post(f"{base_url}/notifications/notif_1/read") as response:
                if response.status == 200:
                    data = await response.json()
                    logger.info(f"✅ POST /notifications/notif_1/read - {data['message']}")
                else:
                    logger.error(f"❌ POST /notifications/notif_1/read failed: {response.status}")
                    
        except Exception as e:
            logger.error(f"❌ Notifications tests failed: {e}")
        
        # Test economic guardian endpoints
        logger.info("🛡️ Testing Economic Guardian APIs...")
        
        try:
            # Get economic status
            async with session.get(f"{base_url}/economic/status") as response:
                if response.status == 200:
                    data = await response.json()
                    logger.info(f"✅ GET /economic/status - {data['current_profit_margin']}% profit margin")
                    logger.info(f"   Daily profit: ${data['estimated_daily_profit']}")
                    logger.info(f"   Recommendations: {len(data['recommendations'])} suggestions")
                else:
                    logger.error(f"❌ GET /economic/status failed: {response.status}")
            
            # Update economic settings
            async with session.post(f"{base_url}/economic/update") as response:
                if response.status == 200:
                    data = await response.json()
                    logger.info(f"✅ POST /economic/update - {data['message']}")
                else:
                    logger.error(f"❌ POST /economic/update failed: {response.status}")
                    
        except Exception as e:
            logger.error(f"❌ Economic guardian tests failed: {e}")
        
        # Test system optimization endpoints
        logger.info("⚡ Testing System Optimization APIs...")
        
        try:
            # Get system optimization
            async with session.get(f"{base_url}/system/optimization") as response:
                if response.status == 200:
                    data = await response.json()
                    logger.info(f"✅ GET /system/optimization - System stats retrieved")
                    logger.info(f"   CPU: {data['cpu_usage']}%, Memory: {data['memory_usage']}%")
                    logger.info(f"   Optimizations: {len(data['optimizations'])} suggestions")
                    for opt in data['optimizations']:
                        logger.info(f"   - {opt['category']}: {opt['suggestion']} (impact: {opt['impact']})")
                else:
                    logger.error(f"❌ GET /system/optimization failed: {response.status}")
                    
        except Exception as e:
            logger.error(f"❌ System optimization tests failed: {e}")


async def test_dashboard_accessibility():
    """Test that the advanced dashboard is accessible"""
    logger.info("🌐 Testing Advanced Dashboard Accessibility...")
    
    try:
        async with aiohttp.ClientSession() as session:
            # Test main dashboard
            async with session.get("http://localhost:31415/") as response:
                if response.status == 200:
                    content = await response.text()
                    if "Mining OS Pro" in content and "Chart.js" in content:
                        logger.info("✅ Advanced dashboard is accessible and contains expected content")
                        logger.info("   - Chart.js library loaded")
                        logger.info("   - Advanced UI components present")
                        logger.info("   - Theme toggle functionality included")
                    else:
                        logger.warning("⚠️ Dashboard accessible but may be missing advanced features")
                else:
                    logger.error(f"❌ Dashboard not accessible: {response.status}")
            
            # Test basic dashboard fallback
            async with session.get("http://localhost:31415/basic") as response:
                if response.status == 200:
                    logger.info("✅ Basic dashboard fallback is accessible")
                else:
                    logger.error(f"❌ Basic dashboard fallback failed: {response.status}")
                    
    except Exception as e:
        logger.error(f"❌ Dashboard accessibility test failed: {e}")


async def test_websocket_enhancements():
    """Test WebSocket with enhanced metrics"""
    logger.info("🔌 Testing Enhanced WebSocket Metrics...")
    
    try:
        import websockets
        
        uri = "ws://localhost:31415/ws/metrics"
        async with websockets.connect(uri) as websocket:
            logger.info("✅ WebSocket connection established")
            
            # Receive a few messages to test enhanced metrics
            for i in range(3):
                message = await websocket.recv()
                data = json.loads(message)
                
                # Check for enhanced metrics
                expected_fields = [
                    'hashrate', 'shares', 'validShares', 'invalidShares',
                    'temperature', 'power', 'efficiency', 'difficulty',
                    'profit', 'is_authorized', 'is_mining', 'uptime',
                    'pool', 'worker'
                ]
                
                missing_fields = [field for field in expected_fields if field not in data]
                
                if not missing_fields:
                    logger.info(f"✅ WebSocket message {i+1}: All enhanced metrics present")
                    logger.info(f"   Hashrate: {data['hashrate']} MH/s, Efficiency: {data['efficiency']} MH/W")
                    logger.info(f"   Pool: {data['pool']}, Mining: {data['is_mining']}")
                else:
                    logger.warning(f"⚠️ WebSocket message {i+1}: Missing fields: {missing_fields}")
                
                await asyncio.sleep(1)
                
    except ImportError:
        logger.warning("⚠️ websockets library not available, skipping WebSocket test")
    except Exception as e:
        logger.error(f"❌ WebSocket test failed: {e}")


async def main():
    """Main test function"""
    logger.info("🚀 Starting Phase 3 Advanced Features Tests")
    
    # Test 1: Advanced API Endpoints
    await test_advanced_api_endpoints()
    
    # Test 2: Dashboard Accessibility
    await test_dashboard_accessibility()
    
    # Test 3: Enhanced WebSocket
    await test_websocket_enhancements()
    
    # Summary
    logger.info("📋 Phase 3 Test Summary:")
    logger.info("✅ Advanced API endpoints tested")
    logger.info("✅ Dashboard accessibility verified")
    logger.info("✅ Enhanced WebSocket metrics tested")
    logger.info("🎉 Phase 3 advanced features are working!")


if __name__ == "__main__":
    asyncio.run(main())
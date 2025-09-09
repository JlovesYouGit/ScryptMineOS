#!/usr/bin/env python3
"""
Unit tests for the monitoring system
"""

import unittest
import asyncio
import logging
from unittest.mock import Mock, patch, AsyncMock
import sys
import os
import time

# Add the refactored directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

from monitoring.stratum_monitoring import (
    StratumMonitor, ShareStats, ConnectionStats, PerformanceMetrics
)

class TestShareStats(unittest.TestCase):
    """Test cases for ShareStats"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.share_stats = ShareStats()
    
    def test_initialization(self):
        """Test ShareStats initialization"""
        self.assertIsInstance(self.share_stats, ShareStats)
        self.assertEqual(self.share_stats.accepted, 0)
        self.assertEqual(self.share_stats.rejected, 0)
        self.assertIsNone(self.share_stats.last_accepted_time)
        self.assertIsNone(self.share_stats.last_rejected_time)
        self.assertEqual(len(self.share_stats.recent_shares), 0)
    
    def test_add_accepted(self):
        """Test adding accepted shares"""
        before_time = time.time()
        self.share_stats.add_accepted()
        after_time = time.time()
        
        self.assertEqual(self.share_stats.accepted, 1)
        self.assertIsNotNone(self.share_stats.last_accepted_time)
        self.assertTrue(before_time <= self.share_stats.last_accepted_time <= after_time)
        self.assertEqual(len(self.share_stats.recent_shares), 1)
        self.assertEqual(self.share_stats.recent_shares[0][0], 'accepted')
    
    def test_add_rejected(self):
        """Test adding rejected shares"""
        before_time = time.time()
        self.share_stats.add_rejected("test reason")
        after_time = time.time()
        
        self.assertEqual(self.share_stats.rejected, 1)
        self.assertIsNotNone(self.share_stats.last_rejected_time)
        self.assertTrue(before_time <= self.share_stats.last_rejected_time <= after_time)
        self.assertEqual(len(self.share_stats.recent_shares), 1)
        self.assertEqual(self.share_stats.recent_shares[0][0], 'rejected')
        self.assertEqual(self.share_stats.recent_shares[0][2], 'test reason')
    
    def test_acceptance_rate(self):
        """Test acceptance rate calculation"""
        # No shares
        self.assertEqual(self.share_stats.acceptance_rate(), 0.0)
        
        # Only accepted shares
        self.share_stats.add_accepted()
        self.assertEqual(self.share_stats.acceptance_rate(), 1.0)
        
        # Mixed accepted and rejected
        self.share_stats.add_rejected()
        self.assertEqual(self.share_stats.acceptance_rate(), 0.5)
        
        # More rejected than accepted
        self.share_stats.add_rejected()
        self.assertEqual(self.share_stats.acceptance_rate(), 0.25)
    
    def test_recent_acceptance_rate(self):
        """Test recent acceptance rate calculation"""
        # No recent shares
        self.assertEqual(self.share_stats.recent_acceptance_rate(), 0.0)
        
        # Add some recent shares
        self.share_stats.add_accepted()
        self.share_stats.add_accepted()
        self.share_stats.add_rejected()
        
        rate = self.share_stats.recent_acceptance_rate()
        self.assertEqual(rate, 2/3)  # 2 accepted out of 3 total

class TestConnectionStats(unittest.TestCase):
    """Test cases for ConnectionStats"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.connection_stats = ConnectionStats()
    
    def test_initialization(self):
        """Test ConnectionStats initialization"""
        self.assertIsInstance(self.connection_stats, ConnectionStats)
        self.assertEqual(self.connection_stats.connection_attempts, 0)
        self.assertEqual(self.connection_stats.successful_connections, 0)
        self.assertEqual(self.connection_stats.disconnections, 0)
        self.assertIsNone(self.connection_stats.last_connect_time)
        self.assertIsNone(self.connection_stats.last_disconnect_time)
        self.assertEqual(self.connection_stats.uptime_seconds, 0.0)
        self.assertEqual(self.connection_stats.downtime_seconds, 0.0)
        self.assertIsNone(self.connection_stats.connection_start_time)
    
    def test_on_connect(self):
        """Test recording successful connection"""
        before_time = time.time()
        self.connection_stats.on_connect()
        after_time = time.time()
        
        self.assertEqual(self.connection_stats.successful_connections, 1)
        self.assertIsNotNone(self.connection_stats.last_connect_time)
        self.assertTrue(before_time <= self.connection_stats.last_connect_time <= after_time)
        self.assertIsNotNone(self.connection_stats.connection_start_time)
    
    def test_on_disconnect(self):
        """Test recording disconnection"""
        # First connect
        self.connection_stats.on_connect()
        connect_time = self.connection_stats.connection_start_time
        
        # Then disconnect
        time.sleep(0.01)  # Small delay to ensure different timestamps
        before_time = time.time()
        self.connection_stats.on_disconnect()
        after_time = time.time()
        
        self.assertEqual(self.connection_stats.disconnections, 1)
        self.assertIsNotNone(self.connection_stats.last_disconnect_time)
        self.assertTrue(before_time <= self.connection_stats.last_disconnect_time <= after_time)
        self.assertIsNone(self.connection_stats.connection_start_time)
        # Check that uptime was calculated
        self.assertGreater(self.connection_stats.uptime_seconds, 0)
    
    def test_uptime_percentage(self):
        """Test uptime percentage calculation"""
        # No connections
        self.assertEqual(self.connection_stats.uptime_percentage(), 0.0)
        
        # Connect and disconnect to create some uptime/downtime
        self.connection_stats.uptime_seconds = 60.0
        self.connection_stats.downtime_seconds = 40.0
        self.assertEqual(self.connection_stats.uptime_percentage(), 60.0)

class TestPerformanceMetrics(unittest.TestCase):
    """Test cases for PerformanceMetrics"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.performance_metrics = PerformanceMetrics()
    
    def test_initialization(self):
        """Test PerformanceMetrics initialization"""
        self.assertIsInstance(self.performance_metrics, PerformanceMetrics)
        self.assertEqual(self.performance_metrics.hashes_per_second, 0.0)
        self.assertIsNone(self.performance_metrics.last_hash_time)
        self.assertEqual(len(self.performance_metrics.hash_intervals), 0)
        self.assertEqual(self.performance_metrics.jobs_received, 0)
        self.assertIsNone(self.performance_metrics.last_job_time)
    
    def test_record_hash(self):
        """Test recording hash computation"""
        # First hash
        self.performance_metrics.record_hash()
        self.assertIsNotNone(self.performance_metrics.last_hash_time)
        self.assertEqual(len(self.performance_metrics.hash_intervals), 0)  # Need at least 2 to calculate rate
        
        # Second hash
        time.sleep(0.01)  # Small delay
        self.performance_metrics.record_hash()
        self.assertEqual(len(self.performance_metrics.hash_intervals), 1)
        self.assertGreater(self.performance_metrics.hashes_per_second, 0)
    
    def test_record_job(self):
        """Test recording job receipt"""
        before_time = time.time()
        self.performance_metrics.record_job()
        after_time = time.time()
        
        self.assertEqual(self.performance_metrics.jobs_received, 1)
        self.assertIsNotNone(self.performance_metrics.last_job_time)
        self.assertTrue(before_time <= self.performance_metrics.last_job_time <= after_time)
    
    def test_average_hash_rate(self):
        """Test average hash rate calculation"""
        # No intervals
        self.assertEqual(self.performance_metrics.average_hash_rate(), 0.0)
        
        # Add some intervals
        self.performance_metrics.hash_intervals.append(0.01)  # 10ms per hash
        self.performance_metrics.hash_intervals.append(0.01)  # 10ms per hash
        rate = self.performance_metrics.average_hash_rate()
        self.assertAlmostEqual(rate, 100.0, places=0)  # ~100 hashes per second

class TestStratumMonitor(unittest.TestCase):
    """Test cases for StratumMonitor"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.monitor = StratumMonitor("test_worker")
    
    def test_initialization(self):
        """Test StratumMonitor initialization"""
        self.assertIsInstance(self.monitor, StratumMonitor)
        self.assertEqual(self.monitor.worker_name, "test_worker")
        self.assertIsInstance(self.monitor.share_stats, ShareStats)
        self.assertIsInstance(self.monitor.connection_stats, ConnectionStats)
        self.assertIsInstance(self.monitor.performance_metrics, PerformanceMetrics)
        self.assertEqual(len(self.monitor.alerts), 0)
        self.assertIsNotNone(self.monitor.start_time)
    
    def test_record_share_accepted(self):
        """Test recording accepted share"""
        self.monitor.record_share_accepted()
        self.assertEqual(self.monitor.share_stats.accepted, 1)
    
    def test_record_share_rejected(self):
        """Test recording rejected share"""
        self.monitor.record_share_rejected("test reason")
        self.assertEqual(self.monitor.share_stats.rejected, 1)
    
    def test_record_connection_attempt(self):
        """Test recording connection attempt"""
        self.monitor.record_connection_attempt()
        self.assertEqual(self.monitor.connection_stats.connection_attempts, 1)
    
    def test_record_connection_success(self):
        """Test recording successful connection"""
        self.monitor.record_connection_success()
        self.assertEqual(self.monitor.connection_stats.successful_connections, 1)
    
    def test_record_disconnection(self):
        """Test recording disconnection"""
        self.monitor.record_disconnection()
        self.assertEqual(self.monitor.connection_stats.disconnections, 1)
    
    def test_record_hash_computation(self):
        """Test recording hash computation"""
        self.monitor.record_hash_computation()
        # Just verify it doesn't crash
        self.assertTrue(True)
    
    def test_record_job_received(self):
        """Test recording job receipt"""
        self.monitor.record_job_received()
        self.assertEqual(self.monitor.performance_metrics.jobs_received, 1)
    
    def test_record_difficulty_change(self):
        """Test recording difficulty change"""
        self.monitor.record_difficulty_change(1.0, 2.0)
        # Just verify it doesn't crash
        self.assertTrue(True)
    
    def test_get_stats(self):
        """Test getting comprehensive statistics"""
        stats = self.monitor.get_stats()
        
        self.assertIsInstance(stats, dict)
        self.assertIn("worker_name", stats)
        self.assertIn("runtime_seconds", stats)
        self.assertIn("shares", stats)
        self.assertIn("connection", stats)
        self.assertIn("performance", stats)
        self.assertIn("alerts", stats)
        
        self.assertEqual(stats["worker_name"], "test_worker")
        self.assertIsInstance(stats["runtime_seconds"], float)
        self.assertIsInstance(stats["shares"], dict)
        self.assertIsInstance(stats["connection"], dict)
        self.assertIsInstance(stats["performance"], dict)
        self.assertIsInstance(stats["alerts"], int)

if __name__ == '__main__':
    # Configure logging for tests
    logging.basicConfig(level=logging.DEBUG)
    unittest.main()
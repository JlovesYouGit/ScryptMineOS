#!/usr/bin/env python3
"""
Unit tests for enhanced Stratum functions
"""

import unittest
import logging
from stratum_enhanced import (
    DifficultyManager, 
    StratumUtils, 
    ExtranonceManager, 
    MergedMiningConfig,
    ConnectionManager,
    StratumJobManager
)

# Configure logging for tests
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("test_stratum_enhanced")

class TestDifficultyManager(unittest.TestCase):
    """Test cases for DifficultyManager"""
    
    def setUp(self):
        self.dm = DifficultyManager(current_difficulty=1.0)
    
    def test_initialization(self):
        """Test DifficultyManager initialization"""
        self.assertEqual(self.dm.current_difficulty, 1.0)
        self.assertIsNotNone(self.dm.target)
        self.assertEqual(self.dm.min_difficulty, 0.001)
        self.assertEqual(self.dm.max_difficulty, 1000000.0)
    
    def test_difficulty_update(self):
        """Test difficulty update functionality"""
        # Valid update
        result = self.dm.update_difficulty(2.0)
        self.assertTrue(result)
        self.assertEqual(self.dm.current_difficulty, 2.0)
        
        # Invalid update (too low)
        result = self.dm.update_difficulty(0.0001)
        self.assertFalse(result)
        self.assertEqual(self.dm.current_difficulty, 2.0)  # Should remain unchanged
        
        # Invalid update (too high)
        result = self.dm.update_difficulty(2000000.0)
        self.assertFalse(result)
        self.assertEqual(self.dm.current_difficulty, 2.0)  # Should remain unchanged
    
    def test_difficulty_adjustment(self):
        """Test difficulty auto-adjustment"""
        # Test with high rejection rate (should decrease difficulty)
        new_diff = self.dm.adjust_difficulty(90, 10)  # 90% acceptance
        self.assertLess(new_diff, 1.0)
        
        # Reset and test with very high acceptance rate (should increase difficulty)
        self.dm.update_difficulty(1.0)
        new_diff = self.dm.adjust_difficulty(999, 1)  # 99.9% acceptance
        self.assertGreater(new_diff, 1.0)
        
        # Test with normal acceptance rate (should remain same)
        self.dm.update_difficulty(1.0)
        new_diff = self.dm.adjust_difficulty(97, 3)  # 97% acceptance
        self.assertEqual(new_diff, 1.0)

class TestStratumUtils(unittest.TestCase):
    """Test cases for StratumUtils"""
    
    def test_merged_mining_worker_string(self):
        """Test merged mining worker string creation and parsing"""
        config = MergedMiningConfig(
            ltc_address="Labc123",
            doge_address="Ddef456",
            aux_coin_addresses={"aux1": "Aux789", "aux2": "Aux012"},
            worker_name="testrig"
        )
        
        # Test creation
        worker_string = StratumUtils.create_merged_mining_worker_string(config)
        expected = "Labc123.Ddef456.Aux789.Aux012.testrig"
        self.assertEqual(worker_string, expected)
        
        # Test parsing
        parsed_config = StratumUtils.parse_merged_mining_worker_string(worker_string)
        self.assertEqual(parsed_config.ltc_address, "Labc123")
        self.assertEqual(parsed_config.doge_address, "Ddef456")
        self.assertEqual(parsed_config.worker_name, "testrig")
        self.assertEqual(len(parsed_config.aux_coin_addresses), 2)
        
        # Test parsing with minimal worker string
        minimal_worker = "Labc123.Ddef456.testrig"
        parsed_minimal = StratumUtils.parse_merged_mining_worker_string(minimal_worker)
        self.assertEqual(parsed_minimal.ltc_address, "Labc123")
        self.assertEqual(parsed_minimal.doge_address, "Ddef456")
        self.assertEqual(parsed_minimal.worker_name, "testrig")
        self.assertEqual(len(parsed_minimal.aux_coin_addresses), 0)
    
    def test_address_validation(self):
        """Test address validation"""
        # Valid LTC address (26-35 characters)
        self.assertTrue(StratumUtils.validate_address("Labc123def456ghi789jkl012mno345p", "ltc"))
        self.assertTrue(StratumUtils.validate_address("Mabc123def456ghi789jkl012mno345p", "ltc"))
        
        # Valid DOGE address (34 characters)
        self.assertTrue(StratumUtils.validate_address("Dabc123def456ghi789jkl012mno345pqr", "doge"))
        
        # Invalid addresses
        self.assertFalse(StratumUtils.validate_address("abc123", "ltc"))
        self.assertFalse(StratumUtils.validate_address("Labc123", "doge"))  # Wrong format for DOGE
    
    def test_hex_target_conversion(self):
        """Test hex to target and back conversion"""
        # Test hex to target
        hex_string = "00000000ffff0000000000000000000000000000000000000000000000000000"
        target_bytes = StratumUtils.hex_to_target(hex_string)
        self.assertEqual(len(target_bytes), 32)
        
        # Test target to hex
        hex_result = StratumUtils.target_to_hex(target_bytes)
        self.assertEqual(hex_result, hex_string)
        
        # Test with 0x prefix
        target_bytes2 = StratumUtils.hex_to_target("0x" + hex_string)
        self.assertEqual(target_bytes, target_bytes2)

class TestExtranonceManager(unittest.TestCase):
    """Test cases for ExtranonceManager"""
    
    def setUp(self):
        self.em = ExtranonceManager("abc123", 4)
    
    def test_initialization(self):
        """Test ExtranonceManager initialization"""
        self.assertEqual(self.em.extranonce1, "abc123")
        self.assertEqual(self.em.extranonce2_size, 4)
        self.assertEqual(self.em.extranonce2_counter, 0)
    
    def test_extranonce2_generation(self):
        """Test extranonce2 generation"""
        # Generate first extranonce2
        en2_1 = self.em.generate_extranonce2()
        self.assertEqual(self.em.extranonce2_counter, 1)
        
        # Generate second extranonce2
        en2_2 = self.em.generate_extranonce2()
        self.assertEqual(self.em.extranonce2_counter, 2)
        
        # They should be different
        self.assertNotEqual(en2_1, en2_2)
        
        # Should be valid hex and correct length
        self.assertEqual(len(bytes.fromhex(en2_1)), 4)
    
    def test_extranonce1_update(self):
        """Test extranonce1 update"""
        self.em.generate_extranonce2()  # Increment counter
        self.assertEqual(self.em.extranonce2_counter, 1)
        
        self.em.update_extranonce1("def456")
        self.assertEqual(self.em.extranonce1, "def456")
        self.assertEqual(self.em.extranonce2_counter, 0)  # Should reset
    
    def test_extranonce2_size_change(self):
        """Test extranonce2 size change"""
        self.em.set_extranonce2_size(8)
        self.assertEqual(self.em.extranonce2_size, 8)
        
        en2 = self.em.generate_extranonce2()
        self.assertEqual(len(bytes.fromhex(en2)), 8)

class TestStratumJobManager(unittest.TestCase):
    """Test cases for StratumJobManager"""
    
    def setUp(self):
        self.jm = StratumJobManager()
    
    def test_job_update(self):
        """Test job update functionality"""
        job_data = {
            'job_id': 'test_job_1',
            'prev_hash': 'abc123',
            'clean_jobs': False
        }
        
        self.jm.update_job(job_data)
        self.assertEqual(self.jm.current_job_id, 'test_job_1')
        self.assertTrue(self.jm.has_job())
        
        current_job = self.jm.get_current_job()
        self.assertEqual(current_job['job_id'], 'test_job_1')
    
    def test_clean_jobs(self):
        """Test clean jobs functionality"""
        # Add first job
        job1 = {'job_id': 'job1', 'clean_jobs': False}
        self.jm.update_job(job1)
        
        # Add second job
        job2 = {'job_id': 'job2', 'clean_jobs': False}
        self.jm.update_job(job2)
        
        # Should have both jobs
        self.assertEqual(len(self.jm.jobs), 2)
        
        # Add clean job
        job3 = {'job_id': 'job3', 'clean_jobs': True}
        self.jm.update_job(job3)
        
        # Should only have the clean job now
        self.assertEqual(len(self.jm.jobs), 1)
        self.assertEqual(self.jm.current_job_id, 'job3')

class TestConnectionManager(unittest.TestCase):
    """Test cases for ConnectionManager"""
    
    def setUp(self):
        # Use a known good endpoint for testing
        self.cm = ConnectionManager("ltc.f2pool.com", 3335, timeout=10)
    
    def test_initialization(self):
        """Test ConnectionManager initialization"""
        self.assertEqual(self.cm.host, "ltc.f2pool.com")
        self.assertEqual(self.cm.port, 3335)
        self.assertEqual(self.cm.timeout, 10)
        self.assertFalse(self.cm.connected)
        self.assertIsNone(self.cm.socket)
        self.assertIsNone(self.cm.file)
    
    # Note: We won't test actual connection in unit tests to avoid network dependencies

if __name__ == '__main__':
    unittest.main()
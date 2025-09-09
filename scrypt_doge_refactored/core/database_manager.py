"""
Database Manager for the mining system.
Handles SQLite database operations for mining statistics and system metrics.
"""

import asyncio
import sqlite3
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from pathlib import Path

logger = logging.getLogger(__name__)


@dataclass
class DatabaseConfig:
    """Database configuration"""
    enabled: bool = True
    uri: str = "sqlite:///mining_data.db"
    name: str = "mining_db"
    collections: Dict[str, str] = None
    
    def __post_init__(self):
        if self.collections is None:
            self.collections = {
                "mining_stats": "mining_statistics",
                "system_metrics": "system_metrics",
                "pool_stats": "pool_statistics"
            }


class DatabaseManager:
    """Manages database operations for the mining system"""
    
    def __init__(self, config: DatabaseConfig):
        self.config = config
        self.db_path = self._parse_db_path(config.uri)
        self.connection: Optional[sqlite3.Connection] = None
        self.logger = logging.getLogger(__name__)
        
    def _parse_db_path(self, uri: str) -> str:
        """Parse database URI to get file path"""
        if uri.startswith("sqlite:///"):
            return uri[10:]  # Remove "sqlite:///"
        elif uri.startswith("sqlite://"):
            return uri[9:]   # Remove "sqlite://"
        else:
            return uri
    
    async def initialize(self) -> bool:
        """Initialize the database and create tables"""
        try:
            # Ensure directory exists
            db_dir = Path(self.db_path).parent
            db_dir.mkdir(parents=True, exist_ok=True)
            
            # Connect to database
            self.connection = sqlite3.connect(self.db_path, check_same_thread=False)
            self.connection.row_factory = sqlite3.Row  # Enable dict-like access
            
            # Create tables
            await self._create_tables()
            
            self.logger.info(f"Database initialized: {self.db_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to initialize database: {e}")
            return False
    
    async def _create_tables(self):
        """Create database tables"""
        cursor = self.connection.cursor()
        
        # Mining statistics table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS mining_statistics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                hashrate REAL,
                shares_accepted INTEGER DEFAULT 0,
                shares_rejected INTEGER DEFAULT 0,
                shares_invalid INTEGER DEFAULT 0,
                pool_name TEXT,
                worker_name TEXT,
                temperature REAL,
                power_consumption REAL,
                profit_usd REAL,
                data JSON
            )
        """)
        
        # System metrics table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS system_metrics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                cpu_usage REAL,
                memory_usage REAL,
                disk_usage REAL,
                network_rx REAL,
                network_tx REAL,
                uptime INTEGER,
                data JSON
            )
        """)
        
        # Pool statistics table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS pool_statistics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                pool_name TEXT,
                pool_url TEXT,
                connected BOOLEAN,
                latency REAL,
                difficulty REAL,
                block_height INTEGER,
                last_share DATETIME,
                data JSON
            )
        """)
        
        # Configuration table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS configuration (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                key TEXT UNIQUE,
                value TEXT,
                data_type TEXT
            )
        """)
        
        # Events/logs table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                level TEXT,
                category TEXT,
                message TEXT,
                data JSON
            )
        """)
        
        self.connection.commit()
        self.logger.info("Database tables created successfully")
    
    async def store_mining_stats(self, stats: Dict[str, Any]) -> bool:
        """Store mining statistics"""
        try:
            cursor = self.connection.cursor()
            cursor.execute("""
                INSERT INTO mining_statistics 
                (hashrate, shares_accepted, shares_rejected, shares_invalid, 
                 pool_name, worker_name, temperature, power_consumption, profit_usd, data)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                stats.get('hashrate', 0),
                stats.get('shares_accepted', 0),
                stats.get('shares_rejected', 0),
                stats.get('shares_invalid', 0),
                stats.get('pool_name', ''),
                stats.get('worker_name', ''),
                stats.get('temperature', 0),
                stats.get('power_consumption', 0),
                stats.get('profit_usd', 0),
                json.dumps(stats)
            ))
            self.connection.commit()
            return True
        except Exception as e:
            self.logger.error(f"Failed to store mining stats: {e}")
            return False
    
    async def store_system_metrics(self, metrics: Dict[str, Any]) -> bool:
        """Store system metrics"""
        try:
            cursor = self.connection.cursor()
            cursor.execute("""
                INSERT INTO system_metrics 
                (cpu_usage, memory_usage, disk_usage, network_rx, network_tx, uptime, data)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                metrics.get('cpu_usage', 0),
                metrics.get('memory_usage', 0),
                metrics.get('disk_usage', 0),
                metrics.get('network_rx', 0),
                metrics.get('network_tx', 0),
                metrics.get('uptime', 0),
                json.dumps(metrics)
            ))
            self.connection.commit()
            return True
        except Exception as e:
            self.logger.error(f"Failed to store system metrics: {e}")
            return False
    
    async def store_pool_stats(self, stats: Dict[str, Any]) -> bool:
        """Store pool statistics"""
        try:
            cursor = self.connection.cursor()
            cursor.execute("""
                INSERT INTO pool_statistics 
                (pool_name, pool_url, connected, latency, difficulty, block_height, data)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                stats.get('pool_name', ''),
                stats.get('pool_url', ''),
                stats.get('connected', False),
                stats.get('latency', 0),
                stats.get('difficulty', 0),
                stats.get('block_height', 0),
                json.dumps(stats)
            ))
            self.connection.commit()
            return True
        except Exception as e:
            self.logger.error(f"Failed to store pool stats: {e}")
            return False
    
    async def get_mining_stats(self, hours: int = 24) -> List[Dict[str, Any]]:
        """Get mining statistics for the last N hours"""
        try:
            cursor = self.connection.cursor()
            since = datetime.now() - timedelta(hours=hours)
            cursor.execute("""
                SELECT * FROM mining_statistics 
                WHERE timestamp >= ? 
                ORDER BY timestamp DESC
            """, (since,))
            
            rows = cursor.fetchall()
            return [dict(row) for row in rows]
        except Exception as e:
            self.logger.error(f"Failed to get mining stats: {e}")
            return []
    
    async def get_system_metrics(self, hours: int = 24) -> List[Dict[str, Any]]:
        """Get system metrics for the last N hours"""
        try:
            cursor = self.connection.cursor()
            since = datetime.now() - timedelta(hours=hours)
            cursor.execute("""
                SELECT * FROM system_metrics 
                WHERE timestamp >= ? 
                ORDER BY timestamp DESC
            """, (since,))
            
            rows = cursor.fetchall()
            return [dict(row) for row in rows]
        except Exception as e:
            self.logger.error(f"Failed to get system metrics: {e}")
            return []
    
    async def get_pool_stats(self, hours: int = 24) -> List[Dict[str, Any]]:
        """Get pool statistics for the last N hours"""
        try:
            cursor = self.connection.cursor()
            since = datetime.now() - timedelta(hours=hours)
            cursor.execute("""
                SELECT * FROM pool_statistics 
                WHERE timestamp >= ? 
                ORDER BY timestamp DESC
            """, (since,))
            
            rows = cursor.fetchall()
            return [dict(row) for row in rows]
        except Exception as e:
            self.logger.error(f"Failed to get pool stats: {e}")
            return []
    
    async def store_event(self, level: str, category: str, message: str, data: Dict[str, Any] = None) -> bool:
        """Store an event/log entry"""
        try:
            cursor = self.connection.cursor()
            cursor.execute("""
                INSERT INTO events (level, category, message, data)
                VALUES (?, ?, ?, ?)
            """, (level, category, message, json.dumps(data) if data else None))
            self.connection.commit()
            return True
        except Exception as e:
            self.logger.error(f"Failed to store event: {e}")
            return False
    
    async def get_events(self, hours: int = 24, level: str = None) -> List[Dict[str, Any]]:
        """Get events/logs for the last N hours"""
        try:
            cursor = self.connection.cursor()
            since = datetime.now() - timedelta(hours=hours)
            
            if level:
                cursor.execute("""
                    SELECT * FROM events 
                    WHERE timestamp >= ? AND level = ?
                    ORDER BY timestamp DESC
                """, (since, level))
            else:
                cursor.execute("""
                    SELECT * FROM events 
                    WHERE timestamp >= ? 
                    ORDER BY timestamp DESC
                """, (since,))
            
            rows = cursor.fetchall()
            return [dict(row) for row in rows]
        except Exception as e:
            self.logger.error(f"Failed to get events: {e}")
            return []
    
    async def cleanup_old_data(self, days: int = 30) -> bool:
        """Clean up old data older than N days"""
        try:
            cursor = self.connection.cursor()
            cutoff = datetime.now() - timedelta(days=days)
            
            # Clean up old records
            tables = ['mining_statistics', 'system_metrics', 'pool_statistics', 'events']
            for table in tables:
                cursor.execute(f"DELETE FROM {table} WHERE timestamp < ?", (cutoff,))
            
            self.connection.commit()
            self.logger.info(f"Cleaned up data older than {days} days")
            return True
        except Exception as e:
            self.logger.error(f"Failed to cleanup old data: {e}")
            return False
    
    async def get_summary_stats(self) -> Dict[str, Any]:
        """Get summary statistics"""
        try:
            cursor = self.connection.cursor()
            
            # Get latest mining stats
            cursor.execute("""
                SELECT AVG(hashrate) as avg_hashrate, 
                       SUM(shares_accepted) as total_accepted,
                       SUM(shares_rejected) as total_rejected,
                       AVG(temperature) as avg_temp,
                       AVG(power_consumption) as avg_power
                FROM mining_statistics 
                WHERE timestamp >= datetime('now', '-24 hours')
            """)
            mining_row = cursor.fetchone()
            
            # Get total records count
            cursor.execute("SELECT COUNT(*) as count FROM mining_statistics")
            total_records = cursor.fetchone()['count']
            
            return {
                'avg_hashrate_24h': mining_row['avg_hashrate'] or 0,
                'total_shares_accepted_24h': mining_row['total_accepted'] or 0,
                'total_shares_rejected_24h': mining_row['total_rejected'] or 0,
                'avg_temperature_24h': mining_row['avg_temp'] or 0,
                'avg_power_24h': mining_row['avg_power'] or 0,
                'total_records': total_records,
                'database_size_mb': Path(self.db_path).stat().st_size / (1024 * 1024) if Path(self.db_path).exists() else 0
            }
        except Exception as e:
            self.logger.error(f"Failed to get summary stats: {e}")
            return {}
    
    async def close(self):
        """Close database connection"""
        if self.connection:
            self.connection.close()
            self.connection = None
            self.logger.info("Database connection closed")


# Utility functions for testing
async def test_database():
    """Test database functionality"""
    config = DatabaseConfig()
    db = DatabaseManager(config)
    
    # Initialize
    success = await db.initialize()
    print(f"Database initialization: {'SUCCESS' if success else 'FAILED'}")
    
    if success:
        # Test storing data
        test_stats = {
            'hashrate': 125.5,
            'shares_accepted': 100,
            'shares_rejected': 2,
            'pool_name': 'test_pool',
            'worker_name': 'test_worker',
            'temperature': 65.0,
            'power_consumption': 150.0,
            'profit_usd': 2.50
        }
        
        success = await db.store_mining_stats(test_stats)
        print(f"Store mining stats: {'SUCCESS' if success else 'FAILED'}")
        
        # Test retrieving data
        stats = await db.get_mining_stats(1)
        print(f"Retrieved {len(stats)} mining stat records")
        
        # Test summary
        summary = await db.get_summary_stats()
        print(f"Summary stats: {summary}")
        
        # Close
        await db.close()


if __name__ == "__main__":
    asyncio.run(test_database())
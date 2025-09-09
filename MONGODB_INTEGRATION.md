# MongoDB Atlas Integration for Scrypt DOGE Mining System

This document describes how to set up and use MongoDB Atlas with the Scrypt DOGE mining system for storing mining statistics, share data, and performance metrics.

## Overview

The MongoDB integration provides persistent storage for mining data, allowing for historical analysis, monitoring, and reporting. The integration includes:

1. Database connection management
2. Data models for mining statistics
3. Automatic data storage from monitoring components
4. Configuration management

## Prerequisites

1. MongoDB Atlas account (https://www.mongodb.com/cloud/atlas)
2. Python 3.10+
3. PyMongo library (included in requirements)

## Setup Instructions

### 1. Create MongoDB Atlas Cluster

1. Sign up for a MongoDB Atlas account
2. Create a new cluster
3. Configure network access (add your IP address)
4. Create a database user with read/write permissions
5. Get your connection string

### 2. Configure Database Settings

Update the `config/mining_config.yaml` file with your MongoDB connection details:

```yaml
database:
  enabled: true
  uri: "mongodb+srv://username:password@cluster.mongodb.net/mining_db?retryWrites=true&w=majority"
  name: "mining_db"
  collections:
    shares: "shares"
    performance: "performance"
    system_metrics: "system_metrics"
    alerts: "alerts"
```

Alternatively, set the `MONGODB_URI` environment variable:

```bash
export MONGODB_URI="mongodb+srv://username:password@cluster.mongodb.net/mining_db?retryWrites=true&w=majority"
```

### 3. Install Dependencies

Install the required dependencies:

```bash
pip install -r requirements.txt
```

This will install PyMongo and dnspython which are required for MongoDB connectivity.

## Data Models

The integration includes the following data models:

### ShareData
- `job_id`: Mining job identifier
- `extranonce2`: Extranonce2 value
- `ntime`: Block time
- `nonce`: Nonce value
- `hash_result`: Hash result
- `worker_name`: Worker identifier
- `difficulty`: Difficulty level
- `accepted`: Whether the share was accepted
- `reason`: Rejection reason (if rejected)

### PerformanceMetric
- `hashrate`: Current hashrate
- `accepted_shares`: Number of accepted shares
- `rejected_shares`: Number of rejected shares
- `hardware_errors`: Number of hardware errors
- `uptime_seconds`: System uptime
- `worker_name`: Worker identifier

### SystemMetric
- `cpu_percent`: CPU usage percentage
- `memory_percent`: Memory usage percentage
- `disk_usage_percent`: Disk usage percentage
- `network_bytes_sent`: Network bytes sent
- `network_bytes_recv`: Network bytes received
- `worker_name`: Worker identifier

### AlertData
- `alert_type`: Type of alert
- `message`: Alert message
- `severity`: Alert severity (info, warning, error, critical)
- `worker_name`: Worker identifier
- `resolved`: Whether the alert is resolved
- `resolution_message`: Resolution message

## Integration Points

The MongoDB integration is automatically used by the following components:

1. **SystemMonitor**: Stores system metrics and share statistics
2. **StratumMonitor**: Stores share submission data
3. **EnhancedStratumClient**: Stores share data and alerts

## Testing

Run the test script to verify the integration:

```bash
python tests/test_database_integration.py
```

## Security Considerations

1. Always use secure connection strings with authentication
2. Restrict database user permissions to only what is needed
3. Use environment variables for sensitive data like connection strings
4. Regularly rotate database credentials

## Troubleshooting

### Connection Issues
- Verify your MongoDB Atlas connection string
- Check network access rules in MongoDB Atlas
- Ensure your IP is whitelisted

### Authentication Issues
- Verify username and password
- Check database user permissions
- Ensure the user has read/write access to the database

### Performance Issues
- Monitor database performance in MongoDB Atlas
- Consider upgrading your cluster tier if needed
- Optimize queries and indexes as needed

## Data Retention

The system does not automatically delete old data. Consider implementing a data retention policy in MongoDB Atlas:

1. Use MongoDB Atlas Data Lake for long-term storage
2. Implement TTL indexes for automatic data expiration
3. Regularly archive old data to reduce database size

## Monitoring

Monitor your MongoDB Atlas cluster through:

1. MongoDB Atlas dashboard
2. Database performance metrics
3. Connection logs
4. Query performance analysis

## Support

For issues with the MongoDB integration, please check:

1. MongoDB Atlas documentation
2. PyMongo documentation
3. Project issue tracker
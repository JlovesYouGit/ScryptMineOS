#!/usr/bin/env python3
"""
Structured Logger and Alerting System for the refactored Scrypt DOGE mining system.
Implements JSON logging, log rotation, and alerting mechanisms.
"""

import logging
import json
import os
import sys
from typing import Dict, Any, Optional
from datetime import datetime
from logging.handlers import RotatingFileHandler
import asyncio
import traceback
import aiohttp
from dataclasses import dataclass, field

@dataclass
class Alert:
    """Alert data structure"""
    timestamp: str
    alert_type: str
    message: str
    severity: str
    data: Dict[str, Any] = field(default_factory=dict)

class StructuredLogger:
    """Structured JSON logger for mining operations"""
    
    def __init__(self, name: str = "mining_system", log_file: str = "logs/mining.log"):
        self.name = name
        self.log_file = log_file
        
        # Create logs directory if it doesn't exist
        os.makedirs(os.path.dirname(log_file) if os.path.dirname(log_file) else ".", exist_ok=True)
        
        # Create logger
        self.logger = logging.getLogger(name)
        self.logger.setLevel(logging.DEBUG)
        
        # Prevent adding multiple handlers if logger already exists
        if not self.logger.handlers:
            # Create formatter
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            
            # Create console handler
            console_handler = logging.StreamHandler(sys.stdout)
            console_handler.setLevel(logging.INFO)
            console_handler.setFormatter(formatter)
            self.logger.addHandler(console_handler)
            
            # Create file handler with rotation
            file_handler = RotatingFileHandler(
                log_file,
                maxBytes=10*1024*1024,  # 10MB
                backupCount=5
            )
            file_handler.setLevel(logging.DEBUG)
            file_handler.setFormatter(formatter)
            self.logger.addHandler(file_handler)
    
    def _log_structured(self, level: str, event_type: str, data: Dict[str, Any], message: str = ""):
        """Log structured data"""
        log_entry = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "logger": self.name,
            "level": level,
            "event_type": event_type,
            "data": data,
            "message": message
        }
        
        log_message = json.dumps(log_entry, default=str)
        
        if level == "DEBUG":
            self.logger.debug(log_message)
        elif level == "INFO":
            self.logger.info(log_message)
        elif level == "WARNING":
            self.logger.warning(log_message)
        elif level == "ERROR":
            self.logger.error(log_message)
        elif level == "CRITICAL":
            self.logger.critical(log_message)
    
    def debug(self, event_type: str, data: Dict[str, Any], message: str = ""):
        """Log debug event"""
        self._log_structured("DEBUG", event_type, data, message)
    
    def info(self, event_type: str, data: Dict[str, Any], message: str = ""):
        """Log info event"""
        self._log_structured("INFO", event_type, data, message)
    
    def warning(self, event_type: str, data: Dict[str, Any], message: str = ""):
        """Log warning event"""
        self._log_structured("WARNING", event_type, data, message)
    
    def error(self, event_type: str, data: Dict[str, Any], message: str = "", exception: Exception = None):
        """Log error event"""
        if exception:
            data["exception"] = str(exception)
            data["traceback"] = traceback.format_exc()
        self._log_structured("ERROR", event_type, data, message)
    
    def critical(self, event_type: str, data: Dict[str, Any], message: str = "", exception: Exception = None):
        """Log critical event"""
        if exception:
            data["exception"] = str(exception)
            data["traceback"] = traceback.format_exc()
        self._log_structured("CRITICAL", event_type, data, message)
    
    def log_mining_event(self, event: str, job_id: str = None, difficulty: float = None, success: bool = None):
        """Log mining-specific events"""
        data = {}
        if job_id:
            data["job_id"] = job_id
        if difficulty:
            data["difficulty"] = difficulty
        if success is not None:
            data["success"] = success
            
        self.info("mining_event", data, f"Mining event: {event}")
    
    def log_share_submission(self, job_id: str, success: bool, difficulty: float, error: str = None):
        """Log share submission event"""
        data = {
            "job_id": job_id,
            "success": success,
            "difficulty": difficulty
        }
        if error:
            data["error"] = error
        
        level = "INFO" if success else "WARNING"
        if level == "INFO":
            self.info("share_submission", data, "Share submitted")
        else:
            self.warning("share_submission", data, f"Share rejected: {error}")
    
    def log_connection_event(self, pool_url: str, event: str, details: Dict[str, Any] = None):
        """Log connection-related events"""
        data = {
            "pool_url": pool_url,
            "event": event
        }
        if details:
            data.update(details)
        
        self.info("connection_event", data, f"Connection event: {event}")
    
    def log_performance_metric(self, metric_name: str, value: float, unit: str):
        """Log performance metrics"""
        data = {
            "metric_name": metric_name,
            "value": value,
            "unit": unit
        }
        
        self.info("performance_metric", data, f"Performance metric: {metric_name} = {value} {unit}")
    
    def log_system_event(self, event: str, details: Dict[str, Any] = None):
        """Log system events"""
        data = {
            "event": event
        }
        if details:
            data.update(details)
        
        self.info("system_event", data, f"System event: {event}")


class AlertManager:
    """Manages alerts and notifications for critical events"""
    
    def __init__(self, logger: StructuredLogger):
        self.logger = logger
        self.alerts_enabled = True
        self.alert_thresholds = {
            "high_rejected_shares": 0.05,  # 5% rejected shares
            "low_hashrate": 0.7,  # 70% of expected hashrate
            "high_temperature": 80.0,  # 80°C
            "connection_failures": 5  # 5 consecutive failures
        }
        self.alert_history = []
        self.webhook_url: Optional[str] = None
        self.email_recipients: list = []
    
    def configure_webhook(self, webhook_url: str):
        """Configure webhook for alert notifications"""
        self.webhook_url = webhook_url
        self.logger.info("alerting", {"webhook_url": webhook_url}, "Webhook configured for alerts")
    
    def configure_email(self, recipients: list):
        """Configure email recipients for alerts"""
        self.email_recipients = recipients
        self.logger.info("alerting", {"recipients": recipients}, "Email recipients configured for alerts")
    
    def check_and_alert(self, metric_name: str, value: float, expected_value: float = None):
        """Check metrics and send alerts if thresholds are exceeded"""
        if not self.alerts_enabled:
            return
        
        alert_sent = False
        alert_message = ""
        alert_type = ""
        
        if metric_name == "rejected_shares_rate" and value > self.alert_thresholds["high_rejected_shares"]:
            alert_type = "HIGH_REJECTED_SHARES"
            alert_message = f"Rejected shares rate is high: {value:.2%}"
            self.send_alert(alert_type, alert_message)
            alert_sent = True
            
        elif metric_name == "hashrate" and expected_value and value < expected_value * self.alert_thresholds["low_hashrate"]:
            alert_type = "LOW_HASHRATE"
            alert_message = f"Hashrate is low: {value} H/s (expected: {expected_value} H/s)"
            self.send_alert(alert_type, alert_message)
            alert_sent = True
            
        elif metric_name == "temperature" and value > self.alert_thresholds["high_temperature"]:
            alert_type = "HIGH_TEMPERATURE"
            alert_message = f"High temperature detected: {value}°C"
            self.send_alert(alert_type, alert_message)
            alert_sent = True
        
        if alert_sent:
            self.logger.warning("alert_sent", {
                "metric": metric_name, 
                "value": value, 
                "alert_type": alert_type,
                "message": alert_message
            }, f"Alert sent for {metric_name}")
    
    def send_alert(self, alert_type: str, message: str, severity: str = "WARNING", data: Dict[str, Any] = None):
        """Send an alert through multiple channels"""
        alert = Alert(
            timestamp=datetime.utcnow().isoformat() + "Z",
            alert_type=alert_type,
            message=message,
            severity=severity,
            data=data or {}
        )
        
        self.alert_history.append(alert)
        # Keep only last 100 alerts
        if len(self.alert_history) > 100:
            self.alert_history = self.alert_history[-100:]
        
        # Log the alert
        self.logger.warning("alert", {
            "alert_type": alert_type,
            "message": message,
            "severity": severity,
            "data": data
        }, f"ALERT: {alert_type} - {message}")
        
        # Send to webhook if configured
        if self.webhook_url:
            asyncio.create_task(self._send_webhook_alert(alert))
        
        # Send email if configured (placeholder)
        if self.email_recipients:
            self._send_email_alert(alert)
    
    async def _send_webhook_alert(self, alert: Alert):
        """Send alert via webhook"""
        try:
            async with aiohttp.ClientSession() as session:
                payload = {
                    "alert_type": alert.alert_type,
                    "message": alert.message,
                    "severity": alert.severity,
                    "timestamp": alert.timestamp,
                    "data": alert.data
                }
                async with session.post(self.webhook_url, json=payload) as response:
                    if response.status != 200:
                        self.logger.error("webhook_error", {
                            "status": response.status,
                            "alert_type": alert.alert_type
                        }, f"Failed to send webhook alert: {response.status}")
        except Exception as e:
            self.logger.error("webhook_error", {
                "exception": str(e),
                "alert_type": alert.alert_type
            }, f"Exception sending webhook alert: {e}")
    
    def _send_email_alert(self, alert: Alert):
        """Send alert via email (placeholder)"""
        # This would integrate with an email service
        self.logger.info("email_alert", {
            "recipients": self.email_recipients,
            "alert_type": alert.alert_type
        }, f"Email alert would be sent to {len(self.email_recipients)} recipients")
    
    def get_recent_alerts(self, count: int = 10) -> list:
        """Get recent alerts"""
        return [{
            "timestamp": alert.timestamp,
            "alert_type": alert.alert_type,
            "message": alert.message,
            "severity": alert.severity
        } for alert in self.alert_history[-count:]]
    
    def enable_alerts(self):
        """Enable alerting"""
        self.alerts_enabled = True
        self.logger.info("alerting", {}, "Alerts enabled")
    
    def disable_alerts(self):
        """Disable alerting"""
        self.alerts_enabled = False
        self.logger.info("alerting", {}, "Alerts disabled")
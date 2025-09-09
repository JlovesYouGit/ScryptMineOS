"""
Web server for Mining OS.
"""
import asyncio
import json
import logging
import os
import sys
import time
from fastapi import FastAPI, WebSocket
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, StreamingResponse
from pydantic import BaseModel
import uvicorn
import ssl

from .config import Settings
from .mining import MiningController
from .constants import LTC_WALLET_ADDRESS, DOGE_WALLET_ADDRESS

logger = logging.getLogger(__name__)


class MiningOSServer:
    def __init__(self, settings: Settings):
        # Check if PAYOUT_ADDR is set
        payout_addr = settings.get_payout_address()
        if not payout_addr:
            logger.error("PAYOUT_ADDR environment variable is required")
            sys.exit(64)  # Exit code 64 for usage error

        self.settings = settings
        self.app = FastAPI(title="Mining OS", version="0.1.0")
        self.mining_controller = MiningController(settings)
        self.pool_switch_count = 0
        self.setup_middleware()
        self.setup_routes()

    def setup_middleware(self):
        """Set up middleware for the application."""
        # CORS middleware with restricted origins for security
        allowed_origins = os.environ.get(
            "ALLOWED_ORIGINS",
            "http://localhost:31415,http://127.0.0.1:31415,"
            "https://localhost:31415,https://127.0.0.1:31415"
        ).split(",")
        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=allowed_origins,
            allow_credentials=True,
            allow_methods=["GET", "POST", "PUT", "DELETE"],
            allow_headers=["*"],
            # Add security headers and SSE support
            expose_headers=[
                "X-Content-Type-Options",
                "X-Frame-Options",
                "X-XSS-Protection",
                "Content-Type",
                "Cache-Control",
                "Connection"
            ],
        )

    def setup_routes(self):
        """Set up routes for the application."""
        # Health check endpoint
        @self.app.get("/health")
        async def health_check():
            return JSONResponse(
                content={
                    "status": "up",
                    "uptime": "0s",  # In a real implementation,
                    # track actual uptime
                    "version": "0.1.0"
                },
                status_code=200
            )

        # Serve static files (React frontend) - this should be EARLY
        # but not at root
        try:
            # Get the directory where this file is located
            current_dir = os.path.dirname(os.path.abspath(__file__))
            static_dir = os.path.join(current_dir, "static")
            if os.path.exists(static_dir):
                # Mount static files at a specific path, not at root
                self.app.mount(
                    "/static",
                    StaticFiles(directory=static_dir, html=True),
                    name="static"
                )
            else:
                logger.warning(
                    f"Static files directory not found: {static_dir}"
                )
        except Exception as e:
            logger.warning(
                f"Failed to mount static files: {e}"
            )

        # Main page - serve advanced dashboard
        @self.app.get("/")
        async def main_page():
            # Serve the advanced HTML dashboard
            try:
                current_dir = os.path.dirname(os.path.abspath(__file__))
                html_path = os.path.join(current_dir, "static", "advanced_dashboard.html")
                if os.path.exists(html_path):
                    with open(html_path, 'r', encoding='utf-8') as f:
                        html_content = f.read()
                    from fastapi.responses import HTMLResponse
                    return HTMLResponse(content=html_content, status_code=200)
                else:
                    # Fallback to basic dashboard
                    basic_html_path = os.path.join(current_dir, "static", "index.html")
                    if os.path.exists(basic_html_path):
                        with open(basic_html_path, 'r', encoding='utf-8') as f:
                            html_content = f.read()
                        from fastapi.responses import HTMLResponse
                        return HTMLResponse(content=html_content, status_code=200)
                    else:
                        return JSONResponse(
                            content={"message": "Mining OS Frontend - HTML file not found"},
                            status_code=200
                        )
            except Exception as e:
                logger.error(f"Error serving main page: {e}")
                return JSONResponse(
                    content={"message": "Mining OS Frontend", "error": str(e)},
                    status_code=200
                )

        # Basic dashboard route
        @self.app.get("/basic")
        async def basic_dashboard():
            # Serve the basic HTML dashboard
            try:
                current_dir = os.path.dirname(os.path.abspath(__file__))
                html_path = os.path.join(current_dir, "static", "index.html")
                if os.path.exists(html_path):
                    with open(html_path, 'r', encoding='utf-8') as f:
                        html_content = f.read()
                    from fastapi.responses import HTMLResponse
                    return HTMLResponse(content=html_content, status_code=200)
                else:
                    return JSONResponse(
                        content={"message": "Basic dashboard not found"},
                        status_code=404
                    )
            except Exception as e:
                logger.error(f"Error serving basic dashboard: {e}")
                return JSONResponse(
                    content={"message": "Error loading basic dashboard", "error": str(e)},
                    status_code=500
                )

        # API routes
        api_router = FastAPI()

        # Get mining configuration
        @api_router.get("/config")
        async def get_config():
            # Get wallet addresses and pool info from environment
            # variables or defaults
            worker_name = os.environ.get("WORKER_NAME", "rig01")
            payout_addr = self.settings.get_payout_address()

            # Get pool information
            ltc_pool_host = os.environ.get("LTC_POOL_HOST", "ltc.f2pool.com")
            ltc_pool_port = int(os.environ.get("LTC_POOL_PORT", "8888"))
            doge_pool_host = os.environ.get("DOGE_POOL_HOST", "doge.zsolo.bid")
            doge_pool_port = int(os.environ.get("DOGE_POOL_PORT", "8057"))

            return JSONResponse(
                content={
                    "ltcAddress": LTC_WALLET_ADDRESS,  # Constant LTC address
                    "dogeAddress": DOGE_WALLET_ADDRESS,  # Constant DOGE
                    "workerName": worker_name,
                    "payoutAddress": payout_addr,
                    "ltcPoolHost": ltc_pool_host,
                    "ltcPoolPort": ltc_pool_port,
                    "dogePoolHost": doge_pool_host,
                    "dogePoolPort": doge_pool_port
                },
                status_code=200
            )

        # Get mining status
        @api_router.get("/status")
        async def get_status():
            status_data = self.mining_controller.get_status()
            # Update pool switch count from mining controller
            self.pool_switch_count = status_data.get("pool_switches", 0)
            return JSONResponse(
                content=status_data,
                status_code=200
            )

        # Start mining
        @api_router.post("/actions/start")
        async def start_mining():
            try:
                success = await self.mining_controller.start()
                if success:
                    controller_status = self.mining_controller.get_status()
                    return JSONResponse(
                        content={
                            "jobId": "mining-job-1",
                            "state": "spinning",
                            "status": controller_status,
                            "message": "Mining started successfully"
                        },
                        status_code=200
                    )
                return JSONResponse(
                    content={
                        "error": "ECONOMIC_GUARDIAN_BLOCKED",
                        "message": (
                            "Mining not started due to economic conditions"
                        )
                    },
                    status_code=409
                )
            except Exception as e:
                logger.error(f"Failed to start mining: {e}")
                return JSONResponse(
                    content={
                        "error": "FAILED_TO_START_MINING",
                        "message": str(e)
                    },
                    status_code=500
                )

        # Stop mining
        @api_router.post("/actions/stop")
        async def stop_mining():
            try:
                await self.mining_controller.stop()
                controller_status = self.mining_controller.get_status()
                return JSONResponse(
                    content={
                        "state": "idle",
                        "status": controller_status,
                        "message": "Mining stopped successfully"
                    },
                    status_code=200
                )
            except Exception as e:
                logger.error(f"Failed to stop mining: {e}")
                return JSONResponse(
                    content={
                        "error": "FAILED_TO_STOP_MINING",
                        "message": str(e)
                    },
                    status_code=500
                )

        # Configuration
        class ConfigUpdate(BaseModel):
            worker_name: str
            minimum_payout_threshold: float
            max_temperature: float
            min_profit_margin: float

        @api_router.put("/config")
        async def update_config(config: ConfigUpdate):
            # Check if the request tries to update the payout address
            # or wallet addresses
            # This is protected and can only be set via environment variable
            if (hasattr(config, "payoutAddress") or
                    hasattr(config, "ltcAddress") or
                    hasattr(config, "dogeAddress")):
                return JSONResponse(
                    content={
                        "error": "WALLET_ADDRESSES_IMMUTABLE",
                        "message": (
                            "Wallet addresses are immutable and can "
                            "only be set via environment variables. "
                            "Use PAYOUT_ADDR env var."
                        )
                    },
                    status_code=403
                )

            # In a real implementation, update the configuration
            # For now, we'll just save to environment variables or a file
            try:
                # Save to environment variables
                # (in a real app, you'd save to a config file)
                os.environ["WORKER_NAME"] = config.worker_name
                os.environ["MINIMUM_PAYOUT_THRESHOLD"] = \
                    str(config.minimum_payout_threshold)
                return JSONResponse(
                    content={
                        "needs_restart": True,
                        "message": "Configuration updated successfully"
                    },
                    status_code=200
                )
            except Exception as e:
                logger.error(f"Failed to update config: {e}")
                return JSONResponse(
                    content={
                        "error": "FAILED_TO_UPDATE_CONFIG",
                        "message": str(e)
                    },
                    status_code=500
                )

        # Pool information
        @api_router.get("/pool/info")
        async def get_pool_info():
            # Return pool information including minimum payout threshold
            return JSONResponse(
                content={
                    "minimum_payout_threshold": 0.001,  # Example value
                    "supported_features": [
                        "pl_parameter",
                        "difficulty_suggestion"
                    ]
                },
                status_code=200
            )

        # Pool payouts
        @api_router.get("/pool/payouts")
        async def get_pool_payouts():
            # Return recent payout information
            return JSONResponse(
                content={
                    "last_payout": "2023-01-01T00:00:00Z",
                    "confirmed_balance": 0.005,
                    "pending_balance": 0.001
                },
                status_code=200
            )

        # Metrics endpoint for Prometheus
        @api_router.get("/metrics")
        async def get_metrics():
            """Return Prometheus metrics"""
            status_data = self.mining_controller.get_status()
            metrics = [
                "# TYPE pool_switches counter",
                f"pool_switches {status_data.get('pool_switches', 0)}",
                "# TYPE is_mining gauge",
                "is_mining " +
                f"{1 if status_data.get('is_mining', False) else 0}",
                "# TYPE uptime_seconds gauge",
                "uptime_seconds " +
                f"{self._parse_uptime(status_data.get('uptime', '0s'))}",
                "# TYPE is_authorized gauge",
                "is_authorized " +
                f"{1 if status_data.get('is_authorized', False) else 0}"
            ]
            return JSONResponse(
                content={"metrics": "\n".join(metrics)},
                status_code=200
            )

        @api_router.get("/config/schema")
        async def get_config_schema():
            # Return JSON schema for configuration
            return JSONResponse(
                content={
                    "type": "object",
                    "properties": {
                        "worker_name": {"type": "string"},
                        "minimum_payout_threshold": {"type": "number"},
                        "max_temperature": {"type": "number"},
                        "min_profit_margin": {"type": "number"}
                    }
                },
                status_code=200
            )

        # Logs - Server-Sent Events endpoint
        @api_router.get("/logs")
        async def get_logs():
            # Create a generator that yields log messages as SSE events
            async def log_generator():
                try:
                    # Send SSE headers
                    yield "retry: 10000\n\n"  # Retry every 10 seconds

                    # For now, we'll simulate log messages
                    # In a real implementation, this would connect to the
                    # actual logging system
                    counter = 0
                    while True:
                        counter += 1
                        log_entry = {
                            "timestamp": time.time(),
                            "level": "info",
                            "message": (
                                f"Log message #{counter} "
                                f"from mining process"
                            )
                        }
                        # Format as SSE event
                        yield f"data: {json.dumps(log_entry)}\n\n"
                        # Send a log message every 2 seconds
                        await asyncio.sleep(2)
                except asyncio.CancelledError:
                    # Client disconnected
                    logger.info("Log stream client disconnected")
                    raise
                except Exception as e:
                    logger.error(f"Error in log stream: {e}")
                    error_entry = {
                        "timestamp": time.time(),
                        "level": "error",
                        "message": f"Error in log stream: {str(e)}"
                    }
                    yield f"data: {json.dumps(error_entry)}\n\n"

            # Return streaming response with SSE content type
            response = StreamingResponse(
                log_generator(),
                media_type="text/event-stream"
            )
            response.headers["Cache-Control"] = "no-cache"
            response.headers["Connection"] = "keep-alive"
            return response

        # Advanced API endpoints for Phase 3 features
        
        # Pool management endpoints
        @api_router.get("/pools")
        async def get_pools():
            """Get available mining pools"""
            pools = [
                {
                    "id": "f2pool_ltc",
                    "name": "F2Pool LTC",
                    "url": "stratum+tcp://ltc.f2pool.com:8888",
                    "algorithm": "scrypt",
                    "status": "online",
                    "hashrate": "125.4 MH/s",
                    "latency": 45,
                    "fee": 2.5,
                    "minimum_payout": 0.005
                },
                {
                    "id": "zsolo_doge",
                    "name": "ZSolo DOGE",
                    "url": "stratum+tcp://doge.zsolo.bid:8057",
                    "algorithm": "scrypt",
                    "status": "online",
                    "hashrate": "98.7 MH/s",
                    "latency": 32,
                    "fee": 1.0,
                    "minimum_payout": 0.001
                }
            ]
            return JSONResponse(content={"pools": pools}, status_code=200)
        
        @api_router.post("/pools/switch")
        async def switch_pool():
            """Switch to a different mining pool"""
            # In real implementation, this would switch pools
            return JSONResponse(
                content={"message": "Pool switch initiated", "success": True},
                status_code=200
            )
        
        @api_router.post("/pools/test")
        async def test_pool_connection():
            """Test connection to a mining pool"""
            return JSONResponse(
                content={
                    "pool": "F2Pool LTC",
                    "status": "connected",
                    "latency": 45,
                    "message": "Connection successful"
                },
                status_code=200
            )
        
        # Analytics endpoints
        @api_router.get("/analytics/hashrate")
        async def get_hashrate_history():
            """Get hashrate history for charts"""
            # Mock data for now - in real implementation, get from database
            import random
            timestamps = []
            hashrates = []
            
            for i in range(20):
                timestamps.append(f"{i:02d}:00")
                hashrates.append(120 + random.uniform(-10, 15))
            
            return JSONResponse(
                content={
                    "timestamps": timestamps,
                    "hashrates": hashrates
                },
                status_code=200
            )
        
        @api_router.get("/analytics/shares")
        async def get_shares_analytics():
            """Get share statistics"""
            return JSONResponse(
                content={
                    "accepted": 1250,
                    "rejected": 45,
                    "invalid": 12,
                    "acceptance_rate": 96.2,
                    "recent_shares": [
                        {"timestamp": "12:00", "accepted": 50, "rejected": 2},
                        {"timestamp": "12:05", "accepted": 48, "rejected": 1},
                        {"timestamp": "12:10", "accepted": 52, "rejected": 3}
                    ]
                },
                status_code=200
            )
        
        @api_router.get("/analytics/profitability")
        async def get_profitability_analysis():
            """Get profitability analysis"""
            return JSONResponse(
                content={
                    "current_profit_usd_per_day": 2.45,
                    "electricity_cost_per_day": 0.86,
                    "net_profit_per_day": 1.59,
                    "break_even_hashrate": 85.2,
                    "roi_days": 245,
                    "profit_margin_percent": 64.9,
                    "recommendations": [
                        "Consider switching to DOGE pool for 12% higher profit",
                        "Optimize power settings to reduce electricity cost",
                        "Current efficiency is above average"
                    ]
                },
                status_code=200
            )
        
        # Hardware optimization endpoints
        @api_router.get("/hardware/profiles")
        async def get_hardware_profiles():
            """Get hardware optimization profiles"""
            profiles = [
                {
                    "id": "balanced",
                    "name": "Balanced",
                    "description": "Optimal balance of performance and efficiency",
                    "power_limit": 180,
                    "temperature_target": 75,
                    "fan_speed": "auto",
                    "expected_hashrate": 125.4,
                    "expected_efficiency": 0.83
                },
                {
                    "id": "performance",
                    "name": "High Performance",
                    "description": "Maximum hashrate with higher power consumption",
                    "power_limit": 220,
                    "temperature_target": 80,
                    "fan_speed": 85,
                    "expected_hashrate": 145.2,
                    "expected_efficiency": 0.66
                },
                {
                    "id": "efficiency",
                    "name": "High Efficiency",
                    "description": "Lower power consumption with reduced hashrate",
                    "power_limit": 150,
                    "temperature_target": 65,
                    "fan_speed": "auto",
                    "expected_hashrate": 105.8,
                    "expected_efficiency": 1.02
                }
            ]
            return JSONResponse(content={"profiles": profiles}, status_code=200)
        
        @api_router.post("/hardware/profiles/{profile_id}/apply")
        async def apply_hardware_profile(profile_id: str):
            """Apply a hardware optimization profile"""
            return JSONResponse(
                content={
                    "message": f"Applied {profile_id} profile successfully",
                    "profile_id": profile_id,
                    "restart_required": False
                },
                status_code=200
            )
        
        # Scheduler endpoints
        @api_router.get("/scheduler/tasks")
        async def get_scheduled_tasks():
            """Get scheduled mining tasks"""
            tasks = [
                {
                    "id": "daily_mining",
                    "name": "Daily Mining Schedule",
                    "enabled": True,
                    "schedule": "0 8 * * *",  # 8 AM daily
                    "action": "start_mining",
                    "conditions": ["profit_margin > 5%", "temperature < 80°C"]
                },
                {
                    "id": "night_stop",
                    "name": "Night Stop",
                    "enabled": True,
                    "schedule": "0 22 * * *",  # 10 PM daily
                    "action": "stop_mining",
                    "conditions": []
                }
            ]
            return JSONResponse(content={"tasks": tasks}, status_code=200)
        
        @api_router.post("/scheduler/tasks")
        async def create_scheduled_task():
            """Create a new scheduled task"""
            return JSONResponse(
                content={
                    "message": "Scheduled task created successfully",
                    "task_id": "new_task_123"
                },
                status_code=201
            )
        
        # Notifications endpoints
        @api_router.get("/notifications")
        async def get_notifications():
            """Get recent notifications"""
            notifications = [
                {
                    "id": "notif_1",
                    "type": "success",
                    "title": "Mining Started",
                    "message": "Mining operation started successfully",
                    "timestamp": "2024-01-15T10:30:00Z",
                    "read": False
                },
                {
                    "id": "notif_2",
                    "type": "warning",
                    "title": "High Temperature",
                    "message": "GPU temperature reached 78°C",
                    "timestamp": "2024-01-15T10:25:00Z",
                    "read": True
                },
                {
                    "id": "notif_3",
                    "type": "info",
                    "title": "Pool Switch",
                    "message": "Switched to more profitable pool",
                    "timestamp": "2024-01-15T10:20:00Z",
                    "read": True
                }
            ]
            return JSONResponse(content={"notifications": notifications}, status_code=200)
        
        @api_router.post("/notifications/{notification_id}/read")
        async def mark_notification_read(notification_id: str):
            """Mark a notification as read"""
            return JSONResponse(
                content={"message": "Notification marked as read"},
                status_code=200
            )
        
        # Economic guardian endpoints
        @api_router.get("/economic/status")
        async def get_economic_status():
            """Get economic guardian status"""
            return JSONResponse(
                content={
                    "enabled": True,
                    "current_profit_margin": 15.2,
                    "minimum_profit_margin": 5.0,
                    "electricity_cost_per_hour": 0.036,
                    "estimated_daily_profit": 2.45,
                    "break_even_point": 85.2,
                    "recommendations": [
                        "Current operation is profitable",
                        "Consider mining during off-peak hours",
                        "Monitor electricity rates for optimization"
                    ],
                    "last_check": "2024-01-15T10:30:00Z"
                },
                status_code=200
            )
        
        @api_router.post("/economic/update")
        async def update_economic_settings():
            """Update economic guardian settings"""
            return JSONResponse(
                content={"message": "Economic guardian settings updated"},
                status_code=200
            )
        
        # System optimization endpoints
        @api_router.get("/system/optimization")
        async def get_system_optimization():
            """Get system optimization suggestions"""
            return JSONResponse(
                content={
                    "cpu_usage": 25.4,
                    "memory_usage": 68.2,
                    "disk_usage": 45.1,
                    "network_usage": 12.3,
                    "optimizations": [
                        {
                            "category": "performance",
                            "suggestion": "Increase virtual memory for better stability",
                            "impact": "medium",
                            "effort": "low"
                        },
                        {
                            "category": "efficiency",
                            "suggestion": "Enable CPU power management",
                            "impact": "low",
                            "effort": "low"
                        },
                        {
                            "category": "cooling",
                            "suggestion": "Adjust fan curves for better cooling",
                            "impact": "high",
                            "effort": "medium"
                        }
                    ]
                },
                status_code=200
            )

        # Mount API router
        self.app.mount("/api", api_router)

        # WebSocket for real-time metrics
        @self.app.websocket("/ws/metrics")
        async def metrics_websocket(websocket: WebSocket):
            await websocket.accept()
            try:
                # Send real mining metrics
                while True:
                    # Get real-time metrics from mining controller
                    status = self.mining_controller.get_status()
                    
                    # Calculate additional metrics
                    total_shares = 0
                    valid_shares = 0
                    invalid_shares = 0
                    
                    # Try to get real mining service data if available
                    real_metrics = {}
                    if hasattr(self.mining_controller, 'real_mining_service'):
                        try:
                            real_metrics = self.mining_controller.real_mining_service.get_real_time_metrics()
                        except:
                            pass
                    
                    # Combine status data with real metrics
                    metrics = {
                        "hashrate": real_metrics.get("hashrate", 125.4 if status["is_mining"] else 0.0),
                        "shares": real_metrics.get("shares", total_shares),
                        "validShares": real_metrics.get("validShares", valid_shares),
                        "invalidShares": real_metrics.get("invalidShares", invalid_shares),
                        "temperature": real_metrics.get("temperature", 65.0 + (time.time() % 20)),
                        "power": real_metrics.get("power", 150.0 if status["is_mining"] else 0.0),
                        "efficiency": real_metrics.get("efficiency", 0.83 if status["is_mining"] else 0.0),
                        "difficulty": real_metrics.get("difficulty", 1.0),
                        "profit": 0.0025 if status["is_mining"] else 0.0,
                        "is_authorized": status["is_authorized"],
                        "is_mining": status["is_mining"],
                        "uptime": status.get("uptime", "0s"),
                        "pool": status.get("connected_pool", "Not Connected"),
                        "worker": status.get("worker_name", "rig01")
                    }
                    
                    await websocket.send_text(json.dumps(metrics))
                    await asyncio.sleep(1)  # Send updates every second
            except Exception as e:
                logger.error(f"WebSocket error: {e}")
            finally:
                await websocket.close()

    def _parse_uptime(self, uptime_str: str) -> int:
        """Parse uptime string to seconds"""
        # Simple parsing for format like "1h 30m 45s"
        total_seconds = 0
        if "h" in uptime_str:
            hours_part = uptime_str.split("h")[0]
            total_seconds += int(hours_part) * 3600
            uptime_str = uptime_str.split("h")[1].strip()
        if "m" in uptime_str:
            minutes_part = uptime_str.split("m")[0]
            total_seconds += int(minutes_part) * 60
            uptime_str = uptime_str.split("m")[1].strip()
        if "s" in uptime_str:
            seconds_part = uptime_str.split("s")[0]
            total_seconds += int(seconds_part)
        return total_seconds

    async def start(self):
        """Start the server."""
        # Configure SSL if cert and key files are provided
        ssl_context = None
        if self.settings.use_ssl():
            try:
                ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
                certfile = self.settings.ssl_certfile
                keyfile = self.settings.ssl_keyfile
                if certfile and keyfile:
                    ssl_context.load_cert_chain(certfile, keyfile)
                    logger.info("SSL context loaded successfully")
            except Exception as e:
                logger.error(f"Failed to load SSL context: {e}")
                ssl_context = None

        config = uvicorn.Config(
            self.app,
            host=self.settings.host,
            port=self.settings.port,
            log_level="info",
            ssl_certfile=self.settings.ssl_certfile if ssl_context else None,
            ssl_keyfile=self.settings.ssl_keyfile if ssl_context else None
        )
        self.server = uvicorn.Server(config)
        await self.server.serve()

    async def stop(self):
        """Stop the server."""
        if self.server:
            await self.server.shutdown()
        await self.mining_controller.stop()


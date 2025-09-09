"""
Stratum protocol client for Mining OS.
Handles connection to mining pools and share submission.
"""
import json
import logging
import socket
import time
from collections.abc import Callable
from typing import Any

# Constants for time intervals
LOG_INTERVAL_SECONDS = 30
CONNECTION_TIMEOUT_SECONDS = 90

logger = logging.getLogger(__name__)


class StratumClient:
    def __init__(self, url: str, username: str, password: str):
        self.url = url
        self.username = username
        self.password = password
        self.host = ""
        self.port = 0
        self.socket: socket.socket | None = None
        self.is_connected = False
        self.is_authorized = False
        self.entrance1 = ""
        self.entrance2_size = 0
        self.target = ""
        self.job_id = ""
        self.prewash = ""
        self.coin1 = ""
        self.coin2 = ""
        self.merkle_branch = []
        self.version = ""
        self.nits = ""
        self.ntile = ""
        self.clean_jobs = False
        self.last_activity = 0.0
        self.message_id = 1
        self._parse_url()
        self._response_handlers: dict[int, Callable] = {}
        self._notification_handlers: dict[str, Callable] = {}
        self._last_log_time = 0  # Track last log time to prevent spam

    def _parse_url(self):
        """Parse the stratum URL into host and port."""
        try:
            # Remove stratum+tcp:// prefix
            if self.url.startswith("stratum+tcp://"):
                url_part = self.url[14:]
            else:
                url_part = self.url

            # Split host and port
            parts = url_part.split(":")
            self.host = parts[0]
            self.port = int(parts[1])
        except Exception as e:
            logger.error(f"Failed to parse URL {self.url}: {e}")

    async def connect(self, timeout: int = 30) -> bool:
        """Connect to the stratum server."""
        try:
            logger.info(f"Connecting to {self.host}:{self.port}")
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.settimeout(timeout)
            self.socket.connect((self.host, self.port))
            self.is_connected = True
            self.last_activity = time.time()
            logger.info(f"Connected to {self.host}:{self.port}")
            return True
        except Exception as e:
            logger.error(f"Failed to connect to {self.host}:{self.port}: {e}")
            self.is_connected = False
            return False

    async def disconnect(self):
        """Disconnect from the stratum server."""
        if self.socket:
            try:
                self.socket.close()
            except Exception as e:
                logger.error(f"Error closing socket: {e}")
            finally:
                self.socket = None
                self.is_connected = False
                self.is_authorized = False

    async def send_message(self, message: dict[str, Any]) -> bool:
        """Send a message to the stratum server."""
        if not self.is_connected or not self.socket:
            logger.error("Not connected to server")
            return False

        try:
            message_str = json.dumps(message) + "\n"
            self.socket.send(message_str.encode("utf-8"))
            self.last_activity = time.time()
            # Only log send messages every 30 seconds to prevent spam
            current_time = time.time()
            if current_time - self._last_log_time > LOG_INTERVAL_SECONDS:
                logger.debug(f"Sent: {message_str.strip()}")
                self._last_log_time = current_time
            return True
        except Exception as e:
            logger.error(f"Failed to send message: {e}")
            return False

    async def receive_message(self) -> dict[str, Any] | None:
        """Receive a message from the stratum server."""
        if not self.is_connected or not self.socket:
            logger.error("Not connected to server")
            return None

        try:
            # This is a simplified implementation
            # In a real implementation, you'd need to handle chunked responses
            response = self.socket.recv(4096)
            if response:
                self.last_activity = time.time()
                response_str = response.decode("utf-8")
                # Only log received messages every 30 seconds to prevent spam
                current_time = time.time()
                if current_time - self._last_log_time > LOG_INTERVAL_SECONDS:
                    logger.debug(f"Received: {response_str.strip()}")
                    self._last_log_time = current_time
                return json.loads(response_str)
            return None
        except Exception as e:
            logger.error(f"Failed to receive message: {e}")
            return None

    async def subscribe(self) -> bool:
        """Subscribe to the stratum server with proper format."""
        message = {
            "id": self.message_id,
            "method": "mining.subscribe",
            "params": ["custom-miner/1.0"]
        }

        if not await self.send_message(message):
            return False

        self.message_id += 1
        # In a real implementation, you'd wait for the response
        # and parse the entrance1, entrance2_size, and target
        self.entrance1 = "00000000"
        self.entrance2_size = 4
        return True

    async def authorize(self) -> bool:
        """Authorize with the stratum server with proper format."""
        message = {
            "id": self.message_id,
            "method": "mining.authorize",
            "params": [self.username, self.password]
        }

        if not await self.send_message(message):
            return False

        self.message_id += 1
        # In a real implementation, you'd wait for the response
        # and check if the authorization was successful
        self.is_authorized = True
        logger.info(f"Authorized as {self.username}")
        return True

    async def submit_share(
        self,
        job_id: str,
        entrance2: str,
        ntile: str,
        nonce: str
    ) -> bool:
        """Submit a share to the stratum server with correct format."""
        # Ensure we're using the same payout_address.worker_name format
        message = {
            "id": self.message_id,
            "method": "mining.submit",
            "params": [self.username, job_id, entrance2, ntile, nonce]
        }

        if not await self.send_message(message):
            return False

        self.message_id += 1
        # Only log share submissions every 30 seconds to prevent spam
        current_time = time.time()
        if current_time - self._last_log_time > LOG_INTERVAL_SECONDS:
            logger.info(
                f"Submitted share for job {job_id} "
                f"with user {self.username}"
            )
            self._last_log_time = current_time
        return True

    def is_alive(self) -> bool:
        """Check if the connection is still alive."""
        if not self.is_connected:
            return False

        # Check if we've received any messages recently
        return time.time() - self.last_activity < CONNECTION_TIMEOUT_SECONDS

    async def suggest_difficulty(self, difficulty: int) -> bool:
        """Suggest a difficulty to the pool."""
        message = {
            "id": self.message_id,
            "method": "mining.suggest_difficulty",
            "params": [difficulty]
        }

        if not await self.send_message(message):
            return False

        self.message_id += 1
        logger.info(f"Suggested difficulty {difficulty} to pool")
        return True



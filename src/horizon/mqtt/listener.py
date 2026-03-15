"""
MQTT listener for Frigate events.

Connects to MQTT broker and listens for license plate events published by Frigate.
"""

import asyncio
import json
import logging
from typing import Callable, Optional, Set
from datetime import datetime, timezone

try:
    import paho.mqtt.client as mqtt
except ImportError:
    mqtt = None
    raise ImportError("paho-mqtt is required. Install with: pip install paho-mqtt")

from webui.models.config import MQTTConfig

logger = logging.getLogger(__name__)


class FrigateMQTTListener:
    """
    Connects to Frigate MQTT broker and listens for license plate events.
    """

    def __init__(self, config: MQTTConfig):
        """
        Initialize the MQTT listener.

        Args:
            config: MQTT configuration
        """
        if mqtt is None:
            raise ImportError("paho-mqtt is required")

        self.config = config
        self.client: Optional[mqtt.Client] = None
        self.connected: bool = False
        self.message_callback: Optional[Callable] = None

        # Store the event loop for thread-safe callbacks
        self.event_loop: Optional[asyncio.AbstractEventLoop] = None

        # Statistics
        self.messages_received: int = 0
        self.messages_processed: int = 0
        self.messages_ignored: int = 0
        self.last_message_at: Optional[datetime] = None
        self.last_error: Optional[str] = None

        # Camera discovery
        self.detected_cameras: Set[str] = set()

    def _create_client(self) -> mqtt.Client:
        """Create and configure MQTT client."""
        # Create client with callback API version
        client = mqtt.Client(
            client_id=self.config.client_id,
            callback_api_version=mqtt.CallbackAPIVersion.VERSION2
        )

        # Set callbacks
        client.on_connect = self._on_connect
        client.on_disconnect = self._on_disconnect
        client.on_message = self._on_message

        # Set credentials if provided
        if self.config.username and self.config.password:
            client.username_pw_set(
                self.config.username,
                self.config.password
            )

        # Set QoS
        if self.config.qos not in (0, 1, 2):
            logger.warning(f"Invalid QoS {self.config.qos}, using 1")
            self.config.qos = 1

        # Enable automatic reconnect with exponential backoff
        # This helps recover from network interruptions (e.g., macOS sleep)
        client.reconnect_delay_set(
            min_delay=1,    # Start with 1 second
            max_delay=60    # Cap at 60 seconds between retries
        )

        return client

    def _on_connect(self, client, userdata, flags, reason_code, properties):
        """Called when client connects to broker."""
        if reason_code == 0:
            self.connected = True
            logger.info(f"MQTT connected to {self.config.broker_host}:{self.config.broker_port}")

            # Subscribe to tracked_object_update topic
            topic = f"{self.config.topic_prefix}/tracked_object_update"
            client.subscribe(topic, qos=self.config.qos)
            logger.info(f"Subscribed to topic: {topic}")
        else:
            self.connected = False
            self.last_error = f"Connection failed with code {reason_code}"
            logger.error(f"MQTT connection failed: {reason_code}")

    def _on_disconnect(self, client, userdata, reason_code, *args):
        """Called when client disconnects from broker."""
        self.connected = False
        if reason_code != 0:
            logger.warning(f"MQTT disconnected: {reason_code}")
            self.last_error = f"Disconnected: {reason_code}"
        else:
            logger.info("MQTT disconnected cleanly")

    def _on_message(self, client, userdata, msg):
        """Called when message is received (runs in paho-mqtt thread)."""
        self.messages_received += 1
        self.last_message_at = datetime.now(timezone.utc)

        try:
            # Parse payload
            payload = json.loads(msg.payload.decode())

            # Camera is now in the payload
            camera = payload.get('camera', 'unknown')
            self.detected_cameras.add(camera)

            # Check if should process camera
            if not self._should_process_camera(camera):
                self.messages_ignored += 1
                logger.debug(f"Ignored message from camera: {camera}")
                return

            # Call message callback if registered (thread-safe)
            if self.message_callback and self.event_loop:
                asyncio.run_coroutine_threadsafe(
                    self.message_callback(payload),
                    self.event_loop
                )
                self.messages_processed += 1

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse MQTT message: {e}")
            self.last_error = f"JSON decode error: {e}"
        except Exception as e:
            logger.error(f"Error processing MQTT message: {e}")
            self.last_error = str(e)

    def _should_process_camera(self, camera: str) -> bool:
        """
        Check if camera should be processed based on filter settings.

        Args:
            camera: Camera name

        Returns:
            True if camera should be processed
        """
        if not self.config.enabled_cameras:
            # Empty list = process all cameras
            return True

        if self.config.enabled_cameras_mode == "whitelist":
            return camera in self.config.enabled_cameras
        else:  # blacklist
            return camera not in self.config.enabled_cameras

    async def connect(self) -> bool:
        """
        Connect to MQTT broker.

        Returns:
            True if connected successfully
        """
        try:
            # Store the current event loop for thread-safe callbacks
            self.event_loop = asyncio.get_running_loop()

            self.client = self._create_client()

            logger.info(f"Connecting to MQTT broker at {self.config.broker_host}:{self.config.broker_port}...")
            self.client.connect(
                self.config.broker_host,
                self.config.broker_port,
                keepalive=60
            )

            # Start network loop in background
            self.client.loop_start()

            # Wait for connection
            for _ in range(self.config.connection_timeout):
                await asyncio.sleep(1)
                if self.connected:
                    return True

            self.last_error = "Connection timeout"
            logger.error("MQTT connection timeout")
            return False

        except Exception as e:
            self.last_error = str(e)
            logger.error(f"Failed to connect to MQTT broker: {e}")
            return False

    async def disconnect(self) -> None:
        """Disconnect from MQTT broker."""
        if self.client:
            self.client.loop_stop()
            self.client.disconnect()
            self.connected = False
            logger.info("MQTT disconnected")

    def is_connected(self) -> bool:
        """Check if currently connected."""
        return self.connected

    def get_stats(self) -> dict:
        """
        Get listener statistics.

        Returns:
            Dictionary with statistics
        """
        return {
            "connected": self.connected,
            "messages_received": self.messages_received,
            "messages_processed": self.messages_processed,
            "messages_ignored": self.messages_ignored,
            "last_message_at": self.last_message_at.isoformat() if self.last_message_at else None,
            "last_error": self.last_error,
            "detected_cameras": list(self.detected_cameras)
        }

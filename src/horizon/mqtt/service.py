"""
MQTT service for Frigate integration.

Manages the MQTT listener, processor, and lifecycle for real-time
license plate detection.
"""

import asyncio
import logging
from datetime import datetime
from typing import Optional

from webui.models.config import MQTTConfig, PatternDetectionConfig
from horizon.mqtt.listener import FrigateMQTTListener
from horizon.mqtt.processor import MQTTProcessor
from horizon.mqtt.deduplicator import EventDeduplicator
from horizon.mqtt.profile_manager import ProfileManager
from horizon.mqtt.event_logger import EventLogger, get_event_logger
from horizon.processor import PROFILES_FILE

logger = logging.getLogger(__name__)


class MQTTService:
    """
    Manages MQTT listener lifecycle and integration with processor.

    Uses an internal message queue to decouple event reception from processing,
    allowing the system to handle traffic bursts without dropping messages.
    """

    def __init__(
        self,
        mqtt_config: MQTTConfig,
        pattern_config: PatternDetectionConfig,
        profiles_path: Optional[str] = None,
        queue_size: int = 10000
    ):
        """
        Initialize the MQTT service.

        Args:
            mqtt_config: MQTT configuration
            pattern_config: Pattern detection configuration
            profiles_path: Path to profiles file (optional)
            queue_size: Maximum number of events to queue (default: 10000)
        """
        self.config = mqtt_config
        self.pattern_config = pattern_config
        self.queue_size = queue_size

        # Use default path if not provided
        if profiles_path is None:
            profiles_path = PROFILES_FILE

        # Initialize components
        self.deduplicator = EventDeduplicator()
        self.profile_manager = ProfileManager(profiles_path)
        self.listener = FrigateMQTTListener(mqtt_config)
        self.event_logger = get_event_logger()
        self.processor = MQTTProcessor(
            mqtt_config,
            pattern_config,
            self.profile_manager,
            self.deduplicator,
            self.event_logger
        )

        # Message queue for decoupling reception from processing
        self.event_queue: asyncio.Queue = asyncio.Queue(maxsize=queue_size)

        # Queue statistics
        self._queue_full_count: int = 0
        self._queue_peak_size: int = 0

        # State
        self.running: bool = False
        self.started_at: Optional[datetime] = None
        self.connect_task: Optional[asyncio.Task] = None
        self.processor_task: Optional[asyncio.Task] = None

        # Register message callback
        self.listener.message_callback = self._enqueue_message

    async def start(self) -> bool:
        """
        Start the MQTT service.

        Returns:
            True if started successfully
        """
        if self.running:
            logger.warning("MQTT service is already running")
            return True

        logger.info("Starting MQTT service...")

        # Connect to broker
        connected = await self.listener.connect()
        if not connected:
            logger.error("Failed to connect to MQTT broker")
            return False

        self.running = True
        self.started_at = datetime.now()

        # Start connection monitor
        self.connect_task = asyncio.create_task(self._monitor_connection())

        # Start event queue processor
        self.processor_task = asyncio.create_task(self._process_queue())

        logger.info("MQTT service started successfully")
        return True

    async def stop(self) -> None:
        """
        Stop the MQTT service.
        """
        if not self.running:
            return

        logger.info("Stopping MQTT service...")

        self.running = False

        # Cancel processor task first to stop processing
        if self.processor_task:
            self.processor_task.cancel()
            try:
                await self.processor_task
            except asyncio.CancelledError:
                pass

        # Cancel monitor task
        if self.connect_task:
            self.connect_task.cancel()
            try:
                await self.connect_task
            except asyncio.CancelledError:
                pass

        # Wait for queue to drain (with timeout)
        try:
            await asyncio.wait_for(self._drain_queue(), timeout=5.0)
        except asyncio.TimeoutError:
            remaining = self.event_queue.qsize()
            logger.warning(f"Queue drain timeout, {remaining} events will not be processed")

        # Force save profiles
        await self.profile_manager.force_save()

        # Disconnect
        await self.listener.disconnect()

        logger.info("MQTT service stopped")

    async def _monitor_connection(self) -> None:
        """
        Monitor MQTT connection and attempt reconnection if lost.

        Implements exponential backoff and will keep retrying indefinitely
        to handle network interruptions (e.g., macOS sleep, WiFi reconnects).
        """
        retry_count = 0

        while self.running:
            await asyncio.sleep(5)

            if not self.listener.is_connected():
                logger.warning("MQTT connection lost, attempting to reconnect...")

                # Keep trying to reconnect indefinitely (not limited by max_retries)
                while self.running and not self.listener.is_connected():
                    if not self.running:
                        return

                    connected = await self.listener.connect()
                    if connected:
                        logger.info("MQTT reconnected successfully")
                        retry_count = 0  # Reset retry count on success
                        break

                    retry_count += 1

                    # Exponential backoff: wait longer between retries
                    # Start at retry_interval, cap at 60 seconds
                    backoff = min(
                        self.config.retry_interval * (1.5 ** (retry_count // 3)),
                        60
                    )

                    logger.warning(
                        f"Reconnection attempt {retry_count} failed. "
                        f"Retrying in {backoff:.1f} seconds..."
                    )
                    await asyncio.sleep(backoff)

    async def _enqueue_message(self, payload: dict) -> None:
        """
        Enqueue incoming MQTT message for processing.

        This is called from the MQTT listener callback (runs in paho-mqtt thread)
        and puts the event into the queue for later processing.

        Args:
            payload: Message payload from Frigate
        """
        try:
            # Try to put in queue without blocking
            self.event_queue.put_nowait(payload)

            # Update peak size statistic
            current_size = self.event_queue.qsize()
            if current_size > self._queue_peak_size:
                self._queue_peak_size = current_size

        except asyncio.QueueFull:
            self._queue_full_count += 1
            logger.error(f"Event queue full! Dropping message. Total drops: {self._queue_full_count}")

    async def _process_queue(self) -> None:
        """
        Background task that processes events from the queue.

        Runs continuously while the service is running, pulling events
        from the queue and processing them through the processor.
        """
        logger.info("Event queue processor started")

        while self.running:
            try:
                # Wait for event with timeout to allow checking running state
                payload = await asyncio.wait_for(
                    self.event_queue.get(),
                    timeout=1.0
                )

                # Process the event
                try:
                    plate = await self.processor.process_message(payload)
                    if plate:
                        logger.debug(f"Successfully processed reading for {plate}")
                except Exception as e:
                    logger.error(f"Error processing event from queue: {e}")

            except asyncio.TimeoutError:
                # Normal timeout, just continue
                continue
            except Exception as e:
                if self.running:
                    logger.error(f"Unexpected error in queue processor: {e}")
                # Don't break the loop, try to continue

        logger.info("Event queue processor stopped")

    async def _drain_queue(self) -> None:
        """
        Drain remaining events from the queue during shutdown.

        Processes all remaining events in the queue before shutdown.
        """
        queue_size = self.event_queue.qsize()
        if queue_size == 0:
            return

        logger.info(f"Draining {queue_size} remaining events from queue...")

        processed = 0
        while not self.event_queue.empty():
            try:
                payload = self.event_queue.get_nowait()
                await self.processor.process_message(payload)
                processed += 1

                # Log progress every 100 events
                if processed % 100 == 0:
                    remaining = self.event_queue.qsize()
                    logger.info(f"Drain progress: {processed} processed, {remaining} remaining")

            except Exception as e:
                logger.error(f"Error draining queue: {e}")

        logger.info(f"Queue drain complete: {processed} events processed")

    def uptime_seconds(self) -> Optional[int]:
        """
        Get service uptime in seconds.

        Returns:
            Uptime in seconds or None if not started
        """
        if self.started_at is None:
            return None

        return int((datetime.now() - self.started_at).total_seconds())

    def get_status(self) -> dict:
        """
        Get comprehensive service status.

        Returns:
            Dictionary with status information
        """
        listener_stats = self.listener.get_stats()
        processor_stats = self.processor.get_stats()
        deduplicator_stats = self.deduplicator.get_stats()
        profile_stats = self.profile_manager.get_stats()
        event_logger_stats = self.event_logger.get_stats()

        return {
            'running': self.running,
            'enabled': self.config.enabled,
            'uptime_seconds': self.uptime_seconds(),
            'started_at': self.started_at.isoformat() if self.started_at else None,
            'listener': listener_stats,
            'processor': processor_stats,
            'deduplicator': deduplicator_stats,
            'profiles': profile_stats,
            'event_logger': event_logger_stats,
            'queue': {
                'size': self.event_queue.qsize(),
                'max_size': self.queue_size,
                'utilization_percent': round(
                    (self.event_queue.qsize() / self.queue_size) * 100, 2
                ),
                'peak_size': self._queue_peak_size,
                'drops': self._queue_full_count
            }
        }

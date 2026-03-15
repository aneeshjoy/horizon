"""
MQTT integration for Frigate.

This package provides real-time license plate detection via MQTT.
"""

from horizon.mqtt.service import MQTTService
from horizon.mqtt.listener import FrigateMQTTListener
from horizon.mqtt.processor import MQTTProcessor
from horizon.mqtt.deduplicator import EventDeduplicator
from horizon.mqtt.profile_manager import ProfileManager
from horizon.mqtt.event_logger import EventLogger, get_event_logger

__all__ = [
    'MQTTService',
    'FrigateMQTTListener',
    'MQTTProcessor',
    'EventDeduplicator',
    'ProfileManager',
    'EventLogger',
    'get_event_logger'
]

"""
Status and monitoring API endpoints
"""

from fastapi import APIRouter, Request
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

router = APIRouter(prefix="/api/status", tags=["status"])


class MQTTStatus(BaseModel):
    """MQTT service status"""
    enabled: bool
    connected: bool
    running: bool
    broker_host: str
    broker_port: int
    client_id: str
    uptime_seconds: Optional[int]
    messages_received: int
    messages_processed: int
    messages_ignored: int
    last_message_at: Optional[str]
    error_message: Optional[str]
    detected_cameras: List[str]
    stats: dict
    queue: Optional[dict] = None  # Queue statistics (may be None if service not running)


@router.get("/mqtt", response_model=MQTTStatus)
async def get_mqtt_status(request: Request) -> MQTTStatus:
    """
    Get MQTT connection and service status.

    Returns comprehensive status information about the MQTT integration
    including connection state, message statistics, and detected cameras.
    """
    app = request.app

    # Check if service is running
    mqtt_service = getattr(app.state, 'mqtt_service', None)

    if not mqtt_service:
        return MQTTStatus(
            enabled=False,
            connected=False,
            running=False,
            broker_host="",
            broker_port=0,
            client_id="",
            uptime_seconds=None,
            messages_received=0,
            messages_processed=0,
            messages_ignored=0,
            last_message_at=None,
            error_message=None,
            detected_cameras=[],
            stats={}
        )

    service = mqtt_service
    status = service.get_status()

    # Extract listener stats
    listener = status.get('listener', {})

    return MQTTStatus(
        enabled=status.get('enabled', False),
        connected=listener.get('connected', False),
        running=status.get('running', False),
        broker_host=service.config.broker_host,
        broker_port=service.config.broker_port,
        client_id=service.config.client_id,
        uptime_seconds=status.get('uptime_seconds'),
        messages_received=listener.get('messages_received', 0),
        messages_processed=listener.get('messages_processed', 0),
        messages_ignored=listener.get('messages_ignored', 0),
        last_message_at=listener.get('last_message_at'),
        error_message=listener.get('last_error'),
        detected_cameras=listener.get('detected_cameras', []),
        stats={
            'processor': status.get('processor', {}),
            'deduplicator': status.get('deduplicator', {}),
            'profiles': status.get('profiles', {}),
            'event_logger': status.get('event_logger', {}),
            'queue': status.get('queue', {})
        },
        queue=status.get('queue')
    )


@router.get("/cameras")
async def get_available_cameras(request: Request) -> List[str]:
    """
    Get list of cameras detected via MQTT.

    Returns a list of camera names that have been detected in MQTT messages.
    """
    app = request.app

    if not hasattr(app.state, 'mqtt_service'):
        return []

    service = app.state.mqtt_service
    status = service.get_status()
    return status.get('listener', {}).get('detected_cameras', [])


@router.get("/health")
async def health_check(request: Request) -> dict:
    """
    Health check endpoint.

    Returns overall system health including MQTT status.
    """
    app = request.app

    mqtt_status = "disabled"
    if hasattr(app.state, 'mqtt_service'):
        service = app.state.mqtt_service
        listener_status = service.get_status().get('listener', {})
        if listener_status.get('connected'):
            mqtt_status = "connected"
        elif service.running:
            mqtt_status = "disconnected"

    return {
        "status": "healthy",
        "mqtt": mqtt_status,
        "timestamp": datetime.utcnow().isoformat()
    }

"""
Service layer for Horizon Web UI
"""

from src.webui.services.vehicle_service import VehicleService, get_vehicle_service
from src.webui.services.config_service import (
    ConfigService,
    get_config_service,
)

__all__ = [
    "VehicleService",
    "get_vehicle_service",
    "ConfigService",
    "get_config_service",
]

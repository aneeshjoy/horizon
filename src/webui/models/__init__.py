"""
Pydantic models for the Horizon Web UI API
"""

from src.webui.models.vehicle import (
    SightingPattern,
    VehicleSummary,
    VehicleListItem,
)
from src.webui.models.grid import (
    GridCell,
    GridRow,
    PatternGrid,
)
from src.webui.models.config import (
    ClassificationColorScheme,
    PatternDetectionConfig,
    ClassificationConfig,
    DisplayConfig,
    SystemConfig,
    ConfigValidationResult,
)

__all__ = [
    # Vehicle models
    "SightingPattern",
    "VehicleSummary",
    "VehicleListItem",
    # Grid models
    "GridCell",
    "GridRow",
    "PatternGrid",
    # Config models
    "ClassificationColorScheme",
    "PatternDetectionConfig",
    "ClassificationConfig",
    "DisplayConfig",
    "SystemConfig",
    "ConfigValidationResult",
]

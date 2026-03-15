"""
Configuration management models
"""

from pydantic import BaseModel, Field, validator
from typing import List, Optional, Literal
from enum import Enum
from datetime import datetime


class ClassificationColorScheme(str, Enum):
    """Predefined color schemes for classifications"""
    MODERN = "modern"  # Teal/Blue/Purple
    TRAFFIC = "traffic"  # Green/Yellow/Red
    NEUTRAL = "neutral"  # Grays with accent colors


class PatternDetectionConfig(BaseModel):
    """Pattern detection algorithm parameters"""
    bucket_tolerance_minutes: int = Field(
        default=45,
        ge=15,
        le=180,
        description="Time tolerance for matching readings to same bucket (minutes)"
    )
    min_pattern_samples: int = Field(
        default=3,
        ge=2,
        le=10,
        description="Minimum readings required to form a pattern"
    )
    confidence_threshold: float = Field(
        default=0.65,
        ge=0.0,
        le=1.0,
        description="Minimum confidence score to accept a reading"
    )
    ocr_similarity_threshold: float = Field(
        default=0.85,
        ge=0.5,
        le=1.0,
        description="Similarity score for OCR fuzzy matching"
    )


class ClassificationConfig(BaseModel):
    """Vehicle classification parameters"""
    commuter_threshold: int = Field(
        default=80,
        ge=0,
        le=100,
        description="Minimum RDS score for Commuter classification"
    )
    unknown_threshold: int = Field(
        default=60,
        ge=0,
        le=100,
        description="Minimum RDS score for Unknown classification"
    )
    pattern_adherence_weight: float = Field(
        default=0.40,
        ge=0.0,
        le=1.0,
        description="Weight of pattern adherence in RDS calculation"
    )
    confidence_stability_weight: float = Field(
        default=0.30,
        ge=0.0,
        le=1.0,
        description="Weight of confidence stability in RDS calculation"
    )
    pattern_concentration_weight: float = Field(
        default=0.30,
        ge=0.0,
        le=1.0,
        description="Weight of pattern concentration in RDS calculation"
    )

    @validator('commuter_threshold')
    def commuter_greater_than_unknown(cls, v, values):
        """Ensure commuter threshold is greater than unknown threshold"""
        if 'unknown_threshold' in values and v <= values['unknown_threshold']:
            raise ValueError('Commuter threshold must be greater than Unknown threshold')
        return v


class DisplayConfig(BaseModel):
    """UI display and visualization parameters"""
    grid_time_granularity_minutes: int = Field(
        default=45,
        ge=15,
        le=120,
        description="Minutes per grid row (time bucket size)"
    )
    auto_refresh_interval_seconds: int = Field(
        default=0,
        ge=0,
        le=600,
        description="Auto-refresh interval (0 = disabled)"
    )


class ImportConfig(BaseModel):
    """Data import settings for Frigate database"""
    auto_import_on_startup: bool = Field(
        default=False,
        description="Automatically import from Frigate DB on startup"
    )
    auto_rebuild_after_import: bool = Field(
        default=True,
        description="Automatically rebuild profiles after successful import"
    )
    import_db_path: str = Field(
        default="data/external/frigate.db",
        description="Path to Frigate database file for import"
    )
    import_after_date: Optional[str] = Field(
        default=None,
        description="Only import events after this date (ISO format YYYY-MM-DD)"
    )


class MQTTConfig(BaseModel):
    """MQTT integration for Frigate"""
    enabled: bool = Field(
        default=False,
        description="Enable MQTT integration"
    )
    broker_host: str = Field(
        default="localhost",
        description="MQTT broker hostname or IP"
    )
    broker_port: int = Field(
        default=1883,
        ge=1,
        le=65535,
        description="MQTT broker port"
    )
    username: Optional[str] = Field(
        default=None,
        description="MQTT username (if authentication required)"
    )
    password: Optional[str] = Field(
        default=None,
        description="MQTT password (if authentication required)"
    )
    client_id: str = Field(
        default="horizon-lpr",
        description="MQTT client ID"
    )
    topic_prefix: str = Field(
        default="frigate",
        description="MQTT topic prefix for Frigate events"
    )
    qos: int = Field(
        default=1,
        ge=0,
        le=2,
        description="MQTT Quality of Service level"
    )
    retry_interval: int = Field(
        default=5,
        ge=1,
        le=60,
        description="Seconds between reconnection attempts"
    )
    max_retries: int = Field(
        default=10,
        ge=1,
        le=100,
        description="Maximum reconnection attempts before backoff"
    )
    connection_timeout: int = Field(
        default=30,
        ge=5,
        le=120,
        description="Seconds to wait for connection"
    )
    timezone: str = Field(
        default="America/Los_Angeles",
        description="Local timezone for timestamp conversion"
    )
    enabled_cameras: List[str] = Field(
        default_factory=list,
        description="List of cameras to monitor (empty = all cameras)"
    )
    enabled_cameras_mode: Literal["whitelist", "blacklist"] = Field(
        default="whitelist",
        description="Camera filter mode: whitelist or blacklist"
    )


class SystemConfig(BaseModel):
    """Complete system configuration"""
    mqtt: MQTTConfig = Field(default_factory=MQTTConfig)
    pattern_detection: PatternDetectionConfig = Field(default_factory=PatternDetectionConfig)
    classification: ClassificationConfig = Field(default_factory=ClassificationConfig)
    display: DisplayConfig = Field(default_factory=DisplayConfig)
    import_config: ImportConfig = Field(default_factory=ImportConfig)

    class Config:
        json_schema_extra = {
            "example": {
                "pattern_detection": {
                    "bucket_tolerance_minutes": 45,
                    "min_pattern_samples": 3,
                    "confidence_threshold": 0.65,
                    "ocr_similarity_threshold": 0.85
                },
                "classification": {
                    "commuter_threshold": 80,
                    "unknown_threshold": 60,
                    "pattern_adherence_weight": 0.40,
                    "confidence_stability_weight": 0.30,
                    "pattern_concentration_weight": 0.30
                },
                "display": {
                    "grid_time_granularity_minutes": 45,
                    "auto_refresh_interval_seconds": 0
                }
            }
        }


class ConfigValidationResult(BaseModel):
    """Result of configuration validation"""
    is_valid: bool = Field(..., description="Whether configuration is valid")
    errors: List[str] = Field(default_factory=list, description="Validation error messages")
    warnings: List[str] = Field(default_factory=list, description="Validation warning messages")


class ReprocessStatus(BaseModel):
    """Status of profile reprocessing job"""
    job_id: str = Field(..., description="Unique job identifier")
    status: str = Field(..., description="Job status: pending, running, completed, failed, cancelled")
    progress: float = Field(..., ge=0.0, le=1.0, description="Progress (0.0 to 1.0)")
    total_vehicles: int = Field(..., ge=0, description="Total vehicles to process")
    processed_vehicles: int = Field(..., ge=0, description="Number of vehicles processed")
    started_at: Optional[datetime] = Field(None, description="Job start timestamp")
    completed_at: Optional[datetime] = Field(None, description="Job completion timestamp")
    error_message: Optional[str] = Field(None, description="Error message if failed")


class ImportStatus(BaseModel):
    """Status of Frigate database import"""
    job_id: str = Field(..., description="Unique job identifier")
    status: str = Field(..., description="Job status: pending, running, completed, failed, cancelled")
    progress: float = Field(..., ge=0.0, le=1.0, description="Progress (0.0 to 1.0)")
    total_events: int = Field(..., ge=0, description="Total events to import")
    processed_events: int = Field(..., ge=0, description="Number of events processed")
    filtered_events: int = Field(..., ge=0, description="Events filtered (low confidence, etc)")
    plates_created: int = Field(..., ge=0, description="New plates added")
    started_at: Optional[datetime] = Field(None, description="Job start timestamp")
    completed_at: Optional[datetime] = Field(None, description="Job completion timestamp")
    error_message: Optional[str] = Field(None, description="Error message if failed")
    db_path: str = Field(..., description="Path to Frigate database being imported")
    db_size_mb: float = Field(..., ge=0, description="Database file size in MB")
    rebuild_triggered: bool = Field(default=False, description="Whether profile rebuild was triggered after import")

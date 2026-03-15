"""
Vehicle-related Pydantic models
"""

from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime


class SightingPattern(BaseModel):
    """Individual pattern bucket"""
    pattern_id: int = Field(..., description="Pattern identifier")
    time: str = Field(..., description="Time in HH:MM format")
    days: List[str] = Field(..., description="Days of week (e.g., ['Mon', 'Tue'])")
    sightings: int = Field(..., ge=0, description="Number of sightings in this pattern")
    avg_confidence: float = Field(..., ge=0.0, le=1.0, description="Average detection confidence")
    time_minutes: int = Field(..., ge=0, le=1439, description="Minutes from midnight")


class VehicleSummary(BaseModel):
    """Complete vehicle analytics summary"""
    plate: str = Field(..., description="License plate number")
    total_readings: int = Field(..., ge=0, description="Total number of sightings")
    first_seen: datetime = Field(..., description="First sighting timestamp")
    last_seen: datetime = Field(..., description="Last sighting timestamp")
    patterns: List[SightingPattern] = Field(default_factory=list, description="Identified patterns")
    pending_readings: int = Field(..., ge=0, description="Unclassified readings")
    classification: str = Field(..., description="Vehicle classification: Commuter, Unknown, or Suspicious")
    routine_deviation_score: int = Field(..., ge=0, le=100, description="RDS score (0-100)")
    confidence_score: float = Field(..., ge=0.0, le=1.0, description="Overall detection confidence")


class VehicleListItem(BaseModel):
    """Lightweight vehicle list item for search results"""
    plate: str = Field(..., description="License plate number")
    total_readings: int = Field(..., ge=0, description="Total number of sightings")
    classification: str = Field(..., description="Vehicle classification")
    last_seen: datetime = Field(..., description="Last sighting timestamp")
    pattern_count: int = Field(..., ge=0, description="Number of identified patterns")

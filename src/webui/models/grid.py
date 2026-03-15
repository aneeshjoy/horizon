"""
Pattern grid visualization models
"""

from pydantic import BaseModel, Field
from typing import List


class GridCell(BaseModel):
    """Individual grid cell data"""
    day: int = Field(..., ge=0, le=6, description="Day of week (0=Monday, 6=Sunday)")
    time_slot: int = Field(..., ge=0, description="Time slot index")
    count: int = Field(..., ge=0, description="Number of sightings in this cell")
    avg_confidence: float = Field(..., ge=0.0, le=1.0, description="Average confidence for cell")
    pattern_ids: List[int] = Field(default_factory=list, description="Associated pattern IDs")


class GridRow(BaseModel):
    """Row in the pattern grid (time slot)"""
    time_slot: int = Field(..., ge=0, description="Time slot index")
    time_label: str = Field(..., description="Time label (e.g., '00:00', '00:45')")
    cells: List[GridCell] = Field(..., min_length=7, max_length=7, description="7 cells (one per day)")


class PatternGrid(BaseModel):
    """Complete pattern grid data for visualization"""
    vehicle_plate: str = Field(..., description="License plate number")
    rows: List[GridRow] = Field(..., description="Grid rows (time slots)")
    max_count: int = Field(..., ge=0, description="Maximum count for scaling")
    total_patterns: int = Field(..., ge=0, description="Total number of patterns")

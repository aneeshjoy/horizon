"""
Horizon - License Plate Pattern Analysis System

A system for analyzing vehicle movement patterns from license plate
recognition data, with integration for Frigate NVR.
"""

__version__ = "0.1.0"

from .processor import (
    process_reading,
    load_profiles,
    save_profiles,
    get_vehicle_summary,
    similarity_score,
    correct_ocr_error,
)

from .analysis import (
    analyze_plate_pattern,
    classify_vehicle,
    calculate_routine_deviation_score,
)

__all__ = [
    "process_reading",
    "load_profiles",
    "save_profiles",
    "get_vehicle_summary",
    "similarity_score",
    "correct_ocr_error",
    "analyze_plate_pattern",
    "classify_vehicle",
    "calculate_routine_deviation_score",
]

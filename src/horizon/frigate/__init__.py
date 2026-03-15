"""
Frigate integration module for Horizon.

Provides database extraction capabilities for Frigate NVR
license plate detection data.
"""

from .extractor import (
    query_frigate_plates,
    export_to_jsonl,
)

from .inspector import (
    inspect_frigate_db,
    safe_copy_database,
    check_license_plate_data,
)

__all__ = [
    "query_frigate_plates",
    "export_to_jsonl",
    "inspect_frigate_db",
    "safe_copy_database",
    "check_license_plate_data",
]

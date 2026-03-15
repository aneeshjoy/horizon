"""
Vehicle API endpoints
"""

from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional

from src.webui.models.vehicle import VehicleSummary, VehicleListItem
from src.webui.models.grid import PatternGrid
from src.webui.services.vehicle_service import get_vehicle_service


router = APIRouter(prefix="/api/vehicles", tags=["vehicles"])


@router.get("/{plate}", response_model=VehicleSummary)
async def get_vehicle_summary(
    plate: str,
    fuzzy: bool = Query(False, description="Enable fuzzy matching")
):
    """Get complete analytics summary for a vehicle"""
    service = get_vehicle_service()
    result = service.get_vehicle_summary(plate, fuzzy=fuzzy)

    if not result:
        raise HTTPException(status_code=404, detail=f"Vehicle {plate} not found")

    return result


@router.get("/{plate}/grid", response_model=PatternGrid)
async def get_vehicle_grid(
    plate: str,
    fuzzy: bool = Query(False, description="Enable fuzzy matching")
):
    """Get pattern grid data for visualization"""
    service = get_vehicle_service()
    result = service.get_pattern_grid(plate, fuzzy=fuzzy)

    if not result:
        raise HTTPException(status_code=404, detail=f"Vehicle {plate} not found")

    return result


@router.get("", response_model=List[VehicleListItem])
async def list_vehicles(
    limit: int = Query(50, ge=1, le=500),
    offset: int = Query(0, ge=0),
    classification: Optional[str] = Query(None, description="Filter by classification"),
    sort_by: str = Query("last_seen", pattern="^(last_seen|total_readings|plate)$")
):
    """List all vehicles with pagination and filters"""
    service = get_vehicle_service()
    return service.list_vehicles(
        limit=limit,
        offset=offset,
        classification=classification,
        sort_by=sort_by
    )

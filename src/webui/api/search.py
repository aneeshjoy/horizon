"""
Search API endpoints
"""

from fastapi import APIRouter, Query
from typing import List

from src.webui.models.vehicle import VehicleListItem
from src.webui.services.vehicle_service import get_vehicle_service


router = APIRouter(prefix="/api/search", tags=["search"])


@router.get("")
async def search_vehicles(
    q: str = Query(..., description="Search query (plate number)"),
    limit: int = Query(10, ge=1, le=50, description="Maximum results to return")
) -> List[VehicleListItem]:
    """
    Search for vehicles by plate number

    Supports exact matches and fuzzy matching for
    partial or misspelled plate numbers.
    """
    service = get_vehicle_service()
    return service.search_vehicles(q, limit=limit)

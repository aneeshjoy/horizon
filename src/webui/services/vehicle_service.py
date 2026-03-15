"""
Vehicle analysis and data service
"""

from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple
import statistics

from src.horizon.processor import load_profiles, get_vehicle_summary, minutes_from_midnight
from src.horizon.analysis import calculate_routine_deviation_score, classify_vehicle
from src.webui.models.vehicle import VehicleSummary, VehicleListItem, SightingPattern
from src.webui.models.grid import PatternGrid, GridRow, GridCell


class VehicleService:
    """Service for vehicle data and analysis"""

    def __init__(self):
        self.day_names = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]

    def get_vehicle_summary(self, plate: str, fuzzy: bool = False) -> Optional[VehicleSummary]:
        """
        Get complete analytics summary for a vehicle
        """
        profiles = load_profiles()

        # Try exact match first
        if plate in profiles:
            return self._build_summary(plate, profiles[plate])

        # Try fuzzy matching if requested
        if fuzzy:
            from difflib import SequenceMatcher
            best_match = None
            best_score = 0

            for stored_plate in profiles.keys():
                score = SequenceMatcher(None, plate, stored_plate).ratio()
                if score > best_score:
                    best_score = score
                    best_match = stored_plate

            if best_score >= 0.85 and best_match:
                return self._build_summary(best_match, profiles[best_match])

        return None

    def _build_summary(self, plate: str, profile: dict) -> VehicleSummary:
        """Build VehicleSummary from profile data"""
        patterns = []
        for i, bucket in enumerate(profile.get('buckets', [])):
            avg_hour = bucket['avg_minutes'] // 60
            avg_min = bucket['avg_minutes'] % 60
            days_str = ", ".join([self.day_names[d] for d in bucket.get('days_seen', [])])
            avg_conf = sum(bucket.get('confidence_scores', [0])) / max(1, len(bucket.get('confidence_scores', [])))

            patterns.append(SightingPattern(
                pattern_id=i,
                time=f"{avg_hour:02d}:{avg_min:02d}",
                days=days_str.split(", "),
                sightings=bucket.get('count', 0),
                avg_confidence=round(avg_conf, 3),
                time_minutes=bucket.get('avg_minutes', 0)
            ))

        # Get classification
        summary = get_vehicle_summary(plate)
        if summary:
            classification, detail, score = classify_vehicle(summary)
        else:
            classification = "Unknown"
            score = 0

        # Calculate overall confidence score from patterns
        if patterns:
            total_confidence = sum(p.avg_confidence * p.sightings for p in patterns)
            total_sightings = sum(p.sightings for p in patterns)
            confidence_score = total_confidence / total_sightings if total_sightings > 0 else 0.0
        else:
            confidence_score = 0.0

        return VehicleSummary(
            plate=plate,
            total_readings=profile.get('total_readings', 0),
            first_seen=datetime.fromisoformat(profile.get('first_seen', datetime.now().isoformat())),
            last_seen=datetime.fromisoformat(profile.get('last_seen', datetime.now().isoformat())),
            patterns=patterns,
            pending_readings=len(profile.get('pending', [])),
            classification=classification,
            routine_deviation_score=score,
            confidence_score=round(confidence_score, 3),
        )

    def get_pattern_grid(self, plate: str, fuzzy: bool = False) -> Optional[PatternGrid]:
        """
        Get pattern grid data for visualization
        """
        summary = self.get_vehicle_summary(plate, fuzzy)
        if not summary:
            return None

        # Get granularity from config
        from src.webui.services.config_service import get_config_service
        config = get_config_service().load_config()
        granularity = config.display.grid_time_granularity_minutes

        # Calculate number of time slots
        num_slots = int((24 * 60) / granularity)  # e.g., 32 for 45-min granularity

        # Initialize grid with zeros
        grid_matrix = {}  # (day, time_slot) -> count
        for day in range(7):
            for slot in range(num_slots):
                grid_matrix[(day, slot)] = {
                    'count': 0,
                    'confidence_sum': 0.0,
                    'pattern_ids': []
                }

        # Fill in pattern data
        max_count = 0
        for pattern in summary.patterns:
            pattern_minutes = pattern.time_minutes
            slot = int(pattern_minutes / granularity)

            # Parse days and add to grid
            for day_str in pattern.days:
                day_idx = self.day_names.index(day_str) if day_str in self.day_names else 0
                key = (day_idx, slot)
                if key in grid_matrix:
                    grid_matrix[key]['count'] += pattern.sightings
                    grid_matrix[key]['confidence_sum'] += pattern.avg_confidence * pattern.sightings
                    grid_matrix[key]['pattern_ids'].append(pattern.pattern_id)
                    max_count = max(max_count, grid_matrix[key]['count'])

        # Build rows
        rows = []
        for slot in range(num_slots):
            hour = int((slot * granularity) / 60)
            minute = (slot * granularity) % 60
            time_label = f"{hour:02d}:{minute:02d}"

            cells = []
            for day in range(7):
                key = (day, slot)
                cell_data = grid_matrix.get(key, {'count': 0, 'confidence_sum': 0.0, 'pattern_ids': []})

                avg_conf = (
                    cell_data['confidence_sum'] / cell_data['count']
                    if cell_data['count'] > 0 else 0.0
                )

                cells.append(GridCell(
                    day=day,
                    time_slot=slot,
                    count=cell_data['count'],
                    avg_confidence=round(avg_conf, 3),
                    pattern_ids=cell_data['pattern_ids']
                ))

            rows.append(GridRow(
                time_slot=slot,
                time_label=time_label,
                cells=cells
            ))

        return PatternGrid(
            vehicle_plate=plate,
            rows=rows,
            max_count=max_count,
            total_patterns=len(summary.patterns)
        )

    def list_vehicles(
        self,
        limit: int = 50,
        offset: int = 0,
        classification: Optional[str] = None,
        sort_by: str = "last_seen"
    ) -> List[VehicleListItem]:
        """List all vehicles with pagination and filters"""
        profiles = load_profiles()
        vehicles = []

        for plate, profile in profiles.items():
            # Get classification
            summary = get_vehicle_summary(plate)
            if summary:
                vehicle_classification, _, _ = classify_vehicle(summary)
            else:
                vehicle_classification = "Unknown"

            # Filter by classification if specified
            if classification and vehicle_classification != classification:
                continue

            vehicles.append(VehicleListItem(
                plate=plate,
                total_readings=profile.get('total_readings', 0),
                classification=vehicle_classification,
                last_seen=datetime.fromisoformat(profile.get('last_seen', datetime.now().isoformat())),
                pattern_count=len(profile.get('buckets', []))
            ))

        # Sort
        if sort_by == "last_seen":
            vehicles.sort(key=lambda x: x.last_seen, reverse=True)
        elif sort_by == "total_readings":
            vehicles.sort(key=lambda x: x.total_readings, reverse=True)
        elif sort_by == "plate":
            vehicles.sort(key=lambda x: x.plate)

        # Paginate
        return vehicles[offset:offset + limit]

    def search_vehicles(self, query: str, limit: int = 10) -> List[VehicleListItem]:
        """Search for vehicles by plate number"""
        profiles = load_profiles()
        results = []

        query_upper = query.upper()

        # Exact match first
        if query_upper in profiles:
            summary = self.get_vehicle_summary(query_upper)
            if summary:
                results.append(self._list_item_from_summary(summary))

        # Fuzzy matches
        if len(results) < limit:
            from difflib import SequenceMatcher
            matches = []

            for plate in profiles:
                if plate == query_upper:
                    continue

                score = SequenceMatcher(None, query_upper, plate).ratio()
                if score >= 0.7:  # Reasonable similarity threshold
                    matches.append((plate, score))

            # Sort by similarity score
            matches.sort(key=lambda x: x[1], reverse=True)

            for plate, score in matches[:limit - len(results)]:
                summary = self.get_vehicle_summary(plate)
                if summary:
                    results.append(self._list_item_from_summary(summary))

        return results

    def _list_item_from_summary(self, summary: VehicleSummary) -> VehicleListItem:
        """Convert VehicleSummary to VehicleListItem"""
        return VehicleListItem(
            plate=summary.plate,
            total_readings=summary.total_readings,
            classification=summary.classification,
            last_seen=summary.last_seen,
            pattern_count=len(summary.patterns)
        )


# Singleton instance
_vehicle_service = None


def get_vehicle_service() -> VehicleService:
    """Get singleton vehicle service instance"""
    global _vehicle_service
    if _vehicle_service is None:
        _vehicle_service = VehicleService()
    return _vehicle_service

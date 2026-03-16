"""
Frigate Database Import Service

Handles importing license plate events from Frigate SQLite database
into the Horizon event system for profile building.
"""

import os
import sqlite3
import json
import logging
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List, TYPE_CHECKING
from pathlib import Path
import threading
import time

from webui.models.config import ImportStatus

if TYPE_CHECKING:
    from horizon.mqtt.profile_manager import ProfileManager

logger = logging.getLogger(__name__)


class FrigateImportJob:
    """Represents a single import job"""

    def __init__(self, job_id: str, db_path: str, after_date: Optional[str] = None, auto_rebuild: bool = True):
        self.job_id = job_id
        self.db_path = db_path
        self.after_date = after_date
        self.auto_rebuild = auto_rebuild
        self.status = 'pending'
        self.progress = 0.0
        self.total_events = 0
        self.processed_events = 0
        self.filtered_events = 0
        self.plates_created = 0
        self.started_at: Optional[datetime] = None
        self.completed_at: Optional[datetime] = None
        self.error_message: Optional[str] = None
        self.db_size_mb = 0.0
        self._stop_requested = False
        self.rebuild_triggered = False

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API response"""
        return {
            'job_id': self.job_id,
            'status': self.status,
            'progress': self.progress,
            'total_events': self.total_events,
            'processed_events': self.processed_events,
            'filtered_events': self.filtered_events,
            'plates_created': self.plates_created,
            'started_at': self.started_at.isoformat() if self.started_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
            'error_message': self.error_message,
            'db_path': self.db_path,
            'db_size_mb': self.db_size_mb,
            'rebuild_triggered': self.rebuild_triggered
        }

    def to_model(self) -> ImportStatus:
        """Convert to ImportStatus model"""
        return ImportStatus(**self.to_dict())


class FrigateImportService:
    """
    Service for importing Frigate database events.

    Provides background job management for importing license plate
    detections from Frigate's SQLite database into the Horizon system.
    """

    def __init__(
        self,
        events_file: str = "data/raw/frigate_events.jsonl",
        profile_manager: Optional['ProfileManager'] = None
    ):
        self.events_file = events_file
        self.profile_manager = profile_manager
        self.jobs: Dict[str, FrigateImportJob] = {}
        self._lock = threading.Lock()
        self._ensure_directories()

    def _ensure_directories(self):
        """Ensure necessary directories exist"""
        os.makedirs(os.path.dirname(self.events_file), exist_ok=True)

    def _count_events(self, db_path: str, after_date: Optional[str] = None) -> int:
        """Count events to import from database"""
        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()

            # Try different schema variations
            queries = [
                # Method 1: plate_detections table
                """
                SELECT COUNT(*) FROM plate_detections
                WHERE confidence > 0.65
                """,
                # Method 2: event_detections with license_plate label
                """
                SELECT COUNT(*) FROM event_detections
                WHERE label = 'license_plate' AND data LIKE '%"confidence":%.' AND data NOT LIKE '%"confidence":0.%'
                """,
                # Method 3: event table with label filter
                """
                SELECT COUNT(*) FROM event
                WHERE label = 'license_plate' AND data LIKE '%"recognized_license_plate":%'
                """
            ]

            count = 0
            for query in queries:
                try:
                    cursor.execute(query)
                    count = max(count, cursor.fetchone()[0])
                except Exception:
                    continue

            conn.close()
            return count

        except Exception as e:
            logger.error(f"Error counting events: {e}")
            return 0

    def _extract_events(self, db_path: str, events_file: str,
                        after_date: Optional[str] = None,
                        progress_callback=None) -> Dict[str, int]:
        """
        Extract license plate events from Frigate database

        Returns dict with stats:
        - processed: total events processed
        - written: events written to file
        - filtered: events filtered out
        - unique_plates: number of unique plates
        """
        stats = {'processed': 0, 'written': 0, 'filtered': 0, 'unique_plates': set()}
        confidence_threshold = 0.65

        try:
            conn = sqlite3.connect(db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            # Try different extraction methods
            events = self._try_extraction_methods(cursor, after_date, confidence_threshold)

            if not events:
                logger.warning(f"No events found in {db_path}")
                conn.close()
                return stats

            # Write events to JSONL file
            with open(events_file, 'w') as f:
                for i, event in enumerate(events):
                    stats['processed'] += 1

                    # Apply filters
                    if event.get('confidence', 1.0) < confidence_threshold:
                        stats['filtered'] += 1
                        continue

                    # Write to file
                    f.write(json.dumps(event) + '\n')
                    stats['written'] += 1
                    stats['unique_plates'].add(event.get('plate', ''))

                    # Progress callback
                    if progress_callback and i % 100 == 0:
                        progress_callback(i + 1)

            conn.close()
            stats['unique_plates'] = len(stats['unique_plates'])
            logger.info(f"Extracted {stats['written']} events ({stats['filtered']} filtered)")

        except Exception as e:
            logger.error(f"Error extracting events: {e}")
            raise

        return stats

    def _try_extraction_methods(self, cursor, after_date: Optional[str],
                                confidence_threshold: float) -> List[Dict]:
        """Try different methods to extract events based on schema"""

        methods = [
            self._extract_from_plate_detections,
            self._extract_from_event_detections,
            self._extract_from_event_table
        ]

        for method in methods:
            try:
                events = method(cursor, after_date, confidence_threshold)
                if events:
                    logger.info(f"Extracted {len(events)} events using {method.__name__}")
                    return events
            except Exception as e:
                logger.debug(f"Method {method.__name__} failed: {e}")
                continue

        return []

    def _extract_from_plate_detections(self, cursor, after_date: Optional[str],
                                      confidence_threshold: float) -> List[Dict]:
        """Extract from plate_detections table (newer Frigate versions)"""
        query = """
            SELECT
                plate,
                confidence,
                start_time as timestamp,
                camera_id
            FROM plate_detections
            WHERE confidence >= ?
            ORDER BY start_time
        """

        params = [confidence_threshold]

        if after_date:
            query += " AND start_time >= ?"
            params.append(after_date)

        cursor.execute(query, params)

        events = []
        for row in cursor.fetchall():
            # Access camera_id from Row object directly
            camera = row['camera_id'] if 'camera_id' in row.keys() else 'unknown'

            events.append({
                'plate': row['plate'],
                'score': float(row['confidence']),  # Changed from 'confidence' to 'score'
                'timestamp': row['timestamp'],
                'camera': camera
            })

        return events

    def _extract_from_event_detections(self, cursor, after_date: Optional[str],
                                      confidence_threshold: float) -> List[Dict]:
        """Extract from event_detections table (mid Frigate versions)"""
        query = """
            SELECT
                data,
                created_at as timestamp
            FROM event_detections
            WHERE label = 'license_plate'
            ORDER BY created_at
        """

        if after_date:
            query += " AND created_at >= ?"

        cursor.execute(query, [after_date] if after_date else [])

        events = []
        for row in cursor.fetchall():
            try:
                data = json.loads(row['data'])

                plate = data.get('recognized_license_plate') or data.get('plate')
                confidence = data.get('recognized_license_plate_score') or data.get('confidence', 1.0)

                if not plate or confidence < confidence_threshold:
                    continue

                events.append({
                    'plate': plate,
                    'score': float(confidence),  # Changed from 'confidence' to 'score'
                    'timestamp': row['timestamp'],
                    'camera': data.get('camera', 'unknown')
                })
            except (json.JSONDecodeError, KeyError, TypeError):
                continue

        return events

    def _extract_from_event_table(self, cursor, after_date: Optional[str],
                                   confidence_threshold: float) -> List[Dict]:
        """Extract from event table (older Frigate versions)"""
        query = """
            SELECT
                data,
                camera,
                start_time as timestamp
            FROM event
            WHERE label = 'license_plate'
            ORDER BY start_time
        """

        if after_date:
            query += " AND start_time >= ?"

        cursor.execute(query, [after_date] if after_date else [])

        events = []
        for row in cursor.fetchall():
            try:
                data = json.loads(row['data'])

                plate = data.get('recognized_license_plate')
                confidence = data.get('recognized_license_plate_score', 1.0)

                if not plate or confidence < confidence_threshold:
                    continue

                # Access camera from Row object directly
                camera = row['camera'] if 'camera' in row.keys() else 'unknown'

                events.append({
                    'plate': plate,
                    'score': float(confidence),  # Changed from 'confidence' to 'score' for rebuild service compatibility
                    'timestamp': row['timestamp'],
                    'camera': camera
                })
            except (json.JSONDecodeError, KeyError, TypeError) as e:
                logger.debug(f"Error processing row: {e}")
                continue

        return events

    def start_import(self, db_path: str, after_date: Optional[str] = None, auto_rebuild: bool = True) -> str:
        """
        Start a new import job

        Args:
            db_path: Path to Frigate database
            after_date: Optional date filter (YYYY-MM-DD)
            auto_rebuild: Automatically trigger profile rebuild after import

        Returns:
            Job ID for tracking
        """
        # Validate file exists
        if not os.path.exists(db_path):
            raise FileNotFoundError(f"Database not found: {db_path}")

        # Create job
        job_id = f"import_{int(datetime.now().timestamp())}"
        job = FrigateImportJob(job_id, db_path, after_date, auto_rebuild)

        # Get DB size
        job.db_size_mb = os.path.getsize(db_path) / (1024 * 1024)

        with self._lock:
            self.jobs[job_id] = job

        # Start import in background thread
        thread = threading.Thread(
            target=self._run_import,
            args=(job,),
            daemon=True
        )
        thread.start()

        return job_id

    def _run_import(self, job: FrigateImportJob):
        """Run import job in background"""
        try:
            job.status = 'running'
            job.started_at = datetime.now()

            # Count total events
            job.total_events = self._count_events(job.db_path, job.after_date)
            logger.info(f"Import job {job.job_id}: Found {job.total_events} events")

            if job.total_events == 0:
                job.status = 'completed'
                job.completed_at = datetime.now()
                return

            # Progress callback
            def progress_callback(processed: int):
                job.processed_events = processed
                job.progress = processed / job.total_events if job.total_events > 0 else 0

            # Extract events
            stats = self._extract_events(
                job.db_path,
                self.events_file,
                job.after_date,
                progress_callback
            )

            # Update job stats
            job.processed_events = stats['processed']
            job.filtered_events = stats['filtered']
            job.plates_created = stats['unique_plates']
            job.progress = 1.0

            if job._stop_requested:
                job.status = 'cancelled'
            else:
                job.status = 'completed'

            job.completed_at = datetime.now()
            logger.info(f"Import job {job.job_id} completed: {stats['written']} events written")

            # Automatically trigger rebuild after successful import
            if job.status == 'completed' and stats['written'] > 0 and job.auto_rebuild:
                logger.info(f"Import complete, triggering automatic profile rebuild")
                job.rebuild_triggered = True
                self._trigger_rebuild()

        except Exception as e:
            job.status = 'failed'
            job.error_message = str(e)
            job.completed_at = datetime.now()
            logger.error(f"Import job {job.job_id} failed: {e}")

    def _trigger_rebuild(self):
        """Trigger automatic profile rebuild after import"""
        try:
            import asyncio
            from horizon.rebuild.rebuild_service import get_rebuild_service

            async def run_rebuild():
                # Pass profile_manager to rebuild service for coordination
                rebuild_service = get_rebuild_service(profile_manager=self.profile_manager)
                rebuild_job_id = rebuild_service.start_rebuild()
                logger.info(f"Auto-rebuild started: {rebuild_job_id}")

            # Run the async function in a new event loop
            asyncio.run(run_rebuild())
        except Exception as e:
            logger.error(f"Failed to trigger auto-rebuild: {e}")

    def cancel_import(self, job_id: str) -> bool:
        """Cancel an import job"""
        with self._lock:
            job = self.jobs.get(job_id)
            if job and job.status == 'running':
                job._stop_requested = True
                job.status = 'cancelled'
                job.completed_at = datetime.now()
                return True
        return False

    def set_profile_manager(self, profile_manager: 'ProfileManager') -> None:
        """
        Set the ProfileManager for coordinated rebuilds.

        Args:
            profile_manager: ProfileManager instance to coordinate with
        """
        self.profile_manager = profile_manager
        logger.info("ProfileManager set for coordinated rebuilds")

    def get_job(self, job_id: str) -> Optional[Dict[str, Any]]:
        """Get job status"""
        with self._lock:
            job = self.jobs.get(job_id)
            if job:
                return job.to_dict()
        return None

    def get_latest_job(self) -> Optional[Dict[str, Any]]:
        """Get the most recent job"""
        with self._lock:
            if not self.jobs:
                return None

            # Return most recent job
            latest = max(self.jobs.items(), key=lambda x: x[1].started_at or datetime.min)
            return latest[1].to_dict()


# Singleton instance
_import_service: Optional[FrigateImportService] = None


def get_import_service(profile_manager: Optional['ProfileManager'] = None) -> FrigateImportService:
    """
    Get the singleton import service.

    Args:
        profile_manager: Optional ProfileManager instance for coordinated rebuilds

    Returns:
        FrigateImportService instance
    """
    global _import_service
    if _import_service is None:
        _import_service = FrigateImportService(profile_manager=profile_manager)
    elif profile_manager is not None and _import_service.profile_manager is None:
        # Update profile manager if not set
        _import_service.set_profile_manager(profile_manager)
    return _import_service

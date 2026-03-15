"""
Rebuild service for processing frigate_events.jsonl

Reads all events from JSONL and rebuilds plate_profiles.json from scratch.
Useful when configuration changes require reprocessing all data.
"""

import asyncio
import json
import logging
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional, Callable
from uuid import uuid4

import pytz

from webui.models.config import PatternDetectionConfig, SystemConfig
from webui.services.config_service import get_config_service
from horizon.processor import clean_plate_string, correct_ocr_error

logger = logging.getLogger(__name__)


class RebuildJob:
    """Represents a single rebuild job"""

    def __init__(self, job_id: str, config: PatternDetectionConfig):
        self.job_id = job_id
        self.config = config
        self.status = "pending"
        self.progress = 0.0
        self.total_events = 0
        self.processed_events = 0
        self.started_at: Optional[datetime] = None
        self.completed_at: Optional[datetime] = None
        self.error_message: Optional[str] = None
        self._cancel_requested = False

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API response"""
        return {
            'job_id': self.job_id,
            'status': self.status,
            'progress': self.progress,
            'total_events': self.total_events,
            'processed_events': self.processed_events,
            'started_at': self.started_at.isoformat() if self.started_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
            'error_message': self.error_message
        }


class RebuildService:
    """Service for rebuilding plate profiles from JSONL events"""

    def __init__(self, profiles_path: Optional[str] = None, events_path: Optional[str] = None):
        """
        Initialize the rebuild service.

        Args:
            profiles_path: Path to plate_profiles.json
            events_path: Path to frigate_events.jsonl
        """
        if profiles_path is None:
            from horizon.processor import PROFILES_FILE
            profiles_path = PROFILES_FILE

        if events_path is None:
            events_path = os.environ.get("HORIZON_EVENTS_FILE", "data/raw/frigate_events.jsonl")

        self.profiles_path = Path(profiles_path)
        self.events_path = Path(events_path)
        self.jobs: Dict[str, RebuildJob] = {}
        self._current_job: Optional[RebuildJob] = None

    def start_rebuild(self) -> str:
        """
        Start a new rebuild job.

        Returns:
            Job ID for tracking
        """
        job_id = str(uuid4())

        # Get current config
        config_service = get_config_service()
        system_config = config_service.load_config()
        pattern_config = system_config.pattern_detection

        job = RebuildJob(job_id, pattern_config)
        self.jobs[job_id] = job
        self._current_job = job

        # Start the rebuild in a background task
        asyncio.create_task(self._run_rebuild(job))

        return job_id

    async def _run_rebuild(self, job: RebuildJob) -> None:
        """
        Execute the rebuild job.

        Args:
            job: The rebuild job to run
        """
        try:
            job.status = "running"
            job.started_at = datetime.now()

            # Check if events file exists
            if not self.events_path.exists():
                job.status = "failed"
                job.error_message = f"Events file not found: {self.events_path}"
                job.completed_at = datetime.now()
                return

            # Load all events from JSONL
            events = []
            with open(self.events_path, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if line:
                        try:
                            event = json.loads(line)
                            events.append(event)
                        except json.JSONDecodeError as e:
                            logger.warning(f"Skipping invalid JSON line: {e}")
                            continue

            job.total_events = len(events)

            if job.total_events == 0:
                job.status = "completed"
                job.progress = 1.0
                job.completed_at = datetime.now()
                return

            # Sort events by timestamp
            events.sort(key=lambda e: e.get('timestamp', 0))

            # Process events and build profiles
            profiles: Dict[str, Dict] = {}
            timezone = pytz.timezone('UTC')  # Events store Unix timestamps

            for i, event in enumerate(events):
                if job._cancel_requested:
                    job.status = "cancelled"
                    job.completed_at = datetime.now()
                    return

                # Process event
                self._process_event(event, profiles, job.config, timezone)

                job.processed_events = i + 1
                job.progress = job.processed_events / job.total_events

                # Log progress every 100 events
                if i % 100 == 0:
                    logger.info(f"Rebuild progress: {job.processed_events}/{job.total_events} events")

            # Save profiles
            self._save_profiles(profiles)

            job.status = "completed"
            job.completed_at = datetime.now()

            logger.info(f"Rebuild completed: {len(profiles)} profiles from {job.total_events} events")

        except Exception as e:
            job.status = "failed"
            job.error_message = str(e)
            job.completed_at = datetime.now()
            logger.error(f"Rebuild failed: {e}")

        finally:
            self._current_job = None

    def _process_event(
        self,
        event: Dict[str, Any],
        profiles: Dict[str, Dict],
        config: PatternDetectionConfig,
        timezone
    ) -> None:
        """
        Process a single event and update profiles.

        Args:
            event: Event data from JSONL
            profiles: Dictionary of profiles to update
            config: Pattern detection configuration
            timezone: Timezone for timestamp conversion
        """
        try:
            # Extract data
            plate_text = event.get('plate', '')
            confidence = event.get('score', 0)
            camera = event.get('camera', 'unknown')
            name = event.get('name')  # May be None
            unix_timestamp = event.get('timestamp')

            if not plate_text or not unix_timestamp:
                return

            # Clean and normalize plate
            plate = clean_plate_string(plate_text)
            if not plate or len(plate) < 2:
                return

            # Filter by confidence
            if confidence < config.confidence_threshold:
                return

            # Convert timestamp
            dt = datetime.fromtimestamp(unix_timestamp, tz=timezone)

            # Get or create profile
            if plate not in profiles:
                profiles[plate] = {
                    'buckets': [],
                    'pending': [],
                    'first_seen': None,
                    'last_seen': None,
                    'total_readings': 0,
                    'name': name  # Set name from first event
                }
            elif name and not profiles[plate].get('name'):
                # Update name if not set
                profiles[plate]['name'] = name

            profile = profiles[plate]

            # Update first_seen and last_seen
            reading_str = dt.isoformat()

            if profile['first_seen'] is None:
                profile['first_seen'] = reading_str
            else:
                first_seen = datetime.fromisoformat(profile['first_seen'])
                if dt < first_seen:
                    profile['first_seen'] = reading_str

            if profile['last_seen'] is None:
                profile['last_seen'] = reading_str
            else:
                last_seen = datetime.fromisoformat(profile['last_seen'])
                if dt > last_seen:
                    profile['last_seen'] = reading_str

            # Extract time components
            reading_minutes = dt.hour * 60 + dt.minute
            day_of_week = dt.weekday()

            # Try to fit into existing bucket
            for bucket in profile['buckets']:
                if abs(reading_minutes - bucket['avg_minutes']) <= config.bucket_tolerance_minutes:
                    # Update existing bucket
                    count = bucket['count']
                    bucket['avg_minutes'] = int(
                        bucket['avg_minutes'] * 0.7 + reading_minutes * 0.3
                    )
                    if day_of_week not in bucket['days_seen']:
                        bucket['days_seen'].append(day_of_week)
                        bucket['days_seen'].sort()
                    bucket['confidence_scores'].append(confidence)
                    bucket['count'] += 1
                    bucket['last_updated'] = datetime.now().isoformat()
                    profile['total_readings'] += 1
                    return

            # Add to pending
            profile['pending'].append({
                'minutes': reading_minutes,
                'day_of_week': day_of_week,
                'confidence': confidence,
                'timestamp': reading_str,
                'camera': camera
            })

            # Check if pending readings can form a new bucket
            if len(profile['pending']) >= config.min_pattern_samples:
                new_bucket = self._try_create_bucket_from_pending(profile['pending'], config)
                if new_bucket:
                    profile['buckets'].append(new_bucket)
                    # Remove used readings from pending
                    used_count = len(new_bucket.get('_used_readings', []))
                    profile['pending'] = profile['pending'][used_count:]
                    profile['total_readings'] += used_count
                else:
                    profile['total_readings'] += 1
            else:
                profile['total_readings'] += 1

        except Exception as e:
            logger.error(f"Error processing event: {e}")

    def _try_create_bucket_from_pending(
        self,
        pending: list,
        config: PatternDetectionConfig
    ) -> Optional[Dict]:
        """
        Try to create a new bucket from pending readings.

        Args:
            pending: List of pending readings
            config: Pattern detection configuration

        Returns:
            New bucket dict or None
        """
        if len(pending) < config.min_pattern_samples:
            return None

        pending_sorted = sorted(pending, key=lambda x: x['minutes'])

        # Try to find a cluster
        for i in range(len(pending_sorted) - config.min_pattern_samples + 1):
            cluster = pending_sorted[i:i + config.min_pattern_samples]
            time_range = cluster[-1]['minutes'] - cluster[0]['minutes']

            if time_range <= config.bucket_tolerance_minutes:
                avg_minutes = int(sum(p['minutes'] for p in cluster) / len(cluster))
                days = sorted(list(set(p['day_of_week'] for p in cluster)))
                confidences = [p['confidence'] for p in cluster]

                bucket = {
                    'avg_minutes': avg_minutes,
                    'days_seen': days,
                    'confidence_scores': confidences,
                    'count': len(cluster),
                    'last_updated': datetime.now().isoformat(),
                    '_used_readings': cluster  # Mark as used
                }
                return bucket

        return None

    def _save_profiles(self, profiles: Dict[str, Dict]) -> None:
        """
        Save profiles to disk.

        Args:
            profiles: Dictionary of profiles to save
        """
        try:
            # Ensure directory exists
            self.profiles_path.parent.mkdir(parents=True, exist_ok=True)

            # Write to temp file first (atomic)
            temp_path = self.profiles_path.with_suffix('.tmp')
            with open(temp_path, 'w') as f:
                json.dump(profiles, f, indent=2, default=str)

            # Rename to actual file
            temp_path.replace(self.profiles_path)

            logger.info(f"Saved {len(profiles)} profiles to {self.profiles_path}")
        except Exception as e:
            logger.error(f"Failed to save profiles: {e}")
            raise

    def get_job_status(self, job_id: str) -> Optional[Dict[str, Any]]:
        """
        Get the status of a rebuild job.

        Args:
            job_id: Job ID to check

        Returns:
            Job status dict or None if not found
        """
        job = self.jobs.get(job_id)
        if job:
            return job.to_dict()
        return None

    def cancel_job(self, job_id: str) -> bool:
        """
        Cancel a rebuild job.

        Args:
            job_id: Job ID to cancel

        Returns:
            True if cancelled successfully
        """
        job = self.jobs.get(job_id)
        if job and job.status == 'running':
            job._cancel_requested = True
            return True
        return False

    def get_latest_job(self) -> Optional[Dict[str, Any]]:
        """
        Get the most recent job status.

        Returns:
            Latest job status or None
        """
        if self.jobs:
            job_id = list(self.jobs.keys())[-1]
            return self.get_job_status(job_id)
        return None


# Singleton instance
_rebuild_service: Optional[RebuildService] = None


def get_rebuild_service() -> RebuildService:
    """Get singleton rebuild service instance"""
    global _rebuild_service
    if _rebuild_service is None:
        _rebuild_service = RebuildService()
    return _rebuild_service

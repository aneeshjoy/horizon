"""
MQTT message processor for Frigate license plate events.

Processes incoming MQTT messages and integrates with the existing
pattern detection and bucket management system.
"""

import logging
import asyncio
from datetime import datetime
from typing import Optional, Dict, Any

import pytz

from horizon.mqtt.deduplicator import EventDeduplicator
from horizon.mqtt.profile_manager import ProfileManager
from horizon.mqtt.event_logger import EventLogger, get_event_logger
from webui.models.config import MQTTConfig, PatternDetectionConfig

# Import existing processing functions
from horizon.processor import (
    correct_ocr_error,
    clean_plate_string,
    BUCKET_EPS,
    BUCKET_MIN_SAMPLES
)

logger = logging.getLogger(__name__)


class MQTTProcessor:
    """
    Process MQTT messages from Frigate and update vehicle profiles.
    """

    def __init__(
        self,
        mqtt_config: MQTTConfig,
        pattern_config: PatternDetectionConfig,
        profile_manager: ProfileManager,
        deduplicator: EventDeduplicator,
        event_logger: Optional[EventLogger] = None
    ):
        """
        Initialize the MQTT processor.

        Args:
            mqtt_config: MQTT configuration
            pattern_config: Pattern detection configuration
            profile_manager: Profile manager instance
            deduplicator: Event deduplicator instance
            event_logger: Event logger instance (optional, uses singleton if not provided)
        """
        self.mqtt_config = mqtt_config
        self.pattern_config = pattern_config
        self.profile_manager = profile_manager
        self.deduplicator = deduplicator
        self.event_logger = event_logger or get_event_logger()

        # Statistics
        self.processed_count: int = 0
        self.duplicate_count: int = 0
        self.filtered_count: int = 0
        self.error_count: int = 0

    async def process_message(self, payload: Dict[str, Any]) -> Optional[str]:
        """
        Process an MQTT message payload.

        Args:
            payload: MQTT message payload (Frigate event format)

        Returns:
            License plate number if processed successfully, None otherwise
        """
        try:
            # Extract event data
            event_data = self._extract_event_data(payload)
            if not event_data:
                return None

            # Check for duplicates
            if self.deduplicator.is_processed(event_data['event_id']):
                logger.debug(f"Duplicate event {event_data['event_id']}, skipping")
                self.duplicate_count += 1
                return None

            # Mark as processed
            self.deduplicator.mark_processed(event_data['event_id'])

            # Log event to JSONL (raw data for reprocessing)
            self._log_raw_event(payload, event_data)

            # Extract and normalize plate
            plate = self._extract_and_normalize_plate(event_data)
            if not plate:
                self.filtered_count += 1
                return None

            # Apply OCR correction
            all_profiles = await self.profile_manager.get_all_profiles()
            known_plates = list(all_profiles.keys())
            corrected_plate = correct_ocr_error(plate, known_plates)

            # Filter by confidence
            if event_data['confidence'] < self.pattern_config.confidence_threshold:
                logger.debug(f"Low confidence {event_data['confidence']}, filtering")
                self.filtered_count += 1
                return None

            # Process the reading
            await self._process_reading(
                corrected_plate,
                event_data['timestamp'],
                event_data['confidence'],
                event_data['camera'],
                event_data.get('name')  # Pass name field
            )

            self.processed_count += 1
            logger.info(f"Processed reading: {corrected_plate} (confidence: {event_data['confidence']:.2f})")

            return corrected_plate

        except Exception as e:
            self.error_count += 1
            logger.error(f"Error processing MQTT message: {e}")
            return None

    def _extract_event_data(self, payload: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Extract relevant data from tracked_object_update MQTT payload.

        Payload format:
        {
            "type": "lpr",
            "name": null,
            "plate": "251-WW-2075",
            "score": 0.936,
            "id": "1773567566.224675-m03c53",
            "camera": "lprcam",
            "timestamp": 1773567568.322408
        }

        Args:
            payload: MQTT message payload

        Returns:
            Event data dict or None if not a valid plate event
        """
        # Must be LPR type
        if payload.get('type') != 'lpr':
            return None

        # Extract event ID
        event_id = payload.get('id')
        if not event_id:
            return None

        # Extract camera name
        camera = payload.get('camera', 'unknown')

        # Get plate text
        plate_text = payload.get('plate', '')
        if not plate_text or len(clean_plate_string(plate_text)) < 2:
            return None

        # Get confidence (score field)
        confidence = payload.get('score', 0)
        if confidence < 0.1:  # Filter out obviously invalid readings
            return None

        # Convert timestamp (Unix to local timezone)
        unix_timestamp = payload.get('timestamp')
        if not unix_timestamp:
            return None

        # Convert to local timezone
        utc_dt = datetime.fromtimestamp(unix_timestamp)
        local_tz = pytz.timezone(self.mqtt_config.timezone)
        local_dt = utc_dt.replace(tzinfo=pytz.UTC).astimezone(local_tz)

        return {
            'event_id': event_id,
            'camera': camera,
            'plate_text': plate_text,
            'confidence': confidence,
            'timestamp': local_dt,
            'unix_timestamp': unix_timestamp,
            'name': payload.get('name')  # Include name from Frigate
        }

    def _extract_and_normalize_plate(self, event_data: Dict[str, Any]) -> Optional[str]:
        """
        Extract and normalize license plate text.

        Args:
            event_data: Event data dict

        Returns:
            Normalized plate text or None if invalid
        """
        plate_text = event_data['plate_text']
        cleaned = clean_plate_string(plate_text)

        if not cleaned or len(cleaned) < 2:
            return None

        return cleaned

    def _log_raw_event(self, payload: Dict[str, Any], event_data: Dict[str, Any]) -> None:
        """
        Log raw event to JSONL file for later reprocessing.

        Args:
            payload: Original MQTT payload
            event_data: Extracted event data
        """
        raw_event = {
            'timestamp': event_data['unix_timestamp'],
            'plate': event_data['plate_text'],
            'score': event_data['confidence'],
            'camera': event_data['camera'],
            'id': event_data['event_id'],
            'name': event_data.get('name')  # May be None
        }

        self.event_logger.log_event(raw_event)

    async def _process_reading(
        self,
        plate: str,
        timestamp: datetime,
        confidence: float,
        camera: str,
        name: Optional[str] = None
    ) -> None:
        """
        Process a single reading and update profile.

        Args:
            plate: Normalized license plate
            timestamp: Reading timestamp (local timezone)
            confidence: OCR confidence score
            camera: Camera name
            name: Friendly name from Frigate (optional)
        """
        async def update_profile(profile: Dict) -> None:
            # Update first_seen and last_seen
            reading_str = timestamp.isoformat()

            if profile['first_seen'] is None:
                profile['first_seen'] = reading_str
            else:
                first_seen = datetime.fromisoformat(profile['first_seen'])
                # Handle timezone mismatch - compare as naive or make both aware
                if first_seen.tzinfo is None and timestamp.tzinfo is not None:
                    # Make timestamp naive for comparison
                    timestamp_naive = timestamp.replace(tzinfo=None)
                    if timestamp_naive < first_seen:
                        profile['first_seen'] = reading_str
                elif first_seen.tzinfo is not None and timestamp.tzinfo is None:
                    # Make first_seen naive for comparison
                    first_seen_naive = first_seen.replace(tzinfo=None)
                    if timestamp < first_seen_naive:
                        profile['first_seen'] = reading_str
                else:
                    if timestamp < first_seen:
                        profile['first_seen'] = reading_str

            if profile['last_seen'] is None:
                profile['last_seen'] = reading_str
            else:
                last_seen = datetime.fromisoformat(profile['last_seen'])
                # Handle timezone mismatch - compare as naive or make both aware
                if last_seen.tzinfo is None and timestamp.tzinfo is not None:
                    # Make timestamp naive for comparison
                    timestamp_naive = timestamp.replace(tzinfo=None)
                    if timestamp_naive > last_seen:
                        profile['last_seen'] = reading_str
                elif last_seen.tzinfo is not None and timestamp.tzinfo is None:
                    # Make last_seen naive for comparison
                    last_seen_naive = last_seen.replace(tzinfo=None)
                    if timestamp > last_seen_naive:
                        profile['last_seen'] = reading_str
                else:
                    if timestamp > last_seen:
                        profile['last_seen'] = reading_str

            # Update name if provided and not already set
            if name and 'name' not in profile:
                profile['name'] = name

            # Extract time components
            reading_minutes = timestamp.hour * 60 + timestamp.minute
            day_of_week = timestamp.weekday()

            # Try to fit into existing bucket
            for bucket in profile['buckets']:
                if abs(reading_minutes - bucket['avg_minutes']) <= self.pattern_config.bucket_tolerance_minutes:
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
                    logger.debug(f"Added to existing bucket for {plate}")
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
            if len(profile['pending']) >= self.pattern_config.min_pattern_samples:
                new_bucket = self._try_create_bucket_from_pending(profile['pending'])
                if new_bucket:
                    profile['buckets'].append(new_bucket)
                    # Remove used readings from pending
                    used_count = len(new_bucket.get('_used_readings', []))
                    profile['pending'] = profile['pending'][used_count:]
                    profile['total_readings'] += used_count
                    logger.debug(f"Created new bucket for {plate}")
                else:
                    profile['total_readings'] += 1
            else:
                profile['total_readings'] += 1

        await self.profile_manager.update_profile(plate, update_profile)

    def _try_create_bucket_from_pending(self, pending: list) -> Optional[Dict]:
        """
        Try to create a new bucket from pending readings.

        Args:
            pending: List of pending readings

        Returns:
            New bucket dict or None
        """
        if len(pending) < self.pattern_config.min_pattern_samples:
            return None

        pending_sorted = sorted(pending, key=lambda x: x['minutes'])

        # Try to find a cluster
        for i in range(len(pending_sorted) - self.pattern_config.min_pattern_samples + 1):
            cluster = pending_sorted[i:i + self.pattern_config.min_pattern_samples]
            time_range = cluster[-1]['minutes'] - cluster[0]['minutes']

            if time_range <= self.pattern_config.bucket_tolerance_minutes:
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

    def get_stats(self) -> Dict:
        """
        Get processor statistics.

        Returns:
            Dictionary with statistics
        """
        return {
            'processed': self.processed_count,
            'duplicates': self.duplicate_count,
            'filtered': self.filtered_count,
            'errors': self.error_count
        }

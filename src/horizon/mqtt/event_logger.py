"""
Raw event logger for MQTT events.

Appends incoming license plate events to frigate_events.jsonl
for later reprocessing when configuration changes.
"""

import json
import logging
import os
from datetime import datetime
from pathlib import Path
from threading import Lock
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)


class EventLogger:
    """
    Thread-safe logger for raw license plate events.

    Appends each event to a JSONL file (one JSON object per line).
    This provides a complete record of all events for reprocessing.
    """

    def __init__(self, events_path: Optional[str] = None):
        """
        Initialize the event logger.

        Args:
            events_path: Path to the JSONL events file
        """
        if events_path is None:
            events_path = os.environ.get(
                "HORIZON_EVENTS_FILE",
                "data/raw/frigate_events.jsonl"
            )

        self.events_path = Path(events_path)
        self._lock = Lock()
        self._ensure_directory()

        # Statistics
        self.events_logged: int = 0
        self.last_log_time: Optional[datetime] = None
        self.errors: int = 0

    def _ensure_directory(self) -> None:
        """Create the directory for the events file if it doesn't exist."""
        self.events_path.parent.mkdir(parents=True, exist_ok=True)

    def log_event(self, event_data: Dict[str, Any]) -> bool:
        """
        Log an event to the JSONL file.

        Args:
            event_data: Dictionary containing event data

        Returns:
            True if logged successfully, False otherwise
        """
        try:
            with self._lock:
                # Convert to JSON and append to file
                json_line = json.dumps(event_data, separators=(',', ':'))

                # Open in append mode, create if doesn't exist
                with open(self.events_path, 'a', encoding='utf-8') as f:
                    f.write(json_line + '\n')

                self.events_logged += 1
                self.last_log_time = datetime.now()

                logger.debug(f"Logged event to {self.events_path}")

                return True

        except Exception as e:
            self.errors += 1
            logger.error(f"Failed to log event to {self.events_path}: {e}")
            return False

    def get_stats(self) -> Dict[str, Any]:
        """
        Get logger statistics.

        Returns:
            Dictionary with statistics
        """
        return {
            "events_logged": self.events_logged,
            "errors": self.errors,
            "last_log_time": self.last_log_time.isoformat() if self.last_log_time else None,
            "events_path": str(self.events_path),
            "file_exists": self.events_path.exists(),
            "file_size_bytes": self.events_path.stat().st_size if self.events_path.exists() else 0
        }

    def clear_events(self) -> bool:
        """
        Clear all events from the log file.

        Returns:
            True if cleared successfully
        """
        try:
            with self._lock:
                if self.events_path.exists():
                    self.events_path.unlink()
                    logger.info(f"Cleared events file: {self.events_path}")
                return True
        except Exception as e:
            logger.error(f"Failed to clear events file: {e}")
            return False


# Singleton instance
_event_logger: Optional[EventLogger] = None


def get_event_logger() -> EventLogger:
    """Get singleton event logger instance."""
    global _event_logger
    if _event_logger is None:
        _event_logger = EventLogger()
    return _event_logger

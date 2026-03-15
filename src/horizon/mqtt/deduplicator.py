"""
Event deduplication for MQTT messages.

Tracks processed Frigate event IDs to prevent duplicate processing
when both MQTT and batch processing are active.
"""

from collections import OrderedDict
from datetime import datetime, timedelta
from typing import Optional


class EventDeduplicator:
    """
    Track processed Frigate event IDs to prevent duplicate processing.
    Uses LRU cache with TTL to manage memory usage.
    """

    def __init__(self, max_size: int = 10000, ttl_hours: int = 24):
        """
        Initialize the deduplicator.

        Args:
            max_size: Maximum number of event IDs to track
            ttl_hours: Time-to-live for event IDs in hours
        """
        self.max_size = max_size
        self.ttl = timedelta(hours=ttl_hours)
        self._events: OrderedDict[str, datetime] = OrderedDict()
        self._hits: int = 0
        self._misses: int = 0
        self._evictions: int = 0

    def is_processed(self, event_id: Optional[str]) -> bool:
        """
        Check if event has been processed.

        Args:
            event_id: The Frigate event ID to check

        Returns:
            True if the event has been processed recently, False otherwise
        """
        if not event_id:
            return False

        if event_id not in self._events:
            self._misses += 1
            return False

        # Check if expired
        if datetime.now() - self._events[event_id] > self.ttl:
            del self._events[event_id]
            self._misses += 1
            return False

        self._hits += 1

        # Move to end (LRU)
        self._events.move_to_end(event_id)

        return True

    def mark_processed(self, event_id: str) -> None:
        """
        Mark event as processed.

        Args:
            event_id: The Frigate event ID to mark as processed
        """
        if not event_id:
            return

        # Evict oldest if at capacity
        if len(self._events) >= self.max_size:
            self._events.popitem(last=False)
            self._evictions += 1

        self._events[event_id] = datetime.now()

    def clear(self) -> None:
        """Clear all tracked events."""
        self._events.clear()
        self._hits = 0
        self._misses = 0
        self._evictions = 0

    @property
    def size(self) -> int:
        """Current number of tracked events."""
        return len(self._events)

    @property
    def hit_rate(self) -> float:
        """Cache hit rate (0.0 to 1.0)."""
        total = self._hits + self._misses
        return self._hits / total if total > 0 else 0.0

    def get_stats(self) -> dict:
        """
        Get deduplicator statistics.

        Returns:
            Dictionary with statistics
        """
        return {
            "size": self.size,
            "max_size": self.max_size,
            "hits": self._hits,
            "misses": self._misses,
            "evictions": self._evictions,
            "hit_rate": f"{self.hit_rate:.2%}"
        }

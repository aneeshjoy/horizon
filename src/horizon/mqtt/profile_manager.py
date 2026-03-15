"""
Profile manager with batched disk writes.

Manages in-memory profile cache with periodic disk synchronization
to prevent excessive I/O during high-volume MQTT message processing.
"""

import asyncio
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Callable, Dict, Optional

logger = logging.getLogger(__name__)


class ProfileManager:
    """
    Manage profile updates with batched disk writes.

    Reduces disk I/O by batching updates and debouncing saves.
    """

    def __init__(
        self,
        profiles_path: str,
        save_interval: int = 5,
        save_after_updates: int = 10
    ):
        """
        Initialize the profile manager.

        Args:
            profiles_path: Path to the profiles JSON file
            save_interval: Seconds to wait before saving (debounce)
            save_after_updates: Minimum updates before forcing save
        """
        self.profiles_path = Path(profiles_path)
        self.save_interval = save_interval
        self.save_after_updates = save_after_updates
        self.lock = asyncio.Lock()
        self.profiles: Dict = {}
        self.last_save: Optional[datetime] = None
        self.pending_updates: int = 0
        self._save_task: Optional[asyncio.Task] = None
        self._total_saves: int = 0
        self._total_updates: int = 0

        # Load existing profiles
        self._load_profiles()

    def _load_profiles(self) -> None:
        """Load profiles from disk."""
        try:
            if self.profiles_path.exists():
                with open(self.profiles_path, 'r') as f:
                    self.profiles = json.load(f)
                logger.info(f"Loaded {len(self.profiles)} profiles from {self.profiles_path}")
            else:
                self.profiles = {}
                logger.info(f"No existing profiles file at {self.profiles_path}, starting fresh")
        except Exception as e:
            logger.error(f"Failed to load profiles: {e}")
            self.profiles = {}

    async def update_profile(self, plate: str, update_func: Callable[[Dict], None]) -> None:
        """
        Update a profile with debounced saves.

        Args:
            plate: License plate number
            update_func: Async function to call with the profile dict
        """
        async with self.lock:
            # Ensure profile exists
            if plate not in self.profiles:
                self.profiles[plate] = self._create_empty_profile()

            # Apply update (await if it's a coroutine)
            result = update_func(self.profiles[plate])
            if asyncio.iscoroutine(result):
                await result

            self.pending_updates += 1
            self._total_updates += 1

            # Save if threshold reached
            if self.pending_updates >= self.save_after_updates:
                await self._save_now()
            else:
                self._schedule_save()

    async def get_profile(self, plate: str) -> Optional[Dict]:
        """
        Get a profile by plate number.

        Args:
            plate: License plate number

        Returns:
            Profile dict or None if not found
        """
        async with self.lock:
            return self.profiles.get(plate)

    async def get_all_profiles(self) -> Dict:
        """
        Get all profiles.

        Returns:
            Dictionary of all profiles
        """
        async with self.lock:
            return self.profiles.copy()

    async def force_save(self) -> None:
        """Force immediate save of all profiles."""
        async with self.lock:
            await self._save_now()

    def _create_empty_profile(self) -> Dict:
        """Create an empty profile structure."""
        return {
            "buckets": [],
            "pending": [],
            "first_seen": None,
            "last_seen": None,
            "total_readings": 0,
            "name": None  # Friendly name from Frigate
        }

    def _schedule_save(self) -> None:
        """Schedule a save if not already pending."""
        if self._save_task is None or self._save_task.done():
            self._save_task = asyncio.create_task(self._save_debounced())

    async def _save_debounced(self) -> None:
        """Save after delay if no more updates."""
        try:
            await asyncio.sleep(self.save_interval)

            # Only save if still needed
            if self.pending_updates > 0:
                await self._save_now()
        except asyncio.CancelledError:
            # Task was cancelled, force save
            await self._save_now()

    async def _save_now(self) -> None:
        """Immediately save profiles to disk."""
        try:
            # Ensure directory exists
            self.profiles_path.parent.mkdir(parents=True, exist_ok=True)

            # Write to temp file first (atomic)
            temp_path = self.profiles_path.with_suffix('.tmp')
            with open(temp_path, 'w') as f:
                json.dump(self.profiles, f, indent=2, default=str)

            # Rename to actual file
            temp_path.replace(self.profiles_path)

            self.last_save = datetime.now()
            self._total_saves += 1
            self.pending_updates = 0

            logger.debug(f"Saved {len(self.profiles)} profiles to {self.profiles_path}")
        except Exception as e:
            logger.error(f"Failed to save profiles: {e}")

    def get_stats(self) -> Dict:
        """
        Get profile manager statistics.

        Returns:
            Dictionary with statistics
        """
        return {
            "total_profiles": len(self.profiles),
            "pending_updates": self.pending_updates,
            "total_updates": self._total_updates,
            "total_saves": self._total_saves,
            "last_save": self.last_save.isoformat() if self.last_save else None
        }

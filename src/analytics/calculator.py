from __future__ import annotations

import datetime
from typing import Dict, List


class EfficiencyCalculator:
    """Real-time efficiency tracker for Delta Force Analytics.

    Tracks total value, item count, and provides live stats and
    projections based on elapsed time since the session started.
    """

    def __init__(self) -> None:
        # Core counters
        self.total_value: int = 0
        self.items_count: int = 0
        self.loot_names: List[str] = []
        # Timing
        self.session_start_time: datetime.datetime | None = None

    def start_session(self) -> None:
        """Start a new analytics session and reset all counters."""
        self.session_start_time = datetime.datetime.now()
        self.total_value = 0
        self.items_count = 0
        self.loot_names = []

    def add_loot(self, name: str, value: int, quantity: int = 1) -> None:
        """Add loot value to the session totals.

        Args:
            name: Display name of the loot item (kept for reference).
            value: Value of a single unit of the loot.
            quantity: Number of units of this loot.
        """
        if quantity < 0:
            raise ValueError("quantity must be non-negative")
        self.total_value += int(value) * int(quantity)
        self.items_count += int(quantity)
        self.loot_names.append(name)

    def get_elapsed_seconds(self) -> int:
        """Return seconds elapsed since session_start_time, or 0 if not started."""
        if self.session_start_time is None:
            return 0
        now = datetime.datetime.now()
        delta = now - self.session_start_time
        return int(delta.total_seconds())

    def get_value_per_minute(self) -> float:
        """Return current value per minute. 0.0 if session too new to compute."""
        elapsed = self.get_elapsed_seconds()
        if elapsed < 1:
            return 0.0
        return self.total_value / (elapsed / 60.0)

    def get_estimated_total(self, game_duration_minutes: int = 15) -> int:
        """Estimate final value based on current value per minute.

        Args:
            game_duration_minutes: Duration to project to (default 15 minutes).
        """
        vpm = self.get_value_per_minute()
        if vpm <= 0:
            return 0
        return int(round(vpm * float(game_duration_minutes)))

    def get_stats(self) -> Dict[str, int | float]:
        """Return a dict of current statistics."""
        return {
            "total_value": self.total_value,
            "items_count": self.items_count,
            "elapsed_seconds": self.get_elapsed_seconds(),
            "value_per_minute": self.get_value_per_minute(),
            "estimated_final": self.get_estimated_total(),
        }

    def get_live_summary(self) -> str:
        """Return a formatted overlay summary string."""
        elapsed = self.get_elapsed_seconds()
        mm = elapsed // 60
        ss = elapsed % 60
        elapsed_str = f"{mm:02d}:{ss:02d}"

        total_value_str = f"{int(self.total_value):,}"
        vpm = self.get_value_per_minute()
        vpm_int = int(round(vpm)) if vpm is not None else 0
        vpm_str = f"{vpm_int:,}"

        est = self.get_estimated_total()
        est_str = f"{est:,}"

        return (
            f"⏱️ {elapsed_str} | 💰 {total_value_str} | ⚡ {vpm_str}/min\n"
            f"📦 {self.items_count} items | 📈 Est: {est_str}"
        )

 
import json
import time
from vxe_utility.config import (
    HISTORY_FILE,
    HISTORY_RETENTION_HOURS,
    HISTORY_MIN_INTERVAL_SEC,
)


class BatteryHistoryStore:
    def __init__(self, initial_battery: int = 75):
        self.points: list[dict] = []
        self.load(initial_battery)

    def load(self, fallback_pct: int) -> None:
        if HISTORY_FILE.exists():
            try:
                with open(HISTORY_FILE, "r", encoding="utf-8") as f:
                    data = json.load(f)
                cutoff = time.time() - (HISTORY_RETENTION_HOURS * 3600)
                self.points = [pt for pt in data if pt.get("ts", 0) > cutoff]
            except Exception:
                self.points = []

        if len(self.points) < 2:
            now = time.time()
            base = self.points[-1]["pct"] if self.points else fallback_pct
            self.points = [
                {"ts": now - 3600 * 8, "pct": min(100, base + 18)},
                {"ts": now - 3600 * 6, "pct": min(100, base + 14)},
                {"ts": now - 3600 * 4, "pct": min(100, base + 9)},
                {"ts": now - 3600 * 2, "pct": min(100, base + 4)},
                {"ts": now, "pct": base},
            ]

    @property
    def latest_percentage(self) -> int | None:
        return self.points[-1]["pct"] if self.points else None

    def record(self, pct: int) -> None:
        now = time.time()
        should_save = (
            not self.points
            or (now - self.points[-1]["ts"] >= HISTORY_MIN_INTERVAL_SEC)
            or (self.points[-1]["pct"] != pct)
        )
        if not should_save:
            return

        self.points.append({"ts": now, "pct": pct})
        cutoff = now - (HISTORY_RETENTION_HOURS * 3600)
        self.points = [pt for pt in self.points if pt["ts"] > cutoff]

        try:
            with open(HISTORY_FILE, "w", encoding="utf-8") as f:
                json.dump(self.points, f)
        except Exception:
            pass
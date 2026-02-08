from __future__ import annotations

import random
import time
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any
from zoneinfo import ZoneInfo

from app.provider.alphavantage import FatalConfigError, RateLimitSkip, fetch_market_data
from app.utils.time import TimeWindow, ceil_to_interval, next_window_start, now_in_tz, parse_time


@dataclass
class Scheduler:
    config: dict[str, Any]
    logger: Any
    on_tick: Any

    def _allowed_weekday(self, now: datetime) -> bool:
        weekday = now.strftime("%a").upper()[:2]
        return weekday in set(self.config["usage_schedule"]["weekdays"])

    def _windows(self) -> list[TimeWindow]:
        windows = []
        for window in self.config["usage_schedule"]["windows"]:
            windows.append(TimeWindow(parse_time(window["start"]), parse_time(window["end"])))
        return windows

    def _next_window_start(self, now: datetime) -> datetime:
        windows = self._windows()
        candidates = [next_window_start(now, window) for window in windows]
        return min(candidates)

    def _within_window(self, now: datetime) -> bool:
        return any(window.contains(now) for window in self._windows())

    def _interval_minutes(self) -> int:
        interval = self.config["alphavantage"]["interval"]
        if interval == "5min":
            return 5
        return 15

    def _sleep_until(self, target: datetime) -> None:
        delta = (target - datetime.now(target.tzinfo)).total_seconds()
        if delta > 0:
            time.sleep(delta)

    def run(self) -> None:
        tz = ZoneInfo(self.config["general"]["timezone"])
        interval_minutes = self._interval_minutes()
        jitter_seconds = int(self.config["fetch_policy"]["jitter_seconds"])
        backfill = bool(self.config["fetch_policy"].get("backfill_on_start"))

        if backfill:
            now = now_in_tz(self.config["general"]["timezone"])
            if self._allowed_weekday(now) and self._within_window(now):
                try:
                    self.on_tick()
                except RateLimitSkip:
                    pass
                except FatalConfigError:
                    return

        while True:
            now = now_in_tz(self.config["general"]["timezone"])
            if not self._allowed_weekday(now) or not self._within_window(now):
                next_start = self._next_window_start(now)
                if not self._allowed_weekday(next_start):
                    next_start += timedelta(days=1)
                self.logger.info("Outside schedule. Sleeping until %s", next_start)
                self._sleep_until(next_start)
                continue

            next_slot = ceil_to_interval(now, interval_minutes)
            next_slot = next_slot.replace(tzinfo=tz)
            jitter = random.randint(0, jitter_seconds)
            target = next_slot + timedelta(seconds=jitter)
            self.logger.info("Sleeping until next interval %s", target)
            self._sleep_until(target)

            try:
                self.on_tick()
            except RateLimitSkip:
                continue
            except FatalConfigError:
                return

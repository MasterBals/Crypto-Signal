from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, time, timedelta
from zoneinfo import ZoneInfo


@dataclass(frozen=True)
class TimeWindow:
    start: time
    end: time

    def contains(self, candidate: datetime) -> bool:
        return self.start <= candidate.time() <= self.end


def parse_time(value: str) -> time:
    hours, minutes = value.split(":")
    return time(int(hours), int(minutes))


def now_in_tz(tz_name: str) -> datetime:
    return datetime.now(ZoneInfo(tz_name))


def next_window_start(now: datetime, window: TimeWindow) -> datetime:
    candidate = now.replace(hour=window.start.hour, minute=window.start.minute, second=0, microsecond=0)
    if candidate <= now:
        candidate += timedelta(days=1)
    return candidate


def ceil_to_interval(now: datetime, interval_minutes: int) -> datetime:
    minute = (now.minute // interval_minutes + 1) * interval_minutes
    hour = now.hour
    day = now.date()
    if minute >= 60:
        minute = 0
        hour += 1
        if hour == 24:
            hour = 0
            day = (now + timedelta(days=1)).date()
    return datetime.combine(day, time(hour, minute, tzinfo=now.tzinfo))

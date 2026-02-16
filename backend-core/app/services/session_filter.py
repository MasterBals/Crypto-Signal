from datetime import datetime
from zoneinfo import ZoneInfo


def get_session_score(now: datetime | None = None) -> float:
    current = now or datetime.now(ZoneInfo("Europe/Berlin"))
    minute = current.hour * 60 + current.minute
    london = 7 * 60 <= minute <= 11 * 60 + 30
    ny = 14 * 60 <= minute <= 18 * 60 + 30
    if london or ny:
        return 1.0
    return 0.2

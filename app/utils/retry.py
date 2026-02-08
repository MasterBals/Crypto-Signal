from __future__ import annotations

import time
from collections.abc import Callable
from typing import TypeVar

T = TypeVar("T")


def no_retry(func: Callable[[], T]) -> T:
    return func()


def sleep_seconds(seconds: float) -> None:
    time.sleep(seconds)

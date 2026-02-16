import time

from sqlalchemy import text

from app.db.base import Base
from app.db.session import engine


def init_db_with_retry(max_attempts: int = 30, sleep_seconds: int = 2) -> None:
    last_error: Exception | None = None
    for _ in range(max_attempts):
        try:
            with engine.connect() as connection:
                connection.execute(text("SELECT 1"))
            Base.metadata.create_all(bind=engine)
            return
        except Exception as exc:  # pragma: no cover - startup protection
            last_error = exc
            time.sleep(sleep_seconds)
    if last_error:
        raise last_error

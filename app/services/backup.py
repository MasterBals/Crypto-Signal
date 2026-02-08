from __future__ import annotations

from pathlib import Path
import time
import zipfile

from app.config import DEFAULT_SETTINGS_PATH
from app.services.db import DB_PATH


def create_backup() -> Path:
    data_dir = Path(DB_PATH).parent
    backups_dir = data_dir / "backups"
    backups_dir.mkdir(parents=True, exist_ok=True)
    timestamp = time.strftime("%Y%m%d-%H%M%S")
    backup_path = backups_dir / f"backup-{timestamp}.zip"

    with zipfile.ZipFile(backup_path, "w", zipfile.ZIP_DEFLATED) as archive:
        db_file = Path(DB_PATH)
        if db_file.exists():
            archive.write(db_file, arcname="market.db")
        settings_file = Path(DEFAULT_SETTINGS_PATH)
        if settings_file.exists():
            archive.write(settings_file, arcname="settings.json")

    return backup_path

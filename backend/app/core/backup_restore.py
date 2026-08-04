"""
AiChat Pro — Backup & Restore
Create ZIP backups of /data/, restore from archive, list available backups.
"""
from __future__ import annotations
import shutil
import logging
from datetime import datetime
from pathlib import Path
from typing import List, Dict
from core.storage import get_conn, now_iso
from shared_config import DATA_DIR, BACKUP_DIR

logger = logging.getLogger(__name__)


def create_backup() -> str:
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    archive_base = str(BACKUP_DIR / f"backup_{ts}")
    archive_path = shutil.make_archive(archive_base, "zip", str(DATA_DIR))
    conn = get_conn()
    conn.execute("INSERT INTO backups (archive_path, created_at) VALUES (?,?)",
                 (archive_path, now_iso()))
    conn.commit()
    conn.close()
    logger.info("Backup created: %s", archive_path)
    return archive_path


def restore_backup(archive_path: str) -> bool:
    p = Path(archive_path)
    if not p.exists():
        return False
    try:
        shutil.unpack_archive(str(p), str(DATA_DIR))
        logger.info("Restored from: %s", archive_path)
        return True
    except Exception as e:
        logger.error("Restore failed: %s", e)
        return False


def list_backups() -> List[Dict]:
    conn = get_conn()
    rows = conn.execute("SELECT * FROM backups ORDER BY id DESC LIMIT 50").fetchall()
    conn.close()
    return [dict(r) for r in rows]

"""Shared pytest fixtures.

Every test that touches the database gets an isolated, temporary SQLite
file so tests never read or write the developer's real data/aichat_pro.db.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pytest

import core.storage as storage


@pytest.fixture()
def temp_db(tmp_path, monkeypatch):
    """Point core.storage at a throwaway SQLite file and initialize it."""
    db_path = tmp_path / "test_aichat_pro.db"
    monkeypatch.setattr(storage, "DB_PATH", db_path)
    storage.init_db()
    yield db_path

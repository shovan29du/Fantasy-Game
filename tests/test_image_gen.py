"""Image provider fallback chain and local-only mode (core/image_gen.py).

All network-touching provider functions are mocked — these tests verify the
fallback ordering and local-only filtering logic, not any live provider.
"""
from unittest.mock import patch

import core.image_gen as image_gen
from core.storage import set_bool_setting


def test_download_image_falls_back_to_placeholder_when_all_providers_fail(temp_db, tmp_path, monkeypatch):
    monkeypatch.setattr(image_gen, "IMG_DIR", tmp_path)
    with patch.object(image_gen, "_try_pollinations", return_value=None), \
         patch.object(image_gen, "_try_comfyui", return_value=None), \
         patch.object(image_gen, "_try_automatic1111", return_value=None):
        path = image_gen.download_image("a knight in shining armor", filename="test.svg")
    assert path
    assert (tmp_path / "test.svg").exists()
    assert b"<svg" in (tmp_path / "test.svg").read_bytes()


def test_download_image_stops_at_first_successful_provider(temp_db, tmp_path, monkeypatch):
    monkeypatch.setattr(image_gen, "IMG_DIR", tmp_path)
    with patch.object(image_gen, "_try_pollinations", return_value=None) as poll, \
         patch.object(image_gen, "_try_comfyui", return_value=b"fake-png-bytes") as comfy, \
         patch.object(image_gen, "_try_automatic1111") as a1111:
        path = image_gen.download_image("a dragon", filename="test.png")
    assert (tmp_path / "test.png").exists()
    assert (tmp_path / "test.png").read_bytes() == b"fake-png-bytes"
    poll.assert_called_once()
    comfy.assert_called_once()
    a1111.assert_not_called()  # chain must stop once comfyui succeeds


def test_local_only_mode_skips_pollinations(temp_db, tmp_path, monkeypatch):
    monkeypatch.setattr(image_gen, "IMG_DIR", tmp_path)
    set_bool_setting("local_only_mode", True)
    with patch.object(image_gen, "_try_pollinations") as poll, \
         patch.object(image_gen, "_try_comfyui", return_value=b"local-bytes"):
        path = image_gen.download_image("a castle", filename="local.png")
    poll.assert_not_called()
    assert (tmp_path / "local.png").read_bytes() == b"local-bytes"


def test_local_only_mode_off_by_default_still_tries_pollinations(temp_db, tmp_path, monkeypatch):
    monkeypatch.setattr(image_gen, "IMG_DIR", tmp_path)
    with patch.object(image_gen, "_try_pollinations", return_value=b"poll-bytes") as poll:
        image_gen.download_image("a forest", filename="default.png")
    poll.assert_called_once()

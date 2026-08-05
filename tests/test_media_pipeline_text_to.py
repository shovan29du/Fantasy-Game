"""Text-to-animation and text-to-video orchestration (core/media_pipeline.py).

download_image (network) and create_animation/create_slideshow (ffmpeg) are
mocked -- these tests verify the chaining/fallback logic, not any live
provider or a real ffmpeg render.
"""
from unittest.mock import patch

import core.image_gen as image_gen
import core.media_pipeline as media_pipeline


def test_generate_animated_clip_chains_image_then_animation():
    with patch.object(image_gen, "download_image", return_value="/tmp/fake.png") as dl, \
         patch.object(media_pipeline, "create_animation", return_value="/tmp/fake.mp4") as anim:
        result = media_pipeline.generate_animated_clip("a lonely lighthouse", style_prefix="oil painting",
                                                         effect="pan_left", duration=4)
    dl.assert_called_once_with("oil painting, a lonely lighthouse", width=768, height=512)
    anim.assert_called_once_with("/tmp/fake.png", effect="pan_left", duration=4)
    assert result == {"image_path": "/tmp/fake.png", "video_path": "/tmp/fake.mp4"}


def test_generate_animated_clip_returns_none_when_image_generation_fails():
    with patch.object(image_gen, "download_image", return_value=None):
        result = media_pipeline.generate_animated_clip("a lonely lighthouse")
    assert result is None


def test_generate_animated_clip_returns_none_when_ffmpeg_render_fails():
    with patch.object(image_gen, "download_image", return_value="/tmp/fake.png"), \
         patch.object(media_pipeline, "create_animation", return_value=None):
        result = media_pipeline.generate_animated_clip("a lonely lighthouse")
    assert result is None


def test_generate_scene_video_generates_one_image_per_prompt():
    with patch.object(image_gen, "download_image", side_effect=["/tmp/a.png", "/tmp/b.png", "/tmp/c.png"]) as dl, \
         patch.object(media_pipeline, "create_slideshow", return_value="/tmp/scenes.mp4") as slideshow:
        result = media_pipeline.generate_scene_video(["dawn over the city", "a chase through the alleys", "the final standoff"])
    assert dl.call_count == 3
    slideshow.assert_called_once()
    assert slideshow.call_args.args[0] == ["/tmp/a.png", "/tmp/b.png", "/tmp/c.png"]
    assert result["image_paths"] == ["/tmp/a.png", "/tmp/b.png", "/tmp/c.png"]
    assert result["video_path"] == "/tmp/scenes.mp4"


def test_generate_scene_video_skips_scenes_whose_image_generation_failed():
    with patch.object(image_gen, "download_image", side_effect=["/tmp/a.png", None, "/tmp/c.png"]), \
         patch.object(media_pipeline, "create_slideshow", return_value="/tmp/scenes.mp4") as slideshow:
        result = media_pipeline.generate_scene_video(["scene one", "scene two", "scene three"])
    assert slideshow.call_args.args[0] == ["/tmp/a.png", "/tmp/c.png"]
    assert result["image_paths"] == ["/tmp/a.png", "/tmp/c.png"]


def test_generate_scene_video_returns_none_when_every_scene_fails():
    with patch.object(image_gen, "download_image", return_value=None):
        result = media_pipeline.generate_scene_video(["scene one", "scene two"])
    assert result is None


def test_generate_scene_video_returns_none_when_slideshow_render_fails():
    with patch.object(image_gen, "download_image", return_value="/tmp/a.png"), \
         patch.object(media_pipeline, "create_slideshow", return_value=None):
        result = media_pipeline.generate_scene_video(["scene one"])
    assert result is None

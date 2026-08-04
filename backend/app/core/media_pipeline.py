"""AiChat Pro v21 — Media Pipeline
Image provider selector, FFmpeg animation pipeline, video job queue,
achievement/boss cinematic triggers, character portrait batch gen."""

from __future__ import annotations
import json, os, subprocess, time, threading, hashlib
from pathlib import Path
from typing import Dict, List, Optional
from core.storage import get_conn, now_iso
from shared_config import MEDIA_DIR
from core.logging_setup import get_logger

log = get_logger(__name__)

ANIM_DIR = MEDIA_DIR / "animation"; ANIM_DIR.mkdir(parents=True, exist_ok=True)
VIDEO_DIR = MEDIA_DIR / "video"; VIDEO_DIR.mkdir(parents=True, exist_ok=True)

# ═══ IMAGE PROVIDER SELECTOR ═══

def get_provider_options() -> List[Dict]:
    """Return available image providers with status."""
    providers = [
        {"id": "pollinations", "name": "Pollinations.ai", "needs_key": False,
         "desc": "Free, no API key. Good quality, unlimited."},
        {"id": "comfyui", "name": "ComfyUI", "needs_key": False,
         "desc": "Local install. Requires ComfyUI running."},
        {"id": "automatic1111", "name": "Automatic1111", "needs_key": False,
         "desc": "Local install. Requires SDWEBUI running."},
        {"id": "dalle", "name": "DALL-E", "needs_key": True,
         "desc": "OpenAI API. Requires API key. $0.02-0.08/image."},
        {"id": "placeholder", "name": "Placeholder", "needs_key": False,
         "desc": "SVG fallback. Always available."},
    ]
    return providers

# ═══ FFMPEG ANIMATION PIPELINE ═══

ANIMATION_EFFECTS = {
    "zoom_in": "-vf \"zoompan=z='min(zoom+0.002,1.5)':d=125:s=1280x720\"",
    "zoom_out": "-vf \"zoompan=z='if(lte(zoom,1.0),1.5,max(1.001,zoom-0.002))':d=125:s=1280x720\"",
    "pan_right": "-vf \"zoompan=z=1.3:x='iw/2-(iw/zoom/2)+on*2':d=125:s=1280x720\"",
    "pan_left": "-vf \"zoompan=z=1.3:x='iw/2-(iw/zoom/2)-on*2':d=125:s=1280x720\"",
    "ken_burns": "-vf \"zoompan=z='min(zoom+0.001,1.3)':x='iw/2-(iw/zoom/2)+on':d=125:s=1280x720\"",
    "fade_in": "-vf \"fade=t=in:st=0:d=1\"",
}

def create_animation(image_path: str, output_name: str = None,
                     effect: str = "ken_burns", duration: int = 5) -> Optional[str]:
    """Create video from single image with pan/zoom effect. Returns output path or None."""
    if not os.path.exists(image_path):
        return None
    if not output_name:
        h = hashlib.md5(image_path.encode()).hexdigest()[:8]
        output_name = f"anim_{h}.mp4"
    output_path = str(ANIM_DIR / output_name)
    effect_filter = ANIMATION_EFFECTS.get(effect, ANIMATION_EFFECTS["ken_burns"])
    frames = duration * 25

    # Replace d= with actual frame count
    effect_filter = effect_filter.replace("d=125", f"d={frames}")

    cmd = (f"ffmpeg -y -loop 1 -i \"{image_path}\" "
           f"{effect_filter} "
           f"-t {duration} -pix_fmt yuv420p -c:v libx264 "
           f"\"{output_path}\"")
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, timeout=120)
        if result.returncode == 0 and os.path.exists(output_path):
            return output_path
    except Exception:
        pass
    return None

def create_slideshow(image_paths: List[str], output_name: str = "slideshow.mp4",
                     duration_per_slide: int = 3) -> Optional[str]:
    """Create slideshow video from multiple images."""
    if not image_paths:
        return None
    output_path = str(VIDEO_DIR / output_name)
    # Build concat file
    concat_file = str(VIDEO_DIR / "_concat.txt")
    with open(concat_file, "w") as f:
        for img in image_paths:
            if os.path.exists(img):
                f.write(f"file '{img}'\nduration {duration_per_slide}\n")
    cmd = (f"ffmpeg -y -f concat -safe 0 -i \"{concat_file}\" "
           f"-vf \"scale=1280:720:force_original_aspect_ratio=decrease,pad=1280:720:(ow-iw)/2:(oh-ih)/2\" "
           f"-pix_fmt yuv420p -c:v libx264 \"{output_path}\"")
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, timeout=300)
        if result.returncode == 0:
            try: os.remove(concat_file)
            except Exception:
                log.debug("suppressed error", exc_info=True)
                pass
            return output_path
    except Exception:
        pass
    return None

# ═══ VIDEO JOB QUEUE ═══

_job_thread = None
_job_running = False

def queue_media_job(job_type: str, input_path: str = "", params: Dict = None) -> int:
    """Queue a media job for background processing. Returns job ID."""
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("INSERT INTO media_jobs (job_type, status, input_path, params_json, created_at) "
                "VALUES (?,?,?,?,?)",
                (job_type, "queued", input_path, json.dumps(params or {}), now_iso()))
    job_id = cur.lastrowid
    conn.commit(); conn.close()
    _ensure_worker()
    return job_id

def get_job_status(job_id: int) -> Optional[Dict]:
    conn = get_conn()
    row = conn.execute("SELECT * FROM media_jobs WHERE id=?", (job_id,)).fetchone()
    conn.close()
    return dict(row) if row else None

def list_jobs(status: str = None, limit: int = 20) -> List[Dict]:
    conn = get_conn()
    if status:
        rows = conn.execute("SELECT * FROM media_jobs WHERE status=? ORDER BY id DESC LIMIT ?",
                            (status, limit)).fetchall()
    else:
        rows = conn.execute("SELECT * FROM media_jobs ORDER BY id DESC LIMIT ?",
                            (limit,)).fetchall()
    conn.close()
    return [dict(r) for r in rows]

def _process_job(job: Dict):
    """Process a single media job."""
    job_id = job["id"]
    job_type = job["job_type"]
    params = json.loads(job["params_json"] or "{}")
    conn = get_conn()
    conn.execute("UPDATE media_jobs SET status='processing' WHERE id=?", (job_id,))
    conn.commit(); conn.close()

    output = None
    try:
        if job_type == "animation":
            output = create_animation(
                job["input_path"],
                effect=params.get("effect", "ken_burns"),
                duration=params.get("duration", 5)
            )
        elif job_type == "slideshow":
            images = params.get("images", [])
            output = create_slideshow(images, duration_per_slide=params.get("duration", 3))
        elif job_type == "portrait_batch":
            _batch_generate_portraits(params)
            output = "batch_complete"
    except Exception as e:
        output = None

    conn = get_conn()
    status = "completed" if output else "failed"
    conn.execute("UPDATE media_jobs SET status=?, output_path=?, completed_at=? WHERE id=?",
                 (status, output or "", now_iso(), job_id))
    conn.commit(); conn.close()

def _worker_loop():
    global _job_running
    while _job_running:
        conn = get_conn()
        job = conn.execute("SELECT * FROM media_jobs WHERE status='queued' ORDER BY id LIMIT 1").fetchone()
        conn.close()
        if job:
            _process_job(dict(job))
        else:
            time.sleep(2)

def _ensure_worker():
    global _job_thread, _job_running
    if _job_thread and _job_thread.is_alive():
        return
    _job_running = True
    _job_thread = threading.Thread(target=_worker_loop, daemon=True)
    _job_thread.start()

# ═══ CINEMATIC TRIGGERS ═══

def trigger_achievement_cinematic(character_name: str, achievement_title: str,
                                  badge_icon: str = "🏆") -> Optional[int]:
    """Queue celebration image generation for achievement milestone."""
    from core.image_gen import download_image
    prompt = (f"epic celebration scene, golden light, {character_name} receiving award, "
              f"achievement unlocked, {achievement_title}, fantasy art, dramatic lighting")
    path = download_image(prompt, width=1280, height=720)
    if path:
        return queue_media_job("animation", path, {"effect": "zoom_in", "duration": 4})
    return None

def trigger_boss_cinematic(boss_name: str, world_name: str = "") -> Optional[int]:
    """Queue boss encounter cinematic."""
    from core.image_gen import download_image
    prompt = (f"epic boss encounter, {boss_name}, dark atmosphere, dramatic lighting, "
              f"fantasy battle scene, menacing, powerful, cinematic")
    path = download_image(prompt, width=1280, height=720)
    if path:
        return queue_media_job("animation", path, {"effect": "zoom_in", "duration": 6})
    return None

# ═══ BATCH PORTRAIT GENERATION ═══

def _batch_generate_portraits(params: Dict):
    """Generate portraits for all characters missing photos."""
    from core.image_gen import generate_character_image
    conn = get_conn()
    chars = conn.execute(
        "SELECT * FROM characters WHERE photo_path IS NULL OR photo_path=''").fetchall()
    conn.close()
    for c in chars:
        try:
            path = generate_character_image(dict(c), style_key=params.get("style", "Anime Portrait"))
            if path:
                conn2 = get_conn()
                conn2.execute("UPDATE characters SET photo_path=? WHERE id=?", (path, c["id"]))
                conn2.commit(); conn2.close()
        except Exception:
            continue

def queue_batch_portraits(style: str = "Anime Portrait") -> int:
    """Queue batch portrait generation for all characters without photos."""
    return queue_media_job("portrait_batch", params={"style": style})

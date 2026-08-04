"""AiChat Pro v21 — Image Generation with 4-provider fallback chain
Pollinations.ai → ComfyUI → Automatic1111 → placeholder SVG.
Provider selector UI support. Character prompt builder."""
import os, urllib.parse, random, hashlib, json, base64
from pathlib import Path
from shared_config import MEDIA_DIR, COMFYUI_URL, A1111_URL
from core.logging_setup import get_logger

log = get_logger(__name__)

IMG_DIR = MEDIA_DIR / "images"; IMG_DIR.mkdir(parents=True, exist_ok=True)

PHOTO_STYLES = {
    "Anime Portrait": "anime style portrait, detailed face, beautiful lighting, high quality",
    "Anime Full Body": "anime style full body shot, detailed, beautiful lighting, standing pose",
    "Realistic Portrait": "photorealistic portrait photograph, studio lighting, 8k, detailed face",
    "Realistic Full Body": "photorealistic full body photograph, studio lighting, 8k, professional",
    "Fantasy Art": "fantasy art painting, detailed, dramatic lighting, epic composition",
    "Fantasy Full Body": "fantasy art full body illustration, detailed armor/clothing, epic scene",
    "3D Render": "3D rendered character, Unreal Engine, detailed textures, studio lighting",
    "3D Full Body": "3D rendered full body character, Unreal Engine, T-pose or action pose",
    "Comic Book": "comic book style illustration, bold lines, vibrant colors, dynamic pose",
    "Cyberpunk": "cyberpunk style portrait, neon lighting, futuristic, detailed",
    "Dark Fantasy": "dark fantasy art, moody lighting, gothic atmosphere, detailed",
    "Steampunk": "steampunk style portrait, brass gears, Victorian aesthetic, detailed",
    "Oil Painting": "oil painting portrait, classical art style, rich colors, brushstrokes",
    "Watercolour": "watercolor painting portrait, soft colors, artistic, beautiful",
    "Manga": "manga style illustration, black and white with screentones, detailed",
    "Chibi": "chibi style character, cute, big head small body, adorable, colorful",
    "Concept Art": "concept art character design, professional, detailed turnaround",
    "Pin-Up": "pin-up art style, vintage aesthetic, glamorous pose, beautiful",
    "Cinematic": "cinematic scene, movie poster quality, dramatic lighting, 4k",
    "Furry Art": "furry art style, anthropomorphic character, detailed fur, expressive",
    "Sci-Fi": "sci-fi character portrait, futuristic technology, space aesthetic",
    "Gothic": "gothic art style, dark and elegant, detailed, atmospheric",
    "Custom": "",
}

PROVIDERS = ["pollinations", "comfyui", "automatic1111", "placeholder"]

# ═══ PROVIDER IMPLEMENTATIONS ═══

def _try_pollinations(prompt, width=512, height=768, seed=None):
    """Free, no API key, no content filter."""
    import requests
    encoded = urllib.parse.quote(prompt)
    url = f"https://image.pollinations.ai/prompt/{encoded}?width={width}&height={height}&nologo=true&nofeed=true&safe=false"
    if seed is not None: url += f"&seed={seed}"
    r = requests.get(url, timeout=120)
    if r.status_code == 200 and len(r.content) > 1000:
        return r.content
    return None

def _try_comfyui(prompt, width=512, height=768):
    """Local ComfyUI instance."""
    if not COMFYUI_URL:
        return None
    import requests
    workflow = {
        "prompt": {
            "3": {"class_type": "KSampler", "inputs": {
                "seed": random.randint(0, 2**32), "steps": 20, "cfg": 7,
                "sampler_name": "euler", "scheduler": "normal",
                "positive": ["6", 0], "negative": ["7", 0],
                "latent_image": ["5", 0], "model": ["4", 0]
            }},
            "5": {"class_type": "EmptyLatentImage", "inputs": {
                "width": width, "height": height, "batch_size": 1
            }},
            "6": {"class_type": "CLIPTextEncode", "inputs": {
                "text": prompt, "clip": ["4", 1]
            }},
            "7": {"class_type": "CLIPTextEncode", "inputs": {
                "text": "worst quality, low quality, blurry", "clip": ["4", 1]
            }},
        }
    }
    try:
        r = requests.post(f"{COMFYUI_URL}/prompt", json=workflow, timeout=120)
        if r.status_code == 200:
            data = r.json()
            prompt_id = data.get("prompt_id", "")
            # Poll for result
            import time
            for _ in range(60):
                time.sleep(2)
                hr = requests.get(f"{COMFYUI_URL}/history/{prompt_id}", timeout=10)
                if hr.status_code == 200:
                    hist = hr.json()
                    if prompt_id in hist:
                        outputs = hist[prompt_id].get("outputs", {})
                        for node_id, output in outputs.items():
                            imgs = output.get("images", [])
                            if imgs:
                                img_data = imgs[0]
                                img_url = f"{COMFYUI_URL}/view?filename={img_data['filename']}"
                                ir = requests.get(img_url, timeout=30)
                                if ir.status_code == 200:
                                    return ir.content
                        break
    except Exception:
        log.debug("ComfyUI generation failed", exc_info=True)
    return None

def _try_automatic1111(prompt, width=512, height=768):
    """Local Automatic1111/SDWEBUI instance."""
    import requests
    a1111_url = A1111_URL
    try:
        payload = {
            "prompt": prompt,
            "negative_prompt": "worst quality, low quality, blurry, deformed",
            "steps": 20, "cfg_scale": 7, "width": width, "height": height,
            "sampler_name": "Euler a"
        }
        r = requests.post(f"{a1111_url}/sdapi/v1/txt2img", json=payload, timeout=120)
        if r.status_code == 200:
            data = r.json()
            images = data.get("images", [])
            if images:
                return base64.b64decode(images[0])
    except Exception:
        log.debug("Automatic1111 generation failed", exc_info=True)
    return None

def _placeholder_image(prompt, width=512, height=768):
    """Generate a simple SVG placeholder when all providers fail."""
    short = prompt[:60].replace('"', "'").replace("<", "").replace(">", "")
    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}">
  <rect width="100%" height="100%" fill="#2a2a3e"/>
  <text x="50%" y="45%" text-anchor="middle" fill="#8888cc" font-size="16" font-family="sans-serif">Image Unavailable</text>
  <text x="50%" y="55%" text-anchor="middle" fill="#666688" font-size="12" font-family="sans-serif">{short}</text>
</svg>'''
    return svg.encode("utf-8")

# ═══ MAIN API ═══

def generate_image_url(prompt, width=512, height=768, seed=None):
    """Quick URL generation (Pollinations, unrestricted)."""
    encoded = urllib.parse.quote(prompt)
    url = f"https://image.pollinations.ai/prompt/{encoded}?width={width}&height={height}&nologo=true&nofeed=true&safe=false"
    if seed is not None: url += f"&seed={seed}"
    return url

def download_image(prompt, filename=None, width=512, height=768, providers=None):
    """Download image through fallback chain. Returns file path or empty string.

    If Settings -> Config -> "Local-only mode" is enabled, the "pollinations"
    provider (the app's only non-local, internet-dependent provider) is
    skipped even if present in `providers`."""
    if providers is None:
        providers = PROVIDERS
    try:
        from core.storage import get_bool_setting
        if get_bool_setting("local_only_mode", False):
            providers = [p for p in providers if p != "pollinations"]
    except Exception:
        log.debug("suppressed error", exc_info=True)

    img_data = None
    used_provider = None

    for provider in providers:
        try:
            if provider == "pollinations":
                img_data = _try_pollinations(prompt, width, height)
            elif provider == "comfyui":
                img_data = _try_comfyui(prompt, width, height)
            elif provider == "automatic1111":
                img_data = _try_automatic1111(prompt, width, height)
            elif provider == "placeholder":
                img_data = _placeholder_image(prompt, width, height)

            if img_data:
                used_provider = provider
                break
        except Exception:
            log.debug("Image provider %s failed", provider, exc_info=True)
            continue

    if not img_data:
        return ""

    if not filename:
        h = hashlib.md5(prompt.encode()).hexdigest()[:8]
        safe = "".join(c if c.isalnum() or c in " _-" else "_" for c in prompt[:30]).strip()
        ext = ".svg" if used_provider == "placeholder" else ".png"
        filename = f"{safe}_{h}{ext}"

    path = str(IMG_DIR / filename)
    with open(path, "wb") as f:
        f.write(img_data)
    return path

def build_character_prompt(name, gender, race, hair, eyes, body_type, skin,
                           style_key="Anime Portrait", height="", extra=""):
    """Build image prompt from character fields. Futa always renders female-presenting."""
    parts = []
    style = PHOTO_STYLES.get(style_key, "")
    if style:
        parts.append(style)

    # Futa → female-presenting
    display_gender = gender
    if gender and gender.lower() in ("futa", "futanari"):
        display_gender = "female"

    if display_gender: parts.append(f"{display_gender}")
    if race: parts.append(f"{race}")
    if hair: parts.append(f"{hair} hair")
    if eyes: parts.append(f"{eyes} eyes")
    if body_type: parts.append(f"{body_type} body")
    if skin: parts.append(f"{skin} skin")
    if height: parts.append(f"{height} tall")
    if extra: parts.append(extra)

    prompt = ", ".join(parts)
    return prompt

def generate_character_image(char_dict, style_key="Anime Portrait", width=512, height=768):
    """Generate image for a character dict. Returns file path."""
    prompt = build_character_prompt(
        name=char_dict.get("name", ""),
        gender=char_dict.get("gender", ""),
        race=char_dict.get("race", ""),
        hair=char_dict.get("hair", ""),
        eyes=char_dict.get("eyes", ""),
        body_type=char_dict.get("body_type", ""),
        skin=char_dict.get("skin", ""),
        style_key=style_key,
        height=char_dict.get("height", ""),
    )
    seed = int(hashlib.md5(char_dict.get("name", "x").encode()).hexdigest()[:8], 16)
    return download_image(prompt, width=width, height=height)

def get_active_provider():
    """Get currently configured provider order from settings or default."""
    from core.storage import get_conn
    conn = get_conn()
    row = conn.execute("SELECT value FROM settings WHERE key='image_providers'").fetchone()
    conn.close()
    if row:
        try:
            return json.loads(row["value"])
        except Exception:
            log.warning("Corrupt image_providers setting; using defaults", exc_info=True)
    return PROVIDERS

def set_provider_order(providers):
    """Save provider order to settings."""
    from core.storage import get_conn, now_iso
    conn = get_conn()
    conn.execute("INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)",
                 ("image_providers", json.dumps(providers)))
    conn.commit()
    conn.close()

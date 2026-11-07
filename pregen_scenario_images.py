"""Pre-generate scenario card images based on name + backstory.

Run this while the game server is running:
    python pregen_scenario_images.py

It calls the local API for every scenario using the same rich prompt the
frontend now uses (name + first 120 chars of opening text + category style).
The 46-second rate-limit throttle is handled server-side. Already-cached
images return instantly. Total time for 77 fresh images ≈ 60 minutes.
"""
import sys
import time
import requests

BASE = "http://127.0.0.1:8501"

STYLE_MAP = {
    "fantasy":     "Fantasy Art",
    "anime":       "Anime Portrait",
    "zombie":      "Dark Fantasy",
    "supernatural":"Dark Fantasy",
    "mystery":     "Dark Fantasy",
    "apocalyptic": "Dark Fantasy",
    "cyberpunk":   "Cyberpunk",
    "alien_space": "Sci-Fi",
    "drama":       "Cinematic",
    "game":        "Fantasy Art",
}


def build_prompt(cat_label, cat_key, name, opening):
    hint = opening[:120].replace("'", "").replace('"', "").replace("<", "").replace(">", "").replace("&", "and").strip() if opening else ""
    if hint:
        return f"{cat_label} scene: {name} — {hint}, cinematic rpg illustration, atmospheric lighting, detailed environment, no text"
    return f"{cat_label} rpg scene, {name}, cinematic illustration, atmospheric, detailed"


def main():
    try:
        cats = requests.get(f"{BASE}/api/scenarios/categories", timeout=10).json()
    except Exception as e:
        print(f"[ERROR] Could not reach server at {BASE}: {e}")
        print("       Make sure run_app.bat is running first.")
        sys.exit(1)

    scenarios = []
    for cat in cats:
        for s in cat.get("scenarios", []):
            scenarios.append({
                "name":      s["name"],
                "cat_key":   cat["key"],
                "cat_label": cat["label"],
                "opening":   s.get("opening", ""),
            })

    total = len(scenarios)
    print(f"Found {total} scenarios. Generating images...\n")

    cached = 0
    generated = 0
    errors = 0

    for i, s in enumerate(scenarios, 1):
        name      = s["name"]
        cat_key   = s["cat_key"]
        cat_label = s["cat_label"]
        opening   = s["opening"]
        prompt    = build_prompt(cat_label, cat_key, name, opening)
        style     = STYLE_MAP.get(cat_key, "Fantasy Art")

        t0 = time.monotonic()
        try:
            r = requests.post(
                f"{BASE}/api/media/image",
                json={"prompt": prompt, "style": style, "width": 512, "height": 384, "save_to_chat": False},
                timeout=180,
            )
            r.raise_for_status()
            data = r.json()
            elapsed = time.monotonic() - t0
            if elapsed < 2:
                cached += 1
                tag = "(cached)"
            else:
                generated += 1
                tag = f"({elapsed:.0f}s)"
            print(f"[{i:>3}/{total}] ✓ {name[:45]:<45} {tag}")
        except Exception as e:
            errors += 1
            print(f"[{i:>3}/{total}] ✗ {name[:45]:<45} ERROR: {e}")

    print(f"\nDone. {generated} generated, {cached} from cache, {errors} errors.")
    print("Refresh the game in your browser — all scenario cards will show their images.")


if __name__ == "__main__":
    main()

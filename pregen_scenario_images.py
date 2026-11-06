"""Pre-generate scenario card images.

Run this while the game server is running:
    python pregen_scenario_images.py

It calls the local API for every scenario, letting the backend cache each
image to disk. The 46-second rate-limit throttle is handled server-side;
this script just waits for each response. Already-cached images return
instantly. Total time for 77 fresh images ≈ 60 minutes.
"""
import sys
import time
import requests

BASE = "http://127.0.0.1:8501"


def main():
    # Fetch all scenario categories and their entries
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
                "name": s["name"],
                "cat_label": cat["label"],
            })

    total = len(scenarios)
    print(f"Found {total} scenarios. Generating images...\n")

    cached = 0
    generated = 0
    errors = 0

    for i, s in enumerate(scenarios, 1):
        name = s["name"]
        cat_label = s["cat_label"]
        prompt = (
            f"a {cat_label} rpg scene for {name}, "
            "character portrait, cinematic fantasy illustration"
        )

        t0 = time.monotonic()
        try:
            r = requests.post(
                f"{BASE}/api/media/image",
                json={"prompt": prompt, "style": "Fantasy Art", "width": 512, "height": 384, "save_to_chat": False},
                timeout=180,
            )
            r.raise_for_status()
            data = r.json()
            elapsed = time.monotonic() - t0
            if elapsed < 2:
                # Served from cache — no Pollinations call was made
                cached += 1
                tag = "(cached)"
            else:
                generated += 1
                tag = f"({elapsed:.0f}s)"
            url = data.get("url") or data.get("path") or "?"
            print(f"[{i:>3}/{total}] ✓ {name[:45]:<45} {tag}")
        except Exception as e:
            errors += 1
            print(f"[{i:>3}/{total}] ✗ {name[:45]:<45} ERROR: {e}")

    print(f"\nDone. {generated} generated, {cached} from cache, {errors} errors.")


if __name__ == "__main__":
    main()

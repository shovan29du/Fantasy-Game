"""Pre-generate the illustrations used by the in-app Help.

Run from the repository root:
    python tools/pregen_help_images.py            # everything still missing
    python tools/pregen_help_images.py --sections # only the 17 topic banners
    python tools/pregen_help_images.py --limit 20 # stop after 20 new pictures

Pictures are saved to media/help/<topic>/<entry>.jpg and are skipped when they
already exist, so the script can be stopped and restarted freely. The free
image provider is rate-limited to about one image every 46 seconds.
"""
import argparse
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from core.image_gen import download_image  # noqa: E402
from core.storage import init_db  # noqa: E402
from backend.app.domain.help_content import picture_specs  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--sections", action="store_true", help="only the topic banners")
    parser.add_argument("--limit", type=int, default=0, help="stop after this many new pictures")
    args = parser.parse_args()

    from PIL import Image

    init_db()
    specs = [s for s in picture_specs() if not args.sections or s["section"] == "sections"]
    todo = [s for s in specs if not s["path"].is_file()]
    print(f"{len(specs)} pictures defined, {len(specs) - len(todo)} already done, {len(todo)} to generate.")

    made = failed = 0
    for spec in todo:
        if args.limit and made >= args.limit:
            break
        started = time.time()
        source = download_image(spec["prompt"], width=768, height=432,
                                providers=["pollinations", "comfyui", "automatic1111"])
        if not source:
            failed += 1
            print(f"  FAILED  {spec['section']}/{spec['id']}")
            continue
        spec["path"].parent.mkdir(parents=True, exist_ok=True)
        with Image.open(source) as im:
            im.convert("RGB").resize((640, 360)).save(spec["path"], "JPEG", quality=82, optimize=True)
        made += 1
        print(f"  ok {made:3}/{len(todo)}  {spec['section']}/{spec['id']}  ({time.time() - started:.0f}s)", flush=True)

    print(f"Done: {made} generated, {failed} failed.")
    return 1 if failed and not made else 0


if __name__ == "__main__":
    sys.exit(main())

"""Assemble the README animation from actual browser captures, without mock UI."""
from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

from PIL import Image


ROOT = Path(__file__).resolve().parents[1]


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    paths = [ROOT / "output/playwright" / f"gif-{index:02}.png" for index in range(1, 5)]
    frames = [Image.open(path).convert("RGB") for path in paths]
    if any(frame.size != frames[0].size for frame in frames):
        raise ValueError("All browser captures must use the same viewport.")
    durations = [2300, 4200, 4000, 2000]
    target = ROOT / "docs/receipt-demo.gif"
    frames[0].save(target, save_all=True, append_images=frames[1:], duration=durations,
                   loop=0, optimize=True, disposal=2)
    download = ROOT / ".playwright-cli/freshtrack-synthetic-fixture.json"
    payload = json.loads(download.read_text(encoding="utf-8"))
    if payload["processing_info"]["mode"] != "synthetic_fixture" or len(payload["items"]) != 3:
        raise ValueError("Expected the actual three-item synthetic demo export.")
    source_paths = ["app/api_main.py", "app/static/index.html"]
    recording = {
        "assembled_at_utc": datetime.now(timezone.utc).isoformat(),
        "method": "Actual local app screenshots captured with Playwright CLI / isolated Microsoft Edge",
        "fixture": "Built-in synthetic text; no OCR or model inference",
        "viewport": list(frames[0].size),
        "frame_durations_ms": durations,
        "frames": [{"file": path.relative_to(ROOT).as_posix(), "sha256": digest(path)} for path in paths],
        "source_sha256": {name: digest(ROOT / name) for name in source_paths},
        "download": {"mode": payload["processing_info"]["mode"], "item_count": len(payload["items"]),
                     "sha256": digest(download)},
        "gif_sha256": digest(target),
    }
    (ROOT / "docs/demo-recording.json").write_text(json.dumps(recording, indent=2) + "\n", encoding="utf-8")
    print(f"Wrote {target.relative_to(ROOT)} ({target.stat().st_size} bytes)")


if __name__ == "__main__":
    main()

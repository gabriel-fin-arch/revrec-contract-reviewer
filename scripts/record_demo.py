"""Record docs/images/demo.gif: the offline demo, the run index and one memo.

Every frame comes from the code as it is. The first is the real output of
`revrec demo`, drawn as text; the rest are screenshots, taken with Playwright,
of the pages `revrec site` writes from the corpus with the rules extractor: the
run index, the top of one memo, and a value in that memo with the words it was
read from, its clause and its page. Run from the repo root with a Python that
has Playwright (and its Chromium) and Pillow:

    python scripts/record_demo.py

The commands run through uv with ANTHROPIC_API_KEY set empty, and both pin the
rules extractor, so nothing calls the API. Nothing here is part of the package
or its tests.
"""

from __future__ import annotations

import io
import os
import subprocess
import tempfile
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "docs" / "images" / "demo.gif"
WIDTH, HEIGHT = 1280, 800
GIF_WIDTH = 960
MEMO = "nimbus-of-helix"
OFFLINE = {**os.environ, "ANTHROPIC_API_KEY": ""}


def terminal_frame(command: list[str], prompt: str, lines: int = 30) -> Image.Image:
    out = subprocess.run(command, cwd=ROOT, env=OFFLINE, capture_output=True, text=True, check=True).stdout
    text = [f"$ {prompt}", ""] + out.splitlines()[:lines]
    try:
        font = ImageFont.truetype("consola.ttf", 17)
    except OSError:
        font = ImageFont.truetype("DejaVuSansMono.ttf", 16)
    image = Image.new("RGB", (WIDTH, HEIGHT), "#1e1e1e")
    draw = ImageDraw.Draw(image)
    for i, line in enumerate(text):
        draw.text((24, 20 + i * 24), line[:130], font=font, fill="#9cdcfe" if i == 0 else "#d4d4d4")
    return image


def shot(page) -> Image.Image:
    return Image.open(io.BytesIO(page.screenshot())).convert("RGB")


def site_frames() -> list[Image.Image]:
    frames: list[Image.Image] = []
    with tempfile.TemporaryDirectory() as tmp:
        site = Path(tmp) / "site"
        subprocess.run(["uv", "run", "revrec", "site", "--out", str(site)], cwd=ROOT, env=OFFLINE, check=True,
                       capture_output=True)
        with sync_playwright() as p:
            browser = p.chromium.launch()
            page = browser.new_page(viewport={"width": WIDTH, "height": HEIGHT})
            page.goto((site / "index.html").as_uri())
            frames.append(shot(page))

            page.goto((site / f"{MEMO}.html").as_uri())
            frames.append(shot(page))

            cited = page.locator("table blockquote").first
            cited.scroll_into_view_if_needed()
            page.evaluate("window.scrollBy(0, 200)")  # keep the row's label in view above the quote
            frames.append(shot(page))
            browser.close()
    return frames


def main() -> None:
    frames = [terminal_frame(["uv", "run", "revrec", "demo"], "uv run revrec demo")]
    frames += site_frames()
    small = [f.resize((GIF_WIDTH, round(f.height * GIF_WIDTH / f.width)), Image.LANCZOS) for f in frames]
    palette = [f.quantize(colors=128, method=Image.Quantize.MEDIANCUT) for f in small]
    durations = [5000, 4000, 5000, 6000][: len(palette)]
    OUT.parent.mkdir(parents=True, exist_ok=True)
    palette[0].save(OUT, save_all=True, append_images=palette[1:], duration=durations, loop=0, optimize=True)
    print(f"{OUT}: {len(palette)} frames, {sum(durations) / 1000:.0f} s, {OUT.stat().st_size / 1e6:.2f} MB")


if __name__ == "__main__":
    main()

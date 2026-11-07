"""Generate Citefolio favicon / apple / OG assets (bone / ink / ink-red)."""

from __future__ import annotations

import shutil
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

BONE = (232, 228, 220, 255)
INK = (18, 20, 26, 255)
ACCENT = (196, 92, 74, 255)
STEEL = (61, 74, 92, 255)

ROOT = Path(__file__).resolve().parents[1]
PUBLIC = ROOT / "public"
APP = ROOT / "app"


def mark(size: int, radius_ratio: float = 0.18) -> Image.Image:
    img = Image.new("RGBA", (size, size), BONE)
    d = ImageDraw.Draw(img)
    margin = max(2, size // 16)
    d.rounded_rectangle(
        [margin, margin, size - margin - 1, size - margin - 1],
        radius=max(2, int(size * radius_ratio)),
        outline=INK,
        width=max(1, size // 32),
    )
    bar_w = max(2, size // 10)
    bar_x = margin + size // 6
    d.rectangle(
        [bar_x, margin + size // 5, bar_x + bar_w, size - margin - size // 5],
        fill=ACCENT,
    )
    line_x0 = bar_x + bar_w + max(3, size // 12)
    line_x1 = size - margin - size // 6
    y = margin + size // 4
    gap = max(3, size // 8)
    for i, frac in enumerate((1.0, 0.85, 0.55)):
        x1 = int(line_x0 + (line_x1 - line_x0) * frac)
        color = INK if i < 2 else STEEL
        thick = max(1, size // 28)
        d.rectangle([line_x0, y, x1, y + thick], fill=color)
        y += gap
    return img


def main() -> None:
    PUBLIC.mkdir(exist_ok=True)
    APP.mkdir(exist_ok=True)

    mark(512).save(PUBLIC / "icon_512.png")
    mark(180).save(PUBLIC / "apple-touch-icon.png")
    mark(32).save(PUBLIC / "favicon_32.png")
    mark(16).save(PUBLIC / "favicon_16.png")
    mark(32).save(PUBLIC / "favicon.ico", format="ICO", sizes=[(16, 16), (32, 32)])

    # App Router apple icon (icon.svg lives beside this)
    shutil.copy(PUBLIC / "apple-touch-icon.png", APP / "apple-icon.png")

    og = Image.new("RGB", (1200, 630), (232, 228, 220))
    d = ImageDraw.Draw(og)
    d.rectangle([0, 0, 18, 630], fill=ACCENT)
    og.paste(mark(220).convert("RGB"), (80, 205))
    try:
        font_lg = ImageFont.truetype(r"C:\Windows\Fonts\georgia.ttf", 96)
        font_sm = ImageFont.truetype(r"C:\Windows\Fonts\seguisb.ttf", 36)
        font_mono = ImageFont.truetype(r"C:\Windows\Fonts\consola.ttf", 28)
    except OSError:
        font_lg = ImageFont.load_default()
        font_sm = font_lg
        font_mono = font_lg
    d.text((360, 210), "Citefolio", fill=INK[:3], font=font_lg)
    d.text((360, 330), "Ask your PDF. Answers cite the page.", fill=STEEL[:3], font=font_sm)
    d.text(
        (360, 420),
        "RAG  ·  Next.js  ·  Neon pgvector  ·  FastAPI",
        fill=STEEL[:3],
        font=font_mono,
    )
    og.save(PUBLIC / "og.png", optimize=True)
    print("icons written to", PUBLIC)


if __name__ == "__main__":
    main()

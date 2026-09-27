#!/usr/bin/env python3
"""Generate the QindaQt boot artwork: the rEFInd menu theme and Plymouth splash.

The outputs under share/ are committed, so sys-boot/qinda-boot installs them
without build-time dependencies. Regenerate after changing this file or art/:

    python3 tools/build_assets.py            # write share/
    python3 tools/build_assets.py --check    # fail if share/ is out of date

Needs Pillow, rsvg-convert (gnome-base/librsvg), Inter and IBM Plex Mono.
Colours and the mark follow the QindaQt "reclaimed" SDDM theme.
"""

from __future__ import annotations

import argparse
import io
import math
import os
import subprocess
import sys
import tempfile
from pathlib import Path

from PIL import Image, ImageChops, ImageDraw, ImageFilter, ImageFont

ROOT = Path(__file__).resolve().parent.parent
ART = ROOT / "art" / "reclaimed.png"

FONT_DIRS = [
    Path.home() / ".local/share/fonts/sloom/collection/base",
    Path("/usr/share/fonts"),
]

# QindaQt "reclaimed" palette (SDDM theme.conf).
CANVAS = (0x16, 0x26, 0x27)
CANVAS_DEEP = (0x0C, 0x15, 0x16)
SURFACE = (0x1D, 0x2B, 0x28)
TRACK = (0x2C, 0x3D, 0x39)
ACCENT = (0xBF, 0xD9, 0x85)
SECONDARY = (0xF2, 0xCB, 0x7D)
TEXT = (0xF7, 0xFA, 0xED)
MUTED = (0xC3, 0xCF, 0xB5)
BORDER = (0x56, 0x69, 0x53)


def hexc(rgb: tuple[int, int, int]) -> str:
    return "#%02x%02x%02x" % rgb


def find_font(name: str) -> Path:
    for base in FONT_DIRS:
        for dirpath, _, files in os.walk(base):
            if name in files:
                return Path(dirpath) / name
    sys.exit(f"build_assets: font {name} not found in {FONT_DIRS}")


def inter(px: int, weight: str = "SemiBold") -> ImageFont.FreeTypeFont:
    font = ImageFont.truetype(str(find_font("Inter[opsz,wght].ttf")), px)
    font.set_variation_by_name(weight)
    return font


def plex_mono(px: int) -> ImageFont.FreeTypeFont:
    return ImageFont.truetype(str(find_font("IBMPlexMono-Medium.ttf")), px)


def render_svg(svg: str, width: int, height: int) -> Image.Image:
    png = subprocess.run(
        ["rsvg-convert", "--width", str(width), "--height", str(height), "--format", "png"],
        input=svg.encode(), capture_output=True, check=True,
    ).stdout
    return Image.open(io.BytesIO(png)).convert("RGBA")


# --------------------------------------------------------------------- mark --
def mark_shapes(ink: str) -> str:
    """The two-ring QindaQt mark (components/QqMark.qml) in a 52x40 box."""
    parts = []
    d, s = 0.45 * 52, 0.055 * 52
    y0 = (40 - d) / 2
    for i in range(2):
        x0 = i * 0.47 * 52
        parts.append(
            f'<circle cx="{x0 + d / 2:.3f}" cy="{y0 + d / 2:.3f}" r="{(d - s) / 2:.3f}" '
            f'fill="none" stroke="{ink}" stroke-width="{s:.3f}"/>'
        )
        tx, ty, tw = x0 + 0.66 * d, y0 + 0.76 * d, 0.40 * d
        cx, cy = tx + tw / 2, ty + s / 2
        parts.append(
            f'<rect x="{tx:.3f}" y="{ty:.3f}" width="{tw:.3f}" height="{s:.3f}" rx="{s / 2:.3f}" '
            f'fill="{ink}" transform="rotate(45 {cx:.3f} {cy:.3f})"/>'
        )
        parts.append(
            f'<circle cx="{x0 + 0.45 * d:.3f}" cy="{y0 + 0.43 * d:.3f}" r="{0.08 * d:.3f}" fill="{ink}"/>'
        )
    return "".join(parts)


def mark(width: int, ink: tuple[int, int, int]) -> Image.Image:
    height = round(width * 40 / 52)
    svg = (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 52 40">'
           f"{mark_shapes(hexc(ink))}</svg>")
    return render_svg(svg, width, height)


# -------------------------------------------------------------------- icons --
def tile(inner: str, top: tuple[int, int, int], bottom: tuple[int, int, int]) -> str:
    """A rounded launcher tile in a 256 box, 16 px of air on every side."""
    return f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 256 256">
<defs>
 <linearGradient id="g" x1="0" y1="0" x2="0" y2="1">
  <stop offset="0" stop-color="{hexc(top)}"/><stop offset="1" stop-color="{hexc(bottom)}"/>
 </linearGradient>
 <linearGradient id="h" x1="0" y1="0" x2="0" y2="1">
  <stop offset="0" stop-color="#ffffff" stop-opacity=".16"/><stop offset=".5" stop-color="#ffffff" stop-opacity="0"/>
 </linearGradient>
</defs>
<rect x="18" y="18" width="220" height="220" rx="50" fill="url(#g)"/>
<rect x="18" y="18" width="220" height="220" rx="50" fill="url(#h)"/>
<rect x="19.5" y="19.5" width="217" height="217" rx="48.5" fill="none" stroke="{hexc(BORDER)}" stroke-width="3" stroke-opacity=".9"/>
{inner}
</svg>"""


def icon_qindaqt() -> str:
    scale = 3.1
    w, h = 52 * scale, 40 * scale
    return tile(
        f'<g transform="translate({128 - w / 2:.2f} {128 - h / 2:.2f}) scale({scale})">'
        f"{mark_shapes(hexc(ACCENT))}</g>",
        (0x27, 0x45, 0x3E), CANVAS_DEEP,
    )


def icon_llm_server() -> str:
    amber, lime = hexc(SECONDARY), hexc(ACCENT)
    pins = []
    for k in (-26, 0, 26):
        pins.append(f'<line x1="{128 + k}" y1="58" x2="{128 + k}" y2="76"/>')
        pins.append(f'<line x1="{128 + k}" y1="180" x2="{128 + k}" y2="198"/>')
        pins.append(f'<line x1="58" y1="{128 + k}" x2="76" y2="{128 + k}"/>')
        pins.append(f'<line x1="180" y1="{128 + k}" x2="198" y2="{128 + k}"/>')
    r, c = 30, 128
    star = (f"M{c} {c - r} C{c + 5} {c - 7} {c + 7} {c - 5} {c + r} {c} "
            f"C{c + 7} {c + 5} {c + 5} {c + 7} {c} {c + r} "
            f"C{c - 5} {c + 7} {c - 7} {c + 5} {c - r} {c} "
            f"C{c - 7} {c - 5} {c - 5} {c - 7} {c} {c - r}Z")
    inner = (
        f'<g stroke="{amber}" stroke-width="9" stroke-linecap="round" fill="none">'
        f'<rect x="80" y="80" width="96" height="96" rx="18"/>{"".join(pins)}</g>'
        f'<path d="{star}" fill="{lime}"/>'
        f'<circle cx="152" cy="104" r="6" fill="{lime}"/>'
    )
    return tile(inner, (0x3A, 0x36, 0x24), CANVAS_DEEP)


def icon_advanced() -> str:
    muted = hexc(MUTED)
    inner = (
        f'<g stroke="{muted}" stroke-width="9" stroke-linecap="round" stroke-linejoin="round" fill="none">'
        f'<path d="M128 70 L186 100 L128 130 L70 100 Z"/>'
        f'<path d="M70 128 L128 158 L186 128"/>'
        f'<path d="M70 156 L128 186 L186 156"/></g>'
    )
    return tile(inner, (0x2A, 0x33, 0x31), CANVAS_DEEP)


def func_icon(inner: str) -> str:
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 96 96">'
            f'<g fill="none" stroke="{hexc(TEXT)}" stroke-width="7" stroke-linecap="round" '
            f'stroke-linejoin="round">{inner}</g></svg>')


def arc(cx: float, cy: float, r: float, a0: float, a1: float) -> str:
    x0, y0 = cx + r * math.cos(math.radians(a0)), cy + r * math.sin(math.radians(a0))
    x1, y1 = cx + r * math.cos(math.radians(a1)), cy + r * math.sin(math.radians(a1))
    large = 1 if (a1 - a0) % 360 > 180 else 0
    return f"M{x0:.2f} {y0:.2f} A{r} {r} 0 {large} 1 {x1:.2f} {y1:.2f}"


FUNC_ICONS = {
    "func_shutdown": func_icon(f'<path d="{arc(48, 52, 27, -55, 235)}"/><line x1="48" y1="17" x2="48" y2="47"/>'),
    "func_reset": func_icon(f'<path d="{arc(48, 50, 27, -80, 200)}"/><path d="M30 14 L22 29 L39 32"/>'),
    "func_firmware": func_icon(
        '<line x1="18" y1="28" x2="78" y2="28"/><line x1="18" y1="48" x2="78" y2="48"/>'
        '<line x1="18" y1="68" x2="78" y2="68"/>'
        f'<circle cx="36" cy="28" r="7" fill="{hexc(CANVAS)}"/><circle cx="62" cy="48" r="7" fill="{hexc(CANVAS)}"/>'
        f'<circle cx="44" cy="68" r="7" fill="{hexc(CANVAS)}"/>'),
}

# Menu rows carry their caption inside the icon: rEFInd's own label reads
# "Boot <title> from <volume>", so the menu hides it (hideui label).
OS_ICONS = {
    "os_qindaqt": (icon_qindaqt, "QindaQt"),
    "os_llm-server": (icon_llm_server, "LLM Server"),
    "os_advanced": (icon_advanced, "Advanced"),
}
BIG_ICON = 160      # 1x size of a menu row icon; the tile is 112 of it
SMALL_ICON = 48


def os_icon(svg: str, caption: str, scale: int) -> Image.Image:
    size = BIG_ICON * scale
    tile_px = 112 * scale
    out = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    out.alpha_composite(render_svg(svg, tile_px, tile_px), ((size - tile_px) // 2, 6 * scale))
    label = text_image(caption, inter(17 * scale, "SemiBold"), TEXT)
    out.alpha_composite(label, ((size - label.width) // 2, 6 * scale + tile_px + 12 * scale))
    return out


# ---------------------------------------------------------------- selection --
def rounded(size: tuple[int, int], radius: float, fill, outline=None, width: int = 0,
            inset: float = 0, ss: int = 4) -> Image.Image:
    w, h = size
    big = Image.new("RGBA", (w * ss, h * ss), (0, 0, 0, 0))
    ImageDraw.Draw(big).rounded_rectangle(
        (inset * ss, inset * ss, (w - inset) * ss - 1, (h - inset) * ss - 1),
        radius=radius * ss, fill=fill, outline=outline, width=width * ss)
    return big.resize((w, h), Image.LANCZOS)


def selection(px: int, scale: int) -> Image.Image:
    radius = px * 0.22
    glow = rounded((px, px), radius, fill=ACCENT + (40,), inset=1 * scale)
    ring = rounded((px, px), radius, fill=None, outline=ACCENT + (235,), width=3 * scale,
                   inset=1 * scale)
    return Image.alpha_composite(glow, ring)


# --------------------------------------------------------------------- font --
def refind_font(px: int) -> Image.Image:
    """96 fixed-width glyphs: ASCII 32-126 plus a fallback, one row (rEFInd)."""
    font = plex_mono(px)
    ascent, descent = font.getmetrics()
    cell_w = math.ceil(font.getlength("M"))
    cell_h = ascent + descent
    strip = Image.new("RGBA", (cell_w * 96, cell_h), (0, 0, 0, 0))
    draw = ImageDraw.Draw(strip)
    for i, code in enumerate(list(range(32, 127)) + [ord("?")]):
        # Black glyphs: rEFInd inverts the font itself over a dark background.
        draw.text((i * cell_w, 0), chr(code), font=font, fill=(0, 0, 0, 255))
    return strip


# --------------------------------------------------------------- background --
def cover(img: Image.Image, size: tuple[int, int]) -> Image.Image:
    w, h = size
    k = max(w / img.width, h / img.height)
    resized = img.resize((math.ceil(img.width * k), math.ceil(img.height * k)), Image.LANCZOS)
    left, top = (resized.width - w) // 2, (resized.height - h) // 2
    return resized.crop((left, top, left + w, top + h))


def smoothstep(e0: float, e1: float, x: float) -> float:
    t = min(1.0, max(0.0, (x - e0) / (e1 - e0)))
    return t * t * (3 - 2 * t)


def text_image(text: str, font: ImageFont.FreeTypeFont, rgb, alpha: int = 255) -> Image.Image:
    left, top, right, bottom = font.getbbox(text)
    img = Image.new("RGBA", (right - left + 2, bottom - top + 2), (0, 0, 0, 0))
    ImageDraw.Draw(img).text((-left + 1, -top + 1), text, font=font, fill=rgb + (alpha,))
    return img


def background(size: tuple[int, int], scale: int) -> Image.Image:
    w, h = size
    art = cover(Image.open(ART).convert("RGB"), size).filter(ImageFilter.GaussianBlur(2.2 * scale))

    # Darken toward the canvas colour: lightly at the top, most across the band
    # where rEFInd draws the entry row, its label and the tools.
    shade = Image.new("L", (1, h))
    for y in range(h):
        v = y / h
        a = 0.42 + 0.30 * smoothstep(0.18, 0.40, v) - 0.06 * smoothstep(0.82, 1.0, v)
        shade.putpixel((0, y), round(255 * a))
    shade = shade.resize((w, h))
    vignette = Image.radial_gradient("L").resize((w, h), Image.BILINEAR)
    vignette = vignette.point(lambda p: round(p * 0.35))
    alpha = ImageChops.add(shade, vignette)
    out = Image.composite(Image.new("RGB", size, CANVAS_DEEP), art, alpha).convert("RGBA")

    # Brand, top left, as on the SDDM greeter.
    m = mark(40 * scale, TEXT)
    out.alpha_composite(m, (96 * scale, 40 * scale))
    word = text_image("QindaQt", inter(22 * scale, "SemiBold"), TEXT)
    out.alpha_composite(word, (96 * scale + m.width + 12 * scale,
                               40 * scale + (m.height - word.height) // 2))
    tag = text_image("Qinda Gentoo", inter(15 * scale, "Medium"), MUTED, 200)
    out.alpha_composite(tag, (w - tag.width - 48 * scale, h - tag.height - 36 * scale))

    # rEFInd paints text screens and submenus with the top-left pixel's colour.
    ImageDraw.Draw(out).rectangle((0, 0, 1, 1), fill=CANVAS + (255,))
    return out.convert("RGB")


# ----------------------------------------------------------------- plymouth --
def radial_glow(px: int, rgb, peak: float) -> Image.Image:
    grad = Image.radial_gradient("L").resize((px, px), Image.BICUBIC)
    alpha = grad.point(lambda p: round(255 * peak * (1 - p / 255) ** 2.2))
    img = Image.new("RGBA", (px, px), rgb + (0,))
    img.putalpha(alpha)
    return img


def plymouth_images() -> dict[str, Image.Image]:
    images = {
        "logo.png": mark(640, ACCENT),
        "glow.png": radial_glow(768, ACCENT, 0.22),
        "wordmark.png": text_image("QindaQt", inter(120, "SemiBold"), TEXT),
        "caption-boot.png": text_image("Starting up", inter(44, "Medium"), MUTED),
        "caption-shutdown.png": text_image("Shutting down", inter(44, "Medium"), MUTED),
        "caption-reboot.png": text_image("Restarting", inter(44, "Medium"), MUTED),
        "caption-updates.png": text_image("Installing updates", inter(44, "Medium"), MUTED),
        "progress-track.png": rounded((600, 8), 4, fill=TRACK + (255,)),
        "progress-fill.png": rounded((600, 8), 4, fill=ACCENT + (255,)),
        "entry.png": rounded((720, 88), 22, fill=SURFACE + (242,), outline=BORDER + (255,), width=3),
        "bullet.png": rounded((28, 28), 14, fill=TEXT + (255,)),
    }
    return images


# -------------------------------------------------------------------- build --
def build(out: Path) -> None:
    for name, scale in (("1x", 1), ("2x", 2)):
        base = out / "refind" / name
        (base / "icons").mkdir(parents=True, exist_ok=True)
        background((1920 * scale, 1080 * scale), scale).save(base / "background.png", optimize=True)
        # Selection images are 9/8 of the icon they sit behind, as rEFInd's are.
        selection(BIG_ICON * 9 // 8 * scale, scale).save(base / "selection_big.png")
        selection(64 * scale, scale).save(base / "selection_small.png")
        refind_font(20 * scale).save(base / "font.png")
        for icon, (svg, caption) in OS_ICONS.items():
            os_icon(svg(), caption, scale).save(base / "icons" / f"{icon}.png")
        for icon, svg in FUNC_ICONS.items():
            render_svg(svg, SMALL_ICON * scale, SMALL_ICON * scale).save(base / "icons" / f"{icon}.png")
    ply = out / "plymouth" / "qindaqt"
    ply.mkdir(parents=True, exist_ok=True)
    for name, img in plymouth_images().items():
        img.save(ply / name)


def same_pixels(a: Path, b: Path) -> bool:
    with Image.open(a) as ia, Image.open(b) as ib:
        return ia.size == ib.size and ia.mode == ib.mode and ia.tobytes() == ib.tobytes()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--check", action="store_true", help="verify share/ is current")
    args = parser.parse_args()
    share = ROOT / "share"
    if not args.check:
        build(share)
        return 0
    with tempfile.TemporaryDirectory() as tmp:
        build(Path(tmp))
        stale = []
        for new in sorted(Path(tmp).rglob("*.png")):
            old = share / new.relative_to(tmp)
            if not old.exists() or not same_pixels(old, new):
                stale.append(str(old.relative_to(ROOT)))
        if stale:
            print("build_assets: out of date:\n  " + "\n  ".join(stale), file=sys.stderr)
            return 1
    print("build_assets: share/ is current")
    return 0


if __name__ == "__main__":
    sys.exit(main())

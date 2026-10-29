"""Build the profile hero from real Retro UI Lua-rendered preview assets.

Source previews come from the project's own promo/scripts/generate.py and
tools/preview-instruments.py pipeline. This script only composes those renders.

Usage from the profile repo:
    python scripts/build-retro-ui-showcase.py --promo "../AC Hud/promo"
"""

from __future__ import annotations

import argparse
from pathlib import Path

from PIL import Image, ImageChops, ImageDraw, ImageFilter, ImageFont


PROFILE = Path(__file__).resolve().parent.parent
DEFAULT_PROMO = PROFILE.parent / "AC Hud" / "promo"
OUTPUT = PROFILE / "assets" / "retro-ui-showcase.png"
SIZE = (1600, 760)
PALETTE = {
    "base": "#11111b",
    "mantle": "#181825",
    "surface": "#242536",
    "edge": "#45475a",
    "text": "#cdd6f4",
    "subtext": "#a6adc8",
    "lavender": "#cba6f7",
    "peach": "#fab387",
    "pink": "#f5c2e7",
    "green": "#a6e3a1",
    "blue": "#89b4fa",
}


def font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont:
    fonts = Path("C:/Windows/Fonts")
    choices = (
        [fonts / "seguisb.ttf", fonts / "segoeuib.ttf", fonts / "bahnschrift.ttf"]
        if bold
        else [fonts / "segoeui.ttf", fonts / "seguihis.ttf"]
    )
    for path in choices:
        if path.exists():
            return ImageFont.truetype(str(path), size)
    return ImageFont.truetype("DejaVuSans.ttf", size)


def label(draw: ImageDraw.ImageDraw, xy: tuple[int, int], message: str,
          *, size: int = 20, color: str = "text", bold: bool = False) -> None:
    draw.text(xy, message, font=font(size, bold), fill=PALETTE.get(color, color), anchor="lt")


def capsule(draw: ImageDraw.ImageDraw, xy: tuple[int, int], message: str,
            *, fill: str = "#39324d", fg: str = "lavender", height: int = 36) -> int:
    face = font(16, True)
    width = round(draw.textlength(message, font=face) + 36)
    x, y = xy
    draw.rounded_rectangle((x, y, x + width, y + height), radius=height // 2, fill=fill)
    draw.text((x + 18, y + (height - 16) // 2 - 2), message, font=face,
              fill=PALETTE.get(fg, fg), anchor="lt")
    return width


def add_preview(canvas: Image.Image, path: Path, bounds: tuple[int, int, int, int]) -> None:
    """Isolate pixels drawn by the real Lua renderer and fit without warping."""
    if not path.exists():
        raise FileNotFoundError(f"Required Retro UI preview missing: {path}")
    img = Image.open(path).convert("RGBA")
    if img.getpixel((0, 0))[3] == 0:
        alpha = img.getchannel("A")
    else:
        # Official promo PNGs use a flat #121416 background. Remove only it,
        # while retaining the renderer's translucent antialiasing.
        opaque = img.convert("RGB")
        diff = ImageChops.difference(opaque, Image.new("RGB", opaque.size, (18, 20, 22)))
        alpha = diff.convert("L").point(lambda value: min(255, value * 10))
        img.putalpha(alpha)
    content = alpha.getbbox()
    if not content:
        raise ValueError(f"Preview image contains no rendered content: {path}")
    padding = 4
    content = (max(0, content[0] - padding), max(0, content[1] - padding),
               min(img.width, content[2] + padding), min(img.height, content[3] + padding))
    img = img.crop(content)
    x0, y0, x1, y1 = bounds
    scale = min((x1 - x0) / img.width, (y1 - y0) / img.height)
    size = (max(1, round(img.width * scale)), max(1, round(img.height * scale)))
    img = img.resize(size, Image.Resampling.LANCZOS)
    x = x0 + (x1 - x0 - size[0]) // 2
    y = y0 + (y1 - y0 - size[1]) // 2
    canvas.alpha_composite(img, (x, y))


def main(promo: Path, output: Path) -> None:
    previews = {
        "driving": promo / "instruments" / "analog" / "gt7_steering_dial.png",
        "tach": promo / "instruments" / "analog" / "tachometer_high.png",
        "relative": promo / "instruments" / "digital" / "relative_default.png",
        "map": promo / "instruments" / "digital" / "map_default.png",
    }
    if not (promo / "README.md").exists():
        raise FileNotFoundError(f"Expected the official Retro UI promo directory: {promo}")

    w, h = SIZE
    background = Image.new("RGBA", SIZE, PALETTE["base"])
    light = Image.new("RGBA", SIZE, (0, 0, 0, 0))
    halo = ImageDraw.Draw(light, "RGBA")
    halo.ellipse((400, -240, 1030, 370), fill=(203, 166, 247, 42))
    halo.ellipse((1220, 320, 1900, 1040), fill=(250, 179, 135, 35))
    background = Image.alpha_composite(background, light.filter(ImageFilter.GaussianBlur(90)))
    draw = ImageDraw.Draw(background)

    # Editorial backdrop: small expressive accents, generous negative space.
    draw.arc((325, 188, 790, 648), 225, 325, fill="#5e476b", width=3)
    draw.ellipse((525, 330, 610, 415), fill="#4c3f56")
    draw.ellipse((552, 351, 585, 384), fill=PALETTE["peach"])
    for x in range(50, 560, 24):
        draw.ellipse((x, 722, x + 2, 724), fill="#58516d")

    # Banner header.
    draw.rounded_rectangle((52, 43, 87, 78), radius=12, fill=PALETTE["lavender"])
    label(draw, (64, 50), "/", size=25, color="base", bold=True)
    label(draw, (101, 48), "TOASTBUILDS    /    FEATURED PROJECT", size=18, bold=True)
    label(draw, (1395, 50), "01  /  RETRO UI", size=16, color="subtext", bold=True)
    draw.line((52, 105, 1548, 105), fill="#3b3b51", width=2)

    # Title column.
    label(draw, (65, 149), "ANALOG SOUL   /   DIGITAL PRECISION", size=17,
          color="peach", bold=True)
    label(draw, (56, 205), "RETRO", size=122, bold=True)
    label(draw, (57, 338), "UI.", size=153, bold=True, color="lavender")
    draw.rounded_rectangle((72, 522, 133, 530), radius=4, fill=PALETTE["peach"])
    label(draw, (69, 550), "Motorsport instruments", size=30, bold=True)
    label(draw, (70, 590), "made to feel alive.", size=28, color="subtext")
    next_x = 70
    for s, color in (("ASSETTO CORSA", "lavender"), ("CSP", "peach"), ("OPEN SOURCE", "green")):
        next_x += capsule(draw, (next_x, 660), s, fg=color) + 12

    # Rounded cards support true rendered, reproducible HUD previews.
    panels = [
        (667, 141, 1548, 427),
        (667, 446, 937, 691),
        (950, 446, 1239, 691),
        (1252, 446, 1548, 691),
    ]
    for i, (x0, y0, x1, y1) in enumerate(panels):
        draw.rounded_rectangle((x0 + 4, y0 + 7, x1 + 4, y1 + 7), radius=27, fill="#10101a")
        draw.rounded_rectangle((x0, y0, x1, y1), radius=27,
                               fill=PALETTE["surface"], outline="#49475d", width=2)
        draw.ellipse((x0 + 20, y0 + 25, x0 + 27, y0 + 32), fill=PALETTE["lavender"])

    # Panel headings, numbering and authentic images.
    label(draw, (711, 160), "01  /  DRIVING DISPLAY", size=19, bold=True)
    capsule(draw, (1402, 158), "ANALOG", height=31)
    add_preview(background, previews["driving"], (707, 208, 1504, 404))
    label(draw, (694, 461), "02  /  TACHOMETER", size=17, bold=True)
    label(draw, (976, 461), "03  /  RACE RELATIVE", size=17, bold=True)
    label(draw, (1274, 461), "04  /  TRACK MAP", size=17, bold=True)
    add_preview(background, previews["tach"], (697, 499, 902, 670))
    add_preview(background, previews["relative"], (970, 507, 1219, 672))
    add_preview(background, previews["map"], (1269, 513, 1531, 670))

    draw.line((667, 716, 1548, 716), fill="#434359", width=2)
    label(draw, (674, 727), "ACTUAL LUA INSTRUMENT RENDERS", size=15,
          color="subtext", bold=True)
    label(draw, (1304, 727), "MODULAR  /  LIVE DATA", size=15, color="peach", bold=True)

    output.parent.mkdir(parents=True, exist_ok=True)
    background.convert("RGB").save(output, optimize=True)
    print(f"Built {output} from real Retro UI preview renders ({w} x {h})")
    for key, p in previews.items():
        print(f"  {key}: {p}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--promo", type=Path, default=DEFAULT_PROMO)
    parser.add_argument("--output", type=Path, default=OUTPUT)
    args = parser.parse_args()
    main(args.promo.resolve(), args.output.resolve())

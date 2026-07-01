"""Generate the app icon (assets/icon.png, 1024x1024).

Design: a red "PDF" page fanning out into several documents on a blue
rounded-square background — "one PDF split into several files".

Run:  python assets/make_icon.py
Regenerate whenever you tweak the design; CI turns the PNG into .icns/.ico.
"""
from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont

SS = 4                      # supersampling factor for anti-aliasing
S = 1024                    # final icon size
W = S * SS                  # working canvas size

BLUE_TOP = (37, 99, 235)
BLUE_BOTTOM = (29, 78, 216)
PAGE = (255, 255, 255)
PAGE_BORDER = (208, 213, 221)
TEXT_LINE = (203, 213, 225)
RED = (220, 38, 38)

HERE = Path(__file__).resolve().parent


def _font(size: int) -> ImageFont.FreeTypeFont:
    for name in ("arialbd.ttf", "Arial Bold.ttf", "DejaVuSans-Bold.ttf",
                 "Helvetica.ttc", "seguisb.ttf"):
        try:
            return ImageFont.truetype(name, size)
        except OSError:
            continue
    return ImageFont.load_default()


def _gradient(size: int, top: tuple, bottom: tuple) -> Image.Image:
    grad = Image.new("RGB", (1, size))
    for y in range(size):
        f = y / (size - 1)
        grad.putpixel((0, y), tuple(
            round(top[i] + (bottom[i] - top[i]) * f) for i in range(3)))
    return grad.resize((size, size))


def _page(w: int, h: int, *, header: bool) -> Image.Image:
    """A single white document, optionally with a red PDF header."""
    img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    r = 22 * SS
    d.rounded_rectangle((0, 0, w - 1, h - 1), radius=r,
                        fill=PAGE, outline=PAGE_BORDER, width=2 * SS)
    if header:
        pad = 26 * SS
        bar_h = 58 * SS
        d.rounded_rectangle((pad, pad, w - pad, pad + bar_h),
                            radius=12 * SS, fill=RED)
        f = _font(40 * SS)
        text = "PDF"
        tb = d.textbbox((0, 0), text, font=f)
        tw, th = tb[2] - tb[0], tb[3] - tb[1]
        d.text(((w - tw) / 2 - tb[0], pad + (bar_h - th) / 2 - tb[1]),
               text, font=f, fill=(255, 255, 255))
        y = pad + bar_h + 40 * SS
    else:
        y = 44 * SS
    # content lines
    lx0, lx1 = 30 * SS, w - 30 * SS
    for i in range(5):
        end = lx1 if i % 2 == 0 else lx1 - 60 * SS
        d.rounded_rectangle((lx0, y, end, y + 14 * SS),
                            radius=7 * SS, fill=TEXT_LINE)
        y += 40 * SS
    return img


def _paste_rotated(base: Image.Image, page: Image.Image,
                   angle: float, center: tuple) -> None:
    # soft drop shadow
    shadow = Image.new("RGBA", page.size, (0, 0, 0, 0))
    ImageDraw.Draw(shadow).rounded_rectangle(
        (0, 0, page.width - 1, page.height - 1), radius=22 * SS,
        fill=(15, 23, 42, 120))
    shadow = shadow.rotate(angle, expand=True, resample=Image.BICUBIC)
    shadow = shadow.filter(ImageFilter.GaussianBlur(10 * SS))
    rot = page.rotate(angle, expand=True, resample=Image.BICUBIC)
    sx = round(center[0] - shadow.width / 2)
    sy = round(center[1] - shadow.height / 2 + 10 * SS)
    base.alpha_composite(shadow, (sx, sy))
    px = round(center[0] - rot.width / 2)
    py = round(center[1] - rot.height / 2)
    base.alpha_composite(rot, (px, py))


def main() -> None:
    canvas = Image.new("RGBA", (W, W), (0, 0, 0, 0))

    # blue rounded-square background
    margin = 40 * SS
    mask = Image.new("L", (W, W), 0)
    ImageDraw.Draw(mask).rounded_rectangle(
        (margin, margin, W - margin, W - margin),
        radius=200 * SS, fill=255)
    bg = _gradient(W, BLUE_TOP, BLUE_BOTTOM).convert("RGBA")
    canvas.paste(bg, (0, 0), mask)

    pw, ph = 360 * SS, 460 * SS
    cx, cy = W / 2, W / 2 + 6 * SS
    _paste_rotated(canvas, _page(pw, ph, header=False), 15, (cx + 66 * SS, cy))
    _paste_rotated(canvas, _page(pw, ph, header=False), -15, (cx - 66 * SS, cy))
    _paste_rotated(canvas, _page(pw, ph, header=True), 0, (cx, cy - 4 * SS))

    out = canvas.resize((S, S), Image.LANCZOS)
    dest = HERE / "icon.png"
    out.save(dest)
    print(f"Wrote {dest} ({out.size[0]}x{out.size[1]})")


if __name__ == "__main__":
    main()

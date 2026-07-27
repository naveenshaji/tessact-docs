#!/usr/bin/env python3
"""Composite app screenshots onto the docs' macOS wallpaper treatment (admin-v2 style).

Canvas is always 1600x1000. The screenshot is fit within a 1440x900 box, centered,
with rounded corners and a soft drop shadow over the reconstructed Tahoe-blue wallpaper.
"""
import sys
import numpy as np
import cv2
from PIL import Image, ImageDraw, ImageFilter

import os
REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DOCS = REPO
BG_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "wallpaper-1600x1000.png")

CANVAS_W, CANVAS_H = 1600, 1000
BOX_W, BOX_H = 1440, 900
RADIUS = 14


def build_wallpaper():
    """Reconstruct the wallpaper by inpainting the window area of an existing admin-v2 image."""
    src = cv2.imread(f"{DOCS}/images/admin/admin-overview-live-v2.jpg")
    mask = np.zeros(src.shape[:2], np.uint8)
    # window rect (80,50)-(1519,949) expanded to swallow the shadow
    mask[30:970, 56:1544] = 255
    out = cv2.inpaint(src, mask, 3, cv2.INPAINT_TELEA)
    # smooth the inpainted interior heavily; keep the untouched border as-is
    blurred = cv2.GaussianBlur(out, (0, 0), 40)
    m3 = cv2.GaussianBlur(mask, (0, 0), 15).astype(np.float32)[..., None] / 255.0
    final = (blurred * m3 + out * (1 - m3)).astype(np.uint8)
    cv2.imwrite(BG_PATH, final)
    print("wallpaper written", final.shape)


def treat(in_path, out_path, quality=88, mode="desktop"):
    shot = Image.open(in_path).convert("RGB")
    sw, sh = shot.size
    if mode == "compact":
        # window at native-ish size, canvas hugs it with proportional margins
        w = min(sw, BOX_W)
        h = round(sh * w / sw)
        cw, ch = w + 160, h + 100
    else:
        scale = min(BOX_W / sw, BOX_H / sh)
        w, h = round(sw * scale), round(sh * scale)
        cw, ch = CANVAS_W, CANVAS_H
    bg = Image.open(BG_PATH).convert("RGB")
    bs = max(cw / bg.width, ch / bg.height)
    bg = bg.resize((round(bg.width * bs), round(bg.height * bs)), Image.LANCZOS)
    bg = bg.crop(((bg.width - cw) // 2, (bg.height - ch) // 2,
                  (bg.width - cw) // 2 + cw, (bg.height - ch) // 2 + ch))
    shot = shot.resize((w, h), Image.LANCZOS)
    x, y = (cw - w) // 2, (ch - h) // 2

    # drop shadow
    shadow = Image.new("RGBA", (cw, ch), (0, 0, 0, 0))
    sd = ImageDraw.Draw(shadow)
    sd.rounded_rectangle([x, y + 10, x + w, y + h + 10], RADIUS, fill=(10, 20, 40, 90))
    shadow = shadow.filter(ImageFilter.GaussianBlur(22))
    canvas = Image.alpha_composite(bg.convert("RGBA"), shadow)

    # rounded-corner window
    m = Image.new("L", (w, h), 0)
    ImageDraw.Draw(m).rounded_rectangle([0, 0, w - 1, h - 1], RADIUS, fill=255)
    canvas.paste(shot, (x, y), m)
    canvas.convert("RGB").save(out_path, quality=quality)
    print("wrote", out_path, f"{cw}x{ch} (window {w}x{h})")


def glass_blur_except(in_path, out_path, keep_box, blur_radius=18, dim=0.92, ring=True):
    """Frosted-glass blur over the whole screenshot except keep_box, which stays sharp
    (with a subtle highlight ring). keep_box is (x1,y1,x2,y2) or a list of such boxes,
    in source pixels."""
    src = Image.open(in_path).convert("RGB")
    frosted = src.filter(ImageFilter.GaussianBlur(blur_radius))
    frosted = frosted.point(lambda p: int(p * dim))
    boxes = [keep_box] if isinstance(keep_box[0], (int, float)) else list(keep_box)
    pad = 10
    m = Image.new("L", src.size, 0)
    md = ImageDraw.Draw(m)
    for x1, y1, x2, y2 in boxes:
        md.rounded_rectangle([x1 - pad, y1 - pad, x2 + pad, y2 + pad], 18, fill=255)
    m = m.filter(ImageFilter.GaussianBlur(2))
    out = Image.composite(src, frosted, m)
    if ring:
        layer = Image.new("RGBA", out.size, (0, 0, 0, 0))
        ld = ImageDraw.Draw(layer)
        for x1, y1, x2, y2 in boxes:
            ld.rounded_rectangle([x1 - pad - 2, y1 - pad - 2, x2 + pad + 2, y2 + pad + 2], 20,
                                 outline=(255, 255, 255, 130), width=2)
        out = Image.alpha_composite(out.convert("RGBA"), layer).convert("RGB")
    out.save(out_path)
    print("glass-blurred", out_path, "kept", boxes)


if __name__ == "__main__":
    if sys.argv[1] == "bg":
        build_wallpaper()
    else:
        treat(sys.argv[1], sys.argv[2], mode=(sys.argv[3] if len(sys.argv) > 3 else "desktop"))

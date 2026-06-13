#!/usr/bin/env python3
"""
photo_display.py — Display a photo on GDEY029Z95 e-paper.

Red-channel detection is ON by default. Use --bw for pure black/white.

Usage:
    python3 photo_display.py photo.jpg                       # Atkinson + red
    python3 photo_display.py photo.jpg --dither floyd        # Floyd + red
    python3 photo_display.py photo.jpg --bw                  # B/W only
    python3 photo_display.py photo.jpg --bw --dither floyd   # B/W Floyd
"""

import sys
import argparse
import numpy as np
from PIL import Image, ImageFilter

from epd_driver import (
    WIDTH, HEIGHT, init, image_to_buffer, display, sleep_display
)


def prepare_image(filename: str):
    """Load, orient, crop to display aspect ratio, return RGB float array (0-1)."""
    img = Image.open(filename).convert("RGB")
    if img.width > img.height:
        img = img.rotate(90, expand=True)
    # Centre-crop to 128:296 aspect
    aspect = WIDTH / HEIGHT
    w, h = img.size
    if w / h > aspect:
        new_w = int(h * aspect)
        off = (w - new_w) // 2
        img = img.crop((off, 0, off + new_w, h))
    else:
        new_h = int(w / aspect)
        off = (h - new_h) // 2
        img = img.crop((0, off, w, off + new_h))
    img = img.resize((WIDTH, HEIGHT), Image.LANCZOS)
    return np.array(img, dtype=np.float32) / 255.0


def enhance(img: np.ndarray, contrast: float = 1.4) -> np.ndarray:
    img = (img - 0.5) * contrast + 0.5
    return np.clip(img, 0, 1)


def unsharp_mask(img: np.ndarray, radius: int = 1, amount: float = 0.6) -> np.ndarray:
    blurred = Image.fromarray((img * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(radius=radius))
    blurred_arr = np.array(blurred, dtype=np.float32) / 255.0
    return np.clip(img + (img - blurred_arr) * amount, 0, 1)


def detect_red(rgb: np.ndarray, hue_lo: float = 345, hue_hi: float = 20,
               sat_min: float = 0.30, val_min: float = 0.20) -> np.ndarray:
    r, g, b = rgb[:,:,0], rgb[:,:,1], rgb[:,:,2]
    mx = np.maximum(np.maximum(r, g), b)
    mn = np.minimum(np.minimum(r, g), b)
    diff = mx - mn
    h = np.zeros_like(r)
    s = np.zeros_like(r)
    v = mx.copy()
    s[mx > 0] = diff[mx > 0] / mx[mx > 0]
    red_m = (diff > 0) & (mx == r)
    grn_m = (diff > 0) & (mx == g)
    blu_m = (diff > 0) & (mx == b)
    h[red_m] = (60.0 * ((g[red_m] - b[red_m]) / diff[red_m])) % 360
    h[grn_m] = 60.0 * ((b[grn_m] - r[grn_m]) / diff[grn_m]) + 120.0
    h[blu_m] = 60.0 * ((r[blu_m] - g[blu_m]) / diff[blu_m]) + 240.0
    if hue_lo > hue_hi:
        hue_ok = (h >= hue_lo) | (h <= hue_hi)
    else:
        hue_ok = (h >= hue_lo) & (h <= hue_hi)
    return hue_ok & (s >= sat_min) & (v >= val_min)


def atkinson_dither(gray: np.ndarray) -> Image.Image:
    h, w = gray.shape
    img = gray.copy().astype(np.float32)
    for y in range(h):
        for x in range(w):
            old = img[y, x]
            new = 255.0 if old > 127 else 0.0
            img[y, x] = new
            err = old - new
            if x + 1 < w:      img[y, x+1] += err/8
            if x + 2 < w:      img[y, x+2] += err/8
            if y + 1 < h:
                if x > 0:       img[y+1, x-1] += err/8
                img[y+1, x]   += err/8
                if x+1 < w:     img[y+1, x+1] += err/8
            if y + 2 < h:       img[y+2, x]   += err/8
    return Image.fromarray(np.clip(img, 0, 255).astype(np.uint8), mode="L").convert("1")


def floyd_steinberg(gray: np.ndarray) -> Image.Image:
    return Image.fromarray(gray.astype(np.uint8), mode="L").convert("1", dither=Image.FLOYDSTEINBERG)


def main():
    parser = argparse.ArgumentParser(description="Display a photo on e-paper")
    parser.add_argument("filename", help="Path to image file")
    parser.add_argument("--dither", choices=["atkinson", "floyd"], default="atkinson")
    parser.add_argument("--bw", action="store_true", help="B/W only (disable red channel)")
    parser.add_argument("--red-hue-lo", type=float, default=345)
    parser.add_argument("--red-hue-hi", type=float, default=20)
    parser.add_argument("--red-sat", type=float, default=0.30)
    parser.add_argument("--red-val", type=float, default=0.20)
    parser.add_argument("--contrast", type=float, default=1.4)
    parser.add_argument("--no-sharpen", action="store_true")
    args = parser.parse_args()

    print("Loading image...")
    rgb = prepare_image(args.filename)
    rgb = enhance(rgb, args.contrast)
    if not args.no_sharpen:
        rgb = unsharp_mask(rgb)

    gray = np.mean(rgb, axis=2) * 255.0
    red_mask = None

    if not args.bw:
        print("Detecting red channel...")
        red_mask = detect_red(rgb, args.red_hue_lo, args.red_hue_hi,
                              args.red_sat, args.red_val)
        pct = red_mask.sum() / red_mask.size * 100
        print(f"  Red pixels: {pct:.1f}%")
        gray[red_mask] = 255.0  # keep red areas white in BW plane

    name = "Atkinson" if args.dither == "atkinson" else "Floyd-Steinberg"
    print(f"Dithering ({name})...")
    bw = (atkinson_dither if args.dither == "atkinson" else floyd_steinberg)(gray)

    red_buf = [0] * (WIDTH * HEIGHT // 8)
    if red_mask is not None:
        rb = []
        for y in range(HEIGHT - 1, -1, -1):
            for xb in range(WIDTH // 8):
                byte = 0
                for bit in range(8):
                    if red_mask[y, xb * 8 + bit]:
                        byte |= (0x80 >> bit)
                rb.append(byte)
        red_buf = rb

    bw_buf = [~b & 0xFF for b in image_to_buffer(bw)]

    print("Initialising display...")
    init()
    print("Refreshing...")
    display(bw_buf, red_buf)
    print("Sleeping...")
    sleep_display()
    print("Done ✓")


if __name__ == "__main__":
    main()

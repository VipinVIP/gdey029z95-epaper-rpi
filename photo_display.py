#!/usr/bin/env python3
"""
photo_display.py — Display a photo on GDEY029Z95 e-paper.

Usage:
    python3 photo_display.py photo.jpg              # Atkinson dither (default)
    python3 photo_display.py photo.jpg --dither floyd  # Floyd-Steinberg
"""

import sys
import argparse
import numpy as np
from PIL import Image

from epd_driver import (
    WIDTH, HEIGHT, init, image_to_buffer, display, sleep_display
)


def prepare_image(filename: str) -> np.ndarray:
    """Load, orient to portrait, thumbnail, centre on white. Return grayscale float array 0-255."""
    img = Image.open(filename).convert("RGB")
    if img.width > img.height:
        img = img.rotate(90, expand=True)
    img.thumbnail((WIDTH, HEIGHT))

    canvas = Image.new("RGB", (WIDTH, HEIGHT), (255, 255, 255))
    xoff = (WIDTH - img.width) // 2
    yoff = (HEIGHT - img.height) // 2
    canvas.paste(img, (xoff, yoff))

    gray = canvas.convert("L")
    return np.array(gray, dtype=np.float32)


def floyd_steinberg(gray: np.ndarray) -> Image.Image:
    """Floyd-Steinberg dither (PIL built-in)."""
    return Image.fromarray(gray.astype(np.uint8), mode="L").convert("1", dither=Image.FLOYDSTEINBERG)


def atkinson_dither(gray: np.ndarray) -> Image.Image:
    """
    Atkinson error diffusion dither.

    Distributes 3/4 of error to 6 neighbours (1/8 each), drops 1/4.
    Results in a sharper, contrastier image than Floyd-Steinberg.
    """
    h, w = gray.shape
    img = gray.copy()

    for y in range(h):
        for x in range(w):
            old = img[y, x]
            new = 255.0 if old > 127 else 0.0
            img[y, x] = new
            err = old - new

            if x + 1 < w:
                img[y, x + 1] += err / 8
            if x + 2 < w:
                img[y, x + 2] += err / 8
            if y + 1 < h:
                if x > 0:
                    img[y + 1, x - 1] += err / 8
                img[y + 1, x] += err / 8
                if x + 1 < w:
                    img[y + 1, x + 1] += err / 8
            if y + 2 < h:
                img[y + 2, x] += err / 8

    img = np.clip(img, 0, 255).astype(np.uint8)
    return Image.fromarray(img, mode="L").convert("1")


def main():
    parser = argparse.ArgumentParser(description="Display a photo on e-paper")
    parser.add_argument("filename", help="Path to image file")
    parser.add_argument("--dither", choices=["atkinson", "floyd"],
                        default="atkinson",
                        help="Dithering method (default: atkinson)")
    args = parser.parse_args()

    print("Loading image...")
    gray = prepare_image(args.filename)

    if args.dither == "floyd":
        print("Dithering (Floyd-Steinberg)...")
        bw = floyd_steinberg(gray)
    else:
        print("Dithering (Atkinson)...")
        bw = atkinson_dither(gray)

    bw_buf = [~b & 0xFF for b in image_to_buffer(bw)]
    red_buf = [0] * (WIDTH * HEIGHT // 8)

    print("Initialising display...")
    init()
    print("Refreshing...")
    display(bw_buf, red_buf)
    print("Sleeping...")
    sleep_display()
    print("Done ✓")


if __name__ == "__main__":
    main()

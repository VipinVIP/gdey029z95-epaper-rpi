#!/usr/bin/env python3
"""
photo_display.py — Display a photo on GDEY029Z95 3-colour e-paper (B/W only).

The photo is Floyd-Steinberg dithered to 1-bit black/white.

Usage:
    python3 photo_display.py photo.jpg
"""

import sys
from PIL import Image

from epd_driver import (
    WIDTH, HEIGHT, init, image_to_buffer, display, sleep_display
)


def prepare_image(filename: str) -> Image.Image:
    """Load, orient to portrait, thumbnail, and centre on a white canvas."""
    img = Image.open(filename).convert("RGB")
    if img.width > img.height:
        img = img.rotate(90, expand=True)
    img.thumbnail((WIDTH, HEIGHT))

    canvas = Image.new("RGB", (WIDTH, HEIGHT), (255, 255, 255))
    xoff = (WIDTH - img.width) // 2
    yoff = (HEIGHT - img.height) // 2
    canvas.paste(img, (xoff, yoff))
    return canvas


def main():
    if len(sys.argv) != 2:
        print("Usage: python3 photo_display.py photo.jpg")
        return

    filename = sys.argv[1]
    print("Loading image...")
    canvas = prepare_image(filename)

    print("Creating B/W plane (Floyd-Steinberg dither)...")
    bw = canvas.convert("1", dither=Image.FLOYDSTEINBERG)

    bw_buf = [~b & 0xFF for b in image_to_buffer(bw)]
    red_buf = [0] * (WIDTH * HEIGHT // 8)   # all white = no red

    print("Initialising display...")
    init()

    print("Refreshing...")
    display(bw_buf, red_buf)

    print("Sleeping...")
    sleep_display()

    print("Done ✓")


if __name__ == "__main__":
    main()

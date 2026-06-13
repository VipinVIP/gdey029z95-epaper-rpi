#!/usr/bin/env python3
"""
text_demo.py — Display text on the GDEY029Z95 e-paper.

Usage:
    python3 text_demo.py
"""

from epd_driver import (
    init, image_to_buffer, display, sleep_display,
    prepare_text_image
)


def main():
    bw, red = prepare_text_image(
        text_bw="HELLO",
        text_red="WORLD",
    )

    bw_buf = [~b & 0xFF for b in image_to_buffer(bw)]
    red_buf = image_to_buffer(red)

    print("Initialising display...")
    init()

    print("Updating display...")
    display(bw_buf, red_buf)

    print("Sleeping...")
    sleep_display()

    print("Done — black HELLO, red WORLD on white background.")


if __name__ == "__main__":
    main()

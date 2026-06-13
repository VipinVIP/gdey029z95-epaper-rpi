#!/usr/bin/env python3
"""
epd_driver.py — Core driver for GDEY029Z95 2.9" 3-color e-paper (Raspberry Pi).

Display: Good Display GDEY029Z95 / Waveshare 2.9" B/W/R
Controller: SSD1680
Resolution: 128×296 pixels

Wiring (Raspberry Pi → DESPI-C02 adapter):
    ┌──────────────┬──────────────────────────────┐
    │ DESPI-C02    │ Raspberry Pi                 │
    ├──────────────┼──────────────────────────────┤
    │ 3.3V         │ Pin 1 (3.3V)                 │
    │ GND          │ Pin 6 (GND)                  │
    │ SCK          │ Pin 23 (GPIO11 / SPI0 SCLK)  │
    │ SDI (MOSI)   │ Pin 19 (GPIO10 / SPI0 MOSI)  │
    │ CS           │ Pin 24 (GPIO8 / SPI0 CE0)    │
    │ D/C          │ Pin 22 (GPIO25)              │
    │ RES          │ Pin 11 (GPIO17)              │
    │ BUSY         │ Pin 18 (GPIO24)              │
    └──────────────┴──────────────────────────────┘
"""

from PIL import Image
import spidev
from gpiozero import OutputDevice, InputDevice
from time import sleep

WIDTH = 128
HEIGHT = 296

# GPIO
RST = OutputDevice(17)
DC = OutputDevice(25)
BUSY = InputDevice(24)

# SPI
spi = spidev.SpiDev()
spi.open(0, 0)
spi.max_speed_hz = 4_000_000
spi.mode = 0


# ── Low-level helpers ────────────────────────────────────────────────────────

def wait_busy():
    while BUSY.value == 1:
        sleep(0.01)


def _cmd(c: int):
    DC.off()
    spi.xfer2([c & 0xFF])


def _data(d: int):
    DC.on()
    spi.xfer2([d & 0xFF])


def _data_bulk(buf: list):
    DC.on()
    chunk = 4096
    for i in range(0, len(buf), chunk):
        spi.xfer2(buf[i:i + chunk])


# ── Initialization ────────────────────────────────────────────────────────────

def init():
    """Initialise the display controller (SSD1680)."""
    RST.off()
    sleep(0.01)
    RST.on()
    sleep(0.01)
    wait_busy()

    _cmd(0x12)  # SWRESET
    wait_busy()

    _cmd(0x01)  # Driver output control
    _data((HEIGHT - 1) & 0xFF)
    _data((HEIGHT - 1) >> 8)
    _data(0x00)

    _cmd(0x11)  # Data entry mode: X-increment, Y-decrement
    _data(0x01)

    _cmd(0x44)  # RAM X range
    _data(0x00)
    _data(WIDTH // 8 - 1)

    _cmd(0x45)  # RAM Y range
    _data((HEIGHT - 1) & 0xFF)
    _data((HEIGHT - 1) >> 8)
    _data(0x00)
    _data(0x00)

    _cmd(0x3C)  # Border waveform
    _data(0x05)

    _cmd(0x18)  # Internal temperature sensor
    _data(0x80)

    _cmd(0x4E)  # RAM X counter
    _data(0x00)

    _cmd(0x4F)  # RAM Y counter
    _data((HEIGHT - 1) & 0xFF)
    _data((HEIGHT - 1) >> 8)

    wait_busy()


# ── Buffer conversion ─────────────────────────────────────────────────────────

def image_to_buffer(img: Image.Image) -> list:
    """
    Convert a PIL 1-bit image to a display buffer byte array.

    Y-decrement scan order: sends bottom row first so the image appears
    right-side up on the display.

    Display convention (tested with hello3.py):
        bit=1 → white pixel
        bit=0 → black pixel
    """
    pixels = img.load()
    buf = []
    for y in range(HEIGHT - 1, -1, -1):
        for xb in range(WIDTH // 8):
            byte = 0
            for bit in range(8):
                x = xb * 8 + bit
                if pixels[x, y] == 0:  # PIL black/drawn → set bit
                    byte |= (0x80 >> bit)
            buf.append(byte)
    return buf


# ── Display update ────────────────────────────────────────────────────────────

def display(bw_buf: list, red_buf: list):
    """
    Send both buffers to the display and trigger a full refresh.

    Args:
        bw_buf:  Black/White plane buffer (4736 bytes).
                 bit=1 → white, bit=0 → black.
        red_buf: Red plane buffer (4736 bytes).
                 bit=1 → red pixel, bit=0 → transparent.
    """
    _cmd(0x24)        # BW RAM
    _data_bulk(bw_buf)

    _cmd(0x26)        # Red RAM
    _data_bulk(red_buf)

    _cmd(0x22)
    _data(0xF7)       # Full refresh mode

    _cmd(0x20)        # Activate
    wait_busy()


def sleep_display():
    """Put the display into deep sleep (ultra-low power)."""
    _cmd(0x10)
    _data(0x01)
    sleep(0.1)


def prepare_text_image(text_bw: str, text_red: str = "") -> tuple:
    """
    Create a display image with B/W and optional red text.

    Args:
        text_bw:  Text rendered in black (top area).
        text_red: Text rendered in red (middle area).

    Returns:
        (bw_image, red_image) as PIL 1-bit images.
        Pass these to image_to_buffer() then display().
    """
    from PIL import ImageDraw, ImageFont

    bw = Image.new("1", (WIDTH, HEIGHT), 1)
    red = Image.new("1", (WIDTH, HEIGHT), 1)

    dbw = ImageDraw.Draw(bw)
    dred = ImageDraw.Draw(red)

    try:
        font = ImageFont.truetype(
            "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 22)
    except OSError:
        font = ImageFont.load_default()

    if text_bw:
        dbw.text((10, 40), text_bw, fill=0, font=font)
    if text_red:
        dred.text((10, 130), text_red, fill=0, font=font)

    return bw, red

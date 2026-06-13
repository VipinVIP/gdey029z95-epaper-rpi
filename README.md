# GDEY029Z95 E-Paper Display — Raspberry Pi

Python driver and utilities for the **Good Display GDEY029Z95** / Waveshare-compatible 2.9″ 3‑colour (black/white/red) e‑paper display, driven by an **SSD1680** controller via SPI on a **Raspberry Pi**.

## Wiring

| DESPI‑C02 (adapter) | Raspberry Pi               |
|---------------------|----------------------------|
| 3.3V                | Pin 1 (3.3V)               |
| GND                 | Pin 6 (GND)                |
| SCK                 | Pin 23 (GPIO11 / SPI0 SCLK)|
| SDI                 | Pin 19 (GPIO10 / SPI0 MOSI)|
| CS                  | Pin 24 (GPIO8 / SPI0 CE0)  |
| D/C                 | Pin 22 (GPIO25)            |
| RES                 | Pin 11 (GPIO17)            |
| BUSY                | Pin 18 (GPIO24)            |

> SPI0 uses default pins (SCLK=GPIO11, MOSI=GPIO10, CE0=GPIO8) — handled automatically by spidev. Only D/C, RES, and BUSY need explicit GPIO wiring.
>
> **⚠ The e‑paper module is 3.3V only — never connect 5V.**

## Files

| File | Description |
|------|-------------|
| [`epd_driver.py`](epd_driver.py) | Core driver — init, buffer conversion, display refresh, sleep |
| [`text_demo.py`](text_demo.py)   | Display black/red text on white background |
| [`photo_display.py`](photo_display.py) | Display photos with Floyd–Steinberg dithering + optional red‑channel detection |

## Quick Start

```bash
# Install dependencies
sudo apt install python3-pil python3-numpy
sudo pip3 install spidev gpiozero

# Text demo
python3 text_demo.py

# Photo display (B/W dithered)
python3 photo_display.py photo.jpg              # Atkinson (default)
python3 photo_display.py photo.jpg --dither floyd  # Floyd-Steinberg
```

## Files

| File | Description |
|------|-------------|
| [`epd_driver.py`](epd_driver.py) | Core driver — init, buffer conversion, display refresh, sleep |
| [`text_demo.py`](text_demo.py)   | Display black/red text on white background |
| [`photo_display.py`](photo_display.py) | Display photos with Floyd–Steinberg dithering |

## Display Controller

- **SSD1680** — 176×296 Red/Black/White Active Matrix EPD Driver
- SPI mode 0, up to 4 MHz
- Dual RAM: B/W (0x24) and Red (0x26)
- Full refresh trigger: `0x22` → `0xF7` → `0x20`

## License

MIT

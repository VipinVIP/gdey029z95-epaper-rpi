# GDEY029Z95 E-Paper Display — Raspberry Pi

Python driver and utilities for the **Good Display GDEY029Z95** 2.9″ 3‑colour (black/white/red) e‑paper display, driven by an **SSD1680** controller via SPI on a **Raspberry Pi**.

<br>
<img width="296" height="128" alt="example" src="https://github.com/user-attachments/assets/379e7c5e-17fe-4cf1-a1c3-fd123e927731"/>

## Materials

- **Display:** [GoodDisplay 2.9″ 296×128 Tri-color E-ink Screen](https://robu.in/product/gooddisplay-2-9-inch-296x128-tri-color-e-ink-screen-e-paper-display/)
- **Adapter:** [DESPI-C02 E-Paper HAT Connection Board](https://robu.in/product/e-paper-hat-connection-adapter-board/)


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

> SPI0 uses default pins — handled automatically by spidev. Only D/C (GPIO25), RES (GPIO17), and BUSY (GPIO24) need explicit GPIO wiring.
>
>
> **⚠ The e‑paper module is 3.3V only — never connect 5V.**
>
> **⚠ On the DESPI-C02 board, set the switch to the 0.47 position (not 2.2).**

## Files

| File | Description |
|------|-------------|
| [`epd_driver.py`](epd_driver.py) | Core driver — init, buffer conversion, display refresh, sleep |
| [`text_demo.py`](text_demo.py)   | Display black/red text on white background |
| [`photo_display.py`](photo_display.py) | Display photos with Atkinson dithering (default) or Floyd-Steinberg |

## Quick Start

```bash
# Install dependencies
sudo apt install python3-pil python3-numpy
sudo pip3 install spidev gpiozero

# Text demo
python3 text_demo.py

# Photo display
python3 photo_display.py photo.jpg                 # Atkinson + red (default)
python3 photo_display.py photo.jpg --dither floyd  # Floyd + red
python3 photo_display.py photo.jpg --bw            # B/W only (Atkinson)
python3 photo_display.py photo.jpg --bw --dither floyd  # B/W Floyd
```

## Display Controller

- **SSD1680** — 176×296 Red/Black/White Active Matrix EPD Driver
- SPI mode 0, up to 4 MHz
- Dual RAM: B/W (0x24) and Red (0x26)
- Full refresh trigger: `0x22` → `0xF7` → `0x20`

## License

MIT

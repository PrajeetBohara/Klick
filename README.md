# Klick

Professional desktop auto-clicker and auto-typer for Windows.

Built for accessibility, repetitive productivity tasks, and controlled local automation. It is **not** designed to evade anti-cheat, monitoring, or detection systems.

## Features

### Auto Clicker / Scroll
- Fixed or random interval (hours / minutes / seconds / ms min–max)
- Click or scroll action
- Left, right, or middle mouse button
- Single, double, or triple click
- Scroll up/down with notch count
- Current cursor or fixed coordinates
- Unlimited or fixed repeat count
- Start delay and timed auto-stop

### Auto Typer
- Custom text with character or word pacing
- Fixed or random type interval
- Start delay, repeat options, optional Enter
- Timed auto-stop

### Custom Combo
- Build sequences of click, type, scroll, and wait
- Shared between-step interval (fixed or random)
- Repeat and auto-stop controls

### Jiggler
- Unpredictable cursor movement within a radius
- Random timing between bursts
- Optional pull-back to start and restore on stop

### Controls
- Start / Stop from the UI
- Global hotkeys (defaults: F6 start/stop, F7 emergency stop)
- Persistent settings across launches
- Live status, counters, and elapsed time
- Random intervals use min/max sliders (1 ms–10 s) plus fine-tune fields

## Requirements

- Windows 10/11
- Python 3.10+

## Setup

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python main.py
```

## Usage notes

- Run as a normal user for most apps; some elevated windows may ignore simulated input unless Klick is also elevated.
- Global hotkeys work while another window is focused.
- Use this only where you are allowed to automate input (your own machine, accessibility, approved workflows).

## License

MIT

# Klick

Professional desktop auto-clicker and auto-typer for Windows.

Built for accessibility, repetitive productivity tasks, and controlled local automation. It is **not** designed to evade anti-cheat, monitoring, or detection systems.

## Features

### Auto Clicker / Scroll
- Switch between **Click** and **Scroll** (irrelevant options are hidden automatically)
- **Interval**: Fixed or Random, with min/max **sliders** (1 ms–10 s) plus H/M/S/MS fine-tune
- Clear **Apply delay after** label (each click / each scroll)
- Mouse button: Left / Right / Middle
- Click type: Single / Double / Triple
- Scroll: Up / Down + notch count
- Position: Current cursor or Fixed point + Pick Position
- **Repeat**: Unlimited (Count hidden) or Fixed Count
- Start delay and optional **Auto Stop** timer

### Auto Typer
- **Text to Type** field with character or word pacing
- Fixed or Random type interval (same slider/controls as clicker)
- Repeat: Once / Fixed Count / Unlimited
- Optional Enter after each run
- Start delay and Auto Stop
- **Optional Fixed text mode** add-on:
  - Types the text once and stops when finished
  - Shows estimated total time from your settings
  - Live progress bar and time remaining while typing

### Custom Combo
- Build ordered steps: **Click**, **Type**, **Scroll**, **Wait**
- Step-specific options only show when relevant
- Between-steps interval (Fixed or Random)
- Repeat and Auto Stop controls

### Jiggler
- Irregular cursor movement within a radius
- Random or fixed time between bursts
- Keep near start / restore cursor on stop
- Start delay and Auto Stop

### App controls & UI
- Start / Stop buttons with **hotkey tooltips** on hover
- Global hotkeys (defaults: **F6** start/stop, **F7** emergency stop) — editable in Settings
- Live status, counters, and elapsed time
- **Always on top** option in Settings (persisted)
- In-app **Help** tab with a beginner guide to every control
- Header logo from `assets/text_logo.png`
- Window / taskbar icon from `assets/klick_logo.png`
- Settings saved to `~/.klick/settings.json`

## Requirements

- Windows 10/11
- Python 3.10+

## Setup

```powershell
cd "e:\Software Projects\Klick"
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python main.py
```

## Quick start

1. Open the tab you need (Auto Clicker, Auto Typer, Custom, or Jiggler).
2. Configure interval, action, and repeat options.
3. Set a **Start delay** if you need time to focus another window.
4. Press **Start**, or **F6**.
5. Press **Stop**, or **F7** for emergency stop.
6. Read the **Help** tab for a full walkthrough of each control.
7. Optional: Settings → **Always on top** to keep Klick above other windows.

## Brand assets

Place logos in `assets/`:

| File | Used for |
|------|----------|
| `text_logo.png` | Header logo |
| `klick_logo.png` | Window title bar / taskbar icon |

Header size defaults are in `app/ui/logo.py` (`HEADER_LOGO_HEIGHT`, `HEADER_LOGO_MAX_WIDTH`).

## Usage notes

- Run as a normal user for most apps; some elevated windows may ignore simulated input unless Klick is also elevated.
- Global hotkeys work while another window is focused.
- Use this only where you are allowed to automate input (your own machine, accessibility, approved workflows).
- Random intervals change pacing; they do not hide that input is automated.

## License

MIT

"""In-app help guide for new users."""

from __future__ import annotations

import customtkinter as ctk

from app.ui.theme import COLORS, FONTS


HELP_SECTIONS: list[tuple[str, str]] = [
    (
        "Getting started",
        "Klick automates mouse clicks, typing, scrolling, custom sequences, and light cursor movement "
        "on this computer.\n\n"
        "1. Open the tab for what you want (Clicker, Typer, Custom, or Jiggler).\n"
        "2. Configure the options on that tab.\n"
        "3. Focus the target window (or set a fixed mouse position).\n"
        "4. Press Start — or use the global hotkey (default F6).\n"
        "5. Press Stop or the emergency hotkey (default F7) to halt immediately.\n\n"
        "Tip: use Start delay so you have time to switch to the other window after pressing Start.\n"
        "Tip: open this Help tab anytime you need a refresher on a control.",
    ),
    (
        "Status bar (top)",
        "• Status — Idle, Running, Typing, Completed, etc.\n"
        "• Actions / Keys / Steps / Jiggles — how many actions have run in this session.\n"
        "• Elapsed — how long the current run has been going.\n"
        "• Hotkey reminder — current Start/Stop and Emergency Stop keys.\n\n"
        "Hover the Start and Stop buttons to see the shortcuts in a tooltip.",
    ),
    (
        "Auto Clicker — Action",
        "• Click — performs mouse clicks.\n"
        "• Scroll — moves the mouse wheel instead of clicking.\n"
        "When you choose Scroll, click-only options (button / click type) are hidden and "
        "scroll options (direction / notches) are shown instead.",
    ),
    (
        "Auto Clicker — Interval",
        "• Apply delay after — when the wait happens (each click or each scroll).\n"
        "• Fixed — same wait every time (H / M / S / MS).\n"
        "• Random — each wait is a new value between Min and Max.\n"
        "  Use the Min/Max sliders (1 ms–10 s) or fine-tune fields for exact values.\n"
        "  A new random value is chosen every time the delay runs — not once for the whole run.",
    ),
    (
        "Auto Clicker — Click / Scroll options",
        "Click mode:\n"
        "• Mouse button — Left, Right, or Middle.\n"
        "• Click type — Single, Double, or Triple.\n\n"
        "Scroll mode:\n"
        "• Direction — Up or Down.\n"
        "• Notches — how many wheel steps per scroll action.",
    ),
    (
        "Auto Clicker — Cursor position",
        "• Current Cursor — acts wherever the pointer is (X/Y/Pick are hidden).\n"
        "• Fixed Point — moves to X,Y first, then acts (X/Y/Pick are shown).\n"
        "• Pick Position — waits briefly, then captures your current pointer location.",
    ),
    (
        "Auto Clicker — Repeat & delay",
        "• Unlimited — keeps going until Stop, Emergency Stop, or Auto Stop. Count is hidden.\n"
        "• Fixed Count — runs exactly Count times, then stops. Count field appears only here.\n"
        "• Start delay — seconds to wait after Start before the first action.",
    ),
    (
        "Auto Stop",
        "Optional timer on Clicker, Typer, Custom, and Jiggler.\n"
        "Enable it and set Hours / Minutes / Seconds. The run stops when that duration is reached, "
        "even if Count is not finished.",
    ),
    (
        "Auto Typer — Text to Type",
        "Enter the text you want typed into the focused field or window.\n"
        "Always give yourself a Start delay so you can click into the target box first.\n\n"
        "Without Fixed text mode, use Repeat Options:\n"
        "• Once — one full pass of the text.\n"
        "• Fixed Count — repeat the whole text that many times.\n"
        "• Unlimited — keep repeating until you stop it.",
    ),
    (
        "Auto Typer — Fixed text mode (optional add-on)",
        "Enable this checkbox when you want a one-shot typed document with a countdown.\n"
        "• Types the Text to Type content once, then stops automatically.\n"
        "• Shows estimated total time from your interval + start delay.\n"
        "• Shows live progress (units done / total) and time remaining.\n"
        "• Repeat mode choices are hidden while this add-on is on (behavior is forced to once & stop).\n"
        "• Start delay and Press Enter still apply.\n"
        "Turn it off to return to normal Once / Fixed Count / Unlimited repeating.",
    ),
    (
        "Auto Typer — Interval",
        "• Apply delay after each character or each word.\n"
        "• Fixed or Random interval (same slider + fine-tune controls as the clicker).\n"
        "• Press Enter after each run — optional Enter key at the end of each pass "
        "(or at the end of the single pass in Fixed text mode).",
    ),
    (
        "Custom — Combo sequences",
        "Build a list of steps that run in order:\n"
        "• Click — button, click type, current or fixed position.\n"
        "• Type — text (optional Enter).\n"
        "• Scroll — direction and notches.\n"
        "• Wait — pause for a set number of milliseconds.\n\n"
        "Only fields relevant to the selected step type are shown.\n"
        "Use Add Step to Sequence, Remove Last, or Clear All.\n"
        "Between Steps interval controls the pause after click/type/scroll "
        "(Wait steps use their own time).\n"
        "Repeat Options: Once, Fixed Count (Count shown only then), or Unlimited.",
    ),
    (
        "Jiggler",
        "Moves the cursor in small, irregular bursts (useful to keep a session active).\n"
        "• Jiggle radius — how far from the start point it may wander.\n"
        "• Min/Max step — size of each movement.\n"
        "• Max micro-moves — sub-steps inside one burst.\n"
        "• Keep near starting position — occasionally pulls back toward the origin.\n"
        "• Restore cursor when stopped — returns the pointer to where it started.\n"
        "• Time between jiggles — Fixed or Random, same interval controls as elsewhere.",
    ),
    (
        "Settings",
        "• Start / Stop hotkey — toggle the current tab’s automation (default F6).\n"
        "• Emergency Stop hotkey — always stops everything (default F7).\n"
        "• Save Hotkeys — applies new key names (examples: f8, f9).\n"
        "• Always on top — keeps the Klick window above other windows; preference is saved.\n"
        "Settings are stored in your user folder under ~/.klick/settings.json.",
    ),
    (
        "Help tab",
        "This tab is the built-in user guide. Use it when you are new to Klick or unsure "
        "what a control does. It mirrors the main features of the app so you can configure "
        "safely without guessing.",
    ),
    (
        "Logos & window title",
        "• Header uses assets/text_logo.png (size controlled in app/ui/logo.py).\n"
        "• Window icon uses assets/klick_logo.png.\n"
        "• Window title is simply KLICK.",
    ),
    (
        "Safety & tips",
        "• Use only on machines and workflows you are allowed to automate.\n"
        "• Do not use Klick to bypass security tools, game anti-cheat, or monitoring.\n"
        "• If input seems ignored, the target app may need focus, or Klick may need to run elevated "
        "for elevated windows.\n"
        "• Random intervals only vary timing; they do not hide that input is automated.\n"
        "• Prefer Always on top while setting up, then turn it off if you want Klick to stay in the background.",
    ),
]


class HelpPanel(ctk.CTkFrame):
    def __init__(self, master: ctk.CTkBaseClass, **kwargs) -> None:
        super().__init__(master, fg_color="transparent", **kwargs)
        scroll = ctk.CTkScrollableFrame(self, fg_color="transparent")
        scroll.pack(fill="both", expand=True)

        header = ctk.CTkFrame(scroll, fg_color=COLORS["surface"], corner_radius=12)
        header.pack(fill="x", pady=(0, 12))
        header_inner = ctk.CTkFrame(header, fg_color="transparent")
        header_inner.pack(fill="x", padx=16, pady=14)
        ctk.CTkLabel(
            header_inner,
            text="HELP & USER GUIDE",
            font=FONTS["section"],
            text_color=COLORS["muted"],
            anchor="w",
        ).pack(anchor="w")
        ctk.CTkLabel(
            header_inner,
            text="A beginner-friendly walkthrough of every main control in Klick.",
            font=FONTS["body"],
            text_color=COLORS["text"],
            anchor="w",
        ).pack(anchor="w", pady=(4, 0))

        for title, body in HELP_SECTIONS:
            card = ctk.CTkFrame(scroll, fg_color=COLORS["surface"], corner_radius=12)
            card.pack(fill="x", pady=(0, 10))
            inner = ctk.CTkFrame(card, fg_color="transparent")
            inner.pack(fill="x", padx=16, pady=14)
            ctk.CTkLabel(
                inner,
                text=title.upper(),
                font=FONTS["section"],
                text_color=COLORS["accent"],
                anchor="w",
            ).pack(anchor="w")
            ctk.CTkLabel(
                inner,
                text=body,
                font=FONTS["body"],
                text_color=COLORS["text"],
                anchor="w",
                justify="left",
                wraplength=700,
            ).pack(anchor="w", pady=(8, 0))

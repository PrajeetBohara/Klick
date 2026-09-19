"""Main application window."""

from __future__ import annotations

import time
from typing import Literal

import customtkinter as ctk

from app import __version__
from app.engines import ClickerEngine, ComboEngine, JigglerEngine, TyperEngine
from app.ui.clicker_panel import ClickerPanel
from app.ui.combo_panel import ComboPanel
from app.ui.jiggler_panel import JigglerPanel
from app.ui.logo import LogoPlaceholder
from app.ui.theme import COLORS, FONTS
from app.ui.typer_panel import TyperPanel
from app.utils.hotkeys import HotkeyManager
from app.utils.settings import SettingsStore

Mode = Literal["clicker", "typer", "combo", "jiggler", "none"]


class MainWindow(ctk.CTk):
    def __init__(self) -> None:
        super().__init__()
        self.settings = SettingsStore()

        self.title("KLICK")
        self.geometry("820x880")
        self.minsize(760, 780)
        self.configure(fg_color=COLORS["bg"])

        self._active_mode: Mode = "none"
        self._started_at: float | None = None
        self._elapsed_job: str | None = None

        self.clicker = ClickerEngine(
            on_tick=self._on_clicker_tick,
            on_status=self._on_engine_status,
            on_stopped=self._on_engine_stopped,
        )
        self.typer = TyperEngine(
            on_tick=self._on_typer_tick,
            on_status=self._on_engine_status,
            on_stopped=self._on_engine_stopped,
        )
        self.combo = ComboEngine(
            on_tick=self._on_combo_tick,
            on_status=self._on_engine_status,
            on_stopped=self._on_engine_stopped,
        )
        self.jiggler = JigglerEngine(
            on_tick=self._on_jiggler_tick,
            on_status=self._on_engine_status,
            on_stopped=self._on_engine_stopped,
        )

        hotkeys = self.settings.get_section("hotkeys")
        self.hotkeys = HotkeyManager(
            on_toggle=self._toggle_active,
            on_emergency_stop=self._emergency_stop,
            toggle_key=str(hotkeys.get("toggle", "f6")),
            emergency_key=str(hotkeys.get("emergency_stop", "f7")),
        )

        self._build_ui()
        self.hotkeys.start()
        self.protocol("WM_DELETE_WINDOW", self._on_close)

        tab = self.settings.get_section("ui").get("active_tab", "clicker")
        tab_map = {
            "typer": "Auto Typer",
            "combo": "Custom",
            "jiggler": "Jiggler",
            "clicker": "Auto Clicker",
        }
        self.tabview.set(tab_map.get(str(tab), "Auto Clicker"))

    def _any_running(self) -> bool:
        return (
            self.clicker.is_running
            or self.typer.is_running
            or self.combo.is_running
            or self.jiggler.is_running
        )

    def _set_all_running(self, running: bool) -> None:
        self.clicker_panel.set_running(running)
        self.typer_panel.set_running(running)
        self.combo_panel.set_running(running)
        self.jiggler_panel.set_running(running)

    def _build_ui(self) -> None:
        root = ctk.CTkFrame(self, fg_color="transparent")
        root.pack(fill="both", expand=True, padx=22, pady=18)

        header = ctk.CTkFrame(root, fg_color="transparent")
        header.pack(fill="x", pady=(0, 14))

        brand = ctk.CTkFrame(header, fg_color="transparent")
        brand.pack(side="left")
        LogoPlaceholder(brand, height=48).pack(anchor="w")
        ctk.CTkLabel(
            brand,
            text="Click · Type · Scroll · Jiggle · Custom",
            font=FONTS["subtitle"],
            text_color=COLORS["muted"],
            anchor="w",
        ).pack(anchor="w", pady=(6, 0))

        meta = ctk.CTkFrame(header, fg_color="transparent")
        meta.pack(side="right")
        ctk.CTkLabel(
            meta,
            text=f"v{__version__}",
            font=FONTS["body"],
            text_color=COLORS["muted"],
        ).pack(anchor="e")

        status_box = ctk.CTkFrame(root, fg_color=COLORS["surface"], corner_radius=12)
        status_box.pack(fill="x", pady=(0, 14))
        status_inner = ctk.CTkFrame(status_box, fg_color="transparent")
        status_inner.pack(fill="x", padx=16, pady=12)

        self.status_dot = ctk.CTkLabel(
            status_inner,
            text="●",
            font=("Segoe UI", 16),
            text_color=COLORS["idle"],
            width=24,
        )
        self.status_dot.pack(side="left")
        self.status_label = ctk.CTkLabel(
            status_inner,
            text="Idle",
            font=FONTS["section"],
            text_color=COLORS["text"],
            anchor="w",
        )
        self.status_label.pack(side="left", padx=(4, 20))
        self.counter_label = ctk.CTkLabel(
            status_inner,
            text="Actions: 0",
            font=FONTS["mono"],
            text_color=COLORS["muted"],
        )
        self.counter_label.pack(side="left", padx=(0, 20))
        self.elapsed_label = ctk.CTkLabel(
            status_inner,
            text="Elapsed: 00:00:00",
            font=FONTS["mono"],
            text_color=COLORS["muted"],
        )
        self.elapsed_label.pack(side="left")
        self.hotkey_label = ctk.CTkLabel(
            status_inner,
            text="F6 Start/Stop  ·  F7 Emergency Stop",
            font=FONTS["body"],
            text_color=COLORS["muted"],
        )
        self.hotkey_label.pack(side="right")

        self.tabview = ctk.CTkTabview(
            root,
            fg_color=COLORS["bg"],
            segmented_button_fg_color=COLORS["surface"],
            segmented_button_selected_color=COLORS["accent"],
            segmented_button_selected_hover_color=COLORS["accent_hover"],
            segmented_button_unselected_color=COLORS["surface"],
            segmented_button_unselected_hover_color=COLORS["surface_alt"],
            text_color=COLORS["text"],
            corner_radius=12,
        )
        self.tabview.pack(fill="both", expand=True)
        self.tabview.add("Auto Clicker")
        self.tabview.add("Auto Typer")
        self.tabview.add("Custom")
        self.tabview.add("Jiggler")
        self.tabview.add("Settings")

        self.clicker_panel = ClickerPanel(
            self.tabview.tab("Auto Clicker"),
            settings=self.settings.get_section("clicker"),
            on_start=self.start_clicker,
            on_stop=self.stop_all,
        )
        self.clicker_panel.pack(fill="both", expand=True, padx=4, pady=8)

        self.typer_panel = TyperPanel(
            self.tabview.tab("Auto Typer"),
            settings=self.settings.get_section("typer"),
            on_start=self.start_typer,
            on_stop=self.stop_all,
        )
        self.typer_panel.pack(fill="both", expand=True, padx=4, pady=8)

        self.combo_panel = ComboPanel(
            self.tabview.tab("Custom"),
            settings=self.settings.get_section("combo"),
            on_start=self.start_combo,
            on_stop=self.stop_all,
        )
        self.combo_panel.pack(fill="both", expand=True, padx=4, pady=8)

        self.jiggler_panel = JigglerPanel(
            self.tabview.tab("Jiggler"),
            settings=self.settings.get_section("jiggler"),
            on_start=self.start_jiggler,
            on_stop=self.stop_all,
        )
        self.jiggler_panel.pack(fill="both", expand=True, padx=4, pady=8)

        self._build_settings(self.tabview.tab("Settings"))
        saved_hotkeys = self.settings.get_section("hotkeys")
        self._apply_hotkey_tooltips(
            str(saved_hotkeys.get("toggle", "f6")),
            str(saved_hotkeys.get("emergency_stop", "f7")),
        )

        footer = ctk.CTkLabel(
            root,
            text="For accessibility and approved local automation only.",
            font=("Segoe UI", 11),
            text_color=COLORS["muted"],
        )
        footer.pack(pady=(10, 0))

    def _build_settings(self, parent: ctk.CTkBaseClass) -> None:
        box = ctk.CTkFrame(parent, fg_color=COLORS["surface"], corner_radius=12)
        box.pack(fill="x", padx=4, pady=8)
        inner = ctk.CTkFrame(box, fg_color="transparent")
        inner.pack(fill="x", padx=16, pady=14)

        ctk.CTkLabel(
            inner,
            text="GLOBAL HOTKEYS",
            font=FONTS["section"],
            text_color=COLORS["muted"],
            anchor="w",
        ).pack(anchor="w")
        ctk.CTkLabel(
            inner,
            text="Hotkeys work while another window is focused.",
            font=FONTS["body"],
            text_color=COLORS["muted"],
            anchor="w",
        ).pack(anchor="w", pady=(2, 12))

        hotkeys = self.settings.get_section("hotkeys")
        row = ctk.CTkFrame(inner, fg_color="transparent")
        row.pack(fill="x")

        left = ctk.CTkFrame(row, fg_color="transparent")
        left.pack(side="left", fill="x", expand=True, padx=(0, 8))
        ctk.CTkLabel(
            left, text="Start / Stop", font=FONTS["body"], text_color=COLORS["text"]
        ).pack(anchor="w")
        self.toggle_key = ctk.CTkEntry(
            left,
            height=34,
            font=FONTS["mono"],
            fg_color=COLORS["surface_alt"],
            border_color=COLORS["border"],
            text_color=COLORS["text"],
        )
        self.toggle_key.pack(fill="x", pady=(6, 0))
        self.toggle_key.insert(0, str(hotkeys.get("toggle", "f6")))

        right = ctk.CTkFrame(row, fg_color="transparent")
        right.pack(side="left", fill="x", expand=True, padx=(8, 0))
        ctk.CTkLabel(
            right,
            text="Emergency Stop",
            font=FONTS["body"],
            text_color=COLORS["text"],
        ).pack(anchor="w")
        self.emergency_key = ctk.CTkEntry(
            right,
            height=34,
            font=FONTS["mono"],
            fg_color=COLORS["surface_alt"],
            border_color=COLORS["border"],
            text_color=COLORS["text"],
        )
        self.emergency_key.pack(fill="x", pady=(6, 0))
        self.emergency_key.insert(0, str(hotkeys.get("emergency_stop", "f7")))

        ctk.CTkButton(
            inner,
            text="Save Hotkeys",
            height=36,
            font=FONTS["button"],
            fg_color=COLORS["accent"],
            hover_color=COLORS["accent_hover"],
            command=self._save_hotkeys,
        ).pack(anchor="w", pady=(14, 0))

        note = ctk.CTkFrame(parent, fg_color=COLORS["surface"], corner_radius=12)
        note.pack(fill="x", padx=4, pady=(4, 8))
        note_inner = ctk.CTkFrame(note, fg_color="transparent")
        note_inner.pack(fill="x", padx=16, pady=14)
        ctk.CTkLabel(
            note_inner,
            text="USAGE GUIDANCE",
            font=FONTS["section"],
            text_color=COLORS["muted"],
            anchor="w",
        ).pack(anchor="w")
        ctk.CTkLabel(
            note_inner,
            text=(
                "• Use for accessibility, testing, and workflows you control.\n"
                "• Random intervals vary pacing; they do not hide automation.\n"
                "• Do not use to bypass anti-cheat, CAPTCHAs, or monitoring.\n"
                "• Settings are saved to ~/.klick/settings.json"
            ),
            font=FONTS["body"],
            text_color=COLORS["text"],
            justify="left",
            anchor="w",
        ).pack(anchor="w", pady=(8, 0))

    def _apply_hotkey_tooltips(self, toggle: str, emergency: str) -> None:
        for panel in (
            self.clicker_panel,
            self.typer_panel,
            self.combo_panel,
            self.jiggler_panel,
        ):
            panel.set_hotkey_tooltips(toggle, emergency)

    def _save_hotkeys(self) -> None:
        toggle = self.toggle_key.get().strip().lower() or "f6"
        emergency = self.emergency_key.get().strip().lower() or "f7"
        self.settings.update_section(
            "hotkeys", {"toggle": toggle, "emergency_stop": emergency}
        )
        self.hotkeys.update_keys(toggle, emergency)
        self.hotkey_label.configure(
            text=f"{toggle.upper()} Start/Stop  ·  {emergency.upper()} Emergency Stop"
        )
        self._apply_hotkey_tooltips(toggle, emergency)
        self._set_status("Hotkeys saved", COLORS["success"])

    def start_clicker(self) -> None:
        if self._any_running():
            return
        self._persist_panels()
        config = self.clicker_panel.get_config()
        self._active_mode = "clicker"
        self._set_all_running(True)
        self._begin_session()
        self.clicker.start(config)

    def start_typer(self) -> None:
        if self._any_running():
            return
        config = self.typer_panel.get_config()
        if not config.text.strip():
            self._set_status("Enter text to type", COLORS["warning"])
            return
        self._persist_panels()
        self._active_mode = "typer"
        self._set_all_running(True)
        self._begin_session()
        self.typer.start(config)

    def start_combo(self) -> None:
        if self._any_running():
            return
        config = self.combo_panel.get_config()
        if not config.steps:
            self._set_status("Add at least one combo step", COLORS["warning"])
            return
        self._persist_panels()
        self._active_mode = "combo"
        self._set_all_running(True)
        self._begin_session()
        self.combo.start(config)

    def start_jiggler(self) -> None:
        if self._any_running():
            return
        self._persist_panels()
        config = self.jiggler_panel.get_config()
        self._active_mode = "jiggler"
        self._set_all_running(True)
        self._begin_session()
        self.jiggler.start(config)

    def stop_all(self) -> None:
        self.clicker.stop()
        self.typer.stop()
        self.combo.stop()
        self.jiggler.stop()
        self._finish_session()

    def _emergency_stop(self) -> None:
        self.after(0, self.stop_all)

    def _toggle_active(self) -> None:
        self.after(0, self._toggle_active_ui)

    def _toggle_active_ui(self) -> None:
        if self._any_running():
            self.stop_all()
            return
        current = self.tabview.get()
        if current == "Auto Typer":
            self.start_typer()
        elif current == "Custom":
            self.start_combo()
        elif current == "Jiggler":
            self.start_jiggler()
        else:
            self.start_clicker()

    def _begin_session(self) -> None:
        self._started_at = time.time()
        self.counter_label.configure(text="Actions: 0")
        self._set_status("Running", COLORS["success"])
        self._tick_elapsed()

    def _finish_session(self) -> None:
        self._active_mode = "none"
        self._started_at = None
        if self._elapsed_job is not None:
            try:
                self.after_cancel(self._elapsed_job)
            except Exception:
                pass
            self._elapsed_job = None
        self._set_all_running(False)
        self._set_status("Idle", COLORS["idle"])

    def _tick_elapsed(self) -> None:
        if self._started_at is None:
            return
        elapsed = int(time.time() - self._started_at)
        hours, rem = divmod(elapsed, 3600)
        minutes, seconds = divmod(rem, 60)
        self.elapsed_label.configure(
            text=f"Elapsed: {hours:02d}:{minutes:02d}:{seconds:02d}"
        )
        self._elapsed_job = self.after(500, self._tick_elapsed)

    def _on_clicker_tick(self, count: int) -> None:
        self.after(
            0,
            lambda: self.counter_label.configure(text=f"Actions: {count}"),
        )

    def _on_typer_tick(self, count: int) -> None:
        self.after(0, lambda: self.counter_label.configure(text=f"Keys: {count}"))

    def _on_combo_tick(self, count: int) -> None:
        self.after(0, lambda: self.counter_label.configure(text=f"Steps: {count}"))

    def _on_jiggler_tick(self, count: int) -> None:
        self.after(0, lambda: self.counter_label.configure(text=f"Jiggles: {count}"))

    def _on_engine_status(self, message: str) -> None:
        active = {
            "Clicking",
            "Scrolling",
            "Typing",
            "Running combo",
            "Jiggling",
        }
        if message in active:
            color = COLORS["success"]
        elif message == "Stopped":
            color = COLORS["idle"]
        else:
            color = COLORS["warning"]
        self.after(0, lambda: self._set_status(message, color))

    def _on_engine_stopped(self) -> None:
        self.after(0, self._finish_session)

    def _set_status(self, text: str, color: str) -> None:
        self.status_label.configure(text=text)
        self.status_dot.configure(text_color=color)

    def _persist_panels(self) -> None:
        self.settings.update_section("clicker", self.clicker_panel.export_settings())
        self.settings.update_section("typer", self.typer_panel.export_settings())
        self.settings.update_section("combo", self.combo_panel.export_settings())
        self.settings.update_section("jiggler", self.jiggler_panel.export_settings())
        tab = self.tabview.get()
        active = {
            "Auto Typer": "typer",
            "Custom": "combo",
            "Jiggler": "jiggler",
        }.get(tab, "clicker")
        self.settings.update_section("ui", {"active_tab": active})

    def _on_close(self) -> None:
        self.stop_all()
        self._persist_panels()
        self.hotkeys.stop()
        self.destroy()


def run_app() -> None:
    ctk.set_appearance_mode("dark")
    ctk.set_default_color_theme("dark-blue")
    app = MainWindow()
    app.mainloop()

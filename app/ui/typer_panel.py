"""Auto-typer configuration panel."""

from __future__ import annotations

from typing import Any, Callable

import customtkinter as ctk

from app.engines.typer import TyperConfig
from app.ui.interval_controls import AutoStopBlock, IntervalBlock
from app.ui.theme import COLORS, FONTS
from app.ui.widgets import field_label, int_entry, safe_float, safe_int, section_label
from app.utils.timing import AutoStopConfig, DurationParts, IntervalConfig


class TyperPanel(ctk.CTkFrame):
    def __init__(
        self,
        master: ctk.CTkBaseClass,
        settings: dict[str, Any],
        on_start: Callable[[], None],
        on_stop: Callable[[], None],
        **kwargs: Any,
    ) -> None:
        super().__init__(master, fg_color="transparent", **kwargs)
        self._settings = settings
        self._on_start = on_start
        self._on_stop = on_stop
        self._build()
        self._load_settings()

    def _build(self) -> None:
        scroll = ctk.CTkScrollableFrame(self, fg_color="transparent")
        scroll.pack(fill="both", expand=True)

        text_box = ctk.CTkFrame(scroll, fg_color=COLORS["surface"], corner_radius=12)
        text_box.pack(fill="x", pady=(0, 12))
        text_inner = ctk.CTkFrame(text_box, fg_color="transparent")
        text_inner.pack(fill="x", padx=16, pady=14)
        section_label(text_inner, "Text to Type").pack(anchor="w")
        field_label(
            text_inner, "Focus the target field before start. Use a start delay."
        ).pack(anchor="w", pady=(2, 8))
        self.text = ctk.CTkTextbox(
            text_inner,
            height=120,
            font=FONTS["mono"],
            fg_color=COLORS["surface_alt"],
            border_color=COLORS["border"],
            border_width=1,
            text_color=COLORS["text"],
            wrap="word",
        )
        self.text.pack(fill="x")

        self.interval_block = IntervalBlock(
            scroll,
            title="Type Interval",
            apply_after_options=["each character", "each word"],
            apply_after_default="each character",
        )
        self.interval_block.pack(fill="x", pady=(0, 12))

        repeat_box = ctk.CTkFrame(scroll, fg_color=COLORS["surface"], corner_radius=12)
        repeat_box.pack(fill="x", pady=(0, 12))
        repeat_inner = ctk.CTkFrame(repeat_box, fg_color="transparent")
        repeat_inner.pack(fill="x", padx=16, pady=14)
        section_label(repeat_inner, "Repeat Options").pack(anchor="w")

        repeat_row = ctk.CTkFrame(repeat_inner, fg_color="transparent")
        repeat_row.pack(fill="x", pady=(10, 0))
        mode_col = ctk.CTkFrame(repeat_row, fg_color="transparent")
        mode_col.pack(side="left", fill="x", expand=True)
        field_label(mode_col, "Repeat mode").pack(anchor="w")
        self.repeat_mode = ctk.CTkSegmentedButton(
            mode_col,
            values=["Once", "Fixed Count", "Unlimited"],
            command=self._on_repeat_mode,
            font=FONTS["body"],
            selected_color=COLORS["accent"],
            selected_hover_color=COLORS["accent_hover"],
            unselected_color=COLORS["surface_alt"],
            unselected_hover_color=COLORS["border"],
            text_color=COLORS["text"],
        )
        self.repeat_mode.pack(fill="x", pady=(6, 0))
        self.repeat_mode.set("Once")

        count_col = ctk.CTkFrame(repeat_row, fg_color="transparent")
        count_col.pack(side="left", padx=(12, 0))
        field_label(count_col, "Count").pack(anchor="w")
        self.repeat_count = int_entry(count_col, width=90, default="1")
        self.repeat_count.pack(pady=(6, 0))

        delay_col = ctk.CTkFrame(repeat_row, fg_color="transparent")
        delay_col.pack(side="left", padx=(12, 0))
        field_label(delay_col, "Start delay (s)").pack(anchor="w")
        self.start_delay = int_entry(delay_col, width=90, default="2")
        self.start_delay.pack(pady=(6, 0))

        self.press_enter = ctk.CTkCheckBox(
            repeat_inner,
            text="Press Enter after each run",
            font=FONTS["body"],
            text_color=COLORS["text"],
            fg_color=COLORS["accent"],
            hover_color=COLORS["accent_hover"],
            border_color=COLORS["border"],
        )
        self.press_enter.pack(anchor="w", pady=(14, 0))

        self.auto_stop_block = AutoStopBlock(scroll)
        self.auto_stop_block.pack(fill="x", pady=(0, 12))

        actions = ctk.CTkFrame(self, fg_color="transparent")
        actions.pack(fill="x", pady=(8, 0))
        self.start_btn = ctk.CTkButton(
            actions,
            text="Start Typing",
            height=44,
            font=FONTS["button"],
            fg_color=COLORS["accent"],
            hover_color=COLORS["accent_hover"],
            command=self._on_start,
        )
        self.start_btn.pack(side="left", fill="x", expand=True, padx=(0, 6))
        self.stop_btn = ctk.CTkButton(
            actions,
            text="Stop",
            height=44,
            font=FONTS["button"],
            fg_color=COLORS["danger"],
            hover_color=COLORS["danger_hover"],
            command=self._on_stop,
            state="disabled",
        )
        self.stop_btn.pack(side="left", fill="x", expand=True, padx=(6, 0))
        self._on_repeat_mode("Once")

    def _on_repeat_mode(self, value: str) -> None:
        self.repeat_count.configure(
            state="normal" if value == "Fixed Count" else "disabled"
        )

    def set_running(self, running: bool) -> None:
        self.start_btn.configure(state="disabled" if running else "normal")
        self.stop_btn.configure(state="normal" if running else "disabled")

    def get_config(self) -> TyperConfig:
        mode_map = {
            "Once": "once",
            "Fixed Count": "count",
            "Unlimited": "unlimited",
        }
        apply_after = self.interval_block.get_apply_after().lower()
        unit_mode = "word" if "word" in apply_after else "character"
        return TyperConfig(
            text=self.text.get("1.0", "end-1c"),
            interval=self.interval_block.get_config(),
            unit_mode=unit_mode,
            repeat_mode=mode_map.get(self.repeat_mode.get(), "once"),
            repeat_count=safe_int(self.repeat_count.get(), 1, 1),
            start_delay=safe_float(self.start_delay.get(), 2.0),
            press_enter=bool(self.press_enter.get()),
            auto_stop=self.auto_stop_block.get_config(),
        )

    def export_settings(self) -> dict[str, Any]:
        cfg = self.get_config()
        return {
            "text": cfg.text,
            "interval": cfg.interval.to_dict(),
            "unit_mode": cfg.unit_mode,
            "repeat_mode": cfg.repeat_mode,
            "repeat_count": cfg.repeat_count,
            "start_delay": cfg.start_delay,
            "press_enter": cfg.press_enter,
            "auto_stop": cfg.auto_stop.to_dict(),
        }

    def _load_settings(self) -> None:
        s = self._settings
        self.text.delete("1.0", "end")
        self.text.insert("1.0", str(s.get("text", "")))

        if "interval" in s:
            self.interval_block.load_config(s.get("interval", {}))
        else:
            ms = int(s.get("interval_ms", 50) or 50)
            self.interval_block.load_config(
                IntervalConfig(
                    mode="fixed",
                    fixed=DurationParts(milliseconds=ms),
                    minimum=DurationParts(milliseconds=max(1, ms // 2)),
                    maximum=DurationParts(milliseconds=ms * 2),
                )
            )

        unit = str(s.get("unit_mode", s.get("interval_mode", "character"))).lower()
        self.interval_block.set_apply_after(
            "each word" if unit == "word" else "each character"
        )

        repeat = s.get("repeat_mode", "once")
        if repeat == "count":
            self.repeat_mode.set("Fixed Count")
            self._on_repeat_mode("Fixed Count")
        elif repeat == "unlimited":
            self.repeat_mode.set("Unlimited")
            self._on_repeat_mode("Unlimited")
        else:
            self.repeat_mode.set("Once")
            self._on_repeat_mode("Once")

        self.repeat_count.delete(0, "end")
        self.repeat_count.insert(0, str(s.get("repeat_count", 1)))
        self.start_delay.delete(0, "end")
        self.start_delay.insert(0, str(s.get("start_delay", 2.0)))
        if s.get("press_enter"):
            self.press_enter.select()
        else:
            self.press_enter.deselect()
        self.auto_stop_block.load_config(
            AutoStopConfig.from_dict(s.get("auto_stop", {}))
        )

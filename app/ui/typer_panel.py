"""Auto-typer configuration panel."""

from __future__ import annotations

from typing import Any, Callable

import customtkinter as ctk

from app.engines.typer import (
    TyperConfig,
    estimate_typing_seconds,
    format_duration,
)
from app.ui.interval_controls import AutoStopBlock, IntervalBlock
from app.ui.theme import COLORS, FONTS
from app.ui.widgets import (
    ToolTip,
    field_label,
    hide_widget,
    int_entry,
    safe_float,
    safe_int,
    section_label,
    set_entry_text,
    show_widget,
)
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
        self.after(200, self._refresh_estimate)

    def _build(self) -> None:
        scroll = ctk.CTkScrollableFrame(self, fg_color="transparent")
        scroll.pack(fill="both", expand=True)

        text_box = ctk.CTkFrame(scroll, fg_color=COLORS["surface"], corner_radius=12)
        text_box.pack(fill="x", pady=(0, 12))
        text_inner = ctk.CTkFrame(text_box, fg_color="transparent")
        text_inner.pack(fill="x", padx=16, pady=14)
        section_label(text_inner, "Text to Type").pack(anchor="w")
        field_label(
            text_inner,
            "Focus the target field before start. Use a start delay.",
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
        self.text.bind("<KeyRelease>", lambda _e: self._refresh_estimate())

        # Optional add-on: fixed text mode
        addon_box = ctk.CTkFrame(scroll, fg_color=COLORS["surface"], corner_radius=12)
        addon_box.pack(fill="x", pady=(0, 12))
        addon_inner = ctk.CTkFrame(addon_box, fg_color="transparent")
        addon_inner.pack(fill="x", padx=16, pady=14)
        section_label(addon_inner, "Fixed Text Mode (optional)").pack(anchor="w")
        field_label(
            addon_inner,
            "Add-on: type the text once, show time remaining, and stop when finished.",
        ).pack(anchor="w", pady=(2, 8))

        self.fixed_text_mode = ctk.CTkCheckBox(
            addon_inner,
            text="Enable fixed text mode (once & stop + countdown)",
            font=FONTS["body"],
            text_color=COLORS["text"],
            fg_color=COLORS["accent"],
            hover_color=COLORS["accent_hover"],
            border_color=COLORS["border"],
            command=self._on_fixed_text_toggle,
        )
        self.fixed_text_mode.pack(anchor="w")

        self.fixed_extras = ctk.CTkFrame(addon_inner, fg_color="transparent")
        self.estimate_label = ctk.CTkLabel(
            self.fixed_extras,
            text="Estimated time: —",
            font=FONTS["body"],
            text_color=COLORS["warning"],
            anchor="w",
            justify="left",
            wraplength=680,
        )
        self.estimate_label.pack(anchor="w", pady=(10, 0))

        self.progress = ctk.CTkProgressBar(
            self.fixed_extras,
            height=10,
            progress_color=COLORS["accent"],
            fg_color=COLORS["surface_alt"],
        )
        self.progress.pack(fill="x", pady=(10, 0))
        self.progress.set(0)
        self.progress_label = ctk.CTkLabel(
            self.fixed_extras,
            text="Idle",
            font=FONTS["mono"],
            text_color=COLORS["muted"],
            anchor="w",
        )
        self.progress_label.pack(anchor="w", pady=(6, 0))

        self.interval_block = IntervalBlock(
            scroll,
            title="Type Interval",
            apply_after_options=["each character", "each word"],
            apply_after_default="each character",
            on_apply_after_change=lambda _v: self._refresh_estimate(),
        )
        self.interval_block.pack(fill="x", pady=(0, 12))
        self.interval_block.min_slider.configure(
            command=lambda v: (
                self.interval_block._on_min_slider(v),
                self._refresh_estimate(),
            )
        )
        self.interval_block.max_slider.configure(
            command=lambda v: (
                self.interval_block._on_max_slider(v),
                self._refresh_estimate(),
            )
        )
        original_mode = self.interval_block._on_mode

        def _mode_and_refresh(value: str) -> None:
            original_mode(value)
            self._refresh_estimate()

        self.interval_block.mode.configure(command=_mode_and_refresh)

        self.repeat_box = ctk.CTkFrame(scroll, fg_color=COLORS["surface"], corner_radius=12)
        self.repeat_box.pack(fill="x", pady=(0, 12))
        repeat_inner = ctk.CTkFrame(self.repeat_box, fg_color="transparent")
        repeat_inner.pack(fill="x", padx=16, pady=14)
        section_label(repeat_inner, "Repeat Options").pack(anchor="w")
        self.repeat_hint = field_label(
            repeat_inner,
            "Once = one pass. Fixed Count / Unlimited = type the text again.",
        )
        self.repeat_hint.pack(anchor="w", pady=(2, 8))

        self.repeat_mode_row = ctk.CTkFrame(repeat_inner, fg_color="transparent")
        self.repeat_mode_row.pack(fill="x", pady=(4, 0))
        mode_col = ctk.CTkFrame(self.repeat_mode_row, fg_color="transparent")
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

        self.count_col = ctk.CTkFrame(self.repeat_mode_row, fg_color="transparent")
        field_label(self.count_col, "Count").pack(anchor="w")
        self.repeat_count = int_entry(self.count_col, width=90, default="1")
        self.repeat_count.pack(pady=(6, 0))
        self.repeat_count.bind("<KeyRelease>", lambda _e: self._refresh_estimate())

        delay_row = ctk.CTkFrame(repeat_inner, fg_color="transparent")
        delay_row.pack(fill="x", pady=(12, 0))
        self._delay_col = ctk.CTkFrame(delay_row, fg_color="transparent")
        self._delay_col.pack(side="left")
        field_label(self._delay_col, "Start delay (s)").pack(anchor="w")
        self.start_delay = int_entry(self._delay_col, width=90, default="2")
        self.start_delay.pack(pady=(6, 0))
        self.start_delay.bind("<KeyRelease>", lambda _e: self._refresh_estimate())

        self.press_enter = ctk.CTkCheckBox(
            repeat_inner,
            text="Press Enter after each run",
            font=FONTS["body"],
            text_color=COLORS["text"],
            fg_color=COLORS["accent"],
            hover_color=COLORS["accent_hover"],
            border_color=COLORS["border"],
            command=self._refresh_estimate,
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
        self.start_tip = ToolTip(self.start_btn)
        self.stop_tip = ToolTip(self.stop_btn)
        self._on_repeat_mode("Once")
        self._on_fixed_text_toggle()

    def set_hotkey_tooltips(self, toggle_key: str, emergency_key: str) -> None:
        toggle = toggle_key.upper()
        emergency = emergency_key.upper()
        self.start_tip.set_text(f"Start / Stop  ·  Shortcut: {toggle}")
        self.stop_tip.set_text(f"Stop  ·  Shortcut: {emergency} (emergency)")

    def is_fixed_text_mode(self) -> bool:
        return bool(self.fixed_text_mode.get())

    def _on_fixed_text_toggle(self) -> None:
        if self.is_fixed_text_mode():
            show_widget(self.fixed_extras, fill="x")
            hide_widget(self.repeat_mode_row)
            self.repeat_hint.configure(
                text="Fixed text mode is on: types once, then stops. Start delay still applies."
            )
            self.repeat_mode.set("Once")
            self._on_repeat_mode("Once")
        else:
            hide_widget(self.fixed_extras)
            show_widget(self.repeat_mode_row, fill="x", pady=(4, 0))
            self.repeat_hint.configure(
                text="Once = one pass. Fixed Count / Unlimited = type the text again."
            )
            self._on_repeat_mode(self.repeat_mode.get())
        self._refresh_estimate()

    def _on_repeat_mode(self, value: str) -> None:
        hide_widget(self.count_col)
        if value == "Fixed Count" and not self.is_fixed_text_mode():
            self.count_col.pack(side="left", padx=(12, 0))
            self.repeat_count.configure(state="normal")
        self._refresh_estimate()

    def set_running(self, running: bool) -> None:
        self.start_btn.configure(state="disabled" if running else "normal")
        self.stop_btn.configure(state="normal" if running else "disabled")

    def update_progress(
        self, done: int, total: int, eta_seconds: float | None
    ) -> None:
        if not self.is_fixed_text_mode():
            return
        if total > 0:
            self.progress.set(min(1.0, done / total))
            pct = int(round(100 * done / total))
            eta_text = (
                f" · left {format_duration(eta_seconds)}"
                if eta_seconds is not None
                else ""
            )
            self.progress_label.configure(
                text=f"{done}/{total} units ({pct}%){eta_text}"
            )
        elif eta_seconds is not None:
            self.progress.set(0)
            self.progress_label.configure(
                text=f"Starting… left {format_duration(eta_seconds)}"
            )
        else:
            self.progress_label.configure(text=f"{done} units")

    def reset_progress(self) -> None:
        self.progress.set(0)
        self.progress_label.configure(text="Idle")
        self._refresh_estimate()

    def _refresh_estimate(self) -> None:
        if not self.is_fixed_text_mode():
            return
        try:
            cfg = self.get_config()
        except Exception:
            return
        typing = estimate_typing_seconds(cfg)
        delay = float(cfg.start_delay or 0)
        if typing is None:
            self.estimate_label.configure(text="Estimated time: —")
            return
        total = typing + delay
        random_note = (
            " (mid-point of random min–max)"
            if cfg.interval.mode == "random"
            else ""
        )
        self.estimate_label.configure(
            text=(
                f"Estimated typing {format_duration(typing)} + start delay "
                f"{format_duration(delay)} = ~{format_duration(total)} total"
                f"{random_note}. Stops automatically when the text is finished."
            )
        )

    def get_config(self) -> TyperConfig:
        mode_map = {
            "Once": "once",
            "Once & Stop": "once",
            "Fixed Count": "count",
            "Unlimited": "unlimited",
        }
        apply_after = self.interval_block.get_apply_after().lower()
        unit_mode = "word" if "word" in apply_after else "character"
        # Fixed text add-on always types once and stops
        if self.is_fixed_text_mode():
            repeat_mode = "once"
            repeat_count = 1
        else:
            repeat_mode = mode_map.get(self.repeat_mode.get(), "once")
            repeat_count = safe_int(self.repeat_count.get(), 1, 1)
        return TyperConfig(
            text=self.text.get("1.0", "end-1c"),
            interval=self.interval_block.get_config(),
            unit_mode=unit_mode,
            repeat_mode=repeat_mode,
            repeat_count=repeat_count,
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
            "repeat_mode": (
                "once"
                if self.is_fixed_text_mode()
                else cfg.repeat_mode
            ),
            "repeat_count": cfg.repeat_count,
            "start_delay": cfg.start_delay,
            "press_enter": cfg.press_enter,
            "auto_stop": cfg.auto_stop.to_dict(),
            "fixed_text_mode": self.is_fixed_text_mode(),
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
        set_entry_text(self.repeat_count, str(s.get("repeat_count", 1)))
        if repeat == "count":
            self.repeat_mode.set("Fixed Count")
            self._on_repeat_mode("Fixed Count")
        elif repeat == "unlimited":
            self.repeat_mode.set("Unlimited")
            self._on_repeat_mode("Unlimited")
        else:
            self.repeat_mode.set("Once")
            self._on_repeat_mode("Once")

        set_entry_text(self.start_delay, str(s.get("start_delay", 2.0)))
        if s.get("press_enter"):
            self.press_enter.select()
        else:
            self.press_enter.deselect()
        self.auto_stop_block.load_config(
            AutoStopConfig.from_dict(s.get("auto_stop", {}))
        )

        if s.get("fixed_text_mode"):
            self.fixed_text_mode.select()
        else:
            self.fixed_text_mode.deselect()
        self._on_fixed_text_toggle()

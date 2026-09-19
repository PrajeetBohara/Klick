"""Reusable interval and auto-stop UI blocks."""

from __future__ import annotations

from typing import Any, Callable

import customtkinter as ctk

from app.ui.theme import COLORS, FONTS
from app.ui.widgets import field_label, int_entry, safe_int, section_label
from app.utils.timing import (
    AutoStopConfig,
    DurationParts,
    IntervalConfig,
    format_ms,
    ms_to_parts,
)

SLIDER_MIN_MS = 1
SLIDER_MAX_MS = 10_000


class IntervalBlock(ctk.CTkFrame):
    """Fixed or random interval picker with clear 'applies after' labeling."""

    def __init__(
        self,
        master: ctk.CTkBaseClass,
        title: str = "Interval",
        apply_after_options: list[str] | None = None,
        apply_after_default: str | None = None,
        on_apply_after_change: Callable[[str], None] | None = None,
        **kwargs: Any,
    ) -> None:
        super().__init__(master, fg_color=COLORS["surface"], corner_radius=12, **kwargs)
        self._apply_after_options = apply_after_options or ["each action"]
        self._on_apply_after_change = on_apply_after_change
        self._apply_after_locked = len(self._apply_after_options) == 1
        self._syncing_sliders = False

        inner = ctk.CTkFrame(self, fg_color="transparent")
        inner.pack(fill="x", padx=16, pady=14)

        section_label(inner, title).pack(anchor="w")

        field_label(inner, "Apply delay after").pack(anchor="w", pady=(10, 0))
        if self._apply_after_locked:
            self.apply_after_btn = None
            self.apply_after_label = ctk.CTkLabel(
                inner,
                text=self._apply_after_options[0],
                font=FONTS["body"],
                text_color=COLORS["text"],
                anchor="w",
                fg_color=COLORS["surface_alt"],
                corner_radius=8,
                height=34,
            )
            self.apply_after_label.pack(fill="x", pady=(6, 10))
            self._current_apply_after = self._apply_after_options[0]
        else:
            self.apply_after_label = None
            self.apply_after_btn = ctk.CTkSegmentedButton(
                inner,
                values=self._apply_after_options,
                command=self._on_apply_after,
                font=FONTS["body"],
                selected_color=COLORS["accent"],
                selected_hover_color=COLORS["accent_hover"],
                unselected_color=COLORS["surface_alt"],
                unselected_hover_color=COLORS["border"],
                text_color=COLORS["text"],
            )
            self.apply_after_btn.pack(fill="x", pady=(6, 10))
            default = apply_after_default or self._apply_after_options[0]
            if default not in self._apply_after_options:
                default = self._apply_after_options[0]
            self.apply_after_btn.set(default)
            self._current_apply_after = default

        field_label(inner, "Interval style").pack(anchor="w")
        self.mode = ctk.CTkSegmentedButton(
            inner,
            values=["Fixed", "Random"],
            command=self._on_mode,
            font=FONTS["body"],
            selected_color=COLORS["accent"],
            selected_hover_color=COLORS["accent_hover"],
            unselected_color=COLORS["surface_alt"],
            unselected_hover_color=COLORS["border"],
            text_color=COLORS["text"],
        )
        self.mode.pack(fill="x", pady=(6, 10))
        self.mode.set("Fixed")

        self.summary = ctk.CTkLabel(
            inner,
            text="",
            font=FONTS["body"],
            text_color=COLORS["warning"],
            anchor="w",
            justify="left",
            wraplength=680,
        )
        self.summary.pack(fill="x", pady=(0, 10))

        self.fixed_frame = ctk.CTkFrame(inner, fg_color="transparent")
        self.fixed_frame.pack(fill="x")
        field_label(self.fixed_frame, "Same wait every time").pack(anchor="w")
        fixed_row = ctk.CTkFrame(self.fixed_frame, fg_color="transparent")
        fixed_row.pack(fill="x", pady=(6, 0))
        self.fixed = self._duration_entries(fixed_row, ms_default="100")

        self.random_frame = ctk.CTkFrame(inner, fg_color="transparent")

        # Min slider
        min_header = ctk.CTkFrame(self.random_frame, fg_color="transparent")
        min_header.pack(fill="x")
        field_label(min_header, "Minimum wait").pack(side="left")
        self.min_value_label = ctk.CTkLabel(
            min_header,
            text="50 ms",
            font=FONTS["mono"],
            text_color=COLORS["text"],
        )
        self.min_value_label.pack(side="right")

        self.min_slider = ctk.CTkSlider(
            self.random_frame,
            from_=SLIDER_MIN_MS,
            to=SLIDER_MAX_MS,
            number_of_steps=SLIDER_MAX_MS - SLIDER_MIN_MS,
            command=self._on_min_slider,
            progress_color=COLORS["accent"],
            button_color=COLORS["accent"],
            button_hover_color=COLORS["accent_hover"],
            fg_color=COLORS["surface_alt"],
        )
        self.min_slider.pack(fill="x", pady=(6, 4))
        self.min_slider.set(50)

        min_scale = ctk.CTkFrame(self.random_frame, fg_color="transparent")
        min_scale.pack(fill="x", pady=(0, 10))
        ctk.CTkLabel(
            min_scale, text="1 ms", font=("Segoe UI", 10), text_color=COLORS["muted"]
        ).pack(side="left")
        ctk.CTkLabel(
            min_scale, text="10 s", font=("Segoe UI", 10), text_color=COLORS["muted"]
        ).pack(side="right")

        min_row = ctk.CTkFrame(self.random_frame, fg_color="transparent")
        min_row.pack(fill="x", pady=(0, 12))
        field_label(min_row, "Fine-tune min").pack(anchor="w")
        min_entries = ctk.CTkFrame(self.random_frame, fg_color="transparent")
        min_entries.pack(fill="x", pady=(4, 14))
        self.minimum = self._duration_entries(min_entries, ms_default="50")
        for entry in self.minimum.values():
            entry.bind("<KeyRelease>", lambda _e: self._on_min_entries_changed())
            entry.bind("<FocusOut>", lambda _e: self._on_min_entries_changed())

        # Max slider
        max_header = ctk.CTkFrame(self.random_frame, fg_color="transparent")
        max_header.pack(fill="x")
        field_label(max_header, "Maximum wait").pack(side="left")
        self.max_value_label = ctk.CTkLabel(
            max_header,
            text="200 ms",
            font=FONTS["mono"],
            text_color=COLORS["text"],
        )
        self.max_value_label.pack(side="right")

        self.max_slider = ctk.CTkSlider(
            self.random_frame,
            from_=SLIDER_MIN_MS,
            to=SLIDER_MAX_MS,
            number_of_steps=SLIDER_MAX_MS - SLIDER_MIN_MS,
            command=self._on_max_slider,
            progress_color=COLORS["accent"],
            button_color=COLORS["accent"],
            button_hover_color=COLORS["accent_hover"],
            fg_color=COLORS["surface_alt"],
        )
        self.max_slider.pack(fill="x", pady=(6, 4))
        self.max_slider.set(200)

        max_scale = ctk.CTkFrame(self.random_frame, fg_color="transparent")
        max_scale.pack(fill="x", pady=(0, 10))
        ctk.CTkLabel(
            max_scale, text="1 ms", font=("Segoe UI", 10), text_color=COLORS["muted"]
        ).pack(side="left")
        ctk.CTkLabel(
            max_scale, text="10 s", font=("Segoe UI", 10), text_color=COLORS["muted"]
        ).pack(side="right")

        field_label(self.random_frame, "Fine-tune max").pack(anchor="w")
        max_entries = ctk.CTkFrame(self.random_frame, fg_color="transparent")
        max_entries.pack(fill="x", pady=(4, 0))
        self.maximum = self._duration_entries(max_entries, ms_default="200")
        for entry in self.maximum.values():
            entry.bind("<KeyRelease>", lambda _e: self._on_max_entries_changed())
            entry.bind("<FocusOut>", lambda _e: self._on_max_entries_changed())

        hint = ctk.CTkLabel(
            self.random_frame,
            text=(
                "Drag the sliders to set the random range (1 ms–10 s). "
                "Use fine-tune fields for exact values, including above 10 s. "
                "A new random delay in this range is chosen every time the wait runs."
            ),
            font=("Segoe UI", 11),
            text_color=COLORS["muted"],
            anchor="w",
            justify="left",
            wraplength=680,
        )
        hint.pack(fill="x", pady=(12, 0))

        self._on_mode("Fixed")

    def _duration_entries(
        self, parent: ctk.CTkFrame, ms_default: str
    ) -> dict[str, ctk.CTkEntry]:
        entries: dict[str, ctk.CTkEntry] = {}
        for label, key, default in (
            ("H", "hours", "0"),
            ("M", "minutes", "0"),
            ("S", "seconds", "0"),
            ("MS", "milliseconds", ms_default),
        ):
            col = ctk.CTkFrame(parent, fg_color="transparent")
            col.pack(side="left", padx=(0, 8))
            field_label(col, label).pack(anchor="w")
            entry = int_entry(col, width=64, default=default)
            entry.pack(pady=(4, 0))
            entries[key] = entry
        return entries

    def _on_apply_after(self, value: str) -> None:
        self._current_apply_after = value
        self._refresh_summary()
        if self._on_apply_after_change:
            self._on_apply_after_change(value)

    def _on_mode(self, value: str) -> None:
        if value == "Random":
            self.fixed_frame.pack_forget()
            self.random_frame.pack(fill="x")
            self._sync_sliders_from_entries()
        else:
            self.random_frame.pack_forget()
            self.fixed_frame.pack(fill="x")
        self._refresh_summary()

    def _on_min_slider(self, value: float) -> None:
        if self._syncing_sliders:
            return
        ms = int(round(value))
        max_ms = int(round(self.max_slider.get()))
        if ms > max_ms:
            ms = max_ms
            self.min_slider.set(ms)
        self._syncing_sliders = True
        self._write_duration(self.minimum, ms_to_parts(ms))
        self.min_value_label.configure(text=format_ms(ms))
        self._syncing_sliders = False
        self._refresh_summary()

    def _on_max_slider(self, value: float) -> None:
        if self._syncing_sliders:
            return
        ms = int(round(value))
        min_ms = int(round(self.min_slider.get()))
        if ms < min_ms:
            ms = min_ms
            self.max_slider.set(ms)
        self._syncing_sliders = True
        self._write_duration(self.maximum, ms_to_parts(ms))
        self.max_value_label.configure(text=format_ms(ms))
        self._syncing_sliders = False
        self._refresh_summary()

    def _on_min_entries_changed(self) -> None:
        if self._syncing_sliders:
            return
        self._sync_sliders_from_entries()

    def _on_max_entries_changed(self) -> None:
        if self._syncing_sliders:
            return
        self._sync_sliders_from_entries()

    def _sync_sliders_from_entries(self) -> None:
        self._syncing_sliders = True
        min_ms = self._read_duration(self.minimum, 50).total_ms()
        max_ms = self._read_duration(self.maximum, 200).total_ms()
        if max_ms < min_ms:
            max_ms = min_ms
            self._write_duration(self.maximum, ms_to_parts(max_ms))

        self.min_slider.set(min(max(min_ms, SLIDER_MIN_MS), SLIDER_MAX_MS))
        self.max_slider.set(min(max(max_ms, SLIDER_MIN_MS), SLIDER_MAX_MS))
        self.min_value_label.configure(text=format_ms(min_ms))
        self.max_value_label.configure(text=format_ms(max_ms))
        self._syncing_sliders = False
        self._refresh_summary()

    def _refresh_summary(self) -> None:
        unit = self.get_apply_after()
        if self.mode.get() == "Random":
            min_ms = self._read_duration(self.minimum, 50).total_ms()
            max_ms = self._read_duration(self.maximum, 200).total_ms()
            text = (
                f"How it works: after {unit}, wait a new random time between "
                f"{format_ms(min_ms)} and {format_ms(max_ms)}, then continue. "
                f"The value is re-rolled every time — not once for the whole run."
            )
        else:
            text = (
                f"How it works: after {unit}, Klick always waits the same fixed time, "
                f"then continues."
            )
        self.summary.configure(text=text)

    def set_apply_after(self, value: str) -> None:
        if self.apply_after_btn is not None and value in self._apply_after_options:
            self.apply_after_btn.set(value)
            self._current_apply_after = value
        elif self.apply_after_label is not None:
            self.apply_after_label.configure(text=value)
            self._current_apply_after = value
            self._apply_after_options = [value]
        self._refresh_summary()

    def get_apply_after(self) -> str:
        if self.apply_after_btn is not None:
            return self.apply_after_btn.get()
        return self._current_apply_after

    def _read_duration(self, entries: dict[str, ctk.CTkEntry], fallback_ms: int) -> DurationParts:
        return DurationParts(
            hours=safe_int(entries["hours"].get()),
            minutes=safe_int(entries["minutes"].get()),
            seconds=safe_int(entries["seconds"].get()),
            milliseconds=safe_int(entries["milliseconds"].get(), fallback_ms, 0),
        )

    def _write_duration(self, entries: dict[str, ctk.CTkEntry], duration: DurationParts) -> None:
        mapping = {
            "hours": duration.hours,
            "minutes": duration.minutes,
            "seconds": duration.seconds,
            "milliseconds": duration.milliseconds,
        }
        for key, value in mapping.items():
            entries[key].delete(0, "end")
            entries[key].insert(0, str(value))

    def get_config(self) -> IntervalConfig:
        return IntervalConfig(
            mode="random" if self.mode.get() == "Random" else "fixed",
            fixed=self._read_duration(self.fixed, 100),
            minimum=self._read_duration(self.minimum, 50),
            maximum=self._read_duration(self.maximum, 200),
        )

    def load_config(self, config: IntervalConfig | dict) -> None:
        if isinstance(config, dict):
            config = IntervalConfig.from_dict(config)
        self.mode.set("Random" if config.mode == "random" else "Fixed")
        self._write_duration(self.fixed, config.fixed)
        self._write_duration(self.minimum, config.minimum)
        self._write_duration(self.maximum, config.maximum)
        self._on_mode(self.mode.get())
        self._sync_sliders_from_entries()
        self._refresh_summary()


class AutoStopBlock(ctk.CTkFrame):
    """Optional timed auto-stop."""

    def __init__(self, master: ctk.CTkBaseClass, **kwargs: Any) -> None:
        super().__init__(master, fg_color=COLORS["surface"], corner_radius=12, **kwargs)
        inner = ctk.CTkFrame(self, fg_color="transparent")
        inner.pack(fill="x", padx=16, pady=14)

        section_label(inner, "Auto Stop").pack(anchor="w")
        field_label(inner, "Stop automatically after a set duration").pack(
            anchor="w", pady=(2, 10)
        )

        self.enabled = ctk.CTkCheckBox(
            inner,
            text="Enable auto stop",
            font=FONTS["body"],
            text_color=COLORS["text"],
            fg_color=COLORS["accent"],
            hover_color=COLORS["accent_hover"],
            border_color=COLORS["border"],
            command=self._on_toggle,
        )
        self.enabled.pack(anchor="w")

        row = ctk.CTkFrame(inner, fg_color="transparent")
        row.pack(fill="x", pady=(10, 0))
        self.hours = self._labeled(row, "Hours", "0")
        self.minutes = self._labeled(row, "Minutes", "0")
        self.seconds = self._labeled(row, "Seconds", "30")
        self._on_toggle()

    def _labeled(self, parent: ctk.CTkFrame, label: str, default: str) -> ctk.CTkEntry:
        col = ctk.CTkFrame(parent, fg_color="transparent")
        col.pack(side="left", padx=(0, 10))
        field_label(col, label).pack(anchor="w")
        entry = int_entry(col, width=72, default=default)
        entry.pack(pady=(6, 0))
        return entry

    def _on_toggle(self) -> None:
        state = "normal" if self.enabled.get() else "disabled"
        self.hours.configure(state=state)
        self.minutes.configure(state=state)
        self.seconds.configure(state=state)

    def get_config(self) -> AutoStopConfig:
        return AutoStopConfig(
            enabled=bool(self.enabled.get()),
            hours=safe_int(self.hours.get()),
            minutes=safe_int(self.minutes.get()),
            seconds=safe_int(self.seconds.get(), 30),
        )

    def load_config(self, config: AutoStopConfig | dict) -> None:
        if isinstance(config, dict):
            config = AutoStopConfig.from_dict(config)
        if config.enabled:
            self.enabled.select()
        else:
            self.enabled.deselect()
        self.hours.configure(state="normal")
        self.minutes.configure(state="normal")
        self.seconds.configure(state="normal")
        self.hours.delete(0, "end")
        self.hours.insert(0, str(config.hours))
        self.minutes.delete(0, "end")
        self.minutes.insert(0, str(config.minutes))
        self.seconds.delete(0, "end")
        self.seconds.insert(0, str(config.seconds))
        self._on_toggle()

"""Mouse jiggler configuration panel."""

from __future__ import annotations

from typing import Any, Callable

import customtkinter as ctk

from app.engines.jiggler import JigglerConfig
from app.ui.interval_controls import AutoStopBlock, IntervalBlock
from app.ui.theme import COLORS, FONTS
from app.ui.widgets import field_label, int_entry, safe_float, safe_int, section_label
from app.utils.timing import AutoStopConfig, IntervalConfig


class JigglerPanel(ctk.CTkFrame):
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

        intro = ctk.CTkFrame(scroll, fg_color=COLORS["surface"], corner_radius=12)
        intro.pack(fill="x", pady=(0, 12))
        intro_inner = ctk.CTkFrame(intro, fg_color="transparent")
        intro_inner.pack(fill="x", padx=16, pady=14)
        section_label(intro_inner, "Auto Jiggler").pack(anchor="w")
        field_label(
            intro_inner,
            "Moves the cursor in small, irregular bursts. Timing and direction are re-randomized each burst.",
        ).pack(anchor="w", pady=(4, 0))

        move_box = ctk.CTkFrame(scroll, fg_color=COLORS["surface"], corner_radius=12)
        move_box.pack(fill="x", pady=(0, 12))
        move_inner = ctk.CTkFrame(move_box, fg_color="transparent")
        move_inner.pack(fill="x", padx=16, pady=14)
        section_label(move_inner, "Movement Area").pack(anchor="w")

        radius_header = ctk.CTkFrame(move_inner, fg_color="transparent")
        radius_header.pack(fill="x", pady=(10, 0))
        field_label(radius_header, "Jiggle radius").pack(side="left")
        self.radius_label = ctk.CTkLabel(
            radius_header, text="40 px", font=FONTS["mono"], text_color=COLORS["text"]
        )
        self.radius_label.pack(side="right")

        self.radius_slider = ctk.CTkSlider(
            move_inner,
            from_=5,
            to=200,
            number_of_steps=195,
            command=self._on_radius,
            progress_color=COLORS["accent"],
            button_color=COLORS["accent"],
            button_hover_color=COLORS["accent_hover"],
            fg_color=COLORS["surface_alt"],
        )
        self.radius_slider.pack(fill="x", pady=(6, 4))
        self.radius_slider.set(40)

        step_row = ctk.CTkFrame(move_inner, fg_color="transparent")
        step_row.pack(fill="x", pady=(12, 0))
        min_col = ctk.CTkFrame(step_row, fg_color="transparent")
        min_col.pack(side="left", padx=(0, 12))
        field_label(min_col, "Min step (px)").pack(anchor="w")
        self.min_step = int_entry(min_col, width=90, default="2")
        self.min_step.pack(pady=(6, 0))
        max_col = ctk.CTkFrame(step_row, fg_color="transparent")
        max_col.pack(side="left", padx=(0, 12))
        field_label(max_col, "Max step (px)").pack(anchor="w")
        self.max_step = int_entry(max_col, width=90, default="18")
        self.max_step.pack(pady=(6, 0))
        micro_col = ctk.CTkFrame(step_row, fg_color="transparent")
        micro_col.pack(side="left")
        field_label(micro_col, "Max micro-moves").pack(anchor="w")
        self.micro_moves = int_entry(micro_col, width=90, default="3")
        self.micro_moves.pack(pady=(6, 0))

        self.keep_near = ctk.CTkCheckBox(
            move_inner,
            text="Keep near starting position (random pull-backs)",
            font=FONTS["body"],
            text_color=COLORS["text"],
            fg_color=COLORS["accent"],
            hover_color=COLORS["accent_hover"],
            border_color=COLORS["border"],
        )
        self.keep_near.pack(anchor="w", pady=(14, 0))
        self.keep_near.select()

        self.restore = ctk.CTkCheckBox(
            move_inner,
            text="Restore cursor to start when stopped",
            font=FONTS["body"],
            text_color=COLORS["text"],
            fg_color=COLORS["accent"],
            hover_color=COLORS["accent_hover"],
            border_color=COLORS["border"],
        )
        self.restore.pack(anchor="w", pady=(8, 0))
        self.restore.select()

        self.interval_block = IntervalBlock(
            scroll,
            title="Time Between Jiggles",
            apply_after_options=["each jiggle burst"],
        )
        self.interval_block.pack(fill="x", pady=(0, 12))

        delay_box = ctk.CTkFrame(scroll, fg_color=COLORS["surface"], corner_radius=12)
        delay_box.pack(fill="x", pady=(0, 12))
        delay_inner = ctk.CTkFrame(delay_box, fg_color="transparent")
        delay_inner.pack(fill="x", padx=16, pady=14)
        section_label(delay_inner, "Start Delay").pack(anchor="w")
        field_label(delay_inner, "Seconds before jiggling begins").pack(
            anchor="w", pady=(2, 8)
        )
        self.start_delay = int_entry(delay_inner, width=100, default="0")
        self.start_delay.pack(anchor="w")

        self.auto_stop_block = AutoStopBlock(scroll)
        self.auto_stop_block.pack(fill="x", pady=(0, 12))

        actions = ctk.CTkFrame(self, fg_color="transparent")
        actions.pack(fill="x", pady=(8, 0))
        self.start_btn = ctk.CTkButton(
            actions,
            text="Start Jiggler",
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

    def _on_radius(self, value: float) -> None:
        self.radius_label.configure(text=f"{int(round(value))} px")

    def set_running(self, running: bool) -> None:
        self.start_btn.configure(state="disabled" if running else "normal")
        self.stop_btn.configure(state="normal" if running else "disabled")

    def get_config(self) -> JigglerConfig:
        return JigglerConfig(
            radius_px=int(round(self.radius_slider.get())),
            min_step_px=safe_int(self.min_step.get(), 2, 1),
            max_step_px=safe_int(self.max_step.get(), 18, 1),
            micro_moves=safe_int(self.micro_moves.get(), 3, 1),
            interval=self.interval_block.get_config(),
            start_delay=safe_float(self.start_delay.get()),
            auto_stop=self.auto_stop_block.get_config(),
            keep_near_start=bool(self.keep_near.get()),
            restore_on_stop=bool(self.restore.get()),
        )

    def export_settings(self) -> dict[str, Any]:
        cfg = self.get_config()
        return {
            "radius_px": cfg.radius_px,
            "min_step_px": cfg.min_step_px,
            "max_step_px": cfg.max_step_px,
            "micro_moves": cfg.micro_moves,
            "interval": cfg.interval.to_dict(),
            "start_delay": cfg.start_delay,
            "auto_stop": cfg.auto_stop.to_dict(),
            "keep_near_start": cfg.keep_near_start,
            "restore_on_stop": cfg.restore_on_stop,
        }

    def _load_settings(self) -> None:
        s = self._settings
        radius = int(s.get("radius_px", 40) or 40)
        self.radius_slider.set(radius)
        self._on_radius(radius)
        self.min_step.delete(0, "end")
        self.min_step.insert(0, str(s.get("min_step_px", 2)))
        self.max_step.delete(0, "end")
        self.max_step.insert(0, str(s.get("max_step_px", 18)))
        self.micro_moves.delete(0, "end")
        self.micro_moves.insert(0, str(s.get("micro_moves", 3)))
        self.interval_block.load_config(IntervalConfig.from_dict(s.get("interval", {})))
        # Prefer random for jiggler if unset/fixed from empty defaults with random intent
        if not s.get("interval"):
            self.interval_block.mode.set("Random")
            self.interval_block._on_mode("Random")
        self.start_delay.delete(0, "end")
        self.start_delay.insert(0, str(s.get("start_delay", 0)))
        self.auto_stop_block.load_config(AutoStopConfig.from_dict(s.get("auto_stop", {})))
        if s.get("keep_near_start", True):
            self.keep_near.select()
        else:
            self.keep_near.deselect()
        if s.get("restore_on_stop", True):
            self.restore.select()
        else:
            self.restore.deselect()

"""Auto-clicker / scroll configuration panel."""

from __future__ import annotations

from typing import Any, Callable

import customtkinter as ctk
from pynput.mouse import Controller as MouseController

from app.engines.clicker import ClickerConfig
from app.ui.interval_controls import AutoStopBlock, IntervalBlock
from app.ui.theme import COLORS, FONTS
from app.ui.widgets import field_label, int_entry, safe_float, safe_int, section_label, ToolTip
from app.utils.timing import AutoStopConfig, IntervalConfig


class ClickerPanel(ctk.CTkFrame):
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
        self._mouse = MouseController()
        self._build()
        self._load_settings()
        self.after(100, self._poll_cursor)

    def _build(self) -> None:
        scroll = ctk.CTkScrollableFrame(self, fg_color="transparent")
        scroll.pack(fill="both", expand=True)

        # Action
        action_box = ctk.CTkFrame(scroll, fg_color=COLORS["surface"], corner_radius=12)
        action_box.pack(fill="x", pady=(0, 12))
        action_inner = ctk.CTkFrame(action_box, fg_color="transparent")
        action_inner.pack(fill="x", padx=16, pady=14)
        section_label(action_inner, "Action").pack(anchor="w")
        self.action = ctk.CTkSegmentedButton(
            action_inner,
            values=["Click", "Scroll"],
            command=self._on_action,
            font=FONTS["body"],
            selected_color=COLORS["accent"],
            selected_hover_color=COLORS["accent_hover"],
            unselected_color=COLORS["surface_alt"],
            unselected_hover_color=COLORS["border"],
            text_color=COLORS["text"],
        )
        self.action.pack(fill="x", pady=(10, 0))
        self.action.set("Click")

        self.interval_block = IntervalBlock(
            scroll,
            title="Interval",
            apply_after_options=["each click"],
        )
        self.interval_block.pack(fill="x", pady=(0, 12))

        # Mouse / scroll options
        options_box = ctk.CTkFrame(scroll, fg_color=COLORS["surface"], corner_radius=12)
        options_box.pack(fill="x", pady=(0, 12))
        options_inner = ctk.CTkFrame(options_box, fg_color="transparent")
        options_inner.pack(fill="x", padx=16, pady=14)
        section_label(options_inner, "Mouse Options").pack(anchor="w")

        self.click_options = ctk.CTkFrame(options_inner, fg_color="transparent")
        self.click_options.pack(fill="x", pady=(10, 0))
        grid = ctk.CTkFrame(self.click_options, fg_color="transparent")
        grid.pack(fill="x")
        grid.columnconfigure((0, 1), weight=1)

        left = ctk.CTkFrame(grid, fg_color="transparent")
        left.grid(row=0, column=0, sticky="ew", padx=(0, 8))
        field_label(left, "Mouse button").pack(anchor="w")
        self.button = ctk.CTkSegmentedButton(
            left,
            values=["Left", "Right", "Middle"],
            font=FONTS["body"],
            selected_color=COLORS["accent"],
            selected_hover_color=COLORS["accent_hover"],
            unselected_color=COLORS["surface_alt"],
            unselected_hover_color=COLORS["border"],
            text_color=COLORS["text"],
        )
        self.button.pack(fill="x", pady=(6, 0))
        self.button.set("Left")

        right = ctk.CTkFrame(grid, fg_color="transparent")
        right.grid(row=0, column=1, sticky="ew", padx=(8, 0))
        field_label(right, "Click type").pack(anchor="w")
        self.click_type = ctk.CTkSegmentedButton(
            right,
            values=["Single", "Double", "Triple"],
            font=FONTS["body"],
            selected_color=COLORS["accent"],
            selected_hover_color=COLORS["accent_hover"],
            unselected_color=COLORS["surface_alt"],
            unselected_hover_color=COLORS["border"],
            text_color=COLORS["text"],
        )
        self.click_type.pack(fill="x", pady=(6, 0))
        self.click_type.set("Single")

        self.scroll_options = ctk.CTkFrame(options_inner, fg_color="transparent")
        scroll_grid = ctk.CTkFrame(self.scroll_options, fg_color="transparent")
        scroll_grid.pack(fill="x", pady=(10, 0))
        dir_col = ctk.CTkFrame(scroll_grid, fg_color="transparent")
        dir_col.pack(side="left", fill="x", expand=True)
        field_label(dir_col, "Scroll direction").pack(anchor="w")
        self.scroll_direction = ctk.CTkSegmentedButton(
            dir_col,
            values=["Up", "Down"],
            font=FONTS["body"],
            selected_color=COLORS["accent"],
            selected_hover_color=COLORS["accent_hover"],
            unselected_color=COLORS["surface_alt"],
            unselected_hover_color=COLORS["border"],
            text_color=COLORS["text"],
        )
        self.scroll_direction.pack(fill="x", pady=(6, 0))
        self.scroll_direction.set("Down")

        amt_col = ctk.CTkFrame(scroll_grid, fg_color="transparent")
        amt_col.pack(side="left", padx=(12, 0))
        field_label(amt_col, "Notches").pack(anchor="w")
        self.scroll_amount = int_entry(amt_col, width=90, default="3")
        self.scroll_amount.pack(pady=(6, 0))

        # Position
        pos_box = ctk.CTkFrame(scroll, fg_color=COLORS["surface"], corner_radius=12)
        pos_box.pack(fill="x", pady=(0, 12))
        pos_inner = ctk.CTkFrame(pos_box, fg_color="transparent")
        pos_inner.pack(fill="x", padx=16, pady=14)
        section_label(pos_inner, "Cursor Position").pack(anchor="w")
        self.position_mode = ctk.CTkSegmentedButton(
            pos_inner,
            values=["Current Cursor", "Fixed Point"],
            command=self._on_position_mode,
            font=FONTS["body"],
            selected_color=COLORS["accent"],
            selected_hover_color=COLORS["accent_hover"],
            unselected_color=COLORS["surface_alt"],
            unselected_hover_color=COLORS["border"],
            text_color=COLORS["text"],
        )
        self.position_mode.pack(fill="x", pady=(10, 12))
        self.position_mode.set("Current Cursor")

        coord_row = ctk.CTkFrame(pos_inner, fg_color="transparent")
        coord_row.pack(fill="x")
        self.fixed_x = self._coord_entry(coord_row, "X", "0")
        self.fixed_y = self._coord_entry(coord_row, "Y", "0")
        self.pick_btn = ctk.CTkButton(
            coord_row,
            text="Pick Position",
            width=120,
            height=34,
            font=FONTS["body"],
            fg_color=COLORS["surface_alt"],
            hover_color=COLORS["border"],
            text_color=COLORS["text"],
            command=self._start_pick,
        )
        self.pick_btn.pack(side="left", padx=(8, 0), pady=(18, 0))
        self.cursor_label = ctk.CTkLabel(
            pos_inner,
            text="Live cursor: (0, 0)",
            font=FONTS["mono"],
            text_color=COLORS["muted"],
            anchor="w",
        )
        self.cursor_label.pack(anchor="w", pady=(10, 0))

        # Repeat
        repeat_box = ctk.CTkFrame(scroll, fg_color=COLORS["surface"], corner_radius=12)
        repeat_box.pack(fill="x", pady=(0, 12))
        repeat_inner = ctk.CTkFrame(repeat_box, fg_color="transparent")
        repeat_inner.pack(fill="x", padx=16, pady=14)
        section_label(repeat_inner, "Repeat & Delay").pack(anchor="w")
        repeat_row = ctk.CTkFrame(repeat_inner, fg_color="transparent")
        repeat_row.pack(fill="x", pady=(10, 0))

        mode_col = ctk.CTkFrame(repeat_row, fg_color="transparent")
        mode_col.pack(side="left", fill="x", expand=True)
        field_label(mode_col, "Repeat mode").pack(anchor="w")
        self.repeat_mode = ctk.CTkSegmentedButton(
            mode_col,
            values=["Unlimited", "Fixed Count"],
            command=self._on_repeat_mode,
            font=FONTS["body"],
            selected_color=COLORS["accent"],
            selected_hover_color=COLORS["accent_hover"],
            unselected_color=COLORS["surface_alt"],
            unselected_hover_color=COLORS["border"],
            text_color=COLORS["text"],
        )
        self.repeat_mode.pack(fill="x", pady=(6, 0))
        self.repeat_mode.set("Unlimited")

        count_col = ctk.CTkFrame(repeat_row, fg_color="transparent")
        count_col.pack(side="left", padx=(12, 0))
        field_label(count_col, "Count").pack(anchor="w")
        self.repeat_count = int_entry(count_col, width=90, default="10")
        self.repeat_count.pack(pady=(6, 0))

        delay_col = ctk.CTkFrame(repeat_row, fg_color="transparent")
        delay_col.pack(side="left", padx=(12, 0))
        field_label(delay_col, "Start delay (s)").pack(anchor="w")
        self.start_delay = int_entry(delay_col, width=90, default="0")
        self.start_delay.pack(pady=(6, 0))

        self.auto_stop_block = AutoStopBlock(scroll)
        self.auto_stop_block.pack(fill="x", pady=(0, 12))

        actions = ctk.CTkFrame(self, fg_color="transparent")
        actions.pack(fill="x", pady=(8, 0))
        self.start_btn = ctk.CTkButton(
            actions,
            text="Start",
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

        self._on_action("Click")
        self._on_position_mode("Current Cursor")
        self._on_repeat_mode("Unlimited")

    def set_hotkey_tooltips(self, toggle_key: str, emergency_key: str) -> None:
        toggle = toggle_key.upper()
        emergency = emergency_key.upper()
        self.start_tip.set_text(f"Start / Stop  ·  Shortcut: {toggle}")
        self.stop_tip.set_text(f"Stop  ·  Shortcut: {emergency} (emergency)")

    def _coord_entry(
        self, parent: ctk.CTkFrame, label: str, default: str
    ) -> ctk.CTkEntry:
        col = ctk.CTkFrame(parent, fg_color="transparent")
        col.pack(side="left")
        field_label(col, label).pack(anchor="w")
        entry = int_entry(col, width=90, default=default)
        entry.pack(pady=(6, 0))
        return entry

    def _on_action(self, value: str) -> None:
        if value == "Scroll":
            self.click_options.pack_forget()
            self.scroll_options.pack(fill="x")
            self.start_btn.configure(text="Start Scrolling")
            self.interval_block.set_apply_after("each scroll")
        else:
            self.scroll_options.pack_forget()
            self.click_options.pack(fill="x", pady=(10, 0))
            self.start_btn.configure(text="Start Clicking")
            self.interval_block.set_apply_after("each click")

    def _on_position_mode(self, value: str) -> None:
        enabled = value == "Fixed Point"
        state = "normal" if enabled else "disabled"
        self.fixed_x.configure(state=state)
        self.fixed_y.configure(state=state)
        self.pick_btn.configure(state=state)

    def _on_repeat_mode(self, value: str) -> None:
        self.repeat_count.configure(
            state="normal" if value == "Fixed Count" else "disabled"
        )

    def _start_pick(self) -> None:
        self.pick_btn.configure(text="Capturing…", state="disabled")
        self.after(1200, self._finish_pick)

    def _finish_pick(self) -> None:
        x, y = self._mouse.position
        self.fixed_x.configure(state="normal")
        self.fixed_y.configure(state="normal")
        self.fixed_x.delete(0, "end")
        self.fixed_x.insert(0, str(int(x)))
        self.fixed_y.delete(0, "end")
        self.fixed_y.insert(0, str(int(y)))
        self.pick_btn.configure(text="Pick Position", state="normal")

    def _poll_cursor(self) -> None:
        x, y = self._mouse.position
        self.cursor_label.configure(text=f"Live cursor: ({int(x)}, {int(y)})")
        self.after(80, self._poll_cursor)

    def set_running(self, running: bool) -> None:
        self.start_btn.configure(state="disabled" if running else "normal")
        self.stop_btn.configure(state="normal" if running else "disabled")

    def get_config(self) -> ClickerConfig:
        return ClickerConfig(
            action="scroll" if self.action.get() == "Scroll" else "click",
            interval=self.interval_block.get_config(),
            button=self.button.get().lower(),
            click_type=self.click_type.get().lower(),
            position_mode=(
                "current" if self.position_mode.get() == "Current Cursor" else "fixed"
            ),
            fixed_x=safe_int(self.fixed_x.get()),
            fixed_y=safe_int(self.fixed_y.get()),
            scroll_direction=self.scroll_direction.get().lower(),
            scroll_amount=safe_int(self.scroll_amount.get(), 3, 1),
            repeat_mode=(
                "unlimited" if self.repeat_mode.get() == "Unlimited" else "count"
            ),
            repeat_count=safe_int(self.repeat_count.get(), 10, 1),
            start_delay=safe_float(self.start_delay.get()),
            auto_stop=self.auto_stop_block.get_config(),
        )

    def export_settings(self) -> dict[str, Any]:
        cfg = self.get_config()
        return {
            "action": cfg.action,
            "interval": cfg.interval.to_dict(),
            "button": cfg.button,
            "click_type": cfg.click_type,
            "position_mode": cfg.position_mode,
            "fixed_x": cfg.fixed_x,
            "fixed_y": cfg.fixed_y,
            "scroll_direction": cfg.scroll_direction,
            "scroll_amount": cfg.scroll_amount,
            "repeat_mode": cfg.repeat_mode,
            "repeat_count": cfg.repeat_count,
            "start_delay": cfg.start_delay,
            "auto_stop": cfg.auto_stop.to_dict(),
        }

    def _load_settings(self) -> None:
        s = self._settings
        action = "Scroll" if s.get("action") == "scroll" else "Click"
        self.action.set(action)
        self._on_action(action)

        if "interval" in s:
            self.interval_block.load_config(s.get("interval", {}))
        else:
            self.interval_block.load_config(
                IntervalConfig.from_dict(
                    {
                        "hours": s.get("hours", 0),
                        "minutes": s.get("minutes", 0),
                        "seconds": s.get("seconds", 0),
                        "milliseconds": s.get("milliseconds", 100),
                    }
                )
            )

        button = str(s.get("button", "left")).capitalize()
        if button in ("Left", "Right", "Middle"):
            self.button.set(button)
        click_type = str(s.get("click_type", "single")).capitalize()
        if click_type in ("Single", "Double", "Triple"):
            self.click_type.set(click_type)

        direction = str(s.get("scroll_direction", "down")).capitalize()
        if direction in ("Up", "Down"):
            self.scroll_direction.set(direction)
        self.scroll_amount.delete(0, "end")
        self.scroll_amount.insert(0, str(s.get("scroll_amount", 3)))

        if s.get("position_mode") == "fixed":
            self.position_mode.set("Fixed Point")
            self._on_position_mode("Fixed Point")
        else:
            self.position_mode.set("Current Cursor")
            self._on_position_mode("Current Cursor")

        self.fixed_x.delete(0, "end")
        self.fixed_x.insert(0, str(s.get("fixed_x", 0)))
        self.fixed_y.delete(0, "end")
        self.fixed_y.insert(0, str(s.get("fixed_y", 0)))

        if s.get("repeat_mode") == "count":
            self.repeat_mode.set("Fixed Count")
            self._on_repeat_mode("Fixed Count")
        else:
            self.repeat_mode.set("Unlimited")
            self._on_repeat_mode("Unlimited")

        self.repeat_count.delete(0, "end")
        self.repeat_count.insert(0, str(s.get("repeat_count", 10)))
        self.start_delay.delete(0, "end")
        self.start_delay.insert(0, str(s.get("start_delay", 0)))
        self.auto_stop_block.load_config(
            AutoStopConfig.from_dict(s.get("auto_stop", {}))
        )

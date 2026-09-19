"""Custom combo panel: sequenced click / type / scroll / wait."""

from __future__ import annotations

from typing import Any, Callable

import customtkinter as ctk
from pynput.mouse import Controller as MouseController

from app.engines.combo import ComboConfig, ComboStep
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
)
from app.utils.timing import AutoStopConfig, IntervalConfig


class ComboPanel(ctk.CTkFrame):
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
        self._steps: list[ComboStep] = []
        self._build()
        self._load_settings()

    def _build(self) -> None:
        scroll = ctk.CTkScrollableFrame(self, fg_color="transparent")
        scroll.pack(fill="both", expand=True)

        list_box = ctk.CTkFrame(scroll, fg_color=COLORS["surface"], corner_radius=12)
        list_box.pack(fill="x", pady=(0, 12))
        list_inner = ctk.CTkFrame(list_box, fg_color="transparent")
        list_inner.pack(fill="x", padx=16, pady=14)
        section_label(list_inner, "Combo Sequence").pack(anchor="w")
        field_label(
            list_inner, "Steps run in order. Add click, type, scroll, or wait actions."
        ).pack(anchor="w", pady=(2, 8))

        self.steps_box = ctk.CTkTextbox(
            list_inner,
            height=110,
            font=FONTS["mono"],
            fg_color=COLORS["surface_alt"],
            border_color=COLORS["border"],
            border_width=1,
            text_color=COLORS["text"],
            state="disabled",
        )
        self.steps_box.pack(fill="x")

        list_btns = ctk.CTkFrame(list_inner, fg_color="transparent")
        list_btns.pack(fill="x", pady=(8, 0))
        ctk.CTkButton(
            list_btns,
            text="Remove Last",
            width=120,
            height=32,
            font=FONTS["body"],
            fg_color=COLORS["surface_alt"],
            hover_color=COLORS["border"],
            text_color=COLORS["text"],
            command=self._remove_last,
        ).pack(side="left")
        ctk.CTkButton(
            list_btns,
            text="Clear All",
            width=100,
            height=32,
            font=FONTS["body"],
            fg_color=COLORS["surface_alt"],
            hover_color=COLORS["border"],
            text_color=COLORS["text"],
            command=self._clear_steps,
        ).pack(side="left", padx=(8, 0))

        # Add step
        add_box = ctk.CTkFrame(scroll, fg_color=COLORS["surface"], corner_radius=12)
        add_box.pack(fill="x", pady=(0, 12))
        add_inner = ctk.CTkFrame(add_box, fg_color="transparent")
        add_inner.pack(fill="x", padx=16, pady=14)
        section_label(add_inner, "Add Step").pack(anchor="w")

        field_label(add_inner, "Action type").pack(anchor="w", pady=(10, 0))
        self.step_action = ctk.CTkSegmentedButton(
            add_inner,
            values=["Click", "Type", "Scroll", "Wait"],
            command=self._on_step_action,
            font=FONTS["body"],
            selected_color=COLORS["accent"],
            selected_hover_color=COLORS["accent_hover"],
            unselected_color=COLORS["surface_alt"],
            unselected_hover_color=COLORS["border"],
            text_color=COLORS["text"],
        )
        self.step_action.pack(fill="x", pady=(6, 10))
        self.step_action.set("Click")

        self.click_fields = ctk.CTkFrame(add_inner, fg_color="transparent")
        click_row = ctk.CTkFrame(self.click_fields, fg_color="transparent")
        click_row.pack(fill="x")
        btn_col = ctk.CTkFrame(click_row, fg_color="transparent")
        btn_col.pack(side="left", fill="x", expand=True)
        field_label(btn_col, "Button").pack(anchor="w")
        self.step_button = ctk.CTkSegmentedButton(
            btn_col,
            values=["Left", "Right", "Middle"],
            font=FONTS["body"],
            selected_color=COLORS["accent"],
            selected_hover_color=COLORS["accent_hover"],
            unselected_color=COLORS["surface_alt"],
            unselected_hover_color=COLORS["border"],
            text_color=COLORS["text"],
        )
        self.step_button.pack(fill="x", pady=(6, 0))
        self.step_button.set("Left")
        type_col = ctk.CTkFrame(click_row, fg_color="transparent")
        type_col.pack(side="left", fill="x", expand=True, padx=(8, 0))
        field_label(type_col, "Click type").pack(anchor="w")
        self.step_click_type = ctk.CTkSegmentedButton(
            type_col,
            values=["Single", "Double", "Triple"],
            font=FONTS["body"],
            selected_color=COLORS["accent"],
            selected_hover_color=COLORS["accent_hover"],
            unselected_color=COLORS["surface_alt"],
            unselected_hover_color=COLORS["border"],
            text_color=COLORS["text"],
        )
        self.step_click_type.pack(fill="x", pady=(6, 0))
        self.step_click_type.set("Single")

        self.type_fields = ctk.CTkFrame(add_inner, fg_color="transparent")
        field_label(self.type_fields, "Text").pack(anchor="w")
        self.step_text = ctk.CTkEntry(
            self.type_fields,
            height=34,
            font=FONTS["mono"],
            fg_color=COLORS["surface_alt"],
            border_color=COLORS["border"],
            text_color=COLORS["text"],
        )
        self.step_text.pack(fill="x", pady=(6, 8))
        self.step_press_enter = ctk.CTkCheckBox(
            self.type_fields,
            text="Press Enter after typing",
            font=FONTS["body"],
            text_color=COLORS["text"],
            fg_color=COLORS["accent"],
            hover_color=COLORS["accent_hover"],
            border_color=COLORS["border"],
        )
        self.step_press_enter.pack(anchor="w")

        self.scroll_fields = ctk.CTkFrame(add_inner, fg_color="transparent")
        scroll_row = ctk.CTkFrame(self.scroll_fields, fg_color="transparent")
        scroll_row.pack(fill="x")
        dir_col = ctk.CTkFrame(scroll_row, fg_color="transparent")
        dir_col.pack(side="left", fill="x", expand=True)
        field_label(dir_col, "Direction").pack(anchor="w")
        self.step_scroll_dir = ctk.CTkSegmentedButton(
            dir_col,
            values=["Up", "Down"],
            font=FONTS["body"],
            selected_color=COLORS["accent"],
            selected_hover_color=COLORS["accent_hover"],
            unselected_color=COLORS["surface_alt"],
            unselected_hover_color=COLORS["border"],
            text_color=COLORS["text"],
        )
        self.step_scroll_dir.pack(fill="x", pady=(6, 0))
        self.step_scroll_dir.set("Down")
        amt_col = ctk.CTkFrame(scroll_row, fg_color="transparent")
        amt_col.pack(side="left", padx=(12, 0))
        field_label(amt_col, "Notches").pack(anchor="w")
        self.step_scroll_amount = int_entry(amt_col, width=90, default="3")
        self.step_scroll_amount.pack(pady=(6, 0))

        self.wait_fields = ctk.CTkFrame(add_inner, fg_color="transparent")
        field_label(self.wait_fields, "Wait (ms)").pack(anchor="w")
        self.step_wait_ms = int_entry(self.wait_fields, width=120, default="500")
        self.step_wait_ms.pack(anchor="w", pady=(6, 0))

        # Shared position for click/scroll
        self.pos_fields = ctk.CTkFrame(add_inner, fg_color="transparent")
        field_label(self.pos_fields, "Position").pack(anchor="w", pady=(10, 0))
        self.step_position = ctk.CTkSegmentedButton(
            self.pos_fields,
            values=["Current Cursor", "Fixed Point"],
            command=self._on_step_position,
            font=FONTS["body"],
            selected_color=COLORS["accent"],
            selected_hover_color=COLORS["accent_hover"],
            unselected_color=COLORS["surface_alt"],
            unselected_hover_color=COLORS["border"],
            text_color=COLORS["text"],
        )
        self.step_position.pack(fill="x", pady=(6, 8))
        self.step_position.set("Current Cursor")
        self.step_coord_row = ctk.CTkFrame(self.pos_fields, fg_color="transparent")
        self.step_x = self._coord(self.step_coord_row, "X", "0")
        self.step_y = self._coord(self.step_coord_row, "Y", "0")
        self.pick_btn = ctk.CTkButton(
            self.step_coord_row,
            text="Pick",
            width=80,
            height=34,
            font=FONTS["body"],
            fg_color=COLORS["surface_alt"],
            hover_color=COLORS["border"],
            text_color=COLORS["text"],
            command=self._pick_position,
        )
        self.pick_btn.pack(side="left", padx=(8, 0), pady=(18, 0))

        ctk.CTkButton(
            add_inner,
            text="Add Step to Sequence",
            height=36,
            font=FONTS["button"],
            fg_color=COLORS["accent"],
            hover_color=COLORS["accent_hover"],
            command=self._add_step,
        ).pack(fill="x", pady=(14, 0))

        self.interval_block = IntervalBlock(
            scroll,
            title="Between Steps",
            apply_after_options=["each click / type / scroll step (not Wait steps)"],
        )
        self.interval_block.pack(fill="x", pady=(0, 12))

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
        self.count_col = ctk.CTkFrame(repeat_row, fg_color="transparent")
        field_label(self.count_col, "Count").pack(anchor="w")
        self.repeat_count = int_entry(self.count_col, width=90, default="1")
        self.repeat_count.pack(pady=(6, 0))
        self._delay_col = ctk.CTkFrame(repeat_row, fg_color="transparent")
        self._delay_col.pack(side="left", padx=(12, 0))
        field_label(self._delay_col, "Start delay (s)").pack(anchor="w")
        self.start_delay = int_entry(self._delay_col, width=90, default="2")
        self.start_delay.pack(pady=(6, 0))

        self.auto_stop_block = AutoStopBlock(scroll)
        self.auto_stop_block.pack(fill="x", pady=(0, 12))

        actions = ctk.CTkFrame(self, fg_color="transparent")
        actions.pack(fill="x", pady=(8, 0))
        self.start_btn = ctk.CTkButton(
            actions,
            text="Start Combo",
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

        self._on_step_action("Click")
        self._on_step_position("Current Cursor")
        self._on_repeat_mode("Once")

    def set_hotkey_tooltips(self, toggle_key: str, emergency_key: str) -> None:
        toggle = toggle_key.upper()
        emergency = emergency_key.upper()
        self.start_tip.set_text(f"Start / Stop  ·  Shortcut: {toggle}")
        self.stop_tip.set_text(f"Stop  ·  Shortcut: {emergency} (emergency)")

    def _coord(self, parent: ctk.CTkFrame, label: str, default: str) -> ctk.CTkEntry:
        col = ctk.CTkFrame(parent, fg_color="transparent")
        col.pack(side="left")
        field_label(col, label).pack(anchor="w")
        entry = int_entry(col, width=80, default=default)
        entry.pack(pady=(6, 0))
        return entry

    def _on_step_action(self, value: str) -> None:
        for frame in (
            self.click_fields,
            self.type_fields,
            self.scroll_fields,
            self.wait_fields,
            self.pos_fields,
        ):
            frame.pack_forget()
        if value == "Click":
            self.click_fields.pack(fill="x")
            self.pos_fields.pack(fill="x")
        elif value == "Type":
            self.type_fields.pack(fill="x")
        elif value == "Scroll":
            self.scroll_fields.pack(fill="x")
            self.pos_fields.pack(fill="x")
        else:
            self.wait_fields.pack(fill="x")

    def _on_step_position(self, value: str) -> None:
        hide_widget(self.step_coord_row)
        if value == "Fixed Point":
            self.step_coord_row.pack(fill="x")
            self.step_x.configure(state="normal")
            self.step_y.configure(state="normal")
            self.pick_btn.configure(state="normal")

    def _on_repeat_mode(self, value: str) -> None:
        hide_widget(self.count_col)
        hide_widget(self._delay_col)
        if value == "Fixed Count":
            self.count_col.pack(side="left", padx=(12, 0))
            self.repeat_count.configure(state="normal")
        self._delay_col.pack(side="left", padx=(12, 0))

    def _pick_position(self) -> None:
        if self.step_position.get() != "Fixed Point":
            return
        self.pick_btn.configure(text="…", state="disabled")
        self.after(1200, self._finish_pick)

    def _finish_pick(self) -> None:
        x, y = self._mouse.position
        set_entry_text(self.step_x, str(int(x)))
        set_entry_text(self.step_y, str(int(y)))
        if self.step_position.get() == "Fixed Point":
            self.step_x.configure(state="normal")
            self.step_y.configure(state="normal")
            self.pick_btn.configure(text="Pick", state="normal")
        else:
            self.pick_btn.configure(text="Pick", state="disabled")

    def _add_step(self) -> None:
        action = self.step_action.get().lower()
        step = ComboStep(action=action)
        if action in ("click", "scroll"):
            step.position_mode = (
                "current"
                if self.step_position.get() == "Current Cursor"
                else "fixed"
            )
            step.fixed_x = safe_int(self.step_x.get())
            step.fixed_y = safe_int(self.step_y.get())
        if action == "click":
            step.button = self.step_button.get().lower()
            step.click_type = self.step_click_type.get().lower()
        elif action == "type":
            step.text = self.step_text.get()
            step.press_enter = bool(self.step_press_enter.get())
            if not step.text and not step.press_enter:
                return
        elif action == "scroll":
            step.scroll_direction = self.step_scroll_dir.get().lower()
            step.scroll_amount = safe_int(self.step_scroll_amount.get(), 3, 1)
        elif action == "wait":
            step.wait_ms = safe_int(self.step_wait_ms.get(), 500, 1)
        self._steps.append(step)
        self._refresh_steps_view()

    def _remove_last(self) -> None:
        if self._steps:
            self._steps.pop()
            self._refresh_steps_view()

    def _clear_steps(self) -> None:
        self._steps.clear()
        self._refresh_steps_view()

    def _refresh_steps_view(self) -> None:
        lines: list[str] = []
        for index, step in enumerate(self._steps, start=1):
            lines.append(f"{index}. {self._format_step(step)}")
        self.steps_box.configure(state="normal")
        self.steps_box.delete("1.0", "end")
        self.steps_box.insert("1.0", "\n".join(lines) if lines else "(no steps yet)")
        self.steps_box.configure(state="disabled")

    @staticmethod
    def _format_step(step: ComboStep) -> str:
        if step.action == "click":
            pos = (
                f"@({step.fixed_x},{step.fixed_y})"
                if step.position_mode == "fixed"
                else "@cursor"
            )
            return f"CLICK {step.button} {step.click_type} {pos}"
        if step.action == "type":
            preview = step.text.replace("\n", "\\n")
            if len(preview) > 40:
                preview = preview[:37] + "..."
            enter = " +ENTER" if step.press_enter else ""
            return f'TYPE "{preview}"{enter}'
        if step.action == "scroll":
            return f"SCROLL {step.scroll_direction} x{step.scroll_amount}"
        if step.action == "wait":
            return f"WAIT {step.wait_ms}ms"
        return step.action.upper()

    def set_running(self, running: bool) -> None:
        self.start_btn.configure(state="disabled" if running else "normal")
        self.stop_btn.configure(state="normal" if running else "disabled")

    def get_config(self) -> ComboConfig:
        mode_map = {
            "Once": "once",
            "Fixed Count": "count",
            "Unlimited": "unlimited",
        }
        return ComboConfig(
            steps=list(self._steps),
            interval=self.interval_block.get_config(),
            repeat_mode=mode_map.get(self.repeat_mode.get(), "once"),
            repeat_count=safe_int(self.repeat_count.get(), 1, 1),
            start_delay=safe_float(self.start_delay.get(), 2.0),
            auto_stop=self.auto_stop_block.get_config(),
        )

    def export_settings(self) -> dict[str, Any]:
        cfg = self.get_config()
        return {
            "steps": [step.to_dict() for step in cfg.steps],
            "interval": cfg.interval.to_dict(),
            "repeat_mode": cfg.repeat_mode,
            "repeat_count": cfg.repeat_count,
            "start_delay": cfg.start_delay,
            "auto_stop": cfg.auto_stop.to_dict(),
        }

    def _load_settings(self) -> None:
        s = self._settings
        self._steps = [ComboStep.from_dict(item) for item in s.get("steps", [])]
        self._refresh_steps_view()
        self.interval_block.load_config(
            IntervalConfig.from_dict(s.get("interval", {}))
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
        self.auto_stop_block.load_config(
            AutoStopConfig.from_dict(s.get("auto_stop", {}))
        )

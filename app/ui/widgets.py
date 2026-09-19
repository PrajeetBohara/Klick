"""Reusable UI helpers."""

from __future__ import annotations

import customtkinter as ctk

from app.ui.theme import COLORS, FONTS


def section_label(parent: ctk.CTkBaseClass, text: str) -> ctk.CTkLabel:
    return ctk.CTkLabel(
        parent,
        text=text.upper(),
        font=FONTS["section"],
        text_color=COLORS["muted"],
        anchor="w",
    )


def field_label(parent: ctk.CTkBaseClass, text: str) -> ctk.CTkLabel:
    return ctk.CTkLabel(
        parent,
        text=text,
        font=FONTS["body"],
        text_color=COLORS["text"],
        anchor="w",
    )


def int_entry(
    parent: ctk.CTkBaseClass,
    width: int = 72,
    default: str = "0",
) -> ctk.CTkEntry:
    entry = ctk.CTkEntry(
        parent,
        width=width,
        height=34,
        font=FONTS["mono"],
        fg_color=COLORS["surface_alt"],
        border_color=COLORS["border"],
        text_color=COLORS["text"],
        justify="center",
    )
    entry.insert(0, default)
    return entry


def safe_int(value: str, fallback: int = 0, minimum: int = 0) -> int:
    try:
        return max(minimum, int(value.strip()))
    except (TypeError, ValueError):
        return fallback


def safe_float(value: str, fallback: float = 0.0, minimum: float = 0.0) -> float:
    try:
        return max(minimum, float(value.strip()))
    except (TypeError, ValueError):
        return fallback

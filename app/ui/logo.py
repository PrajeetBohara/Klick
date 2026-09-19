"""Header logo placeholder / loader."""

from __future__ import annotations

from pathlib import Path

import customtkinter as ctk
from PIL import Image

from app.ui.theme import COLORS, FONTS

# Drop your logo file here (PNG/JPG preferred).
LOGO_CANDIDATES = (
    Path(__file__).resolve().parents[2] / "assets" / "logo.png",
    Path(__file__).resolve().parents[2] / "assets" / "logo.jpg",
    Path(__file__).resolve().parents[2] / "assets" / "logo.webp",
)

# Default display size (change these, or pass height=/width= where LogoPlaceholder is created).
DEFAULT_LOGO_HEIGHT = 100
DEFAULT_LOGO_WIDTH = 100


class LogoPlaceholder(ctk.CTkFrame):
    """Shows assets/logo.png when present; otherwise a clear logo drop zone."""

    def __init__(
        self,
        master: ctk.CTkBaseClass,
        height: int = DEFAULT_LOGO_HEIGHT,
        width: int = DEFAULT_LOGO_WIDTH,
        **kwargs,
    ) -> None:
        super().__init__(
            master,
            fg_color=COLORS["surface"],
            corner_radius=10,
            border_width=1,
            border_color=COLORS["border"],
            height=height,
            width=width,
            **kwargs,
        )
        self.pack_propagate(False)
        self._image_ref: ctk.CTkImage | None = None
        self._content: ctk.CTkBaseClass | None = None
        self._render(height=height, width=width)

    def _render(self, height: int, width: int) -> None:
        for path in LOGO_CANDIDATES:
            if path.exists():
                try:
                    pil = Image.open(path)
                    self._image_ref = ctk.CTkImage(
                        light_image=pil,
                        dark_image=pil,
                        size=(max(1, width), max(1, height)),
                    )
                    self.configure(
                        width=width,
                        height=height,
                        fg_color="transparent",
                        border_width=0,
                    )
                    self._content = ctk.CTkLabel(
                        self, text="", image=self._image_ref, fg_color="transparent"
                    )
                    self._content.pack(expand=True)
                    return
                except Exception:
                    break

        self.configure(width=width, height=height)
        self._content = ctk.CTkLabel(
            self,
            text="Your logo here",
            font=FONTS["body"],
            text_color=COLORS["muted"],
            fg_color="transparent",
        )
        self._content.pack(expand=True, padx=16, pady=8)

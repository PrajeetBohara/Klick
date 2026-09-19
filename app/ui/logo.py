"""Header logo and window icon helpers."""

from __future__ import annotations

from pathlib import Path

import customtkinter as ctk
from PIL import Image, ImageTk

from app.ui.theme import COLORS, FONTS

ASSETS_DIR = Path(__file__).resolve().parents[2] / "assets"
HEADER_LOGO_PATH = ASSETS_DIR / "text_logo.png"
WINDOW_ICON_PATH = ASSETS_DIR / "klick_logo.png"

# Header logo display sizing (width follows image aspect after trim).
HEADER_LOGO_HEIGHT = 56
HEADER_LOGO_MAX_WIDTH = 280


def _trim_transparent(image: Image.Image) -> Image.Image:
    """Crop away empty transparent padding so the logo fills the frame."""
    rgba = image.convert("RGBA")
    bbox = rgba.getbbox()
    if bbox:
        return rgba.crop(bbox)
    return rgba


def load_header_logo_image(
    height: int = HEADER_LOGO_HEIGHT,
    max_width: int = HEADER_LOGO_MAX_WIDTH,
) -> tuple[ctk.CTkImage, int, int] | None:
    if not HEADER_LOGO_PATH.exists():
        return None
    pil = _trim_transparent(Image.open(HEADER_LOGO_PATH))
    ratio = height / max(pil.height, 1)
    width = max(1, int(pil.width * ratio))
    if width > max_width:
        width = max_width
        height = max(1, int(pil.height * (max_width / max(pil.width, 1))))
    ctk_image = ctk.CTkImage(
        light_image=pil,
        dark_image=pil,
        size=(width, height),
    )
    return ctk_image, width, height


def apply_window_icon(window: ctk.CTk) -> ImageTk.PhotoImage | None:
    """Set the title-bar / taskbar icon from klick_logo.png. Keep the returned ref."""
    if not WINDOW_ICON_PATH.exists():
        return None
    pil = Image.open(WINDOW_ICON_PATH).convert("RGBA")
    # Multi-size friendly: use a crisp square for the title bar.
    icon = pil.resize((64, 64), Image.Resampling.LANCZOS)
    photo = ImageTk.PhotoImage(icon)
    window.iconphoto(True, photo)
    # Also write a temporary .ico path via iconbitmap on Windows when possible
    try:
        ico_path = ASSETS_DIR / "klick_logo.ico"
        if not ico_path.exists():
            pil.resize((256, 256), Image.Resampling.LANCZOS).save(
                ico_path,
                format="ICO",
                sizes=[(16, 16), (32, 32), (48, 48), (64, 64), (256, 256)],
            )
        window.iconbitmap(default=str(ico_path))
    except Exception:
        pass
    return photo


class LogoPlaceholder(ctk.CTkFrame):
    """Shows assets/text_logo.png sized to the logo; otherwise a drop-zone placeholder."""

    def __init__(
        self,
        master: ctk.CTkBaseClass,
        height: int = HEADER_LOGO_HEIGHT,
        max_width: int = HEADER_LOGO_MAX_WIDTH,
        **kwargs,
    ) -> None:
        super().__init__(
            master,
            fg_color=COLORS["surface"],
            corner_radius=10,
            border_width=1,
            border_color=COLORS["border"],
            **kwargs,
        )
        self.pack_propagate(False)
        self._image_ref: ctk.CTkImage | None = None
        self._content: ctk.CTkBaseClass | None = None
        self._render(height=height, max_width=max_width)

    def _render(self, height: int, max_width: int) -> None:
        loaded = load_header_logo_image(height=height, max_width=max_width)
        if loaded is not None:
            self._image_ref, width, height = loaded
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

        self.configure(width=160, height=height)
        self._content = ctk.CTkLabel(
            self,
            text="Your logo here",
            font=FONTS["body"],
            text_color=COLORS["muted"],
            fg_color="transparent",
        )
        self._content.pack(expand=True, padx=16, pady=8)

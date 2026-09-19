# Brand assets

| File | Purpose |
|------|---------|
| `text_logo.png` | App header logo (transparent padding is trimmed automatically) |
| `klick_logo.png` | Window title bar and taskbar icon |
| `klick_logo.ico` | Optional generated Windows icon (created at runtime if needed) |

## Header size

Edit defaults in `app/ui/logo.py`:

```python
HEADER_LOGO_HEIGHT = 56
HEADER_LOGO_MAX_WIDTH = 280
```

Or pass values when creating the logo widget in `app/main_window.py`.

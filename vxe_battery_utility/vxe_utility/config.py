from pathlib import Path
from PyQt6.QtGui import QColor

# Hardware Constants (Compx / VXE / ATK)
VENDOR_IDS = [0x3554, 0x373B, 0x25A7]
REPORT_ID = 0x08
DEFAULT_CAPACITY_MAH = 500
EST_MAX_RUNTIME_HOURS = 65

# Polling & Storage
POLL_INTERVAL_MS = 10000
HOVER_CHECK_MS = 120
HISTORY_RETENTION_HOURS = 48
HISTORY_MIN_INTERVAL_SEC = 300
HISTORY_FILE = Path.home() / ".vxe_battery_history.json"

# UI Dimensions
OSD_WIDTH = 330
OSD_HEIGHT = 96
PANEL_WIDTH = 370
PANEL_HEIGHT = 470


def lerp_color(c1: tuple[int, int, int], c2: tuple[int, int, int], t: float, alpha: int = 255) -> QColor:
    """Linearly interpolates between two RGB tuples by factor t (0.0 to 1.0)."""
    t = max(0.0, min(1.0, t))
    r = int(c1[0] + (c2[0] - c1[0]) * t)
    g = int(c1[1] + (c2[1] - c1[1]) * t)
    b = int(c1[2] + (c2[2] - c1[2]) * t)
    return QColor(r, g, b, alpha)


def get_battery_palette(pct: float) -> tuple[QColor, QColor, QColor, QColor, QColor]:
    """
    Returns (top_col, bot_col, back_col, crest_col, border_col) smoothly
    interpolated from Emerald Green (100%) -> Amber (50%) -> Crimson Red (0%).
    """
    ratio = max(0.0, min(1.0, pct / 100.0))

    red_top, red_bot = (245, 65, 65), (145, 22, 22)
    amb_top, amb_bot = (245, 185, 45), (165, 100, 15)
    grn_top, grn_bot = (42, 218, 108), (16, 132, 64)

    if ratio >= 0.5:
        t = (ratio - 0.5) / 0.5  # 0.0 at 50%, 1.0 at 100%
        top_col = lerp_color(amb_top, grn_top, t, 235)
        bot_col = lerp_color(amb_bot, grn_bot, t, 245)
        back_col = lerp_color(amb_bot, grn_bot, t, 175)
        crest_col = lerp_color((255, 230, 140), (160, 255, 195), t, 205)
        border_col = lerp_color(amb_top, grn_top, t, 135)
    else:
        t = ratio / 0.5  # 0.0 at 0%, 1.0 at 50%
        top_col = lerp_color(red_top, amb_top, t, 235)
        bot_col = lerp_color(red_bot, amb_bot, t, 245)
        back_col = lerp_color(red_bot, amb_bot, t, 175)
        crest_col = lerp_color((255, 165, 165), (255, 230, 140), t, 205)
        border_col = lerp_color(red_top, amb_top, t, 135)

    return top_col, bot_col, back_col, crest_col, border_col

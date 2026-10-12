"""
Modern Dark Sports Theme for Minaram Cup Tournament Management System.
Deep charcoal backgrounds with football pitch emerald green accents.
"""

# Color Palette
BG_MAIN = "#0F1115"
BG_SIDEBAR = "#14171E"
BG_TOPBAR = "#161A22"
BG_CARD = "#1C212B"
BG_CARD_HOVER = "#232A37"
BG_INPUT = "#161B23"
BG_ROW_ALT = "#181D26"
BORDER_COLOR = "#2A3241"

# Pitch Green Accents
ACCENT_GREEN = "#10B981"
ACCENT_GREEN_HOVER = "#059669"
ACCENT_GREEN_MUTED = "#064E3B"
ACCENT_GREEN_TEXT = "#34D399"

# Functional Colors
TEXT_PRIMARY = "#F9FAFB"
TEXT_SECONDARY = "#9CA3AF"
TEXT_MUTED = "#6B7280"
TEXT_DARK = "#111827"

COLOR_DANGER = "#EF4444"
COLOR_DANGER_HOVER = "#DC2626"
COLOR_DANGER_MUTED = "#7F1D1D"

COLOR_WARNING = "#F59E0B"
COLOR_WARNING_MUTED = "#78350F"

COLOR_INFO = "#3B82F6"
COLOR_INFO_MUTED = "#1E3A8A"

COLOR_PURPLE = "#8B5CF6"
COLOR_PURPLE_MUTED = "#4C1D95"

# Status Badges
STATUS_COLORS = {
    "Confirmed": (ACCENT_GREEN_MUTED, ACCENT_GREEN_TEXT),
    "Pending": (COLOR_WARNING_MUTED, "#FCD34D"),
    "Duplicate": (COLOR_DANGER_MUTED, "#FCA5A5"),
    "Rejected": (COLOR_DANGER_MUTED, "#FCA5A5"),
    "Scheduled": (COLOR_INFO_MUTED, "#93C5FD"),
    "In Progress": (COLOR_PURPLE_MUTED, "#C4B5FD"),
    "Completed": (ACCENT_GREEN_MUTED, ACCENT_GREEN_TEXT),
    "Postponed": (COLOR_WARNING_MUTED, "#FCD34D"),
    "Cancelled": (COLOR_DANGER_MUTED, "#FCA5A5"),
    "Walkover": (COLOR_INFO_MUTED, "#93C5FD"),
}


def get_status_colors(status: str):
    return STATUS_COLORS.get(status, (BORDER_COLOR, TEXT_SECONDARY))


# ----------------------------------------------------
# Global Font Cache (Prevents GDI Handle & RAM Leaks)
# ----------------------------------------------------
import customtkinter as ctk
from typing import Dict, Tuple, Optional

_FONT_CACHE: Dict[Tuple, ctk.CTkFont] = {}
_orig_font_new = ctk.CTkFont.__new__
_orig_font_init = ctk.CTkFont.__init__


def _normalize_font_key(*args, **kwargs):
    family = args[0] if len(args) > 0 else kwargs.get("family", None)
    size = args[1] if len(args) > 1 else kwargs.get("size", None)
    weight = args[2] if len(args) > 2 else kwargs.get("weight", None)
    slant = args[3] if len(args) > 3 else kwargs.get("slant", "roman")
    underline = args[4] if len(args) > 4 else kwargs.get("underline", False)
    overstrike = args[5] if len(args) > 5 else kwargs.get("overstrike", False)
    return (family, size, weight, slant, underline, overstrike)


def _cached_font_new(cls, *args, **kwargs):
    key = _normalize_font_key(*args, **kwargs)
    if key in _FONT_CACHE:
        cached = _FONT_CACHE[key]
        try:
            _ = cached.cget("size")
            return cached
        except Exception:
            _FONT_CACHE.pop(key, None)
    try:
        inst = _orig_font_new(cls)
        _FONT_CACHE[key] = inst
        return inst
    except Exception:
        return _orig_font_new(cls)


def _cached_font_init(self, *args, **kwargs):
    if getattr(self, "_is_cached_initialized", False):
        return
    _orig_font_init(self, *args, **kwargs)
    self._is_cached_initialized = True


# Apply global monkey patch
ctk.CTkFont.__new__ = _cached_font_new
ctk.CTkFont.__init__ = _cached_font_init


def get_font(size: int = 12, weight: str = "normal", family: Optional[str] = None) -> ctk.CTkFont:
    """
    Return a shared cached CTkFont instance.
    Prevents allocating thousands of orphaned Tk font handles during table re-renders,
    keeping application memory footprint minimal and eliminating UI lag.
    """
    return ctk.CTkFont(family=family, size=size, weight=weight)


"""
Modal dialog window base and confirmation popups.
Uses tk.Toplevel directly (NOT CTkToplevel) to avoid the Windows DWM
withdraw/deiconify blink cycle that CTkToplevel triggers on every open.
"""

import tkinter as tk
import customtkinter as ctk
from typing import Optional, Callable
from app.ui import theme


class BaseModal(tk.Toplevel):
    """
    Blink-free modal dialog base class.
    Inherits from tk.Toplevel to bypass the CTkToplevel DWM titlebar
    color cycle (which causes the window to flash then disappear).
    Widgets inside are still regular CTk widgets with correct styling.
    """

    def __init__(self, parent, title: str = "Dialog", width: int = 500, height: int = 400):
        # Resolve the true root Tk window as master
        if hasattr(parent, "winfo_toplevel"):
            root = parent.winfo_toplevel()
        else:
            root = parent

        super().__init__(root)

        self.parent = parent

        # ── Appearance ──────────────────────────────────────────────────
        self.title(title)
        self.configure(bg=theme.BG_MAIN)
        self.resizable(False, False)

        # ── Geometry: center on parent ───────────────────────────────────
        self.update_idletasks()
        try:
            if root and root.winfo_viewable():
                px = root.winfo_rootx()
                py = root.winfo_rooty()
                pw = root.winfo_width()
                ph = root.winfo_height()
                x = px + max(0, (pw - width) // 2)
                y = py + max(0, (ph - height) // 2)
            else:
                sw = self.winfo_screenwidth()
                sh = self.winfo_screenheight()
                x = max(0, (sw - width) // 2)
                y = max(0, (sh - height) // 2)
            self.geometry(f"{width}x{height}+{x}+{y}")
        except Exception:
            self.geometry(f"{width}x{height}")

        # ── Window management ────────────────────────────────────────────
        try:
            self.transient(root)
        except Exception:
            pass

        self.lift()
        self.focus_force()

        # Grab focus AFTER the event loop settles (avoids grab errors)
        self.after(50, self._safe_grab)
        self.protocol("WM_DELETE_WINDOW", self.destroy)

        # ── Layout ───────────────────────────────────────────────────────
        # Outer container card
        self.container = ctk.CTkFrame(
            self,
            fg_color=theme.BG_CARD,
            border_color=theme.BORDER_COLOR,
            border_width=1,
            corner_radius=12
        )
        self.container.pack(fill="both", expand=True, padx=16, pady=16)

        # Header row
        self.header_frame = ctk.CTkFrame(self.container, fg_color="transparent")
        self.header_frame.pack(fill="x", padx=20, pady=(16, 12))

        self.title_label = ctk.CTkLabel(
            self.header_frame,
            text=title,
            font=theme.get_font(18, "bold"),
            text_color=theme.TEXT_PRIMARY
        )
        self.title_label.pack(side="left")

        self.close_btn = ctk.CTkButton(
            self.header_frame,
            text="✕",
            width=28,
            height=28,
            fg_color="transparent",
            hover_color=theme.BG_CARD_HOVER,
            text_color=theme.TEXT_SECONDARY,
            font=theme.get_font(14, "bold"),
            command=self.destroy
        )
        self.close_btn.pack(side="right")

        # Body content frame
        self.body_frame = ctk.CTkFrame(self.container, fg_color="transparent")
        self.body_frame.pack(fill="both", expand=True, padx=20, pady=(0, 16))

    def _safe_grab(self):
        """Grab input focus safely — called after a short delay."""
        try:
            if self.winfo_exists():
                self.grab_set()
        except Exception:
            pass

    def destroy(self):
        try:
            self.grab_release()
        except Exception:
            pass
        try:
            super().destroy()
        except Exception:
            pass


class ConfirmDialog(BaseModal):
    def __init__(
        self,
        parent,
        title: str = "Confirm Action",
        message: str = "Are you sure you want to proceed?",
        confirm_text: str = "Confirm",
        cancel_text: str = "Cancel",
        is_danger: bool = False,
        on_confirm: Optional[Callable[[], None]] = None
    ):
        super().__init__(parent, title=title, width=460, height=240)
        self.on_confirm = on_confirm

        msg_label = ctk.CTkLabel(
            self.body_frame,
            text=message,
            font=theme.get_font(14),
            text_color=theme.TEXT_SECONDARY,
            wraplength=400,
            justify="left"
        )
        msg_label.pack(fill="both", expand=True, pady=12)

        btn_row = ctk.CTkFrame(self.body_frame, fg_color="transparent")
        btn_row.pack(fill="x", pady=(12, 0))

        cancel_btn = ctk.CTkButton(
            btn_row,
            text=cancel_text,
            width=100,
            fg_color="transparent",
            border_color=theme.BORDER_COLOR,
            border_width=1,
            hover_color=theme.BG_CARD_HOVER,
            text_color=theme.TEXT_PRIMARY,
            command=self.destroy
        )
        cancel_btn.pack(side="right", padx=(8, 0))

        conf_color = theme.COLOR_DANGER if is_danger else theme.ACCENT_GREEN
        conf_hover = theme.COLOR_DANGER_HOVER if is_danger else theme.ACCENT_GREEN_HOVER

        confirm_btn = ctk.CTkButton(
            btn_row,
            text=confirm_text,
            width=110,
            fg_color=conf_color,
            hover_color=conf_hover,
            text_color="#FFFFFF" if is_danger else theme.TEXT_DARK,
            font=theme.get_font(12, "bold"),
            command=self._handle_confirm
        )
        confirm_btn.pack(side="right")

    def _handle_confirm(self):
        self.destroy()
        if self.on_confirm:
            self.on_confirm()

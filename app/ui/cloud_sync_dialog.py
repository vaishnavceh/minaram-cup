"""
Cloud Synchronization Modal Dialog for Minaram Cup Desktop Manager.
Provides an interactive 1-click execution interface to push updates directly
to the Render FastAPI cloud backend, publishing changes to Vercel instantly.
"""

import threading
import customtkinter as ctk
from tkinter import messagebox
from typing import Optional, Callable
from app.ui import theme
from app.ui.modal import BaseModal
from app.cloud_sync_service import (
    get_cloud_config,
    save_cloud_config,
    push_database,
    pull_database,
    DEFAULT_BACKEND_URL
)


class CloudSyncModal(BaseModal):
    def __init__(self, parent, on_sync_completed: Optional[Callable[[], None]] = None):
        super().__init__(parent, title="☁️ Cloud Sync (Render API)", width=560, height=480)
        self.on_sync_completed = on_sync_completed
        self.is_syncing = False

        self.cfg = get_cloud_config()
        self.build_ui()

    def build_ui(self):
        # Description
        desc_lbl = ctk.CTkLabel(
            self.container,
            text="Publish local tournament database changes directly to your Render cloud API.\nChanges reflect in real-time on your Vercel public web platform.",
            font=ctk.CTkFont(size=11),
            text_color=theme.TEXT_MUTED,
            justify="left",
            wraplength=500
        )
        desc_lbl.pack(fill="x", padx=20, pady=(0, 14))

        # Config Card
        card = ctk.CTkFrame(self.container, fg_color=theme.BG_INPUT, corner_radius=8, border_color=theme.BORDER_COLOR, border_width=1)
        card.pack(fill="x", padx=20, pady=(0, 14))

        # Backend URL row
        u_box = ctk.CTkFrame(card, fg_color="transparent")
        u_box.pack(fill="x", padx=14, pady=(12, 6))
        ctk.CTkLabel(u_box, text="Render Backend URL:", font=ctk.CTkFont(size=11, weight="bold"), text_color=theme.TEXT_SECONDARY).pack(anchor="w")
        self.url_entry = ctk.CTkEntry(u_box, fg_color=theme.BG_CARD, border_color=theme.BORDER_COLOR)
        self.url_entry.pack(fill="x", pady=(4, 0))
        self.url_entry.insert(0, self.cfg.get("backend_url", DEFAULT_BACKEND_URL))

        # Admin Password row
        p_box = ctk.CTkFrame(card, fg_color="transparent")
        p_box.pack(fill="x", padx=14, pady=(6, 12))
        ctk.CTkLabel(p_box, text="Admin Sync Password:", font=ctk.CTkFont(size=11, weight="bold"), text_color=theme.TEXT_SECONDARY).pack(anchor="w")
        self.pwd_entry = ctk.CTkEntry(p_box, show="•", fg_color=theme.BG_CARD, border_color=theme.BORDER_COLOR)
        self.pwd_entry.pack(fill="x", pady=(4, 0))
        self.pwd_entry.insert(0, self.cfg.get("admin_password", "minaram2026"))

        # Status & Progress Box
        self.status_box = ctk.CTkFrame(self.container, fg_color=theme.BG_CARD_HOVER, corner_radius=8)
        self.status_box.pack(fill="x", padx=20, pady=(0, 16))

        self.status_lbl = ctk.CTkLabel(
            self.status_box,
            text=f"Status: Ready to sync  •  Last: {self.cfg.get('last_sync_time') or 'Never'}",
            font=ctk.CTkFont(size=11),
            text_color=theme.TEXT_PRIMARY
        )
        self.status_lbl.pack(padx=14, pady=(10, 6), anchor="w")

        self.progress_bar = ctk.CTkProgressBar(self.status_box, height=6, mode="indeterminate", progress_color="#0284c7")
        self.progress_bar.pack(fill="x", padx=14, pady=(0, 10))
        self.progress_bar.set(0)

        # Buttons Frame
        btn_frame = ctk.CTkFrame(self.container, fg_color="transparent")
        btn_frame.pack(fill="x", padx=20, pady=(0, 10))

        self.push_btn = ctk.CTkButton(
            btn_frame,
            text="🚀 Push Updates to Render",
            fg_color="#0284c7",
            hover_color="#0369a1",
            text_color="white",
            font=ctk.CTkFont(size=13, weight="bold"),
            height=36,
            command=self.start_push
        )
        self.push_btn.pack(side="left", fill="x", expand=True, padx=(0, 6))

        self.pull_btn = ctk.CTkButton(
            btn_frame,
            text="📥 Pull from Cloud",
            fg_color=theme.BG_INPUT,
            hover_color=theme.BG_CARD_HOVER,
            text_color=theme.TEXT_SECONDARY,
            border_color=theme.BORDER_COLOR,
            border_width=1,
            font=ctk.CTkFont(size=12),
            height=36,
            command=self.start_pull
        )
        self.pull_btn.pack(side="right", padx=(6, 0))

        # Bottom Notice
        ctk.CTkLabel(
            self.container,
            text="Tip: Render free tier services automatically spin down when idle.\nIf it takes ~30-50s on the first sync, it is simply waking up.",
            font=ctk.CTkFont(size=10),
            text_color=theme.TEXT_MUTED,
            justify="center"
        ).pack(fill="x", padx=20, pady=(4, 0))

    def set_syncing(self, is_syncing: bool, message: str = ""):
        self.is_syncing = is_syncing
        if is_syncing:
            self.push_btn.configure(state="disabled", text="⏳ Syncing...")
            self.pull_btn.configure(state="disabled")
            self.url_entry.configure(state="disabled")
            self.pwd_entry.configure(state="disabled")
            self.progress_bar.start()
            if message:
                self.status_lbl.configure(text=f"🔄 {message}", text_color="#38bdf8")
        else:
            self.push_btn.configure(state="normal", text="🚀 Push Updates to Render")
            self.pull_btn.configure(state="normal")
            self.url_entry.configure(state="normal")
            self.pwd_entry.configure(state="normal")
            self.progress_bar.stop()
            self.progress_bar.set(0)
            if message:
                self.status_lbl.configure(text=message)

    def start_push(self):
        url = self.url_entry.get().strip()
        pwd = self.pwd_entry.get().strip()

        if not url:
            messagebox.showwarning("URL Missing", "Please enter your Render Backend URL.")
            return

        save_cloud_config(url, admin_password=pwd)
        self.set_syncing(True, "Connecting to Render and checkpointing SQLite...")

        def worker():
            def on_progress(p_msg: str):
                self.after(0, lambda: self.status_lbl.configure(text=f"🔄 {p_msg}"))

            ok, msg = push_database(base_url=url, password=pwd, progress_callback=on_progress)
            self.after(0, lambda: self._on_push_finished(ok, msg))

        threading.Thread(target=worker, daemon=True).start()

    def _on_push_finished(self, ok: bool, msg: str):
        cfg = get_cloud_config()
        last_t = cfg.get("last_sync_time") or "Just now"
        if ok:
            self.set_syncing(False, f"✅ Successfully synced to Render at {last_t}!")
            self.status_lbl.configure(text_color="#4ade80")
            messagebox.showinfo("Render Cloud Sync Complete", "Database successfully synchronized to Render!\n\nAll tournament standings, fixtures, and results are now live on your Vercel public website.")
            if self.on_sync_completed:
                self.on_sync_completed()
        else:
            self.set_syncing(False, f"❌ Sync Failed")
            self.status_lbl.configure(text_color="#f87171")
            messagebox.showerror("Sync Failed", f"Could not push to Render cloud:\n\n{msg}\n\nPlease check that your Render backend URL is correct and active.")

    def start_pull(self):
        url = self.url_entry.get().strip()
        pwd = self.pwd_entry.get().strip()

        if not url:
            messagebox.showwarning("URL Missing", "Please enter your Render Backend URL.")
            return

        if not messagebox.askyesno("Confirm Pull", "This will download the cloud database and overwrite local data.\nA safety local backup will be created first.\n\nProceed?"):
            return

        save_cloud_config(url, admin_password=pwd)
        self.set_syncing(True, "Connecting and downloading from cloud...")

        def worker():
            def on_progress(p_msg: str):
                self.after(0, lambda: self.status_lbl.configure(text=f"🔄 {p_msg}"))

            ok, msg = pull_database(base_url=url, password=pwd, progress_callback=on_progress)
            self.after(0, lambda: self._on_pull_finished(ok, msg))

        threading.Thread(target=worker, daemon=True).start()

    def _on_pull_finished(self, ok: bool, msg: str):
        cfg = get_cloud_config()
        last_t = cfg.get("last_sync_time") or "Just now"
        if ok:
            self.set_syncing(False, f"✅ Cloud Database Downloaded at {last_t}!")
            self.status_lbl.configure(text_color="#4ade80")
            messagebox.showinfo("Pull Complete", "Latest cloud database downloaded successfully.\nLocal desktop manager now has the latest cloud data.")
            if self.on_sync_completed:
                self.on_sync_completed()
        else:
            self.set_syncing(False, f"❌ Pull Failed")
            self.status_lbl.configure(text_color="#f87171")
            messagebox.showerror("Pull Failed", f"Could not pull from cloud:\n\n{msg}")

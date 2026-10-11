"""
Settings and administration interface: tournament rules, scoring points,
tie-breakers, SQLite backup/restore, sample data generation, and clean reset.
"""

import os
import platform
import subprocess
import customtkinter as ctk
from tkinter import messagebox
from pathlib import Path

from app.ui import theme
from app.ui.modal import BaseModal, ConfirmDialog
from app.database import Database
from app.models import TournamentSettings
from app.tournament_manager import TournamentManager
from app.backup_service import BackupService
from app.cloud_sync_service import (
    get_cloud_config,
    save_cloud_config,
    push_database,
    pull_database,
    DEFAULT_BACKEND_URL
)
from app.ui.cloud_sync_dialog import CloudSyncModal


class SettingsView(ctk.CTkScrollableFrame):
    def __init__(self, parent, db: Database, on_settings_changed=None):
        super().__init__(parent, fg_color="transparent")
        self.db = db
        self.on_settings_changed = on_settings_changed
        self.tourn_mgr = TournamentManager(db)
        self.backup_service = db.get_backup_service()

        self.build_ui()

    def refresh(self):
        self.load_settings_values()
        self.load_backups_list()

    def build_ui(self):
        # Header
        hdr = ctk.CTkFrame(self, fg_color="transparent")
        hdr.pack(fill="x", padx=16, pady=(12, 12))

        title_box = ctk.CTkFrame(hdr, fg_color="transparent")
        title_box.pack(side="left")
        ctk.CTkLabel(title_box, text="Tournament Configuration & Settings", font=ctk.CTkFont(size=20, weight="bold"), text_color=theme.TEXT_PRIMARY).pack(anchor="w")
        ctk.CTkLabel(title_box, text="Configure competition identity, scoring rules, tie-breaker orders, and database backups", font=ctk.CTkFont(size=11), text_color=theme.TEXT_MUTED).pack(anchor="w")

        # Container
        self.container = ctk.CTkFrame(self, fg_color="transparent")
        self.container.pack(fill="both", expand=True, padx=16, pady=(0, 20))

        # 1. Tournament Identity & Rules Card
        rules_card = ctk.CTkFrame(self.container, fg_color=theme.BG_CARD, corner_radius=10, border_color=theme.BORDER_COLOR, border_width=1)
        rules_card.pack(fill="x", pady=(0, 16))

        r_hdr = ctk.CTkFrame(rules_card, fg_color="transparent")
        r_hdr.pack(fill="x", padx=16, pady=(14, 10))
        ctk.CTkLabel(r_hdr, text="Tournament Identity & Scoring Rules", font=ctk.CTkFont(size=14, weight="bold"), text_color=theme.TEXT_PRIMARY).pack(side="left")

        # Identity Grid
        id_grid = ctk.CTkFrame(rules_card, fg_color="transparent")
        id_grid.pack(fill="x", padx=16, pady=(0, 10))
        id_grid.columnconfigure(0, weight=1)
        id_grid.columnconfigure(1, weight=1)
        id_grid.columnconfigure(2, weight=1)

        # Name
        b1 = ctk.CTkFrame(id_grid, fg_color="transparent")
        b1.grid(row=0, column=0, padx=4, sticky="ew")
        ctk.CTkLabel(b1, text="Tournament Name:", font=ctk.CTkFont(size=11), text_color=theme.TEXT_SECONDARY).pack(anchor="w")
        self.name_entry = ctk.CTkEntry(b1, fg_color=theme.BG_INPUT, border_color=theme.BORDER_COLOR)
        self.name_entry.pack(fill="x", pady=(2, 0))

        # Edition
        b2 = ctk.CTkFrame(id_grid, fg_color="transparent")
        b2.grid(row=0, column=1, padx=4, sticky="ew")
        ctk.CTkLabel(b2, text="Edition / Season:", font=ctk.CTkFont(size=11), text_color=theme.TEXT_SECONDARY).pack(anchor="w")
        self.edition_entry = ctk.CTkEntry(b2, fg_color=theme.BG_INPUT, border_color=theme.BORDER_COLOR)
        self.edition_entry.pack(fill="x", pady=(2, 0))

        # Sport
        b3 = ctk.CTkFrame(id_grid, fg_color="transparent")
        b3.grid(row=0, column=2, padx=4, sticky="ew")
        ctk.CTkLabel(b3, text="Sport Type:", font=ctk.CTkFont(size=11), text_color=theme.TEXT_SECONDARY).pack(anchor="w")
        self.sport_entry = ctk.CTkEntry(b3, fg_color=theme.BG_INPUT, border_color=theme.BORDER_COLOR)
        self.sport_entry.pack(fill="x", pady=(2, 0))

        # Scoring & Match Defaults Grid
        sc_grid = ctk.CTkFrame(rules_card, fg_color="transparent")
        sc_grid.pack(fill="x", padx=16, pady=(8, 10))
        sc_grid.columnconfigure(0, weight=1)
        sc_grid.columnconfigure(1, weight=1)
        sc_grid.columnconfigure(2, weight=1)
        sc_grid.columnconfigure(3, weight=1)

        s1 = ctk.CTkFrame(sc_grid, fg_color="transparent")
        s1.grid(row=0, column=0, padx=4, sticky="ew")
        ctk.CTkLabel(s1, text="Win Points:", font=ctk.CTkFont(size=11), text_color=theme.TEXT_SECONDARY).pack(anchor="w")
        self.win_pts_entry = ctk.CTkEntry(s1, fg_color=theme.BG_INPUT, border_color=theme.BORDER_COLOR)
        self.win_pts_entry.pack(fill="x", pady=(2, 0))

        s2 = ctk.CTkFrame(sc_grid, fg_color="transparent")
        s2.grid(row=0, column=1, padx=4, sticky="ew")
        ctk.CTkLabel(s2, text="Draw Points:", font=ctk.CTkFont(size=11), text_color=theme.TEXT_SECONDARY).pack(anchor="w")
        self.draw_pts_entry = ctk.CTkEntry(s2, fg_color=theme.BG_INPUT, border_color=theme.BORDER_COLOR)
        self.draw_pts_entry.pack(fill="x", pady=(2, 0))

        s3 = ctk.CTkFrame(sc_grid, fg_color="transparent")
        s3.grid(row=0, column=2, padx=4, sticky="ew")
        ctk.CTkLabel(s3, text="Loss Points:", font=ctk.CTkFont(size=11), text_color=theme.TEXT_SECONDARY).pack(anchor="w")
        self.loss_pts_entry = ctk.CTkEntry(s3, fg_color=theme.BG_INPUT, border_color=theme.BORDER_COLOR)
        self.loss_pts_entry.pack(fill="x", pady=(2, 0))

        s4 = ctk.CTkFrame(sc_grid, fg_color="transparent")
        s4.grid(row=0, column=3, padx=4, sticky="ew")
        ctk.CTkLabel(s4, text="Match Duration (Mins):", font=ctk.CTkFont(size=11), text_color=theme.TEXT_SECONDARY).pack(anchor="w")
        self.duration_entry = ctk.CTkEntry(s4, fg_color=theme.BG_INPUT, border_color=theme.BORDER_COLOR)
        self.duration_entry.pack(fill="x", pady=(2, 0))

        # Tie-breaker & Venue Row
        tb_grid = ctk.CTkFrame(rules_card, fg_color="transparent")
        tb_grid.pack(fill="x", padx=16, pady=(8, 14))
        tb_grid.columnconfigure(0, weight=2)
        tb_grid.columnconfigure(1, weight=1)

        t1 = ctk.CTkFrame(tb_grid, fg_color="transparent")
        t1.grid(row=0, column=0, padx=4, sticky="ew")
        ctk.CTkLabel(t1, text="Tie-Breakers Priority Order (comma-separated):", font=ctk.CTkFont(size=11), text_color=theme.TEXT_SECONDARY).pack(anchor="w")
        self.tie_entry = ctk.CTkEntry(t1, fg_color=theme.BG_INPUT, border_color=theme.BORDER_COLOR)
        self.tie_entry.pack(fill="x", pady=(2, 0))

        t2 = ctk.CTkFrame(tb_grid, fg_color="transparent")
        t2.grid(row=0, column=1, padx=4, sticky="ew")
        ctk.CTkLabel(t2, text="Default Venue Name:", font=ctk.CTkFont(size=11), text_color=theme.TEXT_SECONDARY).pack(anchor="w")
        self.venue_entry = ctk.CTkEntry(t2, fg_color=theme.BG_INPUT, border_color=theme.BORDER_COLOR)
        self.venue_entry.pack(fill="x", pady=(2, 0))

        # Save Button
        save_bar = ctk.CTkFrame(rules_card, fg_color="transparent")
        save_bar.pack(fill="x", padx=16, pady=(0, 16))
        ctk.CTkButton(
            save_bar,
            text="Save Configuration",
            fg_color=theme.ACCENT_GREEN,
            hover_color=theme.ACCENT_GREEN_HOVER,
            text_color=theme.TEXT_DARK,
            font=ctk.CTkFont(weight="bold"),
            command=self.save_settings
        ).pack(side="right")

        # 2. Cloud Synchronization Card (Render API & Vercel)
        cloud_card = ctk.CTkFrame(self.container, fg_color=theme.BG_CARD, corner_radius=10, border_color=theme.BORDER_COLOR, border_width=1)
        cloud_card.pack(fill="x", pady=(0, 16))

        c_hdr = ctk.CTkFrame(cloud_card, fg_color="transparent")
        c_hdr.pack(fill="x", padx=16, pady=(14, 10))
        ctk.CTkLabel(c_hdr, text="☁️ Cloud Synchronization & Public Web Deployment", font=ctk.CTkFont(size=14, weight="bold"), text_color=theme.TEXT_PRIMARY).pack(side="left")

        ctk.CTkLabel(
            cloud_card,
            text="Link your local offline tournament system with your Render cloud backend.\nPushing your local database immediately updates live fixtures, standings, and results on your Vercel public website.",
            font=ctk.CTkFont(size=11),
            text_color=theme.TEXT_MUTED,
            justify="left"
        ).pack(anchor="w", padx=16, pady=(0, 10))

        # URL and Password inputs
        c_grid = ctk.CTkFrame(cloud_card, fg_color="transparent")
        c_grid.pack(fill="x", padx=16, pady=(0, 10))
        c_grid.columnconfigure(0, weight=2)
        c_grid.columnconfigure(1, weight=1)

        cu1 = ctk.CTkFrame(c_grid, fg_color="transparent")
        cu1.grid(row=0, column=0, padx=4, sticky="ew")
        ctk.CTkLabel(cu1, text="Render Backend API URL:", font=ctk.CTkFont(size=11), text_color=theme.TEXT_SECONDARY).pack(anchor="w")
        self.cloud_url_entry = ctk.CTkEntry(cu1, fg_color=theme.BG_INPUT, border_color=theme.BORDER_COLOR)
        self.cloud_url_entry.pack(fill="x", pady=(2, 0))

        cu2 = ctk.CTkFrame(c_grid, fg_color="transparent")
        cu2.grid(row=0, column=1, padx=4, sticky="ew")
        ctk.CTkLabel(cu2, text="Admin Sync Password:", font=ctk.CTkFont(size=11), text_color=theme.TEXT_SECONDARY).pack(anchor="w")
        self.cloud_pwd_entry = ctk.CTkEntry(cu2, show="•", fg_color=theme.BG_INPUT, border_color=theme.BORDER_COLOR)
        self.cloud_pwd_entry.pack(fill="x", pady=(2, 0))

        # Cloud Status Row & Action Buttons
        c_act = ctk.CTkFrame(cloud_card, fg_color="transparent")
        c_act.pack(fill="x", padx=16, pady=(4, 14))

        self.cloud_status_lbl = ctk.CTkLabel(
            c_act,
            text="Status: Ready to sync",
            font=ctk.CTkFont(size=11),
            text_color=theme.TEXT_SECONDARY
        )
        self.cloud_status_lbl.pack(side="left")

        # Action Buttons
        ctk.CTkButton(
            c_act,
            text="📥 Pull from Cloud",
            fg_color=theme.BG_INPUT,
            hover_color=theme.BG_CARD_HOVER,
            text_color=theme.TEXT_SECONDARY,
            border_color=theme.BORDER_COLOR,
            border_width=1,
            font=ctk.CTkFont(size=11),
            command=self.handle_cloud_pull
        ).pack(side="right", padx=(6, 0))

        ctk.CTkButton(
            c_act,
            text="🚀 Push to Render Now",
            fg_color="#0284c7",
            hover_color="#0369a1",
            text_color="#FFFFFF",
            font=ctk.CTkFont(size=11, weight="bold"),
            command=self.handle_cloud_push
        ).pack(side="right", padx=(6, 0))

        ctk.CTkButton(
            c_act,
            text="Save Cloud Config",
            fg_color=theme.BG_CARD,
            hover_color=theme.BG_CARD_HOVER,
            border_color=theme.BORDER_COLOR,
            border_width=1,
            text_color=theme.TEXT_PRIMARY,
            font=ctk.CTkFont(size=11),
            command=self.save_cloud_config_values
        ).pack(side="right")

        # 3. Database Backup & Restore Card
        backup_card = ctk.CTkFrame(self.container, fg_color=theme.BG_CARD, corner_radius=10, border_color=theme.BORDER_COLOR, border_width=1)
        backup_card.pack(fill="x", pady=(0, 16))

        b_hdr = ctk.CTkFrame(backup_card, fg_color="transparent")
        b_hdr.pack(fill="x", padx=16, pady=(14, 10))

        b_title_box = ctk.CTkFrame(b_hdr, fg_color="transparent")
        b_title_box.pack(side="left")
        ctk.CTkLabel(b_title_box, text="🛡️ Automated Zero-Loss Backup & Safety Center", font=ctk.CTkFont(size=14, weight="bold"), text_color=theme.TEXT_PRIMARY).pack(anchor="w")

        # Top Action Buttons
        b_actions = ctk.CTkFrame(b_hdr, fg_color="transparent")
        b_actions.pack(side="right")

        ctk.CTkButton(
            b_actions,
            text="📂 Open Backups Folder",
            fg_color=theme.BG_INPUT,
            hover_color=theme.BG_CARD_HOVER,
            text_color=theme.TEXT_PRIMARY,
            border_color=theme.BORDER_COLOR,
            border_width=1,
            font=ctk.CTkFont(size=11),
            command=self.open_backups_folder
        ).pack(side="right", padx=(6, 0))

        ctk.CTkButton(
            b_actions,
            text="⚡ Restore Latest Snapshot",
            fg_color="#0d9488",
            hover_color="#0f766e",
            text_color="#FFFFFF",
            font=ctk.CTkFont(size=11, weight="bold"),
            command=self.handle_restore_latest
        ).pack(side="right", padx=(6, 0))

        ctk.CTkButton(
            b_actions,
            text="💾 Backup Now",
            fg_color=theme.COLOR_INFO,
            hover_color=theme.COLOR_INFO_MUTED,
            text_color="#FFFFFF",
            font=ctk.CTkFont(size=11, weight="bold"),
            command=self.create_backup_now
        ).pack(side="right")

        # Live Auto-Backup Status Banner
        self.backup_status_banner = ctk.CTkFrame(backup_card, fg_color=theme.BG_INPUT, corner_radius=8)
        self.backup_status_banner.pack(fill="x", padx=16, pady=(0, 10))

        stat_left = ctk.CTkFrame(self.backup_status_banner, fg_color="transparent")
        stat_left.pack(side="left", padx=12, pady=10)

        badge_row = ctk.CTkFrame(stat_left, fg_color="transparent")
        badge_row.pack(anchor="w")
        ctk.CTkLabel(badge_row, text="● CONTINUOUS PROTECTION ACTIVE", font=ctk.CTkFont(size=11, weight="bold"), text_color=theme.ACCENT_GREEN).pack(side="left")
        ctk.CTkLabel(badge_row, text="— Every mutation automatically saved", font=ctk.CTkFont(size=11), text_color=theme.TEXT_MUTED).pack(side="left", padx=(6, 0))

        self.backup_meta_lbl = ctk.CTkLabel(
            stat_left,
            text="Dual-tier backup: Atomic SQLite clone (.db) + Portable JSON snapshot (.json)",
            font=ctk.CTkFont(size=10),
            text_color=theme.TEXT_SECONDARY
        )
        self.backup_meta_lbl.pack(anchor="w", pady=(2, 0))

        # Backups List Container
        self.backups_container = ctk.CTkFrame(backup_card, fg_color="transparent")
        self.backups_container.pack(fill="x", padx=16, pady=(0, 14))

        # 3. Sample Data & Maintenance Card
        maint_card = ctk.CTkFrame(self.container, fg_color=theme.BG_CARD, corner_radius=10, border_color=theme.BORDER_COLOR, border_width=1)
        maint_card.pack(fill="x", pady=(0, 16))

        m_hdr = ctk.CTkFrame(maint_card, fg_color="transparent")
        m_hdr.pack(fill="x", padx=16, pady=(14, 10))
        ctk.CTkLabel(m_hdr, text="Tournament Data Management", font=ctk.CTkFont(size=14, weight="bold"), text_color=theme.TEXT_PRIMARY).pack(side="left")

        m_inner = ctk.CTkFrame(maint_card, fg_color="transparent")
        m_inner.pack(fill="x", padx=16, pady=(0, 14))

        # Sample data button
        s_box = ctk.CTkFrame(m_inner, fg_color=theme.BG_INPUT, corner_radius=6)
        s_box.pack(fill="x", pady=4)
        ctk.CTkLabel(s_box, text="Sample Tournament Generator", font=ctk.CTkFont(size=12, weight="bold"), text_color=theme.TEXT_PRIMARY).pack(anchor="w", padx=12, pady=(8, 2))
        ctk.CTkLabel(s_box, text="Populate a complete realistic 8-team Minaram Cup tournament with registrations, 2 groups, fixtures, live results, and standings for testing or demonstration.", font=ctk.CTkFont(size=10), text_color=theme.TEXT_MUTED, wraplength=480, justify="left").pack(anchor="w", padx=12, pady=(0, 8))

        ctk.CTkButton(
            s_box,
            text="Generate Sample Tournament",
            fg_color=theme.BG_CARD,
            border_color=theme.ACCENT_GREEN,
            border_width=1,
            hover_color=theme.BG_CARD_HOVER,
            text_color=theme.ACCENT_GREEN_TEXT,
            command=self.handle_generate_sample
        ).pack(anchor="w", padx=12, pady=(0, 10))

        # Reset button
        r_box = ctk.CTkFrame(m_inner, fg_color=theme.BG_INPUT, corner_radius=6)
        r_box.pack(fill="x", pady=4)
        ctk.CTkLabel(r_box, text="Reset All Tournament Data", font=ctk.CTkFont(size=12, weight="bold"), text_color=theme.COLOR_DANGER).pack(anchor="w", padx=12, pady=(8, 2))
        ctk.CTkLabel(r_box, text="Permanently wipe all registrations, teams, fixtures, and scores. Leaves the database in a fresh empty state ready for a new tournament.", font=ctk.CTkFont(size=10), text_color=theme.TEXT_MUTED, wraplength=480, justify="left").pack(anchor="w", padx=12, pady=(0, 8))

        ctk.CTkButton(
            r_box,
            text="⚠️ Wipe & Reset Database",
            fg_color=theme.COLOR_DANGER_MUTED,
            hover_color=theme.COLOR_DANGER,
            text_color="#FFFFFF",
            font=ctk.CTkFont(size=11, weight="bold"),
            command=self.handle_reset_tournament
        ).pack(anchor="w", padx=12, pady=(0, 10))

        self.load_settings_values()
        self.load_backups_list()

    def load_settings_values(self):
        s = self.tourn_mgr.get_settings()
        self.name_entry.delete(0, "end")
        self.name_entry.insert(0, s.tournament_name)

        self.edition_entry.delete(0, "end")
        self.edition_entry.insert(0, s.edition)

        self.sport_entry.delete(0, "end")
        self.sport_entry.insert(0, s.sport)

        self.win_pts_entry.delete(0, "end")
        self.win_pts_entry.insert(0, str(s.win_points))

        self.draw_pts_entry.delete(0, "end")
        self.draw_pts_entry.insert(0, str(s.draw_points))

        self.loss_pts_entry.delete(0, "end")
        self.loss_pts_entry.insert(0, str(s.loss_points))

        self.duration_entry.delete(0, "end")
        self.duration_entry.insert(0, str(s.match_duration_minutes))

        self.tie_entry.delete(0, "end")
        self.tie_entry.insert(0, s.tie_breakers)

        self.venue_entry.delete(0, "end")
        self.venue_entry.insert(0, s.default_venue)

        # Cloud settings
        cfg = get_cloud_config()
        self.cloud_url_entry.delete(0, "end")
        self.cloud_url_entry.insert(0, cfg.get("backend_url", DEFAULT_BACKEND_URL))
        self.cloud_pwd_entry.delete(0, "end")
        self.cloud_pwd_entry.insert(0, cfg.get("admin_password", "minaram2026"))
        last_t = cfg.get("last_sync_time") or "Never"
        last_s = cfg.get("last_sync_status") or "Ready"
        self.cloud_status_lbl.configure(text=f"Status: {last_s} • Last Synced: {last_t}")

    def save_cloud_config_values(self):
        url = self.cloud_url_entry.get().strip()
        pwd = self.cloud_pwd_entry.get().strip()
        if not url:
            messagebox.showwarning("Missing URL", "Please enter a valid Render backend URL.")
            return
        if save_cloud_config(url, admin_password=pwd):
            messagebox.showinfo("Saved", "Cloud configuration saved successfully!")
            self.load_settings_values()
        else:
            messagebox.showerror("Error", "Could not save cloud configuration.")

    def handle_cloud_push(self):
        CloudSyncModal(self, on_sync_completed=self.refresh)

    def handle_cloud_pull(self):
        CloudSyncModal(self, on_sync_completed=self.refresh)

    def save_settings(self):
        try:
            s = TournamentSettings(
                tournament_name=self.name_entry.get().strip() or "Minaram Cup",
                edition=self.edition_entry.get().strip() or "2026 Edition",
                sport=self.sport_entry.get().strip() or "Football",
                win_points=int(self.win_pts_entry.get().strip() or "3"),
                draw_points=int(self.draw_pts_entry.get().strip() or "1"),
                loss_points=int(self.loss_pts_entry.get().strip() or "0"),
                match_duration_minutes=int(self.duration_entry.get().strip() or "90"),
                tie_breakers=self.tie_entry.get().strip() or "points,goal_difference,goals_for,head_to_head,won",
                default_venue=self.venue_entry.get().strip() or "Minaram Stadium"
            )
            self.tourn_mgr.update_settings(s)
            messagebox.showinfo("Saved", "Tournament settings saved successfully!")
            if self.on_settings_changed:
                self.on_settings_changed()
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def open_backups_folder(self):
        try:
            folder = self.backup_service.backup_dir
            if platform.system() == "Windows":
                os.startfile(str(folder))
            else:
                subprocess.run(["xdg-open", str(folder)])
        except Exception as e:
            messagebox.showerror("Error", f"Could not open backups folder: {e}")

    def handle_restore_latest(self):
        latest_db = self.backup_service.backup_dir / "latest" / "minaram_cup_latest.db"
        if not latest_db.exists():
            messagebox.showwarning("No Snapshot", "No latest backup snapshot was found.")
            return

        ConfirmDialog(
            self,
            title="Restore Latest Snapshot",
            message=f"Are you sure you want to restore to the latest snapshot ({latest_db.name})?\nA safety backup will be created first.",
            confirm_text="Restore Latest",
            is_danger=True,
            on_confirm=self._execute_restore_latest
        )

    def _execute_restore_latest(self):
        ok, msg = self.backup_service.restore_from_latest()
        if ok:
            messagebox.showinfo("Restored", "Latest backup restored successfully! Reloading views.")
            self.refresh()
            if self.on_settings_changed:
                self.on_settings_changed()
        else:
            messagebox.showerror("Restore Failed", msg)

    def create_backup_now(self):
        try:
            b_path = self.backup_service.create_backup(label="manual")
            messagebox.showinfo("Backup Created", f"Live SQLite database and JSON state snapshot saved to:\n{b_path.name}")
            self.load_backups_list()
        except Exception as e:
            messagebox.showerror("Backup Failed", str(e))

    def load_backups_list(self):
        for child in self.backups_container.winfo_children():
            child.destroy()

        stats = self.backup_service.get_backup_stats()
        self.backup_meta_lbl.configure(
            text=f"Total Snapshots: {stats['total_backups']} • Latest: {stats['latest_file']} ({stats['latest_size_kb']} KB) • Last Backup: {stats['latest_time']}"
        )

        backups = self.backup_service.list_backups()
        if not backups:
            ctk.CTkLabel(self.backups_container, text="No previous database backups found.", font=ctk.CTkFont(size=11), text_color=theme.TEXT_MUTED).pack(anchor="w")
            return

        for b in backups[:7]:
            is_latest = b.get("is_latest", False)
            row_bg = "#0f231c" if is_latest else theme.BG_INPUT
            border_col = theme.ACCENT_GREEN if is_latest else theme.BORDER_COLOR

            row = ctk.CTkFrame(self.backups_container, fg_color=row_bg, corner_radius=6, border_color=border_col, border_width=1 if is_latest else 0)
            row.pack(fill="x", pady=2)

            left = ctk.CTkFrame(row, fg_color="transparent")
            left.pack(side="left", padx=10, pady=6)

            title_row = ctk.CTkFrame(left, fg_color="transparent")
            title_row.pack(anchor="w")

            if is_latest:
                badge = ctk.CTkLabel(title_row, text="LATEST ACTIVE", font=ctk.CTkFont(size=9, weight="bold"), text_color=theme.ACCENT_GREEN, fg_color=theme.BG_CARD, corner_radius=4)
                badge.pack(side="left", padx=(0, 6))

            action_text = b.get("action", "Auto Change")
            ctk.CTkLabel(title_row, text=f"[{action_text}]", font=ctk.CTkFont(size=10, weight="bold"), text_color="#38bdf8").pack(side="left", padx=(0, 6))
            ctk.CTkLabel(title_row, text=b["filename"], font=ctk.CTkFont(size=11, weight="bold"), text_color=theme.TEXT_PRIMARY).pack(side="left")

            json_info = " • +JSON State Snapshot" if b.get("has_json") else ""
            ctk.CTkLabel(left, text=f"Saved: {b['created_at']} • Size: {b['size_kb']} KB{json_info}", font=ctk.CTkFont(size=10), text_color=theme.TEXT_MUTED).pack(anchor="w")

            btn_box = ctk.CTkFrame(row, fg_color="transparent")
            btn_box.pack(side="right", padx=10, pady=6)

            ctk.CTkButton(
                btn_box,
                text="Restore",
                width=64,
                height=24,
                fg_color=theme.ACCENT_GREEN if is_latest else theme.BG_CARD,
                hover_color=theme.ACCENT_GREEN_HOVER if is_latest else theme.BG_CARD_HOVER,
                text_color=theme.TEXT_DARK if is_latest else theme.TEXT_PRIMARY,
                border_color=theme.BORDER_COLOR,
                border_width=1,
                font=ctk.CTkFont(size=10, weight="bold" if is_latest else "normal"),
                command=lambda b_path=b["path"]: self.handle_restore_backup(b_path)
            ).pack(side="right")

    def handle_restore_backup(self, backup_path: str):
        ConfirmDialog(
            self,
            title="Restore Database Backup",
            message=f"Are you sure you want to restore from '{Path(backup_path).name}'?\nA safety backup of your current database will be saved before restoring.",
            confirm_text="Restore Database",
            is_danger=True,
            on_confirm=lambda: self._execute_restore(backup_path)
        )

    def _execute_restore(self, backup_path: str):
        ok, msg = self.backup_service.restore_backup(Path(backup_path))
        if ok:
            messagebox.showinfo("Restored", "Database restored successfully! Refreshing view.")
            self.refresh()
            if self.on_settings_changed:
                self.on_settings_changed()
        else:
            messagebox.showerror("Restore Failed", msg)

    def handle_generate_sample(self):
        ConfirmDialog(
            self,
            title="Generate Sample Tournament",
            message="This will populate the database with a complete 8-team Minaram Cup demo tournament.\nExisting fixtures and teams will be replaced.\n\nProceed?",
            confirm_text="Generate Sample",
            on_confirm=lambda: self._execute_sample_gen()
        )

    def _execute_sample_gen(self):
        try:
            self.backup_service.generate_sample_tournament()
            messagebox.showinfo("Success", "Sample Minaram Cup tournament generated successfully!")
            self.refresh()
            if self.on_settings_changed:
                self.on_settings_changed()
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def handle_reset_tournament(self):
        ConfirmDialog(
            self,
            title="Reset All Data",
            message="WARNING: This will permanently delete ALL registrations, teams, fixtures, and results from the database.\n\nAre you sure you want to proceed?",
            confirm_text="Wipe All Data",
            is_danger=True,
            on_confirm=lambda: self._execute_reset()
        )

    def _execute_reset(self):
        try:
            self.backup_service.reset_tournament_data()
            messagebox.showinfo("Reset Complete", "Tournament database has been cleared.")
            self.refresh()
            if self.on_settings_changed:
                self.on_settings_changed()
        except Exception as e:
            messagebox.showerror("Error", str(e))

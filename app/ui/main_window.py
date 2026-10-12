"""
Main application window for Minaram Cup Tournament Management System.
Features left sidebar navigation, top bar with global search, database status,
and seamless view switching in a unified desktop workspace.
"""

import customtkinter as ctk
from tkinter import messagebox
from typing import Dict, Any
import gc
from pathlib import Path
from PIL import Image

from app.ui import theme
from app.database import Database
from app.ui.dashboard import DashboardView
from app.ui.registrations import RegistrationsView
from app.ui.teams import TeamsView
from app.ui.groups import GroupsView
from app.ui.fixtures import FixturesView
from app.ui.results import ResultsView
from app.ui.standings import StandingsView
from app.ui.knockout import KnockoutView
from app.ui.reports import ReportsView
from app.ui.settings import SettingsView

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("green")


class LazyViewsDict(dict):
    """
    Dictionary that lazily instantiates view frames on demand.
    Saves significant RAM at boot and avoids heavy synchronous widget
    hierarchy building for tabs that haven't been visited yet.
    """
    def __init__(self, factories, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.factories = factories

    def __contains__(self, key):
        return key in self.factories or super().__contains__(key)

    def __getitem__(self, key):
        if not super().__contains__(key) and key in self.factories:
            self[key] = self.factories[key]()
        return super().__getitem__(key)

    def get(self, key, default=None):
        if key in self:
            return self[key]
        return default


class MainWindow(ctk.CTk):
    def __init__(self, db: Database):
        super().__init__()
        self.db = db

        # Configure window
        self.title("MINARAM CUP — Tournament Management System")
        self.geometry("1280x800")
        self.minsize(1040, 680)
        self.configure(fg_color=theme.BG_MAIN)

        # Set official app icon
        icon_path = Path(__file__).resolve().parent.parent.parent / "Logo" / "minaram_app_icon.ico"
        if icon_path.exists():
            try:
                self.iconbitmap(str(icon_path))
            except Exception:
                pass

        self.current_section = "Dashboard"
        self.nav_buttons = {}

        self.setup_layout()
        self.init_views()
        self.show_section("Dashboard")
        self.protocol("WM_DELETE_WINDOW", self.on_close)

    def on_close(self):
        try:
            self.db.close()
        except Exception:
            pass
        self.destroy()

    def setup_layout(self):
        # 1. Left Sidebar Navigation
        self.sidebar = ctk.CTkFrame(self, width=220, fg_color=theme.BG_SIDEBAR, corner_radius=0)
        self.sidebar.pack(side="left", fill="y")
        self.sidebar.pack_propagate(False)

        # Brand Header with Official Championship Crest
        brand_frame = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        brand_frame.pack(fill="x", padx=16, pady=(16, 12))

        logo_path = Path(__file__).resolve().parent.parent.parent / "Logo" / "minaram_crest_master.png"
        if logo_path.exists():
            try:
                pil_logo = Image.open(logo_path)
                self.sidebar_logo_img = ctk.CTkImage(light_image=pil_logo, dark_image=pil_logo, size=(46, 46))
                logo_lbl = ctk.CTkLabel(brand_frame, image=self.sidebar_logo_img, text="")
                logo_lbl.pack(anchor="w", pady=(0, 6))
            except Exception:
                pass

        title_lbl = ctk.CTkLabel(
            brand_frame,
            text="MINARAM CUP",
            font=ctk.CTkFont(size=18, weight="bold"),
            text_color=theme.ACCENT_GREEN_TEXT
        )
        title_lbl.pack(anchor="w")

        self.sub_edition_lbl = ctk.CTkLabel(
            brand_frame,
            text=f"{self.db.get_setting('edition', '2026 Edition')}",
            font=ctk.CTkFont(size=11),
            text_color=theme.TEXT_MUTED
        )
        self.sub_edition_lbl.pack(anchor="w")

        # Sidebar Separator
        ctk.CTkFrame(self.sidebar, height=1, fg_color=theme.BORDER_COLOR).pack(fill="x", padx=14, pady=(0, 10))

        # Navigation Links
        nav_items = [
            ("Dashboard", "🏠  Dashboard"),
            ("Registrations", "📥  Registrations"),
            ("Teams", "🛡️  Teams"),
            ("Groups", "🗂️  Groups"),
            ("Fixtures", "📅  Fixtures"),
            ("Results", "⚽  Results"),
            ("Points Table", "🏆  Points Table"),
            ("Knockout Stage", "⚔️  Knockout Stage"),
            ("Reports & Exports", "📊  Reports & Exports"),
            ("Settings", "⚙️  Settings"),
        ]

        for sec_id, label_text in nav_items:
            btn = ctk.CTkButton(
                self.sidebar,
                text=label_text,
                font=ctk.CTkFont(size=12, weight="normal"),
                fg_color="transparent",
                hover_color=theme.BG_CARD_HOVER,
                text_color=theme.TEXT_SECONDARY,
                anchor="w",
                height=36,
                corner_radius=6,
                command=lambda s=sec_id: self.show_section(s)
            )
            btn.pack(fill="x", padx=10, pady=2)
            self.nav_buttons[sec_id] = btn

        # Sidebar Footer
        footer_frame = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        footer_frame.pack(side="bottom", fill="x", padx=14, pady=16)

        # Database connection indicator
        db_pill = ctk.CTkFrame(footer_frame, fg_color=theme.BG_INPUT, corner_radius=6)
        db_pill.pack(fill="x", pady=(0, 6))

        dot = ctk.CTkLabel(db_pill, text="●", text_color=theme.ACCENT_GREEN, font=theme.get_font(12))
        dot.pack(side="left", padx=(10, 4), pady=4)
        ctk.CTkLabel(db_pill, text="SQLite Connected", font=theme.get_font(10, "bold"), text_color=theme.TEXT_SECONDARY).pack(side="left", pady=4)

        ctk.CTkLabel(footer_frame, text="Minaram Cup v1.0 • Offline", font=theme.get_font(10), text_color=theme.TEXT_MUTED).pack(anchor="w")

        # 2. Main Right Container
        self.right_container = ctk.CTkFrame(self, fg_color="transparent")
        self.right_container.pack(side="right", fill="both", expand=True)

        # Top Bar
        self.topbar = ctk.CTkFrame(self.right_container, height=56, fg_color=theme.BG_TOPBAR, corner_radius=0)
        self.topbar.pack(fill="x")
        self.topbar.pack_propagate(False)

        # Left Section of Top Bar: Section Title
        top_left = ctk.CTkFrame(self.topbar, fg_color="transparent")
        top_left.pack(side="left", padx=20, pady=10)

        self.section_title_lbl = ctk.CTkLabel(
            top_left,
            text="DASHBOARD",
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color=theme.TEXT_PRIMARY
        )
        self.section_title_lbl.pack(side="left")

        # Right Section of Top Bar: Search, Quick Register, Tournament Badge
        top_right = ctk.CTkFrame(self.topbar, fg_color="transparent")
        top_right.pack(side="right", padx=16, pady=10)

        self.global_search_entry = ctk.CTkEntry(
            top_right,
            placeholder_text="Global search...",
            width=180,
            height=30,
            fg_color=theme.BG_INPUT,
            border_color=theme.BORDER_COLOR
        )
        self.global_search_entry.pack(side="left", padx=(0, 10))
        self.global_search_entry.bind("<Return>", self.handle_global_search)

        ctk.CTkButton(
            top_right,
            text="+ Register",
            fg_color=theme.ACCENT_GREEN,
            hover_color=theme.ACCENT_GREEN_HOVER,
            text_color=theme.TEXT_DARK,
            font=ctk.CTkFont(size=12, weight="bold"),
            height=30,
            command=lambda: self.show_section("Registrations")
        ).pack(side="left", padx=(0, 8))

        self.tourn_badge = ctk.CTkLabel(
            top_right,
            text=f"⚽ {self.db.get_setting('tournament_name', 'Minaram Cup')}",
            fg_color=theme.BG_CARD,
            text_color=theme.ACCENT_GREEN_TEXT,
            corner_radius=6,
            font=ctk.CTkFont(size=11, weight="bold"),
            padx=10,
            pady=4
        )
        self.tourn_badge.pack(side="left")

        # 3. Workspace Frame for Views
        self.workspace = ctk.CTkFrame(self.right_container, fg_color=theme.BG_MAIN, corner_radius=0)
        self.workspace.pack(fill="both", expand=True)

    def init_views(self):
        """Register views with lazy factory constructors."""
        factories = {
            "Dashboard": lambda: DashboardView(self.workspace, self.db, self.show_section, on_cloud_sync=self.open_cloud_sync),
            "Registrations": lambda: RegistrationsView(self.workspace, self.db),
            "Teams": lambda: TeamsView(self.workspace, self.db),
            "Groups": lambda: GroupsView(self.workspace, self.db),
            "Fixtures": lambda: FixturesView(self.workspace, self.db, self.show_section),
            "Results": lambda: ResultsView(self.workspace, self.db),
            "Points Table": lambda: StandingsView(self.workspace, self.db),
            "Knockout Stage": lambda: KnockoutView(self.workspace, self.db, self.show_section),
            "Reports & Exports": lambda: ReportsView(self.workspace, self.db),
            "Settings": lambda: SettingsView(self.workspace, self.db, self.on_settings_updated),
        }
        self.views = LazyViewsDict(factories)

    def show_section(self, section_name: str):
        if section_name not in self.views:
            return

        self.current_section = section_name
        self.section_title_lbl.configure(text=section_name.upper())

        # Update sidebar active states
        for sec_id, btn in self.nav_buttons.items():
            if sec_id == section_name:
                btn.configure(
                    fg_color=theme.BG_CARD,
                    text_color=theme.ACCENT_GREEN_TEXT,
                    font=theme.get_font(12, "bold")
                )
            else:
                btn.configure(
                    fg_color="transparent",
                    text_color=theme.TEXT_SECONDARY,
                    font=theme.get_font(12, "normal")
                )

        # Check if view was already instantiated before this navigation
        is_already_instantiated = super(LazyViewsDict, self.views).__contains__(section_name)
        target_view = self.views[section_name]

        # Hide all instantiated views and show target view
        for name, view in list(self.views.items()):
            if name == section_name:
                view.pack(fill="both", expand=True)
                if is_already_instantiated:
                    view.refresh()
            else:
                view.pack_forget()

        # Reclaim orphaned widgets and objects
        gc.collect()

    def handle_global_search(self, event=None):
        query = self.global_search_entry.get().strip()
        if not query:
            return
        # If user searches, switch to Registrations or Teams and populate search
        self.show_section("Teams")
        self.views["Teams"].search_var.set(query)
        self.views["Teams"].load_teams_table()

    def on_settings_updated(self):
        t_name = self.db.get_setting("tournament_name", "Minaram Cup")
        t_edition = self.db.get_setting("edition", "2026 Edition")
        self.sub_edition_lbl.configure(text=t_edition)
        self.tourn_badge.configure(text=f"⚽ {t_name}")
        # Refresh current view
        if self.current_section in self.views:
            self.views[self.current_section].refresh()

    def open_cloud_sync(self):
        """Open the interactive cloud push & pull dialog."""
        from app.ui.cloud_sync_dialog import CloudSyncModal
        CloudSyncModal(self, on_sync_completed=self.on_cloud_synced)

    def on_cloud_synced(self):
        """Callback when cloud sync successfully completes."""
        if self.current_section in self.views:
            self.views[self.current_section].refresh()


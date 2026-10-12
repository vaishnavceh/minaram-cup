import logging
import customtkinter as ctk
from tkinter import filedialog, messagebox
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta

from app.ui import theme
from app.ui.modal import BaseModal, ConfirmDialog
from app.database import Database
from app.fixture_generator import FixtureGenerator
from app.knockout_manager import KnockoutManager
from app.export_service import ExportService

logger = logging.getLogger("minaram_cup.fixtures")


class FixturesView(ctk.CTkScrollableFrame):
    def __init__(self, parent, db: Database, navigate_callback=None):
        super().__init__(parent, fg_color="transparent")
        self.db = db
        self.navigate = navigate_callback
        self.fixture_gen = FixtureGenerator(db)
        self.knockout_mgr = KnockoutManager(db)
        self.export_service = ExportService(db)

        # Pagination & Performance Cache
        self.current_page = 1
        self.page_size = 25

        # Filters
        self.stage_filter_var = ctk.StringVar(value="All Stages")
        self.status_filter_var = ctk.StringVar(value="All Statuses")
        self.group_filter_var = ctk.StringVar(value="All Groups")

        self.build_ui()


    def refresh(self):
        self.update_group_filter_options()
        self.check_conflicts()
        self.load_fixtures_table()

    def build_ui(self):
        # Header
        hdr = ctk.CTkFrame(self, fg_color="transparent")
        hdr.pack(fill="x", padx=16, pady=(12, 12))

        title_box = ctk.CTkFrame(hdr, fg_color="transparent")
        title_box.pack(side="left")
        ctk.CTkLabel(title_box, text="Fixture Management & Scheduling", font=ctk.CTkFont(size=20, weight="bold"), text_color=theme.TEXT_PRIMARY).pack(anchor="w")
        ctk.CTkLabel(title_box, text="Schedule group stages, generate league & knockout fixtures, and resolve venue conflicts", font=ctk.CTkFont(size=11), text_color=theme.TEXT_MUTED).pack(anchor="w")

        # Action Buttons
        btn_box = ctk.CTkFrame(hdr, fg_color="transparent")
        btn_box.pack(side="right")

        ctk.CTkButton(
            btn_box,
            text="⚡ Fixture Wizard",
            fg_color=theme.ACCENT_GREEN,
            hover_color=theme.ACCENT_GREEN_HOVER,
            text_color=theme.TEXT_DARK,
            font=ctk.CTkFont(size=12, weight="bold"),
            height=32,
            command=self.open_generate_wizard
        ).pack(side="left", padx=4)

        ctk.CTkButton(
            btn_box,
            text="+ Add Fixture",
            fg_color=theme.BG_CARD,
            border_color=theme.BORDER_COLOR,
            border_width=1,
            hover_color=theme.BG_CARD_HOVER,
            text_color=theme.TEXT_PRIMARY,
            height=32,
            command=self.open_add_fixture_modal
        ).pack(side="left", padx=4)

        ctk.CTkButton(
            btn_box,
            text="📤 Export Fixtures",
            fg_color=theme.BG_CARD,
            border_color=theme.BORDER_COLOR,
            border_width=1,
            hover_color=theme.BG_CARD_HOVER,
            text_color=theme.TEXT_PRIMARY,
            height=32,
            command=self.handle_export
        ).pack(side="left", padx=4)

        # Conflict Alert Banner (dynamic)
        self.conflict_banner = ctk.CTkFrame(self, fg_color=theme.COLOR_DANGER_MUTED, corner_radius=8, border_color=theme.COLOR_DANGER, border_width=1)
        self.conflict_label = ctk.CTkLabel(self.conflict_banner, text="", font=ctk.CTkFont(size=11, weight="bold"), text_color="#FECACA")
        self.conflict_label.pack(padx=14, pady=8)

        # Filter Bar Card
        filter_card = ctk.CTkFrame(self, fg_color=theme.BG_CARD, corner_radius=10, border_color=theme.BORDER_COLOR, border_width=1)
        filter_card.pack(fill="x", padx=16, pady=(0, 14))

        f_bar = ctk.CTkFrame(filter_card, fg_color="transparent")
        f_bar.pack(fill="x", padx=14, pady=10)

        ctk.CTkLabel(f_bar, text="Stage:", font=ctk.CTkFont(size=11), text_color=theme.TEXT_MUTED).pack(side="left", padx=(0, 4))
        self.stage_menu = ctk.CTkOptionMenu(
            f_bar,
            variable=self.stage_filter_var,
            values=["All Stages", "Group Stage", "League", "Quarter-Final", "Semi-Final", "Final"],
            width=130,
            height=28,
            fg_color=theme.BG_INPUT,
            command=lambda v: self.load_fixtures_table()
        )
        self.stage_menu.pack(side="left", padx=(0, 12))

        ctk.CTkLabel(f_bar, text="Group:", font=ctk.CTkFont(size=11), text_color=theme.TEXT_MUTED).pack(side="left", padx=(0, 4))
        self.group_menu = ctk.CTkOptionMenu(
            f_bar,
            variable=self.group_filter_var,
            values=["All Groups"],
            width=120,
            height=28,
            fg_color=theme.BG_INPUT,
            command=lambda v: self.load_fixtures_table()
        )
        self.group_menu.pack(side="left", padx=(0, 12))

        ctk.CTkLabel(f_bar, text="Status:", font=ctk.CTkFont(size=11), text_color=theme.TEXT_MUTED).pack(side="left", padx=(0, 4))
        self.status_menu = ctk.CTkOptionMenu(
            f_bar,
            variable=self.status_filter_var,
            values=["All Statuses", "Scheduled", "Completed", "Postponed", "Cancelled", "Walkover"],
            width=120,
            height=28,
            fg_color=theme.BG_INPUT,
            command=lambda v: self.load_fixtures_table()
        )
        self.status_menu.pack(side="left", padx=(0, 12))

        ctk.CTkButton(
            f_bar,
            text="Clear Fixtures",
            width=100,
            height=28,
            fg_color="transparent",
            hover_color=theme.COLOR_DANGER_MUTED,
            text_color=theme.COLOR_DANGER,
            font=ctk.CTkFont(size=11),
            command=self.handle_clear_fixtures
        ).pack(side="right")

        # Table Card
        self.table_card = ctk.CTkFrame(self, fg_color=theme.BG_CARD, corner_radius=10, border_color=theme.BORDER_COLOR, border_width=1)
        self.table_card.pack(fill="both", expand=True, padx=16, pady=(0, 20))

        # Table Header
        self.header_frame = ctk.CTkFrame(self.table_card, fg_color=theme.BG_INPUT, height=32, corner_radius=6)
        self.header_frame.pack(fill="x", padx=14, pady=10)

        cols = [
            ("M#", 36),
            ("Stage / Group", 120),
            ("Home Team", 140),
            ("Score", 70),
            ("Away Team", 140),
            ("Date & Time", 120),
            ("Venue", 120),
            ("Status", 80),
            ("Actions", 140)
        ]
        for name, w in cols:
            ctk.CTkLabel(
                self.header_frame,
                text=name,
                font=ctk.CTkFont(size=11, weight="bold"),
                text_color=theme.TEXT_SECONDARY,
                width=w,
                anchor="center" if w < 80 else "w"
            ).pack(side="left", padx=3)

        self.rows_container = ctk.CTkFrame(self.table_card, fg_color="transparent")
        self.rows_container.pack(fill="both", expand=True, padx=14, pady=(0, 4))

        # Pagination Toolbar (Cuts Widget Count & RAM Usage)
        self.pagination_frame = ctk.CTkFrame(self.table_card, fg_color="transparent")
        self.pagination_frame.pack(fill="x", padx=14, pady=(2, 10))

        self.prev_btn = ctk.CTkButton(
            self.pagination_frame,
            text="◀ Previous",
            width=80,
            height=26,
            fg_color=theme.BG_INPUT,
            hover_color=theme.BG_CARD_HOVER,
            text_color=theme.TEXT_SECONDARY,
            font=theme.get_font(11),
            command=self.prev_page
        )
        self.prev_btn.pack(side="left")

        self.page_info_lbl = ctk.CTkLabel(
            self.pagination_frame,
            text="",
            font=theme.get_font(11),
            text_color=theme.TEXT_MUTED
        )
        self.page_info_lbl.pack(side="left", padx=12)

        self.next_btn = ctk.CTkButton(
            self.pagination_frame,
            text="Next ▶",
            width=80,
            height=26,
            fg_color=theme.BG_INPUT,
            hover_color=theme.BG_CARD_HOVER,
            text_color=theme.TEXT_SECONDARY,
            font=theme.get_font(11),
            command=self.next_page
        )
        self.next_btn.pack(side="left")

        self.update_group_filter_options()
        self.check_conflicts()
        self.load_fixtures_table()

    def prev_page(self):
        if self.current_page > 1:
            self.current_page -= 1
            self.load_fixtures_table()

    def next_page(self):
        self.current_page += 1
        self.load_fixtures_table()

    def update_group_filter_options(self):
        groups = self.db.execute_query("SELECT name FROM groups ORDER BY display_order ASC;")
        self.group_menu.configure(values=["All Groups"] + [g["name"] for g in groups])

    def check_conflicts(self):
        try:
            conflicts = self.fixture_gen.detect_conflicts()
            if conflicts:
                c = conflicts[0]
                if not self.conflict_banner.winfo_ismapped():
                    self.conflict_banner.pack(fill="x", padx=16, pady=(0, 14), before=self.table_card)
                self.conflict_label.configure(
                    text=f"⚠️ Scheduling Conflict Detected: {c['type']} — {c['details']}"
                )
            else:
                if self.conflict_banner.winfo_ismapped():
                    self.conflict_banner.pack_forget()
        except Exception:
            pass

    def load_fixtures_table(self):
        import gc
        for child in self.rows_container.winfo_children():
            child.destroy()

        stage = self.stage_filter_var.get()
        stage_filter = None if stage == "All Stages" else stage

        status = self.status_filter_var.get()
        status_filter = None if status == "All Statuses" else status

        g_sel = self.group_filter_var.get()
        group_id = None
        if g_sel != "All Groups":
            g_row = self.db.execute_one("SELECT id FROM groups WHERE name = ?;", (g_sel,))
            if g_row:
                group_id = g_row["id"]

        matches = self.fixture_gen.get_matches(stage=stage_filter, group_id=group_id, status=status_filter)

        if not matches:
            self.pagination_frame.pack_forget()
            empty_box = ctk.CTkFrame(self.rows_container, fg_color="transparent")
            empty_box.pack(fill="x", pady=30)
            ctk.CTkLabel(empty_box, text="No fixtures found. Click '⚡ Fixture Wizard' to schedule matches.", font=theme.get_font(13), text_color=theme.TEXT_MUTED).pack()
            return

        total_matches = len(matches)
        total_pages = max(1, (total_matches + self.page_size - 1) // self.page_size)
        if self.current_page > total_pages:
            self.current_page = total_pages
        if self.current_page < 1:
            self.current_page = 1

        start_idx = (self.current_page - 1) * self.page_size
        end_idx = min(start_idx + self.page_size, total_matches)
        page_matches = matches[start_idx:end_idx]

        # Update pagination frame
        self.pagination_frame.pack(fill="x", padx=14, pady=(2, 10))
        self.page_info_lbl.configure(
            text=f"Showing {start_idx + 1}-{end_idx} of {total_matches} matches (Page {self.current_page} of {total_pages})"
        )
        self.prev_btn.configure(state="normal" if self.current_page > 1 else "disabled")
        self.next_btn.configure(state="normal" if self.current_page < total_pages else "disabled")

        for idx, m in enumerate(page_matches):
            bg_col = theme.BG_INPUT if idx % 2 == 0 else theme.BG_ROW_ALT
            row = ctk.CTkFrame(self.rows_container, fg_color=bg_col, height=36, corner_radius=4)
            row.pack(fill="x", pady=2)

            ctk.CTkLabel(row, text=str(m.match_number), width=36, font=theme.get_font(11, "bold"), text_color=theme.TEXT_MUTED).pack(side="left", padx=3)

            stage_desc = f"{m.stage} ({m.group_name})" if m.group_name else m.stage
            ctk.CTkLabel(row, text=stage_desc, width=120, font=theme.get_font(11), text_color=theme.TEXT_SECONDARY, anchor="w").pack(side="left", padx=3)

            # Home team
            ctk.CTkLabel(row, text=m.home_team_name, width=140, font=theme.get_font(11, "bold"), text_color=theme.TEXT_PRIMARY, anchor="w").pack(side="left", padx=3)

            # Score
            sc_color = theme.ACCENT_GREEN_TEXT if m.is_completed else theme.TEXT_MUTED
            ctk.CTkLabel(row, text=m.score_display, width=70, font=theme.get_font(12, "bold"), text_color=sc_color).pack(side="left", padx=3)

            # Away team
            ctk.CTkLabel(row, text=m.away_team_name, width=140, font=theme.get_font(11, "bold"), text_color=theme.TEXT_PRIMARY, anchor="w").pack(side="left", padx=3)

            # Date & Time
            dt_s = f"{m.scheduled_date} {m.scheduled_time}".strip() or "-"
            ctk.CTkLabel(row, text=dt_s, width=120, font=theme.get_font(11), text_color=theme.TEXT_SECONDARY, anchor="w").pack(side="left", padx=3)

            # Venue
            ctk.CTkLabel(row, text=m.venue or "-", width=120, font=theme.get_font(11), text_color=theme.TEXT_MUTED, anchor="w").pack(side="left", padx=3)

            # Status Badge
            badge_bg, badge_fg = theme.get_status_colors(m.status)
            ctk.CTkLabel(
                row,
                text=m.status,
                fg_color=badge_bg,
                text_color=badge_fg,
                corner_radius=4,
                font=theme.get_font(10, "bold"),
                width=76,
                height=22
            ).pack(side="left", padx=3)

            # Actions
            act_box = ctk.CTkFrame(row, fg_color="transparent", width=140)
            act_box.pack(side="left", padx=3)

            ctk.CTkButton(
                act_box,
                text="Reschedule",
                width=70,
                height=22,
                fg_color=theme.BG_CARD,
                border_color=theme.BORDER_COLOR,
                border_width=1,
                hover_color=theme.BG_CARD_HOVER,
                text_color=theme.TEXT_PRIMARY,
                font=theme.get_font(10),
                command=lambda match=m: self.open_reschedule_modal(match)
            ).pack(side="left", padx=2)

            ctk.CTkButton(
                act_box,
                text="✕",
                width=24,
                height=22,
                fg_color="transparent",
                hover_color=theme.COLOR_DANGER_MUTED,
                text_color=theme.COLOR_DANGER,
                font=theme.get_font(11, "bold"),
                command=lambda match_id=m.id: self.handle_delete_match(match_id)
            ).pack(side="left", padx=2)

        gc.collect()

    # ----------------------------------------------------
    # Fixture Generation Wizard Modal
    # ----------------------------------------------------
    def open_generate_wizard(self):
        from app.ui.fixture_wizard_dialog import FixtureWizardModal
        self._wizard_modal = FixtureWizardModal(self, self.db, on_saved=self.refresh)

    # ----------------------------------------------------
    # Manual Add Fixture Modal
    # ----------------------------------------------------
    def open_add_fixture_modal(self):
        teams = self.db.execute_query("SELECT id, name FROM teams WHERE status = 'Confirmed' ORDER BY name ASC;")
        if len(teams) < 2:
            messagebox.showinfo("Not Enough Teams", "Need at least 2 confirmed teams to create a fixture.")
            return

        team_names = [t["name"] for t in teams]
        team_id_map = {t["name"]: t["id"] for t in teams}

        modal = BaseModal(self, title="Add Manual Fixture", width=460, height=440)

        ctk.CTkLabel(modal.body_frame, text="Home Team:", font=ctk.CTkFont(size=11), text_color=theme.TEXT_SECONDARY).pack(anchor="w", pady=(2, 2))
        h_menu = ctk.CTkOptionMenu(modal.body_frame, values=team_names, fg_color=theme.BG_INPUT)
        h_menu.pack(fill="x", pady=(0, 6))

        ctk.CTkLabel(modal.body_frame, text="Away Team:", font=ctk.CTkFont(size=11), text_color=theme.TEXT_SECONDARY).pack(anchor="w", pady=(2, 2))
        a_menu = ctk.CTkOptionMenu(modal.body_frame, values=team_names, fg_color=theme.BG_INPUT)
        a_menu.set(team_names[1] if len(team_names) > 1 else team_names[0])
        a_menu.pack(fill="x", pady=(0, 6))

        row2 = ctk.CTkFrame(modal.body_frame, fg_color="transparent")
        row2.pack(fill="x", pady=(0, 6))
        row2.columnconfigure(0, weight=1)
        row2.columnconfigure(1, weight=1)

        d_box = ctk.CTkFrame(row2, fg_color="transparent")
        d_box.grid(row=0, column=0, sticky="ew", padx=(0, 4))
        ctk.CTkLabel(d_box, text="Date (YYYY-MM-DD):", font=ctk.CTkFont(size=11), text_color=theme.TEXT_SECONDARY).pack(anchor="w")
        date_e = ctk.CTkEntry(d_box, fg_color=theme.BG_INPUT, border_color=theme.BORDER_COLOR)
        date_e.insert(0, datetime.now().strftime("%Y-%m-%d"))
        date_e.pack(fill="x")

        t_box = ctk.CTkFrame(row2, fg_color="transparent")
        t_box.grid(row=0, column=1, sticky="ew", padx=(4, 0))
        ctk.CTkLabel(t_box, text="Kick-off Time:", font=ctk.CTkFont(size=11), text_color=theme.TEXT_SECONDARY).pack(anchor="w")
        time_e = ctk.CTkEntry(t_box, fg_color=theme.BG_INPUT, border_color=theme.BORDER_COLOR)
        time_e.insert(0, "15:00")
        time_e.pack(fill="x")

        ctk.CTkLabel(modal.body_frame, text="Venue:", font=ctk.CTkFont(size=11), text_color=theme.TEXT_SECONDARY).pack(anchor="w", pady=(2, 2))
        venue_e = ctk.CTkEntry(modal.body_frame, fg_color=theme.BG_INPUT, border_color=theme.BORDER_COLOR)
        venue_e.insert(0, "Minaram Stadium")
        venue_e.pack(fill="x", pady=(0, 6))

        ctk.CTkLabel(modal.body_frame, text="Stage / Notes:", font=ctk.CTkFont(size=11), text_color=theme.TEXT_SECONDARY).pack(anchor="w", pady=(2, 2))
        notes_e = ctk.CTkEntry(modal.body_frame, fg_color=theme.BG_INPUT, border_color=theme.BORDER_COLOR)
        notes_e.insert(0, "League")
        notes_e.pack(fill="x", pady=(0, 14))

        def save():
            h_name = h_menu.get()
            a_name = a_menu.get()
            if h_name == a_name:
                messagebox.showerror("Error", "Home and away teams cannot be identical.")
                return

            try:
                self.fixture_gen.add_manual_match(
                    home_team_id=team_id_map[h_name],
                    away_team_id=team_id_map[a_name],
                    stage=notes_e.get().strip() or "League",
                    scheduled_date=date_e.get().strip(),
                    scheduled_time=time_e.get().strip(),
                    venue=venue_e.get().strip(),
                    notes=notes_e.get().strip()
                )
                modal.destroy()
                self.refresh()
            except Exception as e:
                messagebox.showerror("Error", str(e))

        ctk.CTkButton(modal.body_frame, text="Save Fixture", fg_color=theme.ACCENT_GREEN, hover_color=theme.ACCENT_GREEN_HOVER, text_color=theme.TEXT_DARK, font=ctk.CTkFont(weight="bold"), command=save).pack(fill="x")

    def open_reschedule_modal(self, match):
        modal = BaseModal(self, title=f"Reschedule Match #{match.match_number}", width=420, height=340)

        ctk.CTkLabel(modal.body_frame, text=f"{match.home_team_name} vs {match.away_team_name}", font=ctk.CTkFont(size=13, weight="bold"), text_color=theme.TEXT_PRIMARY).pack(pady=(0, 10))

        ctk.CTkLabel(modal.body_frame, text="Date (YYYY-MM-DD):", font=ctk.CTkFont(size=11), text_color=theme.TEXT_SECONDARY).pack(anchor="w")
        date_e = ctk.CTkEntry(modal.body_frame, fg_color=theme.BG_INPUT, border_color=theme.BORDER_COLOR)
        date_e.insert(0, match.scheduled_date)
        date_e.pack(fill="x", pady=(0, 6))

        ctk.CTkLabel(modal.body_frame, text="Time (HH:MM):", font=ctk.CTkFont(size=11), text_color=theme.TEXT_SECONDARY).pack(anchor="w")
        time_e = ctk.CTkEntry(modal.body_frame, fg_color=theme.BG_INPUT, border_color=theme.BORDER_COLOR)
        time_e.insert(0, match.scheduled_time)
        time_e.pack(fill="x", pady=(0, 6))

        ctk.CTkLabel(modal.body_frame, text="Venue:", font=ctk.CTkFont(size=11), text_color=theme.TEXT_SECONDARY).pack(anchor="w")
        venue_e = ctk.CTkEntry(modal.body_frame, fg_color=theme.BG_INPUT, border_color=theme.BORDER_COLOR)
        venue_e.insert(0, match.venue)
        venue_e.pack(fill="x", pady=(0, 6))

        ctk.CTkLabel(modal.body_frame, text="Status:", font=ctk.CTkFont(size=11), text_color=theme.TEXT_SECONDARY).pack(anchor="w")
        status_menu = ctk.CTkOptionMenu(modal.body_frame, values=["Scheduled", "Postponed", "Cancelled", "In Progress"], fg_color=theme.BG_INPUT)
        status_menu.set(match.status)
        status_menu.pack(fill="x", pady=(0, 14))

        def save():
            self.fixture_gen.update_match_schedule(
                match_id=match.id,
                scheduled_date=date_e.get().strip(),
                scheduled_time=time_e.get().strip(),
                venue=venue_e.get().strip(),
                status=status_menu.get()
            )
            modal.destroy()
            self.refresh()

        ctk.CTkButton(modal.body_frame, text="Update Match", fg_color=theme.ACCENT_GREEN, hover_color=theme.ACCENT_GREEN_HOVER, text_color=theme.TEXT_DARK, font=ctk.CTkFont(weight="bold"), command=save).pack(fill="x")

    def handle_delete_match(self, match_id: int):
        ConfirmDialog(
            self,
            title="Delete Fixture",
            message="Are you sure you want to delete this fixture?",
            confirm_text="Delete",
            is_danger=True,
            on_confirm=lambda: [self.fixture_gen.delete_match(match_id), self.refresh()]
        )

    def handle_clear_fixtures(self):
        ConfirmDialog(
            self,
            title="Clear All Fixtures",
            message="Are you sure you want to delete ALL tournament fixtures and results?\nThis cannot be undone.",
            confirm_text="Clear All",
            is_danger=True,
            on_confirm=lambda: [self.fixture_gen.save_fixtures([], clear_existing=True), self.refresh()]
        )

    def handle_export(self):
        dest = filedialog.asksaveasfilename(
            defaultextension=".xlsx",
            initialfile="minaram_fixtures.xlsx",
            filetypes=[("Excel Files", "*.xlsx"), ("CSV Files", "*.csv")]
        )
        if not dest:
            return
        try:
            self.export_service.export_fixtures(dest)
            messagebox.showinfo("Export Complete", f"Fixtures exported successfully to:\n{dest}")
        except Exception as e:
            messagebox.showerror("Export Failed", str(e))

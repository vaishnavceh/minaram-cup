"""
Fixture administration interface: fixture generation wizard,
conflict detector, rescheduling, status management, and manual match additions.
"""

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


class FixturesView(ctk.CTkScrollableFrame):
    def __init__(self, parent, db: Database, navigate_callback=None):
        super().__init__(parent, fg_color="transparent")
        self.db = db
        self.navigate = navigate_callback
        self.fixture_gen = FixtureGenerator(db)
        self.knockout_mgr = KnockoutManager(db)
        self.export_service = ExportService(db)

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
        self.rows_container.pack(fill="both", expand=True, padx=14, pady=(0, 14))

        self.update_group_filter_options()
        self.check_conflicts()
        self.load_fixtures_table()

    def update_group_filter_options(self):
        groups = self.db.execute_query("SELECT name FROM groups ORDER BY display_order ASC;")
        self.group_menu.configure(values=["All Groups"] + [g["name"] for g in groups])

    def check_conflicts(self):
        conflicts = self.fixture_gen.detect_conflicts()
        if conflicts:
            c = conflicts[0]
            self.conflict_banner.pack(fill="x", padx=16, pady=(0, 14), before=self.table_card)
            self.conflict_label.configure(
                text=f"⚠️ Scheduling Conflict Detected: {c['type']} — {c['details']}"
            )
        else:
            self.conflict_banner.pack_forget()

    def load_fixtures_table(self):
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
            empty_box = ctk.CTkFrame(self.rows_container, fg_color="transparent")
            empty_box.pack(fill="x", pady=30)
            ctk.CTkLabel(empty_box, text="No fixtures found. Click '⚡ Fixture Wizard' to schedule matches.", font=ctk.CTkFont(size=13), text_color=theme.TEXT_MUTED).pack()
            return

        for idx, m in enumerate(matches):
            bg_col = theme.BG_INPUT if idx % 2 == 0 else theme.BG_ROW_ALT
            row = ctk.CTkFrame(self.rows_container, fg_color=bg_col, height=36, corner_radius=4)
            row.pack(fill="x", pady=2)

            ctk.CTkLabel(row, text=str(m.match_number), width=36, font=ctk.CTkFont(size=11, weight="bold"), text_color=theme.TEXT_MUTED).pack(side="left", padx=3)

            stage_desc = f"{m.stage} ({m.group_name})" if m.group_name else m.stage
            ctk.CTkLabel(row, text=stage_desc, width=120, font=ctk.CTkFont(size=11), text_color=theme.TEXT_SECONDARY, anchor="w").pack(side="left", padx=3)

            # Home team
            ctk.CTkLabel(row, text=m.home_team_name, width=140, font=ctk.CTkFont(size=11, weight="bold"), text_color=theme.TEXT_PRIMARY, anchor="w").pack(side="left", padx=3)

            # Score
            sc_color = theme.ACCENT_GREEN_TEXT if m.is_completed else theme.TEXT_MUTED
            ctk.CTkLabel(row, text=m.score_display, width=70, font=ctk.CTkFont(size=12, weight="bold"), text_color=sc_color).pack(side="left", padx=3)

            # Away team
            ctk.CTkLabel(row, text=m.away_team_name, width=140, font=ctk.CTkFont(size=11, weight="bold"), text_color=theme.TEXT_PRIMARY, anchor="w").pack(side="left", padx=3)

            # Date & Time
            dt_s = f"{m.scheduled_date} {m.scheduled_time}".strip() or "-"
            ctk.CTkLabel(row, text=dt_s, width=120, font=ctk.CTkFont(size=11), text_color=theme.TEXT_SECONDARY, anchor="w").pack(side="left", padx=3)

            # Venue
            ctk.CTkLabel(row, text=m.venue or "-", width=120, font=ctk.CTkFont(size=11), text_color=theme.TEXT_MUTED, anchor="w").pack(side="left", padx=3)

            # Status Badge
            badge_bg, badge_fg = theme.get_status_colors(m.status)
            ctk.CTkLabel(
                row,
                text=m.status,
                fg_color=badge_bg,
                text_color=badge_fg,
                corner_radius=4,
                font=ctk.CTkFont(size=10, weight="bold"),
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
                font=ctk.CTkFont(size=10),
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
                font=ctk.CTkFont(size=11, weight="bold"),
                command=lambda match_id=m.id: self.handle_delete_match(match_id)
            ).pack(side="left", padx=2)

    # ----------------------------------------------------
    # Fixture Generation Wizard Modal
    # ----------------------------------------------------
    # ----------------------------------------------------
    # Fixture Generation Wizard Modal
    # ----------------------------------------------------
    def open_generate_wizard(self):
        modal = BaseModal(self, title="Generate Fixtures Wizard", width=620, height=580)

        ctk.CTkLabel(modal.body_frame, text="Tournament Format:", font=ctk.CTkFont(size=11), text_color=theme.TEXT_SECONDARY).pack(anchor="w", pady=(2, 2))
        format_menu = ctk.CTkOptionMenu(
            modal.body_frame,
            values=["Group Stage (Round Robin within Groups)", "League (Single Round Robin)", "League (Double Round Robin)", "Knockout Bracket (From Group Qualifiers)"],
            fg_color=theme.BG_INPUT
        )
        format_menu.pack(fill="x", pady=(0, 8))

        # Row 1: Start Date and End Date
        row1 = ctk.CTkFrame(modal.body_frame, fg_color="transparent")
        row1.pack(fill="x", pady=(0, 8))
        row1.columnconfigure(0, weight=1)
        row1.columnconfigure(1, weight=1)

        d_box = ctk.CTkFrame(row1, fg_color="transparent")
        d_box.grid(row=0, column=0, sticky="ew", padx=(0, 4))
        ctk.CTkLabel(d_box, text="Tournament Start Date (YYYY-MM-DD):", font=ctk.CTkFont(size=11), text_color=theme.TEXT_SECONDARY).pack(anchor="w")
        date_entry = ctk.CTkEntry(d_box, fg_color=theme.BG_INPUT, border_color=theme.BORDER_COLOR)
        date_entry.insert(0, (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d"))
        date_entry.pack(fill="x")

        end_d_box = ctk.CTkFrame(row1, fg_color="transparent")
        end_d_box.grid(row=0, column=1, sticky="ew", padx=(4, 0))
        ctk.CTkLabel(end_d_box, text="Ending Date (Optional / Auto-calculated):", font=ctk.CTkFont(size=11), text_color=theme.TEXT_SECONDARY).pack(anchor="w")
        end_date_entry = ctk.CTkEntry(end_d_box, fg_color=theme.BG_INPUT, border_color=theme.BORDER_COLOR)
        end_date_entry.insert(0, (datetime.now() + timedelta(days=7)).strftime("%Y-%m-%d"))
        end_date_entry.pack(fill="x")

        # Row 2: Days per Matchweek & Match Duration
        row2 = ctk.CTkFrame(modal.body_frame, fg_color="transparent")
        row2.pack(fill="x", pady=(0, 8))
        row2.columnconfigure(0, weight=1)
        row2.columnconfigure(1, weight=1)

        mw_box = ctk.CTkFrame(row2, fg_color="transparent")
        mw_box.grid(row=0, column=0, sticky="ew", padx=(0, 4))
        ctk.CTkLabel(mw_box, text="Days per Matchweek (Interval, e.g. 3):", font=ctk.CTkFont(size=11), text_color=theme.TEXT_SECONDARY).pack(anchor="w")
        mw_entry = ctk.CTkEntry(mw_box, fg_color=theme.BG_INPUT, border_color=theme.BORDER_COLOR)
        mw_entry.insert(0, "3")
        mw_entry.pack(fill="x")

        dur_box = ctk.CTkFrame(row2, fg_color="transparent")
        dur_box.grid(row=0, column=1, sticky="ew", padx=(4, 0))
        ctk.CTkLabel(dur_box, text="Match Duration (Minutes):", font=ctk.CTkFont(size=11), text_color=theme.TEXT_SECONDARY).pack(anchor="w")
        dur_entry = ctk.CTkEntry(dur_box, fg_color=theme.BG_INPUT, border_color=theme.BORDER_COLOR)
        dur_entry.insert(0, "30")
        dur_entry.pack(fill="x")

        # Row 3: Daily Kick-off Window (Hours)
        row3 = ctk.CTkFrame(modal.body_frame, fg_color="transparent")
        row3.pack(fill="x", pady=(0, 8))
        row3.columnconfigure(0, weight=1)
        row3.columnconfigure(1, weight=1)

        t_box = ctk.CTkFrame(row3, fg_color="transparent")
        t_box.grid(row=0, column=0, sticky="ew", padx=(0, 4))
        ctk.CTkLabel(t_box, text="Daily Match Kick-off Time:", font=ctk.CTkFont(size=11), text_color=theme.TEXT_SECONDARY).pack(anchor="w")
        time_entry = ctk.CTkEntry(t_box, fg_color=theme.BG_INPUT, border_color=theme.BORDER_COLOR)
        time_entry.insert(0, "16:00")
        time_entry.pack(fill="x")

        end_box = ctk.CTkFrame(row3, fg_color="transparent")
        end_box.grid(row=0, column=1, sticky="ew", padx=(4, 0))
        ctk.CTkLabel(end_box, text="Daily Operating End Time:", font=ctk.CTkFont(size=11), text_color=theme.TEXT_SECONDARY).pack(anchor="w")
        end_entry = ctk.CTkEntry(end_box, fg_color=theme.BG_INPUT, border_color=theme.BORDER_COLOR)
        end_entry.insert(0, "20:00")
        end_entry.pack(fill="x")

        # Row 4: Pitches
        row4 = ctk.CTkFrame(modal.body_frame, fg_color="transparent")
        row4.pack(fill="x", pady=(0, 8))

        ctk.CTkLabel(row4, text="Venues / Pitches (comma-separated for simultaneous matches):", font=ctk.CTkFont(size=11), text_color=theme.TEXT_SECONDARY).pack(anchor="w")
        venue_entry = ctk.CTkEntry(row4, fg_color=theme.BG_INPUT, border_color=theme.BORDER_COLOR)
        venue_entry.insert(0, "Minaram Pitch 1, Minaram Pitch 2")
        venue_entry.pack(fill="x")

        clear_check_var = ctk.BooleanVar(value=True)
        ctk.CTkCheckBox(
            modal.body_frame,
            text="Clear existing fixtures before generating",
            variable=clear_check_var,
            font=ctk.CTkFont(size=11),
            text_color=theme.TEXT_SECONDARY
        ).pack(anchor="w", pady=(2, 8))

        preview_box = ctk.CTkTextbox(modal.body_frame, height=120, fg_color=theme.BG_INPUT, border_color=theme.BORDER_COLOR, font=ctk.CTkFont(family="Consolas", size=10))
        preview_box.pack(fill="both", expand=True, pady=(0, 10))
        preview_box.insert("1.0", "Click 'Preview Schedule' to calculate Matchweek rounds and pairings...")

        generated_fixtures: List[Dict[str, Any]] = []

        def preview():
            nonlocal generated_fixtures
            fmt = format_menu.get()
            s_d = date_entry.get().strip()
            e_d = end_date_entry.get().strip()
            s_t = time_entry.get().strip() or "16:00"
            end_t = end_entry.get().strip() or "20:00"
            try:
                dur = int(dur_entry.get().strip() or "30")
            except ValueError:
                dur = 30
            try:
                days_mw = int(mw_entry.get().strip() or "3")
            except ValueError:
                days_mw = 3
            venues = [v.strip() for v in venue_entry.get().split(",") if v.strip()] or ["Minaram Stadium"]

            preview_box.delete("1.0", "end")
            try:
                if "Knockout" in fmt:
                    generated_fixtures = self.knockout_mgr.generate_bracket_from_group_qualifiers(
                        start_date=s_d, start_time=s_t, match_duration_mins=dur, venue=venues[0]
                    )
                elif "League" in fmt:
                    double = ("Double" in fmt)
                    generated_fixtures = self.fixture_gen.preview_league_fixtures(
                        start_date=s_d, start_time=s_t, match_duration_mins=dur, venues=venues,
                        double_round=double, day_end_time=end_t, end_date=e_d, days_per_matchweek=days_mw
                    )
                else:
                    generated_fixtures = self.fixture_gen.preview_group_fixtures(
                        start_date=s_d, start_time=s_t, match_duration_mins=dur, venues=venues,
                        double_round=False, day_end_time=end_t, end_date=e_d, days_per_matchweek=days_mw
                    )

                # Group by Matchweek
                mw_groups: Dict[int, List[Dict[str, Any]]] = {}
                for f in generated_fixtures:
                    mw_groups.setdefault(f.get("round_number", 1), []).append(f)

                txt = f"✓ Generated {len(generated_fixtures)} matches across {len(mw_groups)} Matchweeks:\n"
                txt += f"  Interval: 1 match every {days_mw} days per squad\n"
                for r_num, m_list in sorted(mw_groups.items()):
                    d_str = m_list[0].get("scheduled_date", "")
                    times = f"{m_list[0].get('scheduled_time', '')} to {m_list[-1].get('scheduled_time', '')}"
                    txt += f"  • Matchweek {r_num}: {d_str} ({len(m_list)} matches, {times})\n"

                txt += "\nSample Matchups:\n"
                for f in generated_fixtures[:6]:
                    txt += f"  M#{f['match_number']} [MW {f.get('round_number', 1)}]: {f['home_team_name']} vs {f['away_team_name']} | {f['scheduled_date']} {f['scheduled_time']} @ {f['venue']}\n"
                if len(generated_fixtures) > 6:
                    txt += f"  ... and {len(generated_fixtures) - 6} more matches.\n"

                preview_box.insert("1.0", txt)

            except Exception as e:
                preview_box.insert("1.0", f"Error generating preview: {str(e)}")

        def save():
            if not generated_fixtures:
                messagebox.showerror("No Fixtures", "Please preview the schedule first before saving.")
                return

            saved_cnt = self.fixture_gen.save_fixtures(generated_fixtures, clear_existing=clear_check_var.get())
            messagebox.showinfo("Saved", f"Successfully saved {saved_cnt} fixtures to tournament schedule!")
            modal.destroy()
            self.refresh()

        btn_row = ctk.CTkFrame(modal.body_frame, fg_color="transparent")
        btn_row.pack(fill="x")

        ctk.CTkButton(btn_row, text="Preview Schedule", fg_color=theme.BG_CARD, border_color=theme.BORDER_COLOR, border_width=1, hover_color=theme.BG_CARD_HOVER, text_color=theme.TEXT_PRIMARY, command=preview).pack(side="left")
        ctk.CTkButton(btn_row, text="Confirm & Save Schedule", fg_color=theme.ACCENT_GREEN, hover_color=theme.ACCENT_GREEN_HOVER, text_color=theme.TEXT_DARK, font=ctk.CTkFont(weight="bold"), command=save).pack(side="right")

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

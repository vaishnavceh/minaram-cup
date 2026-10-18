"""
Match results entry interface: score inputs, penalty shootout inputs,
walkovers, audit history viewer modal, and automatic recalculations.
"""

import gc
import customtkinter as ctk
from tkinter import messagebox
from typing import Optional

from app.ui import theme
from app.ui.modal import BaseModal, ConfirmDialog
from app.database import Database
from app.results_manager import ResultsManager
from app.fixture_generator import FixtureGenerator


class ResultsView(ctk.CTkScrollableFrame):
    def __init__(self, parent, db: Database):
        super().__init__(parent, fg_color="transparent")
        self.db = db
        self.results_mgr = ResultsManager(db)
        self.fixture_gen = FixtureGenerator(db)

        self.tab_var = ctk.StringVar(value="Awaiting Results")
        self.stage_var = ctk.StringVar(value="All Stages")

        self.build_ui()

    def refresh(self):
        self.load_results_table()

    def build_ui(self):
        # Header
        hdr = ctk.CTkFrame(self, fg_color="transparent")
        hdr.pack(fill="x", padx=16, pady=(12, 12))

        title_box = ctk.CTkFrame(hdr, fg_color="transparent")
        title_box.pack(side="left")
        ctk.CTkLabel(title_box, text="Match Results & Scores", font=ctk.CTkFont(size=20, weight="bold"), text_color=theme.TEXT_PRIMARY).pack(anchor="w")
        ctk.CTkLabel(title_box, text="Record scores, resolve shootouts, manage walkovers, and inspect audit logs", font=ctk.CTkFont(size=11), text_color=theme.TEXT_MUTED).pack(anchor="w")

        # Tabs / Toggle Bar
        nav_card = ctk.CTkFrame(self, fg_color=theme.BG_CARD, corner_radius=10, border_color=theme.BORDER_COLOR, border_width=1)
        nav_card.pack(fill="x", padx=16, pady=(0, 14))

        t_bar = ctk.CTkFrame(nav_card, fg_color="transparent")
        t_bar.pack(fill="x", padx=14, pady=10)

        self.tab_seg = ctk.CTkSegmentedButton(
            t_bar,
            values=["Awaiting Results", "Completed Matches"],
            variable=self.tab_var,
            selected_color=theme.ACCENT_GREEN,
            selected_hover_color=theme.ACCENT_GREEN_HOVER,
            unselected_color=theme.BG_INPUT,
            unselected_hover_color=theme.BG_CARD_HOVER,
            text_color=theme.TEXT_PRIMARY,
            command=lambda v: self.load_results_table()
        )
        self.tab_seg.pack(side="left")

        ctk.CTkLabel(t_bar, text="Stage:", font=ctk.CTkFont(size=11), text_color=theme.TEXT_MUTED).pack(side="left", padx=(20, 4))
        self.stage_menu = ctk.CTkOptionMenu(
            t_bar,
            variable=self.stage_var,
            values=["All Stages", "Group Stage", "League", "Quarter-Final", "Semi-Final", "Final"],
            width=130,
            height=28,
            fg_color=theme.BG_INPUT,
            command=lambda v: self.load_results_table()
        )
        self.stage_menu.pack(side="left")

        # Table Container
        self.table_card = ctk.CTkFrame(self, fg_color=theme.BG_CARD, corner_radius=10, border_color=theme.BORDER_COLOR, border_width=1)
        self.table_card.pack(fill="both", expand=True, padx=16, pady=(0, 20))

        # Table Header
        self.header_frame = ctk.CTkFrame(self.table_card, fg_color=theme.BG_INPUT, height=32, corner_radius=6)
        self.header_frame.pack(fill="x", padx=14, pady=10)

        cols = [
            ("M#", 36),
            ("Stage", 120),
            ("Home Team", 150),
            ("Score", 90),
            ("Away Team", 150),
            ("Date / Venue", 130),
            ("Status", 90),
            ("Actions", 160)
        ]
        for name, w in cols:
            ctk.CTkLabel(
                self.header_frame,
                text=name,
                font=ctk.CTkFont(size=11, weight="bold"),
                text_color=theme.TEXT_SECONDARY,
                width=w,
                anchor="center" if w < 100 else "w"
            ).pack(side="left", padx=3)

        self.rows_container = ctk.CTkFrame(self.table_card, fg_color="transparent")
        self.rows_container.pack(fill="both", expand=True, padx=14, pady=(0, 14))

        self.load_results_table()

    def load_results_table(self):
        for child in self.rows_container.winfo_children():
            child.destroy()

        tab = self.tab_var.get()
        status_filter = "Scheduled" if tab == "Awaiting Results" else "Completed"

        stage = self.stage_var.get()
        stage_filter = None if stage == "All Stages" else stage

        if tab == "Awaiting Results":
            matches = self.fixture_gen.get_matches(stage=stage_filter, status="Scheduled")
            # Also include Postponed/In Progress
            more_m = self.fixture_gen.get_matches(stage=stage_filter, status="In Progress")
            matches.extend(more_m)
        else:
            matches = self.fixture_gen.get_matches(stage=stage_filter, status="Completed")
            walkovers = self.fixture_gen.get_matches(stage=stage_filter, status="Walkover")
            matches.extend(walkovers)

        if not matches:
            empty_box = ctk.CTkFrame(self.rows_container, fg_color="transparent")
            empty_box.pack(fill="x", pady=30)
            txt = "No matches currently awaiting results." if tab == "Awaiting Results" else "No match results recorded yet."
            ctk.CTkLabel(empty_box, text=txt, font=ctk.CTkFont(size=13), text_color=theme.TEXT_MUTED).pack()
            return

        for idx, m in enumerate(matches):
            bg_col = theme.BG_INPUT if idx % 2 == 0 else theme.BG_ROW_ALT
            row = ctk.CTkFrame(self.rows_container, fg_color=bg_col, height=38, corner_radius=4)
            row.pack(fill="x", pady=2)

            ctk.CTkLabel(row, text=str(m.match_number), width=36, font=theme.get_font(11, "bold"), text_color=theme.TEXT_MUTED).pack(side="left", padx=3)

            stage_desc = f"{m.stage} ({m.group_name})" if m.group_name else m.stage
            ctk.CTkLabel(row, text=stage_desc, width=120, font=theme.get_font(11), text_color=theme.TEXT_SECONDARY, anchor="w").pack(side="left", padx=3)

            # Home team
            is_home_winner = (m.winner_team_id == m.home_team_id and m.is_completed)
            h_col = theme.ACCENT_GREEN_TEXT if is_home_winner else theme.TEXT_PRIMARY
            ctk.CTkLabel(row, text=m.home_team_name, width=150, font=theme.get_font(11, "bold"), text_color=h_col, anchor="w").pack(side="left", padx=3)

            # Score
            sc_color = theme.ACCENT_GREEN_TEXT if m.is_completed else theme.TEXT_MUTED
            ctk.CTkLabel(row, text=m.score_display, width=90, font=theme.get_font(12, "bold"), text_color=sc_color).pack(side="left", padx=3)

            # Away team
            is_away_winner = (m.winner_team_id == m.away_team_id and m.is_completed)
            a_col = theme.ACCENT_GREEN_TEXT if is_away_winner else theme.TEXT_PRIMARY
            ctk.CTkLabel(row, text=m.away_team_name, width=150, font=theme.get_font(11, "bold"), text_color=a_col, anchor="w").pack(side="left", padx=3)

            # Date / Venue
            dt_s = f"{m.scheduled_date} ({m.venue})".strip() or "-"
            ctk.CTkLabel(row, text=dt_s, width=130, font=theme.get_font(11), text_color=theme.TEXT_MUTED, anchor="w").pack(side="left", padx=3)

            # Status Badge
            badge_bg, badge_fg = theme.get_status_colors(m.status)
            ctk.CTkLabel(
                row,
                text=m.status,
                fg_color=badge_bg,
                text_color=badge_fg,
                corner_radius=4,
                font=theme.get_font(10, "bold"),
                width=80,
                height=22
            ).pack(side="left", padx=3)

            # Action Buttons
            act_box = ctk.CTkFrame(row, fg_color="transparent", width=160)
            act_box.pack(side="left", padx=3)

            if not m.is_completed:
                ctk.CTkButton(
                    act_box,
                    text="⚽ Enter Result",
                    width=100,
                    height=24,
                    fg_color=theme.ACCENT_GREEN,
                    hover_color=theme.ACCENT_GREEN_HOVER,
                    text_color=theme.TEXT_DARK,
                    font=theme.get_font(11, "bold"),
                    command=lambda match=m: self.open_score_entry_modal(match)
                ).pack(side="left", padx=2)
            else:
                ctk.CTkButton(
                    act_box,
                    text="Edit",
                    width=44,
                    height=22,
                    fg_color="transparent",
                    border_color=theme.BORDER_COLOR,
                    border_width=1,
                    hover_color=theme.BG_CARD_HOVER,
                    text_color=theme.TEXT_PRIMARY,
                    font=theme.get_font(10),
                    command=lambda match=m: self.open_score_entry_modal(match)
                ).pack(side="left", padx=2)

                ctk.CTkButton(
                    act_box,
                    text="Audit Log",
                    width=60,
                    height=22,
                    fg_color=theme.BG_CARD,
                    border_color=theme.BORDER_COLOR,
                    border_width=1,
                    hover_color=theme.BG_CARD_HOVER,
                    text_color=theme.TEXT_SECONDARY,
                    font=theme.get_font(10),
                    command=lambda match_id=m.id: self.open_audit_modal(match_id)
                ).pack(side="left", padx=2)

                ctk.CTkButton(
                    act_box,
                    text="Reset",
                    width=42,
                    height=22,
                    fg_color="transparent",
                    hover_color=theme.COLOR_DANGER_MUTED,
                    text_color=theme.COLOR_DANGER,
                    font=theme.get_font(10),
                    command=lambda match_id=m.id: self.handle_reset_match(match_id)
                ).pack(side="left", padx=2)

        gc.collect()

    # ----------------------------------------------------
    # Score Entry Modal
    # ----------------------------------------------------
    def open_score_entry_modal(self, match):
        if not match.home_team_id or not match.away_team_id:
            messagebox.showwarning("Incomplete Match", "Both teams must be determined before entering a result.")
            return

        modal = BaseModal(self, title=f"Enter Result — Match #{match.match_number}", width=480, height=530)

        # Team Matchup Header
        match_box = ctk.CTkFrame(modal.body_frame, fg_color=theme.BG_INPUT, corner_radius=8)
        match_box.pack(fill="x", pady=(0, 14))

        ctk.CTkLabel(
            match_box,
            text=f"{match.home_team_name}   vs   {match.away_team_name}",
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color=theme.TEXT_PRIMARY
        ).pack(pady=(8, 2))
        ctk.CTkLabel(
            match_box,
            text=f"Stage: {match.stage} • Venue: {match.venue}",
            font=ctk.CTkFont(size=11),
            text_color=theme.TEXT_MUTED
        ).pack(pady=(0, 8))

        # Score Inputs Row
        score_frame = ctk.CTkFrame(modal.body_frame, fg_color="transparent")
        score_frame.pack(fill="x", pady=(0, 10))
        score_frame.columnconfigure(0, weight=1)
        score_frame.columnconfigure(1, weight=1)

        # Home Score
        h_box = ctk.CTkFrame(score_frame, fg_color="transparent")
        h_box.grid(row=0, column=0, padx=6)
        ctk.CTkLabel(h_box, text=f"{match.home_team_name} Goals:", font=ctk.CTkFont(size=11), text_color=theme.TEXT_SECONDARY).pack(anchor="w")
        home_score_e = ctk.CTkEntry(h_box, font=ctk.CTkFont(size=20, weight="bold"), justify="center", height=42, fg_color=theme.BG_INPUT, border_color=theme.BORDER_COLOR)
        home_score_e.insert(0, str(match.home_score if match.home_score is not None else 0))
        home_score_e.pack(fill="x")

        # Away Score
        a_box = ctk.CTkFrame(score_frame, fg_color="transparent")
        a_box.grid(row=0, column=1, padx=6)
        ctk.CTkLabel(a_box, text=f"{match.away_team_name} Goals:", font=ctk.CTkFont(size=11), text_color=theme.TEXT_SECONDARY).pack(anchor="w")
        away_score_e = ctk.CTkEntry(a_box, font=ctk.CTkFont(size=20, weight="bold"), justify="center", height=42, fg_color=theme.BG_INPUT, border_color=theme.BORDER_COLOR)
        away_score_e.insert(0, str(match.away_score if match.away_score is not None else 0))
        away_score_e.pack(fill="x")

        # Knockout penalty shootout section (if knockout match)
        is_knockout = match.stage in ("Quarter-Final", "Semi-Final", "Final", "Round of 16")
        pen_frame = ctk.CTkFrame(modal.body_frame, fg_color="transparent")
        if is_knockout:
            pen_frame.pack(fill="x", pady=(0, 10))
            pen_frame.columnconfigure(0, weight=1)
            pen_frame.columnconfigure(1, weight=1)

            hp_box = ctk.CTkFrame(pen_frame, fg_color="transparent")
            hp_box.grid(row=0, column=0, padx=6)
            ctk.CTkLabel(hp_box, text="Home Penalties (if draw):", font=ctk.CTkFont(size=10), text_color=theme.TEXT_MUTED).pack(anchor="w")
            home_pen_e = ctk.CTkEntry(hp_box, justify="center", fg_color=theme.BG_INPUT, border_color=theme.BORDER_COLOR)
            if match.home_penalty is not None:
                home_pen_e.insert(0, str(match.home_penalty))
            home_pen_e.pack(fill="x")

            ap_box = ctk.CTkFrame(pen_frame, fg_color="transparent")
            ap_box.grid(row=0, column=1, padx=6)
            ctk.CTkLabel(ap_box, text="Away Penalties (if draw):", font=ctk.CTkFont(size=10), text_color=theme.TEXT_MUTED).pack(anchor="w")
            away_pen_e = ctk.CTkEntry(ap_box, justify="center", fg_color=theme.BG_INPUT, border_color=theme.BORDER_COLOR)
            if match.away_penalty is not None:
                away_pen_e.insert(0, str(match.away_penalty))
            away_pen_e.pack(fill="x")
        else:
            home_pen_e = None
            away_pen_e = None

        # Match Status
        ctk.CTkLabel(modal.body_frame, text="Match Outcome / Status:", font=ctk.CTkFont(size=11), text_color=theme.TEXT_SECONDARY).pack(anchor="w")
        status_menu = ctk.CTkOptionMenu(modal.body_frame, values=["Completed", "Walkover", "Abandoned"], fg_color=theme.BG_INPUT)
        status_menu.set(match.status if match.status in ("Completed", "Walkover", "Abandoned") else "Completed")
        status_menu.pack(fill="x", pady=(0, 6))

        # Walkover Winner dropdown (hidden unless Walkover selected)
        wo_frame = ctk.CTkFrame(modal.body_frame, fg_color="transparent")
        ctk.CTkLabel(wo_frame, text="Walkover Awarded To:", font=ctk.CTkFont(size=11), text_color=theme.TEXT_SECONDARY).pack(anchor="w")
        wo_menu = ctk.CTkOptionMenu(wo_frame, values=[match.home_team_name, match.away_team_name], fg_color=theme.BG_INPUT)
        if match.winner_team_id == match.away_team_id:
            wo_menu.set(match.away_team_name)
        else:
            wo_menu.set(match.home_team_name)
        wo_menu.pack(fill="x")

        notes_label = ctk.CTkLabel(modal.body_frame, text="Notes / Reason / Rule Reference:", font=ctk.CTkFont(size=11), text_color=theme.TEXT_SECONDARY)
        notes_entry = ctk.CTkEntry(modal.body_frame, fg_color=theme.BG_INPUT, border_color=theme.BORDER_COLOR)
        if match.notes:
            notes_entry.insert(0, match.notes)

        def on_status_change(choice):
            if choice == "Walkover":
                wo_frame.pack(fill="x", pady=(0, 6), before=notes_label)
            else:
                wo_frame.pack_forget()

        status_menu.configure(command=on_status_change)
        if match.status == "Walkover":
            wo_frame.pack(fill="x", pady=(0, 6), before=notes_label)

        # Fixture Rules Quick Actions Box
        rules_box = ctk.CTkFrame(modal.body_frame, fg_color=theme.BG_INPUT, corner_radius=6)
        rules_box.pack(fill="x", pady=(0, 10))

        ctk.CTkLabel(
            rules_box,
            text="Fixture Rules Presets (Rule 2 Walkover & Rule 3 Forfeit)",
            font=ctk.CTkFont(size=10, weight="bold"),
            text_color=theme.TEXT_MUTED
        ).pack(anchor="w", padx=8, pady=(4, 2))

        btn_row = ctk.CTkFrame(rules_box, fg_color="transparent")
        btn_row.pack(fill="x", padx=4, pady=(0, 5))

        def set_rule2_home():
            home_score_e.delete(0, "end")
            home_score_e.insert(0, "3")
            away_score_e.delete(0, "end")
            away_score_e.insert(0, "0")
            status_menu.set("Walkover")
            wo_menu.set(match.home_team_name)
            wo_frame.pack(fill="x", pady=(0, 6), before=notes_label)
            notes_entry.delete(0, "end")
            notes_entry.insert(0, f"Rule 2 Walkover: 3–0 awarded to {match.home_team_name} (opponent failed to play within deadline)")

        def set_rule2_away():
            home_score_e.delete(0, "end")
            home_score_e.insert(0, "0")
            away_score_e.delete(0, "end")
            away_score_e.insert(0, "3")
            status_menu.set("Walkover")
            wo_menu.set(match.away_team_name)
            wo_frame.pack(fill="x", pady=(0, 6), before=notes_label)
            notes_entry.delete(0, "end")
            notes_entry.insert(0, f"Rule 2 Walkover: 3–0 awarded to {match.away_team_name} (opponent failed to play within deadline)")

        def set_rule3_draw():
            home_score_e.delete(0, "end")
            home_score_e.insert(0, "0")
            away_score_e.delete(0, "end")
            away_score_e.insert(0, "0")
            status_menu.set("Completed")
            wo_frame.pack_forget()
            notes_entry.delete(0, "end")
            notes_entry.insert(0, "Rule 3: Both teams failed to play within deadline (0–0 recorded, 1 point awarded to each team)")

        h_name_short = match.home_team_name[:12] if len(match.home_team_name) > 12 else match.home_team_name
        a_name_short = match.away_team_name[:12] if len(match.away_team_name) > 12 else match.away_team_name

        ctk.CTkButton(
            btn_row,
            text=f"Rule 2: 3-0 to {h_name_short}",
            height=24,
            font=ctk.CTkFont(size=10),
            fg_color=theme.BG_CARD,
            hover_color=theme.BG_CARD_HOVER,
            command=set_rule2_home
        ).pack(side="left", expand=True, fill="x", padx=2)

        ctk.CTkButton(
            btn_row,
            text=f"Rule 2: 3-0 to {a_name_short}",
            height=24,
            font=ctk.CTkFont(size=10),
            fg_color=theme.BG_CARD,
            hover_color=theme.BG_CARD_HOVER,
            command=set_rule2_away
        ).pack(side="left", expand=True, fill="x", padx=2)

        ctk.CTkButton(
            btn_row,
            text="Rule 3: 0-0 Draw",
            height=24,
            font=ctk.CTkFont(size=10),
            fg_color=theme.BG_CARD,
            hover_color=theme.BG_CARD_HOVER,
            command=set_rule3_draw
        ).pack(side="left", expand=True, fill="x", padx=2)

        notes_label.pack(anchor="w")
        notes_entry.pack(fill="x", pady=(0, 14))

        def save_result():
            try:
                h_sc = int(home_score_e.get().strip())
                a_sc = int(away_score_e.get().strip())
            except ValueError:
                messagebox.showerror("Invalid Score", "Scores must be integer numbers.")
                return

            h_pen = None
            a_pen = None
            if is_knockout and home_pen_e and away_pen_e:
                hp_val = home_pen_e.get().strip()
                ap_val = away_pen_e.get().strip()
                if hp_val and ap_val:
                    try:
                        h_pen = int(hp_val)
                        a_pen = int(ap_val)
                    except ValueError:
                        messagebox.showerror("Invalid Penalties", "Penalty scores must be integers.")
                        return

            stat = status_menu.get()
            wo_winner = None
            if stat == "Walkover":
                sel_w = wo_menu.get()
                wo_winner = match.home_team_id if sel_w == match.home_team_name else match.away_team_id

            ok, msg = self.results_mgr.record_result(
                match_id=match.id,
                home_score=h_sc,
                away_score=a_sc,
                status=stat,
                home_penalty=h_pen,
                away_penalty=a_pen,
                walkover_winner_id=wo_winner,
                notes=notes_entry.get().strip()
            )

            if not ok:
                messagebox.showerror("Error", msg)
            else:
                messagebox.showinfo("Result Saved", msg)
                modal.destroy()
                self.load_results_table()

        ctk.CTkButton(
            modal.body_frame,
            text="Confirm & Save Result",
            fg_color=theme.ACCENT_GREEN,
            hover_color=theme.ACCENT_GREEN_HOVER,
            text_color=theme.TEXT_DARK,
            font=ctk.CTkFont(weight="bold"),
            command=save_result
        ).pack(fill="x")

    def handle_reset_match(self, match_id: int):
        ConfirmDialog(
            self,
            title="Reset Match Result",
            message="Are you sure you want to reset this match back to Scheduled?\nScores will be removed and standings will automatically recalculate.",
            confirm_text="Reset Result",
            is_danger=True,
            on_confirm=lambda: [self.results_mgr.reset_result(match_id), self.load_results_table()]
        )

    def open_audit_modal(self, match_id: int):
        modal = BaseModal(self, title=f"Audit Trail — Match #{match_id}", width=520, height=400)

        audits = self.results_mgr.get_audit_trail(match_id)
        if not audits:
            ctk.CTkLabel(modal.body_frame, text="No revision history recorded for this match.", font=ctk.CTkFont(size=12), text_color=theme.TEXT_MUTED).pack(pady=20)
            return

        scroll = ctk.CTkScrollableFrame(modal.body_frame, fg_color="transparent", height=300)
        scroll.pack(fill="both", expand=True)

        for a in audits:
            box = ctk.CTkFrame(scroll, fg_color=theme.BG_INPUT, corner_radius=6)
            box.pack(fill="x", pady=3)

            top = ctk.CTkFrame(box, fg_color="transparent")
            top.pack(fill="x", padx=10, pady=(6, 2))
            ctk.CTkLabel(top, text=a.action, font=ctk.CTkFont(size=12, weight="bold"), text_color=theme.TEXT_PRIMARY).pack(side="left")
            ctk.CTkLabel(top, text=a.timestamp, font=ctk.CTkFont(size=10), text_color=theme.TEXT_MUTED).pack(side="right")

            score_diff = f"Score: {a.old_home_score}-{a.old_away_score}  ➔  {a.new_home_score}-{a.new_away_score}"
            ctk.CTkLabel(box, text=score_diff, font=ctk.CTkFont(size=11), text_color=theme.ACCENT_GREEN_TEXT).pack(anchor="w", padx=10)

            if a.notes:
                ctk.CTkLabel(box, text=f"Notes: {a.notes}", font=ctk.CTkFont(size=10), text_color=theme.TEXT_SECONDARY).pack(anchor="w", padx=10, pady=(2, 6))

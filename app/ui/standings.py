"""
Points table and tournament standings view: group tables, qualification indicators,
form guides (W/D/L), and tie-breaker summaries.
"""

import gc
import customtkinter as ctk
from tkinter import filedialog, messagebox
from typing import Dict, Any, List, Optional
from functools import cmp_to_key

from app.ui import theme
from app.ui.modal import BaseModal
from app.database import Database
from app.standings import StandingsCalculator
from app.export_service import ExportService
from app.results_manager import ResultsManager
from app.fixture_generator import FixtureGenerator


class StandingsView(ctk.CTkScrollableFrame):
    def __init__(self, parent, db: Database):
        super().__init__(parent, fg_color="transparent")
        self.db = db
        self.standings_calc = StandingsCalculator(db)
        self.export_service = ExportService(db)
        self.results_mgr = ResultsManager(db)
        self.fixture_gen = FixtureGenerator(db)

        self.build_ui()

    def refresh(self):
        self.load_standings_tables()

    def build_ui(self):
        # Header
        hdr = ctk.CTkFrame(self, fg_color="transparent")
        hdr.pack(fill="x", padx=16, pady=(12, 12))

        title_box = ctk.CTkFrame(hdr, fg_color="transparent")
        title_box.pack(side="left")
        ctk.CTkLabel(title_box, text="Points Table & Standings", font=ctk.CTkFont(size=20, weight="bold"), text_color=theme.TEXT_PRIMARY).pack(anchor="w")
        
        w_pts = self.db.get_setting("win_points", "3")
        d_pts = self.db.get_setting("draw_points", "1")
        l_pts = self.db.get_setting("loss_points", "0")
        tie_b = self.db.get_setting("tie_breakers", "points,goal_difference,goals_for,head_to_head,won")
        
        rule_sub = f"Scoring: Win={w_pts}pts, Draw={d_pts}pts, Loss={l_pts}pts • Tie-breakers: {tie_b.replace(',', ' ➔ ')}"
        ctk.CTkLabel(title_box, text=rule_sub, font=ctk.CTkFont(size=11), text_color=theme.TEXT_MUTED).pack(anchor="w")

        # Action Buttons
        btn_box = ctk.CTkFrame(hdr, fg_color="transparent")
        btn_box.pack(side="right")

        ctk.CTkButton(
            btn_box,
            text="✏️ Edit Points Table",
            fg_color=theme.ACCENT_GREEN,
            hover_color=theme.ACCENT_GREEN_HOVER,
            text_color=theme.TEXT_DARK,
            font=ctk.CTkFont(size=12, weight="bold"),
            height=32,
            command=self.open_edit_standings_modal
        ).pack(side="left", padx=4)

        ctk.CTkButton(
            btn_box,
            text="📤 Export Standings",
            fg_color=theme.BG_CARD,
            border_color=theme.BORDER_COLOR,
            border_width=1,
            hover_color=theme.BG_CARD_HOVER,
            text_color=theme.TEXT_PRIMARY,
            height=32,
            command=self.handle_export
        ).pack(side="left", padx=4)

        # Container for Tables
        self.tables_container = ctk.CTkFrame(self, fg_color="transparent")
        self.tables_container.pack(fill="both", expand=True, padx=16, pady=(0, 20))

        self.load_standings_tables()

    def load_standings_tables(self):
        for child in self.tables_container.winfo_children():
            child.destroy()

        all_groups = self.standings_calc.calculate_all_groups_standings()

        # If no groups exist, check for league standings
        if not all_groups:
            league_rows = self.standings_calc.calculate_group_standings(group_id=None)
            if league_rows:
                all_groups = {"League Table": league_rows}

        if not all_groups:
            empty_box = ctk.CTkFrame(self.tables_container, fg_color=theme.BG_CARD, corner_radius=10, border_color=theme.BORDER_COLOR, border_width=1)
            empty_box.pack(fill="x", pady=20)
            ctk.CTkLabel(empty_box, text="No standings data available yet.\nStandings update automatically as match results are confirmed.", font=ctk.CTkFont(size=13), text_color=theme.TEXT_MUTED).pack(pady=24)
            return

        # Render Table Card for each Group
        for g_name, standing_rows in all_groups.items():
            card = ctk.CTkFrame(self.tables_container, fg_color=theme.BG_CARD, corner_radius=10, border_color=theme.BORDER_COLOR, border_width=1)
            card.pack(fill="x", pady=(0, 16))

            # Table Header Bar
            t_hdr = ctk.CTkFrame(card, fg_color="transparent")
            t_hdr.pack(fill="x", padx=14, pady=(12, 8))

            ctk.CTkLabel(t_hdr, text=g_name, font=ctk.CTkFont(size=15, weight="bold"), text_color=theme.TEXT_PRIMARY).pack(side="left")
            ctk.CTkLabel(t_hdr, text="Top positions qualify for Knockout Stage", font=ctk.CTkFont(size=11), text_color=theme.TEXT_MUTED).pack(side="right")

            # Column Names
            cols_frame = ctk.CTkFrame(card, fg_color=theme.BG_INPUT, height=32, corner_radius=6)
            cols_frame.pack(fill="x", padx=14, pady=(0, 8))

            cols = [
                ("Rank", 50),
                ("Team Name", 180),
                ("P", 35),
                ("W", 35),
                ("D", 35),
                ("L", 35),
                ("GF", 40),
                ("GA", 40),
                ("GD", 45),
                ("PTS", 45),
                ("Form", 110),
                ("Status", 100)
            ]
            for col_name, col_w in cols:
                ctk.CTkLabel(
                    cols_frame,
                    text=col_name,
                    font=theme.get_font(11, "bold"),
                    text_color=theme.TEXT_SECONDARY,
                    width=col_w,
                    anchor="w" if col_name == "Team Name" else "center"
                ).pack(side="left", padx=2)

            # Rows
            if not standing_rows:
                ctk.CTkLabel(card, text="No confirmed matches in this group yet.", font=theme.get_font(11), text_color=theme.TEXT_MUTED).pack(pady=14)
            else:
                for idx, row in enumerate(standing_rows):
                    row_bg = theme.BG_INPUT if idx % 2 == 0 else theme.BG_ROW_ALT
                    r_frame = ctk.CTkFrame(card, fg_color=row_bg, height=36, corner_radius=4)
                    r_frame.pack(fill="x", padx=14, pady=2)

                    # Qualification colored indicator line
                    qual_color = theme.ACCENT_GREEN if row.is_qualified else "transparent"
                    ctk.CTkFrame(r_frame, width=3, fg_color=qual_color).pack(side="left", fill="y", padx=(0, 4))

                    # Rank
                    ctk.CTkLabel(r_frame, text=str(row.rank), width=46, font=theme.get_font(11, "bold"), text_color=theme.ACCENT_GREEN_TEXT if row.is_qualified else theme.TEXT_MUTED).pack(side="left", padx=2)

                    # Team
                    t_name_box = ctk.CTkFrame(r_frame, fg_color="transparent", width=180)
                    t_name_box.pack(side="left", padx=2)
                    ctk.CTkLabel(t_name_box, text=row.team_name, font=theme.get_font(11, "bold"), text_color=theme.TEXT_PRIMARY, anchor="w").pack(side="left")
                    if row.has_override:
                        ctk.CTkLabel(t_name_box, text=" [ADJ]", font=theme.get_font(9, "bold"), text_color="#F59E0B").pack(side="left")

                    # P, W, D, L
                    ctk.CTkLabel(r_frame, text=str(row.played), width=35, font=theme.get_font(11), text_color=theme.TEXT_SECONDARY).pack(side="left", padx=2)
                    ctk.CTkLabel(r_frame, text=str(row.won), width=35, font=theme.get_font(11), text_color=theme.ACCENT_GREEN_TEXT).pack(side="left", padx=2)
                    ctk.CTkLabel(r_frame, text=str(row.drawn), width=35, font=theme.get_font(11), text_color=theme.TEXT_SECONDARY).pack(side="left", padx=2)
                    ctk.CTkLabel(r_frame, text=str(row.lost), width=35, font=theme.get_font(11), text_color=theme.COLOR_DANGER).pack(side="left", padx=2)

                    # Goals
                    ctk.CTkLabel(r_frame, text=str(row.goals_for), width=40, font=theme.get_font(11), text_color=theme.TEXT_SECONDARY).pack(side="left", padx=2)
                    ctk.CTkLabel(r_frame, text=str(row.goals_against), width=40, font=theme.get_font(11), text_color=theme.TEXT_SECONDARY).pack(side="left", padx=2)

                    gd_txt = f"+{row.goal_difference}" if row.goal_difference > 0 else str(row.goal_difference)
                    ctk.CTkLabel(r_frame, text=gd_txt, width=45, font=theme.get_font(11), text_color=theme.TEXT_SECONDARY).pack(side="left", padx=2)

                    # Points
                    ctk.CTkLabel(r_frame, text=str(row.points), width=45, font=theme.get_font(12, "bold"), text_color=theme.ACCENT_GREEN_TEXT).pack(side="left", padx=2)

                    # Form chips
                    form_box = ctk.CTkFrame(r_frame, fg_color="transparent", width=110)
                    form_box.pack(side="left", padx=2)

                    if not row.form:
                        ctk.CTkLabel(form_box, text="-", font=theme.get_font(10), text_color=theme.TEXT_MUTED).pack()
                    else:
                        for outcome in row.form:
                            f_bg = theme.ACCENT_GREEN_MUTED if outcome == "W" else (theme.COLOR_DANGER_MUTED if outcome == "L" else theme.BORDER_COLOR)
                            f_fg = theme.ACCENT_GREEN_TEXT if outcome == "W" else (theme.COLOR_DANGER if outcome == "L" else theme.TEXT_SECONDARY)
                            chip = ctk.CTkLabel(form_box, text=outcome, width=18, height=18, fg_color=f_bg, text_color=f_fg, corner_radius=3, font=theme.get_font(9, "bold"))
                            chip.pack(side="left", padx=1)

                    # Status Badge
                    if row.is_qualified:
                        ctk.CTkLabel(
                            r_frame,
                            text="QUALIFIED",
                            fg_color=theme.ACCENT_GREEN_MUTED,
                            text_color=theme.ACCENT_GREEN_TEXT,
                            corner_radius=4,
                            font=theme.get_font(10, "bold"),
                            width=90,
                            height=20
                        ).pack(side="left", padx=4)
                    else:
                        ctk.CTkLabel(r_frame, text="", width=90).pack(side="left", padx=4)

                # Legend at bottom of card
                leg = ctk.CTkFrame(card, fg_color="transparent")
                leg.pack(fill="x", padx=14, pady=(8, 12))
                ctk.CTkFrame(leg, width=10, height=10, fg_color=theme.ACCENT_GREEN).pack(side="left", padx=(0, 6))
                ctk.CTkLabel(leg, text="Green indicator marks qualification zone for the Knockout Stage", font=theme.get_font(10), text_color=theme.TEXT_MUTED).pack(side="left")

        gc.collect()

    def handle_export(self):
        dest = filedialog.asksaveasfilename(
            defaultextension=".xlsx",
            initialfile="minaram_standings.xlsx",
            filetypes=[("Excel Files", "*.xlsx"), ("CSV Files", "*.csv")]
        )
        if not dest:
            return
        try:
            self.export_service.export_standings(dest)
            messagebox.showinfo("Export Complete", f"Standings exported successfully to:\n{dest}")
        except Exception as e:
            messagebox.showerror("Export Failed", str(e))

    def open_edit_standings_modal(self):
        modal = BaseModal(self, title="Edit Points Table & Match Goals", width=920, height=690)

        # Subtitle
        ctk.CTkLabel(
            modal.body_frame,
            text="Enter the goals scored by the two teams. Played, Won, Drawn, Lost, GF, GA, GD, Points, and Rankings calculate on their own automatically.",
            font=ctk.CTkFont(size=11),
            text_color=theme.TEXT_MUTED
        ).pack(anchor="w", pady=(0, 8))

        # Top Bar: Group Selector
        tb = ctk.CTkFrame(modal.body_frame, fg_color="transparent")
        tb.pack(fill="x", pady=(0, 8))

        groups = self.db.execute_query("SELECT id, name FROM groups ORDER BY display_order ASC, name ASC;")
        group_names = [g["name"] for g in groups] or ["Group A"]
        selected_grp_var = ctk.StringVar(value=group_names[0] if group_names else "Group A")

        ctk.CTkLabel(tb, text="Select Group:", font=ctk.CTkFont(size=12, weight="bold"), text_color=theme.TEXT_PRIMARY).pack(side="left", padx=(0, 8))

        # Live Standings Preview Card (at top)
        preview_card = ctk.CTkFrame(modal.body_frame, fg_color=theme.BG_INPUT, corner_radius=8, border_color=theme.BORDER_COLOR, border_width=1)
        preview_card.pack(fill="x", pady=(0, 10))

        preview_hdr = ctk.CTkFrame(preview_card, fg_color="transparent")
        preview_hdr.pack(fill="x", padx=12, pady=(8, 4))
        ctk.CTkLabel(preview_hdr, text="📊 Live Calculated Points Table", font=ctk.CTkFont(size=12, weight="bold"), text_color=theme.ACCENT_GREEN_TEXT).pack(side="left")
        ctk.CTkLabel(preview_hdr, text="Auto-reorders in real-time as match scores are typed below", font=ctk.CTkFont(size=10), text_color=theme.TEXT_MUTED).pack(side="right")

        preview_table_frame = ctk.CTkFrame(preview_card, fg_color="transparent")
        preview_table_frame.pack(fill="x", padx=12, pady=(0, 8))

        # Section label for matches
        ctk.CTkLabel(modal.body_frame, text="⚽ Group Fixtures — Enter Match Goals:", font=ctk.CTkFont(size=12, weight="bold"), text_color=theme.TEXT_PRIMARY).pack(anchor="w", pady=(2, 6))

        # Scrollable matches container
        matches_scroll = ctk.CTkScrollableFrame(modal.body_frame, fg_color="transparent", height=280)
        matches_scroll.pack(fill="both", expand=True, pady=(0, 8))

        match_entries: Dict[int, Dict[str, Any]] = {}
        target_teams: List[Dict[str, Any]] = []
        target_g_id: Optional[int] = None

        def recalculate_live_standings():
            """Recalculates all standings factors (P, W, D, L, GF, GA, GD, PTS) on the fly."""
            win_pts = int(self.db.get_setting("win_points", "3"))
            draw_pts = int(self.db.get_setting("draw_points", "1"))
            loss_pts = int(self.db.get_setting("loss_points", "0"))
            tie_breakers_str = self.db.get_setting("tie_breakers", "points,goal_difference,goals_for,head_to_head,won")
            tie_breakers = [t.strip().lower() for t in tie_breakers_str.split(",") if t.strip()]

            stats: Dict[int, Dict[str, Any]] = {}
            for tr in target_teams:
                stats[tr["id"]] = {
                    "team_id": tr["id"],
                    "team_name": tr["name"],
                    "played": 0,
                    "won": 0,
                    "drawn": 0,
                    "lost": 0,
                    "goals_for": 0,
                    "goals_against": 0,
                    "goal_difference": 0,
                    "points": 0,
                }

            h2h: Dict[tuple, Dict[str, int]] = {}

            for mid, item in match_entries.items():
                m = item["match"]
                h_str = item["h_entry"].get().strip()
                a_str = item["a_entry"].get().strip()
                if h_str != "" and a_str != "":
                    try:
                        h_goals = int(h_str)
                        a_goals = int(a_str)
                        if h_goals >= 0 and a_goals >= 0:
                            h_id = m.home_team_id
                            a_id = m.away_team_id
                            if h_id in stats and a_id in stats:
                                stats[h_id]["played"] += 1
                                stats[a_id]["played"] += 1
                                stats[h_id]["goals_for"] += h_goals
                                stats[h_id]["goals_against"] += a_goals
                                stats[a_id]["goals_for"] += a_goals
                                stats[a_id]["goals_against"] += h_goals

                                h2h.setdefault((h_id, a_id), {"points": 0})
                                h2h.setdefault((a_id, h_id), {"points": 0})

                                if h_goals > a_goals:
                                    stats[h_id]["won"] += 1
                                    stats[h_id]["points"] += win_pts
                                    stats[a_id]["lost"] += 1
                                    stats[a_id]["points"] += loss_pts
                                    h2h[(h_id, a_id)]["points"] += win_pts
                                elif a_goals > h_goals:
                                    stats[a_id]["won"] += 1
                                    stats[a_id]["points"] += win_pts
                                    stats[h_id]["lost"] += 1
                                    stats[h_id]["points"] += loss_pts
                                    h2h[(a_id, h_id)]["points"] += win_pts
                                else:
                                    stats[h_id]["drawn"] += 1
                                    stats[h_id]["points"] += draw_pts
                                    stats[a_id]["drawn"] += 1
                                    stats[a_id]["points"] += draw_pts
                                    h2h[(h_id, a_id)]["points"] += draw_pts
                                    h2h[(a_id, h_id)]["points"] += draw_pts
                    except ValueError:
                        pass

            for s in stats.values():
                s["goal_difference"] = s["goals_for"] - s["goals_against"]

            def compare(a: Dict[str, Any], b: Dict[str, Any]) -> int:
                for tb in tie_breakers:
                    if tb == "points":
                        if a["points"] != b["points"]:
                            return 1 if a["points"] < b["points"] else -1
                    elif tb in ("goal_difference", "goal_diff", "gd"):
                        if a["goal_difference"] != b["goal_difference"]:
                            return 1 if a["goal_difference"] < b["goal_difference"] else -1
                    elif tb in ("goals_for", "gf"):
                        if a["goals_for"] != b["goals_for"]:
                            return 1 if a["goals_for"] < b["goals_for"] else -1
                    elif tb in ("won", "wins"):
                        if a["won"] != b["won"]:
                            return 1 if a["won"] < b["won"] else -1
                    elif tb in ("head_to_head", "h2h"):
                        rec_a = h2h.get((a["team_id"], b["team_id"]))
                        rec_b = h2h.get((b["team_id"], a["team_id"]))
                        if rec_a and rec_b and rec_a["points"] != rec_b["points"]:
                            return 1 if rec_a["points"] < rec_b["points"] else -1
                if a["team_name"].lower() != b["team_name"].lower():
                    return 1 if a["team_name"].lower() > b["team_name"].lower() else -1
                return 0

            sorted_teams = sorted(stats.values(), key=cmp_to_key(compare))

            # Update live preview table widgets
            for child in preview_table_frame.winfo_children():
                child.destroy()

            # Header row
            p_hdr = ctk.CTkFrame(preview_table_frame, fg_color=theme.BG_CARD, height=26, corner_radius=4)
            p_hdr.pack(fill="x", pady=(0, 2))
            cols = [
                ("Rank", 42, "center"),
                ("Team Name", 190, "w"),
                ("P", 40, "center"),
                ("W", 40, "center"),
                ("D", 40, "center"),
                ("L", 40, "center"),
                ("GF", 44, "center"),
                ("GA", 44, "center"),
                ("GD", 48, "center"),
                ("PTS", 54, "center")
            ]
            for c_title, c_w, c_anc in cols:
                ctk.CTkLabel(p_hdr, text=c_title, width=c_w, font=ctk.CTkFont(size=10, weight="bold"), text_color=theme.TEXT_SECONDARY, anchor=c_anc).pack(side="left", padx=1)

            # Team rows
            for idx, s in enumerate(sorted_teams, start=1):
                p_row = ctk.CTkFrame(preview_table_frame, fg_color=theme.BG_CARD if idx % 2 == 0 else theme.BG_INPUT, height=28, corner_radius=4)
                p_row.pack(fill="x", pady=1)

                r_col = theme.ACCENT_GREEN_TEXT if idx <= 2 else theme.TEXT_MUTED
                ctk.CTkLabel(p_row, text=str(idx), width=42, font=ctk.CTkFont(size=11, weight="bold"), text_color=r_col).pack(side="left", padx=1)
                ctk.CTkLabel(p_row, text=s["team_name"], width=190, font=ctk.CTkFont(size=11, weight="bold"), text_color=theme.TEXT_PRIMARY, anchor="w").pack(side="left", padx=1)
                ctk.CTkLabel(p_row, text=str(s["played"]), width=40, font=ctk.CTkFont(size=11), text_color=theme.TEXT_SECONDARY).pack(side="left", padx=1)
                ctk.CTkLabel(p_row, text=str(s["won"]), width=40, font=ctk.CTkFont(size=11), text_color=theme.ACCENT_GREEN_TEXT).pack(side="left", padx=1)
                ctk.CTkLabel(p_row, text=str(s["drawn"]), width=40, font=ctk.CTkFont(size=11), text_color=theme.TEXT_SECONDARY).pack(side="left", padx=1)
                ctk.CTkLabel(p_row, text=str(s["lost"]), width=40, font=ctk.CTkFont(size=11), text_color=theme.COLOR_DANGER).pack(side="left", padx=1)
                ctk.CTkLabel(p_row, text=str(s["goals_for"]), width=44, font=ctk.CTkFont(size=11), text_color=theme.TEXT_SECONDARY).pack(side="left", padx=1)
                ctk.CTkLabel(p_row, text=str(s["goals_against"]), width=44, font=ctk.CTkFont(size=11), text_color=theme.TEXT_SECONDARY).pack(side="left", padx=1)

                gd_txt = f"+{s['goal_difference']}" if s["goal_difference"] > 0 else str(s["goal_difference"])
                ctk.CTkLabel(p_row, text=gd_txt, width=48, font=ctk.CTkFont(size=11, weight="bold"), text_color=theme.TEXT_PRIMARY).pack(side="left", padx=1)
                ctk.CTkLabel(p_row, text=str(s["points"]), width=54, font=ctk.CTkFont(size=12, weight="bold"), text_color=theme.ACCENT_GREEN_TEXT).pack(side="left", padx=1)

        calc_timer = None

        def schedule_recalculation():
            nonlocal calc_timer
            if calc_timer is not None:
                try:
                    modal.after_cancel(calc_timer)
                except Exception:
                    pass
            calc_timer = modal.after(150, recalculate_live_standings)

        def populate_editor():
            nonlocal target_teams, target_g_id
            for child in matches_scroll.winfo_children():
                child.destroy()
            match_entries.clear()

            sel_g_name = selected_grp_var.get()
            target_g_id = None
            for g in groups:
                if g["name"] == sel_g_name:
                    target_g_id = g["id"]
                    break

            # Fetch teams
            team_rows = self.db.execute_query(
                "SELECT id, name FROM teams WHERE group_id = ? AND status = 'Confirmed' ORDER BY name ASC;",
                (target_g_id,)
            )
            target_teams = [{"id": r["id"], "name": r["name"]} for r in team_rows]

            # Fetch matches
            matches = self.fixture_gen.get_matches(group_id=target_g_id)

            if not matches:
                ctk.CTkLabel(matches_scroll, text="No fixtures generated for this group yet.\nPlease generate fixtures first using the Fixture Wizard.", font=ctk.CTkFont(size=12), text_color=theme.TEXT_MUTED).pack(pady=30)
                recalculate_live_standings()
                return

            for idx, m in enumerate(matches):
                mf = ctk.CTkFrame(matches_scroll, fg_color=theme.BG_CARD if idx % 2 == 0 else theme.BG_INPUT, corner_radius=6, height=44)
                mf.pack(fill="x", pady=2, padx=4)

                # Match Number & Matchweek Pill
                mw_lbl = f"M#{m.match_number} [MW {m.round_number}]" if m.round_number else f"M#{m.match_number}"
                ctk.CTkLabel(mf, text=mw_lbl, width=96, font=ctk.CTkFont(size=10, weight="bold"), text_color=theme.TEXT_MUTED, anchor="w").pack(side="left", padx=(8, 2))

                # Home Team Name
                ctk.CTkLabel(mf, text=m.home_team_name, width=170, font=ctk.CTkFont(size=12, weight="bold"), text_color=theme.TEXT_PRIMARY, anchor="e").pack(side="left", padx=4)

                # Home Goals Entry
                h_entry = ctk.CTkEntry(mf, width=44, height=30, justify="center", font=ctk.CTkFont(size=13, weight="bold"), fg_color=theme.BG_INPUT, border_color=theme.BORDER_COLOR)
                if m.home_score is not None:
                    h_entry.insert(0, str(m.home_score))
                h_entry.pack(side="left", padx=4)

                # VS Badge
                ctk.CTkLabel(mf, text="vs", width=24, font=ctk.CTkFont(size=10, weight="bold"), text_color=theme.TEXT_MUTED).pack(side="left", padx=1)

                # Away Goals Entry
                a_entry = ctk.CTkEntry(mf, width=44, height=30, justify="center", font=ctk.CTkFont(size=13, weight="bold"), fg_color=theme.BG_INPUT, border_color=theme.BORDER_COLOR)
                if m.away_score is not None:
                    a_entry.insert(0, str(m.away_score))
                a_entry.pack(side="left", padx=4)

                # Away Team Name
                ctk.CTkLabel(mf, text=m.away_team_name, width=170, font=ctk.CTkFont(size=12, weight="bold"), text_color=theme.TEXT_PRIMARY, anchor="w").pack(side="left", padx=4)

                # Date / Venue info
                dt_str = f"{m.scheduled_date or ''} {m.scheduled_time or ''}".strip()
                ctk.CTkLabel(mf, text=dt_str or "-", width=110, font=ctk.CTkFont(size=10), text_color=theme.TEXT_MUTED).pack(side="left", padx=2)

                # Clear Match button
                def make_clear_handler(h_e=h_entry, a_e=a_entry):
                    def handler():
                        h_e.delete(0, "end")
                        a_e.delete(0, "end")
                        recalculate_live_standings()
                    return handler

                ctk.CTkButton(
                    mf,
                    text="Clear",
                    width=46,
                    height=24,
                    fg_color=theme.BG_CARD,
                    hover_color=theme.BG_CARD_HOVER,
                    border_color=theme.BORDER_COLOR,
                    border_width=1,
                    text_color=theme.TEXT_MUTED,
                    font=ctk.CTkFont(size=10),
                    command=make_clear_handler()
                ).pack(side="left", padx=4)

                def on_key_change(e=None):
                    schedule_recalculation()

                h_entry.bind("<KeyRelease>", on_key_change)
                a_entry.bind("<KeyRelease>", on_key_change)

                match_entries[m.id] = {
                    "match": m,
                    "h_entry": h_entry,
                    "a_entry": a_entry
                }

            recalculate_live_standings()

        # Group Dropdown
        grp_dropdown = ctk.CTkOptionMenu(
            tb,
            variable=selected_grp_var,
            values=group_names,
            width=160,
            fg_color=theme.BG_INPUT,
            command=lambda _: populate_editor()
        )
        grp_dropdown.pack(side="left", padx=(0, 10))

        def clear_all_scores_in_group():
            for item in match_entries.values():
                item["h_entry"].delete(0, "end")
                item["a_entry"].delete(0, "end")
            recalculate_live_standings()

        ctk.CTkButton(
            tb,
            text="↺ Clear All Scores in Group",
            fg_color=theme.BG_CARD,
            border_color=theme.BORDER_COLOR,
            border_width=1,
            hover_color=theme.COLOR_DANGER_MUTED,
            text_color=theme.COLOR_DANGER,
            font=ctk.CTkFont(size=11),
            height=28,
            command=clear_all_scores_in_group
        ).pack(side="left")

        # Bottom Buttons
        bot_bar = ctk.CTkFrame(modal.body_frame, fg_color="transparent")
        bot_bar.pack(fill="x", pady=(4, 0))

        def save_and_commit_scores():
            saved_count = 0
            reset_count = 0
            try:
                for mid, item in match_entries.items():
                    m = item["match"]
                    h_val = item["h_entry"].get().strip()
                    a_val = item["a_entry"].get().strip()

                    if h_val != "" and a_val != "":
                        try:
                            h_score = int(h_val)
                            a_score = int(a_val)
                            if h_score >= 0 and a_score >= 0:
                                ok, _ = self.results_mgr.record_result(
                                    match_id=mid,
                                    home_score=h_score,
                                    away_score=a_score,
                                    status="Completed"
                                )
                                if ok:
                                    saved_count += 1
                        except ValueError:
                            pass
                    elif h_val == "" and a_val == "":
                        # If previously completed, reset back to scheduled
                        if m.is_completed:
                            self.results_mgr.reset_result(mid)
                            reset_count += 1

                # Clear stale manual overrides on this group so standings strictly match the goals
                if target_g_id:
                    self.standings_calc.clear_group_overrides(group_id=target_g_id)

                modal.destroy()
                self.refresh()
                messagebox.showinfo(
                    "Points Table Updated",
                    f"Successfully saved match goals ({saved_count} recorded, {reset_count} reset)!\n"
                    f"Points, Goal Differences, and Rankings have recalculated and auto-reordered on their own."
                )
            except Exception as ex:
                messagebox.showerror("Save Failed", f"Failed to save match scores: {str(ex)}")

        ctk.CTkButton(
            bot_bar,
            text="💾 Save Scores & Update Points Table",
            fg_color=theme.ACCENT_GREEN,
            hover_color=theme.ACCENT_GREEN_HOVER,
            text_color=theme.TEXT_DARK,
            font=ctk.CTkFont(size=12, weight="bold"),
            height=34,
            command=save_and_commit_scores
        ).pack(side="right", padx=(8, 0))

        ctk.CTkButton(
            bot_bar,
            text="Cancel",
            fg_color=theme.BG_CARD,
            hover_color=theme.BG_CARD_HOVER,
            border_color=theme.BORDER_COLOR,
            border_width=1,
            text_color=theme.TEXT_PRIMARY,
            height=34,
            command=modal.destroy
        ).pack(side="right")

        populate_editor()

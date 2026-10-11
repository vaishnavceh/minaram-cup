"""
Points table and tournament standings view: group tables, qualification indicators,
form guides (W/D/L), and tie-breaker summaries.
"""

import customtkinter as ctk
from tkinter import filedialog, messagebox

from app.ui import theme
from app.database import Database
from app.standings import StandingsCalculator
from app.export_service import ExportService


class StandingsView(ctk.CTkScrollableFrame):
    def __init__(self, parent, db: Database):
        super().__init__(parent, fg_color="transparent")
        self.db = db
        self.standings_calc = StandingsCalculator(db)
        self.export_service = ExportService(db)

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

        # Export Button
        ctk.CTkButton(
            hdr,
            text="📤 Export Standings",
            fg_color=theme.BG_CARD,
            border_color=theme.BORDER_COLOR,
            border_width=1,
            hover_color=theme.BG_CARD_HOVER,
            text_color=theme.TEXT_PRIMARY,
            height=32,
            command=self.handle_export
        ).pack(side="right")

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
                    font=ctk.CTkFont(size=11, weight="bold"),
                    text_color=theme.TEXT_SECONDARY,
                    width=col_w,
                    anchor="w" if col_name == "Team Name" else "center"
                ).pack(side="left", padx=2)

            # Rows
            if not standing_rows:
                ctk.CTkLabel(card, text="No confirmed matches in this group yet.", font=ctk.CTkFont(size=11), text_color=theme.TEXT_MUTED).pack(pady=14)
            else:
                for idx, row in enumerate(standing_rows):
                    row_bg = theme.BG_INPUT if idx % 2 == 0 else theme.BG_ROW_ALT
                    r_frame = ctk.CTkFrame(card, fg_color=row_bg, height=36, corner_radius=4)
                    r_frame.pack(fill="x", padx=14, pady=2)

                    # Qualification colored indicator line
                    qual_color = theme.ACCENT_GREEN if row.is_qualified else "transparent"
                    ctk.CTkFrame(r_frame, width=3, fg_color=qual_color).pack(side="left", fill="y", padx=(0, 4))

                    # Rank
                    ctk.CTkLabel(r_frame, text=str(row.rank), width=46, font=ctk.CTkFont(size=11, weight="bold"), text_color=theme.ACCENT_GREEN_TEXT if row.is_qualified else theme.TEXT_MUTED).pack(side="left", padx=2)

                    # Team
                    ctk.CTkLabel(r_frame, text=row.team_name, width=180, font=ctk.CTkFont(size=11, weight="bold"), text_color=theme.TEXT_PRIMARY, anchor="w").pack(side="left", padx=2)

                    # P, W, D, L
                    ctk.CTkLabel(r_frame, text=str(row.played), width=35, font=ctk.CTkFont(size=11), text_color=theme.TEXT_SECONDARY).pack(side="left", padx=2)
                    ctk.CTkLabel(r_frame, text=str(row.won), width=35, font=ctk.CTkFont(size=11), text_color=theme.ACCENT_GREEN_TEXT).pack(side="left", padx=2)
                    ctk.CTkLabel(r_frame, text=str(row.drawn), width=35, font=ctk.CTkFont(size=11), text_color=theme.TEXT_SECONDARY).pack(side="left", padx=2)
                    ctk.CTkLabel(r_frame, text=str(row.lost), width=35, font=ctk.CTkFont(size=11), text_color=theme.COLOR_DANGER).pack(side="left", padx=2)

                    # Goals
                    ctk.CTkLabel(r_frame, text=str(row.goals_for), width=40, font=ctk.CTkFont(size=11), text_color=theme.TEXT_SECONDARY).pack(side="left", padx=2)
                    ctk.CTkLabel(r_frame, text=str(row.goals_against), width=40, font=ctk.CTkFont(size=11), text_color=theme.TEXT_SECONDARY).pack(side="left", padx=2)

                    gd_txt = f"+{row.goal_difference}" if row.goal_difference > 0 else str(row.goal_difference)
                    ctk.CTkLabel(r_frame, text=gd_txt, width=45, font=ctk.CTkFont(size=11), text_color=theme.TEXT_SECONDARY).pack(side="left", padx=2)

                    # Points
                    ctk.CTkLabel(r_frame, text=str(row.points), width=45, font=ctk.CTkFont(size=12, weight="bold"), text_color=theme.ACCENT_GREEN_TEXT).pack(side="left", padx=2)

                    # Form chips
                    form_box = ctk.CTkFrame(r_frame, fg_color="transparent", width=110)
                    form_box.pack(side="left", padx=2)

                    if not row.form:
                        ctk.CTkLabel(form_box, text="-", font=ctk.CTkFont(size=10), text_color=theme.TEXT_MUTED).pack()
                    else:
                        for outcome in row.form:
                            f_bg = theme.ACCENT_GREEN_MUTED if outcome == "W" else (theme.COLOR_DANGER_MUTED if outcome == "L" else theme.BORDER_COLOR)
                            f_fg = theme.ACCENT_GREEN_TEXT if outcome == "W" else (theme.COLOR_DANGER if outcome == "L" else theme.TEXT_SECONDARY)
                            chip = ctk.CTkLabel(form_box, text=outcome, width=18, height=18, fg_color=f_bg, text_color=f_fg, corner_radius=3, font=ctk.CTkFont(size=9, weight="bold"))
                            chip.pack(side="left", padx=1)

                    # Status Badge
                    if row.is_qualified:
                        ctk.CTkLabel(
                            r_frame,
                            text="QUALIFIED",
                            fg_color=theme.ACCENT_GREEN_MUTED,
                            text_color=theme.ACCENT_GREEN_TEXT,
                            corner_radius=4,
                            font=ctk.CTkFont(size=10, weight="bold"),
                            width=90,
                            height=20
                        ).pack(side="left", padx=4)
                    else:
                        ctk.CTkLabel(r_frame, text="", width=90).pack(side="left", padx=4)

                # Legend at bottom of card
                leg = ctk.CTkFrame(card, fg_color="transparent")
                leg.pack(fill="x", padx=14, pady=(8, 12))
                ctk.CTkFrame(leg, width=10, height=10, fg_color=theme.ACCENT_GREEN).pack(side="left", padx=(0, 6))
                ctk.CTkLabel(leg, text="Green indicator marks qualification zone for the Knockout Stage", font=ctk.CTkFont(size=10), text_color=theme.TEXT_MUTED).pack(side="left")

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

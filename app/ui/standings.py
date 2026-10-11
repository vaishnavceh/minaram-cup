"""
Points table and tournament standings view: group tables, qualification indicators,
form guides (W/D/L), and tie-breaker summaries.
"""

import customtkinter as ctk
from tkinter import filedialog, messagebox

from app.ui import theme
from app.ui.modal import BaseModal
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
                    t_name_box = ctk.CTkFrame(r_frame, fg_color="transparent", width=180)
                    t_name_box.pack(side="left", padx=2)
                    ctk.CTkLabel(t_name_box, text=row.team_name, font=ctk.CTkFont(size=11, weight="bold"), text_color=theme.TEXT_PRIMARY, anchor="w").pack(side="left")
                    if row.has_override:
                        ctk.CTkLabel(t_name_box, text=" [ADJ]", font=ctk.CTkFont(size=9, weight="bold"), text_color="#F59E0B").pack(side="left")

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

    def open_edit_standings_modal(self):
        modal = BaseModal(self, title="Edit Points Table & Statistics", width=960, height=640)

        # Subtitle
        ctk.CTkLabel(
            modal.body_frame,
            text="Directly edit match records, goals, and points. Standings and rankings reorder automatically based on tournament tie-breakers.",
            font=ctk.CTkFont(size=11),
            text_color=theme.TEXT_MUTED
        ).pack(anchor="w", pady=(0, 10))

        # Toolbar: Group selection & Reset
        tb = ctk.CTkFrame(modal.body_frame, fg_color="transparent")
        tb.pack(fill="x", pady=(0, 10))

        # Get available groups
        groups = self.db.execute_query("SELECT id, name FROM groups ORDER BY display_order ASC, name ASC;")
        group_names = [g["name"] for g in groups] or ["All Teams"]
        selected_grp_var = ctk.StringVar(value=group_names[0] if group_names else "All Teams")

        ctk.CTkLabel(tb, text="Select Group:", font=ctk.CTkFont(size=11, weight="bold"), text_color=theme.TEXT_SECONDARY).pack(side="left", padx=(0, 6))

        # Scrollable rows frame
        rows_scroll = ctk.CTkScrollableFrame(modal.body_frame, fg_color="transparent", height=410)
        rows_scroll.pack(fill="both", expand=True, pady=(0, 10))

        team_entries = {}

        def populate_editor():
            for child in rows_scroll.winfo_children():
                child.destroy()
            team_entries.clear()

            sel_g_name = selected_grp_var.get()
            target_g_id = None
            for g in groups:
                if g["name"] == sel_g_name:
                    target_g_id = g["id"]
                    break

            standing_rows = self.standings_calc.calculate_group_standings(group_id=target_g_id)

            if not standing_rows:
                ctk.CTkLabel(rows_scroll, text="No confirmed teams in this group.", font=ctk.CTkFont(size=12), text_color=theme.TEXT_MUTED).pack(pady=30)
                return

            hdr_f = ctk.CTkFrame(rows_scroll, fg_color=theme.BG_INPUT, height=32, corner_radius=6)
            hdr_f.pack(fill="x", pady=(0, 6))

            headers = [
                ("Team Name", 170, "w"),
                ("P", 44, "center"),
                ("W", 44, "center"),
                ("D", 44, "center"),
                ("L", 44, "center"),
                ("GF", 48, "center"),
                ("GA", 48, "center"),
                ("GD", 48, "center"),
                ("PTS", 54, "center"),
                ("Admin Notes / Reason", 150, "w"),
                ("Reset", 50, "center")
            ]
            for title, w, anc in headers:
                ctk.CTkLabel(hdr_f, text=title, width=w, font=ctk.CTkFont(size=10, weight="bold"), text_color=theme.TEXT_SECONDARY, anchor=anc).pack(side="left", padx=2)

            for idx, r in enumerate(standing_rows):
                rf = ctk.CTkFrame(rows_scroll, fg_color=theme.BG_CARD if idx % 2 == 0 else theme.BG_INPUT, corner_radius=4, height=36)
                rf.pack(fill="x", pady=2)

                t_lbl = ctk.CTkLabel(rf, text=r.team_name, width=170, font=ctk.CTkFont(size=11, weight="bold"), text_color=theme.TEXT_PRIMARY, anchor="w")
                t_lbl.pack(side="left", padx=2)

                def make_num_entry(parent, default_val, width=44):
                    e = ctk.CTkEntry(parent, width=width, height=26, fg_color=theme.BG_INPUT, border_color=theme.BORDER_COLOR, justify="center", font=ctk.CTkFont(size=11))
                    e.insert(0, str(default_val))
                    e.pack(side="left", padx=2)
                    return e

                p_entry = make_num_entry(rf, r.played, 44)
                w_entry = make_num_entry(rf, r.won, 44)
                d_entry = make_num_entry(rf, r.drawn, 44)
                l_entry = make_num_entry(rf, r.lost, 44)
                gf_entry = make_num_entry(rf, r.goals_for, 48)
                ga_entry = make_num_entry(rf, r.goals_against, 48)

                gd_txt = f"+{r.goal_difference}" if r.goal_difference > 0 else str(r.goal_difference)
                gd_lbl = ctk.CTkLabel(rf, text=gd_txt, width=48, font=ctk.CTkFont(size=11, weight="bold"), text_color=theme.TEXT_SECONDARY)
                gd_lbl.pack(side="left", padx=2)

                def update_gd_label(*args, gf_e=gf_entry, ga_e=ga_entry, lbl=gd_lbl):
                    try:
                        gf = int(gf_e.get().strip() or "0")
                        ga = int(ga_e.get().strip() or "0")
                        diff = gf - ga
                        lbl.configure(text=f"+{diff}" if diff > 0 else str(diff))
                    except Exception:
                        pass

                gf_entry.bind("<KeyRelease>", update_gd_label)
                ga_entry.bind("<KeyRelease>", update_gd_label)

                pts_entry = make_num_entry(rf, r.points, 54)

                notes_entry = ctk.CTkEntry(rf, width=150, height=26, fg_color=theme.BG_INPUT, border_color=theme.BORDER_COLOR, placeholder_text="e.g. fair play", font=ctk.CTkFont(size=10))
                if r.override_notes:
                    notes_entry.insert(0, r.override_notes)
                notes_entry.pack(side="left", padx=2)

                def reset_team(tid=r.team_id):
                    self.standings_calc.clear_team_override(tid)
                    populate_editor()

                ctk.CTkButton(
                    rf,
                    text="↺",
                    width=36,
                    height=24,
                    fg_color=theme.BG_CARD,
                    hover_color=theme.BG_CARD_HOVER,
                    border_color=theme.BORDER_COLOR,
                    border_width=1,
                    text_color=theme.TEXT_MUTED,
                    font=ctk.CTkFont(size=11),
                    command=reset_team
                ).pack(side="left", padx=4)

                team_entries[r.team_id] = {
                    "p": p_entry,
                    "w": w_entry,
                    "d": d_entry,
                    "l": l_entry,
                    "gf": gf_entry,
                    "ga": ga_entry,
                    "pts": pts_entry,
                    "notes": notes_entry
                }

        grp_dropdown = ctk.CTkOptionMenu(
            tb,
            variable=selected_grp_var,
            values=group_names,
            width=150,
            fg_color=theme.BG_INPUT,
            command=lambda _: populate_editor()
        )
        grp_dropdown.pack(side="left", padx=(0, 10))

        def reset_current_group():
            sel_g_name = selected_grp_var.get()
            target_g_id = None
            for g in groups:
                if g["name"] == sel_g_name:
                    target_g_id = g["id"]
                    break
            self.standings_calc.clear_group_overrides(group_id=target_g_id)
            populate_editor()
            self.refresh()
            messagebox.showinfo("Reset Complete", f"Manual overrides cleared for {sel_g_name}. Standings restored to match calculations.")

        ctk.CTkButton(
            tb,
            text="↺ Reset Group to Matches",
            fg_color=theme.BG_CARD,
            border_color=theme.BORDER_COLOR,
            border_width=1,
            hover_color=theme.BG_CARD_HOVER,
            text_color=theme.TEXT_MUTED,
            font=ctk.CTkFont(size=11),
            height=28,
            command=reset_current_group
        ).pack(side="left")

        # Bottom Buttons
        bot_bar = ctk.CTkFrame(modal.body_frame, fg_color="transparent")
        bot_bar.pack(fill="x", pady=(8, 0))

        def save_and_auto_reorder():
            try:
                for tid, ents in team_entries.items():
                    p = int(ents["p"].get().strip() or "0")
                    w = int(ents["w"].get().strip() or "0")
                    d = int(ents["d"].get().strip() or "0")
                    l = int(ents["l"].get().strip() or "0")
                    gf = int(ents["gf"].get().strip() or "0")
                    ga = int(ents["ga"].get().strip() or "0")
                    pts = int(ents["pts"].get().strip() or "0")
                    notes = ents["notes"].get().strip()

                    self.standings_calc.set_team_override(
                        team_id=tid,
                        played=p,
                        won=w,
                        drawn=d,
                        lost=l,
                        goals_for=gf,
                        goals_against=ga,
                        points=pts,
                        notes=notes
                    )

                modal.destroy()
                self.refresh()
                messagebox.showinfo(
                    "Points Table Updated",
                    "Changes saved successfully!\nStandings and rankings have reordered automatically based on tie-breakers."
                )
            except Exception as ex:
                messagebox.showerror("Save Failed", f"Failed to save changes: {ex}")

        ctk.CTkButton(
            bot_bar,
            text="💾 Save & Auto-Reorder",
            fg_color=theme.ACCENT_GREEN,
            hover_color=theme.ACCENT_GREEN_HOVER,
            text_color=theme.TEXT_DARK,
            font=ctk.CTkFont(size=12, weight="bold"),
            height=34,
            command=save_and_auto_reorder
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

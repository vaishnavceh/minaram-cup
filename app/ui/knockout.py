"""
Visual knockout bracket view: interactive tournament tree,
match cards, winner indicators, champion crest, and direct score entry.
"""

import customtkinter as ctk
from tkinter import messagebox
from typing import Dict, List, Optional

from app.ui import theme
from app.database import Database
from app.knockout_manager import KnockoutManager
from app.results_manager import ResultsManager


class KnockoutView(ctk.CTkScrollableFrame):
    def __init__(self, parent, db: Database, navigate_callback=None):
        super().__init__(parent, fg_color="transparent")
        self.db = db
        self.navigate = navigate_callback
        self.knockout_mgr = KnockoutManager(db)
        self.results_mgr = ResultsManager(db)

        self.build_ui()

    def refresh(self):
        self.load_bracket_view()

    def build_ui(self):
        # Header
        hdr = ctk.CTkFrame(self, fg_color="transparent")
        hdr.pack(fill="x", padx=16, pady=(12, 12))

        title_box = ctk.CTkFrame(hdr, fg_color="transparent")
        title_box.pack(side="left")
        ctk.CTkLabel(title_box, text="Knockout Stage Bracket", font=ctk.CTkFont(size=20, weight="bold"), text_color=theme.TEXT_PRIMARY).pack(anchor="w")
        ctk.CTkLabel(title_box, text="Visual tournament progression tree from Quarter-Finals to the Minaram Cup Champion", font=ctk.CTkFont(size=11), text_color=theme.TEXT_MUTED).pack(anchor="w")

        # Action Buttons
        btn_box = ctk.CTkFrame(hdr, fg_color="transparent")
        btn_box.pack(side="right")

        ctk.CTkButton(
            btn_box,
            text="⚡ Generate Bracket",
            fg_color=theme.ACCENT_GREEN,
            hover_color=theme.ACCENT_GREEN_HOVER,
            text_color=theme.TEXT_DARK,
            font=ctk.CTkFont(size=12, weight="bold"),
            height=32,
            command=self.handle_generate_bracket
        ).pack(side="left", padx=4)

        # Champion Trophy Banner Container
        self.champ_banner = ctk.CTkFrame(self, fg_color="transparent")
        self.champ_banner.pack(fill="x", padx=16, pady=(0, 14))

        # Bracket Columns Container (Horizontal layout)
        self.bracket_container = ctk.CTkScrollableFrame(self, fg_color="transparent", orientation="horizontal", height=500)
        self.bracket_container.pack(fill="both", expand=True, padx=16, pady=(0, 20))

        self.load_bracket_view()

    def handle_generate_bracket(self):
        # Check if knockout matches already exist
        existing = self.db.execute_one("SELECT COUNT(*) AS c FROM matches WHERE stage IN ('Quarter-Final', 'Semi-Final', 'Final');")["c"]
        if existing > 0:
            if not messagebox.askyesno("Regenerate Bracket", "Knockout matches already exist. Regenerating will replace existing knockout fixtures.\n\nProceed?"):
                return

        try:
            fixtures = self.knockout_mgr.generate_bracket_from_group_qualifiers()
            # Delete old knockout fixtures
            self.db.execute_non_query("DELETE FROM matches WHERE stage IN ('Quarter-Final', 'Semi-Final', 'Final');")
            for f in fixtures:
                self.db.execute_non_query("""
                    INSERT INTO matches (
                        match_number, stage, round_number, bracket_slot,
                        home_team_id, away_team_id, scheduled_date, scheduled_time,
                        venue, status, notes
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 'Scheduled', ?);
                """, (
                    f["match_number"], f["stage"], f["round_number"], f["bracket_slot"],
                    f.get("home_team_id"), f.get("away_team_id"),
                    f.get("scheduled_date", ""), f.get("scheduled_time", ""),
                    f.get("venue", "Minaram Stadium"), f.get("notes", "")
                ))
            messagebox.showinfo("Bracket Ready", f"Generated {len(fixtures)} knockout matches successfully!")
            self.load_bracket_view()
        except Exception as e:
            messagebox.showerror("Bracket Generation Error", str(e))

    def load_bracket_view(self):
        for child in self.bracket_container.winfo_children():
            child.destroy()
        for child in self.champ_banner.winfo_children():
            child.destroy()

        bracket_tree = self.knockout_mgr.get_bracket_structure()

        # Check for Champion in Final match
        final_matches = bracket_tree.get("Final", [])
        if final_matches and final_matches[0].is_completed and final_matches[0].winner_team_name:
            champ_name = final_matches[0].winner_team_name
            c_box = ctk.CTkFrame(self.champ_banner, fg_color=theme.BG_CARD, corner_radius=10, border_color=theme.ACCENT_GREEN, border_width=2)
            c_box.pack(fill="x", pady=(0, 4))

            c_inner = ctk.CTkFrame(c_box, fg_color="transparent")
            c_inner.pack(padx=20, pady=14)

            ctk.CTkLabel(c_inner, text="🏆 MINARAM CUP TOURNAMENT CHAMPION 🏆", font=ctk.CTkFont(size=14, weight="bold"), text_color=theme.ACCENT_GREEN_TEXT).pack()
            ctk.CTkLabel(c_inner, text=champ_name, font=ctk.CTkFont(size=26, weight="bold"), text_color=theme.TEXT_PRIMARY).pack(pady=(4, 2))
            ctk.CTkLabel(c_inner, text=f"Winner of the {self.db.get_setting('tournament_name', 'Minaram Cup')} {self.db.get_setting('edition', '2026')}", font=ctk.CTkFont(size=12), text_color=theme.TEXT_MUTED).pack()

        if not bracket_tree:
            empty_box = ctk.CTkFrame(self.bracket_container, fg_color=theme.BG_CARD, corner_radius=10, border_color=theme.BORDER_COLOR, border_width=1)
            empty_box.pack(fill="both", expand=True, padx=40, pady=40)
            ctk.CTkLabel(
                empty_box,
                text="No knockout bracket matches scheduled.\n\nClick '⚡ Generate Bracket' above to build brackets from group stage qualifiers.",
                font=ctk.CTkFont(size=13),
                text_color=theme.TEXT_MUTED,
                justify="center"
            ).pack(pady=40)
            return

        # Render sequential columns: Quarter-Finals, Semi-Finals, Final
        stages_order = ["Quarter-Final", "Semi-Final", "Final"]
        active_stages = [s for s in stages_order if s in bracket_tree]

        for s_idx, stg in enumerate(active_stages):
            matches_list = bracket_tree[stg]

            # Column Frame
            col_frame = ctk.CTkFrame(self.bracket_container, fg_color="transparent", width=260)
            col_frame.pack(side="left", fill="y", padx=16, pady=6)

            # Stage Title Header
            c_hdr = ctk.CTkFrame(col_frame, fg_color=theme.BG_CARD, corner_radius=6, border_color=theme.BORDER_COLOR, border_width=1)
            c_hdr.pack(fill="x", pady=(0, 16))
            ctk.CTkLabel(c_hdr, text=stg.upper(), font=ctk.CTkFont(size=12, weight="bold"), text_color=theme.ACCENT_GREEN_TEXT).pack(pady=8)

            # Match Boxes
            for m in matches_list:
                m_card = ctk.CTkFrame(col_frame, fg_color=theme.BG_CARD, corner_radius=8, border_color=theme.BORDER_COLOR, border_width=1)
                m_card.pack(fill="x", pady=12)

                # Match Header Info
                m_top = ctk.CTkFrame(m_card, fg_color="transparent")
                m_top.pack(fill="x", padx=10, pady=(8, 4))
                slot_txt = f"{m.bracket_slot}" if m.bracket_slot else f"M#{m.match_number}"
                ctk.CTkLabel(m_top, text=slot_txt, font=ctk.CTkFont(size=10, weight="bold"), text_color=theme.TEXT_MUTED).pack(side="left")

                badge_bg, badge_fg = theme.get_status_colors(m.status)
                ctk.CTkLabel(m_top, text=m.status, font=ctk.CTkFont(size=9, weight="bold"), fg_color=badge_bg, text_color=badge_fg, corner_radius=3, padx=4).pack(side="right")

                # Home Team Row
                h_row = ctk.CTkFrame(m_card, fg_color=theme.BG_INPUT, corner_radius=4)
                h_row.pack(fill="x", padx=10, pady=2)
                h_win = (m.is_completed and m.winner_team_id == m.home_team_id)
                h_name = m.home_team_name if m.home_team_name else (m.notes or "TBD")
                ctk.CTkLabel(h_row, text=h_name, font=ctk.CTkFont(size=11, weight="bold" if h_win else "normal"), text_color=theme.ACCENT_GREEN_TEXT if h_win else theme.TEXT_PRIMARY, anchor="w").pack(side="left", padx=8, pady=4)
                
                h_sc_txt = str(m.home_score) if m.home_score is not None else "-"
                ctk.CTkLabel(h_row, text=h_sc_txt, font=ctk.CTkFont(size=11, weight="bold"), text_color=theme.ACCENT_GREEN_TEXT if h_win else theme.TEXT_MUTED).pack(side="right", padx=8, pady=4)

                # Away Team Row
                a_row = ctk.CTkFrame(m_card, fg_color=theme.BG_INPUT, corner_radius=4)
                a_row.pack(fill="x", padx=10, pady=2)
                a_win = (m.is_completed and m.winner_team_id == m.away_team_id)
                a_name = m.away_team_name if m.away_team_name else (m.notes or "TBD")
                ctk.CTkLabel(a_row, text=a_name, font=ctk.CTkFont(size=11, weight="bold" if a_win else "normal"), text_color=theme.ACCENT_GREEN_TEXT if a_win else theme.TEXT_PRIMARY, anchor="w").pack(side="left", padx=8, pady=4)

                a_sc_txt = str(m.away_score) if m.away_score is not None else "-"
                ctk.CTkLabel(a_row, text=a_sc_txt, font=ctk.CTkFont(size=11, weight="bold"), text_color=theme.ACCENT_GREEN_TEXT if a_win else theme.TEXT_MUTED).pack(side="right", padx=8, pady=4)

                # Penalties info (if draw and shootout occurred)
                if m.home_penalty is not None and m.away_penalty is not None:
                    p_txt = f"Pens: {m.home_penalty} - {m.away_penalty}"
                    ctk.CTkLabel(m_card, text=p_txt, font=ctk.CTkFont(size=9), text_color=theme.TEXT_MUTED).pack(pady=1)

                # Match Date & Action
                b_row = ctk.CTkFrame(m_card, fg_color="transparent")
                b_row.pack(fill="x", padx=10, pady=(4, 8))
                dt_txt = f"{m.scheduled_date} {m.scheduled_time}".strip() or m.venue
                ctk.CTkLabel(b_row, text=dt_txt, font=ctk.CTkFont(size=9), text_color=theme.TEXT_MUTED).pack(side="left")

                # Direct Enter Result Action
                if m.home_team_id and m.away_team_id:
                    btn_txt = "Score" if not m.is_completed else "Edit"
                    ctk.CTkButton(
                        b_row,
                        text=btn_txt,
                        width=44,
                        height=18,
                        fg_color=theme.ACCENT_GREEN if not m.is_completed else "transparent",
                        border_color=theme.BORDER_COLOR,
                        border_width=1 if m.is_completed else 0,
                        hover_color=theme.ACCENT_GREEN_HOVER if not m.is_completed else theme.BG_CARD_HOVER,
                        text_color=theme.TEXT_DARK if not m.is_completed else theme.TEXT_PRIMARY,
                        font=ctk.CTkFont(size=9, weight="bold"),
                        command=lambda match_item=m: self.open_quick_result_modal(match_item)
                    ).pack(side="right")

    def open_quick_result_modal(self, match):
        from app.ui.results import ResultsView
        # If navigate is available, switch to results or launch direct modal
        modal = ctk.CTkToplevel(self)
        modal.title(f"Enter Score — {match.bracket_slot or match.stage}")
        modal.geometry("400x320")
        modal.configure(fg_color=theme.BG_MAIN)
        modal.transient(self)
        modal.grab_set()

        cont = ctk.CTkFrame(modal, fg_color=theme.BG_CARD, corner_radius=10, border_color=theme.BORDER_COLOR, border_width=1)
        cont.pack(fill="both", expand=True, padx=16, pady=16)

        ctk.CTkLabel(cont, text=f"{match.home_team_name} vs {match.away_team_name}", font=ctk.CTkFont(size=14, weight="bold"), text_color=theme.TEXT_PRIMARY).pack(pady=(12, 10))

        # Scores
        sf = ctk.CTkFrame(cont, fg_color="transparent")
        sf.pack(fill="x", padx=16, pady=(0, 10))
        sf.columnconfigure(0, weight=1)
        sf.columnconfigure(1, weight=1)

        he = ctk.CTkEntry(sf, font=ctk.CTkFont(size=18, weight="bold"), justify="center", fg_color=theme.BG_INPUT)
        he.insert(0, str(match.home_score if match.home_score is not None else 0))
        he.grid(row=0, column=0, padx=4)

        ae = ctk.CTkEntry(sf, font=ctk.CTkFont(size=18, weight="bold"), justify="center", fg_color=theme.BG_INPUT)
        ae.insert(0, str(match.away_score if match.away_score is not None else 0))
        ae.grid(row=0, column=1, padx=4)

        # Penalties
        ctk.CTkLabel(cont, text="Penalties (if draw):", font=ctk.CTkFont(size=10), text_color=theme.TEXT_MUTED).pack()
        pf = ctk.CTkFrame(cont, fg_color="transparent")
        pf.pack(fill="x", padx=16, pady=(0, 14))
        pf.columnconfigure(0, weight=1)
        pf.columnconfigure(1, weight=1)

        hpe = ctk.CTkEntry(pf, justify="center", fg_color=theme.BG_INPUT)
        if match.home_penalty is not None:
            hpe.insert(0, str(match.home_penalty))
        hpe.grid(row=0, column=0, padx=4)

        ape = ctk.CTkEntry(pf, justify="center", fg_color=theme.BG_INPUT)
        if match.away_penalty is not None:
            ape.insert(0, str(match.away_penalty))
        ape.grid(row=0, column=1, padx=4)

        def save():
            try:
                hs = int(he.get().strip())
                as_ = int(ae.get().strip())
            except ValueError:
                messagebox.showerror("Error", "Scores must be numbers.")
                return

            hp = int(hpe.get().strip()) if hpe.get().strip() else None
            ap = int(ape.get().strip()) if ape.get().strip() else None

            ok, msg = self.results_mgr.record_result(match.id, hs, as_, home_penalty=hp, away_penalty=ap)
            if not ok:
                messagebox.showerror("Error", msg)
            else:
                modal.destroy()
                self.load_bracket_view()

        ctk.CTkButton(cont, text="Save Score", fg_color=theme.ACCENT_GREEN, hover_color=theme.ACCENT_GREEN_HOVER, text_color=theme.TEXT_DARK, font=ctk.CTkFont(weight="bold"), command=save).pack(fill="x", padx=16)

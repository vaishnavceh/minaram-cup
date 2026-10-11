"""
Reports & Exports interface: 1-click export of registrations, teams,
fixtures, results, standings, and master tournament workbooks in XLSX and CSV.
"""

import customtkinter as ctk
from tkinter import filedialog, messagebox
from pathlib import Path

from app.ui import theme
from app.database import Database
from app.export_service import ExportService


class ReportsView(ctk.CTkScrollableFrame):
    def __init__(self, parent, db: Database):
        super().__init__(parent, fg_color="transparent")
        self.db = db
        self.export_service = ExportService(db)

        self.build_ui()

    def refresh(self):
        self.load_report_cards()

    def build_ui(self):
        # Header
        hdr = ctk.CTkFrame(self, fg_color="transparent")
        hdr.pack(fill="x", padx=16, pady=(12, 12))

        title_box = ctk.CTkFrame(hdr, fg_color="transparent")
        title_box.pack(side="left")
        ctk.CTkLabel(title_box, text="Reports & Data Export Center", font=ctk.CTkFont(size=20, weight="bold"), text_color=theme.TEXT_PRIMARY).pack(anchor="w")
        ctk.CTkLabel(title_box, text="Export live tournament records in professionally formatted Excel (.xlsx) and CSV formats", font=ctk.CTkFont(size=11), text_color=theme.TEXT_MUTED).pack(anchor="w")

        # Container for Cards
        self.cards_container = ctk.CTkFrame(self, fg_color="transparent")
        self.cards_container.pack(fill="both", expand=True, padx=16, pady=(0, 20))

        self.load_report_cards()

    def load_report_cards(self):
        for child in self.cards_container.winfo_children():
            child.destroy()

        # 1. Master Tournament Workbook Banner Card
        master_card = ctk.CTkFrame(self.cards_container, fg_color=theme.BG_CARD, corner_radius=10, border_color=theme.ACCENT_GREEN, border_width=1)
        master_card.pack(fill="x", pady=(0, 16))

        m_inner = ctk.CTkFrame(master_card, fg_color="transparent")
        m_inner.pack(fill="x", padx=16, pady=16)

        m_left = ctk.CTkFrame(m_inner, fg_color="transparent")
        m_left.pack(side="left", fill="both", expand=True)

        ctk.CTkLabel(m_left, text="📊 Complete Tournament Master Report (Excel)", font=ctk.CTkFont(size=15, weight="bold"), text_color=theme.ACCENT_GREEN_TEXT).pack(anchor="w")
        ctk.CTkLabel(
            m_left,
            text="Comprehensive multi-tab Excel workbook containing Tournament Overview, Registered Teams, Groups, Match Fixtures, Completed Results, and Points Tables with pitch-dark headers and frozen panes.",
            font=ctk.CTkFont(size=11),
            text_color=theme.TEXT_SECONDARY,
            wraplength=550,
            justify="left"
        ).pack(anchor="w", pady=(4, 0))

        ctk.CTkButton(
            m_inner,
            text="Export Master Workbook",
            fg_color=theme.ACCENT_GREEN,
            hover_color=theme.ACCENT_GREEN_HOVER,
            text_color=theme.TEXT_DARK,
            font=ctk.CTkFont(size=12, weight="bold"),
            height=36,
            command=self.export_master_workbook
        ).pack(side="right", padx=(16, 0))

        # 2. Individual Export Cards Grid (2 columns)
        grid_frame = ctk.CTkFrame(self.cards_container, fg_color="transparent")
        grid_frame.pack(fill="x")
        grid_frame.columnconfigure(0, weight=1)
        grid_frame.columnconfigure(1, weight=1)

        reports_data = [
            (
                "📥 Registrations Report",
                "Complete list of all participant registrations with contact details, timestamps, and status.",
                self.db.execute_one("SELECT COUNT(*) AS c FROM registrations;")["c"],
                "registrations",
                self.export_service.export_registrations
            ),
            (
                "🛡️ Teams & Contacts",
                "Confirmed teams roster including captain details, contact phone numbers, groups, and seeds.",
                self.db.execute_one("SELECT COUNT(*) AS c FROM teams WHERE status = 'Confirmed';")["c"],
                "teams",
                self.export_service.export_teams
            ),
            (
                "📅 Fixtures Schedule",
                "Full tournament fixtures with dates, times, pitch venues, and home/away team matchups.",
                self.db.execute_one("SELECT COUNT(*) AS c FROM matches;")["c"],
                "fixtures",
                self.export_service.export_fixtures
            ),
            (
                "🏆 Points Table & Standings",
                "Group-by-group points standings with Played, Won, Drawn, Lost, GD, PTS, and qualification tags.",
                self.db.execute_one("SELECT COUNT(*) AS c FROM matches WHERE status IN ('Completed', 'Walkover');")["c"],
                "standings",
                self.export_service.export_standings
            ),
        ]

        for idx, (title, desc, count, file_slug, export_func) in enumerate(reports_data):
            row_idx = idx // 2
            col_idx = idx % 2

            card = ctk.CTkFrame(grid_frame, fg_color=theme.BG_CARD, corner_radius=10, border_color=theme.BORDER_COLOR, border_width=1)
            card.grid(row=row_idx, column=col_idx, padx=6, pady=6, sticky="nsew")

            c_inner = ctk.CTkFrame(card, fg_color="transparent")
            c_inner.pack(fill="both", expand=True, padx=14, pady=14)

            ctk.CTkLabel(c_inner, text=title, font=ctk.CTkFont(size=13, weight="bold"), text_color=theme.TEXT_PRIMARY).pack(anchor="w")
            ctk.CTkLabel(c_inner, text=desc, font=ctk.CTkFont(size=11), text_color=theme.TEXT_MUTED, wraplength=280, justify="left").pack(anchor="w", pady=(4, 6))

            ctk.CTkLabel(c_inner, text=f"Live Database Records: {count}", font=ctk.CTkFont(size=10, weight="bold"), text_color=theme.ACCENT_GREEN_TEXT).pack(anchor="w", pady=(0, 10))

            btn_row = ctk.CTkFrame(c_inner, fg_color="transparent")
            btn_row.pack(fill="x")

            ctk.CTkButton(
                btn_row,
                text="XLSX",
                width=80,
                height=28,
                fg_color=theme.BG_INPUT,
                border_color=theme.BORDER_COLOR,
                border_width=1,
                hover_color=theme.BG_CARD_HOVER,
                text_color=theme.TEXT_PRIMARY,
                command=lambda f=export_func, s=file_slug: self.run_export(f, s, "xlsx")
            ).pack(side="left", padx=(0, 6))

            ctk.CTkButton(
                btn_row,
                text="CSV",
                width=80,
                height=28,
                fg_color=theme.BG_INPUT,
                border_color=theme.BORDER_COLOR,
                border_width=1,
                hover_color=theme.BG_CARD_HOVER,
                text_color=theme.TEXT_PRIMARY,
                command=lambda f=export_func, s=file_slug: self.run_export(f, s, "csv")
            ).pack(side="left")

    def run_export(self, export_func, slug: str, ext: str):
        default_file = f"minaram_{slug}.{ext}"
        f_types = [("Excel Files", "*.xlsx")] if ext == "xlsx" else [("CSV Files", "*.csv")]
        dest = filedialog.asksaveasfilename(defaultextension=f".{ext}", initialfile=default_file, filetypes=f_types)
        if not dest:
            return

        try:
            export_func(Path(dest))
            messagebox.showinfo("Export Successful", f"File saved successfully to:\n{dest}")
        except Exception as e:
            messagebox.showerror("Export Failed", str(e))

    def export_master_workbook(self):
        default_file = "minaram_cup_master_report.xlsx"
        dest = filedialog.asksaveasfilename(defaultextension=".xlsx", initialfile=default_file, filetypes=[("Excel Files", "*.xlsx")])
        if not dest:
            return

        try:
            self.export_service.export_full_tournament_workbook(Path(dest))
            messagebox.showinfo("Master Report Exported", f"Complete tournament workbook generated successfully at:\n{dest}")
        except Exception as e:
            messagebox.showerror("Export Failed", str(e))

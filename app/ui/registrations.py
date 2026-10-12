"""
Registration management interface: paste parsing, validation preview,
bulk import from CSV/Excel, duplicate warnings, and CRUD management.
"""

import gc
import customtkinter as ctk
from tkinter import filedialog, messagebox
from typing import List, Dict, Any, Optional

from app.ui import theme
from app.ui.modal import BaseModal, ConfirmDialog
from app.database import Database
from app.registration_service import RegistrationService
from app.export_service import ExportService


class RegistrationsView(ctk.CTkScrollableFrame):
    def __init__(self, parent, db: Database):
        super().__init__(parent, fg_color="transparent")
        self.db = db
        self.reg_service = RegistrationService(db)
        self.export_service = ExportService(db)

        self.preview_items: List[Dict[str, Any]] = []

        # Filter states
        self.search_var = ctk.StringVar()
        self.status_var = ctk.StringVar(value="All")
        self.sort_var = ctk.StringVar(value="registered_at")

        self.build_ui()

    def refresh(self):
        self.load_table_data()

    def build_ui(self):
        # Header
        hdr = ctk.CTkFrame(self, fg_color="transparent")
        hdr.pack(fill="x", padx=16, pady=(12, 12))

        title_box = ctk.CTkFrame(hdr, fg_color="transparent")
        title_box.pack(side="left")
        ctk.CTkLabel(title_box, text="Registration Center", font=ctk.CTkFont(size=20, weight="bold"), text_color=theme.TEXT_PRIMARY).pack(anchor="w")
        ctk.CTkLabel(title_box, text="Parse WhatsApp/pasted messages, validate duplicates, and manage participant records", font=ctk.CTkFont(size=11), text_color=theme.TEXT_MUTED).pack(anchor="w")

        # Ingestion Card (Paste Box & Controls)
        ingest_card = ctk.CTkFrame(self, fg_color=theme.BG_CARD, corner_radius=10, border_color=theme.BORDER_COLOR, border_width=1)
        ingest_card.pack(fill="x", padx=16, pady=(0, 14))

        ctk.CTkLabel(ingest_card, text="Paste Registration Message(s)", font=ctk.CTkFont(size=13, weight="bold"), text_color=theme.TEXT_PRIMARY).pack(anchor="w", padx=14, pady=(12, 4))
        ctk.CTkLabel(ingest_card, text="Paste one or multiple messages. Supports WhatsApp messages, backslash delimiters ('\\'), and standard format.", font=ctk.CTkFont(size=11), text_color=theme.TEXT_MUTED).pack(anchor="w", padx=14, pady=(0, 8))

        self.paste_textbox = ctk.CTkTextbox(
            ingest_card,
            height=90,
            fg_color=theme.BG_INPUT,
            border_color=theme.BORDER_COLOR,
            border_width=1,
            text_color=theme.TEXT_PRIMARY,
            font=ctk.CTkFont(family="Consolas", size=11)
        )
        self.paste_textbox.pack(fill="x", padx=14, pady=(0, 10))
        sample_placeholder = "Registration Format\nName: Vaishnav\nPhone No: 9746603975\nTeam Name: Binladen Fc"
        self.paste_textbox.insert("1.0", sample_placeholder)

        # Ingest Buttons Bar
        btn_bar = ctk.CTkFrame(ingest_card, fg_color="transparent")
        btn_bar.pack(fill="x", padx=14, pady=(0, 12))

        ctk.CTkButton(
            btn_bar,
            text="⚡ Parse & Preview",
            fg_color=theme.ACCENT_GREEN,
            hover_color=theme.ACCENT_GREEN_HOVER,
            text_color=theme.TEXT_DARK,
            font=ctk.CTkFont(size=12, weight="bold"),
            height=30,
            command=self.handle_parse
        ).pack(side="left", padx=(0, 6))

        self.save_btn = ctk.CTkButton(
            btn_bar,
            text="💾 Save Valid Records",
            fg_color=theme.COLOR_INFO,
            hover_color=theme.COLOR_INFO_MUTED,
            text_color="#FFFFFF",
            font=ctk.CTkFont(size=12, weight="bold"),
            height=30,
            command=self.handle_save_preview
        )
        self.save_btn.pack(side="left", padx=6)

        ctk.CTkButton(
            btn_bar,
            text="Clear",
            fg_color="transparent",
            border_color=theme.BORDER_COLOR,
            border_width=1,
            hover_color=theme.BG_CARD_HOVER,
            text_color=theme.TEXT_SECONDARY,
            height=30,
            width=70,
            command=self.handle_clear_paste
        ).pack(side="left", padx=6)

        # Right side imports
        ctk.CTkButton(
            btn_bar,
            text="+ Add Manual",
            fg_color="transparent",
            border_color=theme.ACCENT_GREEN,
            border_width=1,
            hover_color=theme.BG_CARD_HOVER,
            text_color=theme.ACCENT_GREEN_TEXT,
            height=30,
            command=self.open_add_manual_modal
        ).pack(side="right", padx=(6, 0))

        ctk.CTkButton(
            btn_bar,
            text="📥 Import Excel",
            fg_color=theme.BG_INPUT,
            border_color=theme.BORDER_COLOR,
            border_width=1,
            hover_color=theme.BG_CARD_HOVER,
            text_color=theme.TEXT_PRIMARY,
            height=30,
            command=self.handle_import_xlsx
        ).pack(side="right", padx=6)

        ctk.CTkButton(
            btn_bar,
            text="📥 Import CSV",
            fg_color=theme.BG_INPUT,
            border_color=theme.BORDER_COLOR,
            border_width=1,
            hover_color=theme.BG_CARD_HOVER,
            text_color=theme.TEXT_PRIMARY,
            height=30,
            command=self.handle_import_csv
        ).pack(side="right", padx=6)

        # Preview Container (Only visible when preview items exist)
        self.preview_frame = ctk.CTkFrame(self, fg_color=theme.BG_CARD, corner_radius=10, border_color=theme.BORDER_COLOR, border_width=1)
        # Initially hidden

        # Registrations Database Table Section
        table_card = ctk.CTkFrame(self, fg_color=theme.BG_CARD, corner_radius=10, border_color=theme.BORDER_COLOR, border_width=1)
        table_card.pack(fill="both", expand=True, padx=16, pady=(0, 20))

        # Search & Filter Controls
        filter_bar = ctk.CTkFrame(table_card, fg_color="transparent")
        filter_bar.pack(fill="x", padx=14, pady=12)

        ctk.CTkLabel(filter_bar, text="Search:", font=ctk.CTkFont(size=11), text_color=theme.TEXT_MUTED).pack(side="left", padx=(0, 4))
        self.search_entry = ctk.CTkEntry(
            filter_bar,
            placeholder_text="Name, Phone, or Team...",
            textvariable=self.search_var,
            width=200,
            height=28,
            fg_color=theme.BG_INPUT,
            border_color=theme.BORDER_COLOR
        )
        self.search_entry.pack(side="left", padx=(0, 12))
        self.search_entry.bind("<KeyRelease>", lambda e: self.load_table_data())

        ctk.CTkLabel(filter_bar, text="Status:", font=ctk.CTkFont(size=11), text_color=theme.TEXT_MUTED).pack(side="left", padx=(0, 4))
        self.status_menu = ctk.CTkOptionMenu(
            filter_bar,
            variable=self.status_var,
            values=["All", "Pending", "Confirmed", "Duplicate", "Rejected"],
            width=110,
            height=28,
            fg_color=theme.BG_INPUT,
            button_color=theme.BG_CARD_HOVER,
            command=lambda v: self.load_table_data()
        )
        self.status_menu.pack(side="left", padx=(0, 12))

        ctk.CTkLabel(filter_bar, text="Sort by:", font=ctk.CTkFont(size=11), text_color=theme.TEXT_MUTED).pack(side="left", padx=(0, 4))
        self.sort_menu = ctk.CTkOptionMenu(
            filter_bar,
            variable=self.sort_var,
            values=["registered_at", "participant_name", "team_name", "id"],
            width=130,
            height=28,
            fg_color=theme.BG_INPUT,
            button_color=theme.BG_CARD_HOVER,
            command=lambda v: self.load_table_data()
        )
        self.sort_menu.pack(side="left", padx=(0, 12))

        # Export Buttons
        ctk.CTkButton(
            filter_bar,
            text="📤 Export XLSX",
            width=100,
            height=28,
            fg_color=theme.BG_INPUT,
            border_color=theme.BORDER_COLOR,
            border_width=1,
            hover_color=theme.BG_CARD_HOVER,
            text_color=theme.TEXT_PRIMARY,
            command=lambda: self.handle_export("xlsx")
        ).pack(side="right", padx=(6, 0))

        ctk.CTkButton(
            filter_bar,
            text="📤 Export CSV",
            width=90,
            height=28,
            fg_color=theme.BG_INPUT,
            border_color=theme.BORDER_COLOR,
            border_width=1,
            hover_color=theme.BG_CARD_HOVER,
            text_color=theme.TEXT_PRIMARY,
            command=lambda: self.handle_export("csv")
        ).pack(side="right")

        # Table Header
        self.table_header = ctk.CTkFrame(table_card, fg_color=theme.BG_INPUT, height=32, corner_radius=6)
        self.table_header.pack(fill="x", padx=14, pady=(0, 6))

        col_defs = [
            ("ID", 40),
            ("Participant Name", 140),
            ("Phone Number", 110),
            ("Team Name", 150),
            ("Date Registered", 130),
            ("Status", 90),
            ("Actions", 160)
        ]
        for name, w in col_defs:
            lbl = ctk.CTkLabel(
                self.table_header,
                text=name,
                font=ctk.CTkFont(size=11, weight="bold"),
                text_color=theme.TEXT_SECONDARY,
                width=w,
                anchor="w" if w > 50 else "center"
            )
            lbl.pack(side="left", padx=4)

        # Table Rows Container
        self.rows_container = ctk.CTkFrame(table_card, fg_color="transparent")
        self.rows_container.pack(fill="both", expand=True, padx=14, pady=(0, 14))

        self.load_table_data()

    # ----------------------------------------------------
    # Ingestion & Parsing Handlers
    # ----------------------------------------------------
    def handle_clear_paste(self):
        self.paste_textbox.delete("1.0", "end")
        self.hide_preview()

    def handle_parse(self):
        raw_text = self.paste_textbox.get("1.0", "end").strip()
        if not raw_text:
            messagebox.showinfo("Empty Input", "Please paste one or more registration messages first.")
            return

        self.preview_items = self.reg_service.preview_raw_text(raw_text)
        if not self.preview_items:
            messagebox.showwarning("Parse Warning", "No valid registration patterns could be identified in the pasted text.")
            return

        self.render_preview_panel()

    def render_preview_panel(self):
        for child in self.preview_frame.winfo_children():
            child.destroy()

        self.preview_frame.pack(fill="x", padx=16, pady=(0, 14), before=self.rows_container.master)

        top = ctk.CTkFrame(self.preview_frame, fg_color="transparent")
        top.pack(fill="x", padx=14, pady=(10, 6))

        valid_count = sum(1 for p in self.preview_items if p["is_valid"])
        total = len(self.preview_items)

        ctk.CTkLabel(
            top,
            text=f"Extraction Preview ({valid_count}/{total} Valid Records)",
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color=theme.TEXT_PRIMARY
        ).pack(side="left")

        ctk.CTkButton(
            top,
            text="✕ Hide Preview",
            width=90,
            height=22,
            fg_color="transparent",
            hover_color=theme.BG_CARD_HOVER,
            text_color=theme.TEXT_MUTED,
            font=ctk.CTkFont(size=11),
            command=self.hide_preview
        ).pack(side="right")

        # Preview Items List
        for idx, item in enumerate(self.preview_items, 1):
            row = ctk.CTkFrame(self.preview_frame, fg_color=theme.BG_INPUT, corner_radius=6)
            row.pack(fill="x", padx=14, pady=3)

            # Left Details
            left = ctk.CTkFrame(row, fg_color="transparent")
            left.pack(side="left", padx=10, pady=6)

            name_str = item["name"] or "[Missing Name]"
            phone_str = item["phone"] or "[Missing Phone]"
            team_str = item["team"] or "[Missing Team]"

            ctk.CTkLabel(left, text=f"#{idx}  {name_str}  •  {phone_str}  •  {team_str}", font=ctk.CTkFont(size=12, weight="bold"), text_color=theme.TEXT_PRIMARY if item["is_valid"] else theme.COLOR_DANGER).pack(anchor="w")

            if item["errors"]:
                ctk.CTkLabel(left, text=f"Errors: {', '.join(item['errors'])}", font=ctk.CTkFont(size=10), text_color=theme.COLOR_DANGER).pack(anchor="w")
            if item["warnings"]:
                ctk.CTkLabel(left, text=f"Warnings: {'; '.join(item['warnings'])}", font=ctk.CTkFont(size=10), text_color=theme.COLOR_WARNING).pack(anchor="w")

            # Right Status Badge
            right = ctk.CTkFrame(row, fg_color="transparent")
            right.pack(side="right", padx=10, pady=6)

            dup = item["duplicate_status"]
            if not item["is_valid"]:
                badge_text, badge_color = "Invalid", theme.COLOR_DANGER_MUTED
            elif "Duplicate" in dup:
                badge_text, badge_color = dup, theme.COLOR_WARNING_MUTED
            else:
                badge_text, badge_color = "Valid", theme.ACCENT_GREEN_MUTED

            ctk.CTkLabel(
                right,
                text=badge_text,
                fg_color=badge_color,
                text_color=theme.TEXT_PRIMARY,
                corner_radius=4,
                font=ctk.CTkFont(size=10, weight="bold"),
                padx=8,
                pady=2
            ).pack()

    def hide_preview(self):
        self.preview_items = []
        self.preview_frame.pack_forget()

    def handle_save_preview(self):
        if not self.preview_items:
            messagebox.showinfo("No Preview", "Please parse and preview registrations first.")
            return

        valid_items = [p for p in self.preview_items if p["is_valid"]]
        if not valid_items:
            messagebox.showerror("No Valid Items", "None of the extracted items are valid. Fix errors and try again.")
            return

        saved_count, errors = self.reg_service.save_parsed_registrations(valid_items)
        msg = f"Successfully saved {saved_count} registrations to database!"
        if errors:
            msg += f"\n\nWarnings/Errors:\n" + "\n".join(errors[:5])

        messagebox.showinfo("Saved", msg)
        self.hide_preview()
        self.paste_textbox.delete("1.0", "end")
        self.load_table_data()

    # ----------------------------------------------------
    # Table Loading & Search
    # ----------------------------------------------------
    def load_table_data(self):
        for child in self.rows_container.winfo_children():
            child.destroy()

        search = self.search_var.get().strip()
        status = self.status_var.get()
        sort_by = self.sort_var.get()

        registrations = self.reg_service.get_registrations(search=search, status=status, sort_by=sort_by)

        if not registrations:
            empty_box = ctk.CTkFrame(self.rows_container, fg_color="transparent")
            empty_box.pack(fill="x", pady=30)
            ctk.CTkLabel(empty_box, text="No registrations found matching criteria.", font=ctk.CTkFont(size=13), text_color=theme.TEXT_MUTED).pack()
            return

        for idx, reg in enumerate(registrations):
            bg_col = theme.BG_INPUT if idx % 2 == 0 else theme.BG_ROW_ALT
            row = ctk.CTkFrame(self.rows_container, fg_color=bg_col, height=36, corner_radius=4)
            row.pack(fill="x", pady=2)

            # Columns
            ctk.CTkLabel(row, text=str(reg.id), width=40, font=theme.get_font(11), text_color=theme.TEXT_MUTED).pack(side="left", padx=4)
            ctk.CTkLabel(row, text=reg.participant_name, width=140, font=theme.get_font(11, "bold"), text_color=theme.TEXT_PRIMARY, anchor="w").pack(side="left", padx=4)
            ctk.CTkLabel(row, text=reg.phone_number, width=110, font=theme.get_font(11), text_color=theme.TEXT_SECONDARY, anchor="w").pack(side="left", padx=4)
            ctk.CTkLabel(row, text=reg.team_name, width=150, font=theme.get_font(11), text_color=theme.TEXT_PRIMARY, anchor="w").pack(side="left", padx=4)
            
            # Short date
            d_short = reg.registered_at.split(" ")[0] if " " in reg.registered_at else reg.registered_at
            ctk.CTkLabel(row, text=d_short, width=130, font=theme.get_font(11), text_color=theme.TEXT_MUTED, anchor="w").pack(side="left", padx=4)

            # Badge
            badge_bg, badge_fg = theme.get_status_colors(reg.status)
            ctk.CTkLabel(
                row,
                text=reg.status,
                fg_color=badge_bg,
                text_color=badge_fg,
                corner_radius=4,
                font=theme.get_font(10, "bold"),
                width=80,
                height=22
            ).pack(side="left", padx=4)

            # Action Buttons
            act_frame = ctk.CTkFrame(row, fg_color="transparent", width=160)
            act_frame.pack(side="left", padx=4)

            if reg.status != "Confirmed":
                ctk.CTkButton(
                    act_frame,
                    text="Confirm",
                    width=54,
                    height=22,
                    fg_color=theme.ACCENT_GREEN,
                    hover_color=theme.ACCENT_GREEN_HOVER,
                    text_color=theme.TEXT_DARK,
                    font=theme.get_font(10, "bold"),
                    command=lambda r_id=reg.id: self.handle_confirm_reg(r_id)
                ).pack(side="left", padx=2)

            ctk.CTkButton(
                act_frame,
                text="Edit",
                width=42,
                height=22,
                fg_color="transparent",
                border_color=theme.BORDER_COLOR,
                border_width=1,
                hover_color=theme.BG_CARD_HOVER,
                text_color=theme.TEXT_PRIMARY,
                font=theme.get_font(10),
                command=lambda r=reg: self.open_edit_modal(r)
            ).pack(side="left", padx=2)

            ctk.CTkButton(
                act_frame,
                text="✕",
                width=24,
                height=22,
                fg_color="transparent",
                hover_color=theme.COLOR_DANGER_MUTED,
                text_color=theme.COLOR_DANGER,
                font=theme.get_font(11, "bold"),
                command=lambda r=reg: self.handle_delete_reg(r)
            ).pack(side="left", padx=2)

        gc.collect()

    # ----------------------------------------------------
    # CRUD Modal Actions
    # ----------------------------------------------------
    def handle_confirm_reg(self, reg_id: int):
        try:
            team_id = self.reg_service.confirm_and_create_team(reg_id)
            messagebox.showinfo("Confirmed", f"Registration confirmed and assigned to Team ID #{team_id}!")
            self.load_table_data()
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def handle_delete_reg(self, reg):
        ConfirmDialog(
            self,
            title="Delete Registration",
            message=f"Are you sure you want to delete registration #{reg.id} ({reg.participant_name} - {reg.team_name})?\nThis action cannot be undone.",
            confirm_text="Delete",
            is_danger=True,
            on_confirm=lambda: self._execute_delete_reg(reg.id)
        )

    def _execute_delete_reg(self, reg_id: int):
        self.reg_service.delete_registration(reg_id)
        self.load_table_data()

    def open_add_manual_modal(self):
        modal = BaseModal(self, title="Add Registration Manually", width=450, height=380)

        # Fields
        ctk.CTkLabel(modal.body_frame, text="Participant Name:", font=ctk.CTkFont(size=11), text_color=theme.TEXT_SECONDARY).pack(anchor="w", pady=(4, 2))
        name_entry = ctk.CTkEntry(modal.body_frame, fg_color=theme.BG_INPUT, border_color=theme.BORDER_COLOR)
        name_entry.pack(fill="x", pady=(0, 6))

        ctk.CTkLabel(modal.body_frame, text="Phone Number:", font=ctk.CTkFont(size=11), text_color=theme.TEXT_SECONDARY).pack(anchor="w", pady=(4, 2))
        phone_entry = ctk.CTkEntry(modal.body_frame, fg_color=theme.BG_INPUT, border_color=theme.BORDER_COLOR)
        phone_entry.pack(fill="x", pady=(0, 6))

        ctk.CTkLabel(modal.body_frame, text="Team Name:", font=ctk.CTkFont(size=11), text_color=theme.TEXT_SECONDARY).pack(anchor="w", pady=(4, 2))
        team_entry = ctk.CTkEntry(modal.body_frame, fg_color=theme.BG_INPUT, border_color=theme.BORDER_COLOR)
        team_entry.pack(fill="x", pady=(0, 6))

        ctk.CTkLabel(modal.body_frame, text="Status:", font=ctk.CTkFont(size=11), text_color=theme.TEXT_SECONDARY).pack(anchor="w", pady=(4, 2))
        status_menu = ctk.CTkOptionMenu(modal.body_frame, values=["Pending", "Confirmed", "Duplicate", "Rejected"], fg_color=theme.BG_INPUT)
        status_menu.pack(fill="x", pady=(0, 12))

        def save():
            n = name_entry.get().strip()
            p = phone_entry.get().strip()
            t = team_entry.get().strip()
            if not n or not p or not t:
                messagebox.showerror("Missing Fields", "Please enter Name, Phone Number, and Team Name.")
                return
            self.reg_service.add_registration_manual(n, p, t, status=status_menu.get())
            modal.destroy()
            self.load_table_data()

        ctk.CTkButton(modal.body_frame, text="Save Registration", fg_color=theme.ACCENT_GREEN, hover_color=theme.ACCENT_GREEN_HOVER, text_color=theme.TEXT_DARK, font=ctk.CTkFont(weight="bold"), command=save).pack(fill="x", pady=(6, 0))

    def open_edit_modal(self, reg):
        modal = BaseModal(self, title=f"Edit Registration #{reg.id}", width=450, height=420)

        ctk.CTkLabel(modal.body_frame, text="Participant Name:", font=ctk.CTkFont(size=11), text_color=theme.TEXT_SECONDARY).pack(anchor="w", pady=(4, 2))
        name_entry = ctk.CTkEntry(modal.body_frame, fg_color=theme.BG_INPUT, border_color=theme.BORDER_COLOR)
        name_entry.insert(0, reg.participant_name)
        name_entry.pack(fill="x", pady=(0, 6))

        ctk.CTkLabel(modal.body_frame, text="Phone Number:", font=ctk.CTkFont(size=11), text_color=theme.TEXT_SECONDARY).pack(anchor="w", pady=(4, 2))
        phone_entry = ctk.CTkEntry(modal.body_frame, fg_color=theme.BG_INPUT, border_color=theme.BORDER_COLOR)
        phone_entry.insert(0, reg.phone_number)
        phone_entry.pack(fill="x", pady=(0, 6))

        ctk.CTkLabel(modal.body_frame, text="Team Name:", font=ctk.CTkFont(size=11), text_color=theme.TEXT_SECONDARY).pack(anchor="w", pady=(4, 2))
        team_entry = ctk.CTkEntry(modal.body_frame, fg_color=theme.BG_INPUT, border_color=theme.BORDER_COLOR)
        team_entry.insert(0, reg.team_name)
        team_entry.pack(fill="x", pady=(0, 6))

        ctk.CTkLabel(modal.body_frame, text="Status:", font=ctk.CTkFont(size=11), text_color=theme.TEXT_SECONDARY).pack(anchor="w", pady=(4, 2))
        status_menu = ctk.CTkOptionMenu(modal.body_frame, values=["Pending", "Confirmed", "Duplicate", "Rejected"], fg_color=theme.BG_INPUT)
        status_menu.set(reg.status)
        status_menu.pack(fill="x", pady=(0, 6))

        ctk.CTkLabel(modal.body_frame, text="Notes:", font=ctk.CTkFont(size=11), text_color=theme.TEXT_SECONDARY).pack(anchor="w", pady=(4, 2))
        notes_entry = ctk.CTkEntry(modal.body_frame, fg_color=theme.BG_INPUT, border_color=theme.BORDER_COLOR)
        notes_entry.insert(0, reg.notes)
        notes_entry.pack(fill="x", pady=(0, 12))

        def save():
            n = name_entry.get().strip()
            p = phone_entry.get().strip()
            t = team_entry.get().strip()
            if not n or not p or not t:
                messagebox.showerror("Missing Fields", "Please enter Name, Phone Number, and Team Name.")
                return
            self.reg_service.update_registration(reg.id, n, p, t, status=status_menu.get(), notes=notes_entry.get())
            modal.destroy()
            self.load_table_data()

        ctk.CTkButton(modal.body_frame, text="Update Record", fg_color=theme.ACCENT_GREEN, hover_color=theme.ACCENT_GREEN_HOVER, text_color=theme.TEXT_DARK, font=ctk.CTkFont(weight="bold"), command=save).pack(fill="x", pady=(6, 0))

    # ----------------------------------------------------
    # Imports & Exports
    # ----------------------------------------------------
    def handle_import_csv(self):
        f = filedialog.askopenfilename(filetypes=[("CSV files", "*.csv"), ("All files", "*.*")])
        if not f:
            return
        count, errors = self.reg_service.import_from_csv(f)
        msg = f"Imported {count} records from CSV."
        if errors:
            msg += "\n\nErrors/Warnings:\n" + "\n".join(errors[:5])
        messagebox.showinfo("CSV Import", msg)
        self.load_table_data()

    def handle_import_xlsx(self):
        f = filedialog.askopenfilename(filetypes=[("Excel files", "*.xlsx"), ("All files", "*.*")])
        if not f:
            return
        count, errors = self.reg_service.import_from_xlsx(f)
        msg = f"Imported {count} records from Excel."
        if errors:
            msg += "\n\nErrors/Warnings:\n" + "\n".join(errors[:5])
        messagebox.showinfo("Excel Import", msg)
        self.load_table_data()

    def handle_export(self, file_type: str):
        default_name = f"minaram_registrations.{file_type}"
        file_filter = ("Excel Files", "*.xlsx") if file_type == "xlsx" else ("CSV Files", "*.csv")
        dest = filedialog.asksaveasfilename(defaultextension=f".{file_type}", initialfile=default_name, filetypes=[file_filter])
        if not dest:
            return
        try:
            status_filter = self.status_var.get()
            self.export_service.export_registrations(dest, status_filter=status_filter)
            messagebox.showinfo("Export Successful", f"Registrations exported successfully to:\n{dest}")
        except Exception as e:
            messagebox.showerror("Export Failed", str(e))

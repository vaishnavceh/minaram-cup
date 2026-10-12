"""
Team management interface: team CRUD, duplicate merging, group assignments,
match history viewer, and performance metrics.
"""

import gc
import customtkinter as ctk
from tkinter import filedialog, messagebox
from typing import List, Optional

from app.ui import theme
from app.ui.modal import BaseModal, ConfirmDialog
from app.database import Database
from app.team_manager import TeamManager
from app.export_service import ExportService


class TeamsView(ctk.CTkScrollableFrame):
    def __init__(self, parent, db: Database):
        super().__init__(parent, fg_color="transparent")
        self.db = db
        self.team_mgr = TeamManager(db)
        self.export_service = ExportService(db)

        self.search_var = ctk.StringVar()
        self.group_filter_var = ctk.StringVar(value="All Groups")
        self.status_filter_var = ctk.StringVar(value="All")
        self._search_timer = None

        self.build_ui()

    def _on_search_key(self, event=None):
        if getattr(self, "_search_timer", None) is not None:
            try:
                self.after_cancel(self._search_timer)
            except Exception:
                pass
        self._search_timer = self.after(250, self.load_teams_table)

    def refresh(self):
        self.update_group_filter_options()
        self.load_teams_table()

    def build_ui(self):
        # Header
        hdr = ctk.CTkFrame(self, fg_color="transparent")
        hdr.pack(fill="x", padx=16, pady=(12, 12))

        title_box = ctk.CTkFrame(hdr, fg_color="transparent")
        title_box.pack(side="left")
        ctk.CTkLabel(title_box, text="Team Administration", font=ctk.CTkFont(size=20, weight="bold"), text_color=theme.TEXT_PRIMARY).pack(anchor="w")
        ctk.CTkLabel(title_box, text="Manage tournament clubs, seeds, match histories, and duplicate team records", font=ctk.CTkFont(size=11), text_color=theme.TEXT_MUTED).pack(anchor="w")

        # Action Buttons
        btn_box = ctk.CTkFrame(hdr, fg_color="transparent")
        btn_box.pack(side="right")

        ctk.CTkButton(
            btn_box,
            text="+ Create Team",
            fg_color=theme.ACCENT_GREEN,
            hover_color=theme.ACCENT_GREEN_HOVER,
            text_color=theme.TEXT_DARK,
            font=ctk.CTkFont(size=12, weight="bold"),
            height=32,
            command=self.open_create_team_modal
        ).pack(side="left", padx=4)

        ctk.CTkButton(
            btn_box,
            text="🔀 Merge Teams",
            fg_color=theme.BG_CARD,
            border_color=theme.BORDER_COLOR,
            border_width=1,
            hover_color=theme.BG_CARD_HOVER,
            text_color=theme.TEXT_PRIMARY,
            height=32,
            command=self.open_merge_modal
        ).pack(side="left", padx=4)

        ctk.CTkButton(
            btn_box,
            text="📤 Export Teams",
            fg_color=theme.BG_CARD,
            border_color=theme.BORDER_COLOR,
            border_width=1,
            hover_color=theme.BG_CARD_HOVER,
            text_color=theme.TEXT_PRIMARY,
            height=32,
            command=self.handle_export
        ).pack(side="left", padx=4)

        # Filters Card
        filter_card = ctk.CTkFrame(self, fg_color=theme.BG_CARD, corner_radius=10, border_color=theme.BORDER_COLOR, border_width=1)
        filter_card.pack(fill="x", padx=16, pady=(0, 14))

        f_bar = ctk.CTkFrame(filter_card, fg_color="transparent")
        f_bar.pack(fill="x", padx=14, pady=10)

        ctk.CTkLabel(f_bar, text="Search:", font=ctk.CTkFont(size=11), text_color=theme.TEXT_MUTED).pack(side="left", padx=(0, 4))
        self.search_entry = ctk.CTkEntry(
            f_bar,
            placeholder_text="Team name or captain...",
            textvariable=self.search_var,
            width=200,
            height=28,
            fg_color=theme.BG_INPUT,
            border_color=theme.BORDER_COLOR
        )
        self.search_entry.pack(side="left", padx=(0, 12))
        self.search_entry.bind("<KeyRelease>", self._on_search_key)

        ctk.CTkLabel(f_bar, text="Group:", font=ctk.CTkFont(size=11), text_color=theme.TEXT_MUTED).pack(side="left", padx=(0, 4))
        self.group_menu = ctk.CTkOptionMenu(
            f_bar,
            variable=self.group_filter_var,
            values=["All Groups"],
            width=130,
            height=28,
            fg_color=theme.BG_INPUT,
            command=lambda v: self.load_teams_table()
        )
        self.group_menu.pack(side="left", padx=(0, 12))

        ctk.CTkLabel(f_bar, text="Status:", font=ctk.CTkFont(size=11), text_color=theme.TEXT_MUTED).pack(side="left", padx=(0, 4))
        self.status_menu = ctk.CTkOptionMenu(
            f_bar,
            variable=self.status_filter_var,
            values=["All", "Confirmed", "Pending", "Withdrawn"],
            width=110,
            height=28,
            fg_color=theme.BG_INPUT,
            command=lambda v: self.load_teams_table()
        )
        self.status_menu.pack(side="left")

        # Teams Table Section
        self.table_card = ctk.CTkFrame(self, fg_color=theme.BG_CARD, corner_radius=10, border_color=theme.BORDER_COLOR, border_width=1)
        self.table_card.pack(fill="both", expand=True, padx=16, pady=(0, 20))

        # Table Header
        self.header_frame = ctk.CTkFrame(self.table_card, fg_color=theme.BG_INPUT, height=32, corner_radius=6)
        self.header_frame.pack(fill="x", padx=14, pady=10)

        cols = [
            ("ID", 40),
            ("Team Name", 160),
            ("Captain / Contact", 150),
            ("Group", 90),
            ("Seed", 50),
            ("P", 30),
            ("W", 30),
            ("D", 30),
            ("L", 30),
            ("GD", 40),
            ("PTS", 40),
            ("Actions", 160)
        ]
        for name, w in cols:
            ctk.CTkLabel(
                self.header_frame,
                text=name,
                font=ctk.CTkFont(size=11, weight="bold"),
                text_color=theme.TEXT_SECONDARY,
                width=w,
                anchor="w" if w > 60 else "center"
            ).pack(side="left", padx=3)

        self.rows_container = ctk.CTkFrame(self.table_card, fg_color="transparent")
        self.rows_container.pack(fill="both", expand=True, padx=14, pady=(0, 14))

        self.update_group_filter_options()
        self.load_teams_table()

    def update_group_filter_options(self):
        groups = self.db.execute_query("SELECT id, name FROM groups ORDER BY display_order ASC, name ASC;")
        vals = ["All Groups", "Unassigned"] + [g["name"] for g in groups]
        self.group_menu.configure(values=vals)

    def load_teams_table(self):
        for child in self.rows_container.winfo_children():
            child.destroy()

        search = self.search_var.get().strip()
        g_val = self.group_filter_var.get()
        group_id = None
        if g_val == "Unassigned":
            group_id = -1
        elif g_val != "All Groups":
            g_row = self.db.execute_one("SELECT id FROM groups WHERE name = ?;", (g_val,))
            if g_row:
                group_id = g_row["id"]

        status = self.status_filter_var.get()
        teams = self.team_mgr.get_teams(search=search, group_id=group_id, status=status)

        if not teams:
            empty_box = ctk.CTkFrame(self.rows_container, fg_color="transparent")
            empty_box.pack(fill="x", pady=30)
            ctk.CTkLabel(empty_box, text="No teams found matching search.", font=ctk.CTkFont(size=13), text_color=theme.TEXT_MUTED).pack()
            return

        for idx, t in enumerate(teams):
            bg_col = theme.BG_INPUT if idx % 2 == 0 else theme.BG_ROW_ALT
            row = ctk.CTkFrame(self.rows_container, fg_color=bg_col, height=36, corner_radius=4)
            row.pack(fill="x", pady=2)

            stats = self.team_mgr.get_team_stats(t.id)

            ctk.CTkLabel(row, text=str(t.id), width=40, font=theme.get_font(11), text_color=theme.TEXT_MUTED).pack(side="left", padx=3)
            ctk.CTkLabel(row, text=t.name, width=160, font=theme.get_font(11, "bold"), text_color=theme.TEXT_PRIMARY, anchor="w").pack(side="left", padx=3)

            contact_str = f"{t.captain_name} ({t.phone_number})" if t.phone_number else t.captain_name or "-"
            ctk.CTkLabel(row, text=contact_str, width=150, font=theme.get_font(11), text_color=theme.TEXT_SECONDARY, anchor="w").pack(side="left", padx=3)

            grp_name = t.group_name or "None"
            ctk.CTkLabel(row, text=grp_name, width=90, font=theme.get_font(11), text_color=theme.TEXT_MUTED, anchor="w").pack(side="left", padx=3)

            ctk.CTkLabel(row, text=f"#{t.seed}" if t.seed > 0 else "-", width=50, font=theme.get_font(11), text_color=theme.COLOR_INFO).pack(side="left", padx=3)

            # Record stats
            ctk.CTkLabel(row, text=str(stats["played"]), width=30, font=theme.get_font(11), text_color=theme.TEXT_SECONDARY).pack(side="left", padx=3)
            ctk.CTkLabel(row, text=str(stats["won"]), width=30, font=theme.get_font(11), text_color=theme.ACCENT_GREEN_TEXT).pack(side="left", padx=3)
            ctk.CTkLabel(row, text=str(stats["drawn"]), width=30, font=theme.get_font(11), text_color=theme.TEXT_SECONDARY).pack(side="left", padx=3)
            ctk.CTkLabel(row, text=str(stats["lost"]), width=30, font=theme.get_font(11), text_color=theme.COLOR_DANGER).pack(side="left", padx=3)

            gd_s = f"+{stats['goal_difference']}" if stats["goal_difference"] > 0 else str(stats["goal_difference"])
            ctk.CTkLabel(row, text=gd_s, width=40, font=theme.get_font(11), text_color=theme.TEXT_SECONDARY).pack(side="left", padx=3)
            ctk.CTkLabel(row, text=str(stats["points"]), width=40, font=theme.get_font(11, "bold"), text_color=theme.ACCENT_GREEN_TEXT).pack(side="left", padx=3)

            # Action Buttons
            act_frame = ctk.CTkFrame(row, fg_color="transparent", width=160)
            act_frame.pack(side="left", padx=3)

            ctk.CTkButton(
                act_frame,
                text="History",
                width=50,
                height=22,
                fg_color=theme.BG_CARD,
                border_color=theme.BORDER_COLOR,
                border_width=1,
                hover_color=theme.BG_CARD_HOVER,
                text_color=theme.TEXT_PRIMARY,
                font=theme.get_font(10),
                command=lambda team=t: self.open_history_modal(team)
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
                command=lambda team=t: self.open_edit_team_modal(team)
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
                command=lambda team=t: self.handle_delete_team(team)
            ).pack(side="left", padx=2)

        gc.collect()

    # ----------------------------------------------------
    # Modals & Actions
    # ----------------------------------------------------
    def open_history_modal(self, team):
        modal = BaseModal(self, title=f"Match History — {team.name}", width=550, height=450)

        stats = self.team_mgr.get_team_stats(team.id)
        stat_bar = ctk.CTkFrame(modal.body_frame, fg_color=theme.BG_INPUT, corner_radius=6)
        stat_bar.pack(fill="x", pady=(0, 12))

        txt = f"Played: {stats['played']}  •  Won: {stats['won']}  •  Drawn: {stats['drawn']}  •  Lost: {stats['lost']}  •  GF: {stats['goals_for']}  •  GA: {stats['goals_against']}  •  PTS: {stats['points']}"
        ctk.CTkLabel(stat_bar, text=txt, font=ctk.CTkFont(size=11, weight="bold"), text_color=theme.ACCENT_GREEN_TEXT).pack(pady=8)

        scroll = ctk.CTkScrollableFrame(modal.body_frame, fg_color="transparent", height=280)
        scroll.pack(fill="both", expand=True)

        history = self.team_mgr.get_team_match_history(team.id)
        if not history:
            ctk.CTkLabel(scroll, text="No matches recorded or scheduled for this team.", font=ctk.CTkFont(size=12), text_color=theme.TEXT_MUTED).pack(pady=20)
            return

        for m in history:
            box = ctk.CTkFrame(scroll, fg_color=theme.BG_INPUT, corner_radius=6)
            box.pack(fill="x", pady=3)

            left = ctk.CTkFrame(box, fg_color="transparent")
            left.pack(side="left", padx=10, pady=6)

            side_tag = "Home" if m["is_home"] else "Away"
            ctk.CTkLabel(left, text=f"vs {m['opponent']} ({side_tag})", font=ctk.CTkFont(size=12, weight="bold"), text_color=theme.TEXT_PRIMARY).pack(anchor="w")
            ctk.CTkLabel(left, text=f"Match #{m['match_number']} • {m['stage']} • {m['date']} {m['time']}", font=ctk.CTkFont(size=10), text_color=theme.TEXT_MUTED).pack(anchor="w")

            right = ctk.CTkFrame(box, fg_color="transparent")
            right.pack(side="right", padx=10, pady=6)

            if m["outcome"] == "Win":
                col = theme.ACCENT_GREEN_TEXT
            elif m["outcome"] == "Loss":
                col = theme.COLOR_DANGER
            else:
                col = theme.TEXT_MUTED

            sc_display = f"{m['team_score']} - {m['opp_score']}" if m["team_score"] is not None else "vs"
            ctk.CTkLabel(right, text=sc_display, font=ctk.CTkFont(size=13, weight="bold"), text_color=col).pack(anchor="e")
            ctk.CTkLabel(right, text=m["outcome"], font=ctk.CTkFont(size=10, weight="bold"), text_color=col).pack(anchor="e")

    def open_create_team_modal(self):
        modal = BaseModal(self, title="Create New Team", width=460, height=440)

        groups = self.db.execute_query("SELECT id, name FROM groups ORDER BY display_order ASC;")
        group_map = {g["name"]: g["id"] for g in groups}
        group_options = ["None"] + list(group_map.keys())

        ctk.CTkLabel(modal.body_frame, text="Team Name *:", font=ctk.CTkFont(size=11), text_color=theme.TEXT_SECONDARY).pack(anchor="w", pady=(2, 2))
        name_entry = ctk.CTkEntry(modal.body_frame, fg_color=theme.BG_INPUT, border_color=theme.BORDER_COLOR)
        name_entry.pack(fill="x", pady=(0, 6))

        ctk.CTkLabel(modal.body_frame, text="Captain Name:", font=ctk.CTkFont(size=11), text_color=theme.TEXT_SECONDARY).pack(anchor="w", pady=(2, 2))
        cap_entry = ctk.CTkEntry(modal.body_frame, fg_color=theme.BG_INPUT, border_color=theme.BORDER_COLOR)
        cap_entry.pack(fill="x", pady=(0, 6))

        ctk.CTkLabel(modal.body_frame, text="Contact Phone:", font=ctk.CTkFont(size=11), text_color=theme.TEXT_SECONDARY).pack(anchor="w", pady=(2, 2))
        phone_entry = ctk.CTkEntry(modal.body_frame, fg_color=theme.BG_INPUT, border_color=theme.BORDER_COLOR)
        phone_entry.pack(fill="x", pady=(0, 6))

        row2 = ctk.CTkFrame(modal.body_frame, fg_color="transparent")
        row2.pack(fill="x", pady=(0, 6))
        row2.columnconfigure(0, weight=1)
        row2.columnconfigure(1, weight=1)

        g_box = ctk.CTkFrame(row2, fg_color="transparent")
        g_box.grid(row=0, column=0, sticky="ew", padx=(0, 4))
        ctk.CTkLabel(g_box, text="Group Assignment:", font=ctk.CTkFont(size=11), text_color=theme.TEXT_SECONDARY).pack(anchor="w")
        grp_menu = ctk.CTkOptionMenu(g_box, values=group_options, fg_color=theme.BG_INPUT)
        grp_menu.pack(fill="x")

        s_box = ctk.CTkFrame(row2, fg_color="transparent")
        s_box.grid(row=0, column=1, sticky="ew", padx=(4, 0))
        ctk.CTkLabel(s_box, text="Seed / Rank (0=None):", font=ctk.CTkFont(size=11), text_color=theme.TEXT_SECONDARY).pack(anchor="w")
        seed_entry = ctk.CTkEntry(s_box, fg_color=theme.BG_INPUT, border_color=theme.BORDER_COLOR)
        seed_entry.insert(0, "0")
        seed_entry.pack(fill="x")

        ctk.CTkLabel(modal.body_frame, text="Notes:", font=ctk.CTkFont(size=11), text_color=theme.TEXT_SECONDARY).pack(anchor="w", pady=(2, 2))
        notes_entry = ctk.CTkEntry(modal.body_frame, fg_color=theme.BG_INPUT, border_color=theme.BORDER_COLOR)
        notes_entry.pack(fill="x", pady=(0, 12))

        def save():
            n = name_entry.get().strip()
            if not n:
                messagebox.showerror("Validation", "Team name cannot be empty.")
                return
            g_sel = grp_menu.get()
            g_id = group_map.get(g_sel) if g_sel != "None" else None
            try:
                sd = int(seed_entry.get().strip() or "0")
            except ValueError:
                sd = 0

            try:
                self.team_mgr.create_team(
                    name=n,
                    captain_name=cap_entry.get().strip(),
                    phone_number=phone_entry.get().strip(),
                    group_id=g_id,
                    seed=sd,
                    notes=notes_entry.get().strip()
                )
                modal.destroy()
                self.load_teams_table()
            except Exception as e:
                messagebox.showerror("Error", str(e))

        ctk.CTkButton(modal.body_frame, text="Create Team", fg_color=theme.ACCENT_GREEN, hover_color=theme.ACCENT_GREEN_HOVER, text_color=theme.TEXT_DARK, font=ctk.CTkFont(weight="bold"), command=save).pack(fill="x", pady=(4, 0))

    def open_edit_team_modal(self, team):
        modal = BaseModal(self, title=f"Edit Team — {team.name}", width=460, height=440)

        groups = self.db.execute_query("SELECT id, name FROM groups ORDER BY display_order ASC;")
        group_map = {g["name"]: g["id"] for g in groups}
        group_options = ["None"] + list(group_map.keys())

        ctk.CTkLabel(modal.body_frame, text="Team Name *:", font=ctk.CTkFont(size=11), text_color=theme.TEXT_SECONDARY).pack(anchor="w", pady=(2, 2))
        name_entry = ctk.CTkEntry(modal.body_frame, fg_color=theme.BG_INPUT, border_color=theme.BORDER_COLOR)
        name_entry.insert(0, team.name)
        name_entry.pack(fill="x", pady=(0, 6))

        ctk.CTkLabel(modal.body_frame, text="Captain Name:", font=ctk.CTkFont(size=11), text_color=theme.TEXT_SECONDARY).pack(anchor="w", pady=(2, 2))
        cap_entry = ctk.CTkEntry(modal.body_frame, fg_color=theme.BG_INPUT, border_color=theme.BORDER_COLOR)
        cap_entry.insert(0, team.captain_name)
        cap_entry.pack(fill="x", pady=(0, 6))

        ctk.CTkLabel(modal.body_frame, text="Contact Phone:", font=ctk.CTkFont(size=11), text_color=theme.TEXT_SECONDARY).pack(anchor="w", pady=(2, 2))
        phone_entry = ctk.CTkEntry(modal.body_frame, fg_color=theme.BG_INPUT, border_color=theme.BORDER_COLOR)
        phone_entry.insert(0, team.phone_number)
        phone_entry.pack(fill="x", pady=(0, 6))

        row2 = ctk.CTkFrame(modal.body_frame, fg_color="transparent")
        row2.pack(fill="x", pady=(0, 6))
        row2.columnconfigure(0, weight=1)
        row2.columnconfigure(1, weight=1)

        g_box = ctk.CTkFrame(row2, fg_color="transparent")
        g_box.grid(row=0, column=0, sticky="ew", padx=(0, 4))
        ctk.CTkLabel(g_box, text="Group Assignment:", font=ctk.CTkFont(size=11), text_color=theme.TEXT_SECONDARY).pack(anchor="w")
        grp_menu = ctk.CTkOptionMenu(g_box, values=group_options, fg_color=theme.BG_INPUT)
        grp_menu.set(team.group_name if team.group_name in group_options else "None")
        grp_menu.pack(fill="x")

        s_box = ctk.CTkFrame(row2, fg_color="transparent")
        s_box.grid(row=0, column=1, sticky="ew", padx=(4, 0))
        ctk.CTkLabel(s_box, text="Seed / Rank:", font=ctk.CTkFont(size=11), text_color=theme.TEXT_SECONDARY).pack(anchor="w")
        seed_entry = ctk.CTkEntry(s_box, fg_color=theme.BG_INPUT, border_color=theme.BORDER_COLOR)
        seed_entry.insert(0, str(team.seed))
        seed_entry.pack(fill="x")

        ctk.CTkLabel(modal.body_frame, text="Notes:", font=ctk.CTkFont(size=11), text_color=theme.TEXT_SECONDARY).pack(anchor="w", pady=(2, 2))
        notes_entry = ctk.CTkEntry(modal.body_frame, fg_color=theme.BG_INPUT, border_color=theme.BORDER_COLOR)
        notes_entry.insert(0, team.notes)
        notes_entry.pack(fill="x", pady=(0, 12))

        def save():
            n = name_entry.get().strip()
            if not n:
                messagebox.showerror("Validation", "Team name cannot be empty.")
                return
            g_sel = grp_menu.get()
            g_id = group_map.get(g_sel) if g_sel != "None" else None
            try:
                sd = int(seed_entry.get().strip() or "0")
            except ValueError:
                sd = 0

            try:
                self.team_mgr.update_team(
                    team_id=team.id,
                    name=n,
                    captain_name=cap_entry.get().strip(),
                    phone_number=phone_entry.get().strip(),
                    group_id=g_id,
                    seed=sd,
                    notes=notes_entry.get().strip()
                )
                modal.destroy()
                self.load_teams_table()
            except Exception as e:
                messagebox.showerror("Error", str(e))

        ctk.CTkButton(modal.body_frame, text="Update Team", fg_color=theme.ACCENT_GREEN, hover_color=theme.ACCENT_GREEN_HOVER, text_color=theme.TEXT_DARK, font=ctk.CTkFont(weight="bold"), command=save).pack(fill="x", pady=(4, 0))

    def handle_delete_team(self, team):
        # First verify if team has matches
        m_cnt = self.db.execute_one("SELECT COUNT(*) AS c FROM matches WHERE home_team_id = ? OR away_team_id = ?;", (team.id, team.id))["c"]
        if m_cnt > 0:
            messagebox.showwarning(
                "Cannot Delete",
                f"Team '{team.name}' has {m_cnt} scheduled or completed matches.\nTo preserve tournament integrity, you must remove or reschedule those matches first, or use Merge Teams."
            )
            return

        ConfirmDialog(
            self,
            title="Delete Team",
            message=f"Are you sure you want to delete '{team.name}'?\nThis will remove the team and unlink any associated registration records.",
            confirm_text="Delete",
            is_danger=True,
            on_confirm=lambda: self._execute_delete_team(team.id)
        )

    def _execute_delete_team(self, team_id: int):
        ok, msg = self.team_mgr.delete_team(team_id)
        if not ok:
            messagebox.showerror("Error", msg)
        else:
            self.load_teams_table()

    def open_merge_modal(self):
        teams = self.team_mgr.get_teams()
        if len(teams) < 2:
            messagebox.showinfo("Merge Teams", "Need at least 2 teams to perform a merge.")
            return

        modal = BaseModal(self, title="Merge Duplicate Teams", width=480, height=340)

        ctk.CTkLabel(
            modal.body_frame,
            text="Merge a duplicate team into a primary team.\nAll match references and registrations from the duplicate team will be transferred to the target team, and the duplicate will be deleted.",
            font=ctk.CTkFont(size=11),
            text_color=theme.TEXT_MUTED,
            wraplength=440,
            justify="left"
        ).pack(fill="x", pady=(0, 12))

        team_names = [f"{t.name} (ID #{t.id})" for t in teams]
        team_id_map = {f"{t.name} (ID #{t.id})": t.id for t in teams}

        ctk.CTkLabel(modal.body_frame, text="Select Duplicate Team to Remove (Source):", font=ctk.CTkFont(size=11), text_color=theme.TEXT_SECONDARY).pack(anchor="w", pady=(2, 2))
        src_menu = ctk.CTkOptionMenu(modal.body_frame, values=team_names, fg_color=theme.BG_INPUT)
        src_menu.pack(fill="x", pady=(0, 10))

        ctk.CTkLabel(modal.body_frame, text="Select Primary Team to Keep (Target):", font=ctk.CTkFont(size=11), text_color=theme.TEXT_SECONDARY).pack(anchor="w", pady=(2, 2))
        tgt_menu = ctk.CTkOptionMenu(modal.body_frame, values=team_names, fg_color=theme.BG_INPUT)
        tgt_menu.pack(fill="x", pady=(0, 16))

        def do_merge():
            s_name = src_menu.get()
            t_name = tgt_menu.get()
            src_id = team_id_map.get(s_name)
            tgt_id = team_id_map.get(t_name)

            if src_id == tgt_id:
                messagebox.showerror("Merge Error", "Source and Target team cannot be the same.")
                return

            ConfirmDialog(
                modal,
                title="Confirm Team Merge",
                message=f"Are you sure you want to merge '{s_name}' into '{t_name}'?\nThis will reassign all matches and registrations and permanently delete the source team.",
                confirm_text="Execute Merge",
                is_danger=True,
                on_confirm=lambda: self._execute_merge(src_id, tgt_id, modal)
            )

        ctk.CTkButton(modal.body_frame, text="Proceed with Merge", fg_color=theme.COLOR_WARNING, hover_color=theme.COLOR_WARNING_MUTED, text_color=theme.TEXT_DARK, font=ctk.CTkFont(weight="bold"), command=do_merge).pack(fill="x")

    def _execute_merge(self, src_id, tgt_id, modal):
        ok, msg = self.team_mgr.merge_teams(src_id, tgt_id)
        if ok:
            messagebox.showinfo("Merge Complete", msg)
            modal.destroy()
            self.load_teams_table()
        else:
            messagebox.showerror("Merge Failed", msg)

    def handle_export(self):
        dest = filedialog.asksaveasfilename(
            defaultextension=".xlsx",
            initialfile="minaram_teams.xlsx",
            filetypes=[("Excel Files", "*.xlsx"), ("CSV Files", "*.csv")]
        )
        if not dest:
            return
        try:
            self.export_service.export_teams(dest)
            messagebox.showinfo("Export Complete", f"Teams exported successfully to:\n{dest}")
        except Exception as e:
            messagebox.showerror("Export Failed", str(e))

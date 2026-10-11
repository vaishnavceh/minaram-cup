"""
Group administration interface: group creation, manual assignment,
automatic distribution, seeded randomization with live preview, and conflict warnings.
"""

import customtkinter as ctk
from tkinter import messagebox
from typing import Dict, List, Any

from app.ui import theme
from app.ui.modal import BaseModal, ConfirmDialog
from app.database import Database
from app.tournament_manager import TournamentManager


class GroupsView(ctk.CTkScrollableFrame):
    def __init__(self, parent, db: Database):
        super().__init__(parent, fg_color="transparent")
        self.db = db
        self.tourn_mgr = TournamentManager(db)

        self.build_ui()

    def refresh(self):
        self.load_groups_view()

    def build_ui(self):
        # Header
        hdr = ctk.CTkFrame(self, fg_color="transparent")
        hdr.pack(fill="x", padx=16, pady=(12, 12))

        title_box = ctk.CTkFrame(hdr, fg_color="transparent")
        title_box.pack(side="left")
        ctk.CTkLabel(title_box, text="Group Stage Management", font=ctk.CTkFont(size=20, weight="bold"), text_color=theme.TEXT_PRIMARY).pack(anchor="w")
        ctk.CTkLabel(title_box, text="Organize teams into groups, seed allocations, and run fair randomized draws", font=ctk.CTkFont(size=11), text_color=theme.TEXT_MUTED).pack(anchor="w")

        # Action Buttons
        btn_box = ctk.CTkFrame(hdr, fg_color="transparent")
        btn_box.pack(side="right")

        ctk.CTkButton(
            btn_box,
            text="+ Add Group",
            fg_color=theme.BG_CARD,
            border_color=theme.BORDER_COLOR,
            border_width=1,
            hover_color=theme.BG_CARD_HOVER,
            text_color=theme.TEXT_PRIMARY,
            height=32,
            command=self.open_add_group_modal
        ).pack(side="left", padx=4)

        ctk.CTkButton(
            btn_box,
            text="⚡ Auto Distribute",
            fg_color=theme.BG_CARD,
            border_color=theme.ACCENT_GREEN,
            border_width=1,
            hover_color=theme.BG_CARD_HOVER,
            text_color=theme.ACCENT_GREEN_TEXT,
            height=32,
            command=lambda: self.open_distribution_preview(randomize=False)
        ).pack(side="left", padx=4)

        ctk.CTkButton(
            btn_box,
            text="🎲 Randomize Draw",
            fg_color=theme.ACCENT_GREEN,
            hover_color=theme.ACCENT_GREEN_HOVER,
            text_color=theme.TEXT_DARK,
            font=ctk.CTkFont(size=12, weight="bold"),
            height=32,
            command=lambda: self.open_distribution_preview(randomize=True)
        ).pack(side="left", padx=4)

        # Warning Banner (if fixtures exist)
        self.warn_banner = ctk.CTkFrame(self, fg_color=theme.COLOR_WARNING_MUTED, corner_radius=8, border_color=theme.COLOR_WARNING, border_width=1)
        self.warn_label = ctk.CTkLabel(
            self.warn_banner,
            text="⚠️ Warning: Fixtures or match results exist for this tournament. Modifying groups now may invalidate tournament schedules.",
            font=ctk.CTkFont(size=11, weight="bold"),
            text_color="#FDE68A"
        )
        self.warn_label.pack(padx=14, pady=8)

        # Content Container (Groups Cards Grid & Unassigned Pool)
        self.content_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.content_frame.pack(fill="both", expand=True, padx=16, pady=(0, 20))

        self.load_groups_view()

    def check_warning_status(self):
        has_conflicts, f_cnt, r_cnt = self.tourn_mgr.check_existing_fixtures_or_results()
        if has_conflicts:
            self.warn_banner.pack(fill="x", padx=16, pady=(0, 14), before=self.content_frame)
            self.warn_label.configure(
                text=f"⚠️ Caution: {f_cnt} fixtures ({r_cnt} completed) currently exist. Changing group assignments will alter tournament progression!"
            )
        else:
            self.warn_banner.pack_forget()

    def load_groups_view(self):
        self.check_warning_status()

        for child in self.content_frame.winfo_children():
            child.destroy()

        groups = self.tourn_mgr.get_groups()
        unassigned_teams = self.tourn_mgr.get_unassigned_teams()

        if not groups:
            empty_box = ctk.CTkFrame(self.content_frame, fg_color=theme.BG_CARD, corner_radius=10, border_color=theme.BORDER_COLOR, border_width=1)
            empty_box.pack(fill="x", pady=20)
            ctk.CTkLabel(empty_box, text="No groups created yet. Click '+ Add Group' to create Group A, Group B, etc.", font=ctk.CTkFont(size=13), text_color=theme.TEXT_MUTED).pack(pady=24)
            return

        # Top section: Groups Grid
        grid_frame = ctk.CTkFrame(self.content_frame, fg_color="transparent")
        grid_frame.pack(fill="x", pady=(0, 16))

        # Max 3 columns per row
        cols_count = min(3, len(groups))
        for col_i in range(cols_count):
            grid_frame.columnconfigure(col_i, weight=1)

        for idx, g in enumerate(groups):
            row_i = idx // cols_count
            col_i = idx % cols_count

            card = ctk.CTkFrame(grid_frame, fg_color=theme.BG_CARD, corner_radius=10, border_color=theme.BORDER_COLOR, border_width=1)
            card.grid(row=row_i, column=col_i, padx=6, pady=6, sticky="nsew")

            # Group Card Header
            c_hdr = ctk.CTkFrame(card, fg_color="transparent")
            c_hdr.pack(fill="x", padx=14, pady=(12, 8))

            ctk.CTkLabel(c_hdr, text=g.name, font=ctk.CTkFont(size=14, weight="bold"), text_color=theme.TEXT_PRIMARY).pack(side="left")
            
            # Action icons
            act_box = ctk.CTkFrame(c_hdr, fg_color="transparent")
            act_box.pack(side="right")

            ctk.CTkButton(
                act_box,
                text="✎",
                width=24,
                height=22,
                fg_color="transparent",
                hover_color=theme.BG_CARD_HOVER,
                text_color=theme.TEXT_SECONDARY,
                font=ctk.CTkFont(size=12),
                command=lambda grp=g: self.open_rename_group_modal(grp)
            ).pack(side="left", padx=2)

            ctk.CTkButton(
                act_box,
                text="✕",
                width=24,
                height=22,
                fg_color="transparent",
                hover_color=theme.COLOR_DANGER_MUTED,
                text_color=theme.COLOR_DANGER,
                font=ctk.CTkFont(size=12, weight="bold"),
                command=lambda grp=g: self.handle_delete_group(grp)
            ).pack(side="left", padx=2)

            # Assigned Teams List
            teams_in_grp = self.tourn_mgr.get_group_teams(g.id)
            ctk.CTkLabel(card, text=f"{len(teams_in_grp)} teams assigned", font=ctk.CTkFont(size=10), text_color=theme.TEXT_MUTED).pack(anchor="w", padx=14, pady=(0, 6))

            teams_list_box = ctk.CTkFrame(card, fg_color="transparent")
            teams_list_box.pack(fill="both", expand=True, padx=12, pady=(0, 10))

            if not teams_in_grp:
                ctk.CTkLabel(teams_list_box, text="No teams in this group.", font=ctk.CTkFont(size=11), text_color=theme.TEXT_MUTED).pack(pady=12)
            else:
                for t in teams_in_grp:
                    t_row = ctk.CTkFrame(teams_list_box, fg_color=theme.BG_INPUT, corner_radius=6)
                    t_row.pack(fill="x", pady=2)

                    t_name_box = ctk.CTkFrame(t_row, fg_color="transparent")
                    t_name_box.pack(side="left", padx=8, pady=6)

                    seed_badge = f"[Seed {t.seed}] " if t.seed > 0 else ""
                    ctk.CTkLabel(t_name_box, text=f"{seed_badge}{t.name}", font=ctk.CTkFont(size=11, weight="bold"), text_color=theme.TEXT_PRIMARY).pack(anchor="w")

                    # Remove from group button
                    ctk.CTkButton(
                        t_row,
                        text="✕",
                        width=20,
                        height=20,
                        fg_color="transparent",
                        hover_color=theme.COLOR_DANGER_MUTED,
                        text_color=theme.TEXT_MUTED,
                        font=ctk.CTkFont(size=10),
                        command=lambda team_id=t.id: self.unassign_team(team_id)
                    ).pack(side="right", padx=6)

            # Quick Assign Dropdown at bottom of card
            if unassigned_teams:
                assign_bar = ctk.CTkFrame(card, fg_color="transparent")
                assign_bar.pack(fill="x", padx=12, pady=(4, 12))

                opt_names = [t.name for t in unassigned_teams]
                opt_map = {t.name: t.id for t in unassigned_teams}
                sel_var = ctk.StringVar(value="Add Team...")

                def on_select(choice, grp_id=g.id, mapping=opt_map):
                    if choice in mapping:
                        self.tourn_mgr.assign_team_to_group(mapping[choice], grp_id)
                        self.load_groups_view()

                opt_menu = ctk.CTkOptionMenu(
                    assign_bar,
                    variable=sel_var,
                    values=["Add Team..."] + opt_names,
                    height=26,
                    fg_color=theme.BG_INPUT,
                    command=on_select
                )
                opt_menu.pack(fill="x")

        # Bottom section: Unassigned Teams Pool
        pool_card = ctk.CTkFrame(self.content_frame, fg_color=theme.BG_CARD, corner_radius=10, border_color=theme.BORDER_COLOR, border_width=1)
        pool_card.pack(fill="x", pady=(0, 16))

        p_hdr = ctk.CTkFrame(pool_card, fg_color="transparent")
        p_hdr.pack(fill="x", padx=14, pady=(12, 6))
        ctk.CTkLabel(p_hdr, text=f"Unassigned Teams Pool ({len(unassigned_teams)} Teams)", font=ctk.CTkFont(size=13, weight="bold"), text_color=theme.TEXT_PRIMARY).pack(side="left")

        if not unassigned_teams:
            ctk.CTkLabel(pool_card, text="All confirmed teams have been assigned to groups.", font=ctk.CTkFont(size=11), text_color=theme.ACCENT_GREEN_TEXT).pack(padx=14, pady=(0, 14), anchor="w")
        else:
            chips_frame = ctk.CTkFrame(pool_card, fg_color="transparent")
            chips_frame.pack(fill="x", padx=14, pady=(0, 14))

            # Display chips
            for t in unassigned_teams:
                chip = ctk.CTkFrame(chips_frame, fg_color=theme.BG_INPUT, corner_radius=6)
                chip.pack(side="left", padx=4, pady=4)
                ctk.CTkLabel(chip, text=t.name, font=ctk.CTkFont(size=11), text_color=theme.TEXT_PRIMARY).pack(side="left", padx=8, pady=4)

    # ----------------------------------------------------
    # Distribution Preview & Randomize Dialog
    # ----------------------------------------------------
    def open_distribution_preview(self, randomize: bool = False):
        has_conflicts, _, _ = self.tourn_mgr.check_existing_fixtures_or_results()
        if has_conflicts:
            if not messagebox.askyesno(
                "Fixtures Exist",
                "Fixtures already exist for this tournament. Re-distributing groups will modify the team structure.\n\nAre you sure you want to proceed?"
            ):
                return

        try:
            alloc = self.tourn_mgr.preview_team_distribution(randomize=randomize, seed_aware=True)
        except Exception as e:
            messagebox.showerror("Cannot Distribute", str(e))
            return

        mode_title = "Randomized Draw Preview" if randomize else "Auto Distribution Preview"
        modal = BaseModal(self, title=mode_title, width=540, height=480)

        ctk.CTkLabel(
            modal.body_frame,
            text="Review the proposed group assignments below. Click 'Apply Draw' to confirm.",
            font=ctk.CTkFont(size=11),
            text_color=theme.TEXT_MUTED
        ).pack(anchor="w", pady=(0, 10))

        scroll = ctk.CTkScrollableFrame(modal.body_frame, fg_color="transparent", height=300)
        scroll.pack(fill="both", expand=True)

        for g_name, team_list in alloc.items():
            g_box = ctk.CTkFrame(scroll, fg_color=theme.BG_INPUT, corner_radius=6)
            g_box.pack(fill="x", pady=4)

            ctk.CTkLabel(g_box, text=f"{g_name} ({len(team_list)} teams)", font=ctk.CTkFont(size=12, weight="bold"), text_color=theme.ACCENT_GREEN_TEXT).pack(anchor="w", padx=10, pady=(6, 2))

            for t in team_list:
                s_txt = f"[Seed {t['seed']}] " if t["seed"] > 0 else ""
                ctk.CTkLabel(g_box, text=f"• {s_txt}{t['name']}", font=ctk.CTkFont(size=11), text_color=theme.TEXT_PRIMARY).pack(anchor="w", padx=18, pady=1)

        # Action Buttons
        act_row = ctk.CTkFrame(modal.body_frame, fg_color="transparent")
        act_row.pack(fill="x", pady=(12, 0))

        def apply_draw():
            self.tourn_mgr.apply_group_allocation(alloc)
            modal.destroy()
            messagebox.showinfo("Success", "Group allocations applied successfully!")
            self.load_groups_view()

        ctk.CTkButton(
            act_row,
            text="Apply Allocation",
            fg_color=theme.ACCENT_GREEN,
            hover_color=theme.ACCENT_GREEN_HOVER,
            text_color=theme.TEXT_DARK,
            font=ctk.CTkFont(weight="bold"),
            command=apply_draw
        ).pack(side="right")

        if randomize:
            ctk.CTkButton(
                act_row,
                text="🎲 Re-roll",
                fg_color=theme.BG_CARD,
                border_color=theme.BORDER_COLOR,
                border_width=1,
                hover_color=theme.BG_CARD_HOVER,
                text_color=theme.TEXT_PRIMARY,
                command=lambda: [modal.destroy(), self.open_distribution_preview(randomize=True)]
            ).pack(side="right", padx=8)

        ctk.CTkButton(
            act_row,
            text="Cancel",
            fg_color="transparent",
            border_color=theme.BORDER_COLOR,
            border_width=1,
            hover_color=theme.BG_CARD_HOVER,
            text_color=theme.TEXT_PRIMARY,
            command=modal.destroy
        ).pack(side="left")

    # ----------------------------------------------------
    # CRUD Handlers
    # ----------------------------------------------------
    def unassign_team(self, team_id: int):
        self.tourn_mgr.assign_team_to_group(team_id, None)
        self.load_groups_view()

    def open_add_group_modal(self):
        modal = BaseModal(self, title="Add New Group", width=380, height=220)

        ctk.CTkLabel(modal.body_frame, text="Group Name (e.g. Group C):", font=ctk.CTkFont(size=11), text_color=theme.TEXT_SECONDARY).pack(anchor="w", pady=(8, 4))
        name_entry = ctk.CTkEntry(modal.body_frame, fg_color=theme.BG_INPUT, border_color=theme.BORDER_COLOR)
        name_entry.pack(fill="x", pady=(0, 16))

        def save():
            n = name_entry.get().strip()
            if not n:
                messagebox.showerror("Error", "Group name cannot be empty.")
                return
            try:
                self.tourn_mgr.create_group(n)
                modal.destroy()
                self.load_groups_view()
            except Exception as e:
                messagebox.showerror("Error", str(e))

        ctk.CTkButton(modal.body_frame, text="Create Group", fg_color=theme.ACCENT_GREEN, hover_color=theme.ACCENT_GREEN_HOVER, text_color=theme.TEXT_DARK, font=ctk.CTkFont(weight="bold"), command=save).pack(fill="x")

    def open_rename_group_modal(self, grp):
        modal = BaseModal(self, title=f"Rename {grp.name}", width=380, height=220)

        ctk.CTkLabel(modal.body_frame, text="New Group Name:", font=ctk.CTkFont(size=11), text_color=theme.TEXT_SECONDARY).pack(anchor="w", pady=(8, 4))
        name_entry = ctk.CTkEntry(modal.body_frame, fg_color=theme.BG_INPUT, border_color=theme.BORDER_COLOR)
        name_entry.insert(0, grp.name)
        name_entry.pack(fill="x", pady=(0, 16))

        def save():
            n = name_entry.get().strip()
            if not n:
                messagebox.showerror("Error", "Group name cannot be empty.")
                return
            try:
                self.tourn_mgr.rename_group(grp.id, n)
                modal.destroy()
                self.load_groups_view()
            except Exception as e:
                messagebox.showerror("Error", str(e))

        ctk.CTkButton(modal.body_frame, text="Rename", fg_color=theme.ACCENT_GREEN, hover_color=theme.ACCENT_GREEN_HOVER, text_color=theme.TEXT_DARK, font=ctk.CTkFont(weight="bold"), command=save).pack(fill="x")

    def handle_delete_group(self, grp):
        ConfirmDialog(
            self,
            title=f"Delete {grp.name}",
            message=f"Are you sure you want to delete {grp.name}?\nAll teams currently in this group will be moved to the unassigned pool.",
            confirm_text="Delete Group",
            is_danger=True,
            on_confirm=lambda: self._execute_delete_group(grp.id)
        )

    def _execute_delete_group(self, group_id: int):
        ok, msg = self.tourn_mgr.delete_group(group_id)
        if not ok:
            messagebox.showerror("Error", msg)
        else:
            self.load_groups_view()

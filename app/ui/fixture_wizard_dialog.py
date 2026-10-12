"""
MINARAM CUP — Fixture Generation Wizard Modal Dialog.
Clean, modern, and robust interface for generating tournament fixtures,
matchweek timeline spacing, parallel pitch scheduling, and knockout brackets.
Includes auto-calculated timeline end date and dynamic additional matchweek controls.
"""

from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Callable
import customtkinter as ctk
from tkinter import messagebox

from app.ui import theme
from app.ui.modal import BaseModal
from app.database import Database
from app.fixture_generator import FixtureGenerator
from app.knockout_manager import KnockoutManager


class FixtureWizardModal(BaseModal):
    def __init__(self, parent, db: Database, on_saved: Optional[Callable[[], None]] = None):
        super().__init__(parent, title="⚡ Fixture Generation Wizard", width=740, height=750)
        self.resizable(True, True)
        self.minsize(660, 600)

        self.db = db
        self.fixture_gen = FixtureGenerator(db)
        self.knockout_mgr = KnockoutManager(db)
        self.on_saved = on_saved

        self.base_matchweeks: int = 3
        self.extra_matchweeks: int = 0
        self.generated_fixtures: List[Dict[str, Any]] = []
        self.mw_options: List[str] = []

        self.build_ui()

    def _get_real_total_matchweeks(self, fmt: str) -> int:
        """Query real base matchweek count from the database for the given format."""
        try:
            return self.fixture_gen.get_total_matchweeks(fmt, double_round=("Double" in fmt)) or 3
        except Exception:
            return 3

    def get_total_effective_matchweeks(self) -> int:
        """Returns the total matchweeks including user-added additional matchweeks."""
        return max(1, self.base_matchweeks + self.extra_matchweeks)

    def build_ui(self):
        # ----------------------------------------------------
        # Pinned Bottom Footer Bar (Always visible)
        # ----------------------------------------------------
        self.footer_bar = ctk.CTkFrame(
            self.body_frame,
            fg_color=theme.BG_CARD,
            height=54,
            corner_radius=8,
            border_color=theme.BORDER_COLOR,
            border_width=1
        )
        self.footer_bar.pack(side="bottom", fill="x", pady=(8, 0))
        self.footer_bar.pack_propagate(False)

        # Footer Left: Status & Preview Button
        f_left = ctk.CTkFrame(self.footer_bar, fg_color="transparent")
        f_left.pack(side="left", padx=12, pady=8)

        self.preview_btn = ctk.CTkButton(
            f_left,
            text="👁️ Preview Schedule",
            fg_color="#0284c7",
            hover_color="#0369a1",
            text_color="#FFFFFF",
            font=theme.get_font(12, "bold"),
            height=34,
            command=self.run_preview
        )
        self.preview_btn.pack(side="left", padx=(0, 10))

        self.status_lbl = ctk.CTkLabel(
            f_left,
            text="Ready to preview schedule",
            font=theme.get_font(11),
            text_color=theme.TEXT_MUTED
        )
        self.status_lbl.pack(side="left")

        # Footer Right: Cancel & Save Buttons
        f_right = ctk.CTkFrame(self.footer_bar, fg_color="transparent")
        f_right.pack(side="right", padx=12, pady=8)

        self.cancel_btn = ctk.CTkButton(
            f_right,
            text="Cancel",
            fg_color="transparent",
            hover_color=theme.BG_CARD_HOVER,
            text_color=theme.TEXT_SECONDARY,
            height=34,
            command=self.destroy
        )
        self.cancel_btn.pack(side="left", padx=(0, 8))

        self.save_btn = ctk.CTkButton(
            f_right,
            text="⚡ Confirm & Save Fixtures",
            fg_color=theme.ACCENT_GREEN,
            hover_color=theme.ACCENT_GREEN_HOVER,
            text_color=theme.TEXT_DARK,
            font=theme.get_font(12, "bold"),
            height=34,
            command=self.run_save
        )
        self.save_btn.pack(side="left")

        # ----------------------------------------------------
        # Scrollable Configuration Form
        # ----------------------------------------------------
        self.scroll_content = ctk.CTkScrollableFrame(self.body_frame, fg_color="transparent")
        self.scroll_content.pack(side="top", fill="both", expand=True, pady=(0, 4))

        # Prediction Summary Banner (Computed from live database)
        self.pred_banner = ctk.CTkFrame(
            self.scroll_content,
            fg_color=theme.BG_CARD,
            corner_radius=8,
            border_color="#0284c7",
            border_width=1
        )
        self.pred_banner.pack(fill="x", pady=(0, 10))

        self.pred_banner_lbl = ctk.CTkLabel(
            self.pred_banner,
            text="📊 Loading tournament prediction...",
            font=theme.get_font(11, "bold"),
            text_color="#38bdf8",
            wraplength=640,
            justify="left"
        )
        self.pred_banner_lbl.pack(anchor="w", padx=12, pady=8)

        # 1. Tournament Format
        ctk.CTkLabel(
            self.scroll_content,
            text="1. Tournament Competition Format:",
            font=theme.get_font(12, "bold"),
            text_color=theme.TEXT_PRIMARY
        ).pack(anchor="w", pady=(0, 4))

        self.format_menu = ctk.CTkOptionMenu(
            self.scroll_content,
            values=[
                "Group Stage (Round Robin within Groups)",
                "League (Single Round Robin - All vs All)",
                "League (Double Round Robin - Home & Away)",
                "Knockout Bracket (From Group Qualifiers)"
            ],
            fg_color=theme.BG_INPUT,
            button_color=theme.BORDER_COLOR,
            button_hover_color=theme.BG_CARD_HOVER,
            font=theme.get_font(11),
            command=self.on_format_changed
        )
        self.format_menu.pack(fill="x", pady=(0, 10))

        # 2. Matchweek Scope & Additional Matchweeks Management Card
        mw_card = ctk.CTkFrame(
            self.scroll_content,
            fg_color=theme.BG_INPUT,
            corner_radius=8,
            border_color=theme.BORDER_COLOR,
            border_width=1
        )
        mw_card.pack(fill="x", pady=(0, 10))

        mw_card_inner = ctk.CTkFrame(mw_card, fg_color="transparent")
        mw_card_inner.pack(fill="x", padx=14, pady=10)

        # Top row: title & additional matchweek stepper controls
        mw_hdr_row = ctk.CTkFrame(mw_card_inner, fg_color="transparent")
        mw_hdr_row.pack(fill="x")

        ctk.CTkLabel(
            mw_hdr_row,
            text="2. Matchweek Scope & Schedule Rounds:",
            font=theme.get_font(11, "bold"),
            text_color=theme.TEXT_PRIMARY
        ).pack(side="left")

        # Additional Matchweek controls on the right
        mw_stepper_frame = ctk.CTkFrame(mw_hdr_row, fg_color="transparent")
        mw_stepper_frame.pack(side="right")

        self.add_mw_btn = ctk.CTkButton(
            mw_stepper_frame,
            text="+ Add Matchweek",
            font=theme.get_font(10, "bold"),
            fg_color="#0284c7",
            hover_color="#0369a1",
            text_color="#FFFFFF",
            width=110,
            height=26,
            command=self.add_matchweek
        )
        self.add_mw_btn.pack(side="left", padx=(0, 4))

        self.remove_mw_btn = ctk.CTkButton(
            mw_stepper_frame,
            text="- Remove",
            font=theme.get_font(10),
            fg_color=theme.BG_CARD,
            border_color=theme.BORDER_COLOR,
            border_width=1,
            hover_color=theme.BG_CARD_HOVER,
            text_color=theme.TEXT_MUTED,
            width=70,
            height=26,
            command=self.remove_matchweek
        )
        self.remove_mw_btn.pack(side="left")

        # Matchweek dropdown menu
        self.base_matchweeks = self._get_real_total_matchweeks("Group Stage")
        tot_mw = self.get_total_effective_matchweeks()
        self.mw_options = [f"All Matchweeks (Full Schedule - {tot_mw} Rounds)"] + [
            f"Matchweek {i} (Round {i}) Only" for i in range(1, tot_mw + 1)
        ]

        self.matchweek_menu = ctk.CTkOptionMenu(
            mw_card_inner,
            values=self.mw_options,
            fg_color=theme.BG_CARD,
            button_color=theme.BORDER_COLOR,
            button_hover_color=theme.BG_CARD_HOVER,
            text_color=theme.TEXT_PRIMARY,
            font=theme.get_font(11),
            command=self.on_matchweek_changed
        )
        self.matchweek_menu.pack(fill="x", pady=(8, 4))

        self.mw_info_lbl = ctk.CTkLabel(
            mw_card_inner,
            text="",
            font=theme.get_font(10),
            text_color=theme.TEXT_MUTED
        )
        self.mw_info_lbl.pack(anchor="w")

        # 3. Tournament Timeline & Matchweek Interval
        ctk.CTkLabel(
            self.scroll_content,
            text="3. Tournament Timeline & Matchweek Interval:",
            font=theme.get_font(12, "bold"),
            text_color=theme.TEXT_PRIMARY
        ).pack(anchor="w", pady=(4, 4))

        timeline_grid = ctk.CTkFrame(self.scroll_content, fg_color="transparent")
        timeline_grid.pack(fill="x", pady=(0, 4))
        timeline_grid.columnconfigure(0, weight=1)
        timeline_grid.columnconfigure(1, weight=1)
        timeline_grid.columnconfigure(2, weight=1)

        # Start Date
        c_start = ctk.CTkFrame(timeline_grid, fg_color="transparent")
        c_start.grid(row=0, column=0, sticky="ew", padx=(0, 4))
        ctk.CTkLabel(c_start, text="Start Date (YYYY-MM-DD):", font=theme.get_font(11), text_color=theme.TEXT_SECONDARY).pack(anchor="w")
        self.date_entry = ctk.CTkEntry(c_start, fg_color=theme.BG_INPUT, border_color=theme.BORDER_COLOR)
        self.date_entry.insert(0, (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d"))
        self.date_entry.pack(fill="x", pady=(2, 0))

        # Days Per Matchweek (e.g. 1 match per 3 days)
        c_mw = ctk.CTkFrame(timeline_grid, fg_color="transparent")
        c_mw.grid(row=0, column=1, sticky="ew", padx=4)
        ctk.CTkLabel(c_mw, text="Days / Matchweek (Interval):", font=theme.get_font(11), text_color=theme.TEXT_SECONDARY).pack(anchor="w")
        self.mw_entry = ctk.CTkEntry(c_mw, fg_color=theme.BG_INPUT, border_color=theme.BORDER_COLOR)
        self.mw_entry.insert(0, "3")
        self.mw_entry.pack(fill="x", pady=(2, 0))

        # Ending Date (Auto-calculated from timeline days)
        c_end = ctk.CTkFrame(timeline_grid, fg_color="transparent")
        c_end.grid(row=0, column=2, sticky="ew", padx=(4, 0))
        ctk.CTkLabel(c_end, text="Ending Date (Auto-calc):", font=theme.get_font(11), text_color=theme.TEXT_SECONDARY).pack(anchor="w")
        self.end_date_entry = ctk.CTkEntry(c_end, fg_color=theme.BG_INPUT, border_color=theme.BORDER_COLOR)
        self.end_date_entry.pack(fill="x", pady=(2, 0))

        # Auto-update ending date when timeline inputs change
        self.date_entry.bind("<KeyRelease>", lambda e: self.auto_update_end_date())
        self.mw_entry.bind("<KeyRelease>", lambda e: self.auto_update_end_date())
        self.end_date_entry.bind("<KeyRelease>", lambda e: self.on_end_date_edited())

        # Live timeline breakdown label
        self.timeline_breakdown_lbl = ctk.CTkLabel(
            self.scroll_content,
            text="",
            font=theme.get_font(10, "bold"),
            text_color=theme.ACCENT_GREEN_TEXT
        )
        self.timeline_breakdown_lbl.pack(anchor="w", pady=(2, 8))

        # 4. Mobile Game Rules & Disconnection Protocol Card
        rules_card = ctk.CTkFrame(
            self.scroll_content,
            fg_color=theme.BG_CARD,
            corner_radius=8,
            border_color="#38bdf8",
            border_width=1
        )
        rules_card.pack(fill="x", pady=(4, 10))

        rules_inner = ctk.CTkFrame(rules_card, fg_color="transparent")
        rules_inner.pack(fill="x", padx=14, pady=10)

        ctk.CTkLabel(
            rules_inner,
            text="📱 4. Mobile Game Match Rules & Network Interruption Protocol:",
            font=theme.get_font(12, "bold"),
            text_color="#38bdf8"
        ).pack(anchor="w", pady=(0, 4))

        ctk.CTkLabel(
            rules_inner,
            text="⏱️ Fixed Match Duration: 10 Minutes per 1v1 match\n"
                 "🌐 Schedule Flexibility: Players can play at ANY time within their Matchweek timeline window.\n\n"
                 "⚠️ Disconnection & Network Interruption Protocol (Strict Enforcement):\n"
                 "• Mandatory Screenshot Proof: When an unintentional network cut occurs, either side must immediately take a clear screenshot showing the scoreline and game clock up to that exact disconnection moment. Submitting screenshot verification to the tournament desk is mandatory.\n"
                 "• Additional 5-Minute Continuation Match: The match will immediately continue from that point by playing an additional 5-minute match between the two teams.\n"
                 "• Aggregate Final Score: The official final scoreline will be calculated as the combined aggregate:\n"
                 "   OFFICIAL FINAL SCORE = (Pre-Disconnect Score from Screenshot) + (Score from 5-Minute Continuation Match)\n"
                 "• Intentional Rage-Quit & Dispute Resolution: Intentionally quitting, disconnecting to manipulate results, refusing to play the continuation match, or failing to produce screenshot proof will result in an immediate match forfeiture (awarded a 3-0 loss) and disciplinary review by tournament organizers.",
            font=theme.get_font(10),
            text_color=theme.TEXT_PRIMARY,
            justify="left",
            wraplength=640
        ).pack(anchor="w")

        # 5. Overwrite Protection Scope Checkbox
        self.clear_check_var = ctk.BooleanVar(value=True)
        self.clear_check = ctk.CTkCheckBox(
            self.scroll_content,
            text="Clear all existing fixtures before generating schedule",
            variable=self.clear_check_var,
            font=theme.get_font(11),
            text_color=theme.TEXT_SECONDARY
        )
        self.clear_check.pack(anchor="w", pady=(4, 10))

        # 6. Live Interactive Preview Box
        ctk.CTkLabel(
            self.scroll_content,
            text="5. Live Schedule Preview & Matchups Breakdown:",
            font=theme.get_font(11, "bold"),
            text_color=theme.TEXT_SECONDARY
        ).pack(anchor="w", pady=(4, 2))

        self.preview_box = ctk.CTkTextbox(
            self.scroll_content,
            height=150,
            fg_color=theme.BG_INPUT,
            border_color=theme.BORDER_COLOR,
            border_width=1,
            font=theme.get_font(10, family="Consolas")
        )
        self.preview_box.pack(fill="x", pady=(0, 8))
        self.preview_box.insert(
            "1.0",
            "Click '👁️ Preview Schedule' to calculate round pairings, simultaneous pitch allocations, and kickoff times..."
        )

        self.update_prediction_display()

    def update_prediction_display(self):
        """Fetch predicted tournament metrics from database and refresh matchweek dropdown & timeline."""
        fmt = self.format_menu.get()
        double = ("Double" in fmt)
        try:
            pred = self.fixture_gen.predict_fixture_summary(fmt, double_round=double)
            self.base_matchweeks = pred.get("base_matchweeks", 3)
            tot_matches = pred.get("total_matches", 0)
            tot_groups = pred.get("total_groups", 0)
            tot_teams = pred.get("total_teams", 0)
            per_mw = pred.get("matches_per_mw", 0)

            if "Knockout" in fmt:
                summary_txt = f"⚔️ Knockout: Top Qualifiers from {tot_groups} Groups • {self.base_matchweeks} Rounds ({tot_matches} matches)"
            elif "League" in fmt:
                summary_txt = f"🏆 League: {tot_teams} Teams • {tot_matches} Total Fixtures • {self.base_matchweeks} Base Matchweeks (~{per_mw}/MW)"
            else:
                summary_txt = f"📊 Predicted: {tot_groups} Groups • {tot_teams} Teams → {tot_matches} Total Fixtures ({self.base_matchweeks} Base MWs, ~{per_mw}/MW)"

            self.pred_banner_lbl.configure(text=summary_txt)
        except Exception:
            self.base_matchweeks = self._get_real_total_matchweeks(fmt)

        self.refresh_matchweek_options()
        self.auto_update_end_date()

    def refresh_matchweek_options(self):
        """Refresh the Matchweek options dropdown based on base + additional matchweeks."""
        tot_mw = self.get_total_effective_matchweeks()
        extra_note = f" (+{self.extra_matchweeks} Extra)" if self.extra_matchweeks > 0 else ""
        first_opt = f"All Matchweeks (Full Schedule - {tot_mw} Rounds{extra_note})"

        current_choice = self.matchweek_menu.get() if hasattr(self, "matchweek_menu") else ""
        self.mw_options = [first_opt] + [f"Matchweek {i} (Round {i}) Only" for i in range(1, tot_mw + 1)]

        self.matchweek_menu.configure(values=self.mw_options)

        # Retain selection if valid, otherwise select All Matchweeks
        if current_choice in self.mw_options:
            self.matchweek_menu.set(current_choice)
            self.on_matchweek_changed(current_choice)
        else:
            self.matchweek_menu.set(self.mw_options[0])
            self.on_matchweek_changed(self.mw_options[0])

    def add_matchweek(self):
        """Increment additional matchweeks and auto-update ending date."""
        self.extra_matchweeks += 1
        self.refresh_matchweek_options()
        self.auto_update_end_date()

    def remove_matchweek(self):
        """Decrement additional matchweeks down to 0."""
        if self.extra_matchweeks > 0:
            self.extra_matchweeks -= 1
            self.refresh_matchweek_options()
            self.auto_update_end_date()

    def get_target_matchweek_number(self) -> Optional[int]:
        choice = self.matchweek_menu.get().strip()
        if choice.startswith("Matchweek "):
            try:
                return int(choice.split()[1])
            except Exception:
                return None
        return None

    def on_format_changed(self, choice: str):
        self.extra_matchweeks = 0
        self.update_prediction_display()

    def on_matchweek_changed(self, choice: str):
        try:
            s_d = datetime.strptime(self.date_entry.get().strip(), "%Y-%m-%d").date()
        except Exception:
            s_d = datetime.now().date()
        try:
            days_mw = int(self.mw_entry.get().strip() or "3")
        except Exception:
            days_mw = 3

        if choice.startswith("Matchweek "):
            try:
                mw_num = int(choice.split()[1])
                mw_start = s_d + timedelta(days=(mw_num - 1) * days_mw)
                mw_end = mw_start + timedelta(days=days_mw)
                self.mw_info_lbl.configure(
                    text=f"📅 Matchweek {mw_num} Window: {mw_start.strftime('%Y-%m-%d')} to {mw_end.strftime('%Y-%m-%d')} ({days_mw} days duration) • Generates and schedules Matchweek {mw_num} only.",
                    text_color="#38bdf8"
                )
                self.clear_check.configure(
                    text=f"Replace existing Matchweek {mw_num} fixtures only (keeps all other matchweeks safe)"
                )
            except Exception:
                pass
        else:
            tot_mw = self.get_total_effective_matchweeks()
            mw_1_end = s_d + timedelta(days=days_mw)
            self.mw_info_lbl.configure(
                text=f"All {tot_mw} matchweeks will be generated sequentially across the timeline (1 Matchweek window: {s_d.strftime('%Y-%m-%d')} to {mw_1_end.strftime('%Y-%m-%d')}).",
                text_color=theme.TEXT_MUTED
            )
            self.clear_check.configure(
                text="Clear all existing fixtures before generating schedule"
            )

        self.auto_update_end_date()

    def auto_update_end_date(self):
        """
        Auto-calculate 1 matchweek's ending date from:
        Start Date + Days/Matchweek
        Example: Start Date = 2026-10-13, Days/Matchweek = 3 -> Ending Date = 2026-10-16.
        """
        try:
            s_d = datetime.strptime(self.date_entry.get().strip(), "%Y-%m-%d").date()
        except Exception:
            s_d = datetime.now().date() + timedelta(days=1)

        try:
            days_mw = int(self.mw_entry.get().strip() or "3")
            if days_mw < 1:
                days_mw = 1
        except Exception:
            days_mw = 3

        target_mw = self.get_target_matchweek_number()
        tot_mw = self.get_total_effective_matchweeks()

        if target_mw is not None:
            mw_start = s_d + timedelta(days=(target_mw - 1) * days_mw)
            mw_end = mw_start + timedelta(days=days_mw)
            self.end_date_entry.delete(0, "end")
            self.end_date_entry.insert(0, mw_end.strftime("%Y-%m-%d"))

            self.timeline_breakdown_lbl.configure(
                text=f"🗓️ Matchweek {target_mw} Window: {mw_start.strftime('%Y-%m-%d')} to {mw_end.strftime('%Y-%m-%d')} ({days_mw} days duration)"
            )
        else:
            # 1 matchweek duration: Start Date to Start Date + Days/Matchweek
            mw_end = s_d + timedelta(days=days_mw)
            full_end = s_d + timedelta(days=tot_mw * days_mw)
            self.end_date_entry.delete(0, "end")
            self.end_date_entry.insert(0, mw_end.strftime("%Y-%m-%d"))

            extra_info = f" (+{self.extra_matchweeks} extra round{'s' if self.extra_matchweeks > 1 else ''})" if self.extra_matchweeks > 0 else ""
            self.timeline_breakdown_lbl.configure(
                text=f"🗓️ 1 Matchweek Window: {s_d.strftime('%Y-%m-%d')} to {mw_end.strftime('%Y-%m-%d')} ({days_mw} days/MW) • Full Tournament ({tot_mw} MWs{extra_info}): {s_d.strftime('%Y-%m-%d')} to {full_end.strftime('%Y-%m-%d')}"
            )

    def on_end_date_edited(self):
        """If user manually edits Ending Date, calculate the span for 1 matchweek and update Days/Matchweek."""
        try:
            s_d = datetime.strptime(self.date_entry.get().strip(), "%Y-%m-%d").date()
            e_d = datetime.strptime(self.end_date_entry.get().strip(), "%Y-%m-%d").date()
            span = (e_d - s_d).days
            if span >= 1:
                target_mw = self.get_target_matchweek_number()
                if target_mw is not None and target_mw > 1:
                    days_mw = max(1, span // target_mw)
                else:
                    days_mw = span
                self.mw_entry.delete(0, "end")
                self.mw_entry.insert(0, str(days_mw))
                tot_mw = self.get_total_effective_matchweeks()
                full_end = s_d + timedelta(days=tot_mw * days_mw)
                self.timeline_breakdown_lbl.configure(
                    text=f"🗓️ 1 Matchweek Window: {s_d.strftime('%Y-%m-%d')} to {e_d.strftime('%Y-%m-%d')} ({days_mw} days/MW) • Full Tournament ({tot_mw} MWs): {s_d.strftime('%Y-%m-%d')} to {full_end.strftime('%Y-%m-%d')}"
                )
        except Exception:
            pass

    def run_preview(self) -> bool:
        fmt = self.format_menu.get()
        s_d = self.date_entry.get().strip()
        e_d = self.end_date_entry.get().strip()
        target_mw = self.get_target_matchweek_number()
        total_mw = self.get_total_effective_matchweeks()

        try:
            days_mw = int(self.mw_entry.get().strip() or "3")
        except ValueError:
            days_mw = 3

        # Fixed 10-minute mobile matches in online/mobile lobby
        dur = 10
        venues = ["Online / Mobile Lobby"]
        s_t = "Flexible"
        end_t = "Flexible"

        self.preview_box.delete("1.0", "end")
        self.status_lbl.configure(text="Generating preview...", text_color=theme.TEXT_MUTED)

        try:
            if "Knockout" in fmt:
                self.generated_fixtures = self.knockout_mgr.generate_bracket_from_group_qualifiers(
                    start_date=s_d, start_time=s_t, match_duration_mins=dur, venue=venues[0]
                )
            elif "League" in fmt:
                double = ("Double" in fmt)
                self.generated_fixtures = self.fixture_gen.preview_league_fixtures(
                    start_date=s_d, start_time=s_t, match_duration_mins=dur, venues=venues,
                    double_round=double, day_end_time=end_t, end_date=e_d, days_per_matchweek=days_mw,
                    target_matchweek=target_mw, total_matchweeks=total_mw
                )
            else:
                self.generated_fixtures = self.fixture_gen.preview_group_fixtures(
                    start_date=s_d, start_time=s_t, match_duration_mins=dur, venues=venues,
                    double_round=False, day_end_time=end_t, end_date=e_d, days_per_matchweek=days_mw,
                    target_matchweek=target_mw, total_matchweeks=total_mw
                )

            if not self.generated_fixtures:
                self.preview_box.insert("1.0", "No fixtures could be generated. Please ensure teams and groups are confirmed.")
                self.status_lbl.configure(text="0 fixtures generated", text_color=theme.COLOR_DANGER)
                return False

            # Group fixtures by Matchweek
            mw_groups: Dict[int, List[Dict[str, Any]]] = {}
            for f in self.generated_fixtures:
                mw_groups.setdefault(f.get("round_number", 1), []).append(f)

            try:
                s_d_obj = datetime.strptime(s_d, "%Y-%m-%d").date()
            except Exception:
                s_d_obj = datetime.now().date()

            if target_mw is not None:
                mw_start = s_d_obj + timedelta(days=(target_mw - 1) * days_mw)
                mw_end = mw_start + timedelta(days=days_mw)
                txt = f"✓ MATCHWEEK {target_mw} SCHEDULE READY: {len(self.generated_fixtures)} matches\n"
                txt += f"  Rule: 10-Minute Mobile Match • Window: {mw_start.strftime('%Y-%m-%d')} to {mw_end.strftime('%Y-%m-%d')} ({days_mw} days)\n"
                txt += f"  Timing: Flexible (Players can play 1v1 at any time within this matchweek timeline)\n"
                txt += f"  Platform: Online / Mobile Lobby\n\n"
                txt += "Official Match Pairings:\n"
                for f in self.generated_fixtures:
                    txt += f"  • M#{f['match_number']} [{f.get('group_name', 'Group')}]: {f['home_team_name']} vs {f['away_team_name']} | Window: {f['scheduled_date']} @ {f['venue']}\n"
            else:
                mw_1_end = s_d_obj + timedelta(days=days_mw)
                full_end = s_d_obj + timedelta(days=len(mw_groups) * days_mw)
                txt = f"✓ FULL TOURNAMENT SCHEDULE READY: {len(self.generated_fixtures)} matches across {len(mw_groups)} Matchweeks\n"
                txt += f"  Rule: Fixed 10-Minute Mobile Matches (Flexible play anytime within Matchweek timeline)\n"
                txt += f"  Disconnection Protocol: 5-Minute Continuation Match + Screenshot Aggregate Score\n"
                txt += f"  1 Matchweek Window: {s_d} to {mw_1_end.strftime('%Y-%m-%d')} ({days_mw} days per squad)\n"
                txt += f"  Full Tournament Timeline: {s_d} to {full_end.strftime('%Y-%m-%d')}\n\n"
                for r_num, m_list in sorted(mw_groups.items()):
                    r_start = s_d_obj + timedelta(days=(r_num - 1) * days_mw)
                    r_end = r_start + timedelta(days=days_mw)
                    extra_tag = " [Extra Round]" if r_num > self.base_matchweeks else ""
                    txt += f"  • Matchweek {r_num}{extra_tag}: {r_start.strftime('%Y-%m-%d')} to {r_end.strftime('%Y-%m-%d')} ({len(m_list)} matches, Flexible 1v1 Window)\n"

                txt += "\nSample Matchups:\n"
                for f in self.generated_fixtures[:8]:
                    txt += f"  • M#{f['match_number']} [MW {f.get('round_number', 1)} - {f.get('group_name', '')}]: {f['home_team_name']} vs {f['away_team_name']} | Window: {f['scheduled_date']} @ {f['venue']}\n"
                if len(self.generated_fixtures) > 8:
                    txt += f"  ... and {len(self.generated_fixtures) - 8} more matches.\n"

            self.preview_box.insert("1.0", txt)
            self.status_lbl.configure(text=f"✓ {len(self.generated_fixtures)} matches prepared", text_color=theme.ACCENT_GREEN)
            return True

        except Exception as e:
            self.preview_box.insert("1.0", f"Error generating preview: {str(e)}")
            self.status_lbl.configure(text="Preview error", text_color=theme.COLOR_DANGER)
            return False

    def run_save(self):
        if not self.generated_fixtures:
            ok = self.run_preview()
            if not ok or not self.generated_fixtures:
                messagebox.showerror(
                    "No Fixtures",
                    "Could not generate fixtures. Please check that teams and groups are assigned."
                )
                return

        target_mw = self.get_target_matchweek_number()
        try:
            if target_mw is not None:
                clear_r = target_mw if self.clear_check_var.get() else None
                saved_cnt = self.fixture_gen.save_fixtures(
                    self.generated_fixtures,
                    clear_existing=False,
                    clear_round=clear_r
                )
                messagebox.showinfo(
                    "Schedule Saved",
                    f"Successfully generated and saved {saved_cnt} fixtures for Matchweek {target_mw}!"
                )
            else:
                saved_cnt = self.fixture_gen.save_fixtures(
                    self.generated_fixtures,
                    clear_existing=self.clear_check_var.get()
                )
                messagebox.showinfo(
                    "Schedule Saved",
                    f"Successfully generated and saved {saved_cnt} tournament fixtures!"
                )

            self.destroy()
            if self.on_saved:
                self.on_saved()

        except Exception as e:
            messagebox.showerror("Save Failed", f"Could not save fixtures: {str(e)}")

"""
MINARAM CUP — Fixture Generation Wizard Modal Dialog.
Clean, modern, and robust interface for generating tournament fixtures,
matchweek timeline spacing, parallel pitch scheduling, and knockout brackets.
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
        super().__init__(parent, title="⚡ Fixture Generation Wizard", width=720, height=720)
        self.resizable(True, True)
        self.minsize(640, 580)

        self.db = db
        self.fixture_gen = FixtureGenerator(db)
        self.knockout_mgr = KnockoutManager(db)
        self.on_saved = on_saved

        self.generated_fixtures: List[Dict[str, Any]] = []
        self.mw_options: List[str] = []

        self.build_ui()

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

        # 2. Matchweek Scope Selection Card
        mw_card = ctk.CTkFrame(self.scroll_content, fg_color=theme.BG_INPUT, corner_radius=8, border_color=theme.BORDER_COLOR, border_width=1)
        mw_card.pack(fill="x", pady=(0, 10))

        mw_card_inner = ctk.CTkFrame(mw_card, fg_color="transparent")
        mw_card_inner.pack(fill="x", padx=14, pady=10)

        ctk.CTkLabel(
            mw_card_inner,
            text="2. Matchweek Scope Selection (All vs Specific Round):",
            font=theme.get_font(11, "bold"),
            text_color=theme.TEXT_PRIMARY
        ).pack(anchor="w")

        total_mw = self.fixture_gen.get_total_matchweeks("Group Stage") or 3
        self.mw_options = ["All Matchweeks (Full Schedule)"] + [f"Matchweek {i} (Round {i}) Only" for i in range(1, total_mw + 1)]

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
        self.matchweek_menu.pack(fill="x", pady=(6, 4))

        self.mw_info_lbl = ctk.CTkLabel(
            mw_card_inner,
            text="All matchweeks will be generated sequentially across the tournament timeline.",
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
        timeline_grid.pack(fill="x", pady=(0, 8))
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

        # Days Per Matchweek
        c_mw = ctk.CTkFrame(timeline_grid, fg_color="transparent")
        c_mw.grid(row=0, column=1, sticky="ew", padx=4)
        ctk.CTkLabel(c_mw, text="Days / Matchweek (Interval):", font=theme.get_font(11), text_color=theme.TEXT_SECONDARY).pack(anchor="w")
        self.mw_entry = ctk.CTkEntry(c_mw, fg_color=theme.BG_INPUT, border_color=theme.BORDER_COLOR)
        self.mw_entry.insert(0, "3")
        self.mw_entry.pack(fill="x", pady=(2, 0))

        # Ending Date (Auto-calculated)
        c_end = ctk.CTkFrame(timeline_grid, fg_color="transparent")
        c_end.grid(row=0, column=2, sticky="ew", padx=(4, 0))
        ctk.CTkLabel(c_end, text="Ending Date (Auto-calc):", font=theme.get_font(11), text_color=theme.TEXT_SECONDARY).pack(anchor="w")
        self.end_date_entry = ctk.CTkEntry(c_end, fg_color=theme.BG_INPUT, border_color=theme.BORDER_COLOR)
        self.end_date_entry.insert(0, (datetime.now() + timedelta(days=7)).strftime("%Y-%m-%d"))
        self.end_date_entry.pack(fill="x", pady=(2, 0))

        # Auto-update ending date when timeline inputs change
        self.date_entry.bind("<KeyRelease>", lambda e: self.auto_update_end_date())
        self.mw_entry.bind("<KeyRelease>", lambda e: self.auto_update_end_date())

        # 4. Match Duration & Daily Operating Hours
        ctk.CTkLabel(
            self.scroll_content,
            text="4. Match Timing & Daily Operating Window:",
            font=theme.get_font(12, "bold"),
            text_color=theme.TEXT_PRIMARY
        ).pack(anchor="w", pady=(4, 4))

        timing_grid = ctk.CTkFrame(self.scroll_content, fg_color="transparent")
        timing_grid.pack(fill="x", pady=(0, 8))
        timing_grid.columnconfigure(0, weight=1)
        timing_grid.columnconfigure(1, weight=1)
        timing_grid.columnconfigure(2, weight=1)

        # Duration
        c_dur = ctk.CTkFrame(timing_grid, fg_color="transparent")
        c_dur.grid(row=0, column=0, sticky="ew", padx=(0, 4))
        ctk.CTkLabel(c_dur, text="Match Duration (Minutes):", font=theme.get_font(11), text_color=theme.TEXT_SECONDARY).pack(anchor="w")
        self.dur_entry = ctk.CTkEntry(c_dur, fg_color=theme.BG_INPUT, border_color=theme.BORDER_COLOR)
        self.dur_entry.insert(0, "30")
        self.dur_entry.pack(fill="x", pady=(2, 0))

        # Kickoff Time
        c_kickoff = ctk.CTkFrame(timing_grid, fg_color="transparent")
        c_kickoff.grid(row=0, column=1, sticky="ew", padx=4)
        ctk.CTkLabel(c_kickoff, text="Kick-off Start Time (HH:MM):", font=theme.get_font(11), text_color=theme.TEXT_SECONDARY).pack(anchor="w")
        self.time_entry = ctk.CTkEntry(c_kickoff, fg_color=theme.BG_INPUT, border_color=theme.BORDER_COLOR)
        self.time_entry.insert(0, "16:00")
        self.time_entry.pack(fill="x", pady=(2, 0))

        # Daily Operating End Time
        c_close = ctk.CTkFrame(timing_grid, fg_color="transparent")
        c_close.grid(row=0, column=2, sticky="ew", padx=(4, 0))
        ctk.CTkLabel(c_close, text="Operating End Time (HH:MM):", font=theme.get_font(11), text_color=theme.TEXT_SECONDARY).pack(anchor="w")
        self.end_entry = ctk.CTkEntry(c_close, fg_color=theme.BG_INPUT, border_color=theme.BORDER_COLOR)
        self.end_entry.insert(0, "20:00")
        self.end_entry.pack(fill="x", pady=(2, 0))

        # 5. Venues & Simultaneous Pitches
        v_box = ctk.CTkFrame(self.scroll_content, fg_color="transparent")
        v_box.pack(fill="x", pady=(4, 8))

        ctk.CTkLabel(
            v_box,
            text="5. Venues / Pitches (comma-separated for parallel simultaneous matches):",
            font=theme.get_font(11),
            text_color=theme.TEXT_SECONDARY
        ).pack(anchor="w")
        self.venue_entry = ctk.CTkEntry(v_box, fg_color=theme.BG_INPUT, border_color=theme.BORDER_COLOR)
        self.venue_entry.insert(0, "Minaram Pitch 1, Minaram Pitch 2")
        self.venue_entry.pack(fill="x", pady=(2, 0))

        # 6. Overwrite Protection Scope Checkbox
        self.clear_check_var = ctk.BooleanVar(value=True)
        self.clear_check = ctk.CTkCheckBox(
            self.scroll_content,
            text="Clear all existing fixtures before generating schedule",
            variable=self.clear_check_var,
            font=theme.get_font(11),
            text_color=theme.TEXT_SECONDARY
        )
        self.clear_check.pack(anchor="w", pady=(4, 10))

        # 7. Live Interactive Preview Box
        ctk.CTkLabel(
            self.scroll_content,
            text="6. Live Schedule Preview & Matchups Breakdown:",
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
        t_mw = self.fixture_gen.get_total_matchweeks(choice, double_round=("Double" in choice)) or 3
        self.mw_options = ["All Matchweeks (Full Schedule)"] + [f"Matchweek {i} (Round {i}) Only" for i in range(1, t_mw + 1)]
        self.matchweek_menu.configure(values=self.mw_options)
        self.matchweek_menu.set(self.mw_options[0])
        self.on_matchweek_changed(self.mw_options[0])
        self.auto_update_end_date()

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
                mw_d = s_d + timedelta(days=(mw_num - 1) * days_mw)
                self.mw_info_lbl.configure(
                    text=f"📅 Scheduled Date: {mw_d.strftime('%Y-%m-%d')} • Generates and schedules Matchweek {mw_num} only.",
                    text_color="#38bdf8"
                )
                self.clear_check.configure(
                    text=f"Replace existing Matchweek {mw_num} fixtures only (keeps all other matchweeks safe)"
                )
            except Exception:
                pass
        else:
            self.mw_info_lbl.configure(
                text="All matchweeks will be generated sequentially across the tournament timeline.",
                text_color=theme.TEXT_MUTED
            )
            self.clear_check.configure(
                text="Clear all existing fixtures before generating schedule"
            )

    def auto_update_end_date(self):
        try:
            s_d = datetime.strptime(self.date_entry.get().strip(), "%Y-%m-%d").date()
            days_mw = int(self.mw_entry.get().strip() or "3")
            fmt = self.format_menu.get()
            t_mw = self.fixture_gen.get_total_matchweeks(fmt, double_round=("Double" in fmt)) or 3
            e_d = s_d + timedelta(days=max(0, (t_mw - 1) * days_mw))
            self.end_date_entry.delete(0, "end")
            self.end_date_entry.insert(0, e_d.strftime("%Y-%m-%d"))
        except Exception:
            pass

    def run_preview(self) -> bool:
        fmt = self.format_menu.get()
        s_d = self.date_entry.get().strip()
        e_d = self.end_date_entry.get().strip()
        s_t = self.time_entry.get().strip() or "16:00"
        end_t = self.end_entry.get().strip() or "20:00"
        target_mw = self.get_target_matchweek_number()

        try:
            dur = int(self.dur_entry.get().strip() or "30")
        except ValueError:
            dur = 30
        try:
            days_mw = int(self.mw_entry.get().strip() or "3")
        except ValueError:
            days_mw = 3

        venues = [v.strip() for v in self.venue_entry.get().split(",") if v.strip()] or ["Minaram Stadium"]

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
                    target_matchweek=target_mw
                )
            else:
                self.generated_fixtures = self.fixture_gen.preview_group_fixtures(
                    start_date=s_d, start_time=s_t, match_duration_mins=dur, venues=venues,
                    double_round=False, day_end_time=end_t, end_date=e_d, days_per_matchweek=days_mw,
                    target_matchweek=target_mw
                )

            if not self.generated_fixtures:
                self.preview_box.insert("1.0", "No fixtures could be generated. Please ensure teams and groups are confirmed.")
                self.status_lbl.configure(text="0 fixtures generated", text_color=theme.COLOR_DANGER)
                return False

            # Group by Matchweek
            mw_groups: Dict[int, List[Dict[str, Any]]] = {}
            for f in self.generated_fixtures:
                mw_groups.setdefault(f.get("round_number", 1), []).append(f)

            if target_mw is not None:
                txt = f"✓ MATCHWEEK {target_mw} SCHEDULE READY: {len(self.generated_fixtures)} matches\n"
                mw_matches = mw_groups.get(target_mw, self.generated_fixtures)
                d_str = mw_matches[0].get("scheduled_date", "") if mw_matches else ""
                times = f"{mw_matches[0].get('scheduled_time', '')} to {mw_matches[-1].get('scheduled_time', '')}" if mw_matches else ""
                txt += f"  Date: {d_str} | Kickoff Window: {times}\n"
                txt += f"  Pitches in parallel: {', '.join(venues)}\n\n"
                txt += "Official Match Pairings:\n"
                for f in mw_matches:
                    txt += f"  • M#{f['match_number']} [{f.get('group_name', 'Group')}]: {f['home_team_name']} vs {f['away_team_name']} | {f['scheduled_time']} @ {f['venue']}\n"
            else:
                txt = f"✓ FULL TOURNAMENT SCHEDULE READY: {len(self.generated_fixtures)} matches across {len(mw_groups)} Matchweeks\n"
                txt += f"  Timeline interval: 1 match every {days_mw} days per squad\n"
                for r_num, m_list in sorted(mw_groups.items()):
                    d_str = m_list[0].get("scheduled_date", "") if m_list else ""
                    times = f"{m_list[0].get('scheduled_time', '')} to {m_list[-1].get('scheduled_time', '')}" if m_list else ""
                    txt += f"  • Matchweek {r_num}: {d_str} ({len(m_list)} matches, {times})\n"

                txt += "\nSample Matchups:\n"
                for f in self.generated_fixtures[:8]:
                    txt += f"  • M#{f['match_number']} [MW {f.get('round_number', 1)} - {f.get('group_name', '')}]: {f['home_team_name']} vs {f['away_team_name']} | {f['scheduled_date']} {f['scheduled_time']} @ {f['venue']}\n"
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

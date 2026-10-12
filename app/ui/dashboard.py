"""
Tournament overview dashboard view with live KPI cards,
upcoming fixtures, recent registrations, standings preview, and quick actions.
"""

import customtkinter as ctk
from app.ui import theme
from app.database import Database
from app.standings import StandingsCalculator


class DashboardView(ctk.CTkScrollableFrame):
    def __init__(self, parent, db: Database, navigate_callback, on_cloud_sync=None):
        super().__init__(parent, fg_color="transparent")
        self.db = db
        self.navigate = navigate_callback
        self.on_cloud_sync = on_cloud_sync
        self.standings_calc = StandingsCalculator(db)

        self.render_dashboard()

    def refresh(self):
        """Re-query database and rebuild dashboard."""
        for child in self.winfo_children():
            child.destroy()
        self.render_dashboard()

    def render_dashboard(self):
        # 1. Fetch live metrics from SQLite
        reg_count = self.db.execute_one("SELECT COUNT(*) AS c FROM registrations;")["c"]
        pending_regs = self.db.execute_one("SELECT COUNT(*) AS c FROM registrations WHERE status = 'Pending';")["c"]
        team_count = self.db.execute_one("SELECT COUNT(*) AS c FROM teams;")["c"]
        confirmed_teams = self.db.execute_one("SELECT COUNT(*) AS c FROM teams WHERE status = 'Confirmed';")["c"]

        total_matches = self.db.execute_one("SELECT COUNT(*) AS c FROM matches;")["c"]
        completed_matches = self.db.execute_one("SELECT COUNT(*) AS c FROM matches WHERE status IN ('Completed', 'Walkover');")["c"]
        awaiting_matches = self.db.execute_one("SELECT COUNT(*) AS c FROM matches WHERE status = 'Scheduled';")["c"]

        completion_pct = int((completed_matches / total_matches) * 100) if total_matches > 0 else 0

        # Header Title & Quick Actions
        top_row = ctk.CTkFrame(self, fg_color="transparent")
        top_row.pack(fill="x", padx=16, pady=(12, 16))

        title_box = ctk.CTkFrame(top_row, fg_color="transparent")
        title_box.pack(side="left")

        t_name = self.db.get_setting("tournament_name", "Minaram Cup")
        t_edition = self.db.get_setting("edition", "2026 Edition")
        ctk.CTkLabel(
            title_box,
            text=f"{t_name} Overview",
            font=theme.get_font(22, "bold"),
            text_color=theme.TEXT_PRIMARY
        ).pack(anchor="w")
        ctk.CTkLabel(
            title_box,
            text=f"Edition: {t_edition} • Live Database Metrics",
            font=theme.get_font(12),
            text_color=theme.TEXT_MUTED
        ).pack(anchor="w")

        # Quick Actions on Right
        actions_box = ctk.CTkFrame(top_row, fg_color="transparent")
        actions_box.pack(side="right")

        if self.on_cloud_sync:
            ctk.CTkButton(
                actions_box,
                text="🚀 Push to Render",
                fg_color="#0284c7",
                hover_color="#0369a1",
                text_color="#FFFFFF",
                font=theme.get_font(12, "bold"),
                height=32,
                command=self.on_cloud_sync
            ).pack(side="left", padx=4)

        ctk.CTkButton(
            actions_box,
            text="+ Register Team",
            fg_color=theme.ACCENT_GREEN,
            hover_color=theme.ACCENT_GREEN_HOVER,
            text_color=theme.TEXT_DARK,
            font=theme.get_font(12, "bold"),
            height=32,
            command=lambda: self.navigate("Registrations")
        ).pack(side="left", padx=4)

        ctk.CTkButton(
            actions_box,
            text="📅 Fixtures",
            fg_color=theme.BG_CARD,
            border_color=theme.BORDER_COLOR,
            border_width=1,
            hover_color=theme.BG_CARD_HOVER,
            text_color=theme.TEXT_PRIMARY,
            height=32,
            font=theme.get_font(11),
            command=lambda: self.navigate("Fixtures")
        ).pack(side="left", padx=4)

        ctk.CTkButton(
            actions_box,
            text="⚽ Enter Result",
            fg_color=theme.BG_CARD,
            border_color=theme.BORDER_COLOR,
            border_width=1,
            hover_color=theme.BG_CARD_HOVER,
            text_color=theme.TEXT_PRIMARY,
            height=32,
            font=theme.get_font(11),
            command=lambda: self.navigate("Results")
        ).pack(side="left", padx=4)

        # Cloud Sync Status & Action Banner
        from app.cloud_sync_service import get_cloud_config
        cfg = get_cloud_config()
        last_sync = cfg.get("last_sync_time") or "Never synced yet"
        cloud_url = cfg.get("backend_url", "https://minaram-cup-api.onrender.com")

        cloud_banner = ctk.CTkFrame(self, fg_color=theme.BG_CARD, corner_radius=10, border_color="#0284c7", border_width=1)
        cloud_banner.pack(fill="x", padx=16, pady=(0, 16))

        cb_left = ctk.CTkFrame(cloud_banner, fg_color="transparent")
        cb_left.pack(side="left", padx=16, pady=10)

        ctk.CTkLabel(
            cb_left,
            text="☁️ Render Cloud API & Live Website Synchronization",
            font=theme.get_font(13, "bold"),
            text_color=theme.TEXT_PRIMARY
        ).pack(anchor="w")

        ctk.CTkLabel(
            cb_left,
            text=f"Target: {cloud_url}   •   Last Published: {last_sync}",
            font=theme.get_font(11),
            text_color=theme.TEXT_SECONDARY
        ).pack(anchor="w", pady=(2, 0))

        if self.on_cloud_sync:
            ctk.CTkButton(
                cloud_banner,
                text="🚀 Push Updates to Render Now",
                fg_color="#0284c7",
                hover_color="#0369a1",
                text_color="#FFFFFF",
                font=theme.get_font(12, "bold"),
                height=34,
                command=self.on_cloud_sync
            ).pack(side="right", padx=16, pady=10)

        # 2. KPI Cards Grid (4 in row 1, 3 in row 2)
        kpi_frame = ctk.CTkFrame(self, fg_color="transparent")
        kpi_frame.pack(fill="x", padx=16, pady=(0, 16))

        cards_row1 = [
            ("Total Registrations", str(reg_count), "📥 Total entries received", theme.ACCENT_GREEN),
            ("Unique Teams", str(team_count), f"{confirmed_teams} confirmed", theme.COLOR_INFO),
            ("Pending Registrations", str(pending_regs), "Awaiting confirmation", theme.COLOR_WARNING),
            ("Tournament Progress", f"{completion_pct}%", f"{completed_matches}/{total_matches} played", theme.COLOR_PURPLE),
        ]

        for idx, (title, val, sub, color) in enumerate(cards_row1):
            kpi_frame.columnconfigure(idx, weight=1)
            card = ctk.CTkFrame(kpi_frame, fg_color=theme.BG_CARD, corner_radius=10, border_color=theme.BORDER_COLOR, border_width=1)
            card.grid(row=0, column=idx, padx=6, pady=4, sticky="nsew")

            ctk.CTkLabel(card, text=title, font=ctk.CTkFont(size=11), text_color=theme.TEXT_SECONDARY).pack(anchor="w", padx=14, pady=(12, 2))
            ctk.CTkLabel(card, text=val, font=ctk.CTkFont(size=24, weight="bold"), text_color=color).pack(anchor="w", padx=14)
            ctk.CTkLabel(card, text=sub, font=ctk.CTkFont(size=10), text_color=theme.TEXT_MUTED).pack(anchor="w", padx=14, pady=(2, 12))

        cards_row2 = [
            ("Scheduled Matches", str(total_matches), "Total tournament fixtures", theme.TEXT_PRIMARY),
            ("Completed Matches", str(completed_matches), "Scores confirmed", theme.ACCENT_GREEN),
            ("Awaiting Results", str(awaiting_matches), "Pending match outcome", theme.COLOR_WARNING),
        ]
        kpi_frame2 = ctk.CTkFrame(self, fg_color="transparent")
        kpi_frame2.pack(fill="x", padx=16, pady=(0, 16))
        for idx, (title, val, sub, color) in enumerate(cards_row2):
            kpi_frame2.columnconfigure(idx, weight=1)
            card = ctk.CTkFrame(kpi_frame2, fg_color=theme.BG_CARD, corner_radius=10, border_color=theme.BORDER_COLOR, border_width=1)
            card.grid(row=0, column=idx, padx=6, pady=4, sticky="nsew")

            ctk.CTkLabel(card, text=title, font=ctk.CTkFont(size=11), text_color=theme.TEXT_SECONDARY).pack(anchor="w", padx=14, pady=(12, 2))
            ctk.CTkLabel(card, text=val, font=ctk.CTkFont(size=22, weight="bold"), text_color=color).pack(anchor="w", padx=14)
            ctk.CTkLabel(card, text=sub, font=ctk.CTkFont(size=10), text_color=theme.TEXT_MUTED).pack(anchor="w", padx=14, pady=(2, 12))

        # 3. Two-Column Middle Section: Upcoming Fixtures vs Latest Results
        mid_grid = ctk.CTkFrame(self, fg_color="transparent")
        mid_grid.pack(fill="x", padx=16, pady=(0, 16))
        mid_grid.columnconfigure(0, weight=1)
        mid_grid.columnconfigure(1, weight=1)

        # Left Column: Upcoming Fixtures
        fixtures_card = ctk.CTkFrame(mid_grid, fg_color=theme.BG_CARD, corner_radius=10, border_color=theme.BORDER_COLOR, border_width=1)
        fixtures_card.grid(row=0, column=0, padx=(0, 8), sticky="nsew")

        f_hdr = ctk.CTkFrame(fixtures_card, fg_color="transparent")
        f_hdr.pack(fill="x", padx=16, pady=(14, 8))
        ctk.CTkLabel(f_hdr, text="Upcoming Fixtures", font=ctk.CTkFont(size=14, weight="bold"), text_color=theme.TEXT_PRIMARY).pack(side="left")
        ctk.CTkButton(f_hdr, text="View All", width=60, height=22, fg_color="transparent", hover_color=theme.BG_CARD_HOVER, text_color=theme.ACCENT_GREEN_TEXT, font=ctk.CTkFont(size=11), command=lambda: self.navigate("Fixtures")).pack(side="right")

        upcoming_matches = self.db.execute_query("""
            SELECT m.match_number, m.stage, ht.name AS home_name, at.name AS away_name,
                   m.scheduled_date, m.scheduled_time, m.venue
            FROM matches m
            LEFT JOIN teams ht ON m.home_team_id = ht.id
            LEFT JOIN teams at ON m.away_team_id = at.id
            WHERE m.status = 'Scheduled'
            ORDER BY m.scheduled_date ASC, m.scheduled_time ASC
            LIMIT 4;
        """)

        if not upcoming_matches:
            ctk.CTkLabel(fixtures_card, text="No scheduled matches awaiting play.", font=ctk.CTkFont(size=12), text_color=theme.TEXT_MUTED).pack(padx=16, pady=24)
        else:
            for m in upcoming_matches:
                row = ctk.CTkFrame(fixtures_card, fg_color=theme.BG_INPUT, corner_radius=6)
                row.pack(fill="x", padx=14, pady=4)
                
                # Info
                left_box = ctk.CTkFrame(row, fg_color="transparent")
                left_box.pack(side="left", padx=10, pady=8)
                h_name = m["home_name"] or "TBD"
                a_name = m["away_name"] or "TBD"
                ctk.CTkLabel(left_box, text=f"{h_name} vs {a_name}", font=ctk.CTkFont(size=12, weight="bold"), text_color=theme.TEXT_PRIMARY).pack(anchor="w")
                ctk.CTkLabel(left_box, text=f"Match #{m['match_number']} • {m['stage']} • {m['venue']}", font=ctk.CTkFont(size=10), text_color=theme.TEXT_MUTED).pack(anchor="w")

                right_box = ctk.CTkFrame(row, fg_color="transparent")
                right_box.pack(side="right", padx=10, pady=8)
                ctk.CTkLabel(right_box, text=f"{m['scheduled_date']} {m['scheduled_time']}", font=ctk.CTkFont(size=11), text_color=theme.ACCENT_GREEN_TEXT).pack(anchor="e")

        # Right Column: Latest Results
        results_card = ctk.CTkFrame(mid_grid, fg_color=theme.BG_CARD, corner_radius=10, border_color=theme.BORDER_COLOR, border_width=1)
        results_card.grid(row=0, column=1, padx=(8, 0), sticky="nsew")

        r_hdr = ctk.CTkFrame(results_card, fg_color="transparent")
        r_hdr.pack(fill="x", padx=16, pady=(14, 8))
        ctk.CTkLabel(r_hdr, text="Latest Results", font=ctk.CTkFont(size=14, weight="bold"), text_color=theme.TEXT_PRIMARY).pack(side="left")
        ctk.CTkButton(r_hdr, text="View All", width=60, height=22, fg_color="transparent", hover_color=theme.BG_CARD_HOVER, text_color=theme.ACCENT_GREEN_TEXT, font=ctk.CTkFont(size=11), command=lambda: self.navigate("Results")).pack(side="right")

        recent_results = self.db.execute_query("""
            SELECT m.match_number, m.stage, ht.name AS home_name, at.name AS away_name,
                   m.home_score, m.away_score, m.status, wt.name AS winner_name
            FROM matches m
            LEFT JOIN teams ht ON m.home_team_id = ht.id
            LEFT JOIN teams at ON m.away_team_id = at.id
            LEFT JOIN teams wt ON m.winner_team_id = wt.id
            WHERE m.status IN ('Completed', 'Walkover')
            ORDER BY m.id DESC
            LIMIT 4;
        """)

        if not recent_results:
            ctk.CTkLabel(results_card, text="No match results recorded yet.", font=ctk.CTkFont(size=12), text_color=theme.TEXT_MUTED).pack(padx=16, pady=24)
        else:
            for r in recent_results:
                row = ctk.CTkFrame(results_card, fg_color=theme.BG_INPUT, corner_radius=6)
                row.pack(fill="x", padx=14, pady=4)

                left_box = ctk.CTkFrame(row, fg_color="transparent")
                left_box.pack(side="left", padx=10, pady=8)
                h_name = r["home_name"] or "TBD"
                a_name = r["away_name"] or "TBD"
                ctk.CTkLabel(left_box, text=f"{h_name} vs {a_name}", font=ctk.CTkFont(size=12, weight="bold"), text_color=theme.TEXT_PRIMARY).pack(anchor="w")
                ctk.CTkLabel(left_box, text=f"Match #{r['match_number']} • {r['stage']}", font=ctk.CTkFont(size=10), text_color=theme.TEXT_MUTED).pack(anchor="w")

                right_box = ctk.CTkFrame(row, fg_color="transparent")
                right_box.pack(side="right", padx=10, pady=8)
                score_str = f"{r['home_score']} - {r['away_score']}"
                ctk.CTkLabel(right_box, text=score_str, font=ctk.CTkFont(size=14, weight="bold"), text_color=theme.ACCENT_GREEN_TEXT).pack(anchor="e")

        # 4. Bottom Section: Standings Preview & Recent Registrations
        bot_grid = ctk.CTkFrame(self, fg_color="transparent")
        bot_grid.pack(fill="x", padx=16, pady=(0, 20))
        bot_grid.columnconfigure(0, weight=1)
        bot_grid.columnconfigure(1, weight=1)

        # Standings Preview Card
        standings_card = ctk.CTkFrame(bot_grid, fg_color=theme.BG_CARD, corner_radius=10, border_color=theme.BORDER_COLOR, border_width=1)
        standings_card.grid(row=0, column=0, padx=(0, 8), sticky="nsew")

        s_hdr = ctk.CTkFrame(standings_card, fg_color="transparent")
        s_hdr.pack(fill="x", padx=16, pady=(14, 8))
        ctk.CTkLabel(s_hdr, text="Standings Preview", font=ctk.CTkFont(size=14, weight="bold"), text_color=theme.TEXT_PRIMARY).pack(side="left")
        ctk.CTkButton(s_hdr, text="Full Table", width=70, height=22, fg_color="transparent", hover_color=theme.BG_CARD_HOVER, text_color=theme.ACCENT_GREEN_TEXT, font=ctk.CTkFont(size=11), command=lambda: self.navigate("Points Table")).pack(side="right")

        all_standings = self.standings_calc.calculate_all_groups_standings()
        top_teams = []
        for g_name, rows in all_standings.items():
            for r in rows[:2]:  # Top 2 per group
                top_teams.append((g_name, r))

        if not top_teams:
            ctk.CTkLabel(standings_card, text="No standings data yet.", font=ctk.CTkFont(size=12), text_color=theme.TEXT_MUTED).pack(padx=16, pady=24)
        else:
            # Simple Mini Table
            tbl_hdr = ctk.CTkFrame(standings_card, fg_color="transparent")
            tbl_hdr.pack(fill="x", padx=14, pady=(2, 4))
            ctk.CTkLabel(tbl_hdr, text="Team", font=ctk.CTkFont(size=10, weight="bold"), text_color=theme.TEXT_MUTED, width=150, anchor="w").pack(side="left")
            ctk.CTkLabel(tbl_hdr, text="P", font=ctk.CTkFont(size=10, weight="bold"), text_color=theme.TEXT_MUTED, width=30).pack(side="left")
            ctk.CTkLabel(tbl_hdr, text="GD", font=ctk.CTkFont(size=10, weight="bold"), text_color=theme.TEXT_MUTED, width=35).pack(side="left")
            ctk.CTkLabel(tbl_hdr, text="PTS", font=ctk.CTkFont(size=10, weight="bold"), text_color=theme.TEXT_MUTED, width=40).pack(side="right")

            for g_name, s in top_teams[:5]:
                t_row = ctk.CTkFrame(standings_card, fg_color=theme.BG_INPUT, corner_radius=4)
                t_row.pack(fill="x", padx=14, pady=2)
                ctk.CTkLabel(t_row, text=f"{s.team_name} ({g_name})", font=ctk.CTkFont(size=11), text_color=theme.TEXT_PRIMARY, width=150, anchor="w").pack(side="left", padx=4)
                ctk.CTkLabel(t_row, text=str(s.played), font=ctk.CTkFont(size=11), text_color=theme.TEXT_SECONDARY, width=30).pack(side="left")
                gd_str = f"+{s.goal_difference}" if s.goal_difference > 0 else str(s.goal_difference)
                ctk.CTkLabel(t_row, text=gd_str, font=ctk.CTkFont(size=11), text_color=theme.TEXT_SECONDARY, width=35).pack(side="left")
                ctk.CTkLabel(t_row, text=str(s.points), font=ctk.CTkFont(size=11, weight="bold"), text_color=theme.ACCENT_GREEN_TEXT, width=40).pack(side="right", padx=4)

        # Recent Registrations Card
        regs_card = ctk.CTkFrame(bot_grid, fg_color=theme.BG_CARD, corner_radius=10, border_color=theme.BORDER_COLOR, border_width=1)
        regs_card.grid(row=0, column=1, padx=(8, 0), sticky="nsew")

        reg_hdr = ctk.CTkFrame(regs_card, fg_color="transparent")
        reg_hdr.pack(fill="x", padx=16, pady=(14, 8))
        ctk.CTkLabel(reg_hdr, text="Recent Registrations", font=ctk.CTkFont(size=14, weight="bold"), text_color=theme.TEXT_PRIMARY).pack(side="left")
        ctk.CTkButton(reg_hdr, text="View All", width=60, height=22, fg_color="transparent", hover_color=theme.BG_CARD_HOVER, text_color=theme.ACCENT_GREEN_TEXT, font=ctk.CTkFont(size=11), command=lambda: self.navigate("Registrations")).pack(side="right")

        recent_regs = self.db.execute_query("""
            SELECT id, participant_name, phone_number, team_name, registered_at, status
            FROM registrations
            ORDER BY id DESC
            LIMIT 5;
        """)

        if not recent_regs:
            ctk.CTkLabel(regs_card, text="No registrations recorded yet.", font=ctk.CTkFont(size=12), text_color=theme.TEXT_MUTED).pack(padx=16, pady=24)
        else:
            for r in recent_regs:
                row = ctk.CTkFrame(regs_card, fg_color=theme.BG_INPUT, corner_radius=4)
                row.pack(fill="x", padx=14, pady=2)
                
                left_box = ctk.CTkFrame(row, fg_color="transparent")
                left_box.pack(side="left", padx=8, pady=4)
                ctk.CTkLabel(left_box, text=r["team_name"], font=ctk.CTkFont(size=11, weight="bold"), text_color=theme.TEXT_PRIMARY).pack(anchor="w")
                ctk.CTkLabel(left_box, text=f"{r['participant_name']} • {r['phone_number']}", font=ctk.CTkFont(size=10), text_color=theme.TEXT_MUTED).pack(anchor="w")

                badge_bg, badge_fg = theme.get_status_colors(r["status"])
                badge = ctk.CTkLabel(row, text=r["status"], fg_color=badge_bg, text_color=badge_fg, corner_radius=4, font=ctk.CTkFont(size=10, weight="bold"), width=65, height=20)
                badge.pack(side="right", padx=8, pady=4)

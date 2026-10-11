"""
Backup and Restore management, data safety transactions,
and sample data generator for Minaram Cup Tournament Management System.
"""

import shutil
import sqlite3
import logging
from pathlib import Path
from datetime import datetime, timedelta
from typing import List, Dict, Any, Tuple

from app.database import Database

logger = logging.getLogger("minaram_cup.backup_service")


class BackupService:
    def __init__(self, db: Database, backup_dir: Optional[Path] = None):
        self.db = db
        self.backup_dir = backup_dir or (db.db_path.parent.parent / "backups")
        self.backup_dir.mkdir(parents=True, exist_ok=True)

    def create_backup(self, label: str = "") -> Path:
        """
        Create a live, atomic backup using SQLite's backup API.
        """
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        suffix = f"_{label.strip()}" if label.strip() else ""
        filename = f"minaram_cup_backup_{ts}{suffix}.db"
        dest_path = self.backup_dir / filename

        source_conn = self.db.get_connection()
        dest_conn = sqlite3.connect(str(dest_path))
        try:
            with dest_conn:
                source_conn.backup(dest_conn)
            logger.info(f"Database backup created successfully: {dest_path}")
        finally:
            dest_conn.close()
            source_conn.close()

        return dest_path

    def restore_backup(self, backup_file: Path) -> Tuple[bool, str]:
        """
        Restore SQLite database from backup.
        Takes a safety backup of the current database before restoring.
        """
        path = Path(backup_file)
        if not path.exists():
            return False, f"Backup file not found: {path}"

        # 1. Take safety backup
        try:
            self.create_backup(label="pre_restore_safety")
        except Exception as e:
            logger.warning(f"Failed to create pre-restore safety backup: {e}")

        # 2. Restore
        try:
            source_conn = sqlite3.connect(str(path))
            dest_conn = self.db.get_connection()
            with dest_conn:
                source_conn.backup(dest_conn)
            source_conn.close()
            dest_conn.close()
            logger.info(f"Database restored from {path}")
            return True, "Database restored successfully."
        except Exception as e:
            logger.error(f"Error restoring backup: {e}")
            return False, f"Restore failed: {str(e)}"

    def list_backups(self) -> List[Dict[str, Any]]:
        """List all available backup files sorted by creation date."""
        backups = []
        for f in self.backup_dir.glob("*.db"):
            stat = f.stat()
            backups.append({
                "filename": f.name,
                "path": str(f),
                "size_kb": round(stat.st_size / 1024, 2),
                "created_at": datetime.fromtimestamp(stat.st_mtime).strftime("%Y-%m-%d %H:%M:%S")
            })
        return sorted(backups, key=lambda b: b["created_at"], reverse=True)

    def reset_tournament_data(self) -> None:
        """Clear all tournament data (matches, audit logs, groups, teams, registrations)."""
        with self.db.transaction() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM match_audit_log;")
            cursor.execute("DELETE FROM matches;")
            cursor.execute("DELETE FROM registration_team_map;")
            cursor.execute("DELETE FROM teams;")
            cursor.execute("DELETE FROM groups;")
            cursor.execute("DELETE FROM registrations;")

    def generate_sample_tournament(self) -> None:
        """
        Populate the database with a realistic sample Minaram Cup tournament:
        8 teams, 2 groups, realistic fixtures, and completed match results with standings.
        """
        now = datetime.now()
        now_str = now.strftime("%Y-%m-%d %H:%M:%S")

        # 1. Clear existing
        self.reset_tournament_data()

        with self.db.transaction() as conn:
            cursor = conn.cursor()

            # Set settings
            cursor.execute("INSERT OR REPLACE INTO settings (key, value) VALUES ('tournament_name', 'Minaram Cup');")
            cursor.execute("INSERT OR REPLACE INTO settings (key, value) VALUES ('edition', '2026 Edition');")
            cursor.execute("INSERT OR REPLACE INTO settings (key, value) VALUES ('sport', 'Football');")
            cursor.execute("INSERT OR REPLACE INTO settings (key, value) VALUES ('format_type', 'Group Stage + Knockout');")
            cursor.execute("INSERT OR REPLACE INTO settings (key, value) VALUES ('win_points', '3');")
            cursor.execute("INSERT OR REPLACE INTO settings (key, value) VALUES ('draw_points', '1');")
            cursor.execute("INSERT OR REPLACE INTO settings (key, value) VALUES ('loss_points', '0');")
            cursor.execute("INSERT OR REPLACE INTO settings (key, value) VALUES ('num_groups', '2');")
            cursor.execute("INSERT OR REPLACE INTO settings (key, value) VALUES ('qualifiers_per_group', '2');")
            cursor.execute("INSERT OR REPLACE INTO settings (key, value) VALUES ('default_venue', 'Minaram Stadium');")

            # 2. Groups
            cursor.execute("INSERT INTO groups (name, display_order) VALUES ('Group A', 1);")
            g_a_id = cursor.lastrowid
            cursor.execute("INSERT INTO groups (name, display_order) VALUES ('Group B', 2);")
            g_b_id = cursor.lastrowid

            # 3. Teams & Registrations
            sample_teams_data = [
                # Group A
                ("Binladen Fc", "Vaishnav", "9746603975", g_a_id, 1),
                ("Red Star FC", "Ahammed", "9847123456", g_a_id, 0),
                ("Royal Challengers", "Farhan", "9745987654", g_a_id, 0),
                ("Black Panthers", "Rayan", "9495123789", g_a_id, 0),
                # Group B
                ("Malabar Warriors", "Shamil", "9562334455", g_b_id, 2),
                ("Cyber Strikers", "Adil", "9895667788", g_b_id, 0),
                ("Coastal Kings", "Nabeel", "9447112233", g_b_id, 0),
                ("Highland Rovers", "Suhail", "9633556677", g_b_id, 0),
            ]

            team_ids = []
            for t_name, cap, ph, g_id, seed in sample_teams_data:
                # Registration
                cursor.execute("""
                    INSERT INTO registrations (participant_name, phone_number, team_name, raw_message, registered_at, status, notes)
                    VALUES (?, ?, ?, 'Sample Registration Entry', ?, 'Confirmed', 'Verified sample entry');
                """, (cap, ph, t_name, now_str))
                reg_id = cursor.lastrowid

                # Team
                cursor.execute("""
                    INSERT INTO teams (name, captain_name, phone_number, status, group_id, seed, created_at)
                    VALUES (?, ?, ?, 'Confirmed', ?, ?, ?);
                """, (t_name, cap, ph, g_id, seed, now_str))
                t_id = cursor.lastrowid
                team_ids.append((t_name, t_id, g_id))

                cursor.execute("INSERT INTO registration_team_map (registration_id, team_id) VALUES (?, ?);", (reg_id, t_id))

        # Map team IDs
        teams_dict = {t_name: t_id for t_name, t_id, _ in team_ids}

        # 4. Create Group Matches & Completed Results
        # Group A matches
        start_d = (now + timedelta(days=1)).strftime("%Y-%m-%d")
        next_d = (now + timedelta(days=2)).strftime("%Y-%m-%d")

        matches_data = [
            # Group A Match 1 (Completed)
            (1, "Group Stage", g_a_id, 1, teams_dict["Binladen Fc"], teams_dict["Red Star FC"], start_d, "09:00", "Minaram Pitch 1", 3, 1, "Completed", teams_dict["Binladen Fc"]),
            # Group A Match 2 (Completed)
            (2, "Group Stage", g_a_id, 1, teams_dict["Royal Challengers"], teams_dict["Black Panthers"], start_d, "10:30", "Minaram Pitch 1", 2, 2, "Completed", None),
            # Group A Match 3 (Completed)
            (3, "Group Stage", g_a_id, 2, teams_dict["Binladen Fc"], teams_dict["Royal Challengers"], start_d, "14:00", "Minaram Pitch 1", 2, 0, "Completed", teams_dict["Binladen Fc"]),
            # Group A Match 4 (Scheduled)
            (4, "Group Stage", g_a_id, 2, teams_dict["Red Star FC"], teams_dict["Black Panthers"], start_d, "15:30", "Minaram Pitch 1", None, None, "Scheduled", None),
            # Group A Match 5 (Scheduled)
            (5, "Group Stage", g_a_id, 3, teams_dict["Black Panthers"], teams_dict["Binladen Fc"], next_d, "09:00", "Minaram Pitch 1", None, None, "Scheduled", None),
            # Group A Match 6 (Scheduled)
            (6, "Group Stage", g_a_id, 3, teams_dict["Red Star FC"], teams_dict["Royal Challengers"], next_d, "10:30", "Minaram Pitch 1", None, None, "Scheduled", None),

            # Group B Match 7 (Completed)
            (7, "Group Stage", g_b_id, 1, teams_dict["Malabar Warriors"], teams_dict["Cyber Strikers"], start_d, "09:00", "Minaram Pitch 2", 4, 1, "Completed", teams_dict["Malabar Warriors"]),
            # Group B Match 8 (Completed)
            (8, "Group Stage", g_b_id, 1, teams_dict["Coastal Kings"], teams_dict["Highland Rovers"], start_d, "10:30", "Minaram Pitch 2", 1, 0, "Completed", teams_dict["Coastal Kings"]),
            # Group B Match 9 (Scheduled)
            (9, "Group Stage", g_b_id, 2, teams_dict["Malabar Warriors"], teams_dict["Coastal Kings"], start_d, "14:00", "Minaram Pitch 2", None, None, "Scheduled", None),
            # Group B Match 10 (Scheduled)
            (10, "Group Stage", g_b_id, 2, teams_dict["Cyber Strikers"], teams_dict["Highland Rovers"], start_d, "15:30", "Minaram Pitch 2", None, None, "Scheduled", None),
            # Group B Match 11 (Scheduled)
            (11, "Group Stage", g_b_id, 3, teams_dict["Highland Rovers"], teams_dict["Malabar Warriors"], next_d, "09:00", "Minaram Pitch 2", None, None, "Scheduled", None),
            # Group B Match 12 (Scheduled)
            (12, "Group Stage", g_b_id, 3, teams_dict["Cyber Strikers"], teams_dict["Coastal Kings"], next_d, "10:30", "Minaram Pitch 2", None, None, "Scheduled", None),
        ]

        with self.db.transaction() as conn:
            cursor = conn.cursor()
            for m_num, stage, g_id, r_num, h_id, a_id, dt, tm, ven, h_sc, a_sc, stat, win_id in matches_data:
                comp_at = now_str if stat == "Completed" else ""
                cursor.execute("""
                    INSERT INTO matches (
                        match_number, stage, group_id, round_number,
                        home_team_id, away_team_id, scheduled_date, scheduled_time,
                        venue, home_score, away_score, status, winner_team_id, completed_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
                """, (m_num, stage, g_id, r_num, h_id, a_id, dt, tm, ven, h_sc, a_sc, stat, win_id, comp_at))
                m_id = cursor.lastrowid

                if stat == "Completed":
                    cursor.execute("""
                        INSERT INTO match_audit_log (
                            match_id, timestamp, action,
                            old_home_score, old_away_score, old_status,
                            new_home_score, new_away_score, new_status, notes
                        ) VALUES (?, ?, 'Result Recorded', NULL, NULL, 'Scheduled', ?, ?, 'Completed', 'Sample result');
                    """, (m_id, now_str, h_sc, a_sc))

            # Semi Finals (Knockout)
            ko_date = (now + timedelta(days=3)).strftime("%Y-%m-%d")
            cursor.execute("""
                INSERT INTO matches (match_number, stage, round_number, bracket_slot, scheduled_date, scheduled_time, venue, status, notes)
                VALUES (13, 'Semi-Final', 1, 'SF1', ?, '15:00', 'Minaram Stadium', 'Scheduled', '1st Group A vs 2nd Group B');
            """, (ko_date,))
            cursor.execute("""
                INSERT INTO matches (match_number, stage, round_number, bracket_slot, scheduled_date, scheduled_time, venue, status, notes)
                VALUES (14, 'Semi-Final', 1, 'SF2', ?, '17:00', 'Minaram Stadium', 'Scheduled', '1st Group B vs 2nd Group A');
            """, (ko_date,))

            final_date = (now + timedelta(days=4)).strftime("%Y-%m-%d")
            cursor.execute("""
                INSERT INTO matches (match_number, stage, round_number, bracket_slot, scheduled_date, scheduled_time, venue, status, notes)
                VALUES (15, 'Final', 2, 'F', ?, '16:00', 'Minaram Stadium', 'Scheduled', 'Winner SF1 vs Winner SF2');
            """, (final_date,))

        logger.info("Sample tournament generated successfully!")

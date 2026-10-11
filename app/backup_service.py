"""
Backup, Recovery, Data Safety Engine and Tournament Sample Generator
for Minaram Cup Tournament Management System.

Features:
- Live, atomic point-in-time SQLite backups via sqlite3 online backup API.
- Comprehensive JSON tournament state snapshots (settings, teams, groups, fixtures, standings, overrides, audit logs).
- Automated continuous zero-loss protection triggered on every data mutation.
- Dual-tier storage: backups/latest/ for instant recovery, backups/history/ with auto-pruning.
- Non-blocking thread worker with debouncing for smooth GUI performance.
"""

from __future__ import annotations

import json
import logging
import os
import platform
import queue
import shutil
import sqlite3
import subprocess
import threading
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Any, Tuple, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from app.database import Database

logger = logging.getLogger("minaram_cup.backup_service")


class BackupService:
    def __init__(
        self,
        db: Database,
        backup_dir: Optional[Path] = None,
        auto_backup: bool = True,
        background: bool = True,
        max_history: int = 50,
        debounce_seconds: float = 0.2
    ):
        self.db = db
        self.auto_backup_enabled = auto_backup
        self.background = background
        self.max_history = max(5, max_history)
        self.debounce_seconds = debounce_seconds

        if backup_dir:
            self.backup_dir = Path(backup_dir)
        else:
            if db.db_path.parent.name == "data":
                self.backup_dir = db.db_path.parent.parent / "backups"
            else:
                self.backup_dir = db.db_path.parent / "backups"

        self.backup_dir.mkdir(parents=True, exist_ok=True)
        self.history_dir = self.backup_dir / "history"
        self.history_dir.mkdir(parents=True, exist_ok=True)
        self.latest_dir = self.backup_dir / "latest"
        self.latest_dir.mkdir(parents=True, exist_ok=True)

        # Set reference on DB if not already set
        if not getattr(self.db, "_backup_service", None):
            self.db._backup_service = self

        # Initialize background worker if background mode enabled
        if self.auto_backup_enabled and self.background:
            self._init_worker()

        # Register with database
        if self.auto_backup_enabled:
            self.db.register_change_listener(self.handle_database_change)

    # ----------------------------------------------------
    # Background Worker & Debouncing Queue
    # ----------------------------------------------------
    def _init_worker(self) -> None:
        self._backup_queue: queue.Queue[str] = queue.Queue()
        self._stop_event = threading.Event()
        self._worker_thread = threading.Thread(
            target=self._worker_loop,
            name="BackupServiceWorker",
            daemon=True
        )
        self._worker_thread.start()

    def _worker_loop(self) -> None:
        while not self._stop_event.is_set():
            try:
                action = self._backup_queue.get(timeout=0.3)
            except queue.Empty:
                continue

            # Debounce: wait briefly to coalesce rapid successive writes
            if self.debounce_seconds > 0:
                time.sleep(self.debounce_seconds)

            # Drain any further actions that queued during debounce window
            while not self._backup_queue.empty():
                try:
                    action = self._backup_queue.get_nowait()
                    self._backup_queue.task_done()
                except queue.Empty:
                    break

            try:
                self.create_auto_backup(action_label=action)
            except Exception as e:
                logger.error(f"Auto-backup worker failed to create backup: {e}", exc_info=True)
            finally:
                self._backup_queue.task_done()

    def handle_database_change(self, action: str = "change") -> None:
        """Callback invoked by Database whenever committed changes occur."""
        if not self.auto_backup_enabled:
            return

        if not self.background:
            try:
                self.create_auto_backup(action_label=action)
            except Exception as e:
                logger.error(f"Synchronous auto-backup failed: {e}", exc_info=True)
        else:
            if hasattr(self, "_backup_queue"):
                self._backup_queue.put(action)

    def flush(self, timeout: float = 5.0) -> None:
        """Block until all queued backups have finished writing to disk."""
        if hasattr(self, "_backup_queue"):
            self._backup_queue.join()

    def stop(self) -> None:
        """Cleanly terminate the worker thread and flush pending backups."""
        if hasattr(self, "_stop_event"):
            self._stop_event.set()
        self.flush()
        if hasattr(self, "_worker_thread") and self._worker_thread.is_alive():
            self._worker_thread.join(timeout=1.5)

    # ----------------------------------------------------
    # Primary Auto-Backup Engine
    # ----------------------------------------------------
    def create_auto_backup(self, action_label: str = "change", update_latest: bool = True) -> Dict[str, Path]:
        """
        Create a comprehensive point-in-time snapshot consisting of:
        1. An atomic, online SQLite clone (.db) in backups/history/
        2. A structured JSON state snapshot (.json) in backups/history/
        3. Pointers in backups/latest/ (if update_latest is True)
        4. Pruned rolling archives
        5. Manifest log updates and live broadcaster event
        """
        now = datetime.now()
        ts = now.strftime("%Y%m%d_%H%M%S")
        clean_action = "".join(c if (c.isalnum() or c in "_-") else "_" for c in action_label.strip())
        if not clean_action:
            clean_action = "change"

        db_dest = self.history_dir / f"minaram_backup_{ts}_{clean_action}.db"
        json_dest = self.history_dir / f"minaram_snapshot_{ts}_{clean_action}.json"

        # 1. SQLite atomic online backup
        source_conn = self.db.get_connection()
        dest_conn = sqlite3.connect(str(db_dest))
        try:
            with dest_conn:
                source_conn.backup(dest_conn)
        finally:
            dest_conn.close()
            source_conn.close()

        # 2. JSON snapshot export
        self.export_state_json(dest_path=json_dest, action_label=clean_action)

        # 3. Update 'latest' folder pointers if requested
        latest_db = self.latest_dir / "minaram_cup_latest.db"
        latest_json = self.latest_dir / "minaram_cup_latest_state.json"
        if update_latest:
            try:
                shutil.copy2(str(db_dest), str(latest_db))
                shutil.copy2(str(json_dest), str(latest_json))
            except Exception as e:
                logger.warning(f"Failed to update latest pointers: {e}")

        # 4. Prune history beyond max_history
        self._prune_history()

        # 5. Update Manifest
        manifest_data = self._update_manifest(db_dest, json_dest, clean_action, now)

        # 6. Notify SSE / broadcaster
        try:
            from app.events import broadcaster
            broadcaster.broadcast_from_thread(
                "backup_created",
                data={
                    "filename": db_dest.name,
                    "action": clean_action,
                    "timestamp": now.strftime("%Y-%m-%d %H:%M:%S"),
                    "total_backups": manifest_data.get("total_backups_count", 0)
                }
            )
        except Exception:
            pass

        logger.info(f"Auto-backup snapshot saved [{clean_action}]: {db_dest.name} & {json_dest.name}")

        return {
            "db": db_dest,
            "json": json_dest,
            "latest_db": latest_db,
            "latest_json": latest_json
        }

    def create_backup(self, label: str = "") -> Path:
        """
        Create a live atomic backup. Supports explicit manual calls
        and creates both SQLite clone and JSON export.
        """
        clean_lbl = label.strip() or "manual"
        update_latest = not clean_lbl.startswith("pre_restore")
        res = self.create_auto_backup(action_label=clean_lbl, update_latest=update_latest)
        return res["db"]

    # ----------------------------------------------------
    # Comprehensive JSON Tournament State Export
    # ----------------------------------------------------
    def export_state_json(self, dest_path: Optional[Path] = None, action_label: str = "") -> Path:
        """
        Export complete tournament state to a portable, human-readable JSON snapshot.
        Includes settings, registrations, teams, groups, fixtures/matches, standings,
        overrides, and audit log.
        """
        if dest_path is None:
            ts = datetime.now().strftime("%Y%m%d_%H%M%S")
            suffix = f"_{action_label.strip()}" if action_label.strip() else ""
            dest_path = self.history_dir / f"minaram_snapshot_{ts}{suffix}.json"

        dest_path = Path(dest_path)
        dest_path.parent.mkdir(parents=True, exist_ok=True)

        # 1. Settings
        settings_dict = self.db.get_all_settings()

        # 2. Groups
        groups_rows = self.db.execute_query(
            "SELECT id, name, display_order FROM groups ORDER BY display_order ASC, id ASC;"
        )
        groups = [dict(r) for r in groups_rows]

        # 3. Teams
        team_rows = self.db.execute_query("""
            SELECT t.id, t.name, t.captain_name, t.phone_number, t.status,
                   t.group_id, g.name AS group_name, t.seed, t.logo_path, t.notes, t.created_at
            FROM teams t
            LEFT JOIN groups g ON t.group_id = g.id
            ORDER BY t.id ASC;
        """)
        teams = [dict(r) for r in team_rows]

        # 4. Registrations
        reg_rows = self.db.execute_query("""
            SELECT id, participant_name, phone_number, team_name, raw_message,
                   registered_at, status, notes
            FROM registrations
            ORDER BY id ASC;
        """)
        registrations = [dict(r) for r in reg_rows]

        # 5. Registration Team Map
        map_rows = self.db.execute_query("SELECT registration_id, team_id FROM registration_team_map;")
        reg_team_map = [dict(r) for r in map_rows]

        # 6. Matches
        match_rows = self.db.execute_query("""
            SELECT m.id, m.match_number, m.stage, m.group_id, g.name AS group_name,
                   m.round_number, m.bracket_slot,
                   m.home_team_id, ht.name AS home_team_name, ht.phone_number AS home_phone,
                   m.away_team_id, at.name AS away_team_name, at.phone_number AS away_phone,
                   m.scheduled_date, m.scheduled_time, m.venue,
                   m.home_score, m.away_score, m.home_penalty, m.away_penalty,
                   m.status, m.winner_team_id, wt.name AS winner_name,
                   m.completed_at, m.notes
            FROM matches m
            LEFT JOIN groups g ON m.group_id = g.id
            LEFT JOIN teams ht ON m.home_team_id = ht.id
            LEFT JOIN teams at ON m.away_team_id = at.id
            LEFT JOIN teams wt ON m.winner_team_id = wt.id
            ORDER BY m.match_number ASC, m.id ASC;
        """)
        matches = [dict(r) for r in match_rows]

        # 7. Standings
        standings_data: Dict[str, Any] = {}
        try:
            from app.standings import StandingsCalculator
            sc = StandingsCalculator(self.db)
            for g in groups:
                g_standings = sc.calculate_group_standings(group_id=g["id"])
                standings_data[g["name"]] = [
                    {
                        "team_id": r.team_id,
                        "team_name": r.team_name,
                        "group_id": r.group_id,
                        "group_name": r.group_name,
                        "played": r.played,
                        "won": r.won,
                        "drawn": r.drawn,
                        "lost": r.lost,
                        "goals_for": r.goals_for,
                        "goals_against": r.goals_against,
                        "goal_difference": r.goal_difference,
                        "points": r.points,
                        "rank": r.rank,
                        "is_qualified": r.is_qualified,
                        "form": r.form,
                        "has_override": r.has_override,
                        "override_notes": r.override_notes
                    }
                    for r in g_standings
                ]
        except Exception as e:
            logger.warning(f"Could not compute standings for JSON snapshot: {e}")

        # 8. Standings Overrides
        try:
            override_rows = self.db.execute_query("""
                SELECT o.team_id, t.name AS team_name, o.played, o.won, o.drawn, o.lost,
                       o.goals_for, o.goals_against, o.points, o.notes, o.updated_at
                FROM standings_overrides o
                LEFT JOIN teams t ON o.team_id = t.id;
            """)
            standings_overrides = [dict(r) for r in override_rows]
        except Exception:
            standings_overrides = []

        # 9. Match Audit Log
        try:
            audit_rows = self.db.execute_query("""
                SELECT id, match_id, timestamp, action,
                       old_home_score, old_away_score, old_status,
                       new_home_score, new_away_score, new_status, notes
                FROM match_audit_log
                ORDER BY id DESC LIMIT 200;
            """)
            audit_log = [dict(r) for r in audit_rows]
        except Exception:
            audit_log = []

        completed_matches = sum(1 for m in matches if m.get("status") in ("Completed", "Walkover"))

        state_payload = {
            "version": "2.0.0",
            "exported_at": datetime.now().isoformat(),
            "action_trigger": action_label or "snapshot",
            "summary": {
                "tournament_name": settings_dict.get("tournament_name", "Minaram Cup"),
                "edition": settings_dict.get("edition", "2026 Edition"),
                "sport": settings_dict.get("sport", "Football"),
                "total_registrations": len(registrations),
                "total_teams": len(teams),
                "total_groups": len(groups),
                "total_matches": len(matches),
                "completed_matches": completed_matches,
                "scheduled_matches": len(matches) - completed_matches,
            },
            "settings": settings_dict,
            "groups": groups,
            "teams": teams,
            "registrations": registrations,
            "registration_team_map": reg_team_map,
            "matches": matches,
            "standings": standings_data,
            "standings_overrides": standings_overrides,
            "audit_log": audit_log
        }

        temp_dest = dest_path.with_suffix(".tmp")
        with open(temp_dest, "w", encoding="utf-8") as f:
            json.dump(state_payload, f, indent=2, ensure_ascii=False)
        temp_dest.replace(dest_path)

        return dest_path

    # ----------------------------------------------------
    # Pruning & Manifest Management
    # ----------------------------------------------------
    def _prune_history(self) -> None:
        """Prune oldest history files beyond max_history threshold."""
        try:
            db_files = sorted(self.history_dir.glob("minaram_backup_*.db"), key=lambda p: p.stat().st_mtime)
            if len(db_files) > self.max_history:
                excess = len(db_files) - self.max_history
                for old_db in db_files[:excess]:
                    old_stem = old_db.stem.replace("minaram_backup_", "minaram_snapshot_")
                    old_json = self.history_dir / f"{old_stem}.json"
                    try:
                        old_db.unlink(missing_ok=True)
                        old_json.unlink(missing_ok=True)
                    except Exception as e:
                        logger.warning(f"Could not remove pruned backup {old_db.name}: {e}")
        except Exception as e:
            logger.warning(f"History pruning error: {e}")

    def _update_manifest(self, db_dest: Path, json_dest: Path, action: str, dt: datetime) -> Dict[str, Any]:
        """Update manifest log of all snapshots."""
        manifest_path = self.backup_dir / "backups_manifest.json"
        manifest = {
            "last_backup_time": dt.strftime("%Y-%m-%d %H:%M:%S"),
            "total_backups_count": 0,
            "latest": {
                "db_file": db_dest.name,
                "json_file": json_dest.name,
                "action": action,
                "timestamp": dt.strftime("%Y-%m-%d %H:%M:%S"),
                "db_size_kb": round(db_dest.stat().st_size / 1024, 2) if db_dest.exists() else 0,
                "json_size_kb": round(json_dest.stat().st_size / 1024, 2) if json_dest.exists() else 0,
            },
            "history": []
        }

        if manifest_path.exists():
            try:
                with open(manifest_path, "r", encoding="utf-8") as f:
                    existing = json.load(f)
                    manifest["history"] = existing.get("history", [])
            except Exception:
                pass

        entry = {
            "timestamp": dt.strftime("%Y-%m-%d %H:%M:%S"),
            "action": action,
            "db_file": db_dest.name,
            "json_file": json_dest.name,
            "db_size_kb": round(db_dest.stat().st_size / 1024, 2) if db_dest.exists() else 0,
            "json_size_kb": round(json_dest.stat().st_size / 1024, 2) if json_dest.exists() else 0,
        }

        manifest["history"].insert(0, entry)
        manifest["history"] = manifest["history"][:self.max_history]
        manifest["total_backups_count"] = len(manifest["history"])

        try:
            temp_manifest = manifest_path.with_suffix(".tmp")
            with open(temp_manifest, "w", encoding="utf-8") as f:
                json.dump(manifest, f, indent=2)
            temp_manifest.replace(manifest_path)
        except Exception as e:
            logger.warning(f"Could not write backups manifest: {e}")

        return manifest

    # ----------------------------------------------------
    # Restore Operations
    # ----------------------------------------------------
    def restore_backup(self, backup_file: Path) -> Tuple[bool, str]:
        """
        Restore SQLite database from backup file.
        Takes a safety backup of the current database before restoring,
        suppresses mutations during restore, and creates a post-restore snapshot.
        """
        path = Path(backup_file).resolve()
        if not path.exists():
            return False, f"Backup file not found: {path}"

        # 1. Take safety backup (pre_restore_safety will not overwrite latest pointers)
        try:
            self.create_backup(label="pre_restore_safety")
        except Exception as e:
            logger.warning(f"Failed to create pre-restore safety backup: {e}")

        # 2. Suppress change notifications during restore
        self.db._suppress_change_notifications = True
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
        finally:
            self.db._suppress_change_notifications = False
            try:
                self.create_auto_backup(action_label="post_restore", update_latest=True)
            except Exception:
                pass

    def restore_from_latest(self) -> Tuple[bool, str]:
        """1-click restore directly from the latest snapshot pointer."""
        latest_db = self.latest_dir / "minaram_cup_latest.db"
        if latest_db.exists():
            return self.restore_backup(latest_db)

        backups = self.list_backups()
        if not backups:
            return False, "No backup snapshots found to restore from."
        newest = backups[0]["path"]
        return self.restore_backup(Path(newest))

    # ----------------------------------------------------
    # Listing & Querying Backups
    # ----------------------------------------------------
    def list_backups(self) -> List[Dict[str, Any]]:
        """
        List all available backups across latest/, history/, and root backups/,
        sorted chronologically descending with metadata.
        """
        results: List[Dict[str, Any]] = []
        seen_paths = set()

        # Check latest
        latest_db = self.latest_dir / "minaram_cup_latest.db"
        if latest_db.exists():
            st = latest_db.stat()
            latest_json = self.latest_dir / "minaram_cup_latest_state.json"
            results.append({
                "filename": latest_db.name,
                "path": str(latest_db),
                "size_kb": round(st.st_size / 1024, 2),
                "created_at": datetime.fromtimestamp(st.st_mtime).strftime("%Y-%m-%d %H:%M:%S"),
                "action": "Latest Active Snapshot",
                "is_latest": True,
                "has_json": latest_json.exists(),
                "json_path": str(latest_json) if latest_json.exists() else None,
                "mtime": st.st_mtime
            })
            seen_paths.add(latest_db.resolve())

        # Check history/
        if self.history_dir.exists():
            for f in self.history_dir.glob("*.db"):
                if f.resolve() in seen_paths:
                    continue
                st = f.stat()
                json_f = self.history_dir / (f.stem.replace("minaram_backup_", "minaram_snapshot_") + ".json")
                parts = f.stem.split("_", 3)
                action_label = parts[3] if len(parts) > 3 else "auto_change"
                results.append({
                    "filename": f.name,
                    "path": str(f),
                    "size_kb": round(st.st_size / 1024, 2),
                    "created_at": datetime.fromtimestamp(st.st_mtime).strftime("%Y-%m-%d %H:%M:%S"),
                    "action": action_label.replace("_", " ").title(),
                    "is_latest": False,
                    "has_json": json_f.exists(),
                    "json_path": str(json_f) if json_f.exists() else None,
                    "mtime": st.st_mtime
                })
                seen_paths.add(f.resolve())

        # Check root backup_dir for legacy backups
        for f in self.backup_dir.glob("*.db"):
            if f.resolve() in seen_paths:
                continue
            st = f.stat()
            results.append({
                "filename": f.name,
                "path": str(f),
                "size_kb": round(st.st_size / 1024, 2),
                "created_at": datetime.fromtimestamp(st.st_mtime).strftime("%Y-%m-%d %H:%M:%S"),
                "action": "Legacy Backup",
                "is_latest": False,
                "has_json": False,
                "json_path": None,
                "mtime": st.st_mtime
            })
            seen_paths.add(f.resolve())

        return sorted(results, key=lambda b: (not b["is_latest"], -b["mtime"]))

    def get_backup_stats(self) -> Dict[str, Any]:
        """Summary statistics of backups."""
        backups = self.list_backups()
        history_cnt = len(list(self.history_dir.glob("*.db")))
        latest_db = self.latest_dir / "minaram_cup_latest.db"

        latest_time = "Never"
        latest_size_kb = 0
        if latest_db.exists():
            st = latest_db.stat()
            latest_time = datetime.fromtimestamp(st.st_mtime).strftime("%Y-%m-%d %H:%M:%S")
            latest_size_kb = round(st.st_size / 1024, 2)
        elif backups:
            latest_time = backups[0]["created_at"]
            latest_size_kb = backups[0]["size_kb"]

        return {
            "total_backups": len(backups),
            "history_count": history_cnt,
            "latest_time": latest_time,
            "latest_file": latest_db.name if latest_db.exists() else (backups[0]["filename"] if backups else "None"),
            "latest_size_kb": latest_size_kb,
            "auto_backup_active": self.auto_backup_enabled
        }

    # ----------------------------------------------------
    # Sample Tournament Generator & Reset Operations
    # ----------------------------------------------------
    def reset_tournament_data(self) -> None:
        """Clear all tournament data (matches, audit logs, groups, teams, registrations)."""
        with self.db.transaction(action="reset_tournament_data") as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM match_audit_log;")
            cursor.execute("DELETE FROM matches;")
            cursor.execute("DELETE FROM registration_team_map;")
            cursor.execute("DELETE FROM teams;")
            cursor.execute("DELETE FROM groups;")
            cursor.execute("DELETE FROM registrations;")
            cursor.execute("DELETE FROM standings_overrides;")

    def generate_sample_tournament(self) -> None:
        """
        Populate the database with a realistic sample Minaram Cup tournament:
        8 teams, 2 groups, realistic fixtures, and completed match results with standings.
        """
        now = datetime.now()
        now_str = now.strftime("%Y-%m-%d %H:%M:%S")

        self.reset_tournament_data()

        with self.db.transaction(action="generate_sample_tournament") as conn:
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

            # Groups
            cursor.execute("INSERT INTO groups (name, display_order) VALUES ('Group A', 1);")
            g_a_id = cursor.lastrowid
            cursor.execute("INSERT INTO groups (name, display_order) VALUES ('Group B', 2);")
            g_b_id = cursor.lastrowid

            # Teams & Registrations
            sample_teams_data = [
                ("Binladen Fc", "Vaishnav", "9746603975", g_a_id, 1),
                ("Red Star FC", "Ahammed", "9847123456", g_a_id, 0),
                ("Royal Challengers", "Farhan", "9745987654", g_a_id, 0),
                ("Black Panthers", "Rayan", "9495123789", g_a_id, 0),
                ("Malabar Warriors", "Shamil", "9562334455", g_b_id, 2),
                ("Cyber Strikers", "Adil", "9895667788", g_b_id, 0),
                ("Coastal Kings", "Nabeel", "9447112233", g_b_id, 0),
                ("Highland Rovers", "Suhail", "9633556677", g_b_id, 0),
            ]

            team_ids = []
            for t_name, cap, ph, g_id, seed in sample_teams_data:
                cursor.execute("""
                    INSERT INTO registrations (participant_name, phone_number, team_name, raw_message, registered_at, status, notes)
                    VALUES (?, ?, ?, 'Sample Registration Entry', ?, 'Confirmed', 'Verified sample entry');
                """, (cap, ph, t_name, now_str))
                reg_id = cursor.lastrowid

                cursor.execute("""
                    INSERT INTO teams (name, captain_name, phone_number, status, group_id, seed, created_at)
                    VALUES (?, ?, ?, 'Confirmed', ?, ?, ?);
                """, (t_name, cap, ph, g_id, seed, now_str))
                t_id = cursor.lastrowid
                team_ids.append((t_name, t_id, g_id))

                cursor.execute("INSERT INTO registration_team_map (registration_id, team_id) VALUES (?, ?);", (reg_id, t_id))

            teams_dict = {t_name: t_id for t_name, t_id, _ in team_ids}

            # Group matches
            start_d = (now + timedelta(days=1)).strftime("%Y-%m-%d")
            next_d = (now + timedelta(days=2)).strftime("%Y-%m-%d")

            matches_data = [
                (1, "Group Stage", g_a_id, 1, teams_dict["Binladen Fc"], teams_dict["Red Star FC"], start_d, "09:00", "Minaram Pitch 1", 3, 1, "Completed", teams_dict["Binladen Fc"]),
                (2, "Group Stage", g_a_id, 1, teams_dict["Royal Challengers"], teams_dict["Black Panthers"], start_d, "10:30", "Minaram Pitch 1", 2, 2, "Completed", None),
                (3, "Group Stage", g_a_id, 2, teams_dict["Binladen Fc"], teams_dict["Royal Challengers"], start_d, "14:00", "Minaram Pitch 1", 2, 0, "Completed", teams_dict["Binladen Fc"]),
                (4, "Group Stage", g_a_id, 2, teams_dict["Red Star FC"], teams_dict["Black Panthers"], start_d, "15:30", "Minaram Pitch 1", None, None, "Scheduled", None),
                (5, "Group Stage", g_a_id, 3, teams_dict["Black Panthers"], teams_dict["Binladen Fc"], next_d, "09:00", "Minaram Pitch 1", None, None, "Scheduled", None),
                (6, "Group Stage", g_a_id, 3, teams_dict["Red Star FC"], teams_dict["Royal Challengers"], next_d, "10:30", "Minaram Pitch 1", None, None, "Scheduled", None),
                (7, "Group Stage", g_b_id, 1, teams_dict["Malabar Warriors"], teams_dict["Cyber Strikers"], start_d, "09:00", "Minaram Pitch 2", 4, 1, "Completed", teams_dict["Malabar Warriors"]),
                (8, "Group Stage", g_b_id, 1, teams_dict["Coastal Kings"], teams_dict["Highland Rovers"], start_d, "10:30", "Minaram Pitch 2", 1, 0, "Completed", teams_dict["Coastal Kings"]),
                (9, "Group Stage", g_b_id, 2, teams_dict["Malabar Warriors"], teams_dict["Coastal Kings"], start_d, "14:00", "Minaram Pitch 2", None, None, "Scheduled", None),
                (10, "Group Stage", g_b_id, 2, teams_dict["Cyber Strikers"], teams_dict["Highland Rovers"], start_d, "15:30", "Minaram Pitch 2", None, None, "Scheduled", None),
                (11, "Group Stage", g_b_id, 3, teams_dict["Highland Rovers"], teams_dict["Malabar Warriors"], next_d, "09:00", "Minaram Pitch 2", None, None, "Scheduled", None),
                (12, "Group Stage", g_b_id, 3, teams_dict["Cyber Strikers"], teams_dict["Coastal Kings"], next_d, "10:30", "Minaram Pitch 2", None, None, "Scheduled", None),
            ]

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

            # Semi Finals
            ko_date = (now + timedelta(days=3)).strftime("%Y-%m-%d")
            cursor.execute("""
                INSERT INTO matches (match_number, stage, round_number, bracket_slot, scheduled_date, scheduled_time, venue, status, notes)
                VALUES (13, 'Semi-Final', 1, 'SF1', ?, '15:00', 'Minaram Stadium', 'Scheduled', '1st Group A vs 2nd Group B');
            """, (ko_date,))
            cursor.execute("""
                INSERT INTO matches (match_number, stage, round_number, bracket_slot, scheduled_date, scheduled_time, venue, status, notes)
                VALUES (14, 'Semi-Final', 1, 'SF2', ?, '17:00', 'Minaram Stadium', 'Scheduled', '1st Group B vs 2nd Group A');
            """, (ko_date,))

            # Final
            final_date = (now + timedelta(days=4)).strftime("%Y-%m-%d")
            cursor.execute("""
                INSERT INTO matches (match_number, stage, round_number, bracket_slot, scheduled_date, scheduled_time, venue, status, notes)
                VALUES (15, 'Final', 2, 'F', ?, '16:00', 'Minaram Stadium', 'Scheduled', 'Winner SF1 vs Winner SF2');
            """, (final_date,))

        logger.info("Sample tournament generated successfully!")

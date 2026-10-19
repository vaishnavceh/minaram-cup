"""
SQLite database engine and transaction manager for Minaram Cup Tournament Management System.
"""

import sqlite3
import os
import logging
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Dict, Any, Tuple
from contextlib import contextmanager

logger = logging.getLogger("minaram_cup.database")

DEFAULT_DB_PATH = Path(__file__).resolve().parent.parent / "data" / "minaram_cup.db"


class Database:
    def __init__(self, db_path: Optional[Path] = None, enable_auto_backup: bool = True):
        self.db_path = Path(db_path) if db_path else DEFAULT_DB_PATH
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._change_listeners: List[Any] = []
        self._suppress_change_notifications: bool = True
        self._in_transaction: bool = False
        self._backup_service = None

        self.init_db()
        self._suppress_change_notifications = False

        if enable_auto_backup:
            self.init_auto_backup()

    def register_change_listener(self, listener) -> None:
        """Register a callback to be notified when data modifications are committed."""
        if listener not in self._change_listeners:
            self._change_listeners.append(listener)

    def unregister_change_listener(self, listener) -> None:
        """Unregister an existing change listener callback."""
        if listener in self._change_listeners:
            self._change_listeners.remove(listener)

    def notify_change(self, action: str = "change") -> None:
        """Notify all registered change listeners of a database mutation."""
        if self._suppress_change_notifications:
            return
        for listener in list(self._change_listeners):
            try:
                listener(action)
            except Exception as e:
                logger.error(f"Error in database change listener: {e}", exc_info=True)

    def init_auto_backup(self) -> None:
        """Initialize and link the automated zero-loss backup service."""
        try:
            from app.backup_service import BackupService
            if not self._backup_service:
                self._backup_service = BackupService(self, auto_backup=True)
        except Exception as e:
            logger.warning(f"Could not initialize auto backup on database: {e}")

    def get_backup_service(self):
        """Retrieve the linked backup service or initialize it."""
        if not self._backup_service:
            self.init_auto_backup()
        return self._backup_service

    def close(self) -> None:
        """Close database and shutdown active backup workers."""
        if self._backup_service:
            try:
                self._backup_service.stop()
            except Exception:
                pass

    def get_connection(self) -> sqlite3.Connection:
        """Create and configure a SQLite database connection."""
        conn = sqlite3.connect(
            str(self.db_path),
            timeout=15.0,
            detect_types=sqlite3.PARSE_DECLTYPES,
            check_same_thread=False
        )
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON;")
        conn.execute("PRAGMA journal_mode = WAL;")
        conn.execute("PRAGMA synchronous = NORMAL;")
        conn.execute("PRAGMA cache_size = -2000;")
        conn.execute("PRAGMA temp_store = MEMORY;")
        return conn

    @contextmanager
    def transaction(self, action: str = "change"):
        """Context manager for atomic database transactions with automatic rollback and mutation notification."""
        conn = self.get_connection()
        start_changes = conn.total_changes
        was_in_tx = self._in_transaction
        self._in_transaction = True
        changes_occurred = False
        try:
            yield conn
            conn.commit()
            changes_occurred = (conn.total_changes > start_changes)
        except Exception as e:
            conn.rollback()
            logger.error(f"Transaction rolled back due to error: {e}")
            raise
        finally:
            self._in_transaction = was_in_tx
            conn.close()

        if not was_in_tx and changes_occurred and not self._suppress_change_notifications:
            self.notify_change(action)

    def execute_query(self, query: str, params: Tuple = ()) -> List[sqlite3.Row]:
        """Execute a read query and return all rows."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, params)
            return cursor.fetchall()

    def execute_one(self, query: str, params: Tuple = ()) -> Optional[sqlite3.Row]:
        """Execute a read query and return the first row or None."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, params)
            return cursor.fetchone()

    def execute_non_query(self, query: str, params: Tuple = (), action: str = "data_updated") -> int:
        """Execute an INSERT/UPDATE/DELETE query and return the lastrowid or rowcount."""
        with self.transaction(action=action) as conn:
            cursor = conn.cursor()
            cursor.execute(query, params)
            return cursor.lastrowid

    def execute_many(self, query: str, seq_of_params: List[Tuple], action: str = "batch_data_updated") -> int:
        """Execute batch operations in a single transaction."""
        with self.transaction(action=action) as conn:
            cursor = conn.cursor()
            cursor.executemany(query, seq_of_params)
            return cursor.rowcount

    def init_db(self) -> None:
        """Initialize database schema, indexes, and default tournament configurations."""
        with self.transaction() as conn:
            cursor = conn.cursor()

            # 1. Settings Table
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS settings (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL
            );
            """)

            # 2. Registrations Table
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS registrations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                participant_name TEXT NOT NULL,
                phone_number TEXT NOT NULL,
                team_name TEXT NOT NULL,
                raw_message TEXT,
                registered_at TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'Pending',
                notes TEXT DEFAULT ''
            );
            """)
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_reg_phone ON registrations(phone_number);")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_reg_team ON registrations(team_name);")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_reg_status ON registrations(status);")

            # 3. Groups Table
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS groups (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE NOT NULL,
                display_order INTEGER DEFAULT 0
            );
            """)

            # 4. Teams Table
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS teams (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE NOT NULL,
                captain_name TEXT DEFAULT '',
                phone_number TEXT DEFAULT '',
                status TEXT NOT NULL DEFAULT 'Confirmed',
                group_id INTEGER REFERENCES groups(id) ON DELETE SET NULL,
                seed INTEGER DEFAULT 0,
                logo_path TEXT DEFAULT '',
                notes TEXT DEFAULT '',
                created_at TEXT NOT NULL
            );
            """)
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_teams_group ON teams(group_id);")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_teams_name ON teams(name);")

            # 5. Registration to Team Map
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS registration_team_map (
                registration_id INTEGER UNIQUE REFERENCES registrations(id) ON DELETE CASCADE,
                team_id INTEGER REFERENCES teams(id) ON DELETE CASCADE,
                PRIMARY KEY (registration_id, team_id)
            );
            """)

            # 6. Matches Table
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS matches (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                match_number INTEGER NOT NULL,
                stage TEXT NOT NULL DEFAULT 'Group Stage',
                group_id INTEGER REFERENCES groups(id) ON DELETE SET NULL,
                round_number INTEGER DEFAULT 1,
                bracket_slot TEXT DEFAULT '',
                home_team_id INTEGER REFERENCES teams(id) ON DELETE RESTRICT,
                away_team_id INTEGER REFERENCES teams(id) ON DELETE RESTRICT,
                scheduled_date TEXT DEFAULT '',
                scheduled_end_date TEXT DEFAULT '',
                scheduled_time TEXT DEFAULT '',
                venue TEXT DEFAULT 'Minaram Stadium',
                home_score INTEGER DEFAULT NULL,
                away_score INTEGER DEFAULT NULL,
                home_penalty INTEGER DEFAULT NULL,
                away_penalty INTEGER DEFAULT NULL,
                status TEXT NOT NULL DEFAULT 'Scheduled',
                winner_team_id INTEGER REFERENCES teams(id) ON DELETE SET NULL,
                notes TEXT DEFAULT '',
                completed_at TEXT DEFAULT ''
            );
            """)
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_matches_stage ON matches(stage);")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_matches_group ON matches(group_id);")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_matches_teams ON matches(home_team_id, away_team_id);")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_matches_status ON matches(status);")

            # Migration: Ensure scheduled_end_date exists in matches
            match_cols = [r[1] for r in cursor.execute("PRAGMA table_info(matches);").fetchall()]
            if "scheduled_end_date" not in match_cols:
                cursor.execute("ALTER TABLE matches ADD COLUMN scheduled_end_date TEXT DEFAULT '';")

            # 7. Match Audit Log Table
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS match_audit_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                match_id INTEGER NOT NULL REFERENCES matches(id) ON DELETE CASCADE,
                timestamp TEXT NOT NULL,
                action TEXT NOT NULL,
                old_home_score INTEGER,
                old_away_score INTEGER,
                old_status TEXT,
                new_home_score INTEGER,
                new_away_score INTEGER,
                new_status TEXT,
                notes TEXT DEFAULT ''
            );
            """)
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_audit_match ON match_audit_log(match_id);")

            # 8. Standings Overrides Table (Points table manual edits)
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS standings_overrides (
                team_id INTEGER PRIMARY KEY REFERENCES teams(id) ON DELETE CASCADE,
                played INTEGER DEFAULT NULL,
                won INTEGER DEFAULT NULL,
                drawn INTEGER DEFAULT NULL,
                lost INTEGER DEFAULT NULL,
                goals_for INTEGER DEFAULT NULL,
                goals_against INTEGER DEFAULT NULL,
                points INTEGER DEFAULT NULL,
                notes TEXT DEFAULT '',
                updated_at TEXT NOT NULL
            );
            """)

            # 9. Knockout Snapshots (Predicted tournament snapshots)
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS knockout_snapshots (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                version TEXT UNIQUE NOT NULL,
                created_at TEXT NOT NULL,
                standings_hash TEXT NOT NULL,
                draw_method TEXT NOT NULL DEFAULT 'seeded',
                is_provisional INTEGER NOT NULL DEFAULT 1,
                is_current INTEGER NOT NULL DEFAULT 1,
                direct_qualifiers_json TEXT NOT NULL,
                fixtures_json TEXT NOT NULL,
                notes TEXT DEFAULT ''
            );
            """)
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_ko_snap_curr ON knockout_snapshots(is_current);")

            # 10. Knockout Official Fixtures (Confirmed fixtures & results)
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS knockout_official_fixtures (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                stage TEXT NOT NULL,
                round_number INTEGER DEFAULT 1,
                match_number INTEGER NOT NULL,
                bracket_slot TEXT NOT NULL UNIQUE,
                home_team_id INTEGER REFERENCES teams(id) ON DELETE SET NULL,
                away_team_id INTEGER REFERENCES teams(id) ON DELETE SET NULL,
                home_placeholder TEXT DEFAULT '',
                away_placeholder TEXT DEFAULT '',
                scheduled_date TEXT DEFAULT '',
                scheduled_time TEXT DEFAULT '',
                scheduled_end_date TEXT DEFAULT '',
                venue TEXT DEFAULT 'Minaram Stadium',
                status TEXT NOT NULL DEFAULT 'PREDICTED',
                home_score INTEGER DEFAULT NULL,
                away_score INTEGER DEFAULT NULL,
                home_penalty INTEGER DEFAULT NULL,
                away_penalty INTEGER DEFAULT NULL,
                winner_team_id INTEGER REFERENCES teams(id) ON DELETE SET NULL,
                winner_method TEXT DEFAULT '',
                notes TEXT DEFAULT '',
                completed_at TEXT DEFAULT '',
                confirmed_at TEXT DEFAULT '',
                confirmed_by TEXT DEFAULT '',
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );
            """)
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_ko_fix_slot ON knockout_official_fixtures(bracket_slot);")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_ko_fix_stage ON knockout_official_fixtures(stage);")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_ko_fix_status ON knockout_official_fixtures(status);")

            # 11. Knockout Direct Overrides (Manual admin override of the 2 direct qualifiers)
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS knockout_direct_overrides (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                slot_index INTEGER NOT NULL UNIQUE,
                team_id INTEGER NOT NULL REFERENCES teams(id) ON DELETE CASCADE,
                reason TEXT DEFAULT '',
                admin_username TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );
            """)

            # 12. Knockout Rules Configuration
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS knockout_rules_config (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                updated_by TEXT DEFAULT 'admin'
            );
            """)

            # 13. Knockout Audit Logs
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS knockout_audit_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                admin_username TEXT NOT NULL,
                action TEXT NOT NULL,
                entity_type TEXT NOT NULL,
                entity_id TEXT DEFAULT '',
                old_value TEXT DEFAULT '',
                new_value TEXT DEFAULT '',
                reason TEXT DEFAULT ''
            );
            """)
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_ko_audit_time ON knockout_audit_logs(timestamp);")

            # 14. Admin Users Table
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS admin_users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                role TEXT NOT NULL DEFAULT 'admin',
                created_at TEXT NOT NULL
            );
            """)
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_admin_username ON admin_users(username);")

            # Seed default administrators
            now_ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            try:
                from backend.auth import hash_password, DEFAULT_ADMINS
                for adm_u, adm_p in DEFAULT_ADMINS.items():
                    existing = cursor.execute("SELECT id FROM admin_users WHERE LOWER(username) = LOWER(?);", (adm_u,)).fetchone()
                    if not existing:
                        cursor.execute("""
                            INSERT INTO admin_users (username, password_hash, role, created_at)
                            VALUES (?, ?, 'admin', ?);
                        """, (adm_u, hash_password(adm_p), now_ts))
            except Exception as e:
                logger.warning(f"Failed to seed admin users: {e}")

            # Default Settings Insertion
            default_settings = {
                "tournament_name": "Minaram Cup",
                "edition": "2026 Edition",
                "sport": "Football",
                "format_type": "Group Stage + Knockout",
                "win_points": "3",
                "draw_points": "1",
                "loss_points": "0",
                "num_groups": "2",
                "qualifiers_per_group": "2",
                "match_duration_minutes": "30",
                "default_venue": "Minaram Stadium",
                "tie_breakers": "points,goal_difference,goals_for,head_to_head,won",
                "theme": "dark"
            }
            for k, v in default_settings.items():
                cursor.execute("INSERT OR IGNORE INTO settings (key, value) VALUES (?, ?);", (k, v))

        logger.info(f"Database initialized successfully at {self.db_path}")

    def get_setting(self, key: str, default: str = "") -> str:
        row = self.execute_one("SELECT value FROM settings WHERE key = ?;", (key,))
        return row["value"] if row else default

    def set_setting(self, key: str, value: str) -> None:
        self.execute_non_query(
            "INSERT INTO settings (key, value) VALUES (?, ?) ON CONFLICT(key) DO UPDATE SET value = excluded.value;",
            (key, str(value))
        )

    def get_all_settings(self) -> Dict[str, str]:
        rows = self.execute_query("SELECT key, value FROM settings;")
        return {row["key"]: row["value"] for row in rows}

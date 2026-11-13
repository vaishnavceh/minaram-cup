"""
MINARAM CUP — Cloud Synchronization Service
Links the local desktop manager with the Render cloud API.
Supports pushing the local SQLite database to Render (which immediately
updates the Vercel live website) and pulling the latest cloud database.
"""

import os
import sys
import json
import sqlite3
import shutil
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Tuple, Optional, Callable
import urllib.request
import urllib.error

logger = logging.getLogger(__name__)

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DB_PATH = PROJECT_ROOT / "data" / "minaram_cup.db"
CONFIG_FILE = PROJECT_ROOT / "data" / "cloud_sync_config.json"

DEFAULT_BACKEND_URL = "https://minaram-cup-api.onrender.com"
DEFAULT_ADMIN_USER = "admin"
DEFAULT_ADMIN_PASS = "minaram2026"


def get_cloud_config() -> Dict[str, Any]:
    """Retrieve saved cloud configuration or defaults."""
    config = {
        "backend_url": DEFAULT_BACKEND_URL,
        "admin_username": DEFAULT_ADMIN_USER,
        "admin_password": DEFAULT_ADMIN_PASS,
        "last_sync_time": "",
        "last_sync_status": ""
    }
    if CONFIG_FILE.exists():
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                saved = json.load(f)
                if isinstance(saved, dict):
                    config.update(saved)
        except Exception as e:
            logger.warning(f"Could not read cloud config: {e}")
    return config


def save_cloud_config(backend_url: str,
                      admin_username: str = DEFAULT_ADMIN_USER,
                      admin_password: str = DEFAULT_ADMIN_PASS,
                      last_sync_time: Optional[str] = None,
                      last_sync_status: Optional[str] = None) -> bool:
    """Save cloud sync configuration to JSON."""
    try:
        config = get_cloud_config()
        config["backend_url"] = backend_url.strip().rstrip("/")
        config["admin_username"] = admin_username.strip()
        config["admin_password"] = admin_password.strip()
        if last_sync_time is not None:
            config["last_sync_time"] = last_sync_time
        if last_sync_status is not None:
            config["last_sync_status"] = last_sync_status

        CONFIG_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(config, f, indent=2)
        return True
    except Exception as e:
        logger.error(f"Failed to save cloud config: {e}")
        return False


def get_jwt_token(base_url: str, username: str, password: str) -> str:
    """Authenticate with the Render FastAPI backend and retrieve a JWT bearer token."""
    login_url = f"{base_url.rstrip('/')}/api/admin/login"
    payload = json.dumps({"username": username, "password": password}).encode("utf-8")
    req = urllib.request.Request(
        login_url,
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST"
    )
    with urllib.request.urlopen(req, timeout=60) as resp:
        data = json.loads(resp.read().decode("utf-8"))
        token = data.get("token") or data.get("access_token")
        if not token:
            raise ValueError("No authentication token returned by server")
        return token


def push_database(base_url: Optional[str] = None,
                  username: Optional[str] = None,
                  password: Optional[str] = None,
                  progress_callback: Optional[Callable[[str], None]] = None) -> Tuple[bool, str]:
    """
    Push local SQLite database to Render cloud backend.
    Flushes WAL checkpoint first to guarantee all local updates are included.
    Returns (success: bool, message: str).
    """
    cfg = get_cloud_config()
    url = (base_url or cfg.get("backend_url") or DEFAULT_BACKEND_URL).strip().rstrip("/")
    user = (username or cfg.get("admin_username") or DEFAULT_ADMIN_USER).strip()
    pwd = (password or cfg.get("admin_password") or DEFAULT_ADMIN_PASS).strip()

    if not url:
        return False, "Render Backend URL cannot be empty."

    if not DB_PATH.exists():
        return False, f"Local database file not found at {DB_PATH}"

    def report(msg: str):
        if progress_callback:
            try:
                progress_callback(msg)
            except Exception:
                pass
        logger.info(msg)

    # 1. Flush SQLite WAL to ensure latest committed changes are stored in minaram_cup.db
    report("Flushing database WAL checkpoint...")
    try:
        conn = sqlite3.connect(str(DB_PATH), timeout=10.0)
        conn.execute("PRAGMA wal_checkpoint(TRUNCATE);")
        conn.close()
    except Exception as e:
        logger.warning(f"WAL checkpoint warning: {e}")

    # 2. Authenticate
    report(f"Authenticating with Render backend at {url}...")
    try:
        token = get_jwt_token(url, user, pwd)
    except urllib.error.HTTPError as e:
        err_msg = f"Authentication failed (HTTP {e.code}): "
        try:
            body = json.loads(e.read().decode("utf-8"))
            err_msg += body.get("detail", str(body))
        except Exception:
            err_msg += e.reason
        return False, err_msg
    except Exception as e:
        return False, f"Could not connect to {url}. Backend may be sleeping or starting up: {e}"

    # 3. Read file and prepare multipart form data
    report("Preparing database payload...")
    try:
        with open(DB_PATH, "rb") as f:
            file_bytes = f.read()
    except Exception as e:
        return False, f"Failed to read local database: {e}"

    boundary = "----MinaramCupDesktopBoundary8NX5ZY"
    body = (
        f"--{boundary}\r\n"
        f'Content-Disposition: form-data; name="file"; filename="minaram_cup.db"\r\n'
        f"Content-Type: application/x-sqlite3\r\n\r\n"
    ).encode("utf-8") + file_bytes + f"\r\n--{boundary}--\r\n".encode("utf-8")

    upload_url = f"{url}/api/admin/sync/upload-database"
    req = urllib.request.Request(
        upload_url,
        data=body,
        headers={
            "Content-Type": f"multipart/form-data; boundary={boundary}",
            "Authorization": f"Bearer {token}",
        },
        method="POST"
    )

    # 4. Upload to Render
    report("Uploading database to Render cloud API...")
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            res_data = json.loads(resp.read().decode("utf-8"))
            server_msg = res_data.get("message", "Database synchronized successfully.")
            
            now_iso = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            save_cloud_config(url, user, pwd, last_sync_time=now_iso, last_sync_status="SUCCESS")
            report("Sync complete! Live website updated.")
            return True, f"Success! {server_msg}\nAll tournament fixtures, standings, and results are now live on your website."
    except urllib.error.HTTPError as e:
        err_detail = f"Server Error (HTTP {e.code}): "
        try:
            body = json.loads(e.read().decode("utf-8"))
            err_detail += body.get("detail", str(body))
        except Exception:
            err_detail += str(e.reason)
        save_cloud_config(url, user, pwd, last_sync_status=f"HTTP {e.code}")
        return False, err_detail
    except Exception as e:
        save_cloud_config(url, user, pwd, last_sync_status=str(e))
        return False, f"Upload error: {e}"


def pull_database(base_url: Optional[str] = None,
                  username: Optional[str] = None,
                  password: Optional[str] = None,
                  progress_callback: Optional[Callable[[str], None]] = None) -> Tuple[bool, str]:
    """
    Pull latest database from Render cloud backend into local desktop manager.
    Creates a pre-pull backup copy before replacing.
    Returns (success: bool, message: str).
    """
    cfg = get_cloud_config()
    url = (base_url or cfg.get("backend_url") or DEFAULT_BACKEND_URL).strip().rstrip("/")
    user = (username or cfg.get("admin_username") or DEFAULT_ADMIN_USER).strip()
    pwd = (password or cfg.get("admin_password") or DEFAULT_ADMIN_PASS).strip()

    if not url:
        return False, "Render Backend URL cannot be empty."

    def report(msg: str):
        if progress_callback:
            try:
                progress_callback(msg)
            except Exception:
                pass
        logger.info(msg)

    # 1. Authenticate
    report(f"Authenticating with Render backend at {url}...")
    try:
        token = get_jwt_token(url, user, pwd)
    except Exception as e:
        return False, f"Authentication error: {e}"

    # 2. Download database
    report("Downloading latest cloud database...")
    dl_url = f"{url}/api/admin/sync/download-database"
    req = urllib.request.Request(
        dl_url,
        headers={"Authorization": f"Bearer {token}"},
        method="GET"
    )

    try:
        with urllib.request.urlopen(req, timeout=45) as resp:
            content = resp.read()
            if not content.startswith(b"SQLite format 3"):
                return False, "Downloaded content is not a valid SQLite database."

            # Check if local DB has completed matches that incoming cloud DB lacks
            local_completed = []
            local_knockout_completed = []
            if DB_PATH.exists():
                try:
                    import sqlite3
                    with sqlite3.connect(DB_PATH) as l_conn:
                        l_conn.row_factory = sqlite3.Row
                        local_completed = [
                            dict(r) for r in l_conn.execute(
                                "SELECT id, match_number, bracket_slot, stage, home_score, away_score, "
                                "home_penalty, away_penalty, status, winner_team_id, completed_at, notes "
                                "FROM matches WHERE status IN ('Completed', 'Walkover');"
                            ).fetchall()
                        ]
                        has_ko = l_conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='knockout_official_fixtures';").fetchone()
                        if has_ko:
                            local_knockout_completed = [
                                dict(r) for r in l_conn.execute(
                                    "SELECT id, bracket_slot, stage, match_number, home_team_id, away_team_id, "
                                    "home_score, away_score, home_penalty, away_penalty, status, winner_team_id, "
                                    "winner_method, completed_at, notes FROM knockout_official_fixtures "
                                    "WHERE status IN ('COMPLETED', 'CONFIRMED');"
                                ).fetchall()
                            ]
                except Exception as e:
                    logger.warning(f"Could not inspect local completed matches before pull: {e}")

            # Safety local backup
            if DB_PATH.exists():
                backup_name = f"minaram_cup.pre_pull_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db"
                safety_path = DB_PATH.parent / "backups" / backup_name
                safety_path.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(DB_PATH, safety_path)
                report(f"Safety backup saved to {backup_name}")

            with open(DB_PATH, "wb") as f:
                f.write(content)

            # Preserve any local completed match results that the incoming cloud DB was missing
            if local_completed:
                try:
                    import sqlite3
                    with sqlite3.connect(DB_PATH) as post_conn:
                        post_conn.row_factory = sqlite3.Row
                        merged_count = 0
                        for lm in local_completed:
                            cond = "bracket_slot = ?" if lm.get("bracket_slot") else "match_number = ?"
                            val = lm["bracket_slot"] if lm.get("bracket_slot") else lm["match_number"]
                            cur_m = post_conn.execute(f"SELECT id, status FROM matches WHERE {cond};", (val,)).fetchone()
                            if cur_m and cur_m["status"] not in ('Completed', 'Walkover'):
                                post_conn.execute(f"""
                                    UPDATE matches
                                    SET home_score = ?, away_score = ?, home_penalty = ?, away_penalty = ?,
                                        status = ?, winner_team_id = ?, completed_at = ?, notes = ?
                                    WHERE {cond};
                                """, (
                                    lm["home_score"], lm["away_score"], lm["home_penalty"], lm["away_penalty"],
                                    lm["status"], lm["winner_team_id"], lm["completed_at"], lm["notes"], val
                                ))
                                merged_count += 1
                        
                        for lk in local_knockout_completed:
                            if not lk.get("bracket_slot"):
                                continue
                            cur_k = post_conn.execute(
                                "SELECT id, status FROM knockout_official_fixtures WHERE bracket_slot = ?;",
                                (lk["bracket_slot"],)
                            ).fetchone()
                            if not cur_k:
                                post_conn.execute("""
                                    INSERT INTO knockout_official_fixtures (
                                        bracket_slot, stage, match_number, home_team_id, away_team_id,
                                        home_score, away_score, home_penalty, away_penalty,
                                        status, winner_team_id, winner_method, completed_at, notes
                                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
                                """, (
                                    lk["bracket_slot"], lk["stage"], lk["match_number"],
                                    lk["home_team_id"], lk["away_team_id"],
                                    lk["home_score"], lk["away_score"], lk["home_penalty"], lk["away_penalty"],
                                    lk["status"], lk["winner_team_id"], lk["winner_method"], lk["completed_at"], lk["notes"]
                                ))
                            elif cur_k["status"] not in ('COMPLETED', 'CONFIRMED') and lk["status"] in ('COMPLETED', 'CONFIRMED'):
                                post_conn.execute("""
                                    UPDATE knockout_official_fixtures
                                    SET home_score = ?, away_score = ?, home_penalty = ?, away_penalty = ?,
                                        status = ?, winner_team_id = ?, winner_method = ?, completed_at = ?, notes = ?
                                    WHERE bracket_slot = ?;
                                """, (
                                    lk["home_score"], lk["away_score"], lk["home_penalty"], lk["away_penalty"],
                                    lk["status"], lk["winner_team_id"], lk["winner_method"], lk["completed_at"], lk["notes"],
                                    lk["bracket_slot"]
                                ))
                        post_conn.commit()
                        if merged_count > 0:
                            report(f"Preserved {merged_count} locally completed matches that were not yet in cloud.")
                except Exception as e:
                    logger.warning(f"Could not merge local completed matches after pull: {e}")

            # Automatically create atomic backup and state snapshot of newly pulled data
            try:
                from app.database import Database
                db = Database()
                db.get_backup_service().create_auto_backup(action_label="cloud_pull_sync")
            except Exception as e:
                logger.warning(f"Could not create post-pull backup snapshot: {e}")

            now_iso = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            save_cloud_config(url, user, pwd, last_sync_time=now_iso, last_sync_status="SUCCESS (PULL)")
            return True, f"Successfully downloaded latest database from cloud ({len(content)} bytes)!"
    except Exception as e:
        return False, f"Pull failed: {e}"

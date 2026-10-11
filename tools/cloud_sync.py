"""
MINARAM CUP — Desktop to Cloud Synchronization Utility.
Securely links the local desktop management software with the Render cloud backend.
Allows 1-click PUSH (publish local database to cloud) or PULL (download cloud database to local).
"""

import sys
import json
import argparse
from pathlib import Path
import urllib.request
import urllib.error

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DB_PATH = PROJECT_ROOT / "data" / "minaram_cup.db"
CONFIG_FILE = PROJECT_ROOT / "data" / "cloud_sync_config.json"


def get_jwt_token(base_url: str, username: str, password: str) -> str:
    url = f"{base_url.rstrip('/')}/api/admin/login"
    payload = json.dumps({"username": username, "password": password}).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST"
    )
    with urllib.request.urlopen(req, timeout=15) as resp:
        data = json.loads(resp.read().decode("utf-8"))
        return data["token"]


def push_to_cloud(base_url: str, username: str = "admin", password: str = "minaram2026"):
    if not DB_PATH.exists():
        print(f"[ERROR] Local database file not found at {DB_PATH}")
        sys.exit(1)

    print(f"[1/3] Authenticating with Render backend at {base_url}...")
    try:
        token = get_jwt_token(base_url, username, password)
    except Exception as e:
        print(f"[ERROR] Failed to authenticate with cloud backend: {e}")
        sys.exit(1)

    print("[2/3] Uploading local SQLite database to Render...")
    boundary = "----MinaramCupBoundary7MA4YWxkTrZu0gW"
    
    with open(DB_PATH, "rb") as f:
        file_bytes = f.read()

    body = (
        f"--{boundary}\r\n"
        f'Content-Disposition: form-data; name="file"; filename="minaram_cup.db"\r\n'
        f"Content-Type: application/x-sqlite3\r\n\r\n"
    ).encode("utf-8") + file_bytes + f"\r\n--{boundary}--\r\n".encode("utf-8")

    upload_url = f"{base_url.rstrip('/')}/api/admin/sync/upload-database"
    req = urllib.request.Request(
        upload_url,
        data=body,
        headers={
            "Content-Type": f"multipart/form-data; boundary={boundary}",
            "Authorization": f"Bearer {token}",
        },
        method="POST"
    )

    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            res_data = json.loads(resp.read().decode("utf-8"))
            print(f"[3/3] [SUCCESS] {res_data.get('message', 'Database synced successfully!')}")
            print(">> All changes are now live on your Vercel public website!")
    except urllib.error.HTTPError as e:
        print(f"[ERROR] HTTP Error {e.code}: {e.read().decode('utf-8')}")
        sys.exit(1)
    except Exception as e:
        print(f"[ERROR] Sync failed: {e}")
        sys.exit(1)


def pull_from_cloud(base_url: str, username: str = "admin", password: str = "minaram2026"):
    print(f"[1/3] Authenticating with Render backend at {base_url}...")
    try:
        token = get_jwt_token(base_url, username, password)
    except Exception as e:
        print(f"[ERROR] Failed to authenticate with cloud backend: {e}")
        sys.exit(1)

    print("[2/3] Downloading latest cloud database from Render...")
    dl_url = f"{base_url.rstrip('/')}/api/admin/sync/download-database"
    req = urllib.request.Request(
        dl_url,
        headers={"Authorization": f"Bearer {token}"},
        method="GET"
    )

    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            content = resp.read()
            if not content.startswith(b"SQLite format 3"):
                print("[ERROR] Received invalid database payload from server.")
                sys.exit(1)
            
            # Backup existing
            backup_path = DB_PATH.with_suffix(".pre_pull_backup.db")
            if DB_PATH.exists():
                import shutil
                shutil.copy2(DB_PATH, backup_path)
                print(f"Safety local backup created: {backup_path.name}")

            with open(DB_PATH, "wb") as f:
                f.write(content)
            
            print(f"[3/3] [SUCCESS] Downloaded {len(content)} bytes from cloud!")
            print(">> Local desktop manager now has the latest cloud data!")
    except Exception as e:
        print(f"[ERROR] Pull failed: {e}")
        sys.exit(1)


def main():
    parser = argparse.ArgumentParser(description="Minaram Cup Desktop-to-Cloud Sync Utility")
    parser.add_argument("action", choices=["push", "pull"], nargs="?", default="push", help="push: upload to cloud, pull: download from cloud")
    parser.add_argument("--url", default="", help="Render backend URL (e.g. https://minaram-cup.onrender.com)")
    parser.add_argument("--password", default="minaram2026", help="Admin password")

    args = parser.parse_args()

    # Load saved URL if available
    saved_url = ""
    if CONFIG_FILE.exists():
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                cfg = json.load(f)
                saved_url = cfg.get("backend_url", "")
        except Exception:
            pass

    backend_url = args.url or saved_url
    if not backend_url:
        print("==================================================")
        print("   MINARAM CUP — CLOUD SYNC CONFIGURATION")
        print("==================================================")
        backend_url = input("Enter your Render Backend URL (e.g. https://minaram-api.onrender.com): ").strip()
        if not backend_url:
            print("Error: Backend URL cannot be empty.")
            sys.exit(1)
        # Save config
        try:
            CONFIG_FILE.parent.mkdir(parents=True, exist_ok=True)
            with open(CONFIG_FILE, "w", encoding="utf-8") as f:
                json.dump({"backend_url": backend_url}, f, indent=2)
            print(f"[Config Saved] Saved to {CONFIG_FILE.name}")
        except Exception:
            pass

    if args.action == "push":
        push_to_cloud(backend_url, password=args.password)
    else:
        pull_from_cloud(backend_url, password=args.password)


if __name__ == "__main__":
    main()

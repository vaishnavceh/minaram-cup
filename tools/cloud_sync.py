"""
MINARAM CUP — Desktop to Cloud Synchronization CLI.
Securely links the local desktop management software with the Render cloud backend.
Allows 1-click PUSH (publish local database to cloud) or PULL (download cloud database to local).
"""

import sys
import argparse
from pathlib import Path

# Add project root to sys.path so app can be imported
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.cloud_sync_service import push_database, pull_database, get_cloud_config, save_cloud_config, DB_PATH


def main():
    parser = argparse.ArgumentParser(description="Minaram Cup Desktop-to-Cloud Sync Utility")
    parser.add_argument("action", choices=["push", "pull"], nargs="?", default="push", help="push: upload to cloud, pull: download from cloud")
    parser.add_argument("--url", default="", help="Render backend URL (e.g. https://minaram-cup-api.onrender.com)")
    parser.add_argument("--password", default="", help="Admin password")

    args = parser.parse_args()

    cfg = get_cloud_config()
    backend_url = args.url or cfg.get("backend_url", "")
    password = args.password or cfg.get("admin_password", "minaram2026")

    if not backend_url:
        print("==================================================")
        print("   MINARAM CUP — CLOUD SYNC CONFIGURATION")
        print("==================================================")
        backend_url = input("Enter your Render Backend URL (e.g. https://minaram-cup-api.onrender.com): ").strip()
        if not backend_url:
            print("Error: Backend URL cannot be empty.")
            sys.exit(1)
        save_cloud_config(backend_url, admin_password=password)
        print(f"[Config Saved] Saved to cloud_sync_config.json")

    def cli_progress(msg: str):
        print(f">> {msg}")

    if args.action == "push":
        print(f"[PUSH] Uploading local tournament database to {backend_url}...")
        ok, msg = push_database(base_url=backend_url, password=password, progress_callback=cli_progress)
        if ok:
            print(f"[SUCCESS] {msg}")
        else:
            print(f"[ERROR] {msg}")
            sys.exit(1)
    else:
        print(f"[PULL] Downloading latest tournament database from {backend_url}...")
        ok, msg = pull_database(base_url=backend_url, password=password, progress_callback=cli_progress)
        if ok:
            print(f"[SUCCESS] {msg}")
        else:
            print(f"[ERROR] {msg}")
            sys.exit(1)


if __name__ == "__main__":
    main()

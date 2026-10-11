"""
Minaram Cup — Tournament Management System
Main Application Entry Point.
"""

import sys
import logging
from pathlib import Path

# Configure application logging
PROJECT_ROOT = Path(__file__).resolve().parent
LOG_DIR = PROJECT_ROOT / "logs"
LOG_DIR.mkdir(parents=True, exist_ok=True)
LOG_FILE = LOG_DIR / "minaram_cup.log"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[
        logging.FileHandler(LOG_FILE, encoding="utf-8"),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger("minaram_cup.main")


def bootstrap_existing_data(db):
    """
    Check if legacy registrations.csv or registrations.xlsx exist in the project directory.
    If so and if registrations table is currently empty, import existing data so no past records are lost.
    """
    from app.registration_service import RegistrationService

    reg_service = RegistrationService(db)
    existing_cnt = db.execute_one("SELECT COUNT(*) AS c FROM registrations;")["c"]
    if existing_cnt > 0:
        return

    csv_file = PROJECT_ROOT / "registrations.csv"
    xlsx_file = PROJECT_ROOT / "registrations.xlsx"

    if csv_file.exists():
        logger.info(f"Found existing legacy CSV file at {csv_file}. Importing records...")
        count, errors = reg_service.import_from_csv(csv_file)
        logger.info(f"Imported {count} records from existing {csv_file}")
    elif xlsx_file.exists():
        logger.info(f"Found existing legacy XLSX file at {xlsx_file}. Importing records...")
        count, errors = reg_service.import_from_xlsx(xlsx_file)
        logger.info(f"Imported {count} records from existing {xlsx_file}")

    # Reconcile any registrations that lack team associations
    reconciled = reg_service.reconcile_registrations_to_teams()
    if reconciled > 0:
        logger.info(f"Reconciled {reconciled} registrations to teams table.")


def main():
    logger.info("Starting Minaram Cup Tournament Management System...")

    from app.database import Database
    db = Database()
    bootstrap_existing_data(db)

    # If launched with --headless-check, verify UI instantiation and exit 0
    if "--headless-check" in sys.argv:
        logger.info("Running headless startup verification check...")
        from app.ui.main_window import MainWindow
        app = MainWindow(db)
        app.update()
        app.destroy()
        logger.info("Headless startup check passed successfully!")
        sys.exit(0)

    from app.ui.main_window import MainWindow
    app = MainWindow(db)
    app.mainloop()


if __name__ == "__main__":
    main()

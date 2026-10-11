#!/usr/bin/env python3
"""
Registration Format -> Excel/CSV
Paste a registration message into the terminal. Each valid registration is
appended to registrations.xlsx and registrations.csv.

Expected format:
Registration Format
Name: Vaishnav
Phone No: 9746603975
Team Name: Binladen Fc

Run: python registration_logger.py
Install Excel support if needed: python -m pip install openpyxl
"""

import csv
import re
from pathlib import Path
from datetime import datetime

OUTPUT_DIR = Path(__file__).resolve().parent
CSV_FILE = OUTPUT_DIR / "registrations.csv"
XLSX_FILE = OUTPUT_DIR / "registrations.xlsx"
HEADERS = ["Name", "Phone No", "Team Name", "Registered At"]


def extract_field(text: str, labels: list[str]) -> str:
    """Extract a labelled value, stopping at the next field or line break."""
    label_pattern = "|".join(re.escape(label) for label in labels)
    pattern = rf"(?im)^\s*(?:{label_pattern})\s*:\s*(.*?)\s*$"
    match = re.search(pattern, text)
    return match.group(1).strip().strip("\\").strip() if match else ""


def parse_registration(text: str) -> dict:
    name = extract_field(text, ["Name"])
    phone = extract_field(text, ["Phone No", "Phone Number", "Phone", "Mobile No"])
    team = extract_field(text, ["Team Name", "Team"])

    missing = [label for label, value in [
        ("Name", name), ("Phone No", phone), ("Team Name", team)
    ] if not value]
    if missing:
        raise ValueError("Missing field(s): " + ", ".join(missing))

    return {
        "Name": name,
        "Phone No": phone,  # Keep as text so leading zeroes are preserved.
        "Team Name": team,
        "Registered At": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    }


def append_csv(row: dict) -> None:
    file_exists = CSV_FILE.exists() and CSV_FILE.stat().st_size > 0
    with CSV_FILE.open("a", newline="", encoding="utf-8-sig") as file:
        writer = csv.DictWriter(file, fieldnames=HEADERS)
        if not file_exists:
            writer.writeheader()
        writer.writerow(row)


def append_xlsx(row: dict) -> None:
    try:
        from openpyxl import Workbook, load_workbook
        from openpyxl.styles import Font, PatternFill
        from openpyxl.utils import get_column_letter
    except ImportError:
        raise RuntimeError(
            "Excel support requires openpyxl. Install it with:\n"
            "python -m pip install openpyxl"
        )

    if XLSX_FILE.exists():
        workbook = load_workbook(XLSX_FILE)
        sheet = workbook.active
    else:
        workbook = Workbook()
        sheet = workbook.active
        sheet.title = "Registrations"
        sheet.append(HEADERS)
        for cell in sheet[1]:
            cell.font = Font(bold=True, color="FFFFFF")
            cell.fill = PatternFill("solid", fgColor="243447")

    sheet.append([row[header] for header in HEADERS])
    sheet.freeze_panes = "A2"
    sheet.auto_filter.ref = sheet.dimensions
    for col_idx, width in enumerate([26, 20, 28, 22], start=1):
        sheet.column_dimensions[get_column_letter(col_idx)].width = width
    workbook.save(XLSX_FILE)


def main() -> None:
    print("=" * 52)
    print("REGISTRATION LOGGER")
    print("Paste one registration, then enter a line containing END.")
    print("Type EXIT on the first line to quit.")
    print("=" * 52)

    while True:
        print("\nPaste registration:")
        lines = []
        while True:
            try:
                line = input()
            except (EOFError, KeyboardInterrupt):
                print("\nExiting.")
                return

            if not lines and line.strip().upper() == "EXIT":
                print("Goodbye.")
                return
            if line.strip().upper() == "END":
                break
            lines.append(line)

        text = "\n".join(lines).replace("\\\n", "\n")
        if not text.strip():
            continue

        try:
            row = parse_registration(text)
            # Write CSV first; then XLSX. CSV remains available if Excel support
            # is missing or the workbook cannot be written.
            append_csv(row)
            try:
                append_xlsx(row)
                print(f"Saved: {row['Name']} | {row['Phone No']} | {row['Team Name']}")
                print(f"Excel: {XLSX_FILE}")
                print(f"CSV:   {CSV_FILE}")
            except Exception as exc:
                print(f"Saved to CSV: {CSV_FILE}")
                print(f"Could not update Excel: {exc}")
        except ValueError as exc:
            print(f"Registration not saved: {exc}")
            print("Please include Name:, Phone No:, and Team Name:.")


if __name__ == "__main__":
    main()

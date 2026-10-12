"""
Service layer for registration management, validation, duplicate detection,
importing from CSV/Excel, and linking registrations to teams.
Automatically synchronizes registrations to the Teams table.
"""

import csv
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime

from app.database import Database
from app.models import Registration, ParsedRegistration
from app.registration_parser import parse_registration_text
from app.events import broadcaster

logger = logging.getLogger("minaram_cup.registration_service")


class RegistrationService:
    def __init__(self, db: Database):
        self.db = db

    def preview_raw_text(self, raw_text: str) -> List[Dict[str, Any]]:
        """
        Parse raw text and check each parsed entry against database for duplicates and validity.
        Returns a list of dicts with keys:
        - name, phone, team, is_valid, errors, warnings, duplicate_type
        """
        parsed_items = parse_registration_text(raw_text)
        preview_results = []

        for p in parsed_items:
            item_dict = {
                "name": p.name,
                "phone": p.phone,
                "team": p.team,
                "raw_text": p.raw_text,
                "is_valid": p.is_valid,
                "errors": list(p.errors),
                "warnings": list(p.warnings),
                "duplicate_status": "Unique",
                "existing_reg_id": None,
                "existing_team_id": None,
            }

            if p.is_valid:
                # Duplicate phone check in registrations
                existing_phone_reg = self.db.execute_one(
                    "SELECT id, participant_name, team_name FROM registrations WHERE phone_number = ?;",
                    (p.phone,)
                )
                if existing_phone_reg:
                    item_dict["duplicate_status"] = "Duplicate Phone"
                    item_dict["existing_reg_id"] = existing_phone_reg["id"]
                    item_dict["warnings"].append(
                        f"Phone matches existing Reg #{existing_phone_reg['id']} ({existing_phone_reg['participant_name']} - {existing_phone_reg['team_name']})"
                    )

                # Duplicate team check
                existing_team = self.db.execute_one(
                    "SELECT id, name FROM teams WHERE LOWER(name) = LOWER(?);",
                    (p.team,)
                )
                if existing_team:
                    if item_dict["duplicate_status"] == "Duplicate Phone":
                        item_dict["duplicate_status"] = "Duplicate Team & Phone"
                    else:
                        item_dict["duplicate_status"] = "Duplicate Team"
                    item_dict["existing_team_id"] = existing_team["id"]
                    item_dict["warnings"].append(f"Team '{p.team}' already exists in Teams table (ID #{existing_team['id']})")
                else:
                    existing_team_reg = self.db.execute_one(
                        "SELECT id, participant_name FROM registrations WHERE LOWER(team_name) = LOWER(?);",
                        (p.team,)
                    )
                    if existing_team_reg:
                        item_dict["warnings"].append(
                            f"Team name matches existing Reg #{existing_team_reg['id']} ({existing_team_reg['participant_name']})"
                        )

            preview_results.append(item_dict)

        return preview_results

    def save_parsed_registrations(self, items: List[Dict[str, Any]], auto_confirm: bool = True) -> Tuple[int, List[str]]:
        """
        Save a batch of parsed registration records into SQLite within a single transaction.
        CRITICAL FIX: Automatically creates or links corresponding teams in the Teams table
        so that every registered team appears immediately across desktop and website.
        """
        saved_count = 0
        errors = []

        now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        with self.db.transaction(action="registrations_saved") as conn:
            cursor = conn.cursor()
            for idx, item in enumerate(items, 1):
                name = item.get("name", "").strip()
                phone = str(item.get("phone", "")).strip()
                team = item.get("team", "").strip()
                raw_text = item.get("raw_text", "")

                if not name or not phone or not team:
                    errors.append(f"Row {idx} skipped: missing required fields")
                    continue

                dup_status = item.get("duplicate_status", "Unique")
                # Confirmed by default so team immediately joins tournament
                status = "Duplicate" if "Duplicate" in dup_status and not auto_confirm else "Confirmed"
                notes = "; ".join(item.get("warnings", []))

                cursor.execute("""
                    INSERT INTO registrations (participant_name, phone_number, team_name, raw_message, registered_at, status, notes)
                    VALUES (?, ?, ?, ?, ?, ?, ?);
                """, (name, phone, team, raw_text, now_str, status, notes))

                reg_id = cursor.lastrowid
                saved_count += 1

                # Find or create corresponding team
                cursor.execute("SELECT id FROM teams WHERE LOWER(name) = LOWER(?);", (team,))
                existing_t = cursor.fetchone()
                if existing_t:
                    team_id = existing_t[0]
                    # Update contact if empty
                    cursor.execute("""
                        UPDATE teams SET 
                            captain_name = CASE WHEN captain_name = '' THEN ? ELSE captain_name END,
                            phone_number = CASE WHEN phone_number = '' THEN ? ELSE phone_number END
                        WHERE id = ?;
                    """, (name, phone, team_id))
                else:
                    cursor.execute("""
                        INSERT INTO teams (name, captain_name, phone_number, status, created_at)
                        VALUES (?, ?, ?, 'Confirmed', ?);
                    """, (team, name, phone, now_str))
                    team_id = cursor.lastrowid

                cursor.execute("""
                    INSERT OR REPLACE INTO registration_team_map (registration_id, team_id)
                    VALUES (?, ?);
                """, (reg_id, team_id))

        # Broadcast live sync event
        if saved_count > 0:
            broadcaster.broadcast_from_thread("registrations_updated", data={"saved_count": saved_count})
            broadcaster.broadcast_from_thread("teams_updated")

        return saved_count, errors

    def reconcile_registrations_to_teams(self) -> int:
        """
        Reconcile and fix any existing registrations in the database that are missing
        from the Teams table. Ensures 100% data consistency.
        """
        now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        reconciled_count = 0

        with self.db.transaction() as conn:
            cursor = conn.cursor()
            # Find orphan registrations
            cursor.execute("""
                SELECT r.id, r.participant_name, r.phone_number, r.team_name, r.status
                FROM registrations r
                LEFT JOIN registration_team_map m ON r.id = m.registration_id
                WHERE m.team_id IS NULL;
            """)
            orphans = cursor.fetchall()

            for r in orphans:
                reg_id = r["id"]
                name = r["participant_name"]
                phone = r["phone_number"]
                team = r["team_name"]

                cursor.execute("SELECT id FROM teams WHERE LOWER(name) = LOWER(?);", (team,))
                existing = cursor.fetchone()
                if existing:
                    team_id = existing[0]
                else:
                    cursor.execute("""
                        INSERT INTO teams (name, captain_name, phone_number, status, created_at)
                        VALUES (?, ?, ?, 'Confirmed', ?);
                    """, (team, name, phone, now_str))
                    team_id = cursor.lastrowid

                cursor.execute("""
                    INSERT OR REPLACE INTO registration_team_map (registration_id, team_id)
                    VALUES (?, ?);
                """, (reg_id, team_id))
                reconciled_count += 1

        if reconciled_count > 0:
            logger.info(f"Reconciled {reconciled_count} registrations to teams table.")
            broadcaster.broadcast_from_thread("teams_updated", data={"reconciled": reconciled_count})

        return reconciled_count

    def get_registrations(
        self,
        search: Optional[str] = None,
        status: Optional[str] = None,
        sort_by: str = "registered_at",
        sort_asc: bool = False
    ) -> List[Registration]:
        """Fetch registrations with optional search, status filter, and sorting."""
        query = "SELECT id, participant_name, phone_number, team_name, raw_message, registered_at, status, notes FROM registrations WHERE 1=1"
        params = []

        if search and search.strip():
            term = f"%{search.strip()}%"
            query += " AND (participant_name LIKE ? OR phone_number LIKE ? OR team_name LIKE ?)"
            params.extend([term, term, term])

        if status and status != "All":
            query += " AND status = ?"
            params.append(status)

        allowed_sort = {
            "id": "id",
            "participant_name": "participant_name",
            "phone_number": "phone_number",
            "team_name": "team_name",
            "registered_at": "registered_at",
            "status": "status"
        }
        order_col = allowed_sort.get(sort_by, "registered_at")
        direction = "ASC" if sort_asc else "DESC"
        query += f" ORDER BY {order_col} {direction};"

        rows = self.db.execute_query(query, tuple(params))
        return [
            Registration(
                id=r["id"],
                participant_name=r["participant_name"],
                phone_number=r["phone_number"],
                team_name=r["team_name"],
                raw_message=r["raw_message"] or "",
                registered_at=r["registered_at"],
                status=r["status"],
                notes=r["notes"] or "",
            )
            for r in rows
        ]

    def add_registration_manual(
        self,
        name: str,
        phone: str,
        team_name: str,
        status: str = "Confirmed",
        notes: str = ""
    ) -> int:
        """
        Manually add a registration and immediately create/link the corresponding team.
        """
        now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with self.db.transaction() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO registrations (participant_name, phone_number, team_name, raw_message, registered_at, status, notes)
                VALUES (?, ?, ?, 'Manual Entry', ?, ?, ?);
            """, (name.strip(), str(phone).strip(), team_name.strip(), now_str, status, notes.strip()))
            reg_id = cursor.lastrowid

            # Find or create corresponding team
            cursor.execute("SELECT id FROM teams WHERE LOWER(name) = LOWER(?);", (team_name.strip(),))
            existing_t = cursor.fetchone()
            if existing_t:
                team_id = existing_t[0]
            else:
                cursor.execute("""
                    INSERT INTO teams (name, captain_name, phone_number, status, created_at)
                    VALUES (?, ?, ?, 'Confirmed', ?);
                """, (team_name.strip(), name.strip(), str(phone).strip(), now_str))
                team_id = cursor.lastrowid

            cursor.execute("""
                INSERT OR REPLACE INTO registration_team_map (registration_id, team_id)
                VALUES (?, ?);
            """, (reg_id, team_id))

        broadcaster.broadcast_from_thread("registrations_updated", entity_id=reg_id)
        broadcaster.broadcast_from_thread("teams_updated", entity_id=team_id)
        return reg_id

    def update_registration(
        self,
        reg_id: int,
        name: str,
        phone: str,
        team_name: str,
        status: str,
        notes: str = ""
    ) -> None:
        self.db.execute_non_query("""
            UPDATE registrations
            SET participant_name = ?, phone_number = ?, team_name = ?, status = ?, notes = ?
            WHERE id = ?;
        """, (name.strip(), str(phone).strip(), team_name.strip(), status, notes.strip(), reg_id))

        broadcaster.broadcast_from_thread("registrations_updated", entity_id=reg_id)

    def delete_registration(self, reg_id: int, delete_associated_team: bool = True) -> None:
        """
        Delete a registration and automatically delete the corresponding team if no other
        registrations are linked to it, keeping registrations and teams strictly synchronized.
        """
        deleted_team_ids = []
        with self.db.transaction(action="registration_deleted") as conn:
            cursor = conn.cursor()

            # Find registration details before deleting
            reg = self.db.execute_one("SELECT team_name FROM registrations WHERE id = ?;", (reg_id,))

            # Find mapped teams
            cursor.execute("SELECT team_id FROM registration_team_map WHERE registration_id = ?;", (reg_id,))
            mapped_rows = cursor.fetchall()
            candidate_team_ids = {r[0] for r in mapped_rows}

            # Also check by team name match if available
            if reg and reg["team_name"]:
                t_match = self.db.execute_one("SELECT id FROM teams WHERE LOWER(name) = LOWER(?);", (reg["team_name"],))
                if t_match:
                    candidate_team_ids.add(t_match["id"])

            # Delete the mapping and registration
            cursor.execute("DELETE FROM registration_team_map WHERE registration_id = ?;", (reg_id,))
            cursor.execute("DELETE FROM registrations WHERE id = ?;", (reg_id,))

            # Automatically delete orphaned teams
            if delete_associated_team:
                for t_id in candidate_team_ids:
                    # Verify no other registration references this team
                    cursor.execute("SELECT COUNT(*) FROM registration_team_map WHERE team_id = ?;", (t_id,))
                    other_mapped = cursor.fetchone()[0]

                    t_row = self.db.execute_one("SELECT name FROM teams WHERE id = ?;", (t_id,))
                    other_by_name = 0
                    if t_row:
                        other_by_name = self.db.execute_one(
                            "SELECT COUNT(*) AS c FROM registrations WHERE LOWER(team_name) = LOWER(?);",
                            (t_row["name"],)
                        )["c"]

                    if other_mapped == 0 and other_by_name == 0:
                        cursor.execute("DELETE FROM standings_overrides WHERE team_id = ?;", (t_id,))
                        cursor.execute("DELETE FROM matches WHERE home_team_id = ? OR away_team_id = ?;", (t_id, t_id))
                        cursor.execute("DELETE FROM teams WHERE id = ?;", (t_id,))
                        deleted_team_ids.append(t_id)

        for t_id in deleted_team_ids:
            broadcaster.broadcast_from_thread("teams_updated", entity_id=t_id)
        broadcaster.broadcast_from_thread("registrations_updated", entity_id=reg_id)


    def confirm_and_create_team(self, reg_id: int) -> int:
        """Confirm a registration and create a corresponding team if not already created."""
        reg = self.db.execute_one("SELECT * FROM registrations WHERE id = ?;", (reg_id,))
        if not reg:
            raise ValueError(f"Registration ID {reg_id} not found.")

        now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with self.db.transaction() as conn:
            cursor = conn.cursor()
            cursor.execute("UPDATE registrations SET status = 'Confirmed' WHERE id = ?;", (reg_id,))

            # Find or insert team
            cursor.execute("SELECT id FROM teams WHERE LOWER(name) = LOWER(?);", (reg["team_name"],))
            team_row = cursor.fetchone()
            if team_row:
                team_id = team_row[0]
            else:
                cursor.execute("""
                    INSERT INTO teams (name, captain_name, phone_number, status, created_at)
                    VALUES (?, ?, ?, 'Confirmed', ?);
                """, (reg["team_name"], reg["participant_name"], reg["phone_number"], now_str))
                team_id = cursor.lastrowid

            cursor.execute("""
                INSERT OR REPLACE INTO registration_team_map (registration_id, team_id)
                VALUES (?, ?);
            """, (reg_id, team_id))

        broadcaster.broadcast_from_thread("registrations_updated", entity_id=reg_id)
        broadcaster.broadcast_from_thread("teams_updated", entity_id=team_id)
        return team_id

    def import_from_csv(self, file_path: Path) -> Tuple[int, List[str]]:
        """Import registrations from CSV file."""
        path = Path(file_path)
        if not path.exists():
            return 0, [f"File does not exist: {path}"]

        imported_count = 0
        errors = []
        raw_items = []

        try:
            with open(path, mode="r", encoding="utf-8-sig", newline="") as f:
                reader = csv.reader(f)
                header_row = next(reader, None)
                if not header_row:
                    return 0, ["CSV file is empty"]

                headers = [h.strip().lower() for h in header_row]
                name_idx = next((i for i, h in enumerate(headers) if "name" in h and "team" not in h), -1)
                phone_idx = next((i for i, h in enumerate(headers) if "phone" in h or "mobile" in h or "contact" in h), -1)
                team_idx = next((i for i, h in enumerate(headers) if "team" in h or "club" in h), -1)

                if name_idx == -1 or phone_idx == -1 or team_idx == -1:
                    if len(headers) >= 3:
                        name_idx, phone_idx, team_idx = 0, 1, 2
                    else:
                        return 0, [f"Could not map Name, Phone, and Team columns in CSV headers: {header_row}"]

                for row_num, row in enumerate(reader, start=2):
                    if not row or not any(row):
                        continue
                    name = row[name_idx].strip() if len(row) > name_idx else ""
                    phone = row[phone_idx].strip() if len(row) > phone_idx else ""
                    team = row[team_idx].strip() if len(row) > team_idx else ""

                    if name and phone and team:
                        raw_items.append({
                            "name": name,
                            "phone": phone,
                            "team": team,
                            "raw_text": f"CSV Import row {row_num}",
                            "warnings": [],
                        })
                    else:
                        errors.append(f"Row {row_num}: incomplete data")

            if raw_items:
                count, save_errors = self.save_parsed_registrations(raw_items, auto_confirm=True)
                imported_count += count
                errors.extend(save_errors)

        except Exception as e:
            logger.error(f"Error importing CSV {path}: {e}")
            errors.append(f"Import error: {str(e)}")

        return imported_count, errors

    def import_from_xlsx(self, file_path: Path) -> Tuple[int, List[str]]:
        """Import registrations from Excel (.xlsx) file."""
        path = Path(file_path)
        if not path.exists():
            return 0, [f"File does not exist: {path}"]

        imported_count = 0
        errors = []
        raw_items = []

        try:
            import openpyxl
            wb = openpyxl.load_workbook(path, data_only=True)
            sheet = wb.active

            rows = list(sheet.iter_rows(values_only=True))
            if not rows or len(rows) < 2:
                return 0, ["Excel sheet does not have enough rows"]

            headers = [str(c).strip().lower() if c is not None else "" for c in rows[0]]
            name_idx = next((i for i, h in enumerate(headers) if "name" in h and "team" not in h), -1)
            phone_idx = next((i for i, h in enumerate(headers) if "phone" in h or "mobile" in h or "contact" in h), -1)
            team_idx = next((i for i, h in enumerate(headers) if "team" in h or "club" in h), -1)

            if name_idx == -1 or phone_idx == -1 or team_idx == -1:
                if len(headers) >= 3:
                    name_idx, phone_idx, team_idx = 0, 1, 2
                else:
                    return 0, [f"Could not map columns from header: {rows[0]}"]

            for row_num, row in enumerate(rows[1:], start=2):
                if not row or not any(row):
                    continue
                name = str(row[name_idx]).strip() if len(row) > name_idx and row[name_idx] is not None else ""
                phone = str(row[phone_idx]).strip() if len(row) > phone_idx and row[phone_idx] is not None else ""
                team = str(row[team_idx]).strip() if len(row) > team_idx and row[team_idx] is not None else ""

                if name and phone and team:
                    raw_items.append({
                        "name": name,
                        "phone": phone,
                        "team": team,
                        "raw_text": f"Excel Import row {row_num}",
                        "warnings": [],
                    })
                else:
                    errors.append(f"Row {row_num}: incomplete data")

            if raw_items:
                count, save_errors = self.save_parsed_registrations(raw_items, auto_confirm=True)
                imported_count += count
                errors.extend(save_errors)

        except Exception as e:
            logger.error(f"Error importing Excel {path}: {e}")
            errors.append(f"Excel import error: {str(e)}")

        return imported_count, errors

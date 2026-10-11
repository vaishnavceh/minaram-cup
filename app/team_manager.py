"""
Team management service: CRUD operations, merging duplicate teams,
group assignments, match history, and performance stats.
"""

import logging
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime

from app.database import Database
from app.models import Team

logger = logging.getLogger("minaram_cup.team_manager")


class TeamManager:
    def __init__(self, db: Database):
        self.db = db

    def create_team(
        self,
        name: str,
        captain_name: str = "",
        phone_number: str = "",
        status: str = "Confirmed",
        group_id: Optional[int] = None,
        seed: int = 0,
        logo_path: str = "",
        notes: str = ""
    ) -> int:
        """Create a new team. Raises ValueError if name is taken."""
        name = name.strip()
        if not name:
            raise ValueError("Team name cannot be empty.")

        existing = self.db.execute_one("SELECT id FROM teams WHERE LOWER(name) = LOWER(?);", (name,))
        if existing:
            raise ValueError(f"Team '{name}' already exists (ID #{existing['id']}).")

        now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        team_id = self.db.execute_non_query("""
            INSERT INTO teams (name, captain_name, phone_number, status, group_id, seed, logo_path, notes, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?);
        """, (name, captain_name.strip(), phone_number.strip(), status, group_id, seed, logo_path.strip(), notes.strip(), now_str))
        return team_id

    def update_team(
        self,
        team_id: int,
        name: str,
        captain_name: str = "",
        phone_number: str = "",
        status: str = "Confirmed",
        group_id: Optional[int] = None,
        seed: int = 0,
        logo_path: str = "",
        notes: str = ""
    ) -> None:
        """Update existing team details."""
        name = name.strip()
        if not name:
            raise ValueError("Team name cannot be empty.")

        existing = self.db.execute_one("SELECT id FROM teams WHERE LOWER(name) = LOWER(?) AND id != ?;", (name, team_id))
        if existing:
            raise ValueError(f"Another team with the name '{name}' already exists (ID #{existing['id']}).")

        self.db.execute_non_query("""
            UPDATE teams
            SET name = ?, captain_name = ?, phone_number = ?, status = ?, group_id = ?, seed = ?, logo_path = ?, notes = ?
            WHERE id = ?;
        """, (name, captain_name.strip(), phone_number.strip(), status, group_id, seed, logo_path.strip(), notes.strip(), team_id))

    def delete_team(self, team_id: int) -> Tuple[bool, str]:
        """
        Delete a team after checking whether it has associated matches.
        Returns (success, message).
        """
        matches_count = self.db.execute_one("""
            SELECT COUNT(*) AS cnt FROM matches
            WHERE home_team_id = ? OR away_team_id = ?;
        """, (team_id, team_id))["cnt"]

        if matches_count > 0:
            return False, f"Cannot delete team: {matches_count} matches are scheduled or recorded for this team. Remove or reschedule matches first, or use Merge."

        with self.db.transaction() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM registration_team_map WHERE team_id = ?;", (team_id,))
            cursor.execute("DELETE FROM teams WHERE id = ?;", (team_id,))

        return True, "Team deleted successfully."

    def merge_teams(self, source_team_id: int, target_team_id: int) -> Tuple[bool, str]:
        """
        Merge source_team into target_team.
        Reassigns matches and registrations from source to target, then deletes source.
        """
        if source_team_id == target_team_id:
            return False, "Source and target team cannot be the same."

        src = self.db.execute_one("SELECT name FROM teams WHERE id = ?;", (source_team_id,))
        tgt = self.db.execute_one("SELECT name FROM teams WHERE id = ?;", (target_team_id,))
        if not src or not tgt:
            return False, "One or both teams not found."

        with self.db.transaction() as conn:
            cursor = conn.cursor()
            # Reassign matches
            cursor.execute("UPDATE matches SET home_team_id = ? WHERE home_team_id = ?;", (target_team_id, source_team_id))
            cursor.execute("UPDATE matches SET away_team_id = ? WHERE away_team_id = ?;", (target_team_id, source_team_id))
            cursor.execute("UPDATE matches SET winner_team_id = ? WHERE winner_team_id = ?;", (target_team_id, source_team_id))

            # Reassign registrations
            cursor.execute("UPDATE registration_team_map SET team_id = ? WHERE team_id = ?;", (target_team_id, source_team_id))

            # Delete source team
            cursor.execute("DELETE FROM teams WHERE id = ?;", (source_team_id,))

        return True, f"Successfully merged '{src['name']}' into '{tgt['name']}'."

    def get_teams(
        self,
        search: Optional[str] = None,
        group_id: Optional[int] = None,
        status: Optional[str] = None
    ) -> List[Team]:
        """Retrieve teams with optional filters."""
        query = """
            SELECT t.id, t.name, t.captain_name, t.phone_number, t.status,
                   t.group_id, g.name AS group_name, t.seed, t.logo_path, t.notes, t.created_at
            FROM teams t
            LEFT JOIN groups g ON t.group_id = g.id
            WHERE 1=1
        """
        params = []

        if search and search.strip():
            term = f"%{search.strip()}%"
            query += " AND (t.name LIKE ? OR t.captain_name LIKE ? OR t.phone_number LIKE ?)"
            params.extend([term, term, term])

        if group_id is not None:
            if group_id == -1:  # Unassigned
                query += " AND t.group_id IS NULL"
            else:
                query += " AND t.group_id = ?"
                params.append(group_id)

        if status and status != "All":
            query += " AND t.status = ?"
            params.append(status)

        query += " ORDER BY t.seed DESC, t.name ASC;"
        rows = self.db.execute_query(query, tuple(params))

        return [
            Team(
                id=r["id"],
                name=r["name"],
                captain_name=r["captain_name"] or "",
                phone_number=r["phone_number"] or "",
                status=r["status"],
                group_id=r["group_id"],
                group_name=r["group_name"],
                seed=r["seed"] or 0,
                logo_path=r["logo_path"] or "",
                notes=r["notes"] or "",
                created_at=r["created_at"]
            )
            for r in rows
        ]

    def get_team_by_id(self, team_id: int) -> Optional[Team]:
        row = self.db.execute_one("""
            SELECT t.id, t.name, t.captain_name, t.phone_number, t.status,
                   t.group_id, g.name AS group_name, t.seed, t.logo_path, t.notes, t.created_at
            FROM teams t
            LEFT JOIN groups g ON t.group_id = g.id
            WHERE t.id = ?;
        """, (team_id,))
        if not row:
            return None
        return Team(
            id=row["id"],
            name=row["name"],
            captain_name=row["captain_name"] or "",
            phone_number=row["phone_number"] or "",
            status=row["status"],
            group_id=row["group_id"],
            group_name=row["group_name"],
            seed=row["seed"] or 0,
            logo_path=row["logo_path"] or "",
            notes=row["notes"] or "",
            created_at=row["created_at"]
        )

    def get_team_match_history(self, team_id: int) -> List[Dict[str, Any]]:
        """Get list of matches played or scheduled for this team."""
        query = """
            SELECT m.id, m.match_number, m.stage, m.round_number, m.scheduled_date, m.scheduled_time, m.venue,
                   m.home_team_id, ht.name AS home_name,
                   m.away_team_id, at.name AS away_name,
                   m.home_score, m.away_score, m.status, m.winner_team_id
            FROM matches m
            LEFT JOIN teams ht ON m.home_team_id = ht.id
            LEFT JOIN teams at ON m.away_team_id = at.id
            WHERE m.home_team_id = ? OR m.away_team_id = ?
            ORDER BY m.round_number ASC, m.match_number ASC;
        """
        rows = self.db.execute_query(query, (team_id, team_id))
        history = []
        for r in rows:
            is_home = (r["home_team_id"] == team_id)
            opponent = r["away_name"] if is_home else r["home_name"]
            team_score = r["home_score"] if is_home else r["away_score"]
            opp_score = r["away_score"] if is_home else r["home_score"]

            outcome = "Scheduled"
            if r["status"] in ("Completed", "Walkover") and team_score is not None and opp_score is not None:
                if team_score > opp_score:
                    outcome = "Win"
                elif team_score < opp_score:
                    outcome = "Loss"
                else:
                    outcome = "Draw"

            history.append({
                "match_id": r["id"],
                "match_number": r["match_number"],
                "stage": r["stage"],
                "date": r["scheduled_date"],
                "time": r["scheduled_time"],
                "venue": r["venue"],
                "is_home": is_home,
                "opponent": opponent,
                "team_score": team_score,
                "opp_score": opp_score,
                "outcome": outcome,
                "status": r["status"]
            })
        return history

    def get_team_stats(self, team_id: int) -> Dict[str, Any]:
        """Compute live tournament stats for a specific team."""
        history = self.get_team_match_history(team_id)
        p, w, d, l, gf, ga = 0, 0, 0, 0, 0, 0
        form = []

        win_pts = int(self.db.get_setting("win_points", "3"))
        draw_pts = int(self.db.get_setting("draw_points", "1"))
        loss_pts = int(self.db.get_setting("loss_points", "0"))

        for m in history:
            if m["status"] in ("Completed", "Walkover") and m["team_score"] is not None and m["opp_score"] is not None:
                p += 1
                gf += m["team_score"]
                ga += m["opp_score"]
                if m["outcome"] == "Win":
                    w += 1
                    form.append("W")
                elif m["outcome"] == "Draw":
                    d += 1
                    form.append("D")
                elif m["outcome"] == "Loss":
                    l += 1
                    form.append("L")

        points = (w * win_pts) + (d * draw_pts) + (l * loss_pts)
        return {
            "played": p,
            "won": w,
            "drawn": d,
            "lost": l,
            "goals_for": gf,
            "goals_against": ga,
            "goal_difference": gf - ga,
            "points": points,
            "form": form[-5:]  # last 5 matches
        }

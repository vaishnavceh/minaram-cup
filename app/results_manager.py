"""
Match results service: score entry, validation, audit trailing,
and automatic progression triggers.
"""

import logging
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime

from app.database import Database
from app.models import MatchAudit
from app.knockout_manager import KnockoutManager

logger = logging.getLogger("minaram_cup.results_manager")


class ResultsManager:
    def __init__(self, db: Database):
        self.db = db
        self.knockout_mgr = KnockoutManager(db)

    def record_result(
        self,
        match_id: int,
        home_score: int,
        away_score: int,
        status: str = "Completed",
        home_penalty: Optional[int] = None,
        away_penalty: Optional[int] = None,
        walkover_winner_id: Optional[int] = None,
        notes: str = ""
    ) -> Tuple[bool, str]:
        """
        Record or edit match result with full audit logging and automatic knockout advancement.
        """
        if home_score < 0 or away_score < 0:
            return False, "Scores cannot be negative."

        match = self.db.execute_one("""
            SELECT id, match_number, stage, bracket_slot, home_team_id, away_team_id,
                   home_score, away_score, status, winner_team_id
            FROM matches WHERE id = ?;
        """, (match_id,))
        if not match:
            return False, f"Match ID #{match_id} not found."

        if not match["home_team_id"] or not match["away_team_id"]:
            return False, "Cannot enter score: participating teams are not yet determined."

        if match["home_team_id"] == match["away_team_id"]:
            return False, "Invalid match: Home and away teams cannot be identical."

        # Determine winner
        winner_id = None
        if status == "Walkover":
            if not walkover_winner_id or walkover_winner_id not in (match["home_team_id"], match["away_team_id"]):
                return False, "For a walkover, a valid winning team must be specified."
            winner_id = walkover_winner_id
        elif status == "Completed":
            if home_score > away_score:
                winner_id = match["home_team_id"]
            elif away_score > home_score:
                winner_id = match["away_team_id"]
            else:
                # Tie
                if home_penalty is not None and away_penalty is not None:
                    if home_penalty < 0 or away_penalty < 0:
                        return False, "Penalty scores cannot be negative."
                    if home_penalty > away_penalty:
                        winner_id = match["home_team_id"]
                    elif away_penalty > home_penalty:
                        winner_id = match["away_team_id"]
                    else:
                        if match["stage"] in ("Semi-Final", "Quarter-Final", "Final", "Round of 16"):
                            return False, "Knockout matches cannot end in a draw without a shootout winner."
                else:
                    if match["stage"] in ("Semi-Final", "Quarter-Final", "Final", "Round of 16"):
                        return False, "Knockout matches cannot end in a draw. Please provide penalty shootout scores."

        now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        is_edit = (match["status"] in ("Completed", "Walkover"))
        action_name = "Result Edited" if is_edit else "Result Recorded"
        action_label = "result_edited" if is_edit else "result_recorded"
        with self.db.transaction(action=action_label) as conn:
            cursor = conn.cursor()

            # 1. Update Match Record
            cursor.execute("""
                UPDATE matches
                SET home_score = ?, away_score = ?, home_penalty = ?, away_penalty = ?,
                    status = ?, winner_team_id = ?, completed_at = ?, notes = ?
                WHERE id = ?;
            """, (
                home_score, away_score, home_penalty, away_penalty,
                status, winner_id, now_str, notes.strip(), match_id
            ))

            # 2. Add Audit Trail
            cursor.execute("""
                INSERT INTO match_audit_log (
                    match_id, timestamp, action,
                    old_home_score, old_away_score, old_status,
                    new_home_score, new_away_score, new_status, notes
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
            """, (
                match_id, now_str, action_name,
                match["home_score"], match["away_score"], match["status"],
                home_score, away_score, status, notes.strip()
            ))

        # 3. Knockout advancement if applicable
        if winner_id and match["bracket_slot"]:
            self.knockout_mgr.advance_winner_in_bracket(match_id, winner_id)

        try:
            from app.events import broadcaster
            broadcaster.broadcast_from_thread("result_updated", entity_id=match_id, data={"home_score": home_score, "away_score": away_score})
            broadcaster.broadcast_from_thread("standings_updated")
        except Exception:
            pass

        return True, "Match result saved successfully."

    def reset_result(self, match_id: int, reason: str = "Admin Reset") -> Tuple[bool, str]:
        """Reset a match result back to 'Scheduled' state."""
        match = self.db.execute_one("""
            SELECT id, match_number, home_score, away_score, status, bracket_slot, winner_team_id
            FROM matches WHERE id = ?;
        """, (match_id,))
        if not match:
            return False, "Match not found."

        now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        with self.db.transaction() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE matches
                SET home_score = NULL, away_score = NULL, home_penalty = NULL, away_penalty = NULL,
                    status = 'Scheduled', winner_team_id = NULL, completed_at = ''
                WHERE id = ?;
            """, (match_id,))

            cursor.execute("""
                INSERT INTO match_audit_log (
                    match_id, timestamp, action,
                    old_home_score, old_away_score, old_status,
                    new_home_score, new_away_score, new_status, notes
                ) VALUES (?, ?, 'Result Reset', ?, ?, ?, NULL, NULL, 'Scheduled', ?);
            """, (
                match_id, now_str,
                match["home_score"], match["away_score"], match["status"],
                reason
            ))

        try:
            from app.events import broadcaster
            broadcaster.broadcast_from_thread("result_updated", entity_id=match_id)
            broadcaster.broadcast_from_thread("standings_updated")
        except Exception:
            pass

        return True, "Match result has been reset to Scheduled."

    def get_audit_trail(self, match_id: int) -> List[MatchAudit]:
        """Get the full revision history for a match."""
        rows = self.db.execute_query("""
            SELECT id, match_id, timestamp, action,
                   old_home_score, old_away_score, old_status,
                   new_home_score, new_away_score, new_status, notes
            FROM match_audit_log
            WHERE match_id = ?
            ORDER BY timestamp DESC;
        """, (match_id,))

        return [
            MatchAudit(
                id=r["id"],
                match_id=r["match_id"],
                timestamp=r["timestamp"],
                action=r["action"],
                old_home_score=r["old_home_score"],
                old_away_score=r["old_away_score"],
                old_status=r["old_status"] or "",
                new_home_score=r["new_home_score"],
                new_away_score=r["new_away_score"],
                new_status=r["new_status"] or "",
                notes=r["notes"] or ""
            )
            for r in rows
        ]

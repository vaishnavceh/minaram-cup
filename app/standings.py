"""
Points table and tournament standings calculator.
Supports configurable scoring rules, tie-breaker order (points, goal difference,
goals for, head-to-head, wins), and group qualification flagging.
"""

import logging
from typing import List, Dict, Any, Optional, Tuple
from functools import cmp_to_key

from app.database import Database
from app.models import StandingRow

logger = logging.getLogger("minaram_cup.standings")


class StandingsCalculator:
    def __init__(self, db: Database):
        self.db = db

    def calculate_group_standings(self, group_id: Optional[int] = None) -> List[StandingRow]:
        """
        Calculate standings for a specific group (or league if group_id is None).
        Returns a sorted list of StandingRow with ranks and qualification flags.
        """
        # 1. Fetch teams in this group/league
        if group_id is not None:
            team_rows = self.db.execute_query("""
                SELECT t.id, t.name, t.group_id, g.name AS group_name
                FROM teams t
                LEFT JOIN groups g ON t.group_id = g.id
                WHERE t.group_id = ? AND t.status = 'Confirmed'
                ORDER BY t.name ASC;
            """, (group_id,))
        else:
            team_rows = self.db.execute_query("""
                SELECT t.id, t.name, t.group_id, g.name AS group_name
                FROM teams t
                LEFT JOIN groups g ON t.group_id = g.id
                WHERE t.status = 'Confirmed'
                ORDER BY t.name ASC;
            """)

        if not team_rows:
            return []

        # 2. Fetch completed matches
        if group_id is not None:
            match_rows = self.db.execute_query("""
                SELECT id, home_team_id, away_team_id, home_score, away_score, status, winner_team_id
                FROM matches
                WHERE group_id = ? AND status IN ('Completed', 'Walkover')
                  AND home_score IS NOT NULL AND away_score IS NOT NULL;
            """, (group_id,))
        else:
            match_rows = self.db.execute_query("""
                SELECT id, home_team_id, away_team_id, home_score, away_score, status, winner_team_id
                FROM matches
                WHERE stage = 'League' AND status IN ('Completed', 'Walkover')
                  AND home_score IS NOT NULL AND away_score IS NOT NULL;
            """)

        # Settings
        win_pts = int(self.db.get_setting("win_points", "3"))
        draw_pts = int(self.db.get_setting("draw_points", "1"))
        loss_pts = int(self.db.get_setting("loss_points", "0"))
        tie_breakers_str = self.db.get_setting("tie_breakers", "points,goal_difference,goals_for,head_to_head,won")
        tie_breakers = [t.strip().lower() for t in tie_breakers_str.split(",") if t.strip()]

        qualifiers_count = int(self.db.get_setting("qualifiers_per_group", "2"))

        # Initialize team record dict
        stats: Dict[int, Dict[str, Any]] = {}
        for tr in team_rows:
            stats[tr["id"]] = {
                "team_id": tr["id"],
                "team_name": tr["name"],
                "group_id": tr["group_id"],
                "group_name": tr["group_name"],
                "played": 0,
                "won": 0,
                "drawn": 0,
                "lost": 0,
                "goals_for": 0,
                "goals_against": 0,
                "goal_difference": 0,
                "points": 0,
                "form": [],
            }

        # Process matches
        # Keep head-to-head records map: (team_a, team_b) -> points_a, gd_a
        h2h: Dict[Tuple[int, int], Dict[str, int]] = {}

        for mr in match_rows:
            h_id = mr["home_team_id"]
            a_id = mr["away_team_id"]
            h_score = mr["home_score"]
            a_score = mr["away_score"]

            if h_id not in stats or a_id not in stats:
                continue

            stats[h_id]["played"] += 1
            stats[a_id]["played"] += 1

            stats[h_id]["goals_for"] += h_score
            stats[h_id]["goals_against"] += a_score
            stats[a_id]["goals_for"] += a_score
            stats[a_id]["goals_against"] += h_score

            h2h.setdefault((h_id, a_id), {"points": 0, "gf": 0, "ga": 0})
            h2h.setdefault((a_id, h_id), {"points": 0, "gf": 0, "ga": 0})

            h2h[(h_id, a_id)]["gf"] += h_score
            h2h[(h_id, a_id)]["ga"] += a_score
            h2h[(a_id, h_id)]["gf"] += a_score
            h2h[(a_id, h_id)]["ga"] += h_score

            if h_score > a_score:
                stats[h_id]["won"] += 1
                stats[h_id]["points"] += win_pts
                stats[h_id]["form"].append("W")
                stats[a_id]["lost"] += 1
                stats[a_id]["points"] += loss_pts
                stats[a_id]["form"].append("L")
                h2h[(h_id, a_id)]["points"] += win_pts
                h2h[(a_id, h_id)]["points"] += loss_pts
            elif h_score < a_score:
                stats[a_id]["won"] += 1
                stats[a_id]["points"] += win_pts
                stats[a_id]["form"].append("W")
                stats[h_id]["lost"] += 1
                stats[h_id]["points"] += loss_pts
                stats[h_id]["form"].append("L")
                h2h[(a_id, h_id)]["points"] += win_pts
                h2h[(h_id, a_id)]["points"] += loss_pts
            else:
                stats[h_id]["drawn"] += 1
                stats[h_id]["points"] += draw_pts
                stats[h_id]["form"].append("D")
                stats[a_id]["drawn"] += 1
                stats[a_id]["points"] += draw_pts
                stats[a_id]["form"].append("D")
                h2h[(h_id, a_id)]["points"] += draw_pts
                h2h[(a_id, h_id)]["points"] += draw_pts

        for s in stats.values():
            s["goal_difference"] = s["goals_for"] - s["goals_against"]

        # Sorting comparator with tie-breakers
        def compare_teams(a: Dict[str, Any], b: Dict[str, Any]) -> int:
            for tb in tie_breakers:
                if tb == "points":
                    if a["points"] != b["points"]:
                        return 1 if a["points"] < b["points"] else -1
                elif tb in ("goal_difference", "goal_diff", "gd"):
                    if a["goal_difference"] != b["goal_difference"]:
                        return 1 if a["goal_difference"] < b["goal_difference"] else -1
                elif tb in ("goals_for", "gf", "goals_scored"):
                    if a["goals_for"] != b["goals_for"]:
                        return 1 if a["goals_for"] < b["goals_for"] else -1
                elif tb in ("won", "wins"):
                    if a["won"] != b["won"]:
                        return 1 if a["won"] < b["won"] else -1
                elif tb in ("head_to_head", "h2h"):
                    # Check mutual record between a and b
                    rec_a = h2h.get((a["team_id"], b["team_id"]))
                    rec_b = h2h.get((b["team_id"], a["team_id"]))
                    if rec_a and rec_b and rec_a["points"] != rec_b["points"]:
                        return 1 if rec_a["points"] < rec_b["points"] else -1

            # Fallback alphabetical
            if a["team_name"].lower() != b["team_name"].lower():
                return 1 if a["team_name"].lower() > b["team_name"].lower() else -1
            return 0

        sorted_stats = sorted(stats.values(), key=cmp_to_key(compare_teams))

        results = []
        for idx, s in enumerate(sorted_stats, start=1):
            is_qual = (idx <= qualifiers_count) and (s["played"] > 0 or len(sorted_stats) <= qualifiers_count)
            results.append(StandingRow(
                team_id=s["team_id"],
                team_name=s["team_name"],
                group_id=s["group_id"],
                group_name=s["group_name"],
                played=s["played"],
                won=s["won"],
                drawn=s["drawn"],
                lost=s["lost"],
                goals_for=s["goals_for"],
                goals_against=s["goals_against"],
                goal_difference=s["goal_difference"],
                points=s["points"],
                form=s["form"][-5:],
                is_qualified=is_qual,
                rank=idx
            ))

        return results

    def calculate_all_groups_standings(self) -> Dict[str, List[StandingRow]]:
        """Calculate standings for all groups in group stage."""
        groups = self.db.execute_query("SELECT id, name FROM groups ORDER BY display_order ASC, name ASC;")
        res = {}
        for g in groups:
            res[g["name"]] = self.calculate_group_standings(group_id=g["id"])
        return res

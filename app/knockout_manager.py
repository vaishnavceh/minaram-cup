"""
Knockout stage tournament management, bracket generation,
and progression tracking.
"""

import logging
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, timedelta

from app.database import Database
from app.models import Match
from app.standings import StandingsCalculator

logger = logging.getLogger("minaram_cup.knockout")

SLOT_PROGRESSION = {
    # 8-team QF progression
    "QF1": ("SF1", "home"),
    "QF2": ("SF1", "away"),
    "QF3": ("SF2", "home"),
    "QF4": ("SF2", "away"),
    # 4-team SF progression
    "SF1": ("F", "home"),
    "SF2": ("F", "away"),
    # 16-team R16 progression
    "R16_1": ("QF1", "home"),
    "R16_2": ("QF1", "away"),
    "R16_3": ("QF2", "home"),
    "R16_4": ("QF2", "away"),
    "R16_5": ("QF3", "home"),
    "R16_6": ("QF3", "away"),
    "R16_7": ("QF4", "home"),
    "R16_8": ("QF4", "away"),
}


class KnockoutManager:
    def __init__(self, db: Database):
        self.db = db
        self.standings = StandingsCalculator(db)

    def generate_bracket_from_group_qualifiers(
        self,
        start_date: str = "",
        start_time: str = "15:00",
        match_duration_mins: int = 90,
        venue: str = "Minaram Stadium"
    ) -> List[Dict[str, Any]]:
        """
        Generate knockout bracket from group stage qualifiers:
        2 groups -> Semifinals + Final
        4 groups -> Quarterfinals + Semifinals + Final
        """
        group_standings = self.standings.calculate_all_groups_standings()
        group_names = sorted(list(group_standings.keys()))

        if len(group_names) < 2:
            raise ValueError("Knockout bracket generation requires at least 2 groups with standings.")

        if not start_date:
            start_date = (datetime.now() + timedelta(days=2)).strftime("%Y-%m-%d")

        curr_dt = datetime.strptime(f"{start_date} {start_time}", "%Y-%m-%d %H:%M")

        # Get existing max match number
        max_num = self.db.execute_one("SELECT MAX(match_number) AS m FROM matches;")["m"] or 0
        match_num = max_num + 1

        fixtures = []

        if len(group_names) == 2:
            # Group A & Group B -> 4 teams -> Semi-finals & Final
            ga_teams = group_standings.get(group_names[0], [])
            gb_teams = group_standings.get(group_names[1], [])

            a1 = ga_teams[0].team_id if len(ga_teams) > 0 else None
            a1_name = ga_teams[0].team_name if len(ga_teams) > 0 else f"1st {group_names[0]}"
            a2 = ga_teams[1].team_id if len(ga_teams) > 1 else None
            a2_name = ga_teams[1].team_name if len(ga_teams) > 1 else f"2nd {group_names[0]}"

            b1 = gb_teams[0].team_id if len(gb_teams) > 0 else None
            b1_name = gb_teams[0].team_name if len(gb_teams) > 0 else f"1st {group_names[1]}"
            b2 = gb_teams[1].team_id if len(gb_teams) > 1 else None
            b2_name = gb_teams[1].team_name if len(gb_teams) > 1 else f"2nd {group_names[1]}"

            # SF1: 1st A vs 2nd B
            fixtures.append({
                "match_number": match_num,
                "stage": "Semi-Final",
                "round_number": 1,
                "bracket_slot": "SF1",
                "home_team_id": a1,
                "away_team_id": b2,
                "home_team_name": a1_name,
                "away_team_name": b2_name,
                "scheduled_date": curr_dt.strftime("%Y-%m-%d"),
                "scheduled_time": curr_dt.strftime("%H:%M"),
                "venue": venue,
                "status": "Scheduled",
                "notes": "Semi-Final 1"
            })
            match_num += 1
            curr_dt += timedelta(minutes=match_duration_mins)

            # SF2: 1st B vs 2nd A
            fixtures.append({
                "match_number": match_num,
                "stage": "Semi-Final",
                "round_number": 1,
                "bracket_slot": "SF2",
                "home_team_id": b1,
                "away_team_id": a2,
                "home_team_name": b1_name,
                "away_team_name": a2_name,
                "scheduled_date": curr_dt.strftime("%Y-%m-%d"),
                "scheduled_time": curr_dt.strftime("%H:%M"),
                "venue": venue,
                "status": "Scheduled",
                "notes": "Semi-Final 2"
            })
            match_num += 1
            curr_dt += timedelta(days=1, hours=-2)  # Final on next day

            # Final: Winner SF1 vs Winner SF2
            fixtures.append({
                "match_number": match_num,
                "stage": "Final",
                "round_number": 2,
                "bracket_slot": "F",
                "home_team_id": None,
                "away_team_id": None,
                "home_team_name": "Winner SF1",
                "away_team_name": "Winner SF2",
                "scheduled_date": curr_dt.strftime("%Y-%m-%d"),
                "scheduled_time": curr_dt.strftime("%H:%M"),
                "venue": venue,
                "status": "Scheduled",
                "notes": "Minaram Cup Final"
            })

        elif len(group_names) >= 4:
            # 4 Groups: A, B, C, D -> 8 teams -> Quarter-finals, Semi-finals, Final
            g = [group_standings.get(gn, []) for gn in group_names[:4]]

            qf_pairings = [
                ("QF1", g[0], 0, g[1], 1, f"1st {group_names[0]}", f"2nd {group_names[1]}"),
                ("QF2", g[2], 0, g[3], 1, f"1st {group_names[2]}", f"2nd {group_names[3]}"),
                ("QF3", g[1], 0, g[0], 1, f"1st {group_names[1]}", f"2nd {group_names[0]}"),
                ("QF4", g[3], 0, g[2], 1, f"1st {group_names[3]}", f"2nd {group_names[2]}"),
            ]

            for slot, g_home, h_idx, g_away, a_idx, def_h_name, def_a_name in qf_pairings:
                h_id = g_home[h_idx].team_id if len(g_home) > h_idx else None
                h_name = g_home[h_idx].team_name if len(g_home) > h_idx else def_h_name
                a_id = g_away[a_idx].team_id if len(g_away) > a_idx else None
                a_name = g_away[a_idx].team_name if len(g_away) > a_idx else def_a_name

                fixtures.append({
                    "match_number": match_num,
                    "stage": "Quarter-Final",
                    "round_number": 1,
                    "bracket_slot": slot,
                    "home_team_id": h_id,
                    "away_team_id": a_id,
                    "home_team_name": h_name,
                    "away_team_name": a_name,
                    "scheduled_date": curr_dt.strftime("%Y-%m-%d"),
                    "scheduled_time": curr_dt.strftime("%H:%M"),
                    "venue": venue,
                    "status": "Scheduled",
                    "notes": f"Quarter-Final ({slot})"
                })
                match_num += 1
                curr_dt += timedelta(minutes=match_duration_mins)

            curr_dt += timedelta(days=1)
            # SF1 & SF2
            fixtures.append({
                "match_number": match_num,
                "stage": "Semi-Final",
                "round_number": 2,
                "bracket_slot": "SF1",
                "home_team_id": None,
                "away_team_id": None,
                "home_team_name": "Winner QF1",
                "away_team_name": "Winner QF2",
                "scheduled_date": curr_dt.strftime("%Y-%m-%d"),
                "scheduled_time": curr_dt.strftime("%H:%M"),
                "venue": venue,
                "status": "Scheduled",
                "notes": "Semi-Final 1"
            })
            match_num += 1
            curr_dt += timedelta(minutes=match_duration_mins)

            fixtures.append({
                "match_number": match_num,
                "stage": "Semi-Final",
                "round_number": 2,
                "bracket_slot": "SF2",
                "home_team_id": None,
                "away_team_id": None,
                "home_team_name": "Winner QF3",
                "away_team_name": "Winner QF4",
                "scheduled_date": curr_dt.strftime("%Y-%m-%d"),
                "scheduled_time": curr_dt.strftime("%H:%M"),
                "venue": venue,
                "status": "Scheduled",
                "notes": "Semi-Final 2"
            })
            match_num += 1
            curr_dt += timedelta(days=1)

            # Final
            fixtures.append({
                "match_number": match_num,
                "stage": "Final",
                "round_number": 3,
                "bracket_slot": "F",
                "home_team_id": None,
                "away_team_id": None,
                "home_team_name": "Winner SF1",
                "away_team_name": "Winner SF2",
                "scheduled_date": curr_dt.strftime("%Y-%m-%d"),
                "scheduled_time": curr_dt.strftime("%H:%M"),
                "venue": venue,
                "status": "Scheduled",
                "notes": "Minaram Cup Grand Final"
            })

        return fixtures

    def advance_winner_in_bracket(self, completed_match_id: int, winner_team_id: int) -> Optional[int]:
        """
        Advance winner of completed_match into the next round's bracket match.
        Returns the next match id if updated, or None.
        """
        m = self.db.execute_one("SELECT bracket_slot FROM matches WHERE id = ?;", (completed_match_id,))
        if not m or not m["bracket_slot"]:
            return None

        slot = m["bracket_slot"]
        target = SLOT_PROGRESSION.get(slot)
        if not target:
            return None

        target_slot, target_side = target

        # Find target match in matches table
        target_m = self.db.execute_one("SELECT id FROM matches WHERE bracket_slot = ?;", (target_slot,))
        if not target_m:
            return None

        target_id = target_m["id"]
        field_to_update = "home_team_id" if target_side == "home" else "away_team_id"

        self.db.execute_non_query(
            f"UPDATE matches SET {field_to_update} = ? WHERE id = ?;",
            (winner_team_id, target_id)
        )
        return target_id

    def get_bracket_structure(self) -> Dict[str, List[Match]]:
        """
        Fetch all knockout matches grouped by stage in chronological tournament order:
        Round of 16 -> Quarter-Final -> Semi-Final -> Final
        """
        stages_order = ["Round of 16", "Quarter-Final", "Semi-Final", "Final"]
        result = {}

        for stg in stages_order:
            matches_in_stage = self.db.execute_query("""
                SELECT m.id, m.match_number, m.stage, m.round_number, m.bracket_slot,
                       m.home_team_id, ht.name AS home_name,
                       m.away_team_id, at.name AS away_name,
                       m.scheduled_date, m.scheduled_time, m.venue,
                       m.home_score, m.away_score, m.home_penalty, m.away_penalty,
                       m.status, m.winner_team_id, wt.name AS winner_name,
                       m.notes, m.completed_at
                FROM matches m
                LEFT JOIN teams ht ON m.home_team_id = ht.id
                LEFT JOIN teams at ON m.away_team_id = at.id
                LEFT JOIN teams wt ON m.winner_team_id = wt.id
                WHERE m.stage = ?
                ORDER BY m.bracket_slot ASC, m.match_number ASC;
            """, (stg,))

            if matches_in_stage:
                result[stg] = [
                    Match(
                        id=r["id"],
                        match_number=r["match_number"],
                        stage=r["stage"],
                        round_number=r["round_number"],
                        bracket_slot=r["bracket_slot"] or "",
                        home_team_id=r["home_team_id"],
                        away_team_id=r["away_team_id"],
                        home_team_name=r["home_name"] or "TBD",
                        away_team_name=r["away_name"] or "TBD",
                        scheduled_date=r["scheduled_date"] or "",
                        scheduled_time=r["scheduled_time"] or "",
                        venue=r["venue"] or "",
                        home_score=r["home_score"],
                        away_score=r["away_score"],
                        home_penalty=r["home_penalty"],
                        away_penalty=r["away_penalty"],
                        status=r["status"],
                        winner_team_id=r["winner_team_id"],
                        winner_team_name=r["winner_name"],
                        notes=r["notes"] or "",
                        completed_at=r["completed_at"] or ""
                    )
                    for r in rows_to_list(matches_in_stage)
                ]

        return result


def rows_to_list(rows):
    return list(rows)

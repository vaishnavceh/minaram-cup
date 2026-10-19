"""
Knockout Stage Tournament Management System for Minaram Cup 2026.
Supports:
- Dynamic calculation of 30 qualified teams from 15 groups (A through O)
- Two Direct Round of 16 Qualifiers ranking and administrator overrides
- Preliminary Draw (Seeded & Reproducible Random)
- 29-match Knockout Format (Preliminary Round ➔ R16 ➔ QF ➔ SF ➔ Final + 3rd Place)
- Separation of Predicted Snapshots vs Official Confirmed Fixtures
- Result confirmation, winner advancement, walkovers, disputes (Under Review)
- Bracket integrity validation and conflict detection
"""

import json
import logging
import hashlib
import random
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, timedelta

from app.database import Database
from app.models import Match
from app.standings import StandingsCalculator

logger = logging.getLogger("minaram_cup.knockout")

# Complete Slot Progression for the 30-team Knockout Tree
# Preliminary Round (14 matches: PR1 to PR14)
# Round of 16 (8 matches: R16_1 to R16_8)
# Quarter-Finals (4 matches: QF1 to QF4)
# Semi-Finals (2 matches: SF1 to SF2)
# Grand Final (1 match: F)
# Optional 3rd Place Playoff (1 match: 3RD)
SLOT_PROGRESSION = {
    # Preliminary winners advance to designated R16 slots
    "PR1": ("R16_1", "away"),
    "PR2": ("R16_2", "home"),
    "PR3": ("R16_2", "away"),
    "PR4": ("R16_3", "home"),
    "PR5": ("R16_3", "away"),
    "PR6": ("R16_4", "home"),
    "PR7": ("R16_4", "away"),
    "PR8": ("R16_5", "away"),
    "PR9": ("R16_6", "home"),
    "PR10": ("R16_6", "away"),
    "PR11": ("R16_7", "home"),
    "PR12": ("R16_7", "away"),
    "PR13": ("R16_8", "home"),
    "PR14": ("R16_8", "away"),
    # Round of 16 winners advance to QF
    "R16_1": ("QF1", "home"),
    "R16_2": ("QF1", "away"),
    "R16_3": ("QF2", "home"),
    "R16_4": ("QF2", "away"),
    "R16_5": ("QF3", "home"),
    "R16_6": ("QF3", "away"),
    "R16_7": ("QF4", "home"),
    "R16_8": ("QF4", "away"),
    # Quarter-Final winners advance to SF
    "QF1": ("SF1", "home"),
    "QF2": ("SF1", "away"),
    "QF3": ("SF2", "home"),
    "QF4": ("SF2", "away"),
    # Semi-Final winners advance to Final
    "SF1": ("F", "home"),
    "SF2": ("F", "away"),
}

SLOT_LOSER_PROGRESSION = {
    "SF1": ("3RD", "home"),
    "SF2": ("3RD", "away"),
}

# Direct Round of 16 seed positions (placed on opposite halves of the bracket tree)
DIRECT_R16_SLOTS = {
    0: ("R16_1", "home"),  # Direct Qualifier #1
    1: ("R16_5", "home"),  # Direct Qualifier #2
}


class KnockoutManager:
    def __init__(self, db: Database):
        self.db = db
        self.standings = StandingsCalculator(db)

    # -------------------------------------------------------------------------
    # 1. QUALIFICATION LOGIC: 30 TEAMS FROM 15 GROUPS
    # -------------------------------------------------------------------------
    def get_qualified_teams(self) -> Dict[str, Any]:
        """
        Calculate the 30 qualifying teams from the 15 groups (top 2 per group).
        Handles provisional statuses if a group has remaining unplayed matches.
        """
        groups = self.db.execute_query("SELECT id, name FROM groups ORDER BY display_order ASC, name ASC;")
        qualified_teams = []
        is_any_provisional = False
        group_statuses = {}

        for g in groups:
            g_id = g["id"]
            g_name = g["name"]
            standings_rows = self.standings.calculate_group_standings(group_id=g_id)

            # Check for unplayed matches in this group
            unplayed_cnt = self.db.execute_one("""
                SELECT COUNT(*) AS c FROM matches
                WHERE group_id = ? AND status NOT IN ('Completed', 'Walkover');
            """, (g_id,))["c"]
            is_group_provisional = (unplayed_cnt > 0)
            if is_group_provisional:
                is_any_provisional = True

            group_statuses[g_name] = {
                "is_provisional": is_group_provisional,
                "unplayed_matches": unplayed_cnt,
            }

            # Top 2 teams qualify
            for rank_idx, row in enumerate(standings_rows[:2], start=1):
                p = row.played
                ppm = round(row.points / p, 2) if p > 0 else 0.0
                gpm = round(row.goals_for / p, 2) if p > 0 else 0.0

                pos_str = "1st" if rank_idx == 1 else "2nd"
                team_data = {
                    "team_id": row.team_id,
                    "team_name": row.team_name,
                    "group_id": g_id,
                    "group_name": g_name,
                    "group_position": pos_str,
                    "rank_in_group": rank_idx,
                    "played": row.played,
                    "won": row.won,
                    "drawn": row.drawn,
                    "lost": row.lost,
                    "goals_for": row.goals_for,
                    "goals_against": row.goals_against,
                    "goal_difference": row.goal_difference,
                    "points": row.points,
                    "points_per_match": ppm,
                    "goals_per_match": gpm,
                    "is_provisional": is_group_provisional,
                    "criteria_summary": f"GF: {row.goals_for} · GD: {row.goal_difference:+d} · Pts/M: {ppm:.2f} · GF/M: {gpm:.2f}"
                }
                qualified_teams.append(team_data)

        return {
            "teams": qualified_teams,
            "total_qualified": len(qualified_teams),
            "is_provisional": is_any_provisional,
            "group_statuses": group_statuses
        }

    # -------------------------------------------------------------------------
    # 2. TWO DIRECT ROUND OF 16 QUALIFIERS
    # -------------------------------------------------------------------------
    def get_direct_qualifiers(self, qualified_teams: Optional[List[Dict[str, Any]]] = None) -> Dict[str, Any]:
        """
        Rank all qualified teams using strict criteria in order:
        1. Highest total Goals For (GF)
        2. Highest Goal Difference (GD)
        3. Highest points per match
        4. Highest goals per match
        5. Tied fallback: alphabetical / ID.
        Checks for manual admin overrides and returns both recommendation and final selection.
        """
        if qualified_teams is None:
            qualified_teams = self.get_qualified_teams()["teams"]

        # Sort all 30 qualified teams by defined ranking procedure
        ranked = sorted(
            qualified_teams,
            key=lambda t: (
                t["goals_for"],
                t["goal_difference"],
                t["points_per_match"],
                t["goals_per_match"],
                -t["team_id"]
            ),
            reverse=True
        )

        recommended = ranked[:2]

        # Check for administrator overrides
        override_rows = self.db.execute_query("""
            SELECT o.slot_index, o.team_id, o.reason, o.admin_username, o.updated_at,
                   t.name AS team_name, t.group_id, g.name AS group_name
            FROM knockout_direct_overrides o
            JOIN teams t ON o.team_id = t.id
            LEFT JOIN groups g ON t.group_id = g.id
            ORDER BY o.slot_index ASC;
        """)

        overrides_map = {r["slot_index"]: dict(r) for r in override_rows}
        final_direct_qualifiers = []
        has_any_override = False

        for slot_idx in range(2):
            if slot_idx in overrides_map:
                has_any_override = True
                ov = overrides_map[slot_idx]
                # Look up full stats from qualified teams if present
                team_info = next((t for t in qualified_teams if t["team_id"] == ov["team_id"]), None)
                if not team_info:
                    # In case overridden team is outside top 2 (e.g. manual administrative ruling)
                    team_info = {
                        "team_id": ov["team_id"],
                        "team_name": ov["team_name"],
                        "group_id": ov["group_id"],
                        "group_name": ov["group_name"] or "Manual Override",
                        "group_position": "Admin Assigned",
                        "rank_in_group": 1,
                        "played": 0, "won": 0, "drawn": 0, "lost": 0,
                        "goals_for": 0, "goals_against": 0, "goal_difference": 0, "points": 0,
                        "points_per_match": 0.0, "goals_per_match": 0.0,
                        "is_provisional": False,
                        "criteria_summary": f"Admin Override: {ov['reason']}"
                    }
                dq_copy = dict(team_info)
                dq_copy["is_override"] = True
                dq_copy["override_reason"] = ov["reason"]
                dq_copy["override_by"] = ov["admin_username"]
                dq_copy["override_at"] = ov["updated_at"]
                dq_copy["recommended_alternate"] = recommended[slot_idx] if slot_idx < len(recommended) else None
                final_direct_qualifiers.append(dq_copy)
            else:
                if slot_idx < len(recommended):
                    dq_copy = dict(recommended[slot_idx])
                    dq_copy["is_override"] = False
                    final_direct_qualifiers.append(dq_copy)

        return {
            "direct_qualifiers": final_direct_qualifiers,
            "recommended_qualifiers": recommended,
            "has_override": has_any_override,
            "all_ranked_candidates": ranked,
            "criteria_order": [
                "1. Highest Total Goals For (GF)",
                "2. Highest Goal Difference (GD)",
                "3. Highest Points Per Match",
                "4. Highest Goals Per Match",
                "5. Transparent Admin Draw / Seed"
            ]
        }

    # -------------------------------------------------------------------------
    # 3. AUTOMATIC PRELIMINARY DRAW (14 MATCHES, 28 TEAMS)
    # -------------------------------------------------------------------------
    def generate_preliminary_draw(
        self,
        qualified_teams: List[Dict[str, Any]],
        direct_qualifiers: List[Dict[str, Any]],
        draw_method: str = "seeded",
        seed_value: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Form the 14 preliminary round matches from the 28 remaining teams:
        - Excludes the 2 direct qualifiers.
        - Avoids matching teams from the same group wherever possible.
        - Ensures every eligible team appears exactly once.
        - Reproducible and snapshot-persisted.
        """
        direct_ids = {dq["team_id"] for dq in direct_qualifiers}
        prelim_pool = [t for t in qualified_teams if t["team_id"] not in direct_ids]

        if len(prelim_pool) < 28:
            logger.warning(f"Preliminary pool has {len(prelim_pool)} teams instead of 28.")

        fixtures = []
        assigned_matches = []

        if draw_method == "random":
            # Deterministic reproducible random shuffle
            rng_seed = seed_value or hashlib.sha256(
                "".join(sorted(str(t["team_id"]) for t in prelim_pool)).encode()
            ).hexdigest()
            rng = random.Random(rng_seed)
            pool_shuffled = list(prelim_pool)
            rng.shuffle(pool_shuffled)

            # Pair adjacent teams with same-group clash resolution
            paired: List[Tuple[Dict[str, Any], Dict[str, Any]]] = []
            while pool_shuffled:
                home = pool_shuffled.pop(0)
                # Find best away opponent that doesn't share group
                away_idx = -1
                for idx, candidate in enumerate(pool_shuffled):
                    if candidate["group_name"] != home["group_name"]:
                        away_idx = idx
                        break
                if away_idx == -1 and pool_shuffled:
                    away_idx = 0  # Fallback if unavoidable
                away = pool_shuffled.pop(away_idx) if away_idx >= 0 else {"team_id": None, "team_name": "TBD", "group_name": "TBD"}
                paired.append((home, away))

            for idx, (h, a) in enumerate(paired, start=1):
                assigned_matches.append((idx, h, a))

        else:
            # "seeded" draw:
            # Pot 1: Group winners (1st place in group)
            # Pot 2: Group runners-up (2nd place in group)
            pot1 = [t for t in prelim_pool if t.get("rank_in_group", 1) == 1]
            pot2 = [t for t in prelim_pool if t.get("rank_in_group", 1) == 2]

            # Balance pots if DQ came from pot1 or pot2
            if len(pot1) > 14:
                pot2.extend(pot1[14:])
                pot1 = pot1[:14]
            elif len(pot2) > 14:
                pot1.extend(pot2[14:])
                pot2 = pot2[:14]

            # Sort both pots by performance (GF desc, GD desc, Points desc)
            pot1_sorted = sorted(pot1, key=lambda x: (x["goals_for"], x["goal_difference"], x["points"]), reverse=True)
            pot2_sorted = sorted(pot2, key=lambda x: (x["goals_for"], x["goal_difference"], x["points"]), reverse=True)

            pot2_available = list(pot2_sorted)
            paired = []

            for h in pot1_sorted:
                chosen_idx = -1
                for idx, candidate in enumerate(pot2_available):
                    if candidate["group_name"] != h["group_name"]:
                        chosen_idx = idx
                        break
                if chosen_idx == -1 and pot2_available:
                    chosen_idx = 0
                if chosen_idx >= 0:
                    a = pot2_available.pop(chosen_idx)
                else:
                    a = {"team_id": None, "team_name": "TBD", "group_name": "TBD"}
                paired.append((h, a))

            for idx, (h, a) in enumerate(paired, start=1):
                assigned_matches.append((idx, h, a))

        # Build 14 match structures
        for match_num, home_t, away_t in assigned_matches:
            slot = f"PR{match_num}"
            fixtures.append({
                "stage": "Preliminary Round",
                "round_number": 1,
                "match_number": match_num,
                "bracket_slot": slot,
                "home_team_id": home_t.get("team_id"),
                "away_team_id": away_t.get("team_id"),
                "home_team_name": home_t.get("team_name", "TBD"),
                "away_team_name": away_t.get("team_name", "TBD"),
                "home_group": home_t.get("group_name", "TBD"),
                "away_group": away_t.get("group_name", "TBD"),
                "home_placeholder": f"Seed {match_num}A",
                "away_placeholder": f"Seed {match_num}B",
                "status": "PREDICTED",
                "home_score": None,
                "away_score": None,
                "home_penalty": None,
                "away_penalty": None,
                "winner_team_id": None,
                "winner_team_name": None,
                "scheduled_date": "2026-10-24",
                "scheduled_time": "Flexible (MW Window)",
                "venue": "Minaram Pitch 1",
                "notes": f"Preliminary Round Match {match_num}"
            })

        return fixtures

    # -------------------------------------------------------------------------
    # 4. PREDICT THE COMPLETE KNOCKOUT BRACKET (FULL TOURNAMENT TREE)
    # -------------------------------------------------------------------------
    def build_complete_predicted_bracket(
        self,
        direct_qualifiers: List[Dict[str, Any]],
        preliminary_fixtures: List[Dict[str, Any]],
        third_place_enabled: bool = False
    ) -> Dict[str, List[Dict[str, Any]]]:
        """
        Build complete connected bracket tree across all rounds:
        - Preliminary Round (14 matches: PR1 to PR14)
        - Round of 16 (8 matches: R16_1 to R16_8)
        - Quarter-Finals (4 matches: QF1 to QF4)
        - Semi-Finals (2 matches: SF1 to SF2)
        - Grand Final (1 match: F)
        - Optional 3rd Place Playoff (1 match: 3RD)
        """
        tree: Dict[str, List[Dict[str, Any]]] = {
            "Preliminary Round": preliminary_fixtures,
            "Round of 16": [],
            "Quarter-Final": [],
            "Semi-Final": [],
            "Final": []
        }

        dq1 = direct_qualifiers[0] if len(direct_qualifiers) > 0 else {}
        dq2 = direct_qualifiers[1] if len(direct_qualifiers) > 1 else {}

        # Round of 16 (8 matches)
        # Symmetrical placement:
        # R16_1: DQ1 vs Winner PR1
        # R16_2: Winner PR2 vs Winner PR3
        # R16_3: Winner PR4 vs Winner PR5
        # R16_4: Winner PR6 vs Winner PR7
        # R16_5: DQ2 vs Winner PR8
        # R16_6: Winner PR9 vs Winner PR10
        # R16_7: Winner PR11 vs Winner PR12
        # R16_8: Winner PR13 vs Winner PR14
        r16_pairings = [
            ("R16_1", 15, dq1.get("team_id"), dq1.get("team_name"), dq1.get("group_name"), "Direct Qualifier #1", None, "Winner of PR1", "PR1", "Winner of PR1"),
            ("R16_2", 16, None, "Winner of PR2", "PR2", "Winner of PR2", None, "Winner of PR3", "PR3", "Winner of PR3"),
            ("R16_3", 17, None, "Winner of PR4", "PR4", "Winner of PR4", None, "Winner of PR5", "PR5", "Winner of PR5"),
            ("R16_4", 18, None, "Winner of PR6", "PR6", "Winner of PR6", None, "Winner of PR7", "PR7", "Winner of PR7"),
            ("R16_5", 19, dq2.get("team_id"), dq2.get("team_name"), dq2.get("group_name"), "Direct Qualifier #2", None, "Winner of PR8", "PR8", "Winner of PR8"),
            ("R16_6", 20, None, "Winner of PR9", "PR9", "Winner of PR9", None, "Winner of PR10", "PR10", "Winner of PR10"),
            ("R16_7", 21, None, "Winner of PR11", "PR11", "Winner of PR11", None, "Winner of PR12", "PR12", "Winner of PR12"),
            ("R16_8", 22, None, "Winner of PR13", "PR13", "Winner of PR13", None, "Winner of PR14", "PR14", "Winner of PR14"),
        ]

        for slot, m_num, h_id, h_name, h_grp, h_ph, a_id, a_name, a_grp, a_ph in r16_pairings:
            tree["Round of 16"].append({
                "stage": "Round of 16",
                "round_number": 2,
                "match_number": m_num,
                "bracket_slot": slot,
                "home_team_id": h_id,
                "away_team_id": a_id,
                "home_team_name": h_name or h_ph,
                "away_team_name": a_name or a_ph,
                "home_group": h_grp or "",
                "away_group": a_grp or "",
                "home_placeholder": h_ph,
                "away_placeholder": a_ph,
                "status": "PREDICTED",
                "home_score": None,
                "away_score": None,
                "home_penalty": None,
                "away_penalty": None,
                "winner_team_id": None,
                "winner_team_name": None,
                "scheduled_date": "2026-10-26",
                "scheduled_time": "Flexible (MW Window)",
                "venue": "Minaram Pitch 1",
                "notes": f"Round of 16 ({slot})"
            })

        # Quarter-Finals (4 matches)
        qf_pairings = [
            ("QF1", 23, "Winner of R16_1", "Winner of R16_2"),
            ("QF2", 24, "Winner of R16_3", "Winner of R16_4"),
            ("QF3", 25, "Winner of R16_5", "Winner of R16_6"),
            ("QF4", 26, "Winner of R16_7", "Winner of R16_8"),
        ]
        for slot, m_num, h_ph, a_ph in qf_pairings:
            tree["Quarter-Final"].append({
                "stage": "Quarter-Final",
                "round_number": 3,
                "match_number": m_num,
                "bracket_slot": slot,
                "home_team_id": None,
                "away_team_id": None,
                "home_team_name": h_ph,
                "away_team_name": a_ph,
                "home_placeholder": h_ph,
                "away_placeholder": a_ph,
                "status": "PREDICTED",
                "home_score": None,
                "away_score": None,
                "home_penalty": None,
                "away_penalty": None,
                "winner_team_id": None,
                "winner_team_name": None,
                "scheduled_date": "2026-10-28",
                "scheduled_time": "Flexible (MW Window)",
                "venue": "Minaram Stadium",
                "notes": f"Quarter-Final ({slot})"
            })

        # Semi-Finals (2 matches)
        sf_pairings = [
            ("SF1", 27, "Winner of QF1", "Winner of QF2"),
            ("SF2", 28, "Winner of QF3", "Winner of QF4"),
        ]
        for slot, m_num, h_ph, a_ph in sf_pairings:
            tree["Semi-Final"].append({
                "stage": "Semi-Final",
                "round_number": 4,
                "match_number": m_num,
                "bracket_slot": slot,
                "home_team_id": None,
                "away_team_id": None,
                "home_team_name": h_ph,
                "away_team_name": a_ph,
                "home_placeholder": h_ph,
                "away_placeholder": a_ph,
                "status": "PREDICTED",
                "home_score": None,
                "away_score": None,
                "home_penalty": None,
                "away_penalty": None,
                "winner_team_id": None,
                "winner_team_name": None,
                "scheduled_date": "2026-10-29",
                "scheduled_time": "Flexible (MW Window)",
                "venue": "Minaram Stadium",
                "notes": f"Semi-Final ({slot})"
            })

        # Grand Final (1 match)
        tree["Final"].append({
            "stage": "Final",
            "round_number": 5,
            "match_number": 29,
            "bracket_slot": "F",
            "home_team_id": None,
            "away_team_id": None,
            "home_team_name": "Winner of SF1",
            "away_team_name": "Winner of SF2",
            "home_placeholder": "Winner of SF1",
            "away_placeholder": "Winner of SF2",
            "status": "PREDICTED",
            "home_score": None,
            "away_score": None,
            "home_penalty": None,
            "away_penalty": None,
            "winner_team_id": None,
            "winner_team_name": None,
            "scheduled_date": "2026-10-31",
            "scheduled_time": "Flexible (MW Window)",
            "venue": "Minaram Grand Arena",
            "notes": "Minaram Cup Grand Final"
        })

        # Optional 3rd Place Playoff
        if third_place_enabled:
            tree["Third-Place Playoff"] = [{
                "stage": "Third-Place Playoff",
                "round_number": 5,
                "match_number": 30,
                "bracket_slot": "3RD",
                "home_team_id": None,
                "away_team_id": None,
                "home_team_name": "Runner-up of SF1",
                "away_team_name": "Runner-up of SF2",
                "home_placeholder": "Runner-up of SF1",
                "away_placeholder": "Runner-up of SF2",
                "status": "PREDICTED",
                "home_score": None,
                "away_score": None,
                "home_penalty": None,
                "away_penalty": None,
                "winner_team_id": None,
                "winner_team_name": None,
                "scheduled_date": "2026-10-30",
                "scheduled_time": "Flexible (MW Window)",
                "venue": "Minaram Stadium",
                "notes": "3rd Place Playoff"
            }]

        return tree

    # -------------------------------------------------------------------------
    # 5. STANDINGS HASH & SNAPSHOT PERSISTENCE
    # -------------------------------------------------------------------------
    def compute_standings_hash(self) -> str:
        """Compute SHA256 signature of current group matches & standings state."""
        matches = self.db.execute_query("""
            SELECT id, home_score, away_score, status, winner_team_id
            FROM matches
            WHERE stage = 'Group Stage'
            ORDER BY id ASC;
        """)
        overrides = self.db.execute_query("SELECT * FROM standings_overrides ORDER BY team_id ASC;")
        dq_overrides = self.db.execute_query("SELECT * FROM knockout_direct_overrides ORDER BY slot_index ASC;")
        rules = self.db.execute_query("SELECT * FROM knockout_rules_config ORDER BY key ASC;")

        data = {
            "m": [dict(r) for r in matches],
            "o": [dict(r) for r in overrides],
            "dq": [dict(r) for r in dq_overrides],
            "rc": [dict(r) for r in rules]
        }
        return hashlib.sha256(json.dumps(data, sort_keys=True).encode()).hexdigest()

    def get_or_create_predicted_snapshot(self, force: bool = False, draw_method: Optional[str] = None) -> Dict[str, Any]:
        """
        Retrieve existing valid snapshot or generate an updated snapshot if standings changed.
        Ensures draw does not randomize on every page load.
        """
        curr_hash = self.compute_standings_hash()
        rules = self.get_rules()
        effective_draw_method = draw_method or rules.get("draw_method", "seeded")
        third_place_enabled = (rules.get("third_place_enabled", "false").lower() == "true")

        # 1. Check existing current snapshot
        if not force:
            row = self.db.execute_one("""
                SELECT * FROM knockout_snapshots WHERE is_current = 1 ORDER BY id DESC LIMIT 1;
            """)
            if row:
                if row["standings_hash"] == curr_hash and row["draw_method"] == effective_draw_method:
                    try:
                        return {
                            "version": row["version"],
                            "created_at": row["created_at"],
                            "standings_hash": row["standings_hash"],
                            "draw_method": row["draw_method"],
                            "is_provisional": bool(row["is_provisional"]),
                            "direct_qualifiers": json.loads(row["direct_qualifiers_json"]),
                            "rounds": json.loads(row["fixtures_json"]),
                            "notes": row["notes"] or "",
                            "prediction_changed": False,
                        }
                    except Exception as e:
                        logger.error(f"Failed to parse snapshot JSON: {e}")

        # 2. Recalculate
        q_data = self.get_qualified_teams()
        dq_data = self.get_direct_qualifiers(q_data["teams"])
        prelim_fixtures = self.generate_preliminary_draw(
            qualified_teams=q_data["teams"],
            direct_qualifiers=dq_data["direct_qualifiers"],
            draw_method=effective_draw_method,
            seed_value=curr_hash
        )
        complete_tree = self.build_complete_predicted_bracket(
            direct_qualifiers=dq_data["direct_qualifiers"],
            preliminary_fixtures=prelim_fixtures,
            third_place_enabled=third_place_enabled
        )

        now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        version_id = f"snap_v{datetime.now().strftime('%Y%m%d_%H%M%S')}_{curr_hash[:8]}"

        # Archive previous current snapshots
        self.db.execute_non_query("UPDATE knockout_snapshots SET is_current = 0 WHERE is_current = 1;")

        # Save new snapshot
        dq_json = json.dumps(dq_data["direct_qualifiers"])
        tree_json = json.dumps(complete_tree)

        self.db.execute_non_query("""
            INSERT INTO knockout_snapshots (
                version, created_at, standings_hash, draw_method,
                is_provisional, is_current, direct_qualifiers_json, fixtures_json, notes
            ) VALUES (?, ?, ?, ?, ?, 1, ?, ?, ?);
        """, (
            version_id, now_str, curr_hash, effective_draw_method,
            1 if q_data["is_provisional"] else 0, dq_json, tree_json,
            "Automatically generated from latest standings"
        ))

        return {
            "version": version_id,
            "created_at": now_str,
            "standings_hash": curr_hash,
            "draw_method": effective_draw_method,
            "is_provisional": q_data["is_provisional"],
            "direct_qualifiers": dq_data["direct_qualifiers"],
            "rounds": complete_tree,
            "notes": "Automatically generated from latest standings",
            "prediction_changed": True
        }

    # -------------------------------------------------------------------------
    # 6. OFFICIAL BRACKET & MERGED TOURNAMENT DATA
    # -------------------------------------------------------------------------
    def get_knockout_tournament_data(self) -> Dict[str, Any]:
        """
        Consolidated master payload for public website & admin portal:
        - Direct qualifiers (with full stats & badges)
        - Predicted vs Official merged bracket
        - Conflict detection flags
        - Rules & configuration
        - Champion if crowned
        """
        snapshot = self.get_or_create_predicted_snapshot()
        rules = self.get_rules()
        q_data = self.get_qualified_teams()
        dq_data = self.get_direct_qualifiers(q_data["teams"])

        # Fetch all official fixtures from knockout_official_fixtures
        official_rows = self.db.execute_query("""
            SELECT f.*,
                   ht.name AS home_name, ht.logo_path AS home_logo,
                   at.name AS away_name, at.logo_path AS away_logo,
                   wt.name AS winner_name
            FROM knockout_official_fixtures f
            LEFT JOIN teams ht ON f.home_team_id = ht.id
            LEFT JOIN teams at ON f.away_team_id = at.id
            LEFT JOIN teams wt ON f.winner_team_id = wt.id
            ORDER BY f.match_number ASC;
        """)
        official_by_slot = {r["bracket_slot"]: dict(r) for r in official_rows}

        # Check for conflicts between latest standings and confirmed fixtures
        conflicts = []
        qualified_team_ids = {t["team_id"] for t in q_data["teams"]}

        for slot, off in official_by_slot.items():
            if off["status"] in ("CONFIRMED", "LIVE", "COMPLETED"):
                if off["home_team_id"] and off["home_team_id"] not in qualified_team_ids:
                    conflicts.append({
                        "bracket_slot": slot,
                        "team_id": off["home_team_id"],
                        "team_name": off["home_name"],
                        "message": f"Confirmed squad '{off['home_name']}' in slot {slot} is no longer in the top 2 qualifying positions of its group."
                    })
                if off["away_team_id"] and off["away_team_id"] not in qualified_team_ids:
                    conflicts.append({
                        "bracket_slot": slot,
                        "team_id": off["away_team_id"],
                        "team_name": off["away_name"],
                        "message": f"Confirmed squad '{off['away_name']}' in slot {slot} is no longer in the top 2 qualifying positions of its group."
                    })

        # Merge official into tree
        merged_tree: Dict[str, List[Dict[str, Any]]] = {}
        for stage_name, matches in snapshot["rounds"].items():
            merged_stage = []
            for m in matches:
                slot = m["bracket_slot"]
                if slot in official_by_slot:
                    off = official_by_slot[slot]
                    merged_stage.append({
                        "id": off["id"],
                        "stage": off["stage"],
                        "round_number": off["round_number"],
                        "match_number": off["match_number"],
                        "bracket_slot": slot,
                        "home_team_id": off["home_team_id"],
                        "away_team_id": off["away_team_id"],
                        "home_team_name": off["home_name"] or off["home_placeholder"] or "Yet to decide",
                        "away_team_name": off["away_name"] or off["away_placeholder"] or "Yet to decide",
                        "home_placeholder": off["home_placeholder"],
                        "away_placeholder": off["away_placeholder"],
                        "scheduled_date": off["scheduled_date"],
                        "scheduled_time": off["scheduled_time"],
                        "scheduled_end_date": off["scheduled_end_date"],
                        "venue": off["venue"],
                        "status": off["status"],
                        "home_score": off["home_score"],
                        "away_score": off["away_score"],
                        "home_penalty": off["home_penalty"],
                        "away_penalty": off["away_penalty"],
                        "winner_team_id": off["winner_team_id"],
                        "winner_team_name": off["winner_name"],
                        "winner_method": off["winner_method"],
                        "notes": off["notes"] or "",
                        "completed_at": off["completed_at"] or "",
                        "confirmed_at": off["confirmed_at"] or "",
                        "is_official": True
                    })
                else:
                    m_copy = dict(m)
                    m_copy["is_official"] = False
                    merged_stage.append(m_copy)
            merged_tree[stage_name] = merged_stage

        # Identify champion if Final is completed
        champion = None
        final_official = official_by_slot.get("F")
        if final_official and final_official["status"] == "COMPLETED" and final_official["winner_team_id"]:
            champ_row = self.db.execute_one("""
                SELECT t.id, t.name, t.captain_name, t.phone_number, t.logo_path, g.name AS group_name
                FROM teams t LEFT JOIN groups g ON t.group_id = g.id
                WHERE t.id = ?;
            """, (final_official["winner_team_id"],))
            if champ_row:
                champion = {
                    "id": champ_row["id"],
                    "name": champ_row["name"],
                    "manager_name": champ_row["captain_name"] or "Squad Captain",
                    "group_name": champ_row["group_name"] or "N/A"
                }

        # Format rounds array for frontend components expecting bracket.rounds
        rounds_list = []
        for stage_name, stage_matches in merged_tree.items():
            enhanced_matches = []
            for m in stage_matches:
                m_enhanced = dict(m)
                m_enhanced["team_a_id"] = m.get("home_team_id")
                m_enhanced["team_b_id"] = m.get("away_team_id")
                m_enhanced["team_a_name"] = m.get("home_team_name") or m.get("home_name")
                m_enhanced["team_b_name"] = m.get("away_team_name") or m.get("away_name")
                m_enhanced["team_a_score"] = m.get("home_score")
                m_enhanced["team_b_score"] = m.get("away_score")
                enhanced_matches.append(m_enhanced)
            rounds_list.append({
                "round_name": stage_name,
                "matches": enhanced_matches
            })

        return {
            "snapshot_version": snapshot["version"],
            "last_updated": snapshot["created_at"],
            "draw_method": snapshot["draw_method"],
            "is_provisional": snapshot["is_provisional"],
            "direct_qualifiers": dq_data["direct_qualifiers"],
            "recommended_qualifiers": dq_data["recommended_qualifiers"],
            "has_direct_override": dq_data["has_override"],
            "bracket": merged_tree,
            "rounds": rounds_list,
            "conflicts": conflicts,
            "champion": champion,
            "rules": rules,
            "statuses_legend": {
                "PREDICTED": "Automatically generated fixture or projected matchup",
                "CONFIRMED": "Fixture officially approved by tournament desk administrator",
                "LIVE": "Match currently in progress",
                "UNDER REVIEW": "Result or dispute awaiting administrator resolution",
                "COMPLETED": "Final score and winner officially recorded",
                "ELIMINATED": "Team eliminated after officially confirmed knockout result"
            }
        }

    # -------------------------------------------------------------------------
    # 7. ADMINISTRATOR FIXTURE WORKFLOWS (CONFIRM, EDIT, SCORE, ADVANCE)
    # -------------------------------------------------------------------------
    def confirm_fixture(self, bracket_slot: str, admin_username: str = "admin") -> Dict[str, Any]:
        """
        Confirm a predicted fixture into the official tournament bracket.
        Locks in teams, generates official record, and logs audit.
        """
        snapshot = self.get_or_create_predicted_snapshot()
        target_fixture = None
        for stage_matches in snapshot["rounds"].values():
            for m in stage_matches:
                if m["bracket_slot"] == bracket_slot:
                    target_fixture = m
                    break
            if target_fixture:
                break

        if not target_fixture:
            raise ValueError(f"Fixture with slot '{bracket_slot}' not found in predictions.")

        now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        existing = self.db.execute_one(
            "SELECT id, status FROM knockout_official_fixtures WHERE bracket_slot = ?;",
            (bracket_slot,)
        )

        old_val = existing["status"] if existing else "None"

        with self.db.transaction(action="fixture_confirmed") as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO knockout_official_fixtures (
                    stage, round_number, match_number, bracket_slot,
                    home_team_id, away_team_id, home_placeholder, away_placeholder,
                    scheduled_date, scheduled_time, scheduled_end_date, venue,
                    status, notes, confirmed_at, confirmed_by, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'CONFIRMED', ?, ?, ?, ?, ?)
                ON CONFLICT(bracket_slot) DO UPDATE SET
                    status = 'CONFIRMED',
                    home_team_id = excluded.home_team_id,
                    away_team_id = excluded.away_team_id,
                    confirmed_at = excluded.confirmed_at,
                    confirmed_by = excluded.confirmed_by,
                    updated_at = excluded.updated_at;
            """, (
                target_fixture["stage"], target_fixture["round_number"], target_fixture["match_number"],
                bracket_slot, target_fixture.get("home_team_id"), target_fixture.get("away_team_id"),
                target_fixture.get("home_placeholder", ""), target_fixture.get("away_placeholder", ""),
                target_fixture.get("scheduled_date", ""), target_fixture.get("scheduled_time", ""),
                target_fixture.get("scheduled_end_date", ""), target_fixture.get("venue", "Minaram Stadium"),
                target_fixture.get("notes", ""), now_str, admin_username, now_str, now_str
            ))

            # Audit log
            cursor.execute("""
                INSERT INTO knockout_audit_logs (timestamp, admin_username, action, entity_type, entity_id, old_value, new_value, reason)
                VALUES (?, ?, 'CONFIRM_FIXTURE', 'knockout_fixture', ?, ?, 'CONFIRMED', 'Admin officially confirmed fixture');
            """, (now_str, admin_username, bracket_slot, old_val))

        # Sync to matches table for general tournament compatibility
        self._sync_official_fixture_to_matches(bracket_slot)

        return {"status": "CONFIRMED", "bracket_slot": bracket_slot, "confirmed_at": now_str}

    def batch_confirm_stage(self, stage: str, admin_username: str = "admin") -> int:
        """Confirm all fixtures of a given round (e.g. 'Preliminary Round')."""
        snapshot = self.get_or_create_predicted_snapshot()
        stage_fixtures = snapshot["rounds"].get(stage, [])
        confirmed_count = 0
        for m in stage_fixtures:
            self.confirm_fixture(m["bracket_slot"], admin_username=admin_username)
            confirmed_count += 1
        return confirmed_count

    def unconfirm_fixture(self, bracket_slot: str, admin_username: str = "admin") -> Dict[str, Any]:
        """Revert a fixture back to predicted if not already in progress or completed."""
        existing = self.db.execute_one(
            "SELECT id, status FROM knockout_official_fixtures WHERE bracket_slot = ?;",
            (bracket_slot,)
        )
        if not existing:
            return {"status": "PREDICTED", "bracket_slot": bracket_slot}
        if existing["status"] in ("COMPLETED", "LIVE"):
            raise ValueError(f"Cannot unconfirm fixture in status '{existing['status']}'.")

        now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with self.db.transaction(action="fixture_unconfirmed") as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM knockout_official_fixtures WHERE bracket_slot = ?;", (bracket_slot,))
            cursor.execute("""
                INSERT INTO knockout_audit_logs (timestamp, admin_username, action, entity_type, entity_id, old_value, new_value, reason)
                VALUES (?, ?, 'UNCONFIRM_FIXTURE', 'knockout_fixture', ?, ?, 'PREDICTED', 'Admin reverted fixture to unconfirmed prediction');
            """, (now_str, admin_username, bracket_slot, existing["status"]))

        return {"status": "PREDICTED", "bracket_slot": bracket_slot}

    def edit_fixture(
        self,
        bracket_slot: str,
        home_team_id: Optional[int],
        away_team_id: Optional[int],
        scheduled_date: str = "",
        scheduled_time: str = "",
        venue: str = "",
        notes: str = "",
        admin_username: str = "admin"
    ) -> Dict[str, Any]:
        """Manually edit teams or schedule of an official knockout fixture."""
        # Validate distinct teams
        if home_team_id and away_team_id and home_team_id == away_team_id:
            raise ValueError("A knockout fixture must feature two distinct teams.")

        # Ensure fixture exists in official table
        self.confirm_fixture(bracket_slot, admin_username=admin_username)
        now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        with self.db.transaction(action="fixture_edited") as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE knockout_official_fixtures
                SET home_team_id = ?, away_team_id = ?,
                    scheduled_date = COALESCE(NULLIF(?, ''), scheduled_date),
                    scheduled_time = COALESCE(NULLIF(?, ''), scheduled_time),
                    venue = COALESCE(NULLIF(?, ''), venue),
                    notes = COALESCE(NULLIF(?, ''), notes),
                    updated_at = ?
                WHERE bracket_slot = ?;
            """, (home_team_id, away_team_id, scheduled_date, scheduled_time, venue, notes, now_str, bracket_slot))

            cursor.execute("""
                INSERT INTO knockout_audit_logs (timestamp, admin_username, action, entity_type, entity_id, old_value, new_value, reason)
                VALUES (?, ?, 'EDIT_FIXTURE', 'knockout_fixture', ?, '', ?, 'Admin manual fixture edit');
            """, (now_str, admin_username, bracket_slot, f"Home:{home_team_id}, Away:{away_team_id}, Date:{scheduled_date}"))

        self._sync_official_fixture_to_matches(bracket_slot)
        return {"bracket_slot": bracket_slot, "status": "updated"}

    def record_knockout_result(
        self,
        bracket_slot: str,
        home_score: int,
        away_score: int,
        home_penalty: Optional[int] = None,
        away_penalty: Optional[int] = None,
        winner_team_id: Optional[int] = None,
        winner_method: str = "Regular Time",
        notes: str = "",
        admin_username: str = "admin"
    ) -> Dict[str, Any]:
        """
        Record and officially confirm a knockout match score and winner:
        - Validates single-elimination invariant (exactly 1 winner).
        - Handles penalties or extra-time if scores are tied.
        - Advances winner to the designated next round slot.
        - Flags loser as eliminated.
        - Persists result and logs audit trail.
        """
        # Ensure confirmed official record exists
        self.confirm_fixture(bracket_slot, admin_username=admin_username)

        fix = self.db.execute_one(
            "SELECT * FROM knockout_official_fixtures WHERE bracket_slot = ?;",
            (bracket_slot,)
        )
        if not fix:
            raise ValueError(f"Fixture '{bracket_slot}' not found.")

        h_id = fix["home_team_id"]
        a_id = fix["away_team_id"]

        if not h_id or not a_id:
            raise ValueError("Cannot record result: both teams must be assigned before recording score.")

        # Determine winner
        calc_winner = None
        if home_score > away_score:
            calc_winner = h_id
            winner_method = winner_method or "Regular Time"
        elif away_score > home_score:
            calc_winner = a_id
            winner_method = winner_method or "Regular Time"
        else:
            # Drawn match: Must have penalty shootout or administrative decision
            if home_penalty is not None and away_penalty is not None:
                if home_penalty > away_penalty:
                    calc_winner = h_id
                    winner_method = "Penalties"
                elif away_penalty > home_penalty:
                    calc_winner = a_id
                    winner_method = "Penalties"
                else:
                    raise ValueError("Knockout match cannot end in a draw. Penalty scores cannot be tied.")
            elif winner_team_id in (h_id, a_id):
                calc_winner = winner_team_id
            else:
                raise ValueError("Knockout matches cannot end in a draw. Provide penalty shootout scores or select an extra-time winner.")

        final_winner_id = winner_team_id or calc_winner
        loser_team_id = a_id if final_winner_id == h_id else h_id
        now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        with self.db.transaction(action="knockout_result_confirmed") as conn:
            cursor = conn.cursor()
            # 1. Update official fixture
            cursor.execute("""
                UPDATE knockout_official_fixtures
                SET home_score = ?, away_score = ?, home_penalty = ?, away_penalty = ?,
                    status = 'COMPLETED', winner_team_id = ?, winner_method = ?,
                    completed_at = ?, notes = ?, updated_at = ?
                WHERE bracket_slot = ?;
            """, (
                home_score, away_score, home_penalty, away_penalty,
                final_winner_id, winner_method, now_str, notes, now_str, bracket_slot
            ))

            # 2. Advance winner into next designated round
            next_target = SLOT_PROGRESSION.get(bracket_slot)
            if next_target:
                target_slot, target_side = next_target
                col = "home_team_id" if target_side == "home" else "away_team_id"
                # Check if target match exists in official table
                cursor.execute(f"""
                    INSERT INTO knockout_official_fixtures (
                        stage, round_number, match_number, bracket_slot,
                        {col}, status, created_at, updated_at
                    ) VALUES ('Knockout', 1, 0, ?, ?, 'CONFIRMED', ?, ?)
                    ON CONFLICT(bracket_slot) DO UPDATE SET
                        {col} = excluded.{col},
                        updated_at = excluded.updated_at;
                """, (target_slot, final_winner_id, now_str, now_str))

            # 3. If 3rd place playoff is active, advance SF loser
            rules = self.get_rules()
            if rules.get("third_place_enabled", "false").lower() == "true":
                loser_target = SLOT_LOSER_PROGRESSION.get(bracket_slot)
                if loser_target:
                    l_slot, l_side = loser_target
                    l_col = "home_team_id" if l_side == "home" else "away_team_id"
                    cursor.execute(f"""
                        INSERT INTO knockout_official_fixtures (
                            stage, round_number, match_number, bracket_slot,
                            {l_col}, status, created_at, updated_at
                        ) VALUES ('Third-Place Playoff', 5, 30, ?, ?, 'CONFIRMED', ?, ?)
                        ON CONFLICT(bracket_slot) DO UPDATE SET
                            {l_col} = excluded.{l_col},
                            updated_at = excluded.updated_at;
                    """, (l_slot, loser_team_id, now_str, now_str))

            # 4. Audit Log
            cursor.execute("""
                INSERT INTO knockout_audit_logs (timestamp, admin_username, action, entity_type, entity_id, old_value, new_value, reason)
                VALUES (?, ?, 'RECORD_RESULT', 'knockout_fixture', ?, '', ?, ?);
            """, (
                now_str, admin_username, bracket_slot,
                f"Score: {home_score}-{away_score}, Pen: {home_penalty}-{away_penalty}, Winner: {final_winner_id} ({winner_method})",
                f"Result confirmed: Winner {final_winner_id} advanced"
            ))

        self._sync_official_fixture_to_matches(bracket_slot)
        if next_target:
            self._sync_official_fixture_to_matches(next_target[0])

        # Broadcast live update
        try:
            from app.events import broadcaster
            broadcaster.broadcast_from_thread("knockout_updated", {"bracket_slot": bracket_slot, "winner_id": final_winner_id})
        except Exception:
            pass

        return {
            "bracket_slot": bracket_slot,
            "status": "COMPLETED",
            "winner_team_id": final_winner_id,
            "advanced_to": next_target[0] if next_target else None
        }

    def set_fixture_status(self, bracket_slot: str, status: str, notes: str = "", admin_username: str = "admin") -> Dict[str, Any]:
        """Set fixture status to 'LIVE', 'UNDER REVIEW', 'CONFIRMED'."""
        self.confirm_fixture(bracket_slot, admin_username=admin_username)
        valid_statuses = ("PREDICTED", "CONFIRMED", "LIVE", "UNDER REVIEW", "COMPLETED")
        if status not in valid_statuses:
            raise ValueError(f"Invalid status '{status}'. Must be one of {valid_statuses}")

        now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with self.db.transaction(action="fixture_status_updated") as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE knockout_official_fixtures
                SET status = ?, notes = COALESCE(NULLIF(?, ''), notes), updated_at = ?
                WHERE bracket_slot = ?;
            """, (status, notes, now_str, bracket_slot))

            cursor.execute("""
                INSERT INTO knockout_audit_logs (timestamp, admin_username, action, entity_type, entity_id, old_value, new_value, reason)
                VALUES (?, ?, 'SET_STATUS', 'knockout_fixture', ?, '', ?, ?);
            """, (now_str, admin_username, bracket_slot, status, notes or "Admin status change"))

        self._sync_official_fixture_to_matches(bracket_slot)
        return {"bracket_slot": bracket_slot, "status": status}

    def record_walkover(
        self,
        bracket_slot: str,
        winner_team_id: int,
        reason: str,
        admin_username: str = "admin"
    ) -> Dict[str, Any]:
        """Record an official walkover with transparent policy justification and audit log."""
        if not reason or len(reason.strip()) < 5:
            raise ValueError("A clear, documented policy reason is required to award a walkover.")

        fix = self.db.execute_one("SELECT * FROM knockout_official_fixtures WHERE bracket_slot = ?;", (bracket_slot,))
        if not fix:
            self.confirm_fixture(bracket_slot, admin_username=admin_username)
            fix = self.db.execute_one("SELECT * FROM knockout_official_fixtures WHERE bracket_slot = ?;", (bracket_slot,))

        h_id = fix["home_team_id"]
        a_id = fix["away_team_id"]
        if winner_team_id not in (h_id, a_id):
            raise ValueError(f"Walkover winner must be one of the participating teams ({h_id} or {a_id}).")

        # Standard 3-0 walkover score
        h_score = 3 if winner_team_id == h_id else 0
        a_score = 0 if winner_team_id == h_id else 3

        return self.record_knockout_result(
            bracket_slot=bracket_slot,
            home_score=h_score,
            away_score=a_score,
            winner_team_id=winner_team_id,
            winner_method="Walkover",
            notes=f"Walkover awarded: {reason}",
            admin_username=admin_username
        )

    # -------------------------------------------------------------------------
    # 8. DIRECT QUALIFIER OVERRIDES & RULES
    # -------------------------------------------------------------------------
    def set_direct_qualifier_override(
        self,
        slot_index: int,
        team_id: int,
        reason: str,
        admin_username: str = "admin"
    ) -> Dict[str, Any]:
        """Manually override a direct qualifier with documented administrative ruling."""
        if slot_index not in (0, 1):
            raise ValueError("slot_index must be 0 (Direct Qualifier 1) or 1 (Direct Qualifier 2).")

        now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with self.db.transaction(action="direct_override_set") as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO knockout_direct_overrides (slot_index, team_id, reason, admin_username, updated_at)
                VALUES (?, ?, ?, ?, ?)
                ON CONFLICT(slot_index) DO UPDATE SET
                    team_id = excluded.team_id,
                    reason = excluded.reason,
                    admin_username = excluded.admin_username,
                    updated_at = excluded.updated_at;
            """, (slot_index, team_id, reason, admin_username, now_str))

            cursor.execute("""
                INSERT INTO knockout_audit_logs (timestamp, admin_username, action, entity_type, entity_id, old_value, new_value, reason)
                VALUES (?, ?, 'OVERRIDE_DIRECT_QUALIFIER', 'direct_qualifiers', ?, '', ?, ?);
            """, (now_str, admin_username, f"Slot_{slot_index}", f"Team_{team_id}", reason))

        # Recalculate predictions with override
        self.get_or_create_predicted_snapshot(force=True)
        return {"slot_index": slot_index, "team_id": team_id, "status": "overridden"}

    def clear_direct_qualifier_overrides(self, admin_username: str = "admin") -> Dict[str, Any]:
        """Clear direct qualifier overrides and restore calculated recommendations."""
        now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with self.db.transaction(action="direct_override_cleared") as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM knockout_direct_overrides;")
            cursor.execute("""
                INSERT INTO knockout_audit_logs (timestamp, admin_username, action, entity_type, entity_id, old_value, new_value, reason)
                VALUES (?, ?, 'CLEAR_DIRECT_OVERRIDE', 'direct_qualifiers', 'ALL', '', 'RESTORE_CALCULATED', 'Admin cleared manual direct qualifier overrides');
            """, (now_str, admin_username))

        self.get_or_create_predicted_snapshot(force=True)
        return {"status": "cleared"}

    def reset_unconfirmed_predictions(self, admin_username: str = "admin") -> Dict[str, Any]:
        """Reset unconfirmed prediction snapshots without touching confirmed or completed fixtures."""
        now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with self.db.transaction(action="predictions_reset") as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM knockout_snapshots;")
            cursor.execute("""
                INSERT INTO knockout_audit_logs (timestamp, admin_username, action, entity_type, entity_id, old_value, new_value, reason)
                VALUES (?, ?, 'RESET_PREDICTIONS', 'knockout_predictions', 'ALL', '', 'RESET', 'Admin triggered prediction reset');
            """, (now_str, admin_username))

        new_snap = self.get_or_create_predicted_snapshot(force=True)
        return {"status": "reset", "version": new_snap["version"]}

    # -------------------------------------------------------------------------
    # 9. RULES & CONFIGURATION
    # -------------------------------------------------------------------------
    def get_rules(self) -> Dict[str, str]:
        """Retrieve knockout tournament rules configuration."""
        defaults = {
            "match_format": "Single-Elimination Knockout",
            "match_duration_minutes": "90",
            "game_mode": "eFootball Authentic / Dream Team Standard",
            "extra_time_enabled": "true",
            "penalties_enabled": "true",
            "third_place_enabled": "false",
            "draw_method": "seeded",
            "walkover_policy": "Strict 3-0 walkover only upon desk authorization after official grace period deadline.",
            "dispute_policy": "Match set to 'Under Review'; result held until match official resolves technical issue or disconnection.",
            "rules_updated_at": "2026-10-18 00:00:00"
        }
        rows = self.db.execute_query("SELECT key, value FROM knockout_rules_config;")
        db_rules = {r["key"]: r["value"] for r in rows}
        return {**defaults, **db_rules}

    def update_rule(self, key: str, value: str, admin_username: str = "admin") -> Dict[str, str]:
        """Update a specific tournament rule or game setting."""
        now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with self.db.transaction(action="rule_updated") as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO knockout_rules_config (key, value, updated_at, updated_by)
                VALUES (?, ?, ?, ?)
                ON CONFLICT(key) DO UPDATE SET
                    value = excluded.value,
                    updated_at = excluded.updated_at,
                    updated_by = excluded.updated_by;
            """, (key, value, now_str, admin_username))

            cursor.execute("""
                INSERT INTO knockout_rules_config (key, value, updated_at, updated_by)
                VALUES ('rules_updated_at', ?, ?, ?)
                ON CONFLICT(key) DO UPDATE SET value = excluded.value, updated_at = excluded.updated_at;
            """, (now_str, now_str, admin_username))

            cursor.execute("""
                INSERT INTO knockout_audit_logs (timestamp, admin_username, action, entity_type, entity_id, old_value, new_value, reason)
                VALUES (?, ?, 'UPDATE_RULE', 'knockout_rule', ?, '', ?, 'Admin updated rule');
            """, (now_str, admin_username, key, value))

        return self.get_rules()

    def toggle_third_place(self, enabled: bool, admin_username: str = "admin") -> Dict[str, Any]:
        """Enable or disable the optional 3rd place playoff match."""
        val = "true" if enabled else "false"
        self.update_rule("third_place_enabled", val, admin_username=admin_username)
        self.get_or_create_predicted_snapshot(force=True)
        return {"third_place_enabled": enabled}

    def get_audit_logs(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Retrieve chronological administrative audit logs."""
        rows = self.db.execute_query("""
            SELECT * FROM knockout_audit_logs ORDER BY id DESC LIMIT ?;
        """, (limit,))
        return [dict(r) for r in rows]

    # -------------------------------------------------------------------------
    # 10. BACKWARDS COMPATIBILITY FOR LEGACY APIS & TESTS
    # -------------------------------------------------------------------------
    def advance_winner_in_bracket(self, completed_match_id: int, winner_team_id: int) -> Optional[int]:
        """Legacy helper: advances winner in matches table."""
        m = self.db.execute_one("SELECT bracket_slot FROM matches WHERE id = ?;", (completed_match_id,))
        if not m or not m["bracket_slot"]:
            return None

        slot = m["bracket_slot"]
        target = SLOT_PROGRESSION.get(slot)
        if not target:
            return None

        target_slot, target_side = target
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
        """Legacy helper: returns matches grouped by stage."""
        stages_order = ["Preliminary Round", "Round of 16", "Quarter-Final", "Semi-Final", "Final", "Third-Place Playoff"]
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
                    for r in matches_in_stage
                ]
        return result

    def generate_bracket_from_group_qualifiers(
        self,
        start_date: str = "",
        start_time: str = "15:00",
        match_duration_mins: int = 90,
        venue: str = "Minaram Stadium"
    ) -> List[Dict[str, Any]]:
        """Preserves legacy fixture generation behavior if called from admin router."""
        group_standings = self.standings.calculate_all_groups_standings()
        group_names = sorted(list(group_standings.keys()))
        if len(group_names) == 15:
            # Full 15 groups: return complete knockout fixtures list
            q_data = self.get_qualified_teams()
            dq_data = self.get_direct_qualifiers(q_data["teams"])
            prelim = self.generate_preliminary_draw(q_data["teams"], dq_data["direct_qualifiers"])
            tree = self.build_complete_predicted_bracket(dq_data["direct_qualifiers"], prelim)
            all_fixtures = []
            for stage_matches in tree.values():
                all_fixtures.extend(stage_matches)
            return all_fixtures

        # Legacy 2-group or 4-group fallback
        if len(group_names) == 2:
            return self._legacy_2group_bracket(group_standings, group_names, start_date, start_time, match_duration_mins, venue)
        elif len(group_names) >= 4:
            return self._legacy_4group_bracket(group_standings, group_names, start_date, start_time, match_duration_mins, venue)
        return []

    def _legacy_2group_bracket(self, group_standings, group_names, start_date, start_time, match_duration_mins, venue):
        max_num = self.db.execute_one("SELECT MAX(match_number) AS m FROM matches;")["m"] or 0
        match_num = max_num + 1
        curr_dt = datetime.now() + timedelta(days=2)
        time_val = "Flexible (MW Window)"
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

        fixtures = [
            {"match_number": match_num, "stage": "Semi-Final", "round_number": 1, "bracket_slot": "SF1",
             "home_team_id": a1, "away_team_id": b2, "home_team_name": a1_name, "away_team_name": b2_name,
             "scheduled_date": curr_dt.strftime("%Y-%m-%d"), "scheduled_time": time_val, "venue": venue, "status": "Scheduled", "notes": "Semi-Final 1"},
            {"match_number": match_num + 1, "stage": "Semi-Final", "round_number": 1, "bracket_slot": "SF2",
             "home_team_id": b1, "away_team_id": a2, "home_team_name": b1_name, "away_team_name": a2_name,
             "scheduled_date": curr_dt.strftime("%Y-%m-%d"), "scheduled_time": time_val, "venue": venue, "status": "Scheduled", "notes": "Semi-Final 2"},
            {"match_number": match_num + 2, "stage": "Final", "round_number": 2, "bracket_slot": "F",
             "home_team_id": None, "away_team_id": None, "home_team_name": "Winner SF1", "away_team_name": "Winner SF2",
             "scheduled_date": curr_dt.strftime("%Y-%m-%d"), "scheduled_time": time_val, "venue": venue, "status": "Scheduled", "notes": "Minaram Cup Final"}
        ]
        return fixtures

    def _legacy_4group_bracket(self, group_standings, group_names, start_date, start_time, match_duration_mins, venue):
        max_num = self.db.execute_one("SELECT MAX(match_number) AS m FROM matches;")["m"] or 0
        match_num = max_num + 1
        curr_dt = datetime.now() + timedelta(days=2)
        time_val = "Flexible (MW Window)"
        g = [group_standings.get(gn, []) for gn in group_names[:4]]
        qf_pairings = [
            ("QF1", g[0], 0, g[1], 1, f"1st {group_names[0]}", f"2nd {group_names[1]}"),
            ("QF2", g[2], 0, g[3], 1, f"1st {group_names[2]}", f"2nd {group_names[3]}"),
            ("QF3", g[1], 0, g[0], 1, f"1st {group_names[1]}", f"2nd {group_names[0]}"),
            ("QF4", g[3], 0, g[2], 1, f"1st {group_names[3]}", f"2nd {group_names[2]}"),
        ]
        fixtures = []
        for slot, g_home, h_idx, g_away, a_idx, def_h_name, def_a_name in qf_pairings:
            h_id = g_home[h_idx].team_id if len(g_home) > h_idx else None
            h_name = g_home[h_idx].team_name if len(g_home) > h_idx else def_h_name
            a_id = g_away[a_idx].team_id if len(g_away) > a_idx else None
            a_name = g_away[a_idx].team_name if len(g_away) > a_idx else def_a_name
            fixtures.append({
                "match_number": match_num, "stage": "Quarter-Final", "round_number": 1, "bracket_slot": slot,
                "home_team_id": h_id, "away_team_id": a_id, "home_team_name": h_name, "away_team_name": a_name,
                "scheduled_date": curr_dt.strftime("%Y-%m-%d"), "scheduled_time": time_val, "venue": venue,
                "status": "Scheduled", "notes": f"Quarter-Final ({slot})"
            })
            match_num += 1

        fixtures.extend([
            {"match_number": match_num, "stage": "Semi-Final", "round_number": 2, "bracket_slot": "SF1",
             "home_team_id": None, "away_team_id": None, "home_team_name": "Winner QF1", "away_team_name": "Winner QF2",
             "scheduled_date": curr_dt.strftime("%Y-%m-%d"), "scheduled_time": time_val, "venue": venue, "status": "Scheduled", "notes": "Semi-Final 1"},
            {"match_number": match_num + 1, "stage": "Semi-Final", "round_number": 2, "bracket_slot": "SF2",
             "home_team_id": None, "away_team_id": None, "home_team_name": "Winner QF3", "away_team_name": "Winner QF4",
             "scheduled_date": curr_dt.strftime("%Y-%m-%d"), "scheduled_time": time_val, "venue": venue, "status": "Scheduled", "notes": "Semi-Final 2"},
            {"match_number": match_num + 2, "stage": "Final", "round_number": 3, "bracket_slot": "F",
             "home_team_id": None, "away_team_id": None, "home_team_name": "Winner SF1", "away_team_name": "Winner SF2",
             "scheduled_date": curr_dt.strftime("%Y-%m-%d"), "scheduled_time": time_val, "venue": venue, "status": "Scheduled", "notes": "Minaram Cup Grand Final"}
        ])
        return fixtures

    def _sync_official_fixture_to_matches(self, bracket_slot: str):
        """Internal helper: safely mirror official knockout fixture into the general matches table."""
        try:
            off = self.db.execute_one("SELECT * FROM knockout_official_fixtures WHERE bracket_slot = ?;", (bracket_slot,))
            if not off:
                return

            h_id = off["home_team_id"]
            a_id = off["away_team_id"]
            # Ensure foreign key constraints in matches table (teams(id)) are strictly satisfied
            if h_id and not self.db.execute_one("SELECT id FROM teams WHERE id = ?;", (h_id,)):
                h_id = None
            if a_id and not self.db.execute_one("SELECT id FROM teams WHERE id = ?;", (a_id,)):
                a_id = None

            m_status = "Completed" if off["status"] == "COMPLETED" else "Scheduled"
            if off["status"] == "LIVE":
                m_status = "In Progress"

            existing = self.db.execute_one("SELECT id FROM matches WHERE bracket_slot = ?;", (bracket_slot,))
            if existing:
                self.db.execute_non_query("""
                    UPDATE matches
                    SET home_team_id = ?, away_team_id = ?,
                        home_score = ?, away_score = ?, home_penalty = ?, away_penalty = ?,
                        status = ?, winner_team_id = ?, completed_at = ?, notes = ?
                    WHERE id = ?;
                """, (
                    h_id, a_id,
                    off["home_score"], off["away_score"], off["home_penalty"], off["away_penalty"],
                    m_status, off["winner_team_id"], off["completed_at"], off["notes"] or "", existing["id"]
                ))
            else:
                max_num = self.db.execute_one("SELECT MAX(match_number) AS m FROM matches;")["m"] or 0
                self.db.execute_non_query("""
                    INSERT INTO matches (
                        match_number, stage, round_number, bracket_slot,
                        home_team_id, away_team_id, scheduled_date, scheduled_time, venue,
                        home_score, away_score, home_penalty, away_penalty,
                        status, winner_team_id, completed_at, notes
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
                """, (
                    max_num + 1, off["stage"], off["round_number"], bracket_slot,
                    h_id, a_id, off["scheduled_date"], off["scheduled_time"], off["venue"],
                    off["home_score"], off["away_score"], off["home_penalty"], off["away_penalty"],
                    m_status, off["winner_team_id"], off["completed_at"], off["notes"] or ""
                ))
        except Exception as e:
            import logging
            logging.getLogger(__name__).warning(f"Error syncing official fixture {bracket_slot} to matches: {e}")

    def apply_custom_draw(self, pairings: list, admin_username: str = "admin") -> dict:
        """Apply administrator's drawn pairings into official knockout fixtures."""
        now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        applied_count = 0
        for p in pairings:
            m_num = p.get("match_number") or p.get("matchNumber") or (applied_count + 1)
            slot = p.get("slot") or f"PR{m_num}"
            home_id = p.get("homeTeam", {}).get("id") if isinstance(p.get("homeTeam"), dict) else p.get("home_team_id")
            away_id = p.get("awayTeam", {}).get("id") if isinstance(p.get("awayTeam"), dict) else p.get("away_team_id")
            home_name = p.get("homeTeam", {}).get("name") if isinstance(p.get("homeTeam"), dict) else p.get("home_team_name")
            away_name = p.get("awayTeam", {}).get("name") if isinstance(p.get("awayTeam"), dict) else p.get("away_team_name")

            # Validate that home_id and away_id exist in teams table, or resolve by name
            if home_id and not self.db.execute_one("SELECT id FROM teams WHERE id = ?;", (home_id,)):
                found_h = self.db.execute_one("SELECT id FROM teams WHERE name = ? OR name LIKE ?;", (home_name, f"%{home_name}%")) if home_name else None
                home_id = found_h["id"] if found_h else None

            if away_id and not self.db.execute_one("SELECT id FROM teams WHERE id = ?;", (away_id,)):
                found_a = self.db.execute_one("SELECT id FROM teams WHERE name = ? OR name LIKE ?;", (away_name, f"%{away_name}%")) if away_name else None
                away_id = found_a["id"] if found_a else None

            if not home_id or not away_id:
                # If neither ID nor name matched real teams, safely look up available teams
                continue

            existing = self.db.execute_one("SELECT bracket_slot FROM knockout_official_fixtures WHERE bracket_slot = ?;", (slot,))
            if existing:
                self.db.execute_non_query("""
                    UPDATE knockout_official_fixtures
                    SET home_team_id = ?, away_team_id = ?, status = 'CONFIRMED', notes = ?, updated_at = ?
                    WHERE bracket_slot = ?;
                """, (home_id, away_id, f"Drawn via Official Ceremonial Draw on {now_str}", now_str, slot))
            else:
                try:
                    num_val = int(str(slot).replace("PR", "")) if "PR" in str(slot) else int(m_num)
                except (ValueError, TypeError):
                    num_val = applied_count + 1
                self.db.execute_non_query("""
                    INSERT INTO knockout_official_fixtures (
                        bracket_slot, stage, match_number, round_number,
                        home_team_id, away_team_id, scheduled_date, scheduled_time, venue,
                        status, notes, created_at, updated_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
                """, (
                    slot, "Preliminary Round", num_val, 0,
                    home_id, away_id, "2026-10-22", "Flexible (MW Window)", "Online / Mobile Lobby",
                    "CONFIRMED", f"Drawn via Official Ceremonial Draw on {now_str}",
                    now_str, now_str
                ))
            self._sync_official_fixture_to_matches(slot)
            applied_count += 1

        self.db.execute_non_query("""
            INSERT INTO knockout_audit_logs (timestamp, admin_username, action, entity_type, entity_id, old_value, new_value, reason)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?);
        """, (now_str, admin_username, "APPLY_CEREMONIAL_DRAW", "PRELIMINARY_STAGE", "PR1-PR14", "", f"{applied_count} ties confirmed", "Applied UEFA Ceremonial Draw to Official Fixtures"))

        return {
            "status": "applied",
            "count": applied_count,
            "message": f"Successfully committed {applied_count} preliminary ties into official knockout fixtures!"
        }

    def export_draw_to_desktop(self, admin_username: str = "admin") -> dict:
        """Format the complete knockout draw and save directly to Desktop."""
        bracket = self.get_or_create_predicted_snapshot()
        direct = bracket.get("direct_qualifiers", [])
        rounds = bracket.get("rounds", [])

        now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        lines = []
        lines.append("=" * 80)
        lines.append("MINARAM CUP 2026 — OFFICIAL KNOCKOUT TOURNAMENT DRAW & SEEDING REPORT")
        lines.append("=" * 80)
        lines.append(f"Generated: {now_str}")
        lines.append(f"Tournament Desk Administrator: {admin_username}")
        lines.append(f"Snapshot Version: {bracket.get('snapshot_version', 'v1')}")
        lines.append(f"Status: {'PROVISIONAL (GROUP STAGE IN PROGRESS)' if bracket.get('is_provisional') else 'OFFICIAL & FINALIZED'}")
        lines.append("")
        lines.append("-" * 80)
        lines.append("1. DIRECT ROUND OF 16 QUALIFIERS (Awarded Byes — Exempt from Preliminary Round)")
        lines.append("-" * 80)
        for i, dq in enumerate(direct, 1):
            slot = "R16_1 (Top Half)" if i == 1 else "R16_5 (Bottom Half)"
            lines.append(f"Seed #{i}: {dq.get('team_name')} ({dq.get('group_name')}) — GF: {dq.get('goals_for')}, GD: {dq.get('goal_difference')}, PTS: {dq.get('points')}")
            lines.append(f"         Assigned Bracket Slot: {slot}")
        lines.append("")
        lines.append("-" * 80)
        lines.append("2. PRELIMINARY KNOCKOUT ROUND (14 Single-Leg Elimination Ties)")
        lines.append("-" * 80)
        lines.append(f"{'Slot':<8} | {'Home Squad':<28} | {'Away Squad':<28} | {'Status':<12}")
        lines.append("-" * 80)

        prelim_matches = []
        r16_matches = []
        if isinstance(rounds, dict):
            prelim_matches = rounds.get("Preliminary Round", [])
            r16_matches = rounds.get("Round of 16", [])
        elif isinstance(rounds, list):
            for r in rounds:
                if isinstance(r, dict):
                    r_name = (r.get("round_name") or "").lower()
                    if "preliminary" in r_name:
                        prelim_matches = r.get("matches", [])
                    elif "16" in r_name:
                        r16_matches = r.get("matches", [])

        for m in prelim_matches:
            slot = m.get("bracket_slot") or f"PR{m.get('match_number')}"
            home = m.get("home_team_name") or f"Team #{m.get('home_team_id')}"
            away = m.get("away_team_name") or f"Team #{m.get('away_team_id')}"
            status = m.get("status") or "PREDICTED"
            lines.append(f"{slot:<8} | {home:<28} | {away:<28} | {status:<12}")

        lines.append("")
        lines.append("-" * 80)
        lines.append("3. ROUND OF 16 BRACKET SLOTS")
        lines.append("-" * 80)
        for m in r16_matches:
            slot = m.get("bracket_slot") or f"R16_{m.get('match_number')}"
            home = m.get("home_team_name") or "TBD"
            away = m.get("away_team_name") or "TBD"
            lines.append(f"{slot:<8}: {home} vs {away}")

        lines.append("=" * 80)
        lines.append("Minaram Cup 2026 · TKM College of Engineering eFootball Championship")
        lines.append("=" * 80)
        content = "\n".join(lines)

        import pathlib
        desktop_candidates = [
            pathlib.Path.home() / "OneDrive" / "Desktop",
            pathlib.Path.home() / "Desktop",
            pathlib.Path("C:/Users/vaish/OneDrive/Desktop"),
        ]
        target_dir = next((p for p in desktop_candidates if p.exists()), pathlib.Path.cwd())
        target_file = target_dir / "MINARAM_CUP_2026_OFFICIAL_KNOCKOUT_DRAW.txt"
        target_file.write_text(content, encoding="utf-8")

        csv_file = target_dir / "MINARAM_CUP_2026_KNOCKOUT_PAIRINGS.csv"
        csv_lines = ["Slot,Match Number,Stage,Home Team,Away Team,Status"]
        for m in prelim_matches:
            csv_lines.append(f"{m.get('bracket_slot')},{m.get('match_number')},{m.get('stage')},{m.get('home_team_name')},{m.get('away_team_name')},{m.get('status')}")
        csv_file.write_text("\n".join(csv_lines), encoding="utf-8")

        self.db.execute_non_query("""
            INSERT INTO knockout_audit_logs (timestamp, admin_username, action, entity_type, entity_id, old_value, new_value, reason)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?);
        """, (now_str, admin_username, "SYNC_DESKTOP", "DRAW_REPORT", str(target_file), "", now_str, "Exported official draw to Desktop"))

        return {
            "status": "success",
            "file_path": str(target_file),
            "csv_path": str(csv_file),
            "filename": "MINARAM_CUP_2026_OFFICIAL_KNOCKOUT_DRAW.txt",
            "content": content
        }

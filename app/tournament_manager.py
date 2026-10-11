"""
Tournament configuration and Group administration service.
Handles group creation, seeding, automatic and randomized team distribution,
and tournament settings.
"""

import random
import math
import string
import logging
from typing import List, Dict, Any, Optional, Tuple

from app.database import Database
from app.models import Group, Team, TournamentSettings

logger = logging.getLogger("minaram_cup.tournament_manager")


class TournamentManager:
    def __init__(self, db: Database):
        self.db = db

    # ----------------------------------------------------
    # Settings Management
    # ----------------------------------------------------
    def get_settings(self) -> TournamentSettings:
        s = self.db.get_all_settings()
        return TournamentSettings(
            tournament_name=s.get("tournament_name", "Minaram Cup"),
            edition=s.get("edition", "2026 Edition"),
            sport=s.get("sport", "Football"),
            format_type=s.get("format_type", "Group Stage + Knockout"),
            win_points=int(s.get("win_points", "3")),
            draw_points=int(s.get("draw_points", "1")),
            loss_points=int(s.get("loss_points", "0")),
            num_groups=int(s.get("num_groups", "2")),
            qualifiers_per_group=int(s.get("qualifiers_per_group", "2")),
            match_duration_minutes=int(s.get("match_duration_minutes", "90")),
            default_venue=s.get("default_venue", "Minaram Stadium"),
            tie_breakers=s.get("tie_breakers", "points,goal_difference,goals_for,head_to_head,won"),
            theme=s.get("theme", "dark"),
        )

    def update_settings(self, settings: TournamentSettings) -> None:
        with self.db.transaction() as conn:
            cursor = conn.cursor()
            cursor.execute("INSERT OR REPLACE INTO settings (key, value) VALUES ('tournament_name', ?);", (settings.tournament_name,))
            cursor.execute("INSERT OR REPLACE INTO settings (key, value) VALUES ('edition', ?);", (settings.edition,))
            cursor.execute("INSERT OR REPLACE INTO settings (key, value) VALUES ('sport', ?);", (settings.sport,))
            cursor.execute("INSERT OR REPLACE INTO settings (key, value) VALUES ('format_type', ?);", (settings.format_type,))
            cursor.execute("INSERT OR REPLACE INTO settings (key, value) VALUES ('win_points', ?);", (str(settings.win_points),))
            cursor.execute("INSERT OR REPLACE INTO settings (key, value) VALUES ('draw_points', ?);", (str(settings.draw_points),))
            cursor.execute("INSERT OR REPLACE INTO settings (key, value) VALUES ('loss_points', ?);", (str(settings.loss_points),))
            cursor.execute("INSERT OR REPLACE INTO settings (key, value) VALUES ('num_groups', ?);", (str(settings.num_groups),))
            cursor.execute("INSERT OR REPLACE INTO settings (key, value) VALUES ('qualifiers_per_group', ?);", (str(settings.qualifiers_per_group),))
            cursor.execute("INSERT OR REPLACE INTO settings (key, value) VALUES ('match_duration_minutes', ?);", (str(settings.match_duration_minutes),))
            cursor.execute("INSERT OR REPLACE INTO settings (key, value) VALUES ('default_venue', ?);", (settings.default_venue,))
            cursor.execute("INSERT OR REPLACE INTO settings (key, value) VALUES ('tie_breakers', ?);", (settings.tie_breakers,))
            cursor.execute("INSERT OR REPLACE INTO settings (key, value) VALUES ('theme', ?);", (settings.theme,))

    # ----------------------------------------------------
    # Group Management
    # ----------------------------------------------------
    def get_groups(self) -> List[Group]:
        query = """
            SELECT g.id, g.name, g.display_order, COUNT(t.id) AS teams_count
            FROM groups g
            LEFT JOIN teams t ON g.id = t.group_id
            GROUP BY g.id
            ORDER BY g.display_order ASC, g.name ASC;
        """
        rows = self.db.execute_query(query)
        return [
            Group(
                id=r["id"],
                name=r["name"],
                display_order=r["display_order"],
                teams_count=r["teams_count"]
            )
            for r in rows
        ]

    def create_group(self, name: str) -> int:
        name = name.strip()
        if not name:
            raise ValueError("Group name cannot be empty.")
        existing = self.db.execute_one("SELECT id FROM groups WHERE LOWER(name) = LOWER(?);", (name,))
        if existing:
            raise ValueError(f"Group '{name}' already exists.")
        
        # Display order defaults to next available
        max_order = self.db.execute_one("SELECT MAX(display_order) as m FROM groups;")["m"] or 0
        return self.db.execute_non_query(
            "INSERT INTO groups (name, display_order) VALUES (?, ?);",
            (name, max_order + 1)
        )

    def rename_group(self, group_id: int, new_name: str) -> None:
        new_name = new_name.strip()
        if not new_name:
            raise ValueError("Group name cannot be empty.")
        existing = self.db.execute_one("SELECT id FROM groups WHERE LOWER(name) = LOWER(?) AND id != ?;", (new_name, group_id))
        if existing:
            raise ValueError(f"Group '{new_name}' already exists.")
        self.db.execute_non_query("UPDATE groups SET name = ? WHERE id = ?;", (new_name, group_id))

    def delete_group(self, group_id: int) -> Tuple[bool, str]:
        """Delete group, unassigning teams first."""
        # Check if matches exist for this group
        matches_cnt = self.db.execute_one("SELECT COUNT(*) AS c FROM matches WHERE group_id = ?;", (group_id,))["c"]
        if matches_cnt > 0:
            return False, f"Cannot delete group: {matches_cnt} matches are scheduled for this group. Remove fixtures first."

        with self.db.transaction() as conn:
            cursor = conn.cursor()
            cursor.execute("UPDATE teams SET group_id = NULL WHERE group_id = ?;", (group_id,))
            cursor.execute("DELETE FROM groups WHERE id = ?;", (group_id,))
        return True, "Group deleted successfully."

    def assign_team_to_group(self, team_id: int, group_id: Optional[int]) -> None:
        self.db.execute_non_query("UPDATE teams SET group_id = ? WHERE id = ?;", (group_id, team_id))

    def check_existing_fixtures_or_results(self) -> Tuple[bool, int, int]:
        """Returns (has_conflicts, fixture_count, result_count)."""
        f_count = self.db.execute_one("SELECT COUNT(*) AS c FROM matches;")["c"]
        r_count = self.db.execute_one("SELECT COUNT(*) AS c FROM matches WHERE status IN ('Completed', 'Walkover');")["c"]
        return (f_count > 0, f_count, r_count)

    def get_group_teams(self, group_id: int) -> List[Team]:
        rows = self.db.execute_query("""
            SELECT id, name, captain_name, phone_number, status, group_id, seed, logo_path, notes, created_at
            FROM teams
            WHERE group_id = ?
            ORDER BY seed DESC, name ASC;
        """, (group_id,))
        return [
            Team(
                id=r["id"],
                name=r["name"],
                captain_name=r["captain_name"] or "",
                phone_number=r["phone_number"] or "",
                status=r["status"],
                group_id=r["group_id"],
                seed=r["seed"] or 0,
                logo_path=r["logo_path"] or "",
                notes=r["notes"] or "",
                created_at=r["created_at"]
            )
            for r in rows
        ]

    def get_unassigned_teams(self) -> List[Team]:
        rows = self.db.execute_query("""
            SELECT id, name, captain_name, phone_number, status, group_id, seed, logo_path, notes, created_at
            FROM teams
            WHERE group_id IS NULL AND status = 'Confirmed'
            ORDER BY seed DESC, name ASC;
        """)
        return [
            Team(
                id=r["id"],
                name=r["name"],
                captain_name=r["captain_name"] or "",
                phone_number=r["phone_number"] or "",
                status=r["status"],
                group_id=r["group_id"],
                seed=r["seed"] or 0,
                logo_path=r["logo_path"] or "",
                notes=r["notes"] or "",
                created_at=r["created_at"]
            )
            for r in rows
        ]

    def preview_team_distribution(
        self,
        randomize: bool = False,
        seed_aware: bool = True,
        max_teams_per_group: int = 4,
        auto_create_groups: bool = True
    ) -> Dict[str, List[Dict[str, Any]]]:
        """
        Generate a proposed group allocation for all confirmed teams.
        If auto_create_groups=True or no groups exist in the database,
        automatically derives groups ('Group A', 'Group B', ...) with at most
        max_teams_per_group (default: 4) teams per group.
        Returns a dict mapping group_name -> list of team dicts.
        """
        # Fetch all confirmed teams
        teams_rows = self.db.execute_query("""
            SELECT id, name, seed FROM teams WHERE status = 'Confirmed' ORDER BY seed DESC, name ASC;
        """)
        teams = [{"id": r["id"], "name": r["name"], "seed": r["seed"] or 0} for r in teams_rows]
        if not teams:
            raise ValueError("No confirmed teams to distribute. Please confirm team registrations first.")

        num_teams = len(teams)
        existing_groups = self.get_groups()

        # If auto_create_groups is True, or if no groups exist yet:
        if auto_create_groups or not existing_groups:
            limit = max(2, max_teams_per_group)
            num_g = max(1, math.ceil(num_teams / limit))
            group_names = [
                f"Group {string.ascii_uppercase[i]}" if i < 26 else f"Group {i+1}"
                for i in range(num_g)
            ]
        else:
            group_names = [g.name for g in existing_groups]
            num_g = len(group_names)

        # Initialize group buckets
        allocations = {gn: [] for gn in group_names}

        # Calculate exact target capacities so all groups have <= max_teams_per_group
        base_size = num_teams // num_g
        remainder = num_teams % num_g
        capacities = {gn: base_size + (1 if idx < remainder else 0) for idx, gn in enumerate(group_names)}

        if seed_aware:
            # Separate seeded (seed > 0) and unseeded
            seeded = [t for t in teams if t["seed"] > 0]
            unseeded = [t for t in teams if t["seed"] == 0]

            if randomize:
                random.shuffle(seeded)
                random.shuffle(unseeded)

            # Distribute seeded teams across groups first (round robin)
            for idx, t in enumerate(seeded):
                g_target = group_names[idx % num_g]
                allocations[g_target].append(t)

            # Distribute unseeded teams into groups respecting their capacity
            for t in unseeded:
                available_groups = [gn for gn in group_names if len(allocations[gn]) < capacities[gn]]
                if not available_groups:
                    available_groups = group_names

                min_len = min(len(allocations[gn]) for gn in available_groups)
                tie_groups = [gn for gn in available_groups if len(allocations[gn]) == min_len]
                target_g = random.choice(tie_groups) if randomize else tie_groups[0]
                allocations[target_g].append(t)
        else:
            team_pool = list(teams)
            if randomize:
                random.shuffle(team_pool)

            for t in team_pool:
                available_groups = [gn for gn in group_names if len(allocations[gn]) < capacities[gn]]
                if not available_groups:
                    available_groups = group_names

                min_len = min(len(allocations[gn]) for gn in available_groups)
                tie_groups = [gn for gn in available_groups if len(allocations[gn]) == min_len]
                target_g = random.choice(tie_groups) if randomize else tie_groups[0]
                allocations[target_g].append(t)

        return allocations

    def apply_group_allocation(self, allocation: Dict[str, List[Dict[str, Any]]], clean_empty_groups: bool = False) -> None:
        """
        Apply confirmed group allocation to the database.
        Automatically creates groups if they do not exist.
        """
        with self.db.transaction() as conn:
            cursor = conn.cursor()

            # Map existing groups
            cursor.execute("SELECT id, name FROM groups;")
            groups = {r["name"]: r["id"] for r in cursor.fetchall()}

            cursor.execute("SELECT COALESCE(MAX(display_order), 0) AS m FROM groups;")
            max_order_row = cursor.fetchone()
            max_order = max_order_row["m"] if max_order_row else 0

            # Ensure all groups in allocation exist
            for group_name in allocation.keys():
                if group_name not in groups:
                    max_order += 1
                    cursor.execute(
                        "INSERT INTO groups (name, display_order) VALUES (?, ?);",
                        (group_name, max_order)
                    )
                    groups[group_name] = cursor.lastrowid

            # Assign teams to their designated group
            for group_name, team_list in allocation.items():
                group_id = groups[group_name]
                for t in team_list:
                    cursor.execute("UPDATE teams SET group_id = ? WHERE id = ?;", (group_id, t["id"]))

            if clean_empty_groups:
                cursor.execute("""
                    DELETE FROM groups
                    WHERE id NOT IN (SELECT DISTINCT group_id FROM teams WHERE group_id IS NOT NULL);
                """)

"""
Fixture scheduling, round-robin generation, knockout bracket creation,
and scheduling conflict detection.
"""

import logging
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, timedelta

from app.database import Database
from app.models import Match

logger = logging.getLogger("minaram_cup.fixture_generator")


class FixtureGenerator:
    def __init__(self, db: Database):
        self.db = db

    # ----------------------------------------------------
    # Round-Robin Algorithm (Berger / Circle Method)
    # ----------------------------------------------------
    @staticmethod
    def generate_round_robin_pairings(teams: List[Dict[str, Any]], double_round: bool = False) -> List[List[Tuple[Dict[str, Any], Dict[str, Any]]]]:
        """
        Generate round-robin rounds using the Circle Method.
        Handles odd numbers of teams by inserting a BYE dummy team.
        Returns a list of rounds, where each round is a list of (home_team, away_team) tuples.
        """
        team_list = list(teams)
        if len(team_list) < 2:
            return []

        # If odd, add dummy BYE team
        has_bye = (len(team_list) % 2 != 0)
        if has_bye:
            team_list.append({"id": None, "name": "BYE"})

        n = len(team_list)
        rounds_count = n - 1
        half = n // 2

        all_rounds = []
        indices = list(range(n))

        for r in range(rounds_count):
            round_matches = []
            for i in range(half):
                t1_idx = indices[i]
                t2_idx = indices[n - 1 - i]
                t1 = team_list[t1_idx]
                t2 = team_list[t2_idx]

                # Don't schedule match if one team is BYE
                if t1["id"] is None or t2["id"] is None:
                    continue

                # Alternate home/away based on round to keep balance
                if (r + i) % 2 == 0:
                    round_matches.append((t1, t2))
                else:
                    round_matches.append((t2, t1))

            all_rounds.append(round_matches)

            # Rotate indices, fixing the first element
            indices = [indices[0]] + [indices[-1]] + indices[1:-1]

        if double_round:
            second_leg_rounds = []
            for r_matches in all_rounds:
                inverted = [(away, home) for (home, away) in r_matches]
                second_leg_rounds.append(inverted)
            all_rounds.extend(second_leg_rounds)

        return all_rounds

    # ----------------------------------------------------
    # Generate Group Stage Fixtures
    # ----------------------------------------------------
    # Generate Group Stage Fixtures
    # ----------------------------------------------------
    def preview_group_fixtures(
        self,
        start_date: str = "",
        start_time: str = "16:00",
        match_duration_mins: int = 30,
        venues: Optional[List[str]] = None,
        double_round: bool = False,
        day_end_time: str = "20:00",
        end_date: str = "",
        days_per_matchweek: int = 3,
        target_matchweek: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Generate balanced, round-interleaved fixtures for all groups with:
        1. Multi-pitch simultaneous scheduling (pitches utilized concurrently).
        2. Round-by-round interleaving across groups (all Round 1 matches before Round 2).
        3. Matchweek timeline splitting (1 match per team every days_per_matchweek days, e.g. 3 days).
        4. Operating hours limit (matches strictly within daily kick-off window, never past midnight).
        5. Zero double-booking of teams in the same time slot.
        6. Support for generating all matchweeks or isolating a specific target matchweek.
        """
        groups = self.db.execute_query("SELECT id, name FROM groups ORDER BY display_order ASC, name ASC;")
        if not groups:
            raise ValueError("No groups found. Please create groups and assign teams first.")

        if not venues:
            venues = [self.db.get_setting("default_venue", "Minaram Stadium")]
        else:
            cleaned_venues = []
            for v in venues:
                for sub in str(v).split(","):
                    s = sub.strip()
                    if s and s not in cleaned_venues:
                        cleaned_venues.append(s)
            venues = cleaned_venues or [self.db.get_setting("default_venue", "Minaram Stadium")]

        if not start_date:
            start_date = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")

        try:
            curr_date = datetime.strptime(start_date, "%Y-%m-%d").date()
        except Exception:
            curr_date = (datetime.now() + timedelta(days=1)).date()

        try:
            start_t = datetime.strptime(start_time, "%H:%M").time()
        except Exception:
            start_t = datetime.strptime("16:00", "%H:%M").time()

        try:
            end_t = datetime.strptime(day_end_time, "%H:%M").time()
        except Exception:
            end_t = datetime.strptime("20:00", "%H:%M").time()

        group_data: Dict[int, Dict[str, Any]] = {}
        for g in groups:
            g_id = g["id"]
            g_name = g["name"]
            team_rows = self.db.execute_query(
                "SELECT id, name FROM teams WHERE group_id = ? AND status = 'Confirmed' ORDER BY seed DESC, name ASC;",
                (g_id,)
            )
            teams = [{"id": r["id"], "name": r["name"]} for r in team_rows]
            if len(teams) >= 2:
                rounds = self.generate_round_robin_pairings(teams, double_round=double_round)
                group_data[g_id] = {
                    "name": g_name,
                    "rounds": rounds
                }

        if not group_data:
            return []

        max_rounds = max(len(g["rounds"]) for g in group_data.values())

        if days_per_matchweek < 1:
            days_per_matchweek = 3

        if end_date:
            try:
                target_end = datetime.strptime(end_date, "%Y-%m-%d").date()
                if target_end > curr_date and max_rounds > 1:
                    span_days = (target_end - curr_date).days
                    auto_interval = max(1, span_days // (max_rounds - 1))
                    if days_per_matchweek == 3 and auto_interval != 3:
                        days_per_matchweek = auto_interval
            except Exception:
                pass

        fixtures: List[Dict[str, Any]] = []

        # Determine starting match number and rounds to schedule
        if target_matchweek is not None and target_matchweek > 1:
            existing = self.db.execute_one(
                "SELECT COALESCE(MAX(match_number), 0) AS m FROM matches WHERE round_number < ?;",
                (target_matchweek,)
            )
            if existing and existing["m"] > 0:
                match_num = existing["m"] + 1
            else:
                prior_matches = 0
                for r in range(target_matchweek - 1):
                    for g_info in group_data.values():
                        if r < len(g_info["rounds"]):
                            prior_matches += len(g_info["rounds"][r])
                match_num = prior_matches + 1
            rounds_to_schedule = [target_matchweek - 1] if (target_matchweek - 1 < max_rounds) else []
        elif target_matchweek == 1:
            match_num = 1
            rounds_to_schedule = [0]
        else:
            match_num = 1
            rounds_to_schedule = list(range(max_rounds))

        for round_idx in rounds_to_schedule:
            mw_number = round_idx + 1
            # Each matchweek is spaced out by days_per_matchweek (e.g. 3 days apart)
            mw_date = curr_date + timedelta(days=round_idx * days_per_matchweek)
            slot_dt = datetime.combine(mw_date, start_t)
            slot_end_dt = datetime.combine(mw_date, end_t)

            # Gather all matches for this round across all groups (interleaving groups)
            round_matches: List[Dict[str, Any]] = []
            for g_id, g_info in group_data.items():
                if round_idx < len(g_info["rounds"]):
                    for home, away in g_info["rounds"][round_idx]:
                        round_matches.append({
                            "group_id": g_id,
                            "group_name": g_info["name"],
                            "round_number": mw_number,
                            "home": home,
                            "away": away
                        })

            # Schedule this round across pitches
            while round_matches:
                # If current slot would finish past operating hours, advance to next day within matchday window
                if slot_dt + timedelta(minutes=match_duration_mins) > slot_end_dt:
                    mw_date += timedelta(days=1)
                    slot_dt = datetime.combine(mw_date, start_t)
                    slot_end_dt = datetime.combine(mw_date, end_t)

                teams_playing_in_slot = set()

                for venue in venues:
                    match_to_assign = None
                    for candidate in round_matches:
                        h_id = candidate["home"]["id"]
                        a_id = candidate["away"]["id"]
                        if h_id not in teams_playing_in_slot and a_id not in teams_playing_in_slot:
                            match_to_assign = candidate
                            break

                    if match_to_assign is not None:
                        round_matches.remove(match_to_assign)
                        teams_playing_in_slot.add(match_to_assign["home"]["id"])
                        teams_playing_in_slot.add(match_to_assign["away"]["id"])

                        fixtures.append({
                            "match_number": match_num,
                            "stage": "Group Stage",
                            "group_id": match_to_assign["group_id"],
                            "group_name": match_to_assign["group_name"],
                            "round_number": mw_number,
                            "bracket_slot": "",
                            "home_team_id": match_to_assign["home"]["id"],
                            "away_team_id": match_to_assign["away"]["id"],
                            "home_team_name": match_to_assign["home"]["name"],
                            "away_team_name": match_to_assign["away"]["name"],
                            "scheduled_date": slot_dt.strftime("%Y-%m-%d"),
                            "scheduled_time": slot_dt.strftime("%H:%M"),
                            "venue": venue,
                            "status": "Scheduled",
                            "notes": f"Matchweek {mw_number}"
                        })
                        match_num += 1

                # Advance time slot by match duration
                slot_dt += timedelta(minutes=match_duration_mins)

        return fixtures

    # ----------------------------------------------------
    # Generate League Fixtures (Single or Double Round Robin)
    # ----------------------------------------------------
    def preview_league_fixtures(
        self,
        start_date: str = "",
        start_time: str = "16:00",
        match_duration_mins: int = 30,
        venues: Optional[List[str]] = None,
        double_round: bool = False,
        day_end_time: str = "20:00",
        end_date: str = "",
        days_per_matchweek: int = 3,
        target_matchweek: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """Generate proposed fixtures for a full league tournament with matchweek spacing, multi-pitch support and operating hours."""
        teams_rows = self.db.execute_query(
            "SELECT id, name FROM teams WHERE status = 'Confirmed' ORDER BY seed DESC, name ASC;"
        )
        teams = [{"id": r["id"], "name": r["name"]} for r in teams_rows]
        if len(teams) < 2:
            raise ValueError("Need at least 2 confirmed teams to generate league fixtures.")

        if not venues:
            venues = [self.db.get_setting("default_venue", "Minaram Stadium")]
        else:
            cleaned_venues = []
            for v in venues:
                for sub in str(v).split(","):
                    s = sub.strip()
                    if s and s not in cleaned_venues:
                        cleaned_venues.append(s)
            venues = cleaned_venues or [self.db.get_setting("default_venue", "Minaram Stadium")]

        if not start_date:
            start_date = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")

        try:
            curr_date = datetime.strptime(start_date, "%Y-%m-%d").date()
        except Exception:
            curr_date = (datetime.now() + timedelta(days=1)).date()

        try:
            start_t = datetime.strptime(start_time, "%H:%M").time()
        except Exception:
            start_t = datetime.strptime("16:00", "%H:%M").time()

        try:
            end_t = datetime.strptime(day_end_time, "%H:%M").time()
        except Exception:
            end_t = datetime.strptime("20:00", "%H:%M").time()

        rounds = self.generate_round_robin_pairings(teams, double_round=double_round)
        if not rounds:
            return []

        if days_per_matchweek < 1:
            days_per_matchweek = 3

        if end_date:
            try:
                target_end = datetime.strptime(end_date, "%Y-%m-%d").date()
                if target_end > curr_date and len(rounds) > 1:
                    span_days = (target_end - curr_date).days
                    auto_interval = max(1, span_days // (len(rounds) - 1))
                    if days_per_matchweek == 3 and auto_interval != 3:
                        days_per_matchweek = auto_interval
            except Exception:
                pass

        fixtures: List[Dict[str, Any]] = []

        if target_matchweek is not None and target_matchweek > 1:
            existing = self.db.execute_one(
                "SELECT COALESCE(MAX(match_number), 0) AS m FROM matches WHERE round_number < ?;",
                (target_matchweek,)
            )
            if existing and existing["m"] > 0:
                match_num = existing["m"] + 1
            else:
                prior_matches = sum(len(rounds[r]) for r in range(min(target_matchweek - 1, len(rounds))))
                match_num = prior_matches + 1
            rounds_indices = [target_matchweek] if (target_matchweek <= len(rounds)) else []
        elif target_matchweek == 1:
            match_num = 1
            rounds_indices = [1]
        else:
            match_num = 1
            rounds_indices = list(range(1, len(rounds) + 1))

        for round_idx in rounds_indices:
            r_matches = rounds[round_idx - 1]
            mw_date = curr_date + timedelta(days=(round_idx - 1) * days_per_matchweek)
            slot_dt = datetime.combine(mw_date, start_t)
            slot_end_dt = datetime.combine(mw_date, end_t)

            round_matches = [{"home": h, "away": a, "round_number": round_idx} for h, a in r_matches]

            while round_matches:
                if slot_dt + timedelta(minutes=match_duration_mins) > slot_end_dt:
                    mw_date += timedelta(days=1)
                    slot_dt = datetime.combine(mw_date, start_t)
                    slot_end_dt = datetime.combine(mw_date, end_t)

                teams_playing_in_slot = set()

                for venue in venues:
                    match_to_assign = None
                    for candidate in round_matches:
                        h_id = candidate["home"]["id"]
                        a_id = candidate["away"]["id"]
                        if h_id not in teams_playing_in_slot and a_id not in teams_playing_in_slot:
                            match_to_assign = candidate
                            break

                    if match_to_assign is not None:
                        round_matches.remove(match_to_assign)
                        teams_playing_in_slot.add(match_to_assign["home"]["id"])
                        teams_playing_in_slot.add(match_to_assign["away"]["id"])

                        fixtures.append({
                            "match_number": match_num,
                            "stage": "League",
                            "group_id": None,
                            "group_name": "League",
                            "round_number": match_to_assign["round_number"],
                            "bracket_slot": "",
                            "home_team_id": match_to_assign["home"]["id"],
                            "away_team_id": match_to_assign["away"]["id"],
                            "home_team_name": match_to_assign["home"]["name"],
                            "away_team_name": match_to_assign["away"]["name"],
                            "scheduled_date": slot_dt.strftime("%Y-%m-%d"),
                            "scheduled_time": slot_dt.strftime("%H:%M"),
                            "venue": venue,
                            "status": "Scheduled",
                            "notes": f"Matchweek {round_idx}"
                        })
                        match_num += 1

                slot_dt += timedelta(minutes=match_duration_mins)

        return fixtures

    def get_total_matchweeks(self, format_type: str = "Group Stage", double_round: bool = False) -> int:
        """Calculate total number of matchweeks for the competition."""
        if "League" in format_type:
            teams_rows = self.db.execute_query("SELECT id FROM teams WHERE status = 'Confirmed';")
            n = len(teams_rows)
            if n < 2:
                return 0
            base_rounds = n - 1 if n % 2 == 0 else n
            return base_rounds * 2 if double_round else base_rounds
        else:
            groups = self.db.execute_query("SELECT id FROM groups;")
            max_teams = 0
            for g in groups:
                cnt = self.db.execute_one(
                    "SELECT COUNT(*) AS c FROM teams WHERE group_id = ? AND status = 'Confirmed';",
                    (g["id"],)
                )["c"]
                if cnt > max_teams:
                    max_teams = cnt
            if max_teams < 2:
                num_groups = int(self.db.get_setting("num_groups", "2"))
                total_teams = self.db.execute_one("SELECT COUNT(*) AS c FROM teams WHERE status = 'Confirmed';")["c"]
                if total_teams >= 2 and num_groups > 0:
                    per_group = max(2, (total_teams + num_groups - 1) // num_groups)
                    return per_group - 1 if per_group % 2 == 0 else per_group
                return 3
            base_rounds = max_teams - 1 if max_teams % 2 == 0 else max_teams
            return base_rounds * 2 if double_round else base_rounds

    # ----------------------------------------------------
    # Save Generated Fixtures
    # ----------------------------------------------------
    def save_fixtures(
        self,
        fixtures: List[Dict[str, Any]],
        clear_existing: bool = False,
        clear_round: Optional[int] = None
    ) -> int:
        """
        Save a list of fixture dictionaries to database.
        Supports clearing all existing fixtures, or clearing only a specific round/matchweek.
        """
        with self.db.transaction(action="fixtures_saved") as conn:
            cursor = conn.cursor()
            if clear_existing:
                cursor.execute("DELETE FROM match_audit_log;")
                cursor.execute("DELETE FROM matches;")
            elif clear_round is not None:
                cursor.execute("DELETE FROM matches WHERE round_number = ?;", (clear_round,))
                cursor.execute("DELETE FROM match_audit_log WHERE match_id NOT IN (SELECT id FROM matches);")

            count = 0
            for f in fixtures:
                cursor.execute("""
                    INSERT INTO matches (
                        match_number, stage, group_id, round_number, bracket_slot,
                        home_team_id, away_team_id, scheduled_date, scheduled_time,
                        venue, status, notes
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'Scheduled', ?);
                """, (
                    f["match_number"],
                    f["stage"],
                    f.get("group_id"),
                    f.get("round_number", 1),
                    f.get("bracket_slot", ""),
                    f["home_team_id"],
                    f["away_team_id"],
                    f.get("scheduled_date", ""),
                    f.get("scheduled_time", ""),
                    f.get("venue", "Minaram Stadium"),
                    f.get("notes", "")
                ))
                count += 1

        return count

    # ----------------------------------------------------
    # Conflict Detection
    # ----------------------------------------------------
    def detect_conflicts(self, duration_mins: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Detect scheduling conflicts:
        1. Team playing two matches on the same date with conflicting times.
        2. Venue booked for multiple matches at the exact same date & time.
        """
        matches = self.get_matches()
        conflicts = []

        if duration_mins is not None:
            duration = duration_mins
        else:
            try:
                duration = int(self.db.get_setting("match_duration_minutes", "30"))
            except ValueError:
                duration = 30

        # Venue time conflicts
        venue_slots: Dict[Tuple[str, str, str], List[Match]] = {}
        for m in matches:
            if m.scheduled_date and m.scheduled_time and m.venue:
                key = (m.venue, m.scheduled_date, m.scheduled_time)
                venue_slots.setdefault(key, []).append(m)

        for (v, dt, tm), m_list in venue_slots.items():
            if len(m_list) > 1:
                conflicts.append({
                    "type": "Venue Double Booking",
                    "severity": "High",
                    "details": f"Venue '{v}' is scheduled for {len(m_list)} matches at {dt} {tm}",
                    "match_ids": [m.id for m in m_list],
                    "match_numbers": [m.match_number for m in m_list]
                })

        # Team conflict: same team scheduled for 2 matches within match_duration of each other
        team_matches: Dict[int, List[Match]] = {}
        for m in matches:
            if m.home_team_id:
                team_matches.setdefault(m.home_team_id, []).append(m)
            if m.away_team_id:
                team_matches.setdefault(m.away_team_id, []).append(m)

        for team_id, m_list in team_matches.items():
            # Check pairwise
            for i in range(len(m_list)):
                for j in range(i + 1, len(m_list)):
                    m1 = m_list[i]
                    m2 = m_list[j]
                    if m1.scheduled_date == m2.scheduled_date and m1.scheduled_date:
                        try:
                            t1 = datetime.strptime(f"{m1.scheduled_date} {m1.scheduled_time}", "%Y-%m-%d %H:%M")
                            t2 = datetime.strptime(f"{m2.scheduled_date} {m2.scheduled_time}", "%Y-%m-%d %H:%M")
                            diff = abs((t1 - t2).total_seconds()) / 60.0
                            if diff < duration:
                                conflicts.append({
                                    "type": "Team Schedule Overlap",
                                    "severity": "Critical",
                                    "details": f"Team (ID #{team_id}) is scheduled for Match #{m1.match_number} ({m1.scheduled_time}) and Match #{m2.match_number} ({m2.scheduled_time}) only {int(diff)} mins apart",
                                    "match_ids": [m1.id, m2.id],
                                    "match_numbers": [m1.match_number, m2.match_number]
                                })
                        except Exception:
                            pass

        return conflicts

    # ----------------------------------------------------
    # Queries & Updates
    # ----------------------------------------------------
    def get_matches(
        self,
        stage: Optional[str] = None,
        group_id: Optional[int] = None,
        status: Optional[str] = None,
        date: Optional[str] = None
    ) -> List[Match]:
        query = """
            SELECT m.id, m.match_number, m.stage, m.group_id, g.name AS group_name,
                   m.round_number, m.bracket_slot,
                   m.home_team_id, ht.name AS home_name, ht.captain_name AS home_captain, ht.phone_number AS home_phone,
                   m.away_team_id, at.name AS away_name, at.captain_name AS away_captain, at.phone_number AS away_phone,
                   m.scheduled_date, m.scheduled_time, m.venue,
                   m.home_score, m.away_score, m.home_penalty, m.away_penalty,
                   m.status, m.winner_team_id, wt.name AS winner_name,
                   m.notes, m.completed_at
            FROM matches m
            LEFT JOIN groups g ON m.group_id = g.id
            LEFT JOIN teams ht ON m.home_team_id = ht.id
            LEFT JOIN teams at ON m.away_team_id = at.id
            LEFT JOIN teams wt ON m.winner_team_id = wt.id
            WHERE 1=1
        """
        params = []
        if stage and stage != "All":
            query += " AND m.stage = ?"
            params.append(stage)
        if group_id is not None:
            query += " AND m.group_id = ?"
            params.append(group_id)
        if status and status != "All":
            query += " AND m.status = ?"
            params.append(status)
        if date and date.strip():
            query += " AND m.scheduled_date = ?"
            params.append(date.strip())

        query += " ORDER BY m.stage ASC, m.round_number ASC, m.match_number ASC;"

        rows = self.db.execute_query(query, tuple(params))
        return [
            Match(
                id=r["id"],
                match_number=r["match_number"],
                stage=r["stage"],
                group_id=r["group_id"],
                group_name=r["group_name"],
                round_number=r["round_number"],
                bracket_slot=r["bracket_slot"] or "",
                home_team_id=r["home_team_id"],
                away_team_id=r["away_team_id"],
                home_team_name=r["home_name"] or "TBD",
                away_team_name=r["away_name"] or "TBD",
                home_captain=r["home_captain"] or "",
                home_phone=r["home_phone"] or "",
                away_captain=r["away_captain"] or "",
                away_phone=r["away_phone"] or "",
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
            for r in rows
        ]

    def add_manual_match(
        self,
        home_team_id: int,
        away_team_id: int,
        stage: str = "Group Stage",
        group_id: Optional[int] = None,
        round_number: int = 1,
        scheduled_date: str = "",
        scheduled_time: str = "",
        venue: str = "Minaram Stadium",
        notes: str = ""
    ) -> int:
        if home_team_id == away_team_id:
            raise ValueError("A team cannot play against itself.")

        max_num = self.db.execute_one("SELECT MAX(match_number) AS m FROM matches;")["m"] or 0
        match_id = self.db.execute_non_query("""
            INSERT INTO matches (
                match_number, stage, group_id, round_number,
                home_team_id, away_team_id, scheduled_date, scheduled_time, venue, status, notes
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 'Scheduled', ?);
        """, (
            max_num + 1, stage, group_id, round_number,
            home_team_id, away_team_id, scheduled_date, scheduled_time, venue, notes
        ))
        return match_id

    def update_match_schedule(
        self,
        match_id: int,
        scheduled_date: str,
        scheduled_time: str,
        venue: str,
        status: Optional[str] = None
    ) -> None:
        if status:
            self.db.execute_non_query("""
                UPDATE matches SET scheduled_date = ?, scheduled_time = ?, venue = ?, status = ?
                WHERE id = ?;
            """, (scheduled_date, scheduled_time, venue, status, match_id))
        else:
            self.db.execute_non_query("""
                UPDATE matches SET scheduled_date = ?, scheduled_time = ?, venue = ?
                WHERE id = ?;
            """, (scheduled_date, scheduled_time, venue, match_id))

    def delete_match(self, match_id: int) -> None:
        with self.db.transaction() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM match_audit_log WHERE match_id = ?;", (match_id,))
            cursor.execute("DELETE FROM matches WHERE id = ?;", (match_id,))

#!/usr/bin/env python3
"""
Minaram Cup — Tournament Match Checker & Analytics Tool
======================================================
Comprehensive match progress tracker, status analyzer, and tournament statistics reporter.

Capabilities:
  • Calculates total matches, completed matches, pending/not-completed matches, and % completion.
  • Breakdown by tournament stage (Group Stage, Knockouts, Quarter-Finals, Semi-Finals, Final).
  • Detailed group-by-group completion tracking (completed vs pending per group).
  • Match result analytics: goals scored, averages, home/away wins, draws, penalty shootouts, clean sheets.
  • Top attacking teams, best defensive records, and thriller matches (highest scoring / largest margins).
  • Upcoming/pending fixtures browser and recent completed match results viewer.
  • Filter matches by Stage, Group, or Team name.
  • Dual data source: Live SQLite Database (data/minaram_cup.db) with seamless fallback to minaram_fixtures.csv.
  • Export reports to JSON, Markdown, or CSV.
  • Optional interactive mode for terminal navigation.

Usage:
  py check_matches.py                  # Full tournament summary dashboard
  py check_matches.py --remaining-group-matches # Check how many group matches are remaining
  py check_matches.py --count          # Quick match count overview (completed, non-completed, etc.)
  py check_matches.py --count-completed # Direct count of completed matches
  py check_matches.py --count-pending  # Direct count of non-completed / pending matches
  py check_matches.py --count-total    # Total match count
  py check_matches.py --count completed -q  # Raw number only (e.g. 58) for scripts/pipes
  py check_matches.py --group "Group A" --count # Count completed vs non-completed in Group A
  py check_matches.py --team "MIDHUN" --count   # Count completed vs pending for a team
  py check_matches.py --pending        # List all pending / not completed matches
  py check_matches.py --completed      # List all completed matches with scores
  py check_matches.py --group "Group A"# Show matches and stats for a specific group
  py check_matches.py --stage "Final"  # Show matches for a specific stage
  py check_matches.py --team "MIDHUN"  # Show all fixtures & results for a specific team
  py check_matches.py --export json    # Export summary report to JSON
  py check_matches.py --export md      # Export summary report to Markdown
  py check_matches.py --interactive    # Launch interactive menu
"""

import sys
import os
import csv
import json
import sqlite3
import argparse
from pathlib import Path
from datetime import datetime
from collections import defaultdict
from typing import List, Dict, Any, Optional, Tuple

# Ensure Windows terminal handles UTF-8 smoothly
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass
if hasattr(sys.stderr, "reconfigure"):
    try:
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

# Base paths
ROOT_DIR = Path(__file__).resolve().parent
DB_PATH = ROOT_DIR / "data" / "minaram_cup.db"
CSV_PATH = ROOT_DIR / "minaram_fixtures.csv"

# ANSI Colors for terminal output
class Colors:
    HEADER = "\033[95m"
    BLUE = "\033[94m"
    CYAN = "\033[96m"
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    RED = "\033[91m"
    BOLD = "\033[1m"
    UNDERLINE = "\033[4m"
    DIM = "\033[2m"
    RESET = "\033[0m"

    @classmethod
    def disable(cls):
        cls.HEADER = ""
        cls.BLUE = ""
        cls.CYAN = ""
        cls.GREEN = ""
        cls.YELLOW = ""
        cls.RED = ""
        cls.BOLD = ""
        cls.UNDERLINE = ""
        cls.DIM = ""
        cls.RESET = ""


def format_progress_bar(completed: int, total: int, width: int = 28) -> str:
    """Generate a visual ASCII/Unicode progress bar."""
    if total == 0:
        return "[----------------]"
    pct = completed / total
    filled = int(round(width * pct))
    bar = "█" * filled + "░" * (width - filled)
    return f"[{bar}] {pct * 100:5.1f}%"


class MatchChecker:
    """Loads, verifies, and analyzes tournament match records from SQLite or CSV."""

    def __init__(self, source_path: Optional[Path] = None):
        self.source_path = source_path
        self.source_type = "unknown"
        self.matches: List[Dict[str, Any]] = []
        self._load_matches()

    def _load_matches(self) -> None:
        """Attempt to load from SQLite first; fallback to CSV if database is unavailable."""
        target = self.source_path

        # If explicit path provided
        if target and target.exists():
            if str(target).endswith(".db"):
                self._load_from_sqlite(target)
                return
            elif str(target).endswith(".csv"):
                self._load_from_csv(target)
                return

        # Default detection: SQLite DB first
        if DB_PATH.exists():
            try:
                self._load_from_sqlite(DB_PATH)
                return
            except Exception as e:
                # If DB load failed, fall back to CSV
                pass

        # Secondary fallback: CSV
        if CSV_PATH.exists():
            self._load_from_csv(CSV_PATH)
            return

        raise FileNotFoundError(
            f"Could not locate tournament data. Neither SQLite DB '{DB_PATH}' nor CSV '{CSV_PATH}' was found."
        )

    def _load_from_sqlite(self, db_path: Path) -> None:
        """Read match data and join team & group labels from SQLite."""
        conn = sqlite3.connect(str(db_path))
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()

        query = """
            SELECT 
                m.id,
                m.match_number,
                m.stage,
                COALESCE(g.name, '') AS group_name,
                m.round_number,
                m.bracket_slot,
                COALESCE(ht.name, 'TBD') AS home_team,
                COALESCE(at.name, 'TBD') AS away_team,
                COALESCE(wt.name, '') AS winner_team,
                m.home_score,
                m.away_score,
                m.home_penalty,
                m.away_penalty,
                m.status,
                COALESCE(m.scheduled_date, '') AS scheduled_date,
                COALESCE(m.scheduled_end_date, '') AS scheduled_end_date,
                COALESCE(m.scheduled_time, '') AS scheduled_time,
                COALESCE(m.venue, '') AS venue,
                COALESCE(m.completed_at, '') AS completed_at,
                COALESCE(m.notes, '') AS notes
            FROM matches m
            LEFT JOIN groups g ON m.group_id = g.id
            LEFT JOIN teams ht ON m.home_team_id = ht.id
            LEFT JOIN teams at ON m.away_team_id = at.id
            LEFT JOIN teams wt ON m.winner_team_id = wt.id
            ORDER BY m.match_number ASC;
        """
        rows = cur.execute(query).fetchall()
        conn.close()

        self.matches = []
        for r in rows:
            m = dict(r)
            # Normalize completed status
            m["is_completed"] = m["status"] in ("Completed", "Walkover")
            self.matches.append(m)

        self.source_type = f"SQLite Database ({db_path.name})"

    def _load_from_csv(self, csv_path: Path) -> None:
        """Read match records from CSV file."""
        self.matches = []
        with open(csv_path, mode="r", encoding="utf-8-sig") as f:
            reader = csv.DictReader(f)
            for row in reader:
                # Field names match minaram_fixtures.csv:
                # Match #,Stage,Group,Round,Home Team,Away Team,Date,Time,Venue,Score,Status,Winner
                score_str = row.get("Score", "").strip()
                home_score = None
                away_score = None
                home_penalty = None
                away_penalty = None

                if score_str and score_str != "vs" and "-" in score_str:
                    try:
                        # Handle potential penalty like "2 - 2 (4-3 pen)"
                        main_part = score_str
                        if "(" in score_str and "pen" in score_str:
                            main_part = score_str.split("(")[0].strip()
                            pen_part = score_str.split("(")[1].replace("pen)", "").replace(")", "").strip()
                            if "-" in pen_part:
                                hp, ap = pen_part.split("-")
                                home_penalty = int(hp.strip())
                                away_penalty = int(ap.strip())

                        parts = main_part.split("-")
                        home_score = int(parts[0].strip())
                        away_score = int(parts[1].strip())
                    except Exception:
                        pass

                status = row.get("Status", "Scheduled").strip()
                winner = row.get("Winner", "").strip()
                if winner == "-":
                    winner = ""

                m = {
                    "id": None,
                    "match_number": int(row.get("Match #", 0) or 0),
                    "stage": row.get("Stage", "Group Stage").strip(),
                    "group_name": row.get("Group", "").strip(),
                    "round_number": int(row.get("Round", 1) or 1),
                    "bracket_slot": "",
                    "home_team": row.get("Home Team", "TBD").strip(),
                    "away_team": row.get("Away Team", "TBD").strip(),
                    "winner_team": winner,
                    "home_score": home_score,
                    "away_score": away_score,
                    "home_penalty": home_penalty,
                    "away_penalty": away_penalty,
                    "status": status,
                    "scheduled_date": row.get("Date", "").strip(),
                    "scheduled_end_date": "",
                    "scheduled_time": row.get("Time", "").strip(),
                    "venue": row.get("Venue", "").strip(),
                    "completed_at": "",
                    "notes": "",
                    "is_completed": status in ("Completed", "Walkover"),
                }
                self.matches.append(m)

        self.source_type = f"Fixtures CSV ({csv_path.name})"

    # -------------------------------------------------------------------------
    # Core Aggregations & Statistics
    # -------------------------------------------------------------------------
    def get_summary_stats(self) -> Dict[str, Any]:
        """Compute full statistical overview of tournament match progress."""
        total = len(self.matches)
        completed = sum(1 for m in self.matches if m["is_completed"])
        not_completed = total - completed
        completion_pct = (completed / total * 100) if total > 0 else 0.0

        # Status counts
        status_counts = defaultdict(int)
        for m in self.matches:
            status_counts[m["status"]] += 1

        # Stage breakdown
        stage_stats = defaultdict(lambda: {"total": 0, "completed": 0, "pending": 0})
        for m in self.matches:
            st = m["stage"] or "Unassigned"
            stage_stats[st]["total"] += 1
            if m["is_completed"]:
                stage_stats[st]["completed"] += 1
            else:
                stage_stats[st]["pending"] += 1

        for st, data in stage_stats.items():
            tot = data["total"]
            data["pct"] = (data["completed"] / tot * 100) if tot > 0 else 0.0

        # Group breakdown
        group_stats = defaultdict(lambda: {"total": 0, "completed": 0, "pending": 0})
        for m in self.matches:
            grp = m["group_name"]
            if grp:
                group_stats[grp]["total"] += 1
                if m["is_completed"]:
                    group_stats[grp]["completed"] += 1
                else:
                    group_stats[grp]["pending"] += 1

        for grp, data in group_stats.items():
            tot = data["total"]
            data["pct"] = (data["completed"] / tot * 100) if tot > 0 else 0.0
            data["all_done"] = (data["completed"] == tot and tot > 0)

        # Goal & match dynamics
        total_goals = 0
        home_wins = 0
        away_wins = 0
        draws = 0
        penalty_shootouts = 0
        clean_sheets = 0
        highest_scoring_match = None
        highest_score_sum = -1
        biggest_blowout = None
        biggest_margin = -1

        # Team stats
        team_goals_scored = defaultdict(int)
        team_goals_conceded = defaultdict(int)
        team_matches_played = defaultdict(int)
        team_clean_sheets = defaultdict(int)

        for m in self.matches:
            if m["is_completed"] and m["home_score"] is not None and m["away_score"] is not None:
                hs = m["home_score"]
                as_ = m["away_score"]
                match_goals = hs + as_
                total_goals += match_goals

                ht = m["home_team"]
                at = m["away_team"]
                team_matches_played[ht] += 1
                team_matches_played[at] += 1
                team_goals_scored[ht] += hs
                team_goals_scored[at] += as_
                team_goals_conceded[ht] += as_
                team_goals_conceded[at] += hs

                if as_ == 0:
                    clean_sheets += 1
                    team_clean_sheets[ht] += 1
                if hs == 0:
                    clean_sheets += 1
                    team_clean_sheets[at] += 1

                if hs > as_:
                    home_wins += 1
                elif as_ > hs:
                    away_wins += 1
                else:
                    draws += 1
                    if m.get("home_penalty") is not None and m.get("away_penalty") is not None:
                        penalty_shootouts += 1

                # Thriller check
                if match_goals > highest_score_sum:
                    highest_score_sum = match_goals
                    highest_scoring_match = m

                # Blowout check
                margin = abs(hs - as_)
                if margin > biggest_margin:
                    biggest_margin = margin
                    biggest_blowout = m

        avg_goals = (total_goals / completed) if completed > 0 else 0.0

        # Top scoring teams
        top_scorers = sorted(
            [{"team": t, "goals": g, "matches": team_matches_played[t], "avg": round(g / max(1, team_matches_played[t]), 2)}
             for t, g in team_goals_scored.items()],
            key=lambda x: (x["goals"], x["avg"]),
            reverse=True
        )[:5]

        # Best defense (lowest conceded, at least 1 match played)
        best_defense = sorted(
            [{"team": t, "conceded": c, "matches": team_matches_played[t], "avg": round(c / max(1, team_matches_played[t]), 2), "clean_sheets": team_clean_sheets[t]}
             for t, c in team_goals_conceded.items() if team_matches_played[t] > 0],
            key=lambda x: (x["avg"], x["conceded"])
        )[:5]

        return {
            "source": self.source_type,
            "total_matches": total,
            "completed_matches": completed,
            "not_completed_matches": not_completed,
            "completion_percentage": round(completion_pct, 1),
            "status_breakdown": dict(status_counts),
            "stage_breakdown": dict(stage_stats),
            "group_breakdown": dict(group_stats),
            "groups_total": len(group_stats),
            "groups_completed_count": sum(1 for g in group_stats.values() if g["all_done"]),
            "goals": {
                "total_goals": total_goals,
                "average_goals_per_match": round(avg_goals, 2),
                "home_wins": home_wins,
                "away_wins": away_wins,
                "draws": draws,
                "penalty_shootouts": penalty_shootouts,
                "clean_sheets": clean_sheets,
                "highest_scoring_match": highest_scoring_match,
                "biggest_blowout": biggest_blowout,
            },
            "top_scorers": top_scorers,
            "best_defense": best_defense,
        }

    # -------------------------------------------------------------------------
    # Filtering Helpers
    # -------------------------------------------------------------------------
    def get_pending_matches(self, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """Return matches that are not completed yet."""
        pending = [m for m in self.matches if not m["is_completed"]]
        return pending[:limit] if limit else pending

    def get_completed_matches(self, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """Return matches that have been completed."""
        comp = [m for m in self.matches if m["is_completed"]]
        return comp[:limit] if limit else comp

    def filter_by_group(self, group_name: str) -> List[Dict[str, Any]]:
        """Filter matches belonging to a specific group."""
        target = group_name.strip().lower()
        return [
            m for m in self.matches
            if target in m["group_name"].lower() or target in m["stage"].lower()
        ]

    def filter_by_stage(self, stage_name: str) -> List[Dict[str, Any]]:
        """Filter matches belonging to a stage."""
        target = stage_name.strip().lower()
        return [m for m in self.matches if target in m["stage"].lower()]

    def filter_by_team(self, team_name: str) -> List[Dict[str, Any]]:
        """Filter matches where team is either home or away."""
        target = team_name.strip().lower()
        return [
            m for m in self.matches
            if target in m["home_team"].lower() or target in m["away_team"].lower()
        ]

    def compute_counts(self, match_list: Optional[List[Dict[str, Any]]] = None) -> Dict[str, Any]:
        """Compute quick counts for all matches or a provided subset."""
        target_list = self.matches if match_list is None else match_list
        total = len(target_list)
        completed = sum(1 for m in target_list if m["is_completed"])
        pending = total - completed
        pct = (completed / total * 100) if total > 0 else 0.0

        status_counts = defaultdict(int)
        stage_counts = defaultdict(lambda: {"total": 0, "completed": 0, "pending": 0})
        group_counts = defaultdict(lambda: {"total": 0, "completed": 0, "pending": 0})

        for m in target_list:
            status_counts[m["status"]] += 1
            st = m["stage"] or "Unassigned"
            stage_counts[st]["total"] += 1
            if m["is_completed"]:
                stage_counts[st]["completed"] += 1
            else:
                stage_counts[st]["pending"] += 1

            grp = m["group_name"]
            if grp:
                group_counts[grp]["total"] += 1
                if m["is_completed"]:
                    group_counts[grp]["completed"] += 1
                else:
                    group_counts[grp]["pending"] += 1

        return {
            "total": total,
            "completed": completed,
            "pending": pending,
            "completion_pct": round(pct, 1),
            "status_counts": dict(status_counts),
            "stage_counts": dict(stage_counts),
            "group_counts": dict(group_counts),
        }


# -----------------------------------------------------------------------------
# Terminal Printing & Display Functions
# -----------------------------------------------------------------------------
def print_counts(
    counts: Dict[str, Any],
    target: str = "all",
    filter_label: Optional[str] = None,
    raw: bool = False
) -> None:
    """Print match count summary or specific raw/formatted count."""
    c = Colors
    target = (target or "all").lower().strip()

    # Raw single-value output for scripting
    if raw:
        if target in ("completed", "done"):
            print(counts["completed"])
        elif target in ("pending", "non_completed", "not_completed", "left"):
            print(counts["pending"])
        elif target in ("total", "all_matches"):
            print(counts["total"])
        elif target in ("pct", "percentage"):
            print(counts["completion_pct"])
        else:
            print(f"{counts['completed']}/{counts['total']}")
        return

    # Single targeted outputs (non-raw)
    if target in ("completed", "done"):
        label = f" [{filter_label}]" if filter_label else ""
        print(f"Completed Matches{label}: {c.GREEN}{c.BOLD}{counts['completed']}{c.RESET} / {counts['total']} ({counts['completion_pct']}%)")
        return

    if target in ("pending", "non_completed", "not_completed", "left"):
        label = f" [{filter_label}]" if filter_label else ""
        pending_pct = round(100 - counts["completion_pct"], 1) if counts["total"] > 0 else 0.0
        print(f"Non-Completed (Pending) Matches{label}: {c.YELLOW}{c.BOLD}{counts['pending']}{c.RESET} / {counts['total']} ({pending_pct}%)")
        return

    if target in ("total", "all_matches"):
        label = f" [{filter_label}]" if filter_label else ""
        print(f"Total Matches Scheduled{label}: {c.BOLD}{counts['total']}{c.RESET}")
        return

    # Comprehensive counts card
    print()
    print(f"{c.BOLD}{c.HEADER}======================================================================{c.RESET}")
    print(f"{c.BOLD}{c.HEADER}                  MINARAM CUP — MATCH COUNT SUMMARY                   {c.RESET}")
    print(f"{c.BOLD}{c.HEADER}======================================================================{c.RESET}")
    if filter_label:
        print(f"  {c.CYAN}{c.BOLD}Filter Scope : {filter_label}{c.RESET}\n")

    tot = counts["total"]
    comp = counts["completed"]
    pend = counts["pending"]
    pct = counts["completion_pct"]
    pend_pct = round(100 - pct, 1) if tot > 0 else 0.0

    print(f"  • Total Matches Scheduled       : {c.BOLD}{tot:3d}{c.RESET}")
    print(f"  • Completed Matches             : {c.GREEN}{c.BOLD}{comp:3d}{c.RESET}  ({pct:5.1f}%)")
    print(f"  • Non-Completed (Pending)       : {c.YELLOW}{c.BOLD}{pend:3d}{c.RESET}  ({pend_pct:5.1f}%)")
    print(f"  • Progress Tracker              : {c.GREEN}{format_progress_bar(comp, tot, 25)}{c.RESET}")

    # Status counts
    if counts["status_counts"]:
        print(f"\n  {c.BOLD}Status Breakdown:{c.RESET}")
        for s_name, s_num in counts["status_counts"].items():
            col = c.GREEN if s_name in ("Completed", "Walkover") else c.YELLOW
            print(f"    - {s_name:<16}: {col}{s_num:>3d}{c.RESET}")

    # Stage counts
    if counts["stage_counts"] and (len(counts["stage_counts"]) > 1 or not filter_label):
        print(f"\n  {c.BOLD}Stage Counts:{c.RESET}")
        for st, sdata in sorted(counts["stage_counts"].items()):
            col = c.GREEN if sdata["pending"] == 0 and sdata["total"] > 0 else (c.YELLOW if sdata["completed"] > 0 else c.DIM)
            print(f"    - {st:<18}: {col}{sdata['completed']:>2d} completed{c.RESET} / {sdata['total']:>2d} total ({sdata['pending']:>2d} pending)")

    # Group counts
    if counts["group_counts"] and (len(counts["group_counts"]) > 1 or not filter_label):
        print(f"\n  {c.BOLD}Group Counts (Completed / Total):{c.RESET}")
        items = sorted(counts["group_counts"].items())
        for i in range(0, len(items), 3):
            chunk = items[i:i+3]
            line_parts = []
            for grp, gdata in chunk:
                if gdata["pending"] == 0 and gdata["total"] > 0:
                    badge = f"{c.GREEN}{gdata['completed']}/{gdata['total']} (Done){c.RESET}"
                else:
                    badge = f"{c.YELLOW}{gdata['completed']}/{gdata['total']} ({gdata['pending']} left){c.RESET}"
                line_parts.append(f"{grp}: {badge}".ljust(35))
            print("    " + "".join(line_parts).strip())

    print(f"{c.BOLD}{c.HEADER}======================================================================{c.RESET}\n")


def print_dashboard(checker: MatchChecker) -> None:
    """Print the complete, visually rich terminal summary dashboard."""
    stats = checker.get_summary_stats()
    c = Colors

    total = stats["total_matches"]
    completed = stats["completed_matches"]
    not_completed = stats["not_completed_matches"]
    pct = stats["completion_percentage"]
    bar = format_progress_bar(completed, total, width=28)

    print()
    print(f"{c.BOLD}{c.HEADER}======================================================================{c.RESET}")
    print(f"{c.BOLD}{c.HEADER}           MINARAM CUP — MATCH PROGRESS & ANALYTICS DASHBOARD         {c.RESET}")
    print(f"{c.BOLD}{c.HEADER}======================================================================{c.RESET}")
    print(f"{c.DIM}Data Source: {stats['source']} | Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}{c.RESET}\n")

    # 1. Main Stats Box
    print(f"{c.BOLD}{c.CYAN}[1] OVERALL MATCH COMPLETION STATUS{c.RESET}")
    print(f"  {'-' * 66}")
    print(f"  • Total Matches Scheduled : {c.BOLD}{total:3d}{c.RESET}")
    print(f"  • Completed Matches        : {c.GREEN}{c.BOLD}{completed:3d}{c.RESET}  ({pct:5.1f}%)")
    print(f"  • Not Completed (Pending)  : {c.YELLOW}{c.BOLD}{not_completed:3d}{c.RESET}  ({(100 - pct):5.1f}%)")
    print(f"  • Progress Tracker         : {c.GREEN}{bar}{c.RESET}")
    print(f"  {'-' * 66}")

    # Status Breakdown
    statuses = stats["status_breakdown"]
    status_str_list = []
    for s_name, s_count in statuses.items():
        color = c.GREEN if s_name in ("Completed", "Walkover") else c.YELLOW
        status_str_list.append(f"{s_name}: {color}{s_count}{c.RESET}")
    print(f"  Status Details: {' | '.join(status_str_list)}\n")

    # 2. Stage Breakdown
    print(f"{c.BOLD}{c.CYAN}[2] STAGE-BY-STAGE PROGRESSION{c.RESET}")
    print(f"  {'-' * 66}")
    print(f"  {'Stage':<20} {'Total':>8} {'Completed':>12} {'Pending':>10} {'Progress':>12}")
    print(f"  {'-' * 20} {'-' * 8} {'-' * 12} {'-' * 10} {'-' * 12}")
    for stage, sdata in sorted(stats["stage_breakdown"].items()):
        prog = f"{sdata['pct']:.1f}%"
        color = c.GREEN if sdata["pending"] == 0 and sdata["total"] > 0 else (c.YELLOW if sdata["completed"] > 0 else c.DIM)
        print(f"  {stage:<20} {sdata['total']:>8} {color}{sdata['completed']:>12}{c.RESET} {sdata['pending']:>10} {color}{prog:>12}{c.RESET}")
    print(f"  {'-' * 66}\n")

    # 3. Group Stage Matrix
    group_stats = stats["group_breakdown"]
    if group_stats:
        finished_grps = stats["groups_completed_count"]
        total_grps = stats["groups_total"]
        print(f"{c.BOLD}{c.CYAN}[3] GROUP STAGE BREAKDOWN ({finished_grps}/{total_grps} Groups Fully Finished){c.RESET}")
        print(f"  {'-' * 66}")
        print(f"  {'Group':<14} {'Total':>8} {'Done':>8} {'Left':>8}   {'Status'}")
        print(f"  {'-' * 14} {'-' * 8} {'-' * 8} {'-' * 8}   {'-' * 20}")
        for grp, gdata in sorted(group_stats.items()):
            if gdata["all_done"]:
                state_badge = f"{c.GREEN}[COMPLETED]{c.RESET}"
            elif gdata["completed"] > 0:
                state_badge = f"{c.YELLOW}[IN PROGRESS - {gdata['completed']}/{gdata['total']}]{c.RESET}"
            else:
                state_badge = f"{c.DIM}[NOT STARTED]{c.RESET}"
            print(f"  {grp:<14} {gdata['total']:>8} {gdata['completed']:>8} {gdata['pending']:>8}   {state_badge}")
        print(f"  {'-' * 66}\n")

    # 4. Tournament Scoring & Match Dynamics
    g = stats["goals"]
    print(f"{c.BOLD}{c.CYAN}[4] GOAL & MATCH ANALYTICS (Completed Matches){c.RESET}")
    print(f"  {'-' * 66}")
    print(f"  • Total Goals Scored       : {c.BOLD}{g['total_goals']}{c.RESET} goals across {completed} matches")
    print(f"  • Average Goals per Match  : {c.BOLD}{g['average_goals_per_match']:.2f}{c.RESET} goals/game")
    print(f"  • Match Outcomes           : Home Wins: {c.GREEN}{g['home_wins']}{c.RESET} | Away Wins: {c.GREEN}{g['away_wins']}{c.RESET} | Draws: {c.YELLOW}{g['draws']}{c.RESET}")
    print(f"  • Penalty Shootouts        : {c.BOLD}{g['penalty_shootouts']}{c.RESET}")
    print(f"  • Clean Sheets Recorded    : {c.BOLD}{g['clean_sheets']}{c.RESET}")

    if g["highest_scoring_match"]:
        m = g["highest_scoring_match"]
        score = f"{m['home_score']} - {m['away_score']}"
        print(f"  • Highest Scoring Thriller : Match #{m['match_number']} ({m['home_team']} {score} {m['away_team']}) — {m['home_score'] + m['away_score']} total goals")

    if g["biggest_blowout"]:
        m = g["biggest_blowout"]
        score = f"{m['home_score']} - {m['away_score']}"
        margin = abs(m["home_score"] - m["away_score"])
        winner = m["winner_team"] or (m["home_team"] if m["home_score"] > m["away_score"] else m["away_team"])
        print(f"  • Largest Margin Victory   : Match #{m['match_number']} ({m['home_team']} {score} {m['away_team']}) — {winner} by {margin} goals")
    print(f"  {'-' * 66}\n")

    # 5. Top Attacking Teams & Best Defense
    if stats["top_scorers"] or stats["best_defense"]:
        print(f"{c.BOLD}{c.CYAN}[5] TEAM PERFORMANCE LEADERS{c.RESET}")
        print(f"  {'-' * 66}")
        print(f"  {c.BOLD}Top Scoring Attacks:{c.RESET}")
        for idx, t in enumerate(stats["top_scorers"][:4], start=1):
            print(f"    {idx}. {t['team']:<24} {c.GREEN}{t['goals']:>2} goals{c.RESET} in {t['matches']} matches ({t['avg']} /game)")
        print()
        print(f"  {c.BOLD}Top Defensive Walls (Fewest Goals Conceded):{c.RESET}")
        for idx, t in enumerate(stats["best_defense"][:4], start=1):
            print(f"    {idx}. {t['team']:<24} {c.CYAN}{t['conceded']:>2} conceded{c.RESET} in {t['matches']} matches ({t['avg']} /game, {t['clean_sheets']} clean sheets)")
        print(f"  {'-' * 66}\n")

    # 6. Next Upcoming Matches Preview
    pending_preview = checker.get_pending_matches(limit=5)
    if pending_preview:
        print(f"{c.BOLD}{c.CYAN}[6] NEXT PENDING FIXTURES TO BE PLAYED{c.RESET}")
        print(f"  {'-' * 66}")
        for m in pending_preview:
            grp_info = f"({m['group_name']})" if m["group_name"] else f"({m['stage']})"
            date_info = m["scheduled_date"] or "Flexible / TBD"
            print(f"  • Match #{m['match_number']:>2} {grp_info:<12} : {c.BOLD}{m['home_team']}{c.RESET} vs {c.BOLD}{m['away_team']}{c.RESET} | {c.DIM}{date_info} @ {m['venue'] or 'Main Pitch'}{c.RESET}")
        if not_completed > 5:
            print(f"  {c.DIM}... and {not_completed - 5} more pending matches. Use --pending to view all.{c.RESET}")
        print(f"  {'-' * 66}\n")

    print(f"{c.BOLD}💡 Tip:{c.RESET} Use {c.CYAN}py check_matches.py --pending{c.RESET} to inspect all pending games,")
    print(f"        or {c.CYAN}py check_matches.py --export json{c.RESET} to export complete data.\n")


def print_remaining_group_matches(checker: MatchChecker, show_table: bool = True, raw: bool = False) -> None:
    """Display comprehensive report on remaining group stage matches."""
    c = Colors
    group_matches = [m for m in checker.matches if (m["stage"] or "").lower() == "group stage" or m["group_name"]]
    remaining = [m for m in group_matches if not m["is_completed"]]
    completed = [m for m in group_matches if m["is_completed"]]
    total = len(group_matches)
    rem_count = len(remaining)
    comp_count = len(completed)
    pct = (comp_count / total * 100) if total > 0 else 0.0

    if raw:
        print(rem_count)
        return

    # Group counts
    group_tally = defaultdict(lambda: {"total": 0, "completed": 0, "remaining": 0})
    for m in group_matches:
        grp = m["group_name"] or "Unknown"
        group_tally[grp]["total"] += 1
        if m["is_completed"]:
            group_tally[grp]["completed"] += 1
        else:
            group_tally[grp]["remaining"] += 1

    finished_groups = [g for g, d in sorted(group_tally.items()) if d["remaining"] == 0 and d["total"] > 0]
    active_groups = [(g, d) for g, d in sorted(group_tally.items(), key=lambda x: (-x[1]["remaining"], x[0])) if d["remaining"] > 0]

    print()
    print(f"{c.BOLD}{c.HEADER}======================================================================{c.RESET}")
    print(f"{c.BOLD}{c.HEADER}            MINARAM CUP — REMAINING GROUP STAGE MATCHES               {c.RESET}")
    print(f"{c.BOLD}{c.HEADER}======================================================================{c.RESET}")
    print(f"  • {c.YELLOW}{c.BOLD}Remaining Group Matches : {rem_count}{c.RESET} matches left to be played (out of {total})")
    print(f"  • Group Stage Progress    : {c.GREEN}{comp_count} completed ({pct:.1f}%){c.RESET} | {c.YELLOW}{rem_count} pending ({100-pct:.1f}%){c.RESET}")
    print(f"  • Progress Tracker        : {c.GREEN}{format_progress_bar(comp_count, total, 28)}{c.RESET}")
    print(f"  • Finished Groups ({len(finished_groups)}/{len(group_tally)}) : {c.GREEN}{', '.join(finished_groups) if finished_groups else 'None'}{c.RESET}")
    print(f"  • Active Groups ({len(active_groups)}/{len(group_tally)})   : {len(active_groups)} groups still have pending matches")
    print(f"  {'-' * 66}")
    print(f"  {c.BOLD}Remaining Matches by Group (Highest to Lowest):{c.RESET}")

    for grp, d in active_groups:
        bar = f"{d['completed']}/{d['total']}"
        print(f"    • {c.BOLD}{grp:<12}{c.RESET}: {c.YELLOW}{c.BOLD}{d['remaining']:>2} remaining{c.RESET}  ({bar} completed)")

    print(f"  {'-' * 66}")

    if show_table and remaining:
        print_matches_table(remaining, f"REMAINING GROUP STAGE FIXTURES ({rem_count} MATCHES)")
    else:
        print()


def print_matches_table(matches: List[Dict[str, Any]], title: str) -> None:
    """Print an aligned table of matches."""
    c = Colors
    print()
    print(f"{c.BOLD}{c.HEADER}=== {title} ({len(matches)} matches) ==={c.RESET}")
    print(f"{'-' * 95}")
    print(f"{'#':<4} {'Stage / Group':<18} {'Home Team':<22} {'Score / Status':<18} {'Away Team':<22} {'Date / Window':<12}")
    print(f"{'-' * 4} {'-' * 18} {'-' * 22} {'-' * 18} {'-' * 22} {'-' * 12}")

    for m in matches:
        num = str(m["match_number"])
        stage_grp = m["group_name"] if m["group_name"] else m["stage"]

        if m["is_completed"]:
            score_txt = f"{m['home_score']} - {m['away_score']}"
            if m.get("home_penalty") is not None and m.get("away_penalty") is not None:
                score_txt += f" ({m['home_penalty']}-{m['away_penalty']}p)"
            status_display = f"{c.GREEN}{score_txt}{c.RESET}"
        else:
            status_display = f"{c.YELLOW}{m['status']}{c.RESET}"

        date_val = m["scheduled_date"][:10] if m["scheduled_date"] else "TBD"
        print(f"{num:<4} {stage_grp:<18} {m['home_team']:<22} {status_display:<27} {m['away_team']:<22} {date_val:<12}")

    print(f"{'-' * 95}\n")


def export_report(checker: MatchChecker, format_type: str, output_path: Optional[str] = None) -> Path:
    """Export summary data to JSON, Markdown, or CSV."""
    stats = checker.get_summary_stats()
    format_type = format_type.lower().strip()

    if format_type == "json":
        out = Path(output_path) if output_path else ROOT_DIR / "match_report.json"
        with open(out, "w", encoding="utf-8") as f:
            json.dump(stats, f, indent=2, default=str)
        return out

    elif format_type in ("md", "markdown"):
        out = Path(output_path) if output_path else ROOT_DIR / "MATCH_REPORT.md"
        with open(out, "w", encoding="utf-8") as f:
            f.write(f"# Minaram Cup — Match Progress Report\n\n")
            f.write(f"- **Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"- **Data Source:** {stats['source']}\n\n")

            f.write(f"## 1. Overall Completion Summary\n\n")
            f.write(f"| Metric | Value | Percentage |\n")
            f.write(f"|---|---|---|\n")
            f.write(f"| **Total Matches** | {stats['total_matches']} | 100.0% |\n")
            f.write(f"| **Completed Matches** | {stats['completed_matches']} | {stats['completion_percentage']}% |\n")
            f.write(f"| **Not Completed (Pending)** | {stats['not_completed_matches']} | {round(100 - stats['completion_percentage'], 1)}% |\n\n")

            f.write(f"## 2. Stage Breakdown\n\n")
            f.write(f"| Stage | Total | Completed | Pending | % Completed |\n")
            f.write(f"|---|---|---|---|---|\n")
            for st, data in sorted(stats["stage_breakdown"].items()):
                f.write(f"| {st} | {data['total']} | {data['completed']} | {data['pending']} | {data['pct']:.1f}% |\n")
            f.write("\n")

            f.write(f"## 3. Group Breakdown\n\n")
            f.write(f"| Group | Total | Completed | Pending | Status |\n")
            f.write(f"|---|---|---|---|---|\n")
            for grp, data in sorted(stats["group_breakdown"].items()):
                status = "Completed" if data["all_done"] else ("In Progress" if data["completed"] > 0 else "Not Started")
                f.write(f"| {grp} | {data['total']} | {data['completed']} | {data['pending']} | {status} |\n")
            f.write("\n")

            f.write(f"## 4. Scoring Statistics\n\n")
            g = stats["goals"]
            f.write(f"- **Total Goals:** {g['total_goals']}\n")
            f.write(f"- **Average Goals per Match:** {g['average_goals_per_match']:.2f}\n")
            f.write(f"- **Home Wins:** {g['home_wins']} | **Away Wins:** {g['away_wins']} | **Draws:** {g['draws']}\n")
            f.write(f"- **Clean Sheets:** {g['clean_sheets']}\n")
        return out

    elif format_type == "csv":
        out = Path(output_path) if output_path else ROOT_DIR / "match_status_export.csv"
        fieldnames = [
            "match_number", "stage", "group_name", "home_team", "away_team",
            "home_score", "away_score", "status", "winner_team", "scheduled_date", "venue"
        ]
        with open(out, "w", newline="", encoding="utf-8-sig") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
            writer.writeheader()
            for m in checker.matches:
                writer.writerow(m)
        return out

    else:
        raise ValueError(f"Unsupported export format '{format_type}'. Use json, md, or csv.")


# -----------------------------------------------------------------------------
# Interactive Mode
# -----------------------------------------------------------------------------
def run_interactive(checker: MatchChecker) -> None:
    """Terminal interactive menu for effortless navigation."""
    c = Colors
    while True:
        print()
        print(f"{c.BOLD}{c.HEADER}--- MINARAM CUP MATCH CHECKER INTERACTIVE MENU ---{c.RESET}")
        print("1. View Full Dashboard Summary")
        print("2. View Match Counts (Total, Completed, Non-Completed, by Stage/Group)")
        print("3. Check Remaining Group Matches (Count & Pending Fixtures)")
        print("4. List All Pending / Not Completed Matches")
        print("5. List All Completed Matches")
        print("6. Filter Matches by Group (e.g. Group A)")
        print("7. Search Matches by Team Name")
        print("8. Export Report (JSON / Markdown / CSV)")
        print("0. Exit")
        choice = input(f"{c.CYAN}Select an option (0-8): {c.RESET}").strip()

        if choice == "1":
            print_dashboard(checker)
        elif choice == "2":
            counts = checker.compute_counts()
            print_counts(counts)
        elif choice == "3":
            print_remaining_group_matches(checker)
        elif choice == "4":
            pending = checker.get_pending_matches()
            print_matches_table(pending, "PENDING / NOT COMPLETED MATCHES")
        elif choice == "5":
            completed = checker.get_completed_matches()
            print_matches_table(completed, "COMPLETED MATCHES")
        elif choice == "6":
            grp = input("Enter Group Name (e.g. Group A): ").strip()
            if grp:
                m_list = checker.filter_by_group(grp)
                counts_yn = input("Show quick count only? (y/N): ").strip().lower()
                if counts_yn == "y":
                    c_data = checker.compute_counts(m_list)
                    print_counts(c_data, filter_label=f"Group: {grp.upper()}")
                else:
                    print_matches_table(m_list, f"MATCHES IN {grp.upper()}")
        elif choice == "7":
            team = input("Enter Team Name to search: ").strip()
            if team:
                m_list = checker.filter_by_team(team)
                counts_yn = input("Show quick count only? (y/N): ").strip().lower()
                if counts_yn == "y":
                    c_data = checker.compute_counts(m_list)
                    print_counts(c_data, filter_label=f"Team: {team}")
                else:
                    print_matches_table(m_list, f"MATCHES FOR '{team}'")
        elif choice == "8":
            fmt = input("Enter export format (json / md / csv) [json]: ").strip() or "json"
            try:
                out = export_report(checker, fmt)
                print(f"{c.GREEN}Successfully exported report to: {out}{c.RESET}")
            except Exception as e:
                print(f"{c.RED}Export failed: {e}{c.RESET}")
        elif choice in ("0", "q", "exit"):
            print("Goodbye!")
            break
        else:
            print(f"{c.YELLOW}Invalid selection. Please try again.{c.RESET}")


# -----------------------------------------------------------------------------
# CLI Entrypoint
# -----------------------------------------------------------------------------
def main():
    parser = argparse.ArgumentParser(
        description="Minaram Cup — Check Total Completed & Pending Matches, Stage Analytics, and Tournament Stats."
    )
    parser.add_argument(
        "--source", "-s",
        type=str,
        default=None,
        help="Custom path to SQLite database (.db) or fixtures CSV (.csv)."
    )
    parser.add_argument(
        "--remaining-group-matches", "--remaining-groups", "--group-remaining",
        dest="remaining_groups",
        action="store_true",
        help="Check how many group matches are remaining with a detailed breakdown and pending fixtures list."
    )
    parser.add_argument(
        "--count", "--counts", "-C",
        dest="count",
        nargs="?",
        const="all",
        default=None,
        choices=["all", "completed", "pending", "non_completed", "not_completed", "total", "stages", "groups"],
        help="Get count of matches: 'all', 'completed', 'pending' (non-completed), 'total', 'stages', or 'groups'."
    )
    parser.add_argument(
        "--count-completed",
        action="store_true",
        help="Quick shortcut: get the count of completed matches."
    )
    parser.add_argument(
        "--count-pending", "--count-not-completed", "--count-non-completed",
        dest="count_pending",
        action="store_true",
        help="Quick shortcut: get the count of non-completed / pending matches."
    )
    parser.add_argument(
        "--count-total",
        action="store_true",
        help="Quick shortcut: get the total count of matches."
    )
    parser.add_argument(
        "--raw", "-q", "--quiet",
        action="store_true",
        help="Print raw number only without extra text/formatting (ideal for shell scripts or piping)."
    )
    parser.add_argument(
        "--pending", "-p",
        action="store_true",
        help="List all pending / uncompleted matches in a table."
    )
    parser.add_argument(
        "--completed", "-c",
        action="store_true",
        help="List all completed matches with results and scores in a table."
    )
    parser.add_argument(
        "--group", "-g",
        type=str,
        default=None,
        help="Filter matches by Group name (e.g. 'Group A')."
    )
    parser.add_argument(
        "--stage",
        type=str,
        default=None,
        help="Filter matches by Stage (e.g. 'Group Stage', 'Quarter-Final', 'Final')."
    )
    parser.add_argument(
        "--team", "-t",
        type=str,
        default=None,
        help="Filter fixtures and results for a specific team name."
    )
    parser.add_argument(
        "--export", "-e",
        type=str,
        choices=["json", "md", "csv"],
        default=None,
        help="Export comprehensive statistics to json, md, or csv."
    )
    parser.add_argument(
        "--interactive", "-i",
        action="store_true",
        help="Open interactive command-line navigation menu."
    )
    parser.add_argument(
        "--no-color",
        action="store_true",
        help="Disable ANSI terminal colors."
    )

    args = parser.parse_args()

    # Disable colors if requested or redirected
    if args.no_color or not sys.stdout.isatty():
        Colors.disable()

    # Initialize checker
    custom_src = Path(args.source) if args.source else None
    try:
        checker = MatchChecker(source_path=custom_src)
    except Exception as e:
        print(f"Error loading tournament match data: {e}", file=sys.stderr)
        sys.exit(1)

    # Handle interactive mode
    if args.interactive:
        run_interactive(checker)
        return

    # Check if remaining group matches requested
    if args.remaining_groups:
        print_remaining_group_matches(checker, show_table=not args.raw, raw=args.raw)
        return

    # Check if count was requested
    count_target = None
    if args.count:
        count_target = args.count
    elif args.count_completed:
        count_target = "completed"
    elif args.count_pending:
        count_target = "pending"
    elif args.count_total:
        count_target = "total"

    if count_target:
        matches_subset = None
        filter_label = None

        if args.group:
            matches_subset = checker.filter_by_group(args.group)
            filter_label = f"Group: {args.group.upper()}"
        elif args.stage:
            matches_subset = checker.filter_by_stage(args.stage)
            filter_label = f"Stage: {args.stage.upper()}"
        elif args.team:
            matches_subset = checker.filter_by_team(args.team)
            filter_label = f"Team: {args.team}"

        counts = checker.compute_counts(matches_subset)
        print_counts(counts, target=count_target, filter_label=filter_label, raw=args.raw)
        return

    # Handle filters
    if args.pending:
        pending = checker.get_pending_matches()
        print_matches_table(pending, "PENDING / NOT COMPLETED MATCHES")
        return

    if args.completed:
        completed = checker.get_completed_matches()
        print_matches_table(completed, "COMPLETED MATCHES")
        return

    if args.group:
        matches = checker.filter_by_group(args.group)
        print_matches_table(matches, f"MATCHES FOR {args.group.upper()}")
        return

    if args.stage:
        matches = checker.filter_by_stage(args.stage)
        print_matches_table(matches, f"MATCHES FOR STAGE: {args.stage.upper()}")
        return

    if args.team:
        matches = checker.filter_by_team(args.team)
        print_matches_table(matches, f"MATCHES FOR TEAM: '{args.team}'")
        return

    # Handle export
    if args.export:
        out_file = export_report(checker, args.export)
        print(f"{Colors.GREEN}Report exported successfully to:{Colors.RESET} {out_file}")
        return

    # Default action: Full Dashboard
    print_dashboard(checker)


if __name__ == "__main__":
    main()

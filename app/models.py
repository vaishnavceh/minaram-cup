"""
Domain models and dataclasses for Minaram Cup Tournament Management System.
"""

from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any
from datetime import datetime


@dataclass
class Registration:
    id: Optional[int] = None
    participant_name: str = ""
    phone_number: str = ""
    team_name: str = ""
    raw_message: str = ""
    registered_at: str = field(default_factory=lambda: datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    status: str = "Pending"  # Pending, Confirmed, Rejected, Duplicate
    notes: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "participant_name": self.participant_name,
            "phone_number": self.phone_number,
            "team_name": self.team_name,
            "raw_message": self.raw_message,
            "registered_at": self.registered_at,
            "status": self.status,
            "notes": self.notes,
        }


@dataclass
class ParsedRegistration:
    name: str = ""
    phone: str = ""
    team: str = ""
    raw_text: str = ""
    is_valid: bool = False
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)


@dataclass
class Team:
    id: Optional[int] = None
    name: str = ""
    captain_name: str = ""
    phone_number: str = ""
    status: str = "Confirmed"  # Confirmed, Pending, Withdrawn
    group_id: Optional[int] = None
    group_name: Optional[str] = None
    seed: int = 0
    logo_path: str = ""
    notes: str = ""
    created_at: str = field(default_factory=lambda: datetime.now().strftime("%Y-%m-%d %H:%M:%S"))

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "captain_name": self.captain_name,
            "phone_number": self.phone_number,
            "status": self.status,
            "group_id": self.group_id,
            "group_name": self.group_name,
            "seed": self.seed,
            "logo_path": self.logo_path,
            "notes": self.notes,
            "created_at": self.created_at,
        }


@dataclass
class Group:
    id: Optional[int] = None
    name: str = ""
    display_order: int = 0
    teams_count: int = 0


@dataclass
class Match:
    id: Optional[int] = None
    match_number: int = 1
    stage: str = "Group Stage"  # Group Stage, League, Round of 16, Quarter-Final, Semi-Final, Final, Third Place
    group_id: Optional[int] = None
    group_name: Optional[str] = None
    round_number: int = 1
    bracket_slot: str = ""  # e.g., 'QF1', 'QF2', 'SF1', 'F'
    home_team_id: Optional[int] = None
    away_team_id: Optional[int] = None
    home_team_name: str = "TBD"
    away_team_name: str = "TBD"
    home_captain: str = ""
    home_phone: str = ""
    away_captain: str = ""
    away_phone: str = ""
    scheduled_date: str = ""
    scheduled_time: str = ""
    venue: str = "Main Pitch"
    home_score: Optional[int] = None
    away_score: Optional[int] = None
    home_penalty: Optional[int] = None
    away_penalty: Optional[int] = None
    status: str = "Scheduled"  # Scheduled, In Progress, Completed, Postponed, Cancelled, Walkover
    winner_team_id: Optional[int] = None
    winner_team_name: Optional[str] = None
    notes: str = ""
    completed_at: str = ""

    @property
    def is_completed(self) -> bool:
        return self.status in ("Completed", "Walkover")

    @property
    def score_display(self) -> str:
        if self.home_score is None or self.away_score is None:
            return "vs"
        res = f"{self.home_score} - {self.away_score}"
        if self.home_penalty is not None and self.away_penalty is not None:
            res += f" ({self.home_penalty}-{self.away_penalty} pen)"
        return res


@dataclass
class MatchAudit:
    id: Optional[int] = None
    match_id: int = 0
    timestamp: str = ""
    action: str = ""
    old_home_score: Optional[int] = None
    old_away_score: Optional[int] = None
    old_status: str = ""
    new_home_score: Optional[int] = None
    new_away_score: Optional[int] = None
    new_status: str = ""
    notes: str = ""


@dataclass
class StandingRow:
    team_id: int
    team_name: str
    group_id: Optional[int] = None
    group_name: Optional[str] = None
    played: int = 0
    won: int = 0
    drawn: int = 0
    lost: int = 0
    goals_for: int = 0
    goals_against: int = 0
    goal_difference: int = 0
    points: int = 0
    form: List[str] = field(default_factory=list)  # e.g. ['W', 'D', 'W']
    is_qualified: bool = False
    rank: int = 1
    has_override: bool = False
    override_notes: str = ""


@dataclass
class TournamentSettings:
    tournament_name: str = "Minaram Cup"
    edition: str = "2026 Edition"
    sport: str = "Football"
    format_type: str = "Group Stage + Knockout"  # "League", "Group Stage + Knockout", "Knockout", "Custom"
    win_points: int = 3
    draw_points: int = 1
    loss_points: int = 0
    num_groups: int = 2
    qualifiers_per_group: int = 2
    match_duration_minutes: int = 90
    default_venue: str = "Minaram Stadium"
    tie_breakers: str = "points,goal_difference,goals_for,head_to_head,won"
    theme: str = "dark"

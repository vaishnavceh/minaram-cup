export interface PublicTournament {
  id: number;
  name: string;
  edition: string;
  status: string;
  team_count: number;
  groups_count: number;
  match_count: number;
  completed_matches: number;
  group_stage_completed: boolean;
}

export interface PublicTeam {
  id: number;
  name: string;
  manager_name: string;
  department: string;
  year: string;
  group_name?: string;
  registration_date?: string;
  matches_played: number;
  wins: number;
  draws: number;
  losses: number;
  points: number;
}

export interface TeamDetail extends PublicTeam {
  recent_matches?: PublicMatch[];
}

export interface PublicMatch {
  id: number;
  tournament_id: number;
  stage: string;
  group_name?: string | null;
  round_number?: number | null;
  match_number?: number | null;
  team_a_id?: number | null;
  team_b_id?: number | null;
  team_a_name?: string | null;
  team_b_name?: string | null;
  team_a_captain?: string | null;
  team_a_phone?: string | null;
  team_a_whatsapp?: string | null;
  team_b_captain?: string | null;
  team_b_phone?: string | null;
  team_b_whatsapp?: string | null;
  team_a_score?: number | null;
  team_b_score?: number | null;
  penalty_a?: number | null;
  penalty_b?: number | null;
  status: 'SCHEDULED' | 'IN_PROGRESS' | 'COMPLETED' | 'CANCELLED' | 'PREDICTED' | 'CONFIRMED' | 'LIVE' | 'UNDER REVIEW';
  raw_status?: string | null;
  scheduled_time?: string | null;
  scheduled_date?: string | null;
  start_date?: string | null;
  end_date?: string | null;
  scheduled_end_date?: string | null;
  pitch?: string | null;
  winner_id?: number | null;
  winner_name?: string | null;
  notes?: string | null;
  bracket_slot?: string | null;
  home_group?: string | null;
  away_group?: string | null;
  is_official?: boolean;
  is_published?: boolean;
  winner_method?: string | null;
}

export interface GroupStandingRow {
  team_id: number;
  team_name: string;
  played: number;
  won: number;
  drawn: number;
  lost: number;
  goals_for: number;
  goals_against: number;
  goal_difference: number;
  points: number;
  rank: number;
}

export interface PublicGroupStandings {
  group_name: string;
  standings: GroupStandingRow[];
}

export interface DirectQualifier {
  team_id: number;
  team_name: string;
  group_id: number;
  group_name: string;
  group_position: string;
  rank_in_group: number;
  played: number;
  won: number;
  drawn: number;
  lost: number;
  goals_for: number;
  goals_against: number;
  goal_difference: number;
  points: number;
  points_per_match: number;
  goals_per_match: number;
  is_provisional: boolean;
  criteria_summary: string;
  is_override?: boolean;
  override_reason?: string;
  override_by?: string;
  override_at?: string;
}

export interface KnockoutConflict {
  bracket_slot: string;
  team_id: number;
  team_name: string;
  message: string;
}

export interface KnockoutAuditEntry {
  id: number;
  timestamp: string;
  admin_username: string;
  action: string;
  entity_type: string;
  entity_id: string;
  old_value: string;
  new_value: string;
  reason: string;
}

export interface PublicKnockoutRound {
  round_name: string;
  matches: PublicMatch[];
}

export interface PublicBracket {
  rounds: PublicKnockoutRound[];
  champion?: PublicTeam | null;
  direct_qualifiers?: DirectQualifier[];
  recommended_qualifiers?: DirectQualifier[];
  preliminary_pool?: any[];
  has_direct_override?: boolean;
  snapshot_version?: string;
  last_updated?: string;
  is_provisional?: boolean;
  draw_method?: string;
  conflicts?: KnockoutConflict[];
  rules?: Record<string, string>;
  statuses_legend?: Record<string, string>;
}

export interface AssetManifest {
  version: string;
  generated_at: string;
  logos: Record<string, string>;
  backgrounds: Record<string, string>;
}

export interface LiveEventPayload {
  event: string;
  timestamp: string;
  data: any;
}

export interface TopScorer {
  rank: number;
  team_id: number;
  team_name: string;
  player_name: string;
  group_name: string;
  goals: number;
  matches_played: number;
  goals_per_match: number;
}


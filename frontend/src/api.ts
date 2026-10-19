import {
  PublicTournament,
  PublicTeam,
  TeamDetail,
  PublicMatch,
  PublicGroupStandings,
  PublicBracket,
  AssetManifest,
  TopScorer,
} from './types';
import { makeWhatsAppLink } from './utils/whatsapp';

const RAW_BASE = (import.meta.env.VITE_API_URL as string) || '';
const API_BASE = RAW_BASE ? `${RAW_BASE.replace(/\/+$/, '')}/api` : '/api';

async function handleResponse<T>(res: Response): Promise<T> {
  if (!res.ok) {
    const errorText = await res.text();
    let msg = `HTTP ${res.status}: ${res.statusText}`;
    try {
      const parsed = JSON.parse(errorText);
      if (parsed.detail) msg = parsed.detail;
    } catch {
      if (errorText) msg = errorText;
    }
    throw new Error(msg);
  }
  return res.json() as Promise<T>;
}

export function normalizeMatch(m: any): PublicMatch {
  if (!m) return {} as PublicMatch;
  const homeScore = m.home_score !== undefined ? m.home_score : m.team_a_score;
  const awayScore = m.away_score !== undefined ? m.away_score : m.team_b_score;
  const rawStatus = (m.status || 'SCHEDULED').toUpperCase();
  let status: any = 'SCHEDULED';
  if (rawStatus === 'COMPLETED' || rawStatus === 'WALKOVER') {
    status = 'COMPLETED';
  } else if (rawStatus === 'LIVE' || rawStatus === 'IN_PROGRESS' || rawStatus === 'IN PROGRESS') {
    status = 'LIVE';
  } else if (rawStatus === 'UNDER REVIEW' || rawStatus === 'UNDER_REVIEW') {
    status = 'UNDER REVIEW';
  } else if (rawStatus === 'CONFIRMED') {
    status = 'CONFIRMED';
  } else if (rawStatus === 'PREDICTED') {
    status = 'PREDICTED';
  }

  const date = m.scheduled_date || m.date || m.start_date || '';
  const endDate = m.scheduled_end_date || m.end_date || '';
  const time = m.scheduled_time || m.time || '';
  const sched = date && time ? `${date} · ${time}` : date || time || 'Scheduled';

  return {
    id: m.id || m.match_id || 0,
    tournament_id: m.tournament_id || 1,
    stage: m.stage || 'Group Stage',
    group_name: m.group_name || null,
    round_number: m.round_number || null,
    match_number: m.match_number || null,
    team_a_id: m.home_team_id ?? m.team_a_id ?? null,
    team_b_id: m.away_team_id ?? m.team_b_id ?? null,
    team_a_name: !m.home_team_name && !m.team_a_name ? 'Yet to decide' : (m.home_team_name === 'TBD' || m.team_a_name === 'TBD' ? 'Yet to decide' : (m.home_team_name ?? m.team_a_name ?? m.opponent_a ?? (m.is_home ? m.name : m.opponent) ?? 'Yet to decide')),
    team_b_name: !m.away_team_name && !m.team_b_name ? 'Yet to decide' : (m.away_team_name === 'TBD' || m.team_b_name === 'TBD' ? 'Yet to decide' : (m.away_team_name ?? m.team_b_name ?? m.opponent_b ?? (!m.is_home ? m.name : m.opponent) ?? 'Yet to decide')),
    team_a_captain: m.home_captain ?? m.team_a_captain ?? null,
    team_a_phone: m.home_phone ?? m.team_a_phone ?? null,
    team_a_whatsapp: m.home_whatsapp_link || makeWhatsAppLink(m.home_phone ?? m.team_a_phone),
    team_b_captain: m.away_captain ?? m.team_b_captain ?? null,
    team_b_phone: m.away_phone ?? m.team_b_phone ?? null,
    team_b_whatsapp: m.away_whatsapp_link || makeWhatsAppLink(m.away_phone ?? m.team_b_phone),
    team_a_score: homeScore !== undefined && homeScore !== null ? Number(homeScore) : null,
    team_b_score: awayScore !== undefined && awayScore !== null ? Number(awayScore) : null,
    penalty_a: m.home_penalty ?? m.penalty_a ?? null,
    penalty_b: m.away_penalty ?? m.penalty_b ?? null,
    status: status,
    scheduled_time: sched,
    scheduled_date: date || null,
    start_date: date || null,
    end_date: endDate || null,
    scheduled_end_date: endDate || null,
    pitch: m.venue || m.pitch || 'Online / Mobile Lobby',
    winner_id: m.winner_team_id ?? m.winner_id ?? null,
    winner_name: m.winner_team_name ?? m.winner_name ?? null,
    notes: m.notes || null,
    raw_status: m.status || null,
    bracket_slot: m.bracket_slot || null,
    home_group: m.home_group || null,
    away_group: m.away_group || null,
    is_official: Boolean(m.is_official),
    winner_method: m.winner_method || null,
  };
}

export function normalizeTeam(t: any): PublicTeam {
  if (!t) return {} as PublicTeam;
  const stats = t.stats || {};
  return {
    id: t.id || 0,
    name: t.name || 'Unknown Squad',
    manager_name: t.captain_name || t.manager_name || 'Squad Manager',
    department: t.department || 'TKMCE',
    year: t.year ? String(t.year) : '2026',
    registration_date: t.registration_date,
    matches_played: stats.played ?? t.matches_played ?? 0,
    wins: stats.won ?? t.wins ?? 0,
    draws: stats.drawn ?? t.draws ?? 0,
    losses: stats.lost ?? t.losses ?? 0,
    points: stats.points ?? t.points ?? 0,
  };
}

export function normalizeStandings(raw: any): PublicGroupStandings[] {
  if (Array.isArray(raw)) {
    return raw.map((g: any) => ({
      group_name: String(g.group_name || '').replace(/^Group\s*/i, ''),
      standings: Array.isArray(g.standings) ? g.standings : [],
    }));
  }
  if (raw && typeof raw === 'object') {
    return Object.entries(raw).map(([groupName, rows]: [string, any]) => ({
      group_name: groupName.replace(/^Group\s*/i, ''),
      standings: Array.isArray(rows)
        ? rows.map((r: any, idx: number) => ({
            team_id: r.team_id || idx + 1,
            team_name: r.team_name || 'Squad',
            played: r.played ?? 0,
            won: r.won ?? 0,
            drawn: r.drawn ?? 0,
            lost: r.lost ?? 0,
            goals_for: r.goals_for ?? 0,
            goals_against: r.goals_against ?? 0,
            goal_difference: r.goal_difference ?? 0,
            points: r.points ?? 0,
            rank: r.rank ?? idx + 1,
          }))
        : [],
    }));
  }
  return [];
}

export function normalizeBracket(raw: any): PublicBracket {
  if (!raw) return { rounds: [] };
  const baseMeta = {
    champion: raw.champion ? normalizeTeam(raw.champion) : null,
    direct_qualifiers: raw.direct_qualifiers || [],
    recommended_qualifiers: raw.recommended_qualifiers || [],
    has_direct_override: Boolean(raw.has_direct_override),
    snapshot_version: raw.snapshot_version,
    last_updated: raw.last_updated,
    is_provisional: Boolean(raw.is_provisional),
    draw_method: raw.draw_method || 'seeded',
    conflicts: raw.conflicts || [],
    rules: raw.rules || {},
    statuses_legend: raw.statuses_legend || {},
  };

  if (Array.isArray(raw.rounds)) {
    return {
      ...baseMeta,
      rounds: raw.rounds.map((r: any) => ({
        round_name: r.round_name || 'Round',
        matches: Array.isArray(r.matches) ? r.matches.map(normalizeMatch) : [],
      })),
    };
  }
  if (typeof raw === 'object') {
    const rounds = [];
    for (const [stageName, list] of Object.entries(raw)) {
      if (['rounds', 'champion', 'direct_qualifiers', 'recommended_qualifiers', 'has_direct_override', 'snapshot_version', 'last_updated', 'is_provisional', 'draw_method', 'conflicts', 'rules', 'statuses_legend'].includes(stageName)) {
        continue;
      }
      if (Array.isArray(list) && list.length > 0) {
        rounds.push({
          round_name: stageName,
          matches: list.map(normalizeMatch),
        });
      }
    }
    return { ...baseMeta, rounds };
  }
  return { rounds: [] };
}

export const api = {
  // Public Read-Only Endpoints
  async getTournament(): Promise<PublicTournament> {
    const res = await fetch(`${API_BASE}/public/tournament`);
    const raw = await handleResponse<any>(res);
    return {
      id: raw.id || 1,
      name: raw.name || 'Minaram Cup',
      edition: raw.edition || '2026 Edition',
      status: raw.status || (raw.stats?.completed_matches > 0 ? 'IN PROGRESS' : 'GROUP STAGE'),
      team_count: raw.stats?.teams_count ?? raw.team_count ?? 0,
      groups_count: raw.stats?.groups_count ?? raw.groups_count ?? 0,
      match_count: raw.stats?.total_matches ?? raw.match_count ?? 0,
      completed_matches: raw.stats?.completed_matches ?? raw.completed_matches ?? 0,
      group_stage_completed: Boolean(raw.group_stage_completed),
    };
  },

  async getTeams(): Promise<PublicTeam[]> {
    const res = await fetch(`${API_BASE}/public/teams`);
    const list = await handleResponse<any[]>(res);
    return Array.isArray(list) ? list.map(normalizeTeam) : [];
  },

  async getTeamById(id: number): Promise<TeamDetail> {
    const res = await fetch(`${API_BASE}/public/teams/${id}`);
    const raw = await handleResponse<any>(res);
    const team = normalizeTeam(raw);
    const history = Array.isArray(raw.match_history) ? raw.match_history.map(normalizeMatch) : [];
    return {
      ...team,
      recent_matches: history,
    };
  },

  async getStandings(): Promise<PublicGroupStandings[]> {
    const res = await fetch(`${API_BASE}/public/standings`);
    const raw = await handleResponse<any>(res);
    return normalizeStandings(raw);
  },

  async getFixtures(stage?: string, group?: string): Promise<PublicMatch[]> {
    const params = new URLSearchParams();
    if (stage && stage !== 'ALL') params.append('stage', stage);
    if (group && group !== 'ALL') params.append('group', group);
    const query = params.toString() ? `?${params.toString()}` : '';
    const res = await fetch(`${API_BASE}/public/fixtures${query}`);
    const list = await handleResponse<any[]>(res);
    return Array.isArray(list) ? list.map(normalizeMatch) : [];
  },

  async getResults(limit?: number): Promise<PublicMatch[]> {
    const query = limit ? `?limit=${limit}` : '';
    const res = await fetch(`${API_BASE}/public/results${query}`);
    const list = await handleResponse<any[]>(res);
    const matches = Array.isArray(list) ? list.map(normalizeMatch) : [];
    return limit ? matches.slice(0, limit) : matches;
  },

  async getBracket(): Promise<PublicBracket> {
    const res = await fetch(`${API_BASE}/public/bracket`);
    const raw = await handleResponse<any>(res);
    return normalizeBracket(raw);
  },

  async getManifest(): Promise<AssetManifest> {
    const res = await fetch(`${API_BASE}/public/manifest`);
    return handleResponse<AssetManifest>(res);
  },

  async getTopScorers(limit?: number): Promise<TopScorer[]> {
    const query = limit ? `?limit=${limit}` : '';
    const res = await fetch(`${API_BASE}/public/top-scorers${query}`);
    const list = await handleResponse<TopScorer[]>(res);
    return Array.isArray(list) ? list : [];
  },


  // Admin Authentication & Mutation Endpoints (Private)
  async adminLogin(formData: URLSearchParams): Promise<{ access_token: string; token_type: string }> {
    const res = await fetch(`${API_BASE}/admin/auth/token`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/x-www-form-urlencoded',
      },
      body: formData,
    });
    return handleResponse<{ access_token: string; token_type: string }>(res);
  },

  async adminRecordResult(
    matchId: number,
    payload: {
      team_a_score: number;
      team_b_score: number;
      penalty_a?: number;
      penalty_b?: number;
      status?: string;
      walkover_winner_id?: number | null;
      notes?: string;
    },
    token: string
  ): Promise<any> {
    const res = await fetch(`${API_BASE}/admin/matches/${matchId}/result`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        Authorization: `Bearer ${token}`,
      },
      body: JSON.stringify({
        ...payload,
        home_score: payload.team_a_score,
        away_score: payload.team_b_score,
        home_penalty: payload.penalty_a,
        away_penalty: payload.penalty_b,
        status: payload.status || 'Completed',
        walkover_winner_id: payload.walkover_winner_id,
        notes: payload.notes || '',
      }),
    });
    return handleResponse(res);
  },

  async adminResetResult(matchId: number, token: string): Promise<any> {
    const res = await fetch(`${API_BASE}/admin/matches/${matchId}/reset`, {
      method: 'POST',
      headers: {
        Authorization: `Bearer ${token}`,
      },
    });
    return handleResponse(res);
  },

  async adminAdvanceStage(token: string): Promise<any> {
    const res = await fetch(`${API_BASE}/admin/tournament/advance-stage`, {
      method: 'POST',
      headers: {
        Authorization: `Bearer ${token}`,
      },
    });
    return handleResponse(res);
  },

  // ----------------------------------------------------
  // Dynamic Knockout Tournament Methods
  // ----------------------------------------------------
  async getKnockoutBracket(): Promise<PublicBracket> {
    const res = await fetch(`${API_BASE}/public/knockout/bracket`);
    const raw = await handleResponse<any>(res);
    return normalizeBracket(raw);
  },

  async getKnockoutRules(): Promise<Record<string, string>> {
    const res = await fetch(`${API_BASE}/public/knockout/rules`);
    return handleResponse<Record<string, string>>(res);
  },

  async adminRecalculateKnockout(token: string): Promise<any> {
    const res = await fetch(`${API_BASE}/admin/knockout/recalculate`, {
      method: 'POST',
      headers: { Authorization: `Bearer ${token}` },
    });
    return handleResponse(res);
  },

  async adminUpdateDrawConfig(drawMethod: string, token: string): Promise<any> {
    const res = await fetch(`${API_BASE}/admin/knockout/draw-config`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        Authorization: `Bearer ${token}`,
      },
      body: JSON.stringify({ draw_method: drawMethod }),
    });
    return handleResponse(res);
  },

  async adminOverrideDirectQualifier(
    slotIndex: number,
    teamId: number,
    reason: string,
    token: string
  ): Promise<any> {
    const res = await fetch(`${API_BASE}/admin/knockout/direct-qualifiers/override`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        Authorization: `Bearer ${token}`,
      },
      body: JSON.stringify({ slot_index: slotIndex, team_id: teamId, reason }),
    });
    return handleResponse(res);
  },

  async adminClearDirectOverride(token: string): Promise<any> {
    const res = await fetch(`${API_BASE}/admin/knockout/direct-qualifiers/override`, {
      method: 'DELETE',
      headers: { Authorization: `Bearer ${token}` },
    });
    return handleResponse(res);
  },

  async adminConfirmFixture(slot: string, token: string): Promise<any> {
    const res = await fetch(`${API_BASE}/admin/knockout/fixtures/${slot}/confirm`, {
      method: 'POST',
      headers: { Authorization: `Bearer ${token}` },
    });
    return handleResponse(res);
  },

  async adminBatchConfirmStage(stage: string, token: string): Promise<any> {
    const res = await fetch(`${API_BASE}/admin/knockout/fixtures/batch-confirm`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        Authorization: `Bearer ${token}`,
      },
      body: JSON.stringify({ stage }),
    });
    return handleResponse(res);
  },

  async adminUnconfirmFixture(slot: string, token: string): Promise<any> {
    const res = await fetch(`${API_BASE}/admin/knockout/fixtures/${slot}/unconfirm`, {
      method: 'POST',
      headers: { Authorization: `Bearer ${token}` },
    });
    return handleResponse(res);
  },

  async adminEditFixture(
    slot: string,
    payload: {
      home_team_id?: number | null;
      away_team_id?: number | null;
      scheduled_date?: string;
      scheduled_time?: string;
      venue?: string;
      notes?: string;
    },
    token: string
  ): Promise<any> {
    const res = await fetch(`${API_BASE}/admin/knockout/fixtures/${slot}`, {
      method: 'PUT',
      headers: {
        'Content-Type': 'application/json',
        Authorization: `Bearer ${token}`,
      },
      body: JSON.stringify(payload),
    });
    return handleResponse(res);
  },

  async adminRecordKnockoutResult(
    slot: string,
    payload: {
      home_score: number;
      away_score: number;
      home_penalty?: number | null;
      away_penalty?: number | null;
      winner_team_id?: number | null;
      winner_method?: string;
      notes?: string;
    },
    token: string
  ): Promise<any> {
    const res = await fetch(`${API_BASE}/admin/knockout/fixtures/${slot}/result`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        Authorization: `Bearer ${token}`,
      },
      body: JSON.stringify(payload),
    });
    return handleResponse(res);
  },

  async adminSetFixtureStatus(
    slot: string,
    status: string,
    notes: string,
    token: string
  ): Promise<any> {
    const res = await fetch(`${API_BASE}/admin/knockout/fixtures/${slot}/status`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        Authorization: `Bearer ${token}`,
      },
      body: JSON.stringify({ status, notes }),
    });
    return handleResponse(res);
  },

  async adminRecordWalkover(
    slot: string,
    winnerTeamId: number,
    reason: string,
    token: string
  ): Promise<any> {
    const res = await fetch(`${API_BASE}/admin/knockout/fixtures/${slot}/walkover`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        Authorization: `Bearer ${token}`,
      },
      body: JSON.stringify({ winner_team_id: winnerTeamId, reason }),
    });
    return handleResponse(res);
  },

  async adminUpdateRule(key: string, value: string, token: string): Promise<any> {
    const res = await fetch(`${API_BASE}/admin/knockout/rules`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        Authorization: `Bearer ${token}`,
      },
      body: JSON.stringify({ key, value }),
    });
    return handleResponse(res);
  },

  async adminToggleThirdPlace(enabled: boolean, token: string): Promise<any> {
    const res = await fetch(`${API_BASE}/admin/knockout/rules/third-place-toggle`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        Authorization: `Bearer ${token}`,
      },
      body: JSON.stringify({ enabled }),
    });
    return handleResponse(res);
  },

  async adminResetPredictions(token: string): Promise<any> {
    const res = await fetch(`${API_BASE}/admin/knockout/reset-predictions`, {
      method: 'POST',
      headers: { Authorization: `Bearer ${token}` },
    });
    return handleResponse(res);
  },

  async adminGetKnockoutAuditLog(token: string): Promise<any[]> {
    const res = await fetch(`${API_BASE}/admin/knockout/audit-log`, {
      headers: { Authorization: `Bearer ${token}` },
    });
    return handleResponse<any[]>(res);
  },

  async adminApplyCeremonialDraw(pairings: any[], token: string): Promise<any> {
    const res = await fetch(`${API_BASE}/admin/knockout/apply-draw`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        Authorization: `Bearer ${token}`,
      },
      body: JSON.stringify({ pairings }),
    });
    return handleResponse(res);
  },

  async adminSyncDrawToDesktop(token: string): Promise<any> {
    const res = await fetch(`${API_BASE}/admin/knockout/sync-desktop`, {
      method: 'POST',
      headers: {
        Authorization: `Bearer ${token}`,
      },
    });
    return handleResponse(res);
  },
};

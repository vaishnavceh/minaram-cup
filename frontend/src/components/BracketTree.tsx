import React from 'react';
import { PublicBracket, PublicKnockoutRound, PublicMatch } from '../types';
import { Trophy, Crown, Sparkles, Swords, Shield, Clock } from 'lucide-react';

interface BracketTreeProps {
  bracket: PublicBracket;
  showTrophyPedestal?: boolean;
}

const DEFAULT_KNOCKOUT_ROUNDS: PublicKnockoutRound[] = [
  {
    round_name: 'Quarter-Final',
    matches: [
      {
        id: 85,
        tournament_id: 1,
        match_number: 85,
        stage: 'Quarter-Final',
        round_number: 1,
        team_a_name: 'Yet to decide',
        team_b_name: 'Yet to decide',
        team_a_score: null,
        team_b_score: null,
        penalty_a: null,
        penalty_b: null,
        status: 'SCHEDULED',
        scheduled_date: '2026-10-26',
        scheduled_time: 'Flexible (MW Window)',
        pitch: 'Minaram Pitch 1',
        notes: 'QF1 · Group Stage Qualifiers',
      },
      {
        id: 86,
        tournament_id: 1,
        match_number: 86,
        stage: 'Quarter-Final',
        round_number: 1,
        team_a_name: 'Yet to decide',
        team_b_name: 'Yet to decide',
        team_a_score: null,
        team_b_score: null,
        penalty_a: null,
        penalty_b: null,
        status: 'SCHEDULED',
        scheduled_date: '2026-10-26',
        scheduled_time: 'Flexible (MW Window)',
        pitch: 'Minaram Pitch 2',
        notes: 'QF2 · Group Stage Qualifiers',
      },
      {
        id: 87,
        tournament_id: 1,
        match_number: 87,
        stage: 'Quarter-Final',
        round_number: 1,
        team_a_name: 'Yet to decide',
        team_b_name: 'Yet to decide',
        team_a_score: null,
        team_b_score: null,
        penalty_a: null,
        penalty_b: null,
        status: 'SCHEDULED',
        scheduled_date: '2026-10-27',
        scheduled_time: 'Flexible (MW Window)',
        pitch: 'Minaram Pitch 1',
        notes: 'QF3 · Group Stage Qualifiers',
      },
      {
        id: 88,
        tournament_id: 1,
        match_number: 88,
        stage: 'Quarter-Final',
        round_number: 1,
        team_a_name: 'Yet to decide',
        team_b_name: 'Yet to decide',
        team_a_score: null,
        team_b_score: null,
        penalty_a: null,
        penalty_b: null,
        status: 'SCHEDULED',
        scheduled_date: '2026-10-27',
        scheduled_time: 'Flexible (MW Window)',
        pitch: 'Minaram Pitch 2',
        notes: 'QF4 · Group Stage Qualifiers',
      },
    ],
  },
  {
    round_name: 'Semi-Final',
    matches: [
      {
        id: 89,
        tournament_id: 1,
        match_number: 89,
        stage: 'Semi-Final',
        round_number: 2,
        team_a_name: 'Yet to decide',
        team_b_name: 'Yet to decide',
        team_a_score: null,
        team_b_score: null,
        penalty_a: null,
        penalty_b: null,
        status: 'SCHEDULED',
        scheduled_date: '2026-10-29',
        scheduled_time: 'Flexible (MW Window)',
        pitch: 'Minaram Stadium',
        notes: 'SF1 · Winner QF1 vs Winner QF2',
      },
      {
        id: 90,
        tournament_id: 1,
        match_number: 90,
        stage: 'Semi-Final',
        round_number: 2,
        team_a_name: 'Yet to decide',
        team_b_name: 'Yet to decide',
        team_a_score: null,
        team_b_score: null,
        penalty_a: null,
        penalty_b: null,
        status: 'SCHEDULED',
        scheduled_date: '2026-10-29',
        scheduled_time: 'Flexible (MW Window)',
        pitch: 'Minaram Stadium',
        notes: 'SF2 · Winner QF3 vs Winner QF4',
      },
    ],
  },
  {
    round_name: 'Final',
    matches: [
      {
        id: 91,
        tournament_id: 1,
        match_number: 91,
        stage: 'Final',
        round_number: 3,
        team_a_name: 'Yet to decide',
        team_b_name: 'Yet to decide',
        team_a_score: null,
        team_b_score: null,
        penalty_a: null,
        penalty_b: null,
        status: 'SCHEDULED',
        scheduled_date: '2026-10-31',
        scheduled_time: 'Flexible (MW Window)',
        pitch: 'Minaram Grand Arena',
        notes: 'Grand Final · Winner SF1 vs Winner SF2',
      },
    ],
  },
];

export const BracketTree: React.FC<BracketTreeProps> = ({ bracket, showTrophyPedestal = true }) => {
  const { rounds, champion } = bracket;

  // Always display the full official tournament bracket structure
  const activeRounds = rounds && rounds.length > 0 ? rounds : DEFAULT_KNOCKOUT_ROUNDS;

  const getSlotLabel = (match: PublicMatch, index: number, roundName: string): string => {
    const rName = roundName.toLowerCase();
    if (rName.includes('quarter')) return `QF${index + 1}`;
    if (rName.includes('semi')) return `SF${index + 1}`;
    if (rName.includes('final')) return 'FINAL';
    return `M#${match.match_number || index + 1}`;
  };

  const getRoundSubtitle = (roundName: string, count: number): string => {
    const rName = roundName.toLowerCase();
    if (rName.includes('quarter')) return '4 CLASHES · TOP 8 QUALIFIERS';
    if (rName.includes('semi')) return '2 CLASHES · PENULTIMATE ROUND';
    if (rName.includes('final')) return 'CHAMPIONSHIP DECIDER';
    return `${count} ${count === 1 ? 'Match' : 'Matches'}`;
  };

  const isUndecided = (name?: string | null): boolean => {
    if (!name) return true;
    const lower = name.trim().toLowerCase();
    return lower === 'tbd' || lower === 'yet to decide' || lower.includes('yet to decide');
  };

  return (
    <div className="space-y-8">
      {/* Trophy Pedestal / Champion Banner */}
      {showTrophyPedestal && (
        <div className="relative overflow-hidden rounded-2xl border border-amber-500/30 bg-gradient-to-r from-black via-[#161208] to-black p-6 sm:p-8 text-center shadow-[0_0_50px_rgba(245,158,11,0.12)]">
          <div className="flex flex-col items-center justify-center space-y-3">
            <div className="w-14 h-14 sm:w-16 sm:h-16 rounded-full bg-amber-500/10 border border-amber-500/40 flex items-center justify-center text-amber-400 shadow-inner">
              <Trophy className="w-7 h-7 sm:w-8 sm:h-8 animate-pulse text-amber-400" />
            </div>
            <div className="flex items-center space-x-2 text-xs font-mono uppercase tracking-widest text-amber-400">
              <Sparkles className="w-3.5 h-3.5" />
              <span>MINARAM CUP 2026 CHAMPIONSHIP</span>
              <Sparkles className="w-3.5 h-3.5" />
            </div>
            <h2 className="font-display text-3xl sm:text-5xl text-white tracking-wider">
              {champion ? champion.name : 'CHAMPION: YET TO DECIDE'}
            </h2>
            <p className="text-xs sm:text-sm font-mono text-neutral-400 max-w-md mx-auto">
              {champion ? (
                <>
                  Squad Manager:{' '}
                  <span className="text-white font-medium">{champion.manager_name}</span> (
                  {champion.department} · Year {champion.year})
                </>
              ) : (
                'All knockout positions are currently awaiting group stage completion. Tournament champion will be crowned at the Grand Final.'
              )}
            </p>
          </div>
        </div>
      )}

      {/* Bracket Rounds Columns */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6 sm:gap-8 relative items-stretch">
        {activeRounds.map((round) => {
          const isFinalRound = round.round_name.toLowerCase() === 'final';
          const isSemiRound = round.round_name.toLowerCase().includes('semi');

          return (
            <div
              key={round.round_name}
              className={`flex flex-col rounded-xl p-3 sm:p-4 border ${
                isFinalRound
                  ? 'bg-gradient-to-b from-[#161208] via-[#0e0d0a] to-[#0a0a0a] border-amber-500/40 shadow-[0_0_30px_rgba(245,158,11,0.08)]'
                  : 'bg-[#0f0f0f] border-neutral-800/80'
              }`}
            >
              {/* Round Header */}
              <div className="mb-4 pb-3 border-b border-neutral-800 text-center">
                <div className="flex items-center justify-center space-x-1.5 mb-1">
                  {isFinalRound ? (
                    <Crown className="w-4 h-4 text-amber-400" />
                  ) : isSemiRound ? (
                    <Swords className="w-4 h-4 text-brand-red" />
                  ) : (
                    <Shield className="w-4 h-4 text-neutral-400" />
                  )}
                  <h3 className="font-display text-xl sm:text-2xl tracking-wider text-white uppercase">
                    {round.round_name}
                  </h3>
                </div>
                <span className="text-[10px] font-mono text-neutral-400 uppercase tracking-widest block">
                  {getRoundSubtitle(round.round_name, (round.matches || []).length)}
                </span>
              </div>

              {/* Matches in Round Column */}
              <div
                className={`flex flex-col space-y-4 flex-grow ${
                  isFinalRound
                    ? 'justify-center'
                    : isSemiRound
                    ? 'justify-around'
                    : 'justify-between'
                }`}
              >
                {(round.matches || []).map((m, idx) => {
                  const isCompleted = m.status === 'COMPLETED';
                  const teamAUndecided = isUndecided(m.team_a_name);
                  const teamBUndecided = isUndecided(m.team_b_name);
                  const slotLabel = getSlotLabel(m, idx, round.round_name);

                  const teamAWon =
                    isCompleted &&
                    ((m.team_a_score ?? 0) > (m.team_b_score ?? 0) ||
                      ((m.team_a_score ?? 0) === (m.team_b_score ?? 0) &&
                        (m.penalty_a ?? 0) > (m.penalty_b ?? 0)));
                  const teamBWon =
                    isCompleted &&
                    ((m.team_b_score ?? 0) > (m.team_a_score ?? 0) ||
                      ((m.team_a_score ?? 0) === (m.team_b_score ?? 0) &&
                        (m.penalty_b ?? 0) > (m.penalty_a ?? 0)));

                  return (
                    <div
                      key={m.id || idx}
                      className={`rounded-lg p-3 sm:p-3.5 transition-all duration-200 border relative ${
                        isFinalRound
                          ? 'bg-[#14120c] border-amber-500/50 shadow-md hover:border-amber-400'
                          : 'bg-[#141414] border-neutral-800 hover:border-neutral-700 shadow-sm'
                      }`}
                    >
                      {/* Top Bar: Match Slot & Status */}
                      <div className="text-[11px] font-mono mb-2.5 flex items-center justify-between">
                        <div className="flex items-center space-x-1.5">
                          <span
                            className={`font-bold px-1.5 py-0.5 rounded text-[10px] uppercase ${
                              isFinalRound
                                ? 'bg-amber-500/20 text-amber-400 border border-amber-500/30'
                                : 'bg-neutral-900 text-neutral-300 border border-neutral-800'
                            }`}
                          >
                            {slotLabel}
                          </span>
                          {m.match_number && (
                            <span className="text-neutral-500 text-[10px]">M#{m.match_number}</span>
                          )}
                        </div>

                        {isCompleted ? (
                          <span className="text-[10px] font-mono font-bold text-emerald-400 bg-emerald-950/60 px-1.5 py-0.5 rounded border border-emerald-800/40">
                            FT
                          </span>
                        ) : (
                          <span className="text-[10px] font-mono font-bold text-amber-400/90 bg-amber-950/40 px-2 py-0.5 rounded border border-amber-700/30 uppercase tracking-wider">
                            Yet to decide
                          </span>
                        )}
                      </div>

                      {/* Team A Slot */}
                      <div
                        className={`flex items-center justify-between py-1.5 px-2.5 rounded transition-colors ${
                          teamAWon
                            ? 'bg-neutral-800 font-bold text-white border border-neutral-700'
                            : teamAUndecided
                            ? 'bg-black/40 border border-dashed border-neutral-800/90 text-neutral-400'
                            : 'text-neutral-200 bg-black/20'
                        }`}
                      >
                        <div className="flex items-center space-x-2 truncate mr-2">
                          <span
                            className={`w-1.5 h-1.5 rounded-full shrink-0 ${
                              teamAWon
                                ? 'bg-amber-400'
                                : teamAUndecided
                                ? 'bg-neutral-600'
                                : 'bg-neutral-500'
                            }`}
                          />
                          <span
                            className={`truncate text-xs ${
                              teamAUndecided
                                ? 'italic font-mono text-neutral-400 font-normal'
                                : 'font-semibold'
                            }`}
                          >
                            {teamAUndecided ? 'Yet to decide' : m.team_a_name}
                          </span>
                        </div>
                        <span className="font-mono text-xs tabular-nums text-neutral-300 select-none">
                          {isCompleted ? m.team_a_score : '—'}
                        </span>
                      </div>

                      {/* Team B Slot */}
                      <div
                        className={`flex items-center justify-between py-1.5 px-2.5 rounded mt-1.5 transition-colors ${
                          teamBWon
                            ? 'bg-neutral-800 font-bold text-white border border-neutral-700'
                            : teamBUndecided
                            ? 'bg-black/40 border border-dashed border-neutral-800/90 text-neutral-400'
                            : 'text-neutral-200 bg-black/20'
                        }`}
                      >
                        <div className="flex items-center space-x-2 truncate mr-2">
                          <span
                            className={`w-1.5 h-1.5 rounded-full shrink-0 ${
                              teamBWon
                                ? 'bg-amber-400'
                                : teamBUndecided
                                ? 'bg-neutral-600'
                                : 'bg-neutral-500'
                            }`}
                          />
                          <span
                            className={`truncate text-xs ${
                              teamBUndecided
                                ? 'italic font-mono text-neutral-400 font-normal'
                                : 'font-semibold'
                            }`}
                          >
                            {teamBUndecided ? 'Yet to decide' : m.team_b_name}
                          </span>
                        </div>
                        <span className="font-mono text-xs tabular-nums text-neutral-300 select-none">
                          {isCompleted ? m.team_b_score : '—'}
                        </span>
                      </div>

                      {/* Penalty line if match went to penalties */}
                      {isCompleted && m.penalty_a !== null && m.penalty_b !== null && (
                        <div className="text-right text-[10px] font-mono text-neutral-400 mt-1">
                          Penalties: {m.penalty_a} - {m.penalty_b}
                        </div>
                      )}

                      {/* Notes & Timeline */}
                      <div className="mt-2.5 pt-2 border-t border-neutral-800/60 flex items-center justify-between text-[10px] font-mono text-neutral-500">
                        <span className="truncate max-w-[160px]">
                          {m.notes || (isFinalRound ? 'Grand Final' : 'Knockout Match')}
                        </span>
                        <span className="text-neutral-500 flex items-center space-x-1 shrink-0">
                          <Clock className="w-3 h-3 text-neutral-500" />
                          <span>{m.scheduled_date || 'TBD'}</span>
                        </span>
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};

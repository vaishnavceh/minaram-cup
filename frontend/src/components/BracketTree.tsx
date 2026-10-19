import React, { useState } from 'react';
import { PublicBracket, PublicKnockoutRound, PublicMatch } from '../types';
import { Trophy, Crown, Sparkles, Swords, Shield, Clock, AlertTriangle, Radio, CheckCircle2, ChevronRight } from 'lucide-react';

interface BracketTreeProps {
  bracket: PublicBracket;
  showTrophyPedestal?: boolean;
  selectedStageFilter?: string;
}

export const BracketTree: React.FC<BracketTreeProps> = ({
  bracket,
  showTrophyPedestal = true,
  selectedStageFilter = 'ALL',
}) => {
  const { rounds, champion, direct_qualifiers, is_provisional, conflicts } = bracket;

  // Filter rounds if stage filter is specified
  const displayRounds = rounds && rounds.length > 0
    ? (selectedStageFilter === 'ALL'
        ? rounds
        : rounds.filter((r) => r.round_name.toLowerCase().includes(selectedStageFilter.toLowerCase())))
    : [];

  const getSlotLabel = (match: PublicMatch, index: number, roundName: string): string => {
    if (match.bracket_slot) return match.bracket_slot;
    const rName = roundName.toLowerCase();
    if (rName.includes('preliminary')) return `PR${index + 1}`;
    if (rName.includes('16')) return `R16_${index + 1}`;
    if (rName.includes('quarter')) return `QF${index + 1}`;
    if (rName.includes('semi')) return `SF${index + 1}`;
    if (rName.includes('final') && !rName.includes('semi') && !rName.includes('quarter')) return 'FINAL';
    if (rName.includes('third')) return '3RD';
    return `M#${match.match_number || index + 1}`;
  };

  const getRoundSubtitle = (roundName: string, count: number): string => {
    const rName = roundName.toLowerCase();
    if (rName.includes('preliminary')) return '14 CLASHES · 28 SQUADS FIGHT FOR R16';
    if (rName.includes('16')) return '8 CLASHES · 2 DIRECT QUALIFIERS + 14 PRELIM WINNERS';
    if (rName.includes('quarter')) return '4 CLASHES · ELITE TOP 8';
    if (rName.includes('semi')) return '2 CLASHES · PENULTIMATE BATTLE';
    if (rName.includes('final') && !rName.includes('semi') && !rName.includes('quarter')) return 'CHAMPIONSHIP DECIDER';
    if (rName.includes('third')) return 'BRONZE MEDAL PLAYOFF';
    return `${count} ${count === 1 ? 'Match' : 'Matches'}`;
  };

  const isUndecided = (name?: string | null): boolean => {
    if (!name) return true;
    const lower = name.trim().toLowerCase();
    return (
      lower === 'tbd' ||
      lower === 'yet to decide' ||
      lower.includes('yet to decide') ||
      lower.startsWith('winner of') ||
      lower.startsWith('runner-up of') ||
      lower.startsWith('seed ')
    );
  };

  const renderStatusBadge = (status: string, isOfficial?: boolean) => {
    const s = (status || 'PREDICTED').toUpperCase();
    if (s === 'COMPLETED' || s === 'WALKOVER') {
      return (
        <span className="inline-flex items-center space-x-1 text-[10px] font-mono font-bold text-emerald-300 bg-emerald-950/80 px-2 py-0.5 rounded border border-emerald-700/60 shadow-sm">
          <CheckCircle2 className="w-3 h-3 text-emerald-400" />
          <span>OFFICIAL FT</span>
        </span>
      );
    }
    if (s === 'LIVE' || s === 'IN_PROGRESS' || s === 'IN PROGRESS') {
      return (
        <span className="inline-flex items-center space-x-1.5 text-[10px] font-mono font-bold text-rose-300 bg-rose-950/90 px-2 py-0.5 rounded border border-rose-600/80 animate-pulse shadow-[0_0_10px_rgba(244,63,94,0.3)]">
          <Radio className="w-3 h-3 text-rose-400 animate-spin" />
          <span>LIVE NOW</span>
        </span>
      );
    }
    if (s === 'UNDER REVIEW' || s === 'UNDER_REVIEW') {
      return (
        <span className="inline-flex items-center space-x-1 text-[10px] font-mono font-bold text-purple-300 bg-purple-950/80 px-2 py-0.5 rounded border border-purple-600/70">
          <AlertTriangle className="w-3 h-3 text-purple-400" />
          <span>UNDER REVIEW</span>
        </span>
      );
    }
    if (s === 'CONFIRMED' || (isOfficial && s !== 'PREDICTED' && s !== 'LIVE_DRAW')) {
      return (
        <span className="inline-flex items-center space-x-1 text-[10px] font-mono font-bold text-cyan-300 bg-cyan-950/80 px-2 py-0.5 rounded border border-cyan-700/60 shadow-[0_0_10px_rgba(6,182,212,0.15)]">
          <Shield className="w-3 h-3 text-cyan-400" />
          <span>CONFIRMED FIXTURE</span>
        </span>
      );
    }
    if (s === 'PREDICTED' || s === 'LIVE_DRAW' || s === 'LIVE DRAW') {
      return (
        <span className="inline-flex items-center space-x-1 text-[10px] font-mono font-bold text-amber-300 bg-amber-950/70 px-2 py-0.5 rounded border border-amber-600/70 shadow-[0_0_10px_rgba(245,158,11,0.2)] uppercase tracking-wider">
          <Sparkles className="w-2.5 h-2.5 text-amber-400 animate-pulse" />
          <span>PREDICTED · LIVE DRAW</span>
        </span>
      );
    }
    return (
      <span className="inline-flex items-center space-x-1 text-[10px] font-mono font-bold text-neutral-400 bg-neutral-900/60 px-2 py-0.5 rounded border border-neutral-700/60 uppercase tracking-wider">
        <Sparkles className="w-2.5 h-2.5 text-neutral-400" />
        <span>PREDICTED</span>
      </span>
    );
  };

  return (
    <div className="space-y-8 select-none">
      {/* Trophy Pedestal / Champion Banner */}
      {showTrophyPedestal && (
        <div className="relative overflow-hidden rounded-2xl border border-amber-500/30 bg-gradient-to-r from-black via-[#161208] to-black p-6 sm:p-8 text-center shadow-[0_0_50px_rgba(245,158,11,0.12)]">
          <div className="flex flex-col items-center justify-center space-y-3">
            <div className="w-14 h-14 sm:w-16 sm:h-16 rounded-full bg-amber-500/10 border border-amber-500/40 flex items-center justify-center text-amber-400 shadow-inner">
              <Trophy className="w-7 h-7 sm:w-8 sm:h-8 animate-pulse text-amber-400" />
            </div>
            <div className="flex items-center space-x-2 text-xs font-mono uppercase tracking-widest text-amber-400">
              <Sparkles className="w-3.5 h-3.5" />
              <span>MINARAM CUP 2026 KNOCKOUT TOURNAMENT</span>
              <Sparkles className="w-3.5 h-3.5" />
            </div>
            <h2 className="font-display text-3xl sm:text-5xl text-white tracking-wider">
              {champion ? champion.name : 'CHAMPION: YET TO BE DECIDED'}
            </h2>
            <p className="text-xs sm:text-sm font-mono text-neutral-400 max-w-xl mx-auto">
              {champion ? (
                <>
                  Official Tournament Champion: <span className="text-amber-300 font-bold">{champion.name}</span>{' '}
                  (Captain: {champion.manager_name}{champion.group_name ? ` · ${champion.group_name}` : ''})
                </>
              ) : is_provisional ? (
                'Tournament is actively in group stage. Qualifying squads and direct Round of 16 entries are dynamically projected below.'
              ) : (
                'Single-elimination championship: 28 preliminary contenders + 2 direct qualifiers battle through to the Grand Final.'
              )}
            </p>
          </div>
        </div>
      )}

      {/* Connected Bracket Columns Container (Horizontal scroll on mobile/tablet, multi-column grid on desktop) */}
      <div className="overflow-x-auto pb-6 scrollbar-thin scrollbar-thumb-neutral-800 scrollbar-track-neutral-950">
        <div
          className="flex flex-nowrap items-stretch gap-6 min-w-[1100px] lg:min-w-full"
          style={{ minWidth: displayRounds.length > 3 ? `${displayRounds.length * 320}px` : '100%' }}
        >
          {displayRounds.map((round) => {
            const rName = round.round_name.toLowerCase();
            const isFinal = rName.includes('final') && !rName.includes('semi') && !rName.includes('quarter');
            const isSemi = rName.includes('semi');
            const isPrelim = rName.includes('preliminary');
            const isR16 = rName.includes('16');

            return (
              <div
                key={round.round_name}
                className={`flex-1 min-w-[300px] max-w-[380px] flex flex-col rounded-2xl p-4 border transition-all ${
                  isFinal
                    ? 'bg-gradient-to-b from-[#181308] via-[#100d07] to-[#0a0a0a] border-amber-500/50 shadow-[0_0_35px_rgba(245,158,11,0.12)]'
                    : isSemi
                    ? 'bg-gradient-to-b from-[#140b0b] to-[#0c0c0c] border-brand-red/30'
                    : isR16
                    ? 'bg-[#0f0f12] border-cyan-900/30'
                    : 'bg-[#0e0e0e] border-neutral-800/80'
                }`}
              >
                {/* Round Header */}
                <div className="mb-4 pb-3 border-b border-neutral-800 text-center">
                  <div className="flex items-center justify-center space-x-1.5 mb-1">
                    {isFinal ? (
                      <Crown className="w-4 h-4 text-amber-400" />
                    ) : isSemi ? (
                      <Swords className="w-4 h-4 text-brand-red" />
                    ) : isR16 ? (
                      <Shield className="w-4 h-4 text-cyan-400" />
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
                  className={`flex flex-col space-y-3.5 flex-grow ${
                    isFinal
                      ? 'justify-center'
                      : isSemi
                      ? 'justify-around'
                      : 'justify-start'
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
                          (m.penalty_a ?? 0) > (m.penalty_b ?? 0)) ||
                        m.winner_id === m.team_a_id);

                    const teamBWon =
                      isCompleted &&
                      ((m.team_b_score ?? 0) > (m.team_a_score ?? 0) ||
                        ((m.team_a_score ?? 0) === (m.team_b_score ?? 0) &&
                          (m.penalty_b ?? 0) > (m.penalty_a ?? 0)) ||
                        m.winner_id === m.team_b_id);

                    const teamALost = isCompleted && !teamAWon;
                    const teamBLost = isCompleted && !teamBWon;

                    return (
                      <div
                        key={m.id || idx}
                        className={`rounded-xl p-3.5 transition-all duration-200 border relative ${
                          isFinal
                            ? 'bg-[#15120a] border-amber-500/60 shadow-lg hover:border-amber-400'
                            : m.is_official
                            ? 'bg-[#121214] border-cyan-900/50 hover:border-cyan-700/80 shadow-sm'
                            : 'bg-[#131313] border-neutral-800/90 hover:border-neutral-700 shadow-sm'
                        }`}
                      >
                        {/* Top Bar: Slot, Match Number, Status Badge */}
                        <div className="text-[11px] font-mono mb-2.5 flex items-center justify-between gap-2">
                          <div className="flex items-center space-x-1.5 shrink-0">
                            <span
                              className={`font-bold px-2 py-0.5 rounded text-[10px] tracking-wider uppercase ${
                                isFinal
                                  ? 'bg-amber-500/20 text-amber-300 border border-amber-500/40'
                                  : isR16
                                  ? 'bg-cyan-950/60 text-cyan-300 border border-cyan-800/50'
                                  : 'bg-neutral-900 text-neutral-300 border border-neutral-800'
                              }`}
                            >
                              {slotLabel}
                            </span>
                            {m.match_number && (
                              <span className="text-neutral-500 text-[10px]">M#{m.match_number}</span>
                            )}
                          </div>

                          <div className="shrink-0">
                            {renderStatusBadge(m.status, m.is_official)}
                          </div>
                        </div>

                        {/* Team A Slot */}
                        <div
                          className={`flex items-center justify-between py-2 px-2.5 rounded transition-colors ${
                            teamAWon
                              ? 'bg-amber-950/40 font-bold text-white border border-amber-600/60'
                              : teamALost
                              ? 'bg-black/40 text-neutral-400 border border-neutral-900 line-through opacity-75'
                              : teamAUndecided
                              ? 'bg-black/30 border border-dashed border-neutral-800 text-neutral-400'
                              : 'text-neutral-100 bg-neutral-900/80 border border-neutral-800/80'
                          }`}
                        >
                          <div className="flex items-center space-x-2 truncate mr-2 min-w-0">
                            <span
                              className={`w-1.5 h-1.5 rounded-full shrink-0 ${
                                teamAWon
                                  ? 'bg-amber-400 shadow-[0_0_8px_rgba(251,191,36,0.8)]'
                                  : teamALost
                                  ? 'bg-rose-500'
                                  : teamAUndecided
                                  ? 'bg-neutral-600'
                                  : 'bg-cyan-400'
                              }`}
                            />
                            <div className="truncate flex flex-col min-w-0">
                              <span
                                className={`truncate text-xs ${
                                  teamAUndecided
                                    ? 'italic font-mono text-neutral-400 font-normal'
                                    : 'font-semibold'
                                }`}
                                title={m.team_a_name || 'Yet to decide'}
                              >
                                {m.team_a_name || 'Yet to decide'}
                              </span>
                              {m.home_group && (
                                <span className="text-[9px] font-mono text-neutral-400 truncate">
                                  {m.home_group}
                                </span>
                              )}
                            </div>
                          </div>
                          <span className="font-mono text-xs tabular-nums text-neutral-200 shrink-0 font-bold">
                            {isCompleted && m.team_a_score !== null ? m.team_a_score : '—'}
                          </span>
                        </div>

                        {/* Team B Slot */}
                        <div
                          className={`flex items-center justify-between py-2 px-2.5 rounded mt-1.5 transition-colors ${
                            teamBWon
                              ? 'bg-amber-950/40 font-bold text-white border border-amber-600/60'
                              : teamBLost
                              ? 'bg-black/40 text-neutral-400 border border-neutral-900 line-through opacity-75'
                              : teamBUndecided
                              ? 'bg-black/30 border border-dashed border-neutral-800 text-neutral-400'
                              : 'text-neutral-100 bg-neutral-900/80 border border-neutral-800/80'
                          }`}
                        >
                          <div className="flex items-center space-x-2 truncate mr-2 min-w-0">
                            <span
                              className={`w-1.5 h-1.5 rounded-full shrink-0 ${
                                teamBWon
                                  ? 'bg-amber-400 shadow-[0_0_8px_rgba(251,191,36,0.8)]'
                                  : teamBLost
                                  ? 'bg-rose-500'
                                  : teamBUndecided
                                  ? 'bg-neutral-600'
                                  : 'bg-cyan-400'
                              }`}
                            />
                            <div className="truncate flex flex-col min-w-0">
                              <span
                                className={`truncate text-xs ${
                                  teamBUndecided
                                    ? 'italic font-mono text-neutral-400 font-normal'
                                    : 'font-semibold'
                                }`}
                                title={m.team_b_name || 'Yet to decide'}
                              >
                                {m.team_b_name || 'Yet to decide'}
                              </span>
                              {m.away_group && (
                                <span className="text-[9px] font-mono text-neutral-400 truncate">
                                  {m.away_group}
                                </span>
                              )}
                            </div>
                          </div>
                          <span className="font-mono text-xs tabular-nums text-neutral-200 shrink-0 font-bold">
                            {isCompleted && m.team_b_score !== null ? m.team_b_score : '—'}
                          </span>
                        </div>

                        {/* Penalty or Winner Method Notification */}
                        {isCompleted && (m.penalty_a !== null || m.winner_method) && (
                          <div className="text-right text-[10px] font-mono text-amber-400/90 mt-1.5">
                            {m.penalty_a !== null && m.penalty_b !== null
                              ? `Penalties: ${m.penalty_a} - ${m.penalty_b}`
                              : m.winner_method ? `Decided via: ${m.winner_method}` : ''}
                          </div>
                        )}

                        {/* Schedule & Venue Footer */}
                        <div className="mt-2.5 pt-2 border-t border-neutral-800/70 flex items-center justify-between text-[10px] font-mono text-neutral-400">
                          <span className="truncate max-w-[150px]">
                            {m.notes || (isFinal ? 'Grand Arena' : m.pitch || 'Minaram Stadium')}
                          </span>
                          <span className="flex items-center space-x-1 shrink-0">
                            <Clock className="w-3 h-3 text-neutral-400" />
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
    </div>
  );
};

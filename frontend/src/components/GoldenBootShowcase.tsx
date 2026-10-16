import React, { useState, useEffect } from 'react';
import { api } from '../api';
import { TopScorer } from '../types';
import { INITIAL_GOLDEN_BOOT_PODIUM, GoldenBootEntry } from '../constants';
import { Trophy, Flame, ChevronDown, ChevronUp, Award, Zap, Shield, Sparkles } from 'lucide-react';

interface GoldenBootShowcaseProps {
  compact?: boolean;
}

export const GoldenBootShowcase: React.FC<GoldenBootShowcaseProps> = ({ compact = false }) => {
  const [topScorers, setTopScorers] = useState<TopScorer[]>([]);
  const [showFullTable, setShowFullTable] = useState(false);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let isMounted = true;
    const fetchScorers = async () => {
      try {
        const data = await api.getTopScorers(10);
        if (isMounted && Array.isArray(data) && data.length > 0) {
          setTopScorers(data);
        }
      } catch (err) {
        console.warn('Using initial Golden Boot constants as fallback', err);
      } finally {
        if (isMounted) setLoading(false);
      }
    };
    fetchScorers();
    return () => {
      isMounted = false;
    };
  }, []);

  // Compute podium: either from live API or fallback constants
  const podiumEntries: GoldenBootEntry[] = React.useMemo(() => {
    if (topScorers.length >= 3) {
      return [
        {
          rank: 1,
          placeLabel: '1ST',
          awardTitle: 'GOLDEN BOOT WINNER',
          awardSub: 'TOURNAMENT TOP SCORER',
          playerName: topScorers[0].player_name,
          teamName: topScorers[0].team_name,
          groupName: topScorers[0].group_name,
          goals: topScorers[0].goals,
          matchesPlayed: topScorers[0].matches_played,
          goalsPerMatch: topScorers[0].goals_per_match,
          featured: true,
        },
        {
          rank: 2,
          placeLabel: '2ND',
          awardTitle: 'SECOND PLACE',
          awardSub: 'SILVER BOOT',
          playerName: topScorers[1].player_name,
          teamName: topScorers[1].team_name,
          groupName: topScorers[1].group_name,
          goals: topScorers[1].goals,
          matchesPlayed: topScorers[1].matches_played,
          goalsPerMatch: topScorers[1].goals_per_match,
          featured: false,
        },
        {
          rank: 3,
          placeLabel: '3RD',
          awardTitle: 'THIRD PLACE',
          awardSub: 'BRONZE BOOT',
          playerName: topScorers[2].player_name,
          teamName: topScorers[2].team_name,
          groupName: topScorers[2].group_name,
          goals: topScorers[2].goals,
          matchesPlayed: topScorers[2].matches_played,
          goalsPerMatch: topScorers[2].goals_per_match,
          featured: false,
        },
      ];
    }
    return INITIAL_GOLDEN_BOOT_PODIUM;
  }, [topScorers]);

  return (
    <section id="golden-boot" className="relative">
      {/* Section Header */}
      <div className="flex flex-col items-center text-center mb-8">
        <div className="flex items-center space-x-2 text-xs font-mono uppercase tracking-widest text-amber-400 mb-1">
          <Flame className="w-4 h-4 text-amber-500 animate-pulse" />
          <span>INDIVIDUAL ACCOLADES</span>
        </div>
        <h2 className="font-display text-4xl sm:text-5xl text-white tracking-wider flex items-center justify-center space-x-2">
          <span>GOLDEN BOOT</span>
        </h2>
        <p className="text-xs sm:text-sm font-mono text-neutral-400 mt-2 max-w-xl">
          Tournament top goal scorers in the Minaram Cup eFootball Championship.
        </p>
      </div>

      {/* Podium Cards Grid (1st Winner, 2nd Runner Up, 3rd Place) */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-5 sm:gap-6 items-stretch max-w-5xl mx-auto">
        {podiumEntries.map((scorer) => {
          const isWinner = scorer.rank === 1;
          const isSecond = scorer.rank === 2;
          const isThird = scorer.rank === 3;

          return (
            <div
              key={scorer.rank}
              className={`relative flex flex-col justify-between rounded-xl transition-all duration-300 ${
                isWinner
                  ? 'bg-gradient-to-b from-[#251b0a] via-[#161208] to-[#0c0c0c] border-2 border-amber-500 shadow-[0_0_35px_rgba(245,158,11,0.22)] p-6 sm:p-7 order-first md:order-2'
                  : isSecond
                  ? 'bg-[#101010] border border-neutral-700/80 hover:border-neutral-500 p-5 sm:p-6 order-2 md:order-1'
                  : 'bg-[#101010] border border-neutral-800 hover:border-neutral-700 p-5 sm:p-6 order-3 md:order-3'
              }`}
            >
              {/* Header: Rank Marker & Award Badge */}
              <div className="flex items-center justify-between mb-4">
                <span
                  className={`text-[11px] font-mono uppercase tracking-widest px-2.5 py-0.5 rounded flex items-center space-x-1.5 ${
                    isWinner
                      ? 'bg-amber-500/20 text-amber-400 border border-amber-500/40 font-bold'
                      : isSecond
                      ? 'bg-neutral-800 text-neutral-300 border border-neutral-700 font-semibold'
                      : 'bg-amber-950/30 text-amber-600/90 border border-amber-800/40 font-semibold'
                  }`}
                >
                  {isWinner && <Trophy className="w-3 h-3 text-amber-400 mr-1" />}
                  <span>{scorer.placeLabel} PLACE</span>
                </span>

                <span
                  className={`font-display text-3xl tabular-nums ${
                    isWinner ? 'text-amber-400 font-bold' : isSecond ? 'text-neutral-400' : 'text-neutral-500'
                  }`}
                >
                  #{scorer.rank}
                </span>
              </div>

              {/* Award Title & Player Info */}
              <div className="my-2">
                <div className="flex items-center space-x-1.5 mb-1">
                  <span
                    className={`text-[10px] font-mono uppercase tracking-widest font-bold ${
                      isWinner ? 'text-amber-400' : 'text-neutral-500'
                    }`}
                  >
                    {scorer.awardTitle}
                  </span>
                </div>

                {/* Player Name */}
                <h3
                  className={`font-display tracking-wider uppercase truncate ${
                    isWinner
                      ? 'text-3xl sm:text-4xl text-white font-bold drop-shadow'
                      : 'text-2xl sm:text-3xl text-neutral-100'
                  }`}
                  title={scorer.playerName}
                >
                  {scorer.playerName}
                </h3>

                {/* Team & Group Badge */}
                <div className="mt-2 flex items-center space-x-2">
                  <span className="inline-flex items-center px-2 py-0.5 rounded bg-neutral-900 border border-neutral-800 text-xs font-mono text-neutral-300">
                    <Shield className="w-3 h-3 text-brand-red mr-1 shrink-0" />
                    <span className="truncate max-w-[140px] font-semibold">{scorer.teamName}</span>
                  </span>
                  {scorer.groupName && (
                    <span className="text-[11px] font-mono text-neutral-400">
                      · {scorer.groupName}
                    </span>
                  )}
                </div>

                {/* Goals Highlight Display */}
                <div className="mt-5 p-3 rounded-lg bg-black/60 border border-neutral-800/80 flex items-baseline justify-between">
                  <div>
                    <span className="text-[10px] font-mono uppercase tracking-wider text-neutral-400 block">
                      TOTAL GOALS
                    </span>
                    <span
                      className={`font-display tracking-tight tabular-nums leading-none ${
                        isWinner
                          ? 'text-5xl sm:text-6xl text-amber-400 font-bold'
                          : isSecond
                          ? 'text-4xl sm:text-5xl text-white'
                          : 'text-4xl sm:text-5xl text-neutral-200'
                      }`}
                    >
                      {scorer.goals}
                    </span>
                    <span className="text-xs font-mono text-neutral-400 ml-1.5 uppercase">
                      GOALS
                    </span>
                  </div>

                  <div className="text-right font-mono text-[11px] text-neutral-400 space-y-0.5">
                    <div>
                      <span className="text-neutral-300 font-bold">{scorer.matchesPlayed}</span>{' '}
                      {scorer.matchesPlayed === 1 ? 'Match' : 'Matches'}
                    </div>
                    <div className="text-[10px] text-neutral-400">
                      {scorer.goalsPerMatch.toFixed(1)} / game
                    </div>
                  </div>
                </div>
              </div>

              {/* Minimal Footer */}
              <div
                className={`mt-5 pt-3 border-t text-[11px] font-mono uppercase tracking-widest flex items-center justify-between ${
                  isWinner
                    ? 'border-amber-500/30 text-amber-400'
                    : isSecond
                    ? 'border-neutral-800 text-neutral-400'
                    : 'border-neutral-800 text-neutral-400'
                }`}
              >
                <span className="font-semibold">{scorer.awardSub}</span>
                {isWinner && (
                  <span className="flex items-center space-x-1.5 font-bold">
                    <span className="w-2 h-2 rounded-full bg-amber-400 animate-ping" />
                    <span>LEADER</span>
                  </span>
                )}
              </div>
            </div>
          );
        })}
      </div>

      {/* Expandable Full Top Scorers Leaderboard Toggle */}
      {!compact && (
        <div className="max-w-5xl mx-auto mt-8">
          <div className="flex justify-center">
            <button
              type="button"
              onClick={() => setShowFullTable((prev) => !prev)}
              className="inline-flex items-center space-x-2 px-4 py-2 rounded-lg bg-neutral-900/90 hover:bg-neutral-800 border border-neutral-800 hover:border-neutral-700 text-neutral-300 hover:text-white text-xs font-mono tracking-wider transition-all cursor-pointer shadow-sm"
            >
              <Award className="w-3.5 h-3.5 text-amber-400" />
              <span>
                {showFullTable
                  ? 'HIDE FULL TOP SCORERS LEADERBOARD'
                  : 'VIEW FULL TOP SCORERS LEADERBOARD (TOP 10)'}
              </span>
              {showFullTable ? (
                <ChevronUp className="w-3.5 h-3.5 ml-1" />
              ) : (
                <ChevronDown className="w-3.5 h-3.5 ml-1" />
              )}
            </button>
          </div>

          {/* Full Leaderboard Table (Conditionally Rendered) */}
          {showFullTable && (
            <div className="mt-6 bg-[#121212] border border-[#222222] rounded-xl overflow-hidden shadow-xl animate-fadeIn">
              <div className="px-5 py-3.5 bg-black/60 border-b border-[#1f1f1f] flex items-center justify-between">
                <div className="flex items-center space-x-2">
                  <span className="w-2 h-2 rounded-full bg-amber-400 animate-pulse" />
                  <h3 className="font-display text-lg tracking-wider text-white uppercase">
                    CHAMPIONSHIP GOAL SCORERS LEADERBOARD
                  </h3>
                </div>
                <span className="text-[10px] font-mono text-neutral-400 uppercase tracking-widest">
                  LIVE GOAL TALLIES
                </span>
              </div>

              <div className="overflow-x-auto">
                <table className="w-full text-left text-xs sm:text-sm">
                  <thead>
                    <tr className="border-b border-[#222222] bg-[#161616]/70 text-[11px] font-mono uppercase tracking-wider text-neutral-400">
                      <th className="py-2.5 px-3 text-center w-12">POS</th>
                      <th className="py-2.5 px-4">PLAYER / CAPTAIN</th>
                      <th className="py-2.5 px-4">SQUAD / CLUB</th>
                      <th className="py-2.5 px-3 text-center">GRP</th>
                      <th className="py-2.5 px-3 text-center">MP</th>
                      <th className="py-2.5 px-3 text-center hidden sm:table-cell">G / MATCH</th>
                      <th className="py-2.5 px-4 text-center font-bold text-amber-400">GOALS</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-[#1c1c1c] font-sans">
                    {(topScorers.length > 0
                      ? topScorers
                      : [
                          { rank: 1, player_name: 'Aromal', team_name: 'Fury FC', group_name: 'Group E', matches_played: 2, goals_per_match: 5.5, goals: 11 },
                          { rank: 2, player_name: 'Brian', team_name: 'Zeltic Fc', group_name: 'Group L', matches_played: 1, goals_per_match: 10.0, goals: 10 },
                          { rank: 3, player_name: 'Akshay T Geevarghese', team_name: 'Imperium', group_name: 'Group B', matches_played: 2, goals_per_match: 4.0, goals: 8 },
                          { rank: 4, player_name: 'Abhikrishna', team_name: 'HORKHAX', group_name: 'Group D', matches_played: 2, goals_per_match: 4.0, goals: 8 },
                          { rank: 5, player_name: 'Mahijith', team_name: 'Napoli', group_name: 'Group D', matches_played: 2, goals_per_match: 3.5, goals: 7 },
                          { rank: 6, player_name: 'Sreehari KJ', team_name: 'Honoured one', group_name: 'Group D', matches_played: 2, goals_per_match: 3.0, goals: 6 },
                          { rank: 7, player_name: 'Kiran', team_name: 'Atalanta', group_name: 'Group O', matches_played: 1, goals_per_match: 5.0, goals: 5 },
                          { rank: 8, player_name: 'Arun Christopher', team_name: 'IPB', group_name: 'Group F', matches_played: 1, goals_per_match: 5.0, goals: 5 },
                          { rank: 9, player_name: 'Nihal.H', team_name: 'MOTTA PUFFS', group_name: 'Group H', matches_played: 1, goals_per_match: 5.0, goals: 5 },
                          { rank: 10, player_name: 'Shravan S', team_name: 'Ya Illaahi', group_name: 'Group C', matches_played: 1, goals_per_match: 5.0, goals: 5 },
                        ]
                    ).map((scorer, idx) => {
                      const isTop3 = idx < 3;
                      return (
                        <tr
                          key={idx}
                          className={`hover:bg-[#181818] transition-colors ${
                            idx === 0
                              ? 'bg-amber-950/15'
                              : isTop3
                              ? 'bg-neutral-900/30'
                              : ''
                          }`}
                        >
                          {/* Position */}
                          <td className="py-3 px-3 text-center font-mono text-xs font-bold">
                            <span
                              className={`inline-flex items-center justify-center w-6 h-6 rounded ${
                                idx === 0
                                  ? 'bg-amber-500/20 text-amber-400 border border-amber-500/50'
                                  : idx === 1
                                  ? 'bg-neutral-800 text-neutral-200 border border-neutral-700'
                                  : idx === 2
                                  ? 'bg-amber-950/40 text-amber-500 border border-amber-800/50'
                                  : 'text-neutral-400'
                              }`}
                            >
                              {scorer.rank}
                            </span>
                          </td>

                          {/* Player Name */}
                          <td className="py-3 px-4 font-semibold text-white">
                            <div className="flex items-center space-x-2">
                              {idx === 0 && <Trophy className="w-3.5 h-3.5 text-amber-400 shrink-0" />}
                              <span className="truncate max-w-[160px] sm:max-w-[220px]">
                                {scorer.player_name}
                              </span>
                            </div>
                          </td>

                          {/* Squad / Team */}
                          <td className="py-3 px-4 font-mono text-neutral-300">
                            <span className="truncate max-w-[160px] sm:max-w-[200px] block">
                              {scorer.team_name}
                            </span>
                          </td>

                          {/* Group */}
                          <td className="py-3 px-3 text-center font-mono text-xs text-neutral-400">
                            {scorer.group_name.replace('Group ', '')}
                          </td>

                          {/* Matches Played */}
                          <td className="py-3 px-3 text-center font-mono text-xs text-neutral-300 tabular-nums">
                            {scorer.matches_played}
                          </td>

                          {/* Goals per Match */}
                          <td className="py-3 px-3 text-center font-mono text-xs text-neutral-400 tabular-nums hidden sm:table-cell">
                            {scorer.goals_per_match.toFixed(1)}
                          </td>

                          {/* Goals */}
                          <td className="py-3 px-4 text-center font-mono text-sm sm:text-base font-bold text-amber-400 tabular-nums">
                            {scorer.goals}
                          </td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>
            </div>
          )}
        </div>
      )}
    </section>
  );
};

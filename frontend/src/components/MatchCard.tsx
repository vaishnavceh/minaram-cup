import React from 'react';
import { PublicMatch } from '../types';
import { Calendar, MapPin, Trophy, Swords } from 'lucide-react';

interface MatchCardProps {
  match: PublicMatch;
  compact?: boolean;
}

export const MatchCard: React.FC<MatchCardProps> = ({ match, compact = false }) => {
  const isCompleted = match.status === 'COMPLETED';
  const isLive = match.status === 'IN_PROGRESS';

  const teamAWon = isCompleted && (
    (match.team_a_score ?? 0) > (match.team_b_score ?? 0) ||
    ((match.team_a_score ?? 0) === (match.team_b_score ?? 0) && (match.penalty_a ?? 0) > (match.penalty_b ?? 0))
  );

  const teamBWon = isCompleted && (
    (match.team_b_score ?? 0) > (match.team_a_score ?? 0) ||
    ((match.team_a_score ?? 0) === (match.team_b_score ?? 0) && (match.penalty_b ?? 0) > (match.penalty_a ?? 0))
  );

  const isDraw = isCompleted && (match.team_a_score ?? 0) === (match.team_b_score ?? 0) && match.penalty_a === null;

  return (
    <div className="bg-[#121212] border border-[#222222] rounded-lg overflow-hidden hover:border-[#383838] transition-all duration-200 group relative">
      {/* Accent top border when live or completed */}
      {isLive && <div className="absolute top-0 left-0 right-0 h-1 bg-brand-red animate-pulse" />}
      {isCompleted && <div className="absolute top-0 left-0 right-0 h-0.5 bg-neutral-700" />}

      {/* Header Info */}
      <div className="px-4 py-2.5 bg-black/40 border-b border-[#1c1c1c] flex items-center justify-between text-xs font-mono">
        <div className="flex items-center space-x-2 text-neutral-400">
          <span className="font-bold uppercase tracking-wider text-neutral-300">
            {match.stage}
          </span>
          {match.group_name && (
            <span className="text-neutral-400">· Group {match.group_name}</span>
          )}
          {match.match_number && (
            <span className="text-neutral-400">· M#{match.match_number}</span>
          )}
        </div>

        {/* Status Badge */}
        <div>
          {isLive ? (
            <span className="inline-flex items-center px-2 py-0.5 rounded text-[10px] font-bold bg-brand-red text-white uppercase tracking-wider animate-pulse">
              LIVE
            </span>
          ) : isCompleted ? (
            <span className="inline-flex items-center px-2 py-0.5 rounded text-[10px] font-medium bg-neutral-800 text-neutral-300 uppercase tracking-wider">
              FT
            </span>
          ) : (
            <span className="inline-flex items-center px-2 py-0.5 rounded text-[10px] font-medium bg-neutral-900 border border-neutral-700 text-neutral-400 uppercase tracking-wider">
              UPCOMING
            </span>
          )}
        </div>
      </div>

      {/* Match Body: Team A vs Team B */}
      <div className="p-4 sm:p-5">
        <div className="grid grid-cols-12 items-center gap-2">
          {/* Team A */}
          <div className="col-span-5 flex items-center space-x-3">
            <div className="w-9 h-9 rounded-full bg-neutral-900 border border-neutral-700 flex items-center justify-center font-display text-base text-white shrink-0 group-hover:border-neutral-500">
              {match.team_a_name ? match.team_a_name.substring(0, 2).toUpperCase() : 'TBD'}
            </div>
            <div className="min-w-0">
              <h4
                className={`font-semibold text-sm sm:text-base truncate ${
                  teamAWon ? 'text-white font-bold' : isCompleted ? 'text-neutral-400' : 'text-neutral-200'
                }`}
                title={match.team_a_name || 'TBD'}
              >
                {match.team_a_name || 'TBD'}
              </h4>
              {teamAWon && (
                <span className="text-[10px] font-mono text-emerald-400 flex items-center">
                  WINNER
                </span>
              )}
            </div>
          </div>

          {/* Center: Score or VS */}
          <div className="col-span-2 flex flex-col items-center justify-center">
            {isCompleted || isLive ? (
              <div className="text-center">
                <div className="font-display text-2xl sm:text-3xl text-white tracking-wider tabular-nums">
                  {match.team_a_score ?? 0} - {match.team_b_score ?? 0}
                </div>
                {(match.penalty_a !== null && match.penalty_b !== null) && (
                  <div className="text-[10px] font-mono text-neutral-400 tracking-wider">
                    ({match.penalty_a} - {match.penalty_b} pen)
                  </div>
                )}
              </div>
            ) : (
              <div className="w-8 h-8 rounded-full bg-neutral-900 border border-neutral-800 flex items-center justify-center text-xs font-mono font-bold text-neutral-400">
                VS
              </div>
            )}
          </div>

          {/* Team B */}
          <div className="col-span-5 flex items-center justify-end space-x-3 text-right">
            <div className="min-w-0 order-1">
              <h4
                className={`font-semibold text-sm sm:text-base truncate ${
                  teamBWon ? 'text-white font-bold' : isCompleted ? 'text-neutral-400' : 'text-neutral-200'
                }`}
                title={match.team_b_name || 'TBD'}
              >
                {match.team_b_name || 'TBD'}
              </h4>
              {teamBWon && (
                <span className="text-[10px] font-mono text-emerald-400 flex items-center justify-end">
                  WINNER
                </span>
              )}
            </div>
            <div className="w-9 h-9 rounded-full bg-neutral-900 border border-neutral-700 flex items-center justify-center font-display text-base text-white shrink-0 group-hover:border-neutral-500 order-2">
              {match.team_b_name ? match.team_b_name.substring(0, 2).toUpperCase() : 'TBD'}
            </div>
          </div>
        </div>
      </div>

      {/* Footer Info: Pitch & Time */}
      {!compact && (
        <div className="px-4 py-2 bg-black/60 border-t border-[#1a1a1a] flex items-center justify-between text-[11px] font-mono text-neutral-400">
          <div className="flex items-center space-x-1.5">
            <MapPin className="w-3 h-3 text-neutral-400" />
            <span>{match.pitch || 'Pitch 1 (eFootball Station)'}</span>
          </div>
          <div className="flex items-center space-x-1.5">
            <Calendar className="w-3 h-3 text-neutral-400" />
            <span>{match.scheduled_time || 'Scheduled'}</span>
          </div>
        </div>
      )}
    </div>
  );
};

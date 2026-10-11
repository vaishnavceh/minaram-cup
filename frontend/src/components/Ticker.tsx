import React from 'react';
import { Flame, Radio, Trophy } from 'lucide-react';
import { PublicMatch } from '../types';

interface TickerProps {
  recentMatches?: PublicMatch[];
  upcomingMatches?: PublicMatch[];
}

export const Ticker: React.FC<TickerProps> = ({ recentMatches = [], upcomingMatches = [] }) => {
  return (
    <div className="bg-black/90 border-y border-[#1f1f1f] text-neutral-300 py-2.5 overflow-hidden flex items-center select-none">
      <div className="flex items-center px-4 shrink-0 bg-brand-red text-white font-display text-sm tracking-widest uppercase z-10 py-1 clip-slanted pr-6 mr-3">
        <Flame className="w-3.5 h-3.5 mr-1.5 animate-pulse" />
        <span>LIVE PULSE</span>
      </div>

      <div className="flex whitespace-nowrap overflow-x-hidden font-mono text-xs">
        <div className="inline-flex items-center space-x-8 animate-marquee">
          {recentMatches.length > 0 ? (
            recentMatches.slice(0, 5).map((m) => (
              <span key={`rec-${m.id}`} className="inline-flex items-center space-x-2">
                <span className="text-neutral-400 font-sans font-bold uppercase">{m.stage}:</span>
                <span className="text-white font-semibold">{m.team_a_name || 'TBD'}</span>
                <span className="bg-neutral-800 text-brand-red px-1.5 py-0.5 rounded font-bold tabular-nums">
                  {m.team_a_score ?? 0} - {m.team_b_score ?? 0}
                </span>
                <span className="text-white font-semibold">{m.team_b_name || 'TBD'}</span>
                <span className="text-neutral-500">•</span>
              </span>
            ))
          ) : (
            <span className="text-neutral-400">
              MINARAM CUP eFootball Championship in progress • Live standings updated in real time •
            </span>
          )}

          {upcomingMatches.length > 0 ? (
            upcomingMatches.slice(0, 4).map((m) => (
              <span key={`up-${m.id}`} className="inline-flex items-center space-x-2">
                <span className="text-brand-gold uppercase font-sans font-bold">NEXT UP:</span>
                <span className="text-white">{m.team_a_name || 'TBD'} vs {m.team_b_name || 'TBD'}</span>
                <span className="text-neutral-400 text-[11px]">{m.pitch || 'Pitch 1'}</span>
                <span className="text-neutral-500">•</span>
              </span>
            ))
          ) : (
            <span className="text-neutral-400">
              Official TKM College Tournament • Powered by minarathintememe • Title Sponsor: AKHADHA •
            </span>
          )}
        </div>
      </div>
    </div>
  );
};

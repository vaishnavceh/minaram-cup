import React, { useState, useEffect } from 'react';
import { Flame, Radio, Trophy, Sparkles } from 'lucide-react';
import { PublicMatch } from '../types';
import { api } from '../api';
import { useLiveUpdates } from '../hooks/useLiveUpdates';

interface TickerProps {
  recentMatches?: PublicMatch[];
  upcomingMatches?: PublicMatch[];
}

export const Ticker: React.FC<TickerProps> = ({ recentMatches: propRecent = [], upcomingMatches: propUpcoming = [] }) => {
  const [recent, setRecent] = useState<PublicMatch[]>(propRecent);
  const [upcoming, setUpcoming] = useState<PublicMatch[]>(propUpcoming);

  const fetchTickerData = async () => {
    try {
      const [resData, fixData] = await Promise.all([
        api.getResults().catch(() => []),
        api.getFixtures().catch(() => []),
      ]);
      if (Array.isArray(resData) && resData.length > 0) {
        setRecent(resData.slice(-6).reverse());
      }
      if (Array.isArray(fixData) && fixData.length > 0) {
        const scheduled = fixData.filter((m) => m.status === 'SCHEDULED' || m.status === 'CONFIRMED');
        setUpcoming(scheduled.slice(0, 6));
      }
    } catch {
      // Ignore fallback
    }
  };

  useEffect(() => {
    if (propRecent.length === 0 && propUpcoming.length === 0) {
      fetchTickerData();
    } else {
      setRecent(propRecent);
      setUpcoming(propUpcoming);
    }
  }, [propRecent, propUpcoming]);

  useLiveUpdates((evt) => {
    const evType = evt.event || (evt as any).type;
    if (['result_updated', 'match_updated', 'knockout_updated', 'fixtures_status_updated'].includes(evType)) {
      fetchTickerData();
    }
  });

  return (
    <div className="bg-black/95 border-y border-blue-900/30 text-neutral-300 py-2.5 overflow-hidden flex items-center select-none shadow-[0_4px_20px_rgba(0,0,0,0.8)] backdrop-blur-md">
      <div className="flex items-center px-4 shrink-0 bg-gradient-to-r from-brand-red to-rose-700 text-white font-display text-sm tracking-widest uppercase z-10 py-1 clip-slanted pr-6 mr-3 shadow-glow-red">
        <Flame className="w-3.5 h-3.5 mr-1.5 animate-pulse text-amber-300" />
        <span>LIVE PULSE</span>
      </div>

      <div className="flex whitespace-nowrap overflow-x-hidden font-mono text-xs">
        <div className="inline-flex items-center space-x-8 animate-marquee">
          {recent.length > 0 ? (
            recent.map((m) => (
              <span key={`rec-${m.id}`} className="inline-flex items-center space-x-2">
                <span className="text-blue-400 font-sans font-bold uppercase text-[11px] tracking-wider px-1.5 py-0.5 rounded bg-blue-950/60 border border-blue-800/40">
                  {m.stage}
                </span>
                <span className="text-white font-semibold">{m.team_a_name || 'TBD'}</span>
                <span className="bg-neutral-900 border border-neutral-700/80 text-brand-red px-2 py-0.5 rounded font-bold tabular-nums shadow-sm">
                  {m.team_a_score ?? 0} - {m.team_b_score ?? 0}
                </span>
                <span className="text-white font-semibold">{m.team_b_name || 'TBD'}</span>
                <span className="text-neutral-600">•</span>
              </span>
            ))
          ) : (
            <span className="text-neutral-400">
              MINARAM CUP eFootball Championship in progress • Live standings updated in real time •
            </span>
          )}

          {upcoming.length > 0 ? (
            upcoming.map((m) => (
              <span key={`up-${m.id}`} className="inline-flex items-center space-x-2">
                <span className="text-amber-400 uppercase font-sans font-bold text-[11px] tracking-wider px-1.5 py-0.5 rounded bg-amber-950/60 border border-amber-800/40">
                  NEXT UP:
                </span>
                <span className="text-white font-medium">{m.team_a_name || 'TBD'}</span>
                <span className="text-neutral-500 font-bold">vs</span>
                <span className="text-white font-medium">{m.team_b_name || 'TBD'}</span>
                <span className="text-neutral-400 text-[11px] font-mono">[{m.pitch || 'Pitch 1'}]</span>
                <span className="text-neutral-600">•</span>
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

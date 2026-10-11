import React, { useEffect, useState } from 'react';
import { api } from '../api';
import { PublicGroupStandings } from '../types';
import { StandingsTable } from '../components/StandingsTable';
import { BarChart3, HelpCircle, ShieldCheck } from 'lucide-react';

export const StandingsPage: React.FC = () => {
  const [standings, setStandings] = useState<PublicGroupStandings[]>([]);
  const [loading, setLoading] = useState(true);

  const loadStandings = async () => {
    try {
      const data = await api.getStandings();
      setStandings(data);
    } catch (err) {
      console.error('Failed to load standings', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadStandings();
  }, []);

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
      {/* Header */}
      <div className="mb-10 pb-6 border-b border-[#222222]">
        <div className="flex items-center space-x-2 text-xs font-mono uppercase tracking-widest text-brand-red mb-2">
          <BarChart3 className="w-4 h-4" />
          <span>POINTS TABLES & RANKINGS</span>
        </div>
        <h1 className="font-display text-4xl sm:text-5xl text-white tracking-wider">
          GROUP STANDINGS
        </h1>
        <p className="text-sm text-neutral-400 mt-2 max-w-xl">
          Live group standings and points calculations. The top two teams from each group
          earn a direct ticket into the championship knockout quarter-finals.
        </p>
      </div>

      {/* Standings Grid */}
      {loading ? (
        <div className="text-center py-20 font-mono text-sm text-neutral-500">
          Calculating standings...
        </div>
      ) : (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          {(Array.isArray(standings) ? standings : []).map((grp) => (
            <StandingsTable key={grp.group_name} groupData={grp} />
          ))}
        </div>
      )}

      {/* Tie-breaker & Rules Callout */}
      <div className="mt-14 bg-[#121212] border border-[#222222] rounded-lg p-6 sm:p-8">
        <div className="flex items-center space-x-2 text-sm font-mono text-white mb-4">
          <HelpCircle className="w-4 h-4 text-brand-red" />
          <span className="font-bold uppercase tracking-wider">OFFICIAL TIE-BREAKER PROTOCOL</span>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4 text-xs font-mono text-neutral-400">
          <div className="bg-black/50 p-4 rounded border border-neutral-800">
            <span className="text-brand-red font-bold text-sm block mb-1">1. TOTAL POINTS</span>
            <span>Win: 3 points • Draw: 1 point • Loss: 0 points</span>
          </div>
          <div className="bg-black/50 p-4 rounded border border-neutral-800">
            <span className="text-brand-red font-bold text-sm block mb-1">2. GOAL DIFFERENCE</span>
            <span>Total goals scored minus total goals conceded (GD)</span>
          </div>
          <div className="bg-black/50 p-4 rounded border border-neutral-800">
            <span className="text-brand-red font-bold text-sm block mb-1">3. GOALS SCORED</span>
            <span>Highest total goals scored in all group matches (GF)</span>
          </div>
          <div className="bg-black/50 p-4 rounded border border-neutral-800">
            <span className="text-brand-red font-bold text-sm block mb-1">4. HEAD-TO-HEAD</span>
            <span>Direct match outcome between the tied teams</span>
          </div>
        </div>
      </div>
    </div>
  );
};

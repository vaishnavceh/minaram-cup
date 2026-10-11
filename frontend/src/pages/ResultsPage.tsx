import React, { useEffect, useState } from 'react';
import { api } from '../api';
import { PublicMatch } from '../types';
import { MatchCard } from '../components/MatchCard';
import { Trophy, CheckCircle, Search } from 'lucide-react';

export const ResultsPage: React.FC = () => {
  const [results, setResults] = useState<PublicMatch[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');

  const loadResults = async () => {
    try {
      const data = await api.getResults();
      setResults(data);
    } catch (err) {
      console.error('Failed to load results', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadResults();
  }, []);

  const filteredResults = results.filter((m) => {
    if (!searchTerm.trim()) return true;
    const q = searchTerm.toLowerCase();
    const a = (m.team_a_name || '').toLowerCase();
    const b = (m.team_b_name || '').toLowerCase();
    return a.includes(q) || b.includes(q);
  });

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
      {/* Header */}
      <div className="mb-10 pb-6 border-b border-[#222222] flex flex-col md:flex-row md:items-end justify-between gap-4">
        <div>
          <div className="flex items-center space-x-2 text-xs font-mono uppercase tracking-widest text-brand-red mb-2">
            <Trophy className="w-4 h-4" />
            <span>OFFICIAL SCORES</span>
          </div>
          <h1 className="font-display text-4xl sm:text-5xl text-white tracking-wider">
            MATCH RESULTS
          </h1>
          <p className="text-sm text-neutral-400 mt-2 max-w-xl">
            Official verified scores from completed matches in the Minaram Cup.
          </p>
        </div>

        {/* Search */}
        <div className="relative min-w-[240px]">
          <Search className="w-4 h-4 text-neutral-500 absolute left-3 top-2.5" />
          <input
            type="text"
            placeholder="Search by team..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="w-full pl-9 pr-3 py-1.5 bg-[#121212] border border-neutral-800 rounded text-xs font-mono text-white placeholder-neutral-600 focus:outline-none focus:border-brand-red"
          />
        </div>
      </div>

      {/* Results Grid */}
      {loading ? (
        <div className="text-center py-20 font-mono text-sm text-neutral-500">
          Loading results...
        </div>
      ) : filteredResults.length > 0 ? (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 sm:gap-6">
          {filteredResults.map((match) => (
            <MatchCard key={match.id} match={match} />
          ))}
        </div>
      ) : (
        <div className="p-12 text-center bg-[#111111] border border-[#222222] rounded-lg">
          <CheckCircle className="w-10 h-10 text-neutral-600 mx-auto mb-3" />
          <p className="text-sm font-mono text-neutral-400">
            No completed match results recorded yet.
          </p>
        </div>
      )}
    </div>
  );
};

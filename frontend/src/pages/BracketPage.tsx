import React, { useEffect, useState } from 'react';
import { api } from '../api';
import { PublicBracket } from '../types';
import { BracketTree } from '../components/BracketTree';
import { GitFork, Trophy } from 'lucide-react';

export const BracketPage: React.FC = () => {
  const [bracket, setBracket] = useState<PublicBracket>({ rounds: [] });
  const [loading, setLoading] = useState(true);

  const loadBracket = async () => {
    try {
      const data = await api.getBracket();
      setBracket(data);
    } catch (err) {
      console.error('Failed to load bracket', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadBracket();
  }, []);

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
      {/* Header */}
      <div className="mb-10 pb-6 border-b border-[#222222]">
        <div className="flex items-center space-x-2 text-xs font-mono uppercase tracking-widest text-brand-red mb-2">
          <GitFork className="w-4 h-4" />
          <span>ROAD TO THE TROPHY</span>
        </div>
        <h1 className="font-display text-4xl sm:text-5xl text-white tracking-wider">
          KNOCKOUT CHAMPIONSHIP
        </h1>
        <p className="text-sm text-neutral-400 mt-2 max-w-xl">
          Single-elimination playoff bracket featuring the top two qualified teams from each group.
          Quarter-Finals, Semi-Finals, and the Grand Final.
        </p>
      </div>

      {loading ? (
        <div className="text-center py-20 font-mono text-sm text-neutral-500">
          Loading tournament bracket...
        </div>
      ) : (
        <BracketTree bracket={bracket} />
      )}
    </div>
  );
};

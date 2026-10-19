import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { api } from '../api';
import { PublicTeam } from '../types';
import { Users, Search, ArrowRight, Shield } from 'lucide-react';

export const TeamsPage: React.FC = () => {
  const [teams, setTeams] = useState<PublicTeam[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');

  const loadTeams = async () => {
    try {
      const data = await api.getTeams();
      setTeams(data);
    } catch (err) {
      console.error('Failed to load teams', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadTeams();
  }, []);

  const filteredTeams = teams.filter((t) => {
    if (!searchTerm.trim()) return true;
    const q = searchTerm.toLowerCase();
    return (
      t.name.toLowerCase().includes(q) ||
      t.manager_name.toLowerCase().includes(q) ||
      t.department.toLowerCase().includes(q)
    );
  });

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
      {/* Header Banner */}
      <div className="mb-10 relative rounded-2xl overflow-hidden border border-blue-500/30 bg-gradient-to-r from-[#030d26] via-[#051336] to-[#020718] p-6 sm:p-8 shadow-2xl flex flex-col md:flex-row md:items-end justify-between gap-4">
        <div className="absolute right-0 top-0 bottom-0 w-full sm:w-2/3 opacity-25 sm:opacity-40 pointer-events-none">
          <img
            src="/assets/backgrounds/ucl_stadium_bg.jpg"
            alt="UEFA Champions League Stadium"
            className="w-full h-full object-cover object-center filter contrast-125"
          />
          <div className="absolute inset-0 bg-gradient-to-r from-[#030d26] via-[#030d26]/80 to-transparent" />
        </div>
        <div className="relative z-10">
          <div className="flex items-center space-x-2 text-xs font-mono uppercase tracking-widest text-blue-400 mb-2">
            <Users className="w-4 h-4 text-amber-400" />
            <span>PARTICIPATING SQUADS · UEFA STAGE</span>
          </div>
          <h1 className="font-display text-4xl sm:text-5xl text-white tracking-wider">
            TEAMS & MANAGERS
          </h1>
          <p className="text-sm text-blue-200/80 mt-2 max-w-xl">
            Official roster of all registered squads competing in the Minaram Cup.
            Click on any team to view their full tournament match history.
          </p>
        </div>

        {/* Search */}
        <div className="relative min-w-[260px]">
          <Search className="w-4 h-4 text-neutral-500 absolute left-3 top-2.5" />
          <input
            type="text"
            placeholder="Search squad, manager, branch..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="w-full pl-9 pr-3 py-1.5 bg-[#121212] border border-neutral-800 rounded text-xs font-mono text-white placeholder-neutral-600 focus:outline-none focus:border-brand-red"
          />
        </div>
      </div>

      {/* Teams Grid */}
      {loading ? (
        <div className="text-center py-20 font-mono text-sm text-neutral-500">
          Loading teams...
        </div>
      ) : filteredTeams.length > 0 ? (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {filteredTeams.map((team) => (
            <Link
              key={team.id}
              to={`/teams/${team.id}`}
              className="bg-[#121212] border border-[#222222] hover:border-[#383838] rounded-lg p-5 transition-all duration-200 group flex flex-col justify-between"
            >
              <div>
                {/* Team Top */}
                <div className="flex items-center justify-between mb-4">
                  <div className="w-12 h-12 rounded-full bg-neutral-900 border border-neutral-700 group-hover:border-brand-red flex items-center justify-center font-display text-lg text-white transition-colors">
                    {team.name.substring(0, 2).toUpperCase()}
                  </div>
                  <div className="text-right">
                    <span className="text-[10px] font-mono text-neutral-400 uppercase tracking-widest block">
                      {team.department || 'TKMCE'}
                    </span>
                    <span className="text-xs font-mono text-neutral-400">
                      Year {team.year || 'N/A'}
                    </span>
                  </div>
                </div>

                {/* Team & Manager */}
                <h3 className="font-display text-2xl text-white tracking-wide group-hover:text-brand-red transition-colors truncate">
                  {team.name}
                </h3>
                <p className="text-xs font-sans text-neutral-400 mt-1">
                  Manager: <strong className="text-neutral-300 font-medium">{team.manager_name}</strong>
                </p>
              </div>

              {/* Record & Stats */}
              <div className="mt-6 pt-4 border-t border-[#1a1a1a] flex items-center justify-between">
                <div className="flex items-center space-x-3 text-xs font-mono">
                  <span className="text-neutral-400">
                    P: <strong className="text-white">{team.matches_played}</strong>
                  </span>
                  <span className="text-neutral-400">
                    W: <strong className="text-emerald-400">{team.wins}</strong>
                  </span>
                  <span className="text-neutral-400">
                    D: <strong className="text-neutral-400">{team.draws}</strong>
                  </span>
                  <span className="text-neutral-400">
                    L: <strong className="text-rose-400">{team.losses}</strong>
                  </span>
                </div>
                <div className="flex items-center text-xs font-mono text-brand-red group-hover:translate-x-1 transition-transform">
                  <span className="font-bold mr-1">{team.points} PTS</span>
                  <ArrowRight className="w-3.5 h-3.5" />
                </div>
              </div>
            </Link>
          ))}
        </div>
      ) : (
        <div className="p-12 text-center bg-[#111111] border border-[#222222] rounded-lg">
          <p className="text-sm font-mono text-neutral-400">
            No teams match your search.
          </p>
        </div>
      )}
    </div>
  );
};

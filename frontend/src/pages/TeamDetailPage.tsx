import React, { useEffect, useState } from 'react';
import { useParams, Link } from 'react-router-dom';
import { api } from '../api';
import { TeamDetail } from '../types';
import { MatchCard } from '../components/MatchCard';
import { ArrowLeft, User, GraduationCap, Calendar, Trophy, BarChart2 } from 'lucide-react';

export const TeamDetailPage: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const [team, setTeam] = useState<TeamDetail | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!id) return;
    const fetchTeam = async () => {
      try {
        const data = await api.getTeamById(parseInt(id, 10));
        setTeam(data);
      } catch (err) {
        console.error('Failed to load team details', err);
      } finally {
        setLoading(false);
      }
    };
    fetchTeam();
  }, [id]);

  if (loading) {
    return (
      <div className="max-w-5xl mx-auto px-4 py-20 text-center font-mono text-sm text-neutral-500">
        Loading squad profile...
      </div>
    );
  }

  if (!team) {
    return (
      <div className="max-w-5xl mx-auto px-4 py-20 text-center">
        <h2 className="font-display text-3xl text-white">TEAM NOT FOUND</h2>
        <Link to="/teams" className="mt-4 inline-flex items-center text-sm font-mono text-brand-red">
          <ArrowLeft className="w-4 h-4 mr-1" /> Back to Teams Directory
        </Link>
      </div>
    );
  }

  return (
    <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
      {/* Back Link */}
      <Link
        to="/teams"
        className="inline-flex items-center space-x-2 text-xs font-mono uppercase tracking-widest text-neutral-400 hover:text-white mb-8 transition-colors"
      >
        <ArrowLeft className="w-4 h-4" />
        <span>BACK TO TEAMS DIRECTORY</span>
      </Link>

      {/* Team Header Profile */}
      <div className="bg-[#121212] border border-[#222222] rounded-xl p-6 sm:p-8 mb-10">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-6">
          <div className="flex items-center space-x-5">
            <div className="w-20 h-20 rounded-full bg-black border-2 border-neutral-700 flex items-center justify-center font-display text-3xl text-white shrink-0 shadow-lg">
              {team.name.substring(0, 2).toUpperCase()}
            </div>
            <div>
              <span className="text-xs font-mono uppercase tracking-widest text-brand-red font-bold">
                OFFICIAL SQUAD
              </span>
              <h1 className="font-display text-4xl sm:text-5xl text-white tracking-wide">
                {team.name}
              </h1>
              <div className="flex flex-wrap items-center gap-4 mt-2 text-xs font-mono text-neutral-400">
                <span className="flex items-center space-x-1.5">
                  <User className="w-3.5 h-3.5 text-neutral-400" />
                  <span>Manager: <strong className="text-white">{team.manager_name}</strong></span>
                </span>
                <span className="flex items-center space-x-1.5">
                  <GraduationCap className="w-3.5 h-3.5 text-neutral-400" />
                  <span>{team.department || 'TKMCE'} · Year {team.year || 'N/A'}</span>
                </span>
              </div>
            </div>
          </div>

          {/* Quick Record Box */}
          <div className="bg-black/60 border border-neutral-800 rounded-lg p-4 flex items-center space-x-6 text-center font-mono">
            <div>
              <span className="block text-2xl font-bold text-white tabular-nums">{team.matches_played}</span>
              <span className="text-[10px] text-neutral-400 uppercase">Played</span>
            </div>
            <div>
              <span className="block text-2xl font-bold text-emerald-400 tabular-nums">{team.wins}</span>
              <span className="text-[10px] text-neutral-400 uppercase">Won</span>
            </div>
            <div>
              <span className="block text-2xl font-bold text-neutral-400 tabular-nums">{team.draws}</span>
              <span className="text-[10px] text-neutral-400 uppercase">Drawn</span>
            </div>
            <div>
              <span className="block text-2xl font-bold text-rose-400 tabular-nums">{team.losses}</span>
              <span className="text-[10px] text-neutral-400 uppercase">Lost</span>
            </div>
            <div className="border-l border-neutral-700 pl-4">
              <span className="block text-3xl font-display text-brand-red tabular-nums">{team.points}</span>
              <span className="text-[10px] text-neutral-400 uppercase">Points</span>
            </div>
          </div>
        </div>
      </div>

      {/* Match History */}
      <div>
        <div className="flex items-center space-x-2 text-xs font-mono uppercase tracking-widest text-brand-red mb-2">
          <Trophy className="w-4 h-4" />
          <span>FIXTURES & RESULTS</span>
        </div>
        <h2 className="font-display text-3xl text-white tracking-wider mb-6">
          SQUAD MATCH SCHEDULE
        </h2>

        {team.recent_matches && team.recent_matches.length > 0 ? (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {team.recent_matches.map((m) => (
              <MatchCard key={m.id} match={m} />
            ))}
          </div>
        ) : (
          <div className="p-8 bg-[#111111] border border-[#222222] rounded-lg text-center font-mono text-sm text-neutral-400">
            No matches scheduled or recorded for this team yet.
          </div>
        )}
      </div>
    </div>
  );
};

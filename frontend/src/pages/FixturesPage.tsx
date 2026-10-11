import React, { useEffect, useState } from 'react';
import { api } from '../api';
import { PublicMatch } from '../types';
import { MatchCard } from '../components/MatchCard';
import { Calendar, Filter, Search } from 'lucide-react';

export const FixturesPage: React.FC = () => {
  const [fixtures, setFixtures] = useState<PublicMatch[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedStage, setSelectedStage] = useState<string>('ALL');
  const [selectedGroup, setSelectedGroup] = useState<string>('ALL');
  const [selectedMatchweek, setSelectedMatchweek] = useState<string>('ALL');
  const [searchTerm, setSearchTerm] = useState<string>('');

  const loadFixtures = async () => {
    try {
      const data = await api.getFixtures();
      setFixtures(data);
    } catch (err) {
      console.error('Failed to load fixtures', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadFixtures();
  }, []);

  const normalizeStageKey = (s?: string | null): string => {
    if (!s) return '';
    return s.toUpperCase().replace(/[\s-]+/g, '_').trim();
  };

  const normalizeGroupKey = (g?: string | null): string => {
    if (!g) return '';
    return g.toUpperCase().replace(/^GROUP\s*/i, '').trim();
  };

  const availableGroups = React.useMemo(() => {
    const set = new Set<string>();
    fixtures.forEach((m) => {
      if (m.group_name) {
        const clean = normalizeGroupKey(m.group_name);
        if (clean) set.add(clean);
      }
    });
    const sorted = Array.from(set).sort((a, b) => a.localeCompare(b, undefined, { numeric: true }));
    return ['ALL', ...sorted];
  }, [fixtures]);

  const availableMatchweeks = React.useMemo(() => {
    const set = new Set<number>();
    fixtures.forEach((m) => {
      if (m.round_number && m.round_number > 0) {
        set.add(m.round_number);
      }
    });
    const sorted = Array.from(set).sort((a, b) => a - b);
    return ['ALL', ...sorted.map(String)];
  }, [fixtures]);

  const stages = [
    { key: 'ALL', label: 'ALL STAGES' },
    { key: 'GROUP_STAGE', label: 'GROUP STAGE' },
    { key: 'QUARTER_FINAL', label: 'QUARTER-FINAL' },
    { key: 'SEMI_FINAL', label: 'SEMI-FINAL' },
    { key: 'FINAL', label: 'FINAL' },
  ];

  const filteredMatches = fixtures.filter((m) => {
    if (selectedStage !== 'ALL') {
      const stageKey = normalizeStageKey(m.stage);
      if (stageKey !== selectedStage) {
        return false;
      }
    }
    if (selectedMatchweek !== 'ALL') {
      if (String(m.round_number) !== selectedMatchweek) {
        return false;
      }
    }
    if (selectedGroup !== 'ALL') {
      const matchGrp = normalizeGroupKey(m.group_name);
      const selGrp = normalizeGroupKey(selectedGroup);
      if (matchGrp !== selGrp) {
        return false;
      }
    }
    if (searchTerm.trim()) {
      const query = searchTerm.toLowerCase();
      const a = (m.team_a_name || '').toLowerCase();
      const b = (m.team_b_name || '').toLowerCase();
      if (!a.includes(query) && !b.includes(query)) {
        return false;
      }
    }
    return true;
  });

  const sortedMatches = [...filteredMatches].sort((a, b) => {
    if (a.match_number && b.match_number) {
      return a.match_number - b.match_number;
    }
    return (a.scheduled_time || '').localeCompare(b.scheduled_time || '');
  });

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
      {/* Header */}
      <div className="mb-10 pb-6 border-b border-[#222222]">
        <div className="flex items-center space-x-2 text-xs font-mono uppercase tracking-widest text-brand-red mb-2">
          <Calendar className="w-4 h-4" />
          <span>SCHEDULE & ROUNDS</span>
        </div>
        <h1 className="font-display text-4xl sm:text-5xl text-white tracking-wider">
          TOURNAMENT FIXTURES
        </h1>
        <p className="text-sm text-neutral-400 mt-2 max-w-xl">
          Complete match schedule across all groups and championship knockout phases.
          All times and pitch allocations are updated live from the tournament desk.
        </p>
      </div>

      {/* Filter Toolbar */}
      <div className="bg-[#121212] border border-[#222222] rounded-lg p-4 mb-8 space-y-4">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          {/* Stage Filter */}
          <div className="flex flex-wrap items-center gap-1.5">
            <span className="text-xs font-mono text-neutral-400 mr-2 flex items-center">
              <Filter className="w-3.5 h-3.5 mr-1" /> STAGE:
            </span>
            {stages.map((st) => (
              <button
                key={st.key}
                onClick={() => setSelectedStage(st.key)}
                className={`px-3 py-1 rounded text-xs font-mono uppercase transition-colors ${
                  selectedStage === st.key
                    ? 'bg-brand-red text-white font-bold'
                    : 'bg-black/40 text-neutral-400 hover:text-white hover:bg-neutral-800'
                }`}
              >
                {st.label}
              </button>
            ))}
          </div>

          {/* Search Box */}
          <div className="relative min-w-[200px]">
            <Search className="w-4 h-4 text-neutral-500 absolute left-3 top-2.5" />
            <input
              type="text"
              placeholder="Search team..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="w-full pl-9 pr-3 py-1.5 bg-black/60 border border-neutral-800 rounded text-xs font-mono text-white placeholder-neutral-600 focus:outline-none focus:border-brand-red"
            />
          </div>
        </div>

        {/* Matchweek Filter */}
        {availableMatchweeks.length > 2 && (
          <div className="flex flex-wrap items-center gap-1.5 pt-2 border-t border-neutral-800/60">
            <span className="text-xs font-mono text-neutral-400 mr-2">MATCHWEEK:</span>
            {availableMatchweeks.map((mw) => (
              <button
                key={mw}
                onClick={() => setSelectedMatchweek(mw)}
                className={`px-2.5 py-0.5 rounded text-xs font-mono transition-colors ${
                  selectedMatchweek === mw
                    ? 'bg-brand-red text-white font-bold'
                    : 'bg-black/40 text-neutral-400 hover:text-white hover:bg-neutral-800'
                }`}
              >
                {mw === 'ALL' ? 'ALL MATCHWEEKS' : `MW ${mw}`}
              </button>
            ))}
          </div>
        )}

        {/* Group Filter (when stage is ALL or GROUP_STAGE) */}
        {(selectedStage === 'ALL' || selectedStage === 'GROUP_STAGE') && (
          <div className="flex flex-wrap items-center gap-1.5 pt-2 border-t border-neutral-800/60">
            <span className="text-xs font-mono text-neutral-400 mr-2">GROUP:</span>
            {availableGroups.map((grp) => (
              <button
                key={grp}
                onClick={() => setSelectedGroup(grp)}
                className={`px-2.5 py-0.5 rounded text-xs font-mono transition-colors ${
                  selectedGroup === grp
                    ? 'bg-neutral-700 text-white font-bold'
                    : 'text-neutral-500 hover:text-neutral-300'
                }`}
              >
                {grp === 'ALL' ? 'ALL GROUPS' : `GROUP ${grp}`}
              </button>
            ))}
          </div>
        )}
      </div>

      {/* Fixtures Grid */}
      {loading ? (
        <div className="text-center py-20 font-mono text-sm text-neutral-500">
          Loading fixtures...
        </div>
      ) : sortedMatches.length > 0 ? (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 sm:gap-6">
          {sortedMatches.map((match) => (
            <MatchCard key={match.id} match={match} />
          ))}
        </div>
      ) : (
        <div className="p-12 text-center bg-[#111111] border border-[#222222] rounded-lg">
          <p className="text-sm font-mono text-neutral-400">
            No matches match the selected criteria.
          </p>
        </div>
      )}
    </div>
  );
};

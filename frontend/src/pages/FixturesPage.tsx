import React, { useEffect, useState } from 'react';
import { api } from '../api';
import { PublicMatch } from '../types';
import { MatchCard } from '../components/MatchCard';
import { Calendar, Filter, Search, Clock, Shield, ChevronDown, ChevronUp } from 'lucide-react';
import { Link } from 'react-router-dom';
import { getMatchTimeline } from '../utils/fixtureDates';
import { useLiveUpdates } from '../hooks/useLiveUpdates';

export const FixturesPage: React.FC = () => {
  const [fixtures, setFixtures] = useState<PublicMatch[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedStage, setSelectedStage] = useState<string>('ALL');
  const [selectedGroup, setSelectedGroup] = useState<string>('ALL');
  const [selectedMatchweek, setSelectedMatchweek] = useState<string>('ALL');
  const [searchTerm, setSearchTerm] = useState<string>('');
  const [showFixtureRules, setShowFixtureRules] = useState<boolean>(false);

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

  useLiveUpdates((evt) => {
    const evType = evt.event || (evt as any).type;
    if (['fixtures_updated', 'match_updated', 'result_updated', 'knockout_updated', 'fixtures_status_updated'].includes(evType)) {
      loadFixtures();
    }
  });

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

  const matchweekTimelineMap = React.useMemo(() => {
    const map = new Map<string, { start: string; end: string }>();
    fixtures.forEach((m) => {
      if (m.round_number) {
        const mwKey = String(m.round_number);
        if (!map.has(mwKey)) {
          const tl = getMatchTimeline(m);
          if (tl.hasDates) {
            map.set(mwKey, {
              start: tl.startDateFormatted,
              end: tl.endDateFormatted,
            });
          }
        }
      }
    });
    return map;
  }, [fixtures]);

  const stages = [
    { key: 'ALL', label: 'ALL STAGES' },
    { key: 'GROUP_STAGE', label: 'GROUP STAGE' },
    { key: 'PRELIMINARY_ROUND', label: 'PRELIMINARY (14)' },
    { key: 'ROUND_OF_16', label: 'ROUND OF 16 (8)' },
    { key: 'QUARTER_FINAL', label: 'QUARTER-FINAL (4)' },
    { key: 'SEMI_FINAL', label: 'SEMI-FINAL (2)' },
    { key: 'FINAL', label: 'FINAL' },
  ];

  const filteredMatches = fixtures.filter((m) => {
    if (selectedStage !== 'ALL') {
      const stageKey = normalizeStageKey(m.stage);
      if (selectedStage === 'PRELIMINARY_ROUND') {
        if (!stageKey.includes('PRELIMINARY')) return false;
      } else if (selectedStage === 'ROUND_OF_16') {
        if (!stageKey.includes('16') && !stageKey.includes('RO16')) return false;
      } else if (stageKey !== selectedStage) {
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
      {/* Header Banner */}
      <div className="mb-10 relative rounded-2xl overflow-hidden border border-blue-500/30 bg-gradient-to-r from-[#030d26] via-[#051336] to-[#020718] p-6 sm:p-8 shadow-2xl">
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
            <Calendar className="w-4 h-4 text-amber-400" />
            <span>SCHEDULE & ROUNDS · UEFA STAGE</span>
          </div>
          <h1 className="font-display text-4xl sm:text-5xl text-white tracking-wider">
            TOURNAMENT FIXTURES
          </h1>
          <p className="text-sm text-blue-200/80 mt-2 max-w-xl">
            Complete match schedule across all groups and championship knockout phases.
            All times and pitch allocations are updated live from the tournament desk.
          </p>
        </div>
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
            {availableMatchweeks.map((mw) => {
              const tl = mw !== 'ALL' ? matchweekTimelineMap.get(mw) : null;
              return (
                <button
                  key={mw}
                  onClick={() => setSelectedMatchweek(mw)}
                  className={`px-2.5 py-1 rounded text-xs font-mono transition-colors flex items-center space-x-1.5 ${
                    selectedMatchweek === mw
                      ? 'bg-brand-red text-white font-bold'
                      : 'bg-black/40 text-neutral-400 hover:text-white hover:bg-neutral-800'
                  }`}
                >
                  <span>{mw === 'ALL' ? 'ALL MATCHWEEKS' : `MW ${mw}`}</span>
                  {tl && (
                    <span className="text-[10px] opacity-80 hidden sm:inline">
                      ({tl.start} – {tl.end})
                    </span>
                  )}
                </button>
              );
            })}
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

      {/* Active Timeline & Rules Info Banner */}
      <div className="bg-[#121212] border border-[#222222] rounded-lg p-4 sm:p-5 mb-8">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div className="space-y-1">
            <div className="flex items-center space-x-2 text-[11px] font-mono uppercase tracking-wider text-neutral-400">
              <Clock className="w-3.5 h-3.5 text-brand-red" />
              <span>
                {selectedMatchweek === 'ALL'
                  ? 'FLEXIBLE MATCHWEEK PLAYING WINDOWS'
                  : `MATCHWEEK ${selectedMatchweek} PLAYING TIMELINE`}
              </span>
            </div>
            <div className="text-sm sm:text-base text-neutral-200">
              {selectedMatchweek !== 'ALL' && matchweekTimelineMap.has(selectedMatchweek) ? (
                <span>
                  Playing Window: <strong className="text-white">{matchweekTimelineMap.get(selectedMatchweek)?.start}</strong> to{' '}
                  <strong className="text-white">{matchweekTimelineMap.get(selectedMatchweek)?.end}</strong> ·{' '}
                  <span className="text-brand-red font-bold">
                    Last Day of Playing: {matchweekTimelineMap.get(selectedMatchweek)?.end}
                  </span>
                </span>
              ) : (
                <span>
                  Each fixture features a 3-day flexible window. All 10-minute mobile matches must be completed by the{' '}
                  <span className="text-brand-red font-bold">Last Day of Playing</span> listed on each match card.
                </span>
              )}
            </div>
          </div>

          <div className="flex items-center space-x-2 shrink-0 self-start md:self-auto">
            <button
              type="button"
              onClick={() => setShowFixtureRules(!showFixtureRules)}
              className="flex items-center space-x-1.5 text-xs font-mono px-3 py-1.5 rounded bg-brand-red/10 border border-brand-red/40 text-brand-red hover:bg-brand-red hover:text-white transition-colors"
            >
              <Shield className="w-3.5 h-3.5" />
              <span>{showFixtureRules ? 'HIDE RULES' : 'FIXTURE RULES'}</span>
              {showFixtureRules ? <ChevronUp className="w-3.5 h-3.5 ml-1" /> : <ChevronDown className="w-3.5 h-3.5 ml-1" />}
            </button>
            <div className="hidden sm:flex items-center space-x-2 text-xs font-mono text-neutral-400 bg-black/60 border border-neutral-800 rounded px-3 py-1.5">
              <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />
              <span>10-Min Mobile Match</span>
            </div>
          </div>
        </div>

        {/* Collapsible Fixture Rules Quick Reference */}
        {showFixtureRules && (
          <div className="mt-4 pt-4 border-t border-[#222222] space-y-3 font-sans">
            <div className="flex items-center justify-between">
              <span className="text-xs font-mono font-bold text-white uppercase tracking-wider flex items-center gap-1.5">
                <Shield className="w-3.5 h-3.5 text-brand-red" />
                OFFICIAL FIXTURE & WALKOVER DIRECTIVES
              </span>
              <Link to="/rules" className="text-[11px] font-mono text-brand-red hover:underline">
                Full Rulebook ➔
              </Link>
            </div>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-2.5 text-xs">
              <div className="bg-black/50 p-3 rounded border border-neutral-800">
                <span className="text-[10px] font-mono font-bold text-brand-red block mb-1">
                  1. POINTS SYSTEM
                </span>
                <span className="text-neutral-300">
                  Win: <strong>3 pts</strong> · Draw: <strong>1 pt</strong> · Loss: <strong>0 pts</strong>
                </span>
              </div>
              <div className="bg-black/50 p-3 rounded border border-brand-red/30">
                <span className="text-[10px] font-mono font-bold text-brand-red block mb-1">
                  2. ONE TEAM FAILS TO PLAY
                </span>
                <span className="text-neutral-300">
                  Opponent awarded <strong className="text-white">3–0 walkover</strong> and receives <strong className="text-emerald-400">3 points</strong>.
                </span>
              </div>
              <div className="bg-black/50 p-3 rounded border border-neutral-800">
                <span className="text-[10px] font-mono font-bold text-amber-400 block mb-1">
                  3. BOTH TEAMS FAIL TO PLAY
                </span>
                <span className="text-neutral-300">
                  Recorded as <strong className="text-white">0–0</strong>, both teams receive <strong className="text-amber-400">1 point each</strong>.
                </span>
              </div>
              <div className="bg-black/50 p-3 rounded border border-neutral-800">
                <span className="text-[10px] font-mono font-bold text-neutral-300 block mb-1">
                  4. WALKOVER CLAIMS
                </span>
                <span className="text-neutral-300">
                  Contact admins <em>only after deadline has passed</em> with proof.
                </span>
              </div>
              <div className="bg-black/50 p-3 rounded border border-neutral-800">
                <span className="text-[10px] font-mono font-bold text-neutral-300 block mb-1">
                  5. DEADLINE
                </span>
                <span className="text-neutral-300">
                  All matches must finish by deadline. Teams coordinate proactively.
                </span>
              </div>
            </div>

            <div className="flex flex-col sm:flex-row items-center justify-between gap-3 pt-2 bg-black/40 p-3 rounded border border-neutral-800 text-xs">
              <div className="text-neutral-300">
                <span className="font-bold text-white">Need to report an issue or coordinate?</span> Each fixture card provides direct captain WhatsApp links. To submit walkover proof or dispute a deadline breach, contact tournament desk.
              </div>
              <a
                href="https://wa.me/919746603975"
                target="_blank"
                rel="noopener noreferrer"
                className="inline-flex items-center space-x-1.5 px-3 py-1.5 rounded bg-emerald-950/80 hover:bg-emerald-900 border border-emerald-700/60 text-emerald-400 font-bold font-mono text-xs shrink-0 transition-colors"
              >
                <span>Raise Complaint / Walkover Claim ➔</span>
              </a>
            </div>
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

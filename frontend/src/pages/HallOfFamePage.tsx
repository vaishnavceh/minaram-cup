import React, { useState, useMemo } from 'react';
import { HALL_OF_FAME_PLAYERS, HallOfFamePlayer } from '../data/hallOfFamePlayers';
import { PlayerCard } from '../components/hall-of-fame/PlayerCard';
import { PlayerDetailsModal } from '../components/hall-of-fame/PlayerDetailsModal';
import { FeaturedLegendBanner } from '../components/hall-of-fame/FeaturedLegendBanner';
import {
  Search,
  X,
  Filter,
  RotateCcw,
  Sparkles,
  Trophy,
  Users,
  Shield,
  Award,
  ChevronDown,
} from 'lucide-react';

export const HallOfFamePage: React.FC = () => {
  // Search & Filter States
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedPosition, setSelectedPosition] = useState<string>('All');
  const [selectedNationality, setSelectedNationality] = useState<string>('All');
  const [selectedEra, setSelectedEra] = useState<string>('All');
  const [selectedRetirementYear, setSelectedRetirementYear] = useState<string>('All');
  const [selectedIntRetirement, setSelectedIntRetirement] = useState<string>('All');
  const [selectedClubRetirement, setSelectedClubRetirement] = useState<string>('All');

  // Modal State
  const [activePlayer, setActivePlayer] = useState<HallOfFamePlayer | null>(null);

  // Dynamic filter option lists derived directly from player dataset
  const allNationalities = useMemo(() => {
    const nats = Array.from(new Set(HALL_OF_FAME_PLAYERS.map((p) => p.nationality))).sort();
    return ['All', ...nats];
  }, []);

  const allRetirementYears = useMemo(() => {
    const years = Array.from(
      new Set(
        HALL_OF_FAME_PLAYERS.map((p) => p.retirementYear)
          .filter((y): y is number => y !== null)
      )
    ).sort((a, b) => b - a);
    return ['All', ...years.map(String)];
  }, []);

  const featuredLegends = useMemo(() => {
    return HALL_OF_FAME_PLAYERS.filter((p) => p.isFeatured);
  }, []);

  // Position categories with live counts
  const positionCategories = [
    { label: 'All Positions', value: 'All' },
    { label: 'Forwards', value: 'Forward' },
    { label: 'Midfielders', value: 'Midfielder' },
    { label: 'Defenders', value: 'Defender' },
    { label: 'Goalkeepers', value: 'Goalkeeper' },
  ];

  const eraOptions = ['All', '1990s', '2000s', '2010s', '2020s'];

  // Check if any filter is active
  const hasActiveFilters =
    searchQuery.trim() !== '' ||
    selectedPosition !== 'All' ||
    selectedNationality !== 'All' ||
    selectedEra !== 'All' ||
    selectedRetirementYear !== 'All' ||
    selectedIntRetirement !== 'All' ||
    selectedClubRetirement !== 'All';

  const handleResetFilters = () => {
    setSearchQuery('');
    setSelectedPosition('All');
    setSelectedNationality('All');
    setSelectedEra('All');
    setSelectedRetirementYear('All');
    setSelectedIntRetirement('All');
    setSelectedClubRetirement('All');
  };

  // Real-time multi-dimensional filter logic
  const filteredPlayers = useMemo(() => {
    const query = searchQuery.trim().toLowerCase();

    return HALL_OF_FAME_PLAYERS.filter((player) => {
      // 1. Position filter
      if (selectedPosition !== 'All' && player.position !== selectedPosition) {
        return false;
      }

      // 2. Nationality filter
      if (selectedNationality !== 'All' && player.nationality !== selectedNationality) {
        return false;
      }

      // 3. Era filter
      if (selectedEra !== 'All' && !player.era.includes(selectedEra)) {
        return false;
      }

      // 4. Retirement Year filter
      if (
        selectedRetirementYear !== 'All' &&
        (!player.retirementYear || String(player.retirementYear) !== selectedRetirementYear)
      ) {
        return false;
      }

      // 5. International Retirement filter
      if (
        selectedIntRetirement !== 'All' &&
        player.internationalRetirementStatus !== selectedIntRetirement
      ) {
        return false;
      }

      // 6. Club Retirement filter
      if (
        selectedClubRetirement !== 'All' &&
        player.clubRetirementStatus !== selectedClubRetirement
      ) {
        return false;
      }

      // 7. Full-text search
      if (query) {
        const matchesName = player.name.toLowerCase().includes(query);
        const matchesNat = player.nationality.toLowerCase().includes(query);
        const matchesPos = player.position.toLowerCase().includes(query);
        const matchesDetailedPos = player.detailedPosition.toLowerCase().includes(query);
        const matchesEra = player.era.toLowerCase().includes(query);
        const matchesClubs = player.famousClubs.some((c) => c.toLowerCase().includes(query));
        const matchesYear = player.retirementYear && String(player.retirementYear).includes(query);

        if (
          !matchesName &&
          !matchesNat &&
          !matchesPos &&
          !matchesDetailedPos &&
          !matchesEra &&
          !matchesClubs &&
          !matchesYear
        ) {
          return false;
        }
      }

      return true;
    });
  }, [
    searchQuery,
    selectedPosition,
    selectedNationality,
    selectedEra,
    selectedRetirementYear,
    selectedIntRetirement,
    selectedClubRetirement,
  ]);

  return (
    <div className="min-h-screen bg-[#04060B] text-editorial-white pb-24">
      {/* Background Ambience */}
      <div className="fixed inset-0 pointer-events-none z-0">
        <div className="absolute top-0 left-1/2 -translate-x-1/2 w-full max-w-7xl h-[600px] bg-gradient-to-b from-amber-500/10 via-transparent to-transparent blur-3xl opacity-60" />
        <div className="absolute top-1/3 right-0 w-96 h-96 bg-rose-500/5 rounded-full blur-[140px]" />
        <div className="absolute bottom-1/4 left-0 w-96 h-96 bg-sky-500/5 rounded-full blur-[140px]" />
      </div>

      <div className="relative z-10 max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 pt-10 sm:pt-14">
        {/* Hall of Fame Header */}
        <header className="text-center max-w-4xl mx-auto space-y-4 mb-10">
          <div className="inline-flex items-center space-x-2 px-4 py-1.5 rounded-full bg-amber-950/60 border border-amber-400/50 text-xs font-mono text-amber-300 uppercase tracking-widest backdrop-blur-md shadow-[0_0_25px_rgba(212,175,55,0.25)]">
            <Trophy className="w-3.5 h-3.5 text-amber-400" />
            <span className="font-bold text-white">THE SACRED PANTHEON</span>
            <span className="w-1.5 h-1.5 rounded-full bg-amber-400" />
            <span className="text-amber-400 font-bold">{HALL_OF_FAME_PLAYERS.length} IMMORTAL LEGENDS</span>
          </div>

          <h1 className="font-display text-5xl sm:text-7xl md:text-8xl tracking-tight text-white uppercase leading-[0.92] drop-shadow-2xl">
            FOOTBALL HALL OF FAME
          </h1>

          <p className="text-base sm:text-xl text-neutral-300 font-normal leading-relaxed max-w-2xl mx-auto">
            Celebrating the greatest footballers who defined generations.
          </p>
        </header>

        {/* Featured Legend Spotlight Section */}
        <FeaturedLegendBanner
          featuredPlayers={featuredLegends}
          onSelectPlayer={(p) => setActivePlayer(p)}
        />

        {/* Search & Comprehensive Filter Controls Bar */}
        <section className="mb-10 space-y-5 rounded-2xl bg-[#080D18]/90 border border-white/10 p-5 sm:p-7 backdrop-blur-xl shadow-[0_10px_35px_rgba(0,0,0,0.6)]">
          {/* Top Controls: Search Bar & Reset Button */}
          <div className="flex flex-col sm:flex-row items-center gap-3.5">
            {/* Real-time Search Input */}
            <div className="relative flex-grow w-full">
              <Search className="absolute left-4 top-1/2 -translate-y-1/2 w-4 h-4 text-neutral-400" />
              <input
                type="text"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                placeholder="Search by player name, country, famous club, era (e.g. Zidane, Real Madrid, 2000s)..."
                className="w-full pl-11 pr-10 py-3 rounded-xl bg-black/60 border border-white/15 focus:border-amber-400/70 focus:outline-none focus:ring-1 focus:ring-amber-400/70 text-sm text-white placeholder-neutral-500 font-mono transition-all"
              />
              {searchQuery && (
                <button
                  type="button"
                  onClick={() => setSearchQuery('')}
                  aria-label="Clear search input"
                  className="absolute right-3.5 top-1/2 -translate-y-1/2 text-neutral-400 hover:text-white p-1"
                >
                  <X className="w-4 h-4" />
                </button>
              )}
            </div>

            {/* Reset Filters Button */}
            {hasActiveFilters && (
              <button
                type="button"
                onClick={handleResetFilters}
                className="w-full sm:w-auto px-4 py-3 rounded-xl bg-neutral-900 hover:bg-neutral-800 border border-amber-400/40 text-amber-300 font-mono text-xs uppercase tracking-wider flex items-center justify-center space-x-2 transition-all cursor-pointer shrink-0"
              >
                <RotateCcw className="w-3.5 h-3.5" />
                <span>RESET ALL FILTERS</span>
              </button>
            )}
          </div>

          {/* Primary Position Filter Chips */}
          <div className="flex flex-wrap items-center gap-2 pt-1 border-t border-white/5">
            <span className="text-xs font-mono text-neutral-400 uppercase tracking-wider mr-1 hidden sm:inline">
              Position:
            </span>
            {positionCategories.map((cat) => {
              const isSelected = selectedPosition === cat.value;
              return (
                <button
                  key={cat.value}
                  type="button"
                  onClick={() => setSelectedPosition(cat.value)}
                  className={`px-3.5 py-1.5 rounded-lg text-xs font-mono font-semibold uppercase tracking-wider transition-all cursor-pointer border ${
                    isSelected
                      ? 'bg-amber-400 text-black border-amber-300 shadow-[0_0_15px_rgba(212,175,55,0.4)]'
                      : 'bg-black/40 text-neutral-300 border-white/10 hover:border-white/30 hover:text-white'
                  }`}
                >
                  {cat.label}
                </button>
              );
            })}
          </div>

          {/* Secondary Filter Dropdowns: Nationality, Era, Retirement Year, Retirement Status */}
          <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-5 gap-3 pt-2">
            {/* Nationality Filter */}
            <div className="space-y-1">
              <label className="text-[10px] font-mono text-neutral-400 uppercase tracking-wider block">
                Nationality
              </label>
              <div className="relative">
                <select
                  value={selectedNationality}
                  onChange={(e) => setSelectedNationality(e.target.value)}
                  className="w-full appearance-none px-3 py-2 pr-8 rounded-lg bg-black/60 border border-white/15 text-xs font-mono text-white focus:outline-none focus:border-amber-400 cursor-pointer"
                >
                  <option value="All">All Nations</option>
                  {allNationalities.filter((n) => n !== 'All').map((nat) => (
                    <option key={nat} value={nat}>
                      {nat}
                    </option>
                  ))}
                </select>
                <ChevronDown className="absolute right-2.5 top-1/2 -translate-y-1/2 w-3.5 h-3.5 text-neutral-400 pointer-events-none" />
              </div>
            </div>

            {/* Era Filter */}
            <div className="space-y-1">
              <label className="text-[10px] font-mono text-neutral-400 uppercase tracking-wider block">
                Era Decade
              </label>
              <div className="relative">
                <select
                  value={selectedEra}
                  onChange={(e) => setSelectedEra(e.target.value)}
                  className="w-full appearance-none px-3 py-2 pr-8 rounded-lg bg-black/60 border border-white/15 text-xs font-mono text-white focus:outline-none focus:border-amber-400 cursor-pointer"
                >
                  <option value="All">All Eras</option>
                  <option value="1990s">1990s</option>
                  <option value="2000s">2000s</option>
                  <option value="2010s">2010s</option>
                  <option value="2020s">2020s</option>
                </select>
                <ChevronDown className="absolute right-2.5 top-1/2 -translate-y-1/2 w-3.5 h-3.5 text-neutral-400 pointer-events-none" />
              </div>
            </div>

            {/* Retirement Year Filter */}
            <div className="space-y-1">
              <label className="text-[10px] font-mono text-neutral-400 uppercase tracking-wider block">
                Retirement Year
              </label>
              <div className="relative">
                <select
                  value={selectedRetirementYear}
                  onChange={(e) => setSelectedRetirementYear(e.target.value)}
                  className="w-full appearance-none px-3 py-2 pr-8 rounded-lg bg-black/60 border border-white/15 text-xs font-mono text-white focus:outline-none focus:border-amber-400 cursor-pointer"
                >
                  <option value="All">All Years</option>
                  {allRetirementYears.filter((y) => y !== 'All').map((year) => (
                    <option key={year} value={year}>
                      {year}
                    </option>
                  ))}
                </select>
                <ChevronDown className="absolute right-2.5 top-1/2 -translate-y-1/2 w-3.5 h-3.5 text-neutral-400 pointer-events-none" />
              </div>
            </div>

            {/* Club Retirement Status */}
            <div className="space-y-1">
              <label className="text-[10px] font-mono text-neutral-400 uppercase tracking-wider block">
                Club Status
              </label>
              <div className="relative">
                <select
                  value={selectedClubRetirement}
                  onChange={(e) => setSelectedClubRetirement(e.target.value)}
                  className="w-full appearance-none px-3 py-2 pr-8 rounded-lg bg-black/60 border border-white/15 text-xs font-mono text-white focus:outline-none focus:border-amber-400 cursor-pointer"
                >
                  <option value="All">All Statuses</option>
                  <option value="Retired">Retired</option>
                  <option value="Active">Active</option>
                </select>
                <ChevronDown className="absolute right-2.5 top-1/2 -translate-y-1/2 w-3.5 h-3.5 text-neutral-400 pointer-events-none" />
              </div>
            </div>

            {/* International Retirement Status */}
            <div className="space-y-1 col-span-2 sm:col-span-1">
              <label className="text-[10px] font-mono text-neutral-400 uppercase tracking-wider block">
                International Status
              </label>
              <div className="relative">
                <select
                  value={selectedIntRetirement}
                  onChange={(e) => setSelectedIntRetirement(e.target.value)}
                  className="w-full appearance-none px-3 py-2 pr-8 rounded-lg bg-black/60 border border-white/15 text-xs font-mono text-white focus:outline-none focus:border-amber-400 cursor-pointer"
                >
                  <option value="All">All Statuses</option>
                  <option value="Retired">Retired</option>
                  <option value="Active">Active</option>
                </select>
                <ChevronDown className="absolute right-2.5 top-1/2 -translate-y-1/2 w-3.5 h-3.5 text-neutral-400 pointer-events-none" />
              </div>
            </div>
          </div>
        </section>

        {/* Results Counter Bar */}
        <div className="flex items-center justify-between mb-6 px-1 text-xs font-mono text-neutral-400">
          <div className="flex items-center space-x-2">
            <span className="w-2 h-2 rounded-full bg-amber-400 inline-block" />
            <span>
              DISPLAYING <strong className="text-white font-bold">{filteredPlayers.length}</strong> OF{' '}
              <strong className="text-white font-bold">{HALL_OF_FAME_PLAYERS.length}</strong> LEGENDS
            </span>
          </div>

          {hasActiveFilters && (
            <button
              type="button"
              onClick={handleResetFilters}
              className="text-amber-400 hover:text-amber-300 uppercase tracking-wider underline cursor-pointer"
            >
              Clear filters ({filteredPlayers.length} matches)
            </button>
          )}
        </div>

        {/* Player Cards Collectible Grid */}
        {filteredPlayers.length > 0 ? (
          <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 xl:grid-cols-5 gap-6">
            {filteredPlayers.map((player) => (
              <PlayerCard
                key={player.id}
                player={player}
                onClick={(p) => setActivePlayer(p)}
              />
            ))}
          </div>
        ) : (
          /* Empty Search State */
          <div className="p-16 rounded-3xl bg-neutral-900/50 border border-white/10 text-center max-w-lg mx-auto my-12 space-y-4">
            <div className="w-16 h-16 rounded-full bg-amber-400/10 border border-amber-400/30 flex items-center justify-center mx-auto text-amber-400">
              <Search className="w-8 h-8" />
            </div>
            <h3 className="font-display text-3xl text-white tracking-wide uppercase">
              NO MATCHING LEGENDS FOUND
            </h3>
            <p className="text-sm font-mono text-neutral-400 leading-relaxed">
              No footballers in our Hall of Fame match &quot;{searchQuery}&quot; with the selected filters.
            </p>
            <button
              type="button"
              onClick={handleResetFilters}
              className="px-6 py-2.5 rounded-xl bg-amber-500 hover:bg-amber-400 text-black font-display text-base tracking-wider transition-colors cursor-pointer"
            >
              RESET ALL CRITERIA
            </button>
          </div>
        )}
      </div>

      {/* Player Details Modal */}
      <PlayerDetailsModal
        player={activePlayer}
        onClose={() => setActivePlayer(null)}
      />
    </div>
  );
};

import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { api } from '../api';
import { PublicTournament, PublicMatch, PublicGroupStandings, PublicBracket } from '../types';
import { MatchCard } from '../components/MatchCard';
import { StandingsTable } from '../components/StandingsTable';
import { Ticker } from '../components/Ticker';
import { GoldenBootShowcase } from '../components/GoldenBootShowcase';
import { BracketTree } from '../components/BracketTree';
import { Trophy, Swords, Calendar, BarChart3, ArrowRight, ShieldAlert, Sparkles, GitFork } from 'lucide-react';
import { PRIZE_POOL, TOTAL_PRIZE_POOL } from '../constants';

export const HomePage: React.FC = () => {
  const [tournament, setTournament] = useState<PublicTournament | null>(null);
  const [recentMatches, setRecentMatches] = useState<PublicMatch[]>([]);
  const [upcomingMatches, setUpcomingMatches] = useState<PublicMatch[]>([]);
  const [standings, setStandings] = useState<PublicGroupStandings[]>([]);
  const [bracket, setBracket] = useState<PublicBracket>({ rounds: [] });
  const [loading, setLoading] = useState(true);

  const loadData = async () => {
    try {
      const [tData, rData, fData, sData, bData] = await Promise.all([
        api.getTournament(),
        api.getResults(6),
        api.getFixtures(),
        api.getStandings(),
        api.getBracket(),
      ]);
      setTournament(tData);
      setRecentMatches(Array.isArray(rData) ? rData : []);
      const fixturesList = Array.isArray(fData) ? fData : [];
      const upcoming = fixturesList.filter((m) => m.status === 'SCHEDULED');
      setUpcomingMatches(upcoming.length > 0 ? upcoming.slice(0, 4) : fixturesList.slice(0, 4));
      setStandings(Array.isArray(sData) ? sData : []);
      setBracket(bData);
    } catch (err) {
      console.error('Failed to load homepage tournament data', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
    // Auto-refresh every 15s as backup to SSE
    const interval = setInterval(loadData, 15000);
    return () => clearInterval(interval);
  }, []);

  return (
    <div className="min-h-screen">
      {/* Hero Section */}
      <section className="relative min-h-[85vh] flex items-center justify-center overflow-hidden border-b border-[#222222]">
        {/* Background Image with Dark Vignette */}
        <div className="absolute inset-0 z-0">
          <img
            src="/assets/backgrounds/bg_stadium_cinematic.webp"
            alt="Cinematic Stadium Background"
            className="w-full h-full object-cover object-center filter brightness-50 contrast-125 scale-105 transition-transform duration-1000"
          />
          <div className="absolute inset-0 bg-gradient-to-t from-[#080808] via-[#080808]/70 to-[#080808]/50" />
          <div className="absolute inset-0 bg-[radial-gradient(circle_at_center,transparent_0%,#080808_90%)]" />
        </div>

        {/* Hero Content */}
        <div className="relative z-10 max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 py-20 text-center flex flex-col items-center">
          {/* Badge */}
          <div className="inline-flex items-center space-x-2 px-3.5 py-1.5 rounded-full bg-black/70 border border-brand-red/60 text-xs font-mono text-neutral-300 mb-6 backdrop-blur-md shadow-glow-red">
            <span className="w-2 h-2 rounded-full bg-brand-red animate-ping" />
            <span className="tracking-widest uppercase text-white font-bold">
              {tournament ? `${tournament.name} · ${tournament.edition}` : 'MINARAM CUP · EDITION 1'}
            </span>
          </div>

          {/* Massive Display Title */}
          <h1 className="font-display text-5xl sm:text-7xl md:text-8xl lg:text-9xl tracking-tight text-white uppercase leading-[0.9] drop-shadow-2xl">
            THE DIGITAL <br />
            <span className="text-stroke-red text-transparent hover:text-brand-red transition-colors duration-300">
              ARENA
            </span>{' '}
            OF CHAMPIONS
          </h1>

          <p className="mt-6 max-w-2xl text-neutral-300 text-sm sm:text-base md:text-lg font-normal leading-relaxed drop-shadow">
            Experience the pinnacle of college eFootball. {tournament?.team_count || 21} elite squads competing across{' '}
            {tournament?.groups_count || (standings.length > 0 ? standings.length : 6)} groups and high-voltage knockout stages for eternal glory at TKM College of Engineering.
          </p>

          {/* Key Stat Cards: Live Dashboard Stats */}
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 sm:gap-4 mt-10 w-full max-w-3xl">
            <div className="bg-black/60 border border-neutral-800 backdrop-blur-md p-3.5 rounded-lg text-center relative overflow-hidden group hover:border-brand-red transition-all shadow-lg">
              <span className="block font-display text-3xl sm:text-4xl text-white tabular-nums">
                {tournament?.team_count ?? (standings.reduce((acc, g) => acc + g.standings.length, 0) || 21)}
              </span>
              <span className="text-[11px] font-mono uppercase tracking-widest text-neutral-400">
                Teams Registered
              </span>
              <div className="flex items-center justify-center space-x-1 mt-1 text-[10px] text-emerald-400 font-mono">
                <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse" />
                <span>LIVE UPDATES</span>
              </div>
            </div>

            <div className="bg-black/60 border border-neutral-800 backdrop-blur-md p-3.5 rounded-lg text-center relative overflow-hidden group hover:border-brand-red transition-all shadow-lg">
              <span className="block font-display text-3xl sm:text-4xl text-brand-red tabular-nums">
                {tournament?.groups_count || (standings.length > 0 ? standings.length : 6)}
              </span>
              <span className="text-[11px] font-mono uppercase tracking-widest text-neutral-400">
                Groups Formed
              </span>
              <div className="flex items-center justify-center space-x-1 mt-1 text-[10px] text-neutral-400 font-mono">
                <span>MAX 4 TEAMS / GRP</span>
              </div>
            </div>

            <div className="bg-black/60 border border-neutral-800 backdrop-blur-md p-3.5 rounded-lg text-center relative overflow-hidden group hover:border-brand-red transition-all shadow-lg">
              <span className="block font-display text-3xl sm:text-4xl text-white tabular-nums">
                {tournament?.match_count || (recentMatches.length + upcomingMatches.length) || 0}
              </span>
              <span className="text-[11px] font-mono uppercase tracking-widest text-neutral-400">
                Total Matches
              </span>
              <div className="flex items-center justify-center space-x-1 mt-1 text-[10px] text-neutral-400 font-mono">
                <span>{tournament?.completed_matches || 0} COMPLETED</span>
              </div>
            </div>

            <div className="bg-black/60 border border-neutral-800 backdrop-blur-md p-3.5 rounded-lg text-center relative overflow-hidden group hover:border-brand-red transition-all shadow-lg">
              <span className="block font-display text-2xl sm:text-3xl text-emerald-400 tracking-wider">
                {tournament?.status || 'GROUP STAGE'}
              </span>
              <span className="text-[11px] font-mono uppercase tracking-widest text-neutral-400">
                Current Stage
              </span>
              <div className="flex items-center justify-center space-x-1 mt-1 text-[10px] text-emerald-400 font-mono">
                <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-ping" />
                <span>SYNCHRONIZED</span>
              </div>
            </div>
          </div>

          {/* Group Stage Active Banner */}
          <div className="w-full max-w-3xl mt-5 p-3.5 sm:px-6 sm:py-3.5 rounded-lg border border-neutral-800 bg-black/70 backdrop-blur-md transition-all duration-300 shadow-lg hover:border-brand-red/50">
            <div className="flex flex-col sm:flex-row items-center justify-between gap-3 sm:gap-6 text-center sm:text-left">
              {/* Left Column: Monospace Status & Large Condensed Announcement */}
              <div className="flex flex-col items-center sm:items-start">
                <div className="flex items-center space-x-2 text-[11px] font-mono uppercase tracking-widest text-emerald-400">
                  <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
                  <span className="font-bold">COMPETITION ACTIVE</span>
                  <span className="text-neutral-600">·</span>
                  <span className="text-neutral-400 font-normal">MATCHWEEK 1 IN PROGRESS</span>
                </div>
                <div className="font-display text-2xl sm:text-3xl text-white tracking-wide leading-none mt-1">
                  GROUP STAGE IS LIVE
                </div>
              </div>

              {/* Right Column: Live Status Badge */}
              <div className="flex items-center space-x-2">
                <div className="flex items-center space-x-2 px-3.5 py-1.5 rounded bg-neutral-900/90 border border-brand-red/50 text-brand-red text-xs font-mono tracking-wider uppercase shadow-sm">
                  <span className="w-1.5 h-1.5 rounded-full bg-brand-red animate-ping" />
                  <span className="font-bold">MATCHES IN PROGRESS</span>
                </div>
              </div>
            </div>
          </div>

          {/* Action Buttons */}
          <div className="flex flex-wrap items-center justify-center gap-4 mt-8">
            <Link
              to="/fixtures"
              className="px-6 py-3 rounded bg-brand-red hover:bg-brand-red-bright text-white font-display text-lg tracking-wider transition-all shadow-glow-red flex items-center space-x-2"
            >
              <span>EXPLORE FIXTURES</span>
              <ArrowRight className="w-5 h-5" />
            </Link>
            <Link
              to="/standings"
              className="px-6 py-3 rounded bg-neutral-900/90 hover:bg-neutral-800 border border-neutral-700 text-white font-display text-lg tracking-wider transition-all flex items-center space-x-2"
            >
              <span>GROUP STANDINGS</span>
            </Link>
          </div>
        </div>
      </section>

      {/* Live Ticker Bar */}
      <Ticker recentMatches={recentMatches} upcomingMatches={upcomingMatches} />

      {/* Main Content Layout */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-16 space-y-20">
        {/* Prize Pool Section */}
        <section id="prize-pool" className="relative">
          <div className="flex flex-col items-center text-center mb-8">
            <span className="text-xs font-mono uppercase tracking-widest text-brand-red mb-1">
              REWARDS
            </span>
            <h2 className="font-display text-4xl sm:text-5xl text-white tracking-wider">
              PRIZE POOL
            </h2>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-5 sm:gap-6 items-stretch max-w-5xl mx-auto">
            {PRIZE_POOL.map((tier) => {
              const isWinner = tier.featured;
              return (
                <div
                  key={tier.id}
                  className={`relative flex flex-col justify-between rounded-xl transition-all duration-300 ${
                    isWinner
                      ? 'bg-gradient-to-b from-[#181012] via-[#120e10] to-[#0c0c0c] border-2 border-brand-red shadow-glow-red p-6 sm:p-7 order-first md:order-none'
                      : 'bg-[#101010] border border-neutral-800 hover:border-neutral-700 p-5 sm:p-6'
                  }`}
                >
                  {/* Position Badge & Marker */}
                  <div className="flex items-center justify-between mb-4">
                    <span
                      className={`text-[11px] font-mono uppercase tracking-widest px-2.5 py-0.5 rounded ${
                        isWinner
                          ? 'bg-brand-red/20 text-brand-red border border-brand-red/40 font-bold'
                          : 'bg-neutral-800/80 text-neutral-400 border border-neutral-700/60'
                      }`}
                    >
                      {tier.label} PLACE
                    </span>
                    <span
                      className={`font-display text-3xl ${
                        isWinner ? 'text-brand-red font-bold' : 'text-neutral-500'
                      }`}
                    >
                      {tier.place}
                    </span>
                  </div>

                  {/* Title & Amount */}
                  <div className="my-2">
                    <h3
                      className={`font-display tracking-wider uppercase ${
                        isWinner ? 'text-2xl text-white font-bold' : 'text-xl text-neutral-300'
                      }`}
                    >
                      {tier.title}
                    </h3>
                    <div className="mt-2 flex items-baseline space-x-1.5">
                      <span
                        className={`font-sans font-bold leading-none ${
                          isWinner ? 'text-3xl sm:text-4xl text-brand-red' : 'text-2xl sm:text-3xl text-neutral-400'
                        }`}
                      >
                        ₹
                      </span>
                      <span
                        className={`font-display tracking-tight text-white tabular-nums leading-none ${
                          isWinner ? 'text-5xl sm:text-6xl font-bold' : 'text-4xl sm:text-5xl'
                        }`}
                      >
                        {tier.amount}
                      </span>
                    </div>
                  </div>

                  {/* Minimal Footer Accent */}
                  <div
                    className={`mt-5 pt-3 border-t text-[11px] font-mono uppercase tracking-widest flex items-center justify-between ${
                      isWinner
                        ? 'border-brand-red/30 text-neutral-300'
                        : 'border-neutral-800 text-neutral-500'
                    }`}
                  >
                    <span>{tier.label} PRIZE</span>
                    {isWinner && (
                      <span className="flex items-center space-x-1.5 text-brand-red font-semibold">
                        <span className="w-1.5 h-1.5 rounded-full bg-brand-red" />
                        <span>CHAMPION</span>
                      </span>
                    )}
                  </div>
                </div>
              );
            })}
          </div>

          {/* Total Prize Pool Footer */}
          <div className="mt-6 text-center">
            <p className="text-xs font-mono tracking-widest text-neutral-400 uppercase">
              TOTAL PRIZE POOL <span className="font-sans font-semibold text-neutral-300">₹</span>{TOTAL_PRIZE_POOL}
            </p>
          </div>
        </section>

        {/* Golden Boot Top Scorers Section */}
        <GoldenBootShowcase />

        {/* Knockout Championship Bracket Section */}
        <section id="knockout-bracket" className="relative">
          <div className="flex flex-col sm:flex-row sm:items-end justify-between mb-8 pb-4 border-b border-[#222222] gap-4">
            <div>
              <div className="flex items-center space-x-2 text-xs font-mono uppercase tracking-widest text-brand-red mb-1">
                <GitFork className="w-4 h-4" />
                <span>CHAMPIONSHIP PLAYOFFS</span>
              </div>
              <h2 className="font-display text-4xl sm:text-5xl text-white tracking-wider">
                KNOCKOUT BRACKET
              </h2>
              <p className="text-xs sm:text-sm font-mono text-neutral-400 max-w-xl mt-1">
                Road to the Minaram Cup trophy. All slots are currently unseeded (yet to decide) while group stage matches are live.
              </p>
            </div>
            <Link
              to="/bracket"
              className="inline-flex items-center space-x-2 px-4 py-2 rounded bg-neutral-900/90 hover:bg-neutral-800 border border-neutral-700 text-white font-mono text-xs tracking-wider uppercase transition-all shrink-0"
            >
              <span>FULL BRACKET VIEW</span>
              <ArrowRight className="w-4 h-4 text-brand-red" />
            </Link>
          </div>

          <BracketTree bracket={bracket} showTrophyPedestal={false} />
        </section>

        {/* Next Matches & Recent Results Split Grid */}
        <section>
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-10">
            {/* Upcoming Fixtures */}
            <div>
              <div className="flex items-center justify-between mb-6 pb-2 border-b border-[#222222]">
                <div className="flex items-center space-x-2.5">
                  <Calendar className="w-5 h-5 text-brand-red" />
                  <h2 className="font-display text-2xl tracking-wider text-white">UPCOMING CLASHES</h2>
                </div>
                <Link to="/fixtures" className="text-xs font-mono text-neutral-400 hover:text-white flex items-center space-x-1">
                  <span>VIEW ALL</span>
                  <ArrowRight className="w-3.5 h-3.5" />
                </Link>
              </div>

              {upcomingMatches.length > 0 ? (
                <div className="space-y-4">
                  {upcomingMatches.map((m) => (
                    <MatchCard key={m.id} match={m} />
                  ))}
                </div>
              ) : (
                <div className="p-8 bg-[#121212] border border-[#222222] rounded-lg text-center text-neutral-400 text-sm">
                  No pending scheduled matches at this time.
                </div>
              )}
            </div>

            {/* Recent Results */}
            <div>
              <div className="flex items-center justify-between mb-6 pb-2 border-b border-[#222222]">
                <div className="flex items-center space-x-2.5">
                  <Trophy className="w-5 h-5 text-brand-red" />
                  <h2 className="font-display text-2xl tracking-wider text-white">LATEST RESULTS</h2>
                </div>
                <Link to="/results" className="text-xs font-mono text-neutral-400 hover:text-white flex items-center space-x-1">
                  <span>FULL RESULTS</span>
                  <ArrowRight className="w-3.5 h-3.5" />
                </Link>
              </div>

              {recentMatches.length > 0 ? (
                <div className="space-y-4">
                  {recentMatches.slice(0, 4).map((m) => (
                    <MatchCard key={m.id} match={m} />
                  ))}
                </div>
              ) : (
                <div className="p-8 bg-[#121212] border border-[#222222] rounded-lg text-center text-neutral-400 text-sm">
                  Tournament matches will appear here as results are recorded.
                </div>
              )}
            </div>
          </div>
        </section>

        {/* Editorial Poster Feature: Ronaldo Focus */}
        <section className="relative rounded-2xl overflow-hidden border border-[#262626] bg-[#0c0c0c] min-h-[400px] flex items-center">
          <div className="absolute right-0 top-0 bottom-0 w-full lg:w-1/2 opacity-35 lg:opacity-60 pointer-events-none">
            <img
              src="/assets/backgrounds/bg_ronaldo_07.webp"
              alt="Cristiano Ronaldo Iconic Number 7"
              className="w-full h-full object-cover object-top filter grayscale contrast-150"
            />
            <div className="absolute inset-0 bg-gradient-to-r from-[#0c0c0c] via-[#0c0c0c]/80 to-transparent" />
          </div>

          <div className="relative z-10 p-8 sm:p-12 lg:p-16 max-w-2xl">
            <div className="inline-block px-3 py-1 bg-brand-red text-white text-[11px] font-mono tracking-widest uppercase mb-4">
              EDITORIAL FOCUS
            </div>
            <h2 className="font-display text-4xl sm:text-5xl lg:text-6xl text-white tracking-tight leading-[0.95]">
              TACTICS OVER TALK. <br />
              PRECISION UNDER PRESSURE.
            </h2>
            <p className="mt-4 text-neutral-400 text-sm sm:text-base leading-relaxed">
              In eFootball, a millisecond decides the line between triumph and heartbreak.
              From high-pressing 4-3-3 formations to disciplined defensive counters, every Minaram Cup
              competitor is tested under relentless campus competition.
            </p>
            <div className="mt-6">
              <Link
                to="/rules"
                className="inline-flex items-center space-x-2 text-sm font-mono uppercase tracking-widest text-brand-red hover:text-white transition-colors"
              >
                <span>Read the Competition Rulebook</span>
                <ArrowRight className="w-4 h-4" />
              </Link>
            </div>
          </div>
        </section>

        {/* Group Standings Snapshot */}
        <section>
          <div className="flex items-center justify-between mb-8 pb-3 border-b border-[#222222]">
            <div>
              <h2 className="font-display text-3xl tracking-wider text-white">GROUP STAGE STANDINGS</h2>
              <p className="text-xs font-mono text-neutral-400 mt-1 uppercase">
                Real-time points table and qualification tracker
              </p>
            </div>
            <Link
              to="/standings"
              className="px-4 py-2 rounded bg-neutral-900 border border-neutral-700 hover:border-neutral-500 text-xs font-mono text-neutral-300 hover:text-white transition-colors"
            >
              ALL GROUPS
            </Link>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {(Array.isArray(standings) ? standings : []).map((g) => (
              <StandingsTable key={g.group_name} groupData={g} />
            ))}
          </div>
        </section>

        {/* Official Sponsor Section */}
        <section className="bg-gradient-to-b from-[#111111] to-[#080808] border border-[#222222] rounded-xl p-8 sm:p-12 text-center">
          <div className="max-w-2xl mx-auto space-y-4">
            <span className="text-xs font-mono tracking-widest text-brand-gold uppercase flex items-center justify-center space-x-1.5">
              <Sparkles className="w-3.5 h-3.5" />
              <span>PRESENTING SPONSOR</span>
              <Sparkles className="w-3.5 h-3.5" />
            </span>
            <div className="py-4 flex justify-center">
              <img
                src="/assets/logos/transparent/akhadha_sponsor_transparent.png"
                alt="AKHADHA Sponsor Emblem"
                className="h-24 sm:h-28 w-auto object-contain filter drop-shadow-[0_0_20px_rgba(255,255,255,0.1)]"
              />
            </div>
            <h3 className="font-display text-3xl text-white tracking-wider">AKHADHA</h3>
            <p className="text-sm text-neutral-400">
              Fueling student esports and competitive spirit at TKM College of Engineering.
            </p>
          </div>
        </section>
      </div>
    </div>
  );
};

import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { api } from '../api';
import { PublicTournament } from '../types';
import { GoldenBootShowcase } from '../components/GoldenBootShowcase';
import { Ticker } from '../components/Ticker';
import { Trophy, Calendar, BarChart3, ArrowRight, Sparkles, GitFork } from 'lucide-react';
import { PRIZE_POOL, TOTAL_PRIZE_POOL } from '../constants';
import { useLiveUpdates } from '../hooks/useLiveUpdates';

export const HomePage: React.FC = () => {
  const [tournament, setTournament] = useState<PublicTournament | null>(null);
  const [loading, setLoading] = useState(true);

  const loadData = async () => {
    try {
      const tData = await api.getTournament();
      setTournament(tData);
    } catch (err) {
      console.error('Failed to load homepage tournament data', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
    const interval = setInterval(loadData, 20000);
    return () => clearInterval(interval);
  }, []);

  useLiveUpdates((evt) => {
    const evType = evt.event || (evt as any).type;
    if (['standings_updated', 'result_updated', 'match_updated', 'knockout_updated'].includes(evType)) {
      loadData();
    }
  });

  return (
    <div className="min-h-screen">
      {/* Hero Section */}
      <section className="relative min-h-[85vh] flex items-center justify-center overflow-hidden border-b border-blue-900/40">
        {/* Background Image with Dark Vignette */}
        <div className="absolute inset-0 z-0">
          <img
            src="/assets/backgrounds/ucl_4k_wallpaper.jpg"
            alt="UEFA Champions League 4K Wallpaper"
            className="w-full h-full object-cover object-center filter brightness-60 contrast-110 scale-105 transition-transform duration-1000"
          />
          <div className="absolute inset-0 bg-gradient-to-t from-[#020718] via-[#030d2a]/70 to-[#020718]/60" />
          <div className="absolute inset-0 bg-[radial-gradient(circle_at_center,transparent_0%,#020718_85%)]" />
        </div>

        {/* Hero Content */}
        <div className="relative z-10 max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 py-20 text-center flex flex-col items-center">
          {/* Badge */}
          <div className="inline-flex items-center space-x-2 px-3.5 py-1.5 rounded-full bg-[#030d26]/80 border border-blue-500/50 text-xs font-mono text-blue-200 mb-6 backdrop-blur-md shadow-[0_0_20px_rgba(59,130,246,0.4)]">
            <span className="w-2 h-2 rounded-full bg-blue-400 animate-ping" />
            <span className="tracking-widest uppercase text-white font-bold">
              {tournament ? `${tournament.name} · ${tournament.edition}` : 'MINARAM CUP · EDITION 1'}
            </span>
          </div>

          {/* Massive Display Title */}
          <h1 className="font-display text-5xl sm:text-7xl md:text-8xl lg:text-9xl tracking-tight text-white uppercase leading-[0.9] drop-shadow-2xl">
            THE DIGITAL <br />
            <span className="text-stroke-ucl text-transparent hover:text-blue-400 transition-colors duration-300">
              ARENA
            </span>{' '}
            OF CHAMPIONS
          </h1>

          <p className="mt-6 max-w-2xl text-neutral-300 text-sm sm:text-base md:text-lg font-normal leading-relaxed drop-shadow">
            Experience the pinnacle of college eFootball. {tournament?.team_count || 58} elite squads competing across{' '}
            {tournament?.groups_count || 15} groups and high-voltage knockout stages for eternal glory at TKM College of Engineering.
          </p>

          {/* Key Stat Cards: Live Dashboard Stats */}
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 sm:gap-4 mt-10 w-full max-w-3xl">
            <div className="bg-black/60 border border-neutral-800 backdrop-blur-md p-3.5 rounded-lg text-center relative overflow-hidden group hover:border-brand-red transition-all shadow-lg">
              <span className="block font-display text-3xl sm:text-4xl text-white tabular-nums">
                {tournament?.team_count ?? 58}
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
                {tournament?.groups_count ?? 15}
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
                {tournament?.match_count ?? 90}
              </span>
              <span className="text-[11px] font-mono uppercase tracking-widest text-neutral-400">
                Total Matches
              </span>
              <div className="flex items-center justify-center space-x-1 mt-1 text-[10px] text-neutral-400 font-mono">
                <span>{tournament?.completed_matches || 51} COMPLETED</span>
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
      <Ticker />

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

        {/* Tournament Competition Directory Section */}
        <section className="relative">
          <div className="flex flex-col sm:flex-row sm:items-end justify-between mb-8 pb-4 border-b border-[#222222] gap-4">
            <div>
              <div className="flex items-center space-x-2 text-xs font-mono uppercase tracking-widest text-brand-red mb-1">
                <Trophy className="w-4 h-4 text-brand-gold" />
                <span>TOURNAMENT COMPETITION HUBS</span>
              </div>
              <h2 className="font-display text-4xl sm:text-5xl text-white tracking-wider">
                EXPLORE CHAMPIONSHIP
              </h2>
              <p className="text-xs sm:text-sm font-mono text-neutral-400 max-w-xl mt-1">
                Access official competition portals: 15-group standings, comprehensive fixtures, match reports, and the live knockout arena.
              </p>
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
            {/* Hub 1: Knockout / Qualifiers */}
            <Link
              to="/bracket"
              className="group relative p-6 rounded-2xl bg-gradient-to-b from-[#161208] via-[#100d06] to-[#080808] border border-brand-gold/40 hover:border-brand-gold transition-all duration-300 flex flex-col justify-between shadow-lg hover:shadow-brand-gold/10"
            >
              <div>
                <div className="flex items-center justify-between mb-4">
                  <div className="w-12 h-12 rounded-xl bg-brand-gold/10 border border-brand-gold/40 flex items-center justify-center text-brand-gold group-hover:scale-110 transition-transform">
                    <Trophy className="w-6 h-6" />
                  </div>
                  <span className="text-[10px] font-mono px-2 py-0.5 rounded-full bg-brand-gold/20 text-brand-gold border border-brand-gold/30 uppercase tracking-widest animate-pulse">
                    UCL DRAW
                  </span>
                </div>
                <h3 className="font-display text-2xl text-white tracking-wide group-hover:text-brand-gold transition-colors">
                  KNOCKOUT / QUALIFIERS
                </h3>
                <p className="text-xs font-mono text-neutral-400 mt-2 leading-relaxed">
                  30 qualified squads, 2 Direct R16 Byes, interactive UEFA Champions League style ceremonial draw simulator, and championship bracket.
                </p>
              </div>
              <div className="mt-6 pt-3 border-t border-neutral-800 flex items-center justify-between text-xs font-mono text-brand-gold group-hover:text-white transition-colors">
                <span>ENTER KNOCKOUT ARENA</span>
                <ArrowRight className="w-4 h-4 group-hover:translate-x-1 transition-transform" />
              </div>
            </Link>

            {/* Hub 2: Group Standings */}
            <Link
              to="/standings"
              className="group relative p-6 rounded-2xl bg-gradient-to-b from-[#0e141a] via-[#090d12] to-[#080808] border border-neutral-800 hover:border-cyan-500/60 transition-all duration-300 flex flex-col justify-between shadow-lg hover:shadow-cyan-900/10"
            >
              <div>
                <div className="flex items-center justify-between mb-4">
                  <div className="w-12 h-12 rounded-xl bg-cyan-950/40 border border-cyan-700/40 flex items-center justify-center text-cyan-400 group-hover:scale-110 transition-transform">
                    <BarChart3 className="w-6 h-6" />
                  </div>
                  <span className="text-[10px] font-mono px-2 py-0.5 rounded-full bg-cyan-950/40 text-cyan-300 border border-cyan-800/40 uppercase tracking-widest">
                    15 GROUPS
                  </span>
                </div>
                <h3 className="font-display text-2xl text-white tracking-wide group-hover:text-cyan-400 transition-colors">
                  GROUP STANDINGS
                </h3>
                <p className="text-xs font-mono text-neutral-400 mt-2 leading-relaxed">
                  Official points tables, goal differences, head-to-head records, and top-2 qualification cutoffs for Groups A through O.
                </p>
              </div>
              <div className="mt-6 pt-3 border-t border-neutral-800 flex items-center justify-between text-xs font-mono text-cyan-400 group-hover:text-white transition-colors">
                <span>VIEW STANDINGS</span>
                <ArrowRight className="w-4 h-4 group-hover:translate-x-1 transition-transform" />
              </div>
            </Link>

            {/* Hub 3: Match Schedule & Fixtures */}
            <Link
              to="/fixtures"
              className="group relative p-6 rounded-2xl bg-gradient-to-b from-[#181112] via-[#100b0c] to-[#080808] border border-neutral-800 hover:border-brand-red transition-all duration-300 flex flex-col justify-between shadow-lg hover:shadow-brand-red/10"
            >
              <div>
                <div className="flex items-center justify-between mb-4">
                  <div className="w-12 h-12 rounded-xl bg-brand-red/10 border border-brand-red/40 flex items-center justify-center text-brand-red group-hover:scale-110 transition-transform">
                    <Calendar className="w-6 h-6" />
                  </div>
                  <span className="text-[10px] font-mono px-2 py-0.5 rounded-full bg-brand-red/20 text-brand-red border border-brand-red/30 uppercase tracking-widest">
                    SCHEDULE
                  </span>
                </div>
                <h3 className="font-display text-2xl text-white tracking-wide group-hover:text-brand-red transition-colors">
                  UPCOMING FIXTURES
                </h3>
                <p className="text-xs font-mono text-neutral-400 mt-2 leading-relaxed">
                  Comprehensive fixture schedules, flexible matchweek windows, pitch assignments, and team clash schedules.
                </p>
              </div>
              <div className="mt-6 pt-3 border-t border-neutral-800 flex items-center justify-between text-xs font-mono text-brand-red group-hover:text-white transition-colors">
                <span>VIEW FIXTURES</span>
                <ArrowRight className="w-4 h-4 group-hover:translate-x-1 transition-transform" />
              </div>
            </Link>

            {/* Hub 4: Results & Match Reports */}
            <Link
              to="/results"
              className="group relative p-6 rounded-2xl bg-gradient-to-b from-[#13111c] via-[#0b0a10] to-[#080808] border border-neutral-800 hover:border-purple-500/60 transition-all duration-300 flex flex-col justify-between shadow-lg hover:shadow-purple-900/10"
            >
              <div>
                <div className="flex items-center justify-between mb-4">
                  <div className="w-12 h-12 rounded-xl bg-purple-950/40 border border-purple-700/40 flex items-center justify-center text-purple-400 group-hover:scale-110 transition-transform">
                    <Sparkles className="w-6 h-6" />
                  </div>
                  <span className="text-[10px] font-mono px-2 py-0.5 rounded-full bg-purple-950/40 text-purple-300 border border-purple-800/40 uppercase tracking-widest">
                    RESULTS
                  </span>
                </div>
                <h3 className="font-display text-2xl text-white tracking-wide group-hover:text-purple-400 transition-colors">
                  MATCH RESULTS
                </h3>
                <p className="text-xs font-mono text-neutral-400 mt-2 leading-relaxed">
                  Full official results archive, penalty shootout outcomes, Rule 2 walkover verdicts, and completed tie histories.
                </p>
              </div>
              <div className="mt-6 pt-3 border-t border-neutral-800 flex items-center justify-between text-xs font-mono text-purple-400 group-hover:text-white transition-colors">
                <span>VIEW RESULTS</span>
                <ArrowRight className="w-4 h-4 group-hover:translate-x-1 transition-transform" />
              </div>
            </Link>
          </div>
        </section>

        {/* Editorial Feature: UEFA Champions League Spirit */}
        <section className="relative rounded-2xl overflow-hidden border border-blue-800/40 bg-gradient-to-r from-[#030d24] via-[#05143a] to-[#020718] min-h-[400px] flex items-center shadow-2xl">
          <div className="absolute right-0 top-0 bottom-0 w-full lg:w-3/5 opacity-40 lg:opacity-75 pointer-events-none">
            <img
              src="/assets/backgrounds/ucl_stars_dark.jpg"
              alt="UEFA Champions League Stars"
              className="w-full h-full object-cover object-center filter contrast-125"
            />
            <div className="absolute inset-0 bg-gradient-to-r from-[#030d24] via-[#030d24]/80 to-transparent" />
          </div>

          <div className="relative z-10 p-8 sm:p-12 lg:p-16 max-w-2xl">
            <div className="inline-block px-3 py-1 bg-gradient-to-r from-blue-600 to-indigo-600 text-white text-[11px] font-mono tracking-widest uppercase mb-4 shadow-[0_0_15px_rgba(59,130,246,0.4)]">
              UEFA CHAMPIONS LEAGUE SPIRIT
            </div>
            <h2 className="font-display text-4xl sm:text-5xl lg:text-6xl text-white tracking-tight leading-[0.95]">
              TACTICS OVER TALK. <br />
              PRECISION UNDER PRESSURE.
            </h2>
            <p className="mt-4 text-blue-200/80 text-sm sm:text-base leading-relaxed">
              In eFootball, a millisecond decides the line between triumph and heartbreak.
              From high-pressing 4-3-3 formations to disciplined defensive counters, every Minaram Cup
              competitor is tested under relentless campus competition.
            </p>
            <div className="mt-6">
              <Link
                to="/rules"
                className="inline-flex items-center space-x-2 text-sm font-mono uppercase tracking-widest text-blue-400 hover:text-white transition-colors"
              >
                <span>Read the Competition Rulebook</span>
                <ArrowRight className="w-4 h-4" />
              </Link>
            </div>
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

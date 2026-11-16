import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { api } from '../api';
import { PublicTournament } from '../types';
import { GoldenBootShowcase } from '../components/GoldenBootShowcase';
import { Ticker } from '../components/Ticker';
import { CinematicHeroBackground } from '../components/CinematicHeroBackground';
import { Trophy, Calendar, BarChart3, ArrowRight, Sparkles, Award, Shield, Star } from 'lucide-react';
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

  const completedCount = tournament?.completed_matches ?? 51;
  const isKnockout = completedCount >= 84;
  const stageBannerTitle = isKnockout ? 'KNOCKOUT ROUND OF 16 IS LIVE' : 'GROUP STAGE IS LIVE';
  const stageBannerSub = isKnockout ? 'CHAMPIONSHIP PLAYOFFS · THE ROAD TO GLORY' : 'MATCHWEEKS IN PROGRESS · GROUPS A–O';

  return (
    <div className="min-h-screen">
      {/* Hero Section */}
      <section className="relative min-h-[90vh] flex items-center justify-center overflow-hidden border-b border-white/10">
        {/* Dynamic Cinematic Hero Background from Bgs */}
        <CinematicHeroBackground fallbackImage="/assets/backgrounds/lionel-messi-world-3840x2160-19207.jpg" />

        {/* Hero Content */}
        <div className="relative z-10 max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 py-24 sm:py-28 text-center flex flex-col items-center">
          {/* Hero Eyebrow */}
          <div className="inline-flex items-center space-x-2 px-4 py-1.5 rounded-full bg-black/80 border border-amber-400/50 text-xs font-mono text-amber-300 mb-6 backdrop-blur-md shadow-[0_0_25px_rgba(212,175,55,0.3)]">
            <Sparkles className="w-3.5 h-3.5 text-amber-400" />
            <span className="tracking-widest uppercase font-bold text-white">
              A TRIBUTE TO THE BEAUTIFUL GAME
            </span>
            <span className="w-1.5 h-1.5 rounded-full bg-amber-400 animate-ping" />
          </div>

          {/* Main Headline */}
          <h1 className="font-display text-4xl sm:text-6xl md:text-7xl lg:text-8xl tracking-tight text-white uppercase leading-[0.95] drop-shadow-2xl max-w-5xl">
            For the legends who made us{' '}
            <span className="text-stroke-gold text-transparent hover:text-amber-300 transition-colors duration-300">
              fall in love
            </span>{' '}
            with football.
          </h1>

          {/* Description */}
          <p className="mt-6 max-w-3xl text-neutral-200 text-sm sm:text-base md:text-lg font-normal leading-relaxed drop-shadow">
            Dedicated to <strong className="text-sky-300 font-semibold">Lionel Messi</strong>,{' '}
            <strong className="text-rose-400 font-semibold">Cristiano Ronaldo</strong>, and{' '}
            <strong className="text-yellow-300 font-semibold">Neymar Jr.</strong> — the icons who turned ordinary days into unforgettable football memories. Their magic, passion, and legacy deserve a place beyond the final whistle.
          </p>

          {/* Hero Action Shortcuts */}
          <div className="flex flex-wrap items-center justify-center gap-4 mt-10">
            <a
              href="#the-championship"
              className="px-6 py-3 rounded-xl bg-gradient-to-r from-amber-500 to-amber-600 hover:from-amber-400 hover:to-amber-500 text-black font-display text-lg tracking-wider transition-all shadow-[0_0_20px_rgba(212,175,55,0.4)] flex items-center space-x-2"
            >
              <span>ENTER THE CHAMPIONSHIP</span>
              <ArrowRight className="w-5 h-5" />
            </a>
            <a
              href="#hall-of-legends"
              className="px-6 py-3 rounded-xl bg-neutral-900/90 hover:bg-neutral-800 border border-amber-400/40 text-amber-300 font-display text-lg tracking-wider transition-all flex items-center space-x-2"
            >
              <Star className="w-4 h-4 text-amber-400" />
              <span>HALL OF LEGENDS</span>
            </a>
          </div>
        </div>
      </section>

      {/* Live Ticker Bar */}
      <Ticker />

      {/* Main Content Layout */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-16 space-y-24">
        
        {/* Next Section — The Championship */}
        <section id="the-championship" className="relative">
          <div className="flex flex-col items-center text-center mb-10">
            <div className="inline-flex items-center space-x-2 px-3 py-1 rounded-full bg-amber-950/40 border border-amber-400/40 text-xs font-mono text-amber-300 uppercase tracking-widest mb-3">
              <Trophy className="w-3.5 h-3.5 text-amber-400" />
              <span>THE CHAMPIONSHIP</span>
            </div>
            <h2 className="font-display text-4xl sm:text-6xl md:text-7xl text-white tracking-wider uppercase">
              The competition begins here.
            </h2>
            <p className="max-w-3xl text-neutral-300 text-sm sm:text-base md:text-lg font-normal mt-3 leading-relaxed">
              58 elite collegiate squads, divided across 15 groups, competing at TKM College of Engineering. A championship built on passion, rivalry, teamwork, and the pursuit of glory.
            </p>
          </div>

          {/* Key Stat Cards: Live Dashboard Stats */}
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 sm:gap-4 max-w-4xl mx-auto">
            <div className="bg-black/75 border border-white/10 backdrop-blur-md p-3.5 rounded-xl text-center relative overflow-hidden group hover:border-amber-400/50 transition-all shadow-lg">
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

            <div className="bg-black/75 border border-white/10 backdrop-blur-md p-3.5 rounded-xl text-center relative overflow-hidden group hover:border-amber-400/50 transition-all shadow-lg">
              <span className="block font-display text-3xl sm:text-4xl text-amber-400 tabular-nums">
                {tournament?.groups_count ?? 15}
              </span>
              <span className="text-[11px] font-mono uppercase tracking-widest text-neutral-400">
                Groups Formed
              </span>
              <div className="flex items-center justify-center space-x-1 mt-1 text-[10px] text-neutral-400 font-mono">
                <span>MAX 4 TEAMS / GRP</span>
              </div>
            </div>

            <div className="bg-black/75 border border-white/10 backdrop-blur-md p-3.5 rounded-xl text-center relative overflow-hidden group hover:border-amber-400/50 transition-all shadow-lg">
              <span className="block font-display text-3xl sm:text-4xl text-white tabular-nums">
                {tournament?.match_count ?? 90}
              </span>
              <span className="text-[11px] font-mono uppercase tracking-widest text-neutral-400">
                Total Matches
              </span>
              <div className="flex items-center justify-center space-x-1 mt-1 text-[10px] text-neutral-400 font-mono">
                <span>{completedCount} COMPLETED</span>
              </div>
            </div>

            <div className="bg-black/75 border border-white/10 backdrop-blur-md p-3.5 rounded-xl text-center relative overflow-hidden group hover:border-amber-400/50 transition-all shadow-lg">
              <span className="block font-display text-2xl sm:text-3xl text-emerald-400 tracking-wider">
                {isKnockout ? 'ROUND OF 16' : (tournament?.status || 'GROUP STAGE')}
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

          {/* Group / Knockout Stage Active Banner */}
          <div className="w-full max-w-4xl mx-auto mt-6 p-4 sm:px-6 sm:py-4 rounded-xl border border-white/10 bg-black/80 backdrop-blur-md transition-all duration-300 shadow-lg hover:border-amber-400/40">
            <div className="flex flex-col sm:flex-row items-center justify-between gap-3 sm:gap-6 text-center sm:text-left">
              <div className="flex flex-col items-center sm:items-start">
                <div className="flex items-center space-x-2 text-[11px] font-mono uppercase tracking-widest text-emerald-400">
                  <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
                  <span className="font-bold">COMPETITION ACTIVE</span>
                  <span className="text-neutral-600">·</span>
                  <span className="text-neutral-400 font-normal">{stageBannerSub}</span>
                </div>
                <div className="font-display text-2xl sm:text-3xl text-white tracking-wide leading-none mt-1">
                  {stageBannerTitle}
                </div>
              </div>

              <div className="flex items-center space-x-2">
                <div className="flex items-center space-x-2 px-3.5 py-1.5 rounded-lg bg-neutral-900 border border-brand-red/60 text-brand-red text-xs font-mono tracking-wider uppercase shadow-sm">
                  <span className="w-1.5 h-1.5 rounded-full bg-brand-red animate-ping" />
                  <span className="font-bold">LIVE MATCHDAYS</span>
                </div>
              </div>
            </div>
          </div>

          {/* Action Buttons */}
          <div className="flex flex-wrap items-center justify-center gap-4 mt-8">
            <Link
              to="/fixtures"
              className="px-6 py-3 rounded-xl bg-gradient-to-r from-amber-500 to-amber-600 hover:from-amber-400 hover:to-amber-500 text-black font-display text-lg tracking-wider transition-all shadow-[0_0_20px_rgba(212,175,55,0.4)] flex items-center space-x-2"
            >
              <span>EXPLORE FIXTURES</span>
              <ArrowRight className="w-5 h-5" />
            </Link>
            <Link
              to="/standings"
              className="px-6 py-3 rounded-xl bg-neutral-900 hover:bg-neutral-800 border border-white/20 text-white font-display text-lg tracking-wider transition-all flex items-center space-x-2"
            >
              <span>GROUP STANDINGS</span>
            </Link>
            <Link
              to="/bracket"
              className="px-6 py-3 rounded-xl bg-neutral-900 hover:bg-neutral-800 border border-amber-400/40 text-amber-300 font-display text-lg tracking-wider transition-all flex items-center space-x-2"
            >
              <span>KNOCKOUT PLAYOFFS</span>
            </Link>
          </div>
        </section>
        
        {/* NEW: Hall of Legends: The Holy Trinity Tribute Gallery */}
        <section id="hall-of-legends" className="relative">
          <div className="flex flex-col items-center text-center mb-12">
            <div className="inline-flex items-center space-x-2 px-3 py-1 rounded-full bg-amber-950/40 border border-amber-400/40 text-xs font-mono text-amber-300 uppercase tracking-widest mb-2">
              <Star className="w-3.5 h-3.5 text-amber-400 fill-current" />
              <span>THE RETIREMENT SALUTE</span>
              <Star className="w-3.5 h-3.5 text-amber-400 fill-current" />
            </div>
            <h2 className="font-display text-4xl sm:text-6xl text-white tracking-wider">
              HALL OF LEGENDS
            </h2>
            <p className="max-w-2xl text-neutral-400 text-sm sm:text-base font-normal mt-2 leading-relaxed">
              Three titans who defined our generation. As their boots are hung and their eternal records stand,
              we honor their enduring genius, artistry, and passion.
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-8 items-stretch">
            {/* Legend 1: Lionel Messi */}
            <div className="relative rounded-2xl overflow-hidden border border-sky-400/30 bg-gradient-to-b from-[#081220] via-[#040810] to-[#04060B] flex flex-col justify-between shadow-[0_8px_30px_rgba(56,189,248,0.15)] group hover:border-sky-400/60 transition-all duration-300">
              <div className="relative h-64 overflow-hidden">
                <img
                  src="/assets/backgrounds/lionel-messi-world-3840x2160-19207.jpg"
                  alt="Young Lionel Messi 2006 Debut"
                  className="w-full h-full object-cover object-left group-hover:scale-105 transition-transform duration-700 filter brightness-90"
                  loading="lazy"
                />
                <div className="absolute inset-0 bg-gradient-to-t from-[#040810] via-transparent to-transparent" />
                <span className="absolute top-4 left-4 px-2.5 py-1 rounded-full bg-sky-950/80 border border-sky-400/60 text-[10px] font-mono font-bold text-sky-200 uppercase tracking-wider backdrop-blur-sm">
                  ALBICELESTE · #10
                </span>
              </div>
              <div className="p-6 flex flex-col justify-between flex-grow">
                <div>
                  <h3 className="font-display text-3xl text-white tracking-wide">
                    LIONEL MESSI
                  </h3>
                  <div className="text-xs font-mono text-sky-400 font-semibold uppercase tracking-wider mt-0.5">
                    The Coronation of Genius
                  </div>
                  <p className="text-xs text-neutral-300 font-normal mt-3 leading-relaxed">
                    From his teenage World Cup debut in 2006 to lifting the FIFA World Cup trophy in Qatar.
                    8 Ballon d'Or trophies, unmatched playmaking vision, and the undisputed pinnacle of football artistry.
                  </p>
                </div>
                <div className="mt-6 pt-4 border-t border-sky-900/40 text-[11px] font-mono text-neutral-400 space-y-1">
                  <div className="flex justify-between">
                    <span className="text-neutral-500">Ballon d'Or:</span>
                    <span className="text-sky-300 font-bold">8 Awards (Record)</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-neutral-500">Career Honors:</span>
                    <span className="text-neutral-200">World Cup, 4x UCL, 10x La Liga</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-neutral-500">Goal Contributions:</span>
                    <span className="text-sky-300 font-bold">1,000+ Goals & Assists</span>
                  </div>
                </div>
              </div>
            </div>

            {/* Legend 2: Cristiano Ronaldo */}
            <div className="relative rounded-2xl overflow-hidden border border-rose-500/30 bg-gradient-to-b from-[#18080c] via-[#0c0406] to-[#04060B] flex flex-col justify-between shadow-[0_8px_30px_rgba(225,29,72,0.15)] group hover:border-rose-500/60 transition-all duration-300">
              <div className="relative h-64 overflow-hidden">
                <img
                  src="/assets/backgrounds/cristiano-ronaldo-3840x2160-14010.jpg"
                  alt="Young Cristiano Ronaldo #7 Portugal"
                  className="w-full h-full object-cover object-center group-hover:scale-105 transition-transform duration-700 filter brightness-90"
                  loading="lazy"
                />
                <div className="absolute inset-0 bg-gradient-to-t from-[#0c0406] via-transparent to-transparent" />
                <span className="absolute top-4 left-4 px-2.5 py-1 rounded-full bg-rose-950/80 border border-rose-500/60 text-[10px] font-mono font-bold text-rose-200 uppercase tracking-wider backdrop-blur-sm">
                  QUINAS · #7
                </span>
              </div>
              <div className="p-6 flex flex-col justify-between flex-grow">
                <div>
                  <h3 className="font-display text-3xl text-white tracking-wide">
                    CRISTIANO RONALDO
                  </h3>
                  <div className="text-xs font-mono text-rose-400 font-semibold uppercase tracking-wider mt-0.5">
                    The Relentless Will
                  </div>
                  <p className="text-xs text-neutral-300 font-normal mt-3 leading-relaxed">
                    From a passionate teenage winger at Euro 2004 to the greatest international goalscorer in football history.
                    A masterclass in dedication, clutch dominance, and unyielding competitive spirit.
                  </p>
                </div>
                <div className="mt-6 pt-4 border-t border-rose-900/40 text-[11px] font-mono text-neutral-400 space-y-1">
                  <div className="flex justify-between">
                    <span className="text-neutral-500">Ballon d'Or:</span>
                    <span className="text-rose-300 font-bold">5 Awards</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-neutral-500">Career Honors:</span>
                    <span className="text-neutral-200">Euro 2016, 5x UCL, 3x Premier League</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-neutral-500">All-Time Goals:</span>
                    <span className="text-rose-300 font-bold">900+ Official Career Goals</span>
                  </div>
                </div>
              </div>
            </div>

            {/* Legend 3: Neymar Jr */}
            <div className="relative rounded-2xl overflow-hidden border border-yellow-400/30 bg-gradient-to-b from-[#181406] via-[#0c0a04] to-[#04060B] flex flex-col justify-between shadow-[0_8px_30px_rgba(234,179,8,0.15)] group hover:border-yellow-400/60 transition-all duration-300">
              <div className="relative h-64 overflow-hidden">
                <img
                  src="/assets/backgrounds/neymar-debut-celebration.webp"
                  alt="Young Neymar Jr Debut Brazil Goal Celebration"
                  className="w-full h-full object-cover object-top group-hover:scale-105 transition-transform duration-700 filter brightness-95"
                  loading="lazy"
                />
                <div className="absolute inset-0 bg-gradient-to-t from-[#0c0a04] via-transparent to-transparent" />
                <span className="absolute top-4 left-4 px-2.5 py-1 rounded-full bg-yellow-950/80 border border-yellow-400/60 text-[10px] font-mono font-bold text-yellow-200 uppercase tracking-wider backdrop-blur-sm">
                  SELEÇÃO · #11
                </span>
              </div>
              <div className="p-6 flex flex-col justify-between flex-grow">
                <div>
                  <h3 className="font-display text-3xl text-white tracking-wide">
                    NEYMAR JR.
                  </h3>
                  <div className="text-xs font-mono text-yellow-400 font-semibold uppercase tracking-wider mt-0.5">
                    The Soul of Samba
                  </div>
                  <p className="text-xs text-neutral-300 font-normal mt-3 leading-relaxed">
                    The torchbearer of Brazilian football magic. Dazzling footwork, infectious joy, and historic clutch moments,
                    surpassing the legendary King Pelé as Brazil's all-time record international goalscorer.
                  </p>
                </div>
                <div className="mt-6 pt-4 border-t border-yellow-900/40 text-[11px] font-mono text-neutral-400 space-y-1">
                  <div className="flex justify-between">
                    <span className="text-neutral-500">Brazil Record:</span>
                    <span className="text-yellow-300 font-bold">79 Goals (Passed Pelé)</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-neutral-500">Career Honors:</span>
                    <span className="text-neutral-200">UCL Treble, Olympic Gold, Libertadores</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-neutral-500">Career Goals:</span>
                    <span className="text-yellow-300 font-bold">400+ Goals Worldwide</span>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </section>

        {/* Prize Pool Section */}
        <section id="prize-pool" className="relative">
          <div className="flex flex-col items-center text-center mb-8">
            <span className="text-xs font-mono uppercase tracking-widest text-amber-400 mb-1">
              CHAMPIONSHIP REWARDS
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
                      ? 'bg-gradient-to-b from-[#181408] via-[#0f0c05] to-[#04060B] border-2 border-amber-400 shadow-[0_0_30px_rgba(212,175,55,0.25)] p-6 sm:p-7 order-first md:order-none'
                      : 'bg-black/60 border border-white/10 hover:border-white/20 p-5 sm:p-6'
                  }`}
                >
                  <div className="flex items-center justify-between mb-4">
                    <span
                      className={`text-[11px] font-mono uppercase tracking-widest px-2.5 py-0.5 rounded ${
                        isWinner
                          ? 'bg-amber-400/20 text-amber-300 border border-amber-400/40 font-bold'
                          : 'bg-neutral-800 text-neutral-400 border border-neutral-700'
                      }`}
                    >
                      {tier.label} PLACE
                    </span>
                    <span
                      className={`font-display text-3xl ${
                        isWinner ? 'text-amber-400 font-bold' : 'text-neutral-500'
                      }`}
                    >
                      {tier.place}
                    </span>
                  </div>

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
                          isWinner ? 'text-3xl sm:text-4xl text-amber-400' : 'text-2xl sm:text-3xl text-neutral-400'
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

                  <div
                    className={`mt-5 pt-3 border-t text-[11px] font-mono uppercase tracking-widest flex items-center justify-between ${
                      isWinner
                        ? 'border-amber-400/30 text-neutral-300'
                        : 'border-white/10 text-neutral-500'
                    }`}
                  >
                    <span>{tier.label} PRIZE</span>
                    {isWinner && (
                      <span className="flex items-center space-x-1.5 text-amber-400 font-semibold">
                        <span className="w-1.5 h-1.5 rounded-full bg-amber-400" />
                        <span>CHAMPION</span>
                      </span>
                    )}
                  </div>
                </div>
              );
            })}
          </div>

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
          <div className="flex flex-col sm:flex-row sm:items-end justify-between mb-8 pb-4 border-b border-white/10 gap-4">
            <div>
              <div className="flex items-center space-x-2 text-xs font-mono uppercase tracking-widest text-amber-400 mb-1">
                <Trophy className="w-4 h-4 text-amber-400" />
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

          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            {/* Hub 1: Group Standings */}
            <Link
              to="/standings"
              className="group relative p-6 rounded-2xl bg-gradient-to-b from-[#080c14] to-[#04060B] border border-white/10 hover:border-amber-400/60 transition-all duration-300 flex flex-col justify-between shadow-lg"
            >
              <div>
                <div className="flex items-center justify-between mb-4">
                  <div className="w-12 h-12 rounded-xl bg-amber-950/40 border border-amber-400/40 flex items-center justify-center text-amber-400 group-hover:scale-110 transition-transform">
                    <BarChart3 className="w-6 h-6" />
                  </div>
                  <span className="text-[10px] font-mono px-2 py-0.5 rounded-full bg-amber-950/40 text-amber-300 border border-amber-400/40 uppercase tracking-widest">
                    15 GROUPS
                  </span>
                </div>
                <h3 className="font-display text-2xl text-white tracking-wide group-hover:text-amber-300 transition-colors">
                  GROUP STANDINGS
                </h3>
                <p className="text-xs font-mono text-neutral-400 mt-2 leading-relaxed">
                  Official points tables, goal differences, head-to-head records, and top-2 qualification cutoffs for Groups A through O.
                </p>
              </div>
              <div className="mt-6 pt-3 border-t border-white/10 flex items-center justify-between text-xs font-mono text-amber-400 group-hover:text-white transition-colors">
                <span>VIEW STANDINGS</span>
                <ArrowRight className="w-4 h-4 group-hover:translate-x-1 transition-transform" />
              </div>
            </Link>

            {/* Hub 2: Match Schedule & Fixtures */}
            <Link
              to="/fixtures"
              className="group relative p-6 rounded-2xl bg-gradient-to-b from-[#14080a] to-[#04060B] border border-white/10 hover:border-rose-500/60 transition-all duration-300 flex flex-col justify-between shadow-lg"
            >
              <div>
                <div className="flex items-center justify-between mb-4">
                  <div className="w-12 h-12 rounded-xl bg-rose-950/40 border border-rose-500/40 flex items-center justify-center text-rose-400 group-hover:scale-110 transition-transform">
                    <Calendar className="w-6 h-6" />
                  </div>
                  <span className="text-[10px] font-mono px-2 py-0.5 rounded-full bg-rose-950/40 text-rose-300 border border-rose-500/30 uppercase tracking-widest">
                    SCHEDULE
                  </span>
                </div>
                <h3 className="font-display text-2xl text-white tracking-wide group-hover:text-rose-400 transition-colors">
                  UPCOMING FIXTURES
                </h3>
                <p className="text-xs font-mono text-neutral-400 mt-2 leading-relaxed">
                  Comprehensive fixture schedules, flexible matchweek windows, pitch allocations, and team clash schedules.
                </p>
              </div>
              <div className="mt-6 pt-3 border-t border-white/10 flex items-center justify-between text-xs font-mono text-rose-400 group-hover:text-white transition-colors">
                <span>VIEW FIXTURES</span>
                <ArrowRight className="w-4 h-4 group-hover:translate-x-1 transition-transform" />
              </div>
            </Link>

            {/* Hub 3: Knockout Bracket */}
            <Link
              to="/bracket"
              className="group relative p-6 rounded-2xl bg-gradient-to-b from-[#081018] to-[#04060B] border border-white/10 hover:border-sky-400/60 transition-all duration-300 flex flex-col justify-between shadow-lg"
            >
              <div>
                <div className="flex items-center justify-between mb-4">
                  <div className="w-12 h-12 rounded-xl bg-sky-950/40 border border-sky-400/40 flex items-center justify-center text-sky-400 group-hover:scale-110 transition-transform">
                    <Trophy className="w-6 h-6" />
                  </div>
                  <span className="text-[10px] font-mono px-2 py-0.5 rounded-full bg-sky-950/40 text-sky-300 border border-sky-400/40 uppercase tracking-widest">
                    PLAYOFFS
                  </span>
                </div>
                <h3 className="font-display text-2xl text-white tracking-wide group-hover:text-sky-300 transition-colors">
                  KNOCKOUT ARENA
                </h3>
                <p className="text-xs font-mono text-neutral-400 mt-2 leading-relaxed">
                  The complete 30-team championship knockout bracket and the interactive Ceremonial Draw Desk.
                </p>
              </div>
              <div className="mt-6 pt-3 border-t border-white/10 flex items-center justify-between text-xs font-mono text-sky-400 group-hover:text-white transition-colors">
                <span>VIEW KNOCKOUT</span>
                <ArrowRight className="w-4 h-4 group-hover:translate-x-1 transition-transform" />
              </div>
            </Link>
          </div>
        </section>

        {/* Editorial Feature: The Spirit of Champions (Ronaldo Victory Fist) */}
        <section className="relative rounded-2xl overflow-hidden border border-white/10 bg-gradient-to-r from-[#0c0508] via-[#080a12] to-[#04060B] min-h-[400px] flex items-center shadow-2xl">
          <div className="absolute right-0 top-0 bottom-0 w-full lg:w-3/5 opacity-35 lg:opacity-65 pointer-events-none">
            <img
              src="/assets/backgrounds/cristiano-ronaldo-5120x2880-17335.webp"
              alt="Cristiano Ronaldo Celebrating Triumph"
              className="w-full h-full object-cover object-center filter contrast-115"
              loading="lazy"
            />
            <div className="absolute inset-0 bg-gradient-to-r from-[#0c0508] via-[#0c0508]/80 to-transparent" />
          </div>

          <div className="relative z-10 p-8 sm:p-12 lg:p-16 max-w-2xl">
            <div className="inline-block px-3 py-1 bg-gradient-to-r from-amber-500 to-rose-600 text-black font-bold text-[11px] font-mono tracking-widest uppercase mb-4 shadow-[0_0_15px_rgba(212,175,55,0.3)] rounded-md">
              THE MENTALITY OF CHAMPIONS
            </div>
            <h2 className="font-display text-4xl sm:text-5xl lg:text-6xl text-white tracking-tight leading-[0.95]">
              TACTICS OVER TALK. <br />
              PRECISION UNDER PRESSURE.
            </h2>
            <p className="mt-4 text-neutral-300 text-sm sm:text-base leading-relaxed">
              In digital football, a split-second input separates immortality from elimination.
              Inspired by the dedication and ruthless standards of the retiring legends, every Minaram Cup
              contender is forged under high-voltage campus competition.
            </p>
            <div className="mt-6">
              <Link
                to="/rules"
                className="inline-flex items-center space-x-2 text-sm font-mono uppercase tracking-widest text-amber-400 hover:text-white transition-colors"
              >
                <span>Read the Competition Rulebook</span>
                <ArrowRight className="w-4 h-4" />
              </Link>
            </div>
          </div>
        </section>

        {/* Official Sponsor Section */}
        <section className="bg-gradient-to-b from-[#080c14] to-[#04060B] border border-white/10 rounded-2xl p-8 sm:p-12 text-center">
          <div className="max-w-2xl mx-auto space-y-4">
            <span className="text-xs font-mono tracking-widest text-amber-400 uppercase flex items-center justify-center space-x-1.5">
              <Sparkles className="w-3.5 h-3.5 text-amber-400" />
              <span>PRESENTING SPONSOR</span>
              <Sparkles className="w-3.5 h-3.5 text-amber-400" />
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

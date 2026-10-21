import React, { useState, useEffect } from 'react';
import { Link, useLocation } from 'react-router-dom';
import { Menu, X, Radio, Trophy, Calendar, Users, BarChart3, GitFork, Shield, Tv } from 'lucide-react';
import { useTheme } from '../ThemeContext';
import { api } from '../api';
import { useLiveUpdates } from '../hooks/useLiveUpdates';

interface NavbarProps {
  isLiveConnected: boolean;
}

export const Navbar: React.FC<NavbarProps> = ({ isLiveConnected }) => {
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const [isStreamLive, setIsStreamLive] = useState(false);
  const location = useLocation();
  const { theme, toggleTheme } = useTheme();
  const isUCL = theme === 'ucl';

  // Check initial livestream status
  useEffect(() => {
    let isMounted = true;
    api.getLiveStream()
      .then((data) => {
        if (isMounted) {
          setIsStreamLive(Boolean(data && data.is_active && data.status === 'Live'));
        }
      })
      .catch(() => {});
    return () => { isMounted = false; };
  }, []);

  // Listen to live stream updates via SSE
  useLiveUpdates((evt) => {
    const evType = evt.event || (evt as any).type;
    if (evType === 'live_stream_updated') {
      const data = evt.data || {};
      setIsStreamLive(Boolean(data.is_active && data.status === 'Live'));
    }
  });

  const navLinks = [
    { name: 'HOME', path: '/', icon: Trophy },
    { name: 'FIXTURES', path: '/fixtures', icon: Calendar },
    { name: 'RESULTS', path: '/results', icon: BarChart3 },
    { name: 'STANDINGS', path: '/standings', icon: BarChart3 },
    { name: 'TEAMS', path: '/teams', icon: Users },
    { name: 'LIVE', path: '/live', icon: Tv },
    { name: 'KNOCKOUT / QUALIFIERS', path: '/bracket', icon: Trophy },
    { name: 'RULES', path: '/rules', icon: Shield },
  ];

  const isActive = (path: string) => {
    if (path === '/' && location.pathname !== '/') return false;
    return location.pathname.startsWith(path);
  };

  const navBg = isUCL
    ? 'bg-[#030d1f]/92 border-b border-blue-900/30 backdrop-blur-xl shadow-[0_2px_30px_rgba(30,80,220,0.12)]'
    : 'bg-[#080808]/90 border-b border-[#222222] backdrop-blur-md';

  const activeBar = isUCL
    ? 'bg-gradient-to-r from-blue-500 to-violet-500 shadow-[0_0_12px_rgba(99,102,241,0.5)]'
    : 'bg-brand-red shadow-glow-red';

  return (
    <header className={`sticky top-0 z-50 ${navBg} theme-header`}>
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-20">
          {/* Brand Crest & Title */}
          <Link to="/" className="flex items-center space-x-3.5 group">
            <div className={`relative w-12 h-12 flex items-center justify-center p-1 bg-black/60 rounded-full border transition-colors ${
              isUCL ? 'border-blue-700/60 group-hover:border-blue-400' : 'border-neutral-700/60 group-hover:border-brand-red'
            }`}>
              <img
                src="/assets/logos/transparent/minaram_logo_white.png"
                alt="Minaram Cup Crest"
                className="w-10 h-10 object-contain drop-shadow-[0_2px_8px_rgba(0,0,0,0.8)]"
              />
            </div>
            <div className="flex flex-col">
              <span className={`font-display text-2xl sm:text-3xl tracking-wider transition-colors leading-none ${
                isUCL ? 'text-blue-100 group-hover:text-blue-300' : 'text-white group-hover:text-brand-red'
              }`}>
                MINARAM CUP
              </span>
              <span className="text-[10px] font-mono tracking-widest text-neutral-400 uppercase">
                {isUCL ? 'Champions League Edition' : 'eFootball Championship'}
              </span>
            </div>
          </Link>

          {/* Desktop Navigation */}
          <nav className="hidden lg:flex items-center space-x-1">
            {navLinks.map((link) => {
              const active = isActive(link.path);
              const isLiveItem = link.name === 'LIVE';
              return (
                <Link
                  key={link.name}
                  to={link.path}
                  className={`px-3.5 py-2 font-display text-base tracking-wider transition-all duration-150 relative flex items-center space-x-1.5 ${
                    isLiveItem && isStreamLive
                      ? 'text-[#F5F5F5] font-bold'
                      : active
                        ? (isUCL ? 'text-blue-200 font-bold' : 'text-white font-bold')
                        : (isUCL ? 'text-blue-300/60 hover:text-blue-100' : 'text-neutral-400 hover:text-white')
                  }`}
                >
                  <span>{link.name}</span>
                  {isLiveItem && isStreamLive && (
                    <span className="flex items-center space-x-1 px-1.5 py-0.5 rounded bg-brand-red text-white text-[10px] font-mono font-bold tracking-widest uppercase shadow-glow-red animate-pulse">
                      <span className="w-1.5 h-1.5 rounded-full bg-white inline-block animate-ping" />
                      <span>NOW</span>
                    </span>
                  )}
                  {active && (
                    <span className={`absolute bottom-0 left-3.5 right-3.5 h-[2px] nav-active-bar ${activeBar}`} />
                  )}
                </Link>
              );
            })}
          </nav>

          {/* Right: Live indicator + Theme Toggle */}
          <div className="hidden sm:flex items-center space-x-3">
            {/* Live status */}
            <div className={`flex items-center space-x-2 px-3 py-1.5 rounded-full border text-xs font-mono ${
              isUCL ? 'bg-blue-950/50 border-blue-800/50' : 'bg-neutral-900/80 border-neutral-800'
            }`}>
              <span className="relative flex h-2 w-2">
                {isLiveConnected ? (
                  <>
                    <span className={`animate-ping absolute inline-flex h-full w-full rounded-full opacity-75 ${
                      isUCL ? 'bg-blue-400' : 'bg-emerald-400'
                    }`} />
                    <span className={`relative inline-flex rounded-full h-2 w-2 ${
                      isUCL ? 'bg-blue-500' : 'bg-emerald-500'
                    }`} />
                  </>
                ) : (
                  <span className="relative inline-flex rounded-full h-2 w-2 bg-amber-500" />
                )}
              </span>
              <span className="text-neutral-300 uppercase tracking-widest text-[11px]">
                {isLiveConnected ? 'LIVE FEED ACTIVE' : 'CONNECTING...'}
              </span>
            </div>

            {/* UEFA Champions League Official Star Badge */}
            <div className="flex items-center space-x-1.5 px-3 py-1.5 rounded-full border border-blue-600/50 bg-gradient-to-r from-blue-950 to-indigo-950 text-[11px] font-mono font-bold tracking-wider text-blue-200 shadow-[0_0_15px_rgba(59,130,246,0.3)] select-none">
              <span className="text-blue-400">★</span>
              <span className="text-white uppercase tracking-widest">UCL OFFICIAL</span>
            </div>
          </div>

          {/* Mobile menu button */}
          <div className="flex lg:hidden">
            <button
              onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
              className={`p-2 focus:outline-none ${
                isUCL ? 'text-blue-300 hover:text-blue-100' : 'text-neutral-400 hover:text-white'
              }`}
              aria-label="Toggle navigation menu"
            >
              {mobileMenuOpen ? <X className="w-6 h-6" /> : <Menu className="w-6 h-6" />}
            </button>
          </div>
        </div>
      </div>

      {/* Mobile menu dropdown */}
      {mobileMenuOpen && (
        <div className={`lg:hidden border-b px-4 pt-3 pb-6 space-y-2 ${
          isUCL ? 'bg-[#030d1f] border-blue-900/40' : 'bg-pitch-900 border-neutral-800'
        }`}>
          {navLinks.map((link) => {
            const Icon = link.icon;
            const active = isActive(link.path);
            const isLiveItem = link.name === 'LIVE';
            return (
              <Link
                key={link.name}
                to={link.path}
                onClick={() => setMobileMenuOpen(false)}
                className={`flex items-center justify-between px-4 py-3 rounded-md font-display text-lg tracking-wider ${
                  isLiveItem && isStreamLive && !active
                    ? 'bg-brand-red/20 border border-brand-red text-white'
                    : active
                      ? (isUCL ? 'bg-blue-900/60 text-blue-100 border border-blue-700/50' : 'bg-brand-red text-white')
                      : (isUCL ? 'text-blue-300/70 hover:bg-blue-900/30 hover:text-blue-100' : 'text-neutral-300 hover:bg-neutral-800 hover:text-white')
                }`}
              >
                <div className="flex items-center space-x-3">
                  <Icon className={`w-5 h-5 ${
                    isLiveItem && isStreamLive ? 'text-brand-red animate-pulse' : (isUCL ? 'text-blue-400' : 'text-neutral-400')
                  }`} />
                  <span>{link.name}</span>
                </div>
                {isLiveItem && isStreamLive && (
                  <span className="flex items-center space-x-1 px-2 py-0.5 rounded-full bg-brand-red text-white text-xs font-mono font-bold tracking-wider animate-pulse shadow-glow-red">
                    <span className="w-1.5 h-1.5 rounded-full bg-white inline-block animate-ping" />
                    <span>LIVE NOW</span>
                  </span>
                )}
              </Link>
            );
          })}
          {/* Mobile UCL Badge */}
          <div className="w-full flex items-center justify-center space-x-2 px-4 py-2.5 rounded-md text-sm font-mono font-bold uppercase tracking-wider border bg-blue-950/60 border-blue-700/50 text-blue-200 shadow-[0_0_15px_rgba(59,130,246,0.2)]">
            <span className="text-blue-400">★</span>
            <span>UEFA CHAMPIONS LEAGUE EDITION</span>
          </div>
          <div className="pt-2 border-t border-neutral-800">
            <div className="flex items-center space-x-2 px-4 py-2 text-xs font-mono text-neutral-400">
              <Radio className={`w-4 h-4 ${isLiveConnected ? (isUCL ? 'text-blue-400 animate-pulse' : 'text-emerald-500 animate-pulse') : 'text-amber-500'}`} />
              <span>{isLiveConnected ? 'Real-Time Sync Connected' : 'Sync Reconnecting...'}</span>
            </div>
          </div>
        </div>
      )}
    </header>
  );
};

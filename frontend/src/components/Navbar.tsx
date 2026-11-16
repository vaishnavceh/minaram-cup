import React, { useState, useEffect } from 'react';
import { Link, useLocation } from 'react-router-dom';
import { Menu, X, Radio, Trophy, Calendar, Users, BarChart3, GitFork, Shield, Tv, Sparkles, Laptop } from 'lucide-react';
import { api } from '../api';
import { useLiveUpdates } from '../hooks/useLiveUpdates';

interface NavbarProps {
  isLiveConnected: boolean;
}

export const Navbar: React.FC<NavbarProps> = ({ isLiveConnected }) => {
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const [isStreamLive, setIsStreamLive] = useState(false);
  const [syncInfo, setSyncInfo] = useState<{ last_sync_time: string; last_sync_status: string }>({
    last_sync_time: '2026-11-16 17:02:13',
    last_sync_status: 'SUCCESS',
  });
  const location = useLocation();

  const fetchSyncStatus = () => {
    api.getSyncStatus()
      .then((data) => {
        if (data && data.last_sync_time) {
          setSyncInfo({
            last_sync_time: data.last_sync_time,
            last_sync_status: data.last_sync_status || 'SUCCESS',
          });
        }
      })
      .catch(() => {});
  };

  // Check initial livestream and sync status
  useEffect(() => {
    let isMounted = true;
    api.getLiveStream()
      .then((data) => {
        if (isMounted) {
          setIsStreamLive(Boolean(data && data.is_active && data.status === 'Live'));
        }
      })
      .catch(() => {});

    fetchSyncStatus();
    const interval = setInterval(fetchSyncStatus, 25000);
    return () => {
      isMounted = false;
      clearInterval(interval);
    };
  }, []);

  // Listen to live stream and cloud sync updates via SSE
  useLiveUpdates((evt) => {
    const evType = evt.event || (evt as any).type;
    if (evType === 'live_stream_updated') {
      const data = evt.data || {};
      setIsStreamLive(Boolean(data.is_active && data.status === 'Live'));
    }
    if (['cloud_sync', 'standings_updated', 'fixtures_updated', 'match_updated', 'knockout_updated'].includes(evType)) {
      fetchSyncStatus();
    }
  });

  const formatSyncTimeAndDate = (rawTime?: string): string => {
    if (!rawTime) return '17:02:13 / 16-11-2026';
    try {
      if (rawTime.includes(' ')) {
        const [datePart, timePart] = rawTime.split(' ');
        const [year, month, day] = datePart.split('-');
        const formattedDate = day && month && year ? `${day}-${month}-${year}` : datePart;
        return `${timePart} / ${formattedDate}`;
      }
      const d = new Date(rawTime);
      if (!isNaN(d.getTime())) {
        const time = d.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit', hour12: false });
        const day = String(d.getDate()).padStart(2, '0');
        const month = String(d.getMonth() + 1).padStart(2, '0');
        const year = d.getFullYear();
        return `${time} / ${day}-${month}-${year}`;
      }
      return rawTime;
    } catch {
      return rawTime || '17:02:13 / 16-11-2026';
    }
  };

  const navLinks = [
    { name: 'HOME', path: '/', icon: Trophy },
    { name: 'FIXTURES', path: '/fixtures', icon: Calendar },
    { name: 'RESULTS', path: '/results', icon: BarChart3 },
    { name: 'STANDINGS', path: '/standings', icon: BarChart3 },
    { name: 'BRACKET', path: '/bracket', icon: GitFork },
    { name: 'TEAMS', path: '/teams', icon: Users },
    { name: 'LIVE', path: '/live', icon: Tv },
    { name: 'RULES', path: '/rules', icon: Shield },
  ];

  const isActive = (path: string) => {
    if (path === '/' && location.pathname !== '/') return false;
    return location.pathname.startsWith(path);
  };

  const navBg = 'bg-[#04060B]/92 border-b border-white/10 backdrop-blur-md shadow-[0_4px_30px_rgba(0,0,0,0.8)]';
  const activeBar = 'bg-gradient-to-r from-amber-400 via-amber-300 to-amber-500 shadow-[0_0_12px_rgba(212,175,55,0.7)]';

  return (
    <header className={`sticky top-0 z-50 ${navBg} theme-header`}>
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-20">
          {/* Brand Crest & Title */}
          <Link to="/" className="flex items-center space-x-3.5 group">
            <div className="relative w-12 h-12 flex items-center justify-center p-1 bg-black/80 rounded-full border border-amber-400/40 group-hover:border-amber-400 transition-colors shadow-[0_0_15px_rgba(212,175,55,0.2)]">
              <img
                src="/assets/logos/transparent/minaram_logo_white.png"
                alt="Minaram Cup Crest"
                className="w-10 h-10 object-contain drop-shadow-[0_2px_8px_rgba(0,0,0,0.8)]"
              />
            </div>
            <div className="flex flex-col">
              <span className="font-display text-2xl sm:text-3xl tracking-wider text-white group-hover:text-amber-300 transition-colors leading-none">
                MINARAM CUP
              </span>
              <span className="text-[10px] font-mono tracking-widest text-amber-400/90 uppercase font-semibold mt-0.5">
                Legends Tribute Edition
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
                      ? 'text-[#F8FAFC] font-bold'
                      : active
                        ? 'text-amber-300 font-bold'
                        : 'text-neutral-400 hover:text-white'
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

          {/* Right: Last PC-to-Server Sync + Live Feed + Legends Tribute */}
          <div className="hidden sm:flex items-center space-x-2.5">
            {/* Last PC to Server Sync Time Widget */}
            <div
              className="flex items-center space-x-2 px-3 py-1.5 rounded-full border border-emerald-500/30 bg-emerald-950/40 text-xs font-mono text-emerald-300 shadow-[0_0_15px_rgba(16,185,129,0.15)] group transition-all hover:border-emerald-400/60 cursor-default"
              title={`Latest PC to Cloud Server Synchronization: ${syncInfo.last_sync_time} (${syncInfo.last_sync_status})`}
            >
              <span className="relative flex h-2 w-2">
                <span className="animate-ping absolute inline-flex h-full w-full rounded-full opacity-75 bg-emerald-400" />
                <span className="relative inline-flex rounded-full h-2 w-2 bg-emerald-500" />
              </span>
              <Laptop className="w-3.5 h-3.5 text-emerald-400 shrink-0" />
              <div className="flex items-center space-x-1.5 leading-none">
                <span className="text-neutral-400 text-[10px] tracking-wider font-semibold">
                  Latest sync:
                </span>
                <span className="text-white text-[11px] font-bold tabular-nums">
                  {formatSyncTimeAndDate(syncInfo.last_sync_time)}
                </span>
              </div>
            </div>

            {/* Commemorative Tribute Badge */}
            <div className="hidden xl:flex items-center space-x-1.5 px-3 py-1.5 rounded-full border border-amber-400/40 bg-gradient-to-r from-amber-950/60 to-black text-[11px] font-mono font-bold tracking-wider text-amber-300 shadow-[0_0_15px_rgba(212,175,55,0.2)] select-none">
              <Sparkles className="w-3.5 h-3.5 text-amber-400" />
              <span className="text-white uppercase tracking-widest">TRIBUTE TO LEGENDS</span>
            </div>
          </div>

          {/* Mobile menu button */}
          <div className="flex lg:hidden">
            <button
              onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
              className="p-2 text-neutral-400 hover:text-white focus:outline-none"
              aria-label="Toggle navigation menu"
            >
              {mobileMenuOpen ? <X className="w-6 h-6" /> : <Menu className="w-6 h-6" />}
            </button>
          </div>
        </div>
      </div>

      {/* Mobile menu dropdown */}
      {mobileMenuOpen && (
        <div className="lg:hidden border-b px-4 pt-3 pb-6 space-y-2 bg-[#04060B] border-white/10">
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
                      ? 'bg-amber-400/20 text-amber-300 border border-amber-400/40'
                      : 'text-neutral-300 hover:bg-neutral-900 hover:text-white'
                }`}
              >
                <div className="flex items-center space-x-3">
                  <Icon className={`w-5 h-5 ${
                    isLiveItem && isStreamLive ? 'text-brand-red animate-pulse' : active ? 'text-amber-400' : 'text-neutral-400'
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
          
          {/* Mobile PC-to-Server Sync Row */}
          <div className="flex items-center justify-between px-4 py-2.5 rounded-md border border-emerald-500/30 bg-emerald-950/20 text-xs font-mono">
            <div className="flex items-center space-x-2 text-neutral-300">
              <Laptop className="w-4 h-4 text-emerald-400" />
              <span className="tracking-wider text-neutral-400 text-[11px]">Latest sync:</span>
            </div>
            <span className="font-bold text-emerald-300 tabular-nums text-xs">
              {formatSyncTimeAndDate(syncInfo.last_sync_time)}
            </span>
          </div>

          {/* Mobile Legends Badge */}
          <div className="w-full flex items-center justify-center space-x-2 px-4 py-2.5 rounded-md text-sm font-mono font-bold uppercase tracking-wider border bg-amber-950/40 border-amber-400/40 text-amber-300 shadow-[0_0_15px_rgba(212,175,55,0.2)]">
            <Sparkles className="w-4 h-4 text-amber-400" />
            <span>HONORING MESSI · RONALDO · NEYMAR</span>
          </div>
          
          <div className="pt-2 border-t border-white/10">
            <div className="flex items-center space-x-2 px-4 py-2 text-xs font-mono text-neutral-400">
              <Radio className={`w-4 h-4 ${isLiveConnected ? 'text-emerald-500 animate-pulse' : 'text-amber-500'}`} />
              <span>{isLiveConnected ? 'Real-Time Sync Connected' : 'Sync Reconnecting...'}</span>
            </div>
          </div>
        </div>
      )}
    </header>
  );
};

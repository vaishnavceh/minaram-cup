import React, { useState } from 'react';
import { Link, useLocation } from 'react-router-dom';
import { Menu, X, Radio, Trophy, Calendar, Users, BarChart3, GitFork, Shield } from 'lucide-react';

interface NavbarProps {
  isLiveConnected: boolean;
}

export const Navbar: React.FC<NavbarProps> = ({ isLiveConnected }) => {
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const location = useLocation();

  const navLinks = [
    { name: 'HOME', path: '/', icon: Trophy },
    { name: 'FIXTURES', path: '/fixtures', icon: Calendar },
    { name: 'RESULTS', path: '/results', icon: BarChart3 },
    { name: 'STANDINGS', path: '/standings', icon: BarChart3 },
    { name: 'TEAMS', path: '/teams', icon: Users },
    { name: 'KNOCKOUT / QUALIFIERS', path: '/bracket', icon: Trophy },
    { name: 'RULES', path: '/rules', icon: Shield },
  ];

  const isActive = (path: string) => {
    if (path === '/' && location.pathname !== '/') return false;
    return location.pathname.startsWith(path);
  };

  return (
    <header className="sticky top-0 z-50 bg-[#080808]/90 backdrop-blur-md border-b border-[#222222]">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-20">
          {/* Brand Crest & Title */}
          <Link to="/" className="flex items-center space-x-3.5 group">
            <div className="relative w-12 h-12 flex items-center justify-center p-1 bg-black/60 rounded-full border border-neutral-700/60 group-hover:border-brand-red transition-colors">
              <img
                src="/assets/logos/transparent/minaram_logo_white.png"
                alt="Minaram Cup Crest"
                className="w-10 h-10 object-contain drop-shadow-[0_2px_8px_rgba(0,0,0,0.8)]"
              />
            </div>
            <div className="flex flex-col">
              <span className="font-display text-2xl sm:text-3xl tracking-wider text-white group-hover:text-brand-red transition-colors leading-none">
                MINARAM CUP
              </span>
              <span className="text-[10px] font-mono tracking-widest text-neutral-400 uppercase">
                eFootball Championship
              </span>
            </div>
          </Link>

          {/* Desktop Navigation */}
          <nav className="hidden lg:flex items-center space-x-1">
            {navLinks.map((link) => {
              const active = isActive(link.path);
              return (
                <Link
                  key={link.name}
                  to={link.path}
                  className={`px-3.5 py-2 font-display text-base tracking-wider transition-all duration-150 relative ${
                    active
                      ? 'text-white font-bold'
                      : 'text-neutral-400 hover:text-white'
                  }`}
                >
                  {link.name}
                  {active && (
                    <span className="absolute bottom-0 left-3.5 right-3.5 h-[2px] bg-brand-red shadow-glow-red" />
                  )}
                </Link>
              );
            })}
          </nav>

          {/* Live Sync Status indicator */}
          <div className="hidden sm:flex items-center space-x-3">
            <div className="flex items-center space-x-2 px-3 py-1.5 rounded-full bg-neutral-900/80 border border-neutral-800 text-xs font-mono">
              <span className="relative flex h-2 w-2">
                {isLiveConnected ? (
                  <>
                    <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
                    <span className="relative inline-flex rounded-full h-2 w-2 bg-emerald-500"></span>
                  </>
                ) : (
                  <span className="relative inline-flex rounded-full h-2 w-2 bg-amber-500"></span>
                )}
              </span>
              <span className="text-neutral-300 uppercase tracking-widest text-[11px]">
                {isLiveConnected ? 'LIVE FEED ACTIVE' : 'CONNECTING...'}
              </span>
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
        <div className="lg:hidden bg-pitch-900 border-b border-neutral-800 px-4 pt-3 pb-6 space-y-2">
          {navLinks.map((link) => {
            const Icon = link.icon;
            const active = isActive(link.path);
            return (
              <Link
                key={link.name}
                to={link.path}
                onClick={() => setMobileMenuOpen(false)}
                className={`flex items-center space-x-3 px-4 py-3 rounded-md font-display text-lg tracking-wider ${
                  active
                    ? 'bg-brand-red text-white'
                    : 'text-neutral-300 hover:bg-neutral-800 hover:text-white'
                }`}
              >
                <Icon className="w-5 h-5 text-neutral-400" />
                <span>{link.name}</span>
              </Link>
            );
          })}
          <div className="pt-2 border-t border-neutral-800">
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

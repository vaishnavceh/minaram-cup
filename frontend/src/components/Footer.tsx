import React from 'react';
import { Link } from 'react-router-dom';
import { ShieldCheck, Heart, Sparkles, Lock } from 'lucide-react';

export const Footer: React.FC = () => {
  return (
    <footer className="relative overflow-hidden bg-gradient-to-t from-[#020514] via-[#030d2a]/95 to-[#020617] border-t border-blue-900/50 text-blue-200/80 mt-20 pt-16 pb-12">
      {/* Background Star Texture */}
      <div className="absolute inset-0 opacity-15 pointer-events-none">
        <img
          src="/assets/backgrounds/ucl_stars_dark.jpg"
          alt="UEFA Champions League Background"
          className="w-full h-full object-cover object-bottom"
        />
        <div className="absolute inset-0 bg-gradient-to-t from-[#020514] via-transparent to-[#020617]" />
      </div>

      <div className="relative z-10 max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-12 mb-12">
          {/* Brand Info */}
          <div className="md:col-span-2 space-y-4">
            <div className="flex items-center space-x-3">
              <img
                src="/assets/logos/transparent/minaram_logo_white.png"
                alt="Minaram Cup Logo"
                className="w-12 h-12 object-contain"
              />
              <div>
                <h3 className="font-display text-2xl tracking-wider text-white">MINARAM CUP</h3>
                <p className="text-xs font-mono text-neutral-400 uppercase tracking-widest">
                  Premier eFootball Championship
                </p>
              </div>
            </div>
            <p className="text-sm text-neutral-400 leading-relaxed max-w-md">
              The flagship competitive eFootball tournament of TKM College of Engineering.
              Bringing together the finest digital football managers and tacticians for high-stakes competition.
            </p>
            <div className="pt-2 flex items-center space-x-2 text-xs font-mono text-neutral-400">
              <span className="w-2 h-2 rounded-full bg-brand-red inline-block" />
              <span>Organized by <strong className="text-white">minarathintememe</strong></span>
            </div>
          </div>

          {/* Quick Links */}
          <div>
            <h4 className="font-display text-lg tracking-wider text-white mb-4 border-b border-neutral-800 pb-2">
              COMPETITION
            </h4>
            <ul className="space-y-2 text-sm">
              <li>
                <Link to="/fixtures" className="hover:text-brand-red transition-colors">
                  Match Schedule & Fixtures
                </Link>
              </li>
              <li>
                <Link to="/results" className="hover:text-brand-red transition-colors">
                  Latest Results & Scores
                </Link>
              </li>
              <li>
                <Link to="/standings" className="hover:text-brand-red transition-colors">
                  Group Stage Standings
                </Link>
              </li>
              <li>
                <Link to="/bracket" className="hover:text-brand-red transition-colors">
                  Knockout / Qualifiers
                </Link>
              </li>
              <li>
                <Link to="/teams" className="hover:text-brand-red transition-colors">
                  Registered Teams & Managers
                </Link>
              </li>
              <li>
                <Link to="/rules" className="hover:text-brand-red transition-colors">
                  Official Tournament Rules
                </Link>
              </li>
            </ul>
          </div>

          {/* Official Sponsor */}
          <div>
            <h4 className="font-display text-lg tracking-wider text-white mb-4 border-b border-neutral-800 pb-2 flex items-center space-x-2">
              <Sparkles className="w-4 h-4 text-brand-gold" />
              <span>OFFICIAL SPONSOR</span>
            </h4>
            <div className="p-4 rounded-lg bg-neutral-900/60 border border-neutral-800 hover:border-neutral-700 transition-colors flex flex-col items-center justify-center space-y-3">
              <img
                src="/assets/logos/transparent/akhadha_sponsor_transparent.png"
                alt="AKHADHA Sponsor"
                className="h-16 w-auto object-contain filter drop-shadow-md"
              />
              <span className="font-display text-sm tracking-widest text-neutral-300 uppercase">
                AKHADHA
              </span>
              <p className="text-[11px] text-center text-neutral-400">
                Official Title Partner of Minaram Cup eFootball
              </p>
            </div>
          </div>
        </div>

        {/* Bottom Bar */}
        <div className="pt-8 border-t border-neutral-800/80 flex flex-col sm:flex-row items-center justify-between text-xs text-neutral-400 space-y-4 sm:space-y-0">
          <div className="flex items-center space-x-1">
            <span>© {new Date().getFullYear()} MINARAM CUP. Crafted with pride for TKM College of Engineering.</span>
          </div>

          <div className="flex items-center space-x-6">
            <span className="flex items-center space-x-1 text-neutral-400">
              <ShieldCheck className="w-3.5 h-3.5 text-neutral-400" />
              <span>Verified Tournament Integrity</span>
            </span>
            <Link
              to="/admin"
              className="flex items-center space-x-1 text-neutral-400 hover:text-neutral-300 transition-colors"
              title="Official Admin Portal"
            >
              <Lock className="w-3 h-3" />
              <span>Admin Access</span>
            </Link>
          </div>
        </div>
      </div>
    </footer>
  );
};

import React, { useEffect } from 'react';
import { HallOfFamePlayer } from '../../data/hallOfFamePlayers';
import { X, Award, Shield, Globe, Calendar, Building2, ExternalLink, Sparkles, CheckCircle2, AlertCircle } from 'lucide-react';

interface PlayerDetailsModalProps {
  player: HallOfFamePlayer | null;
  onClose: () => void;
}

export const PlayerDetailsModal: React.FC<PlayerDetailsModalProps> = ({ player, onClose }) => {
  // Close on Escape key press
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape') onClose();
    };
    if (player) {
      window.addEventListener('keydown', handleKeyDown);
      document.body.style.overflow = 'hidden';
    }
    return () => {
      window.removeEventListener('keydown', handleKeyDown);
      document.body.style.overflow = 'auto';
    };
  }, [player, onClose]);

  if (!player) return null;

  const positionThemes = {
    Forward: 'from-rose-500/20 border-rose-500/40 text-rose-300',
    Midfielder: 'from-amber-400/20 border-amber-400/40 text-amber-300',
    Defender: 'from-sky-400/20 border-sky-400/40 text-sky-300',
    Goalkeeper: 'from-emerald-400/20 border-emerald-400/40 text-emerald-300',
  };

  const themeClass = positionThemes[player.position] || positionThemes.Forward;

  return (
    <div
      role="dialog"
      aria-modal="true"
      aria-labelledby="modal-player-name"
      className="fixed inset-0 z-50 flex items-center justify-center p-3 sm:p-6 overflow-y-auto bg-black/85 backdrop-blur-md animate-fadeIn"
      onClick={onClose}
    >
      {/* Modal Box */}
      <div
        onClick={(e) => e.stopPropagation()}
        className="relative w-full max-w-3xl rounded-3xl overflow-hidden bg-gradient-to-b from-[#0A101D] to-[#04060B] border border-amber-400/30 shadow-[0_25px_60px_-15px_rgba(0,0,0,0.9)] max-h-[92vh] flex flex-col md:flex-row my-auto"
      >
        {/* Close Button */}
        <button
          type="button"
          onClick={onClose}
          aria-label="Close legend dossier"
          className="absolute top-4 right-4 z-30 p-2.5 rounded-full bg-black/70 hover:bg-neutral-800 border border-white/15 text-neutral-300 hover:text-white transition-all cursor-pointer shadow-lg"
        >
          <X className="w-5 h-5" />
        </button>

        {/* Left / Top: High-Def Player Portrait */}
        <div className="relative w-full md:w-5/12 h-72 sm:h-80 md:h-auto min-h-[300px] shrink-0 bg-pitch-950 overflow-hidden">
          <img
            src={player.image}
            alt={player.name}
            className="w-full h-full object-cover object-top filter brightness-95"
          />
          {/* Gradients */}
          <div className="absolute inset-0 bg-gradient-to-t from-[#0A101D] via-transparent to-transparent md:hidden" />
          <div className="hidden md:block absolute inset-0 bg-gradient-to-r from-transparent via-transparent to-[#0A101D]" />

          {/* Positional Watermark */}
          <div className="absolute bottom-4 left-4 z-10 flex items-center space-x-2">
            <span className="px-3 py-1 rounded-full bg-black/80 border border-amber-400/40 text-xs font-mono font-bold text-amber-300 uppercase tracking-widest backdrop-blur-md shadow-lg">
              {player.position}
            </span>
            <span className="px-2.5 py-1 rounded-full bg-black/80 border border-white/20 text-xs font-mono text-neutral-200 backdrop-blur-md flex items-center space-x-1.5">
              <span>{player.flagEmoji}</span>
              <span className="font-semibold">{player.nationality}</span>
            </span>
          </div>
        </div>

        {/* Right: Full Dossier & Statistics */}
        <div className="p-6 sm:p-8 flex-grow flex flex-col justify-between overflow-y-auto space-y-6">
          <div>
            {/* Header Badge */}
            <div className="inline-flex items-center space-x-2 px-3 py-1 rounded-full bg-amber-950/40 border border-amber-400/30 text-[11px] font-mono text-amber-300 uppercase tracking-wider mb-3">
              <Sparkles className="w-3.5 h-3.5 text-amber-400" />
              <span>MINARAM CUP · INDUCTED LEGEND</span>
            </div>

            {/* Name */}
            <h2 id="modal-player-name" className="font-display text-4xl sm:text-5xl text-white tracking-wide uppercase leading-tight">
              {player.name}
            </h2>
            <p className="text-sm font-mono text-amber-300 font-medium tracking-wide uppercase mt-1">
              {player.detailedPosition} · {player.era}
            </p>

            {/* Biography */}
            <p className="mt-4 text-sm sm:text-base text-neutral-300 leading-relaxed font-normal">
              {player.bio}
            </p>
          </div>

          {/* Dossier Grid Details */}
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 text-xs font-mono">
            {/* Club Retirement Status */}
            <div className="p-3.5 rounded-xl bg-black/60 border border-white/10 flex flex-col justify-between">
              <span className="text-neutral-400 uppercase tracking-wider text-[10px]">Club Status</span>
              <div className="mt-1 flex items-center space-x-2 font-bold text-white text-sm">
                {player.clubRetirementStatus === 'Retired' ? (
                  <>
                    <span className="w-2 h-2 rounded-full bg-neutral-400" />
                    <span>Retired {player.retirementYear ? `(${player.retirementYear})` : ''}</span>
                  </>
                ) : (
                  <>
                    <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
                    <span className="text-emerald-400">Active Competitor</span>
                  </>
                )}
              </div>
            </div>

            {/* International Retirement Status */}
            <div className="p-3.5 rounded-xl bg-black/60 border border-white/10 flex flex-col justify-between">
              <span className="text-neutral-400 uppercase tracking-wider text-[10px]">International Status</span>
              <div className="mt-1 flex items-center space-x-2 font-bold text-white text-sm">
                {player.internationalRetirementStatus === 'Retired' ? (
                  <>
                    <span className="w-2 h-2 rounded-full bg-neutral-400" />
                    <span>Retired Nationally</span>
                  </>
                ) : (
                  <>
                    <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
                    <span className="text-emerald-400">Active International</span>
                  </>
                )}
              </div>
            </div>

            {/* Primary Era */}
            <div className="p-3.5 rounded-xl bg-black/60 border border-white/10 flex flex-col justify-between">
              <span className="text-neutral-400 uppercase tracking-wider text-[10px]">Career Era</span>
              <div className="mt-1 font-bold text-amber-300 text-sm flex items-center space-x-1.5">
                <Calendar className="w-4 h-4 text-amber-400 shrink-0" />
                <span>{player.era}</span>
              </div>
            </div>

            {/* Nationality */}
            <div className="p-3.5 rounded-xl bg-black/60 border border-white/10 flex flex-col justify-between">
              <span className="text-neutral-400 uppercase tracking-wider text-[10px]">Nationality</span>
              <div className="mt-1 font-bold text-white text-sm flex items-center space-x-2">
                <span>{player.flagEmoji}</span>
                <span>{player.nationality} ({player.countryCode})</span>
              </div>
            </div>
          </div>

          {/* Famous Clubs */}
          <div className="space-y-2">
            <span className="text-[11px] font-mono text-neutral-400 uppercase tracking-wider flex items-center space-x-1.5">
              <Building2 className="w-3.5 h-3.5 text-neutral-400" />
              <span>Defining Club Tenures</span>
            </span>
            <div className="flex flex-wrap gap-2">
              {player.famousClubs.map((club) => (
                <span
                  key={club}
                  className="px-3 py-1.5 rounded-lg bg-neutral-900/90 border border-amber-400/20 text-xs font-mono text-neutral-200 font-semibold shadow-sm"
                >
                  {club}
                </span>
              ))}
            </div>
          </div>

          {/* Attribution & Source Licensing */}
          <div className="pt-3 border-t border-white/10 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-2 text-[10px] font-mono text-neutral-500">
            <span>Photo Source: {player.imageAttribution}</span>
            <span className="text-amber-400/80">Minaram Cup Historical Archives</span>
          </div>
        </div>
      </div>
    </div>
  );
};

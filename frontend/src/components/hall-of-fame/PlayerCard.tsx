import React, { useState } from 'react';
import { HallOfFamePlayer } from '../../data/hallOfFamePlayers';
import { Shield, Sparkles, Building2, Calendar, Award } from 'lucide-react';

interface PlayerCardProps {
  player: HallOfFamePlayer;
  onClick: (player: HallOfFamePlayer) => void;
}

export const PlayerCard: React.FC<PlayerCardProps> = ({ player, onClick }) => {
  const [imageError, setImageError] = useState(false);

  // Positional styling theme for eFootball / EA FC collectible feel
  const positionThemes = {
    Forward: {
      badge: 'bg-rose-500/20 border-rose-500/60 text-rose-300',
      glow: 'group-hover:shadow-[0_0_30px_rgba(244,63,94,0.35)]',
      border: 'group-hover:border-rose-400/70',
      pill: 'bg-rose-950/70 text-rose-300 border-rose-500/40',
      accent: '#F43F5E',
    },
    Midfielder: {
      badge: 'bg-amber-400/20 border-amber-400/60 text-amber-300',
      glow: 'group-hover:shadow-[0_0_30px_rgba(212,175,55,0.4)]',
      border: 'group-hover:border-amber-400/80',
      pill: 'bg-amber-950/70 text-amber-300 border-amber-500/40',
      accent: '#D4AF37',
    },
    Defender: {
      badge: 'bg-sky-400/20 border-sky-400/60 text-sky-300',
      glow: 'group-hover:shadow-[0_0_30px_rgba(56,189,248,0.35)]',
      border: 'group-hover:border-sky-400/70',
      pill: 'bg-sky-950/70 text-sky-300 border-sky-500/40',
      accent: '#38BDF8',
    },
    Goalkeeper: {
      badge: 'bg-emerald-400/20 border-emerald-400/60 text-emerald-300',
      glow: 'group-hover:shadow-[0_0_30px_rgba(16,185,129,0.35)]',
      border: 'group-hover:border-emerald-400/70',
      pill: 'bg-emerald-950/70 text-emerald-300 border-emerald-500/40',
      accent: '#10B981',
    },
  };

  const theme = positionThemes[player.position] || positionThemes.Forward;

  // Initials for fallback avatar
  const initials = player.name
    .split(' ')
    .map((p) => p[0])
    .filter(Boolean)
    .slice(0, 2)
    .join('')
    .toUpperCase();

  const isFullyRetired =
    player.clubRetirementStatus === 'Retired' &&
    player.internationalRetirementStatus === 'Retired';

  return (
    <div
      role="button"
      tabIndex={0}
      onClick={() => onClick(player)}
      onKeyDown={(e) => {
        if (e.key === 'Enter' || e.key === ' ') {
          e.preventDefault();
          onClick(player);
        }
      }}
      aria-label={`View Hall of Fame details for ${player.name}`}
      className={`group relative flex flex-col justify-between h-[420px] rounded-2xl overflow-hidden cursor-pointer bg-[#070B14] border border-white/10 ${theme.border} ${theme.glow} transition-all duration-300 hover:-translate-y-2 select-none`}
    >
      {/* Background Image Portrait */}
      <div className="absolute inset-0 z-0 overflow-hidden bg-gradient-to-b from-[#0F172A] to-[#04060B]">
        {!imageError ? (
          <img
            src={player.image}
            alt={player.name}
            loading="lazy"
            decoding="async"
            onError={() => setImageError(true)}
            className="w-full h-full object-cover object-top filter brightness-95 group-hover:scale-105 transition-transform duration-700 ease-out"
          />
        ) : (
          <div className="w-full h-full flex flex-col items-center justify-center p-6 bg-gradient-to-b from-neutral-900 via-neutral-950 to-black text-center">
            <div className="w-24 h-24 rounded-full border-2 border-amber-400/50 bg-black/60 flex items-center justify-center mb-4 shadow-[0_0_20px_rgba(212,175,55,0.2)]">
              <span className="font-display text-4xl text-white tracking-widest">{initials}</span>
            </div>
            <span className="text-xs font-mono text-neutral-400 uppercase tracking-widest">{player.detailedPosition}</span>
          </div>
        )}

        {/* Cinematic Card Gradient Vignettes for text contrast */}
        <div className="absolute inset-0 bg-gradient-to-t from-[#04060B] via-[#04060B]/60 to-transparent" />
        <div className="absolute inset-0 bg-gradient-to-b from-[#04060B]/80 via-transparent to-transparent h-28" />
        <div className="absolute inset-x-0 bottom-0 h-44 bg-gradient-to-t from-[#04060B] via-[#04060B]/95 to-transparent" />
      </div>

      {/* Top Header Row: Position, Nation Flag, Era */}
      <div className="relative z-10 p-3.5 flex items-center justify-between">
        {/* Position & Country Flag Badge */}
        <div className="flex items-center space-x-1.5">
          <span
            className={`px-2.5 py-1 rounded-md text-[11px] font-mono font-bold uppercase tracking-wider border backdrop-blur-md shadow-sm ${theme.badge}`}
          >
            {player.position === 'Goalkeeper'
              ? 'GK'
              : player.position === 'Defender'
              ? 'DEF'
              : player.position === 'Midfielder'
              ? 'MID'
              : 'FWD'}
          </span>
          <span
            className="px-2 py-0.5 rounded-md bg-black/60 border border-white/15 text-sm backdrop-blur-md flex items-center space-x-1"
            title={player.nationality}
          >
            <span>{player.flagEmoji}</span>
            <span className="text-[10px] font-mono text-neutral-300 font-semibold uppercase">{player.countryCode}</span>
          </span>
        </div>

        {/* Era Tag */}
        <span className="px-2 py-0.5 rounded-md bg-black/70 border border-white/10 text-[10px] font-mono text-amber-300/90 font-medium backdrop-blur-md">
          {player.era}
        </span>
      </div>

      {/* Subtle Card Shine Overlay on Hover */}
      <div className="absolute inset-0 z-10 pointer-events-none opacity-0 group-hover:opacity-100 transition-opacity duration-500 bg-gradient-to-tr from-transparent via-white/5 to-transparent" />

      {/* Bottom Content Area */}
      <div className="relative z-10 p-4 pt-0 flex flex-col justify-end space-y-2">
        {/* Player Name */}
        <div>
          <h3 className="font-display text-2xl sm:text-[26px] leading-[0.95] text-white tracking-wide uppercase drop-shadow-[0_2px_8px_rgba(0,0,0,0.9)] group-hover:text-amber-300 transition-colors">
            {player.name}
          </h3>
          <p className="text-[11px] font-mono text-neutral-300 tracking-wider uppercase mt-1 truncate">
            {player.detailedPosition}
          </p>
        </div>

        {/* Famous Clubs Chips */}
        <div className="flex flex-wrap items-center gap-1">
          {player.famousClubs.slice(0, 3).map((club) => (
            <span
              key={club}
              className="inline-flex items-center px-1.5 py-0.5 rounded bg-black/75 border border-white/10 text-[10px] font-mono text-neutral-300 backdrop-blur-sm"
            >
              {club}
            </span>
          ))}
          {player.famousClubs.length > 3 && (
            <span className="text-[9px] font-mono text-neutral-400">+{player.famousClubs.length - 3}</span>
          )}
        </div>

        {/* Bottom Bar: Retirement Status & Year */}
        <div className="pt-2 border-t border-white/10 flex items-center justify-between text-[11px] font-mono">
          <div className="flex items-center space-x-1.5">
            {isFullyRetired ? (
              <span className="inline-flex items-center text-neutral-400">
                <span className="w-1.5 h-1.5 rounded-full bg-neutral-500 mr-1.5" />
                <span>Retired {player.retirementYear ? `(${player.retirementYear})` : ''}</span>
              </span>
            ) : (
              <span className="inline-flex items-center text-emerald-400 font-semibold">
                <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse mr-1.5" />
                <span>Club Active</span>
              </span>
            )}
          </div>

          <span className="text-[10px] text-amber-400/90 uppercase tracking-widest font-semibold flex items-center space-x-1 group-hover:translate-x-0.5 transition-transform">
            <span>DOSSIER</span>
            <span>&rarr;</span>
          </span>
        </div>
      </div>
    </div>
  );
};

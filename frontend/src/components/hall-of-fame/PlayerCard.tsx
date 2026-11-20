import React, { useState } from 'react';
import { HallOfFamePlayer } from '../../data/hallOfFamePlayers';

interface PlayerCardProps {
  player: HallOfFamePlayer;
  onClick: (player: HallOfFamePlayer) => void;
}

export const PlayerCard: React.FC<PlayerCardProps> = ({ player, onClick }) => {
  const [imageError, setImageError] = useState(false);

  // Positional interactive aura glows
  const auraGlows: Record<string, string> = {
    Forward: 'group-hover:drop-shadow-[0_15px_30px_rgba(244,63,94,0.4)]',
    Midfielder: 'group-hover:drop-shadow-[0_15px_30px_rgba(212,175,55,0.45)]',
    Defender: 'group-hover:drop-shadow-[0_15px_30px_rgba(56,189,248,0.4)]',
    Goalkeeper: 'group-hover:drop-shadow-[0_15px_30px_rgba(16,185,129,0.4)]',
  };

  const aura = auraGlows[player.position] || auraGlows.Forward;

  // Initials for fallback if image fails
  const initials = player.name
    .split(' ')
    .map((p) => p[0])
    .filter(Boolean)
    .slice(0, 2)
    .join('')
    .toUpperCase();

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
      aria-label={`View stats and dossier for ${player.name}`}
      className="group relative flex flex-col items-center justify-center cursor-pointer select-none py-1.5 transition-all duration-300 hover:-translate-y-2.5 focus:outline-none"
    >
      {/* Background Soft Glow on Hover */}
      <div className="absolute inset-x-8 top-10 bottom-10 rounded-full bg-gradient-to-tr from-amber-500/10 via-yellow-400/5 to-rose-500/10 blur-2xl opacity-0 group-hover:opacity-100 transition-opacity duration-500 pointer-events-none" />

      {/* Collectible Card Display (Clean, direct image, no box clutter) */}
      <div className="relative w-full max-w-[240px] sm:max-w-[260px] aspect-[429/600] flex items-center justify-center">
        {!imageError ? (
          <img
            src={player.image}
            alt={`${player.name} EA FC Collectible Card`}
            loading="lazy"
            decoding="async"
            onError={() => setImageError(true)}
            className={`w-full h-full object-contain filter drop-shadow-[0_10px_20px_rgba(0,0,0,0.85)] ${aura} group-hover:scale-105 active:scale-95 transition-all duration-300 ease-out`}
          />
        ) : (
          /* Elegant fallback card shield if image is unavailable */
          <div className="w-full h-full rounded-2xl bg-gradient-to-b from-[#1E293B] to-[#0A0F1D] border-2 border-amber-400/40 p-4 flex flex-col items-center justify-between shadow-[0_15px_30px_rgba(0,0,0,0.8)] group-hover:scale-105 transition-transform">
            <div className="flex items-center justify-between w-full">
              <span className="text-xs font-mono font-bold text-amber-300">{player.position}</span>
              <span className="text-sm">{player.flagEmoji}</span>
            </div>
            <div className="w-20 h-20 rounded-full border-2 border-amber-400/50 bg-black/60 flex items-center justify-center shadow-lg">
              <span className="font-display text-3xl text-white">{initials}</span>
            </div>
            <div className="text-center w-full">
              <h4 className="font-display text-xl text-white uppercase truncate">{player.name}</h4>
              <p className="text-[10px] font-mono text-neutral-400 uppercase">{player.detailedPosition}</p>
            </div>
          </div>
        )}

        {/* Subtle Shine Flash on Hover */}
        <div className="absolute inset-0 rounded-2xl pointer-events-none opacity-0 group-hover:opacity-100 transition-opacity duration-500 bg-gradient-to-tr from-transparent via-white/10 to-transparent" />
      </div>

      {/* Clean Player Identifier Label Below Card */}
      <div className="mt-2 text-center opacity-85 group-hover:opacity-100 transition-opacity">
        <span className="text-xs font-mono text-neutral-300 uppercase tracking-wider group-hover:text-amber-300 transition-colors flex items-center justify-center space-x-1.5">
          <span>{player.flagEmoji}</span>
          <span className="font-semibold text-white drop-shadow-[0_1px_3px_rgba(0,0,0,0.9)]">{player.name}</span>
        </span>
      </div>
    </div>
  );
};

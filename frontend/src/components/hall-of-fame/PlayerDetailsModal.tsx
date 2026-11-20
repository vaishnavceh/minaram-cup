import React, { useEffect } from 'react';
import { HallOfFamePlayer } from '../../data/hallOfFamePlayers';
import { X, Sparkles, Building2, Calendar, Shield, Activity, BarChart2 } from 'lucide-react';

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

  // Position-tailored stat metrics for the EA FC Stat Screen
  const positionStats: Record<string, { label: string; value: number }[]> = {
    Forward: [
      { label: 'Finishing & Shot Power', value: 94 },
      { label: 'Attacking Positioning', value: 96 },
      { label: 'Dribbling & Agility', value: 92 },
      { label: 'Pace & Acceleration', value: 90 },
      { label: 'Playmaking & Vision', value: 88 },
      { label: 'Clutch / Big Match Mentality', value: 98 },
    ],
    Midfielder: [
      { label: 'Passing Precision & Curve', value: 95 },
      { label: 'Vision & Tactical IQ', value: 97 },
      { label: 'Ball Control & Composure', value: 94 },
      { label: 'Stamina & Work Rate', value: 92 },
      { label: 'Long Range Shooting', value: 87 },
      { label: 'Defensive Transition', value: 85 },
    ],
    Defender: [
      { label: 'Standing & Sliding Tackle', value: 96 },
      { label: 'Interceptions & Anticipation', value: 95 },
      { label: 'Physicality & Strength', value: 93 },
      { label: 'Aerial Duel Dominance', value: 92 },
      { label: 'Defensive Awareness', value: 97 },
      { label: 'Composure Under Pressure', value: 94 },
    ],
    Goalkeeper: [
      { label: 'Reflexes & Shot Stopping', value: 96 },
      { label: 'Diving & Reach', value: 94 },
      { label: 'Positioning & Command', value: 97 },
      { label: 'Handling & Catching', value: 93 },
      { label: 'Kicking & Distribution', value: 89 },
      { label: '1v1 Box Authority', value: 95 },
    ],
  };

  const stats = positionStats[player.position] || positionStats.Forward;

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
        className="relative w-full max-w-4xl rounded-3xl overflow-hidden bg-gradient-to-b from-[#0B1120] via-[#050811] to-[#020307] border border-amber-400/40 shadow-[0_25px_60px_-15px_rgba(0,0,0,0.95)] max-h-[92vh] flex flex-col md:flex-row my-auto"
      >
        {/* Close Button */}
        <button
          type="button"
          onClick={onClose}
          aria-label="Close stat dossier"
          className="absolute top-4 right-4 z-30 p-2.5 rounded-full bg-black/70 hover:bg-neutral-800 border border-white/20 text-neutral-300 hover:text-white transition-all cursor-pointer shadow-lg"
        >
          <X className="w-5 h-5" />
        </button>

        {/* Left: High-Def EA FC Collectible Card Showcase */}
        <div className="relative w-full md:w-5/12 h-96 md:h-auto min-h-[380px] shrink-0 bg-gradient-to-b from-[#0F172A]/30 to-[#04060B] overflow-hidden flex items-center justify-center p-6">
          {/* Subtle Ambient Radial Glow */}
          <div className="absolute inset-0 bg-radial from-amber-500/15 via-transparent to-transparent pointer-events-none" />

          {/* Collectible Card */}
          <img
            src={player.image}
            alt={player.name}
            className="max-h-full max-w-full object-contain filter drop-shadow-[0_20px_40px_rgba(0,0,0,0.95)] transition-transform duration-500 hover:scale-105"
          />

          {/* Positional Badge at Bottom of Image Pane */}
          <div className="absolute bottom-4 left-4 z-10 flex items-center space-x-2">
            <span className="px-3 py-1 rounded-full bg-black/85 border border-amber-400/40 text-xs font-mono font-bold text-amber-300 uppercase tracking-widest backdrop-blur-md shadow-lg">
              {player.position}
            </span>
            <span className="px-2.5 py-1 rounded-full bg-black/85 border border-white/20 text-xs font-mono text-neutral-200 backdrop-blur-md flex items-center space-x-1.5">
              <span>{player.flagEmoji}</span>
              <span className="font-semibold">{player.nationality}</span>
            </span>
          </div>
        </div>

        {/* Right: EA FC Stat Screen & Dossier */}
        <div className="p-6 sm:p-8 flex-grow flex flex-col justify-between overflow-y-auto space-y-5">
          <div>
            {/* Header Telemetry Badge */}
            <div className="inline-flex items-center space-x-2 px-3 py-1 rounded-full bg-amber-950/60 border border-amber-400/35 text-[11px] font-mono text-amber-300 uppercase tracking-wider mb-2.5">
              <Sparkles className="w-3.5 h-3.5 text-amber-400" />
              <span>EA SPORTS FC · IMMORTAL STAT DOSSIER</span>
            </div>

            {/* Name & Subtitle */}
            <h2 id="modal-player-name" className="font-display text-4xl sm:text-5xl text-white tracking-wide uppercase leading-tight">
              {player.name}
            </h2>
            <p className="text-sm font-mono text-amber-300 font-medium tracking-wide uppercase mt-1">
              {player.detailedPosition} · {player.era}
            </p>

            {/* Legend Bio */}
            <p className="mt-3 text-sm text-neutral-300 leading-relaxed font-normal">
              {player.bio}
            </p>
          </div>

          {/* In-Game Key Attributes Telemetry */}
          <div className="space-y-2.5 pt-1">
            <div className="flex items-center justify-between text-xs font-mono text-neutral-300 uppercase tracking-wider">
              <span className="flex items-center space-x-1.5 text-amber-300 font-semibold">
                <BarChart2 className="w-3.5 h-3.5 text-amber-400" />
                <span>Attribute Ratings Breakdown</span>
              </span>
              <span className="text-neutral-400 text-[10px]">ULTIMATE TIER</span>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 text-xs font-mono">
              {stats.map((st) => (
                <div key={st.label} className="p-2.5 rounded-lg bg-black/60 border border-white/10 flex flex-col justify-between">
                  <div className="flex items-center justify-between text-[11px] mb-1">
                    <span className="text-neutral-300 truncate pr-2">{st.label}</span>
                    <span className="font-bold text-amber-300">{st.value}</span>
                  </div>
                  <div className="w-full bg-neutral-800 rounded-full h-1.5 overflow-hidden">
                    <div
                      className="bg-gradient-to-r from-amber-500 to-amber-300 h-1.5 rounded-full"
                      style={{ width: `${st.value}%` }}
                    />
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Dossier Career Status Grid */}
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 text-xs font-mono">
            {/* Club Status */}
            <div className="p-2.5 rounded-lg bg-black/60 border border-white/10 flex flex-col justify-between">
              <span className="text-neutral-400 uppercase tracking-wider text-[10px]">Club Status</span>
              <div className="mt-1 font-bold text-white text-xs truncate">
                {player.clubRetirementStatus === 'Retired' ? (
                  <span className="text-neutral-300">Retired {player.retirementYear ? `(${player.retirementYear})` : ''}</span>
                ) : (
                  <span className="text-emerald-400">Club Active</span>
                )}
              </div>
            </div>

            {/* International Status */}
            <div className="p-2.5 rounded-lg bg-black/60 border border-white/10 flex flex-col justify-between">
              <span className="text-neutral-400 uppercase tracking-wider text-[10px]">International</span>
              <div className="mt-1 font-bold text-white text-xs truncate">
                {player.internationalRetirementStatus === 'Retired' ? (
                  <span className="text-neutral-300">Retired (Int.)</span>
                ) : (
                  <span className="text-emerald-400">National Active</span>
                )}
              </div>
            </div>

            {/* Primary Era */}
            <div className="p-2.5 rounded-lg bg-black/60 border border-white/10 flex flex-col justify-between">
              <span className="text-neutral-400 uppercase tracking-wider text-[10px]">Era</span>
              <div className="mt-1 font-bold text-amber-300 text-xs truncate">
                {player.era}
              </div>
            </div>

            {/* Nationality */}
            <div className="p-2.5 rounded-lg bg-black/60 border border-white/10 flex flex-col justify-between">
              <span className="text-neutral-400 uppercase tracking-wider text-[10px]">Nation</span>
              <div className="mt-1 font-bold text-white text-xs flex items-center space-x-1 truncate">
                <span>{player.flagEmoji}</span>
                <span>{player.countryCode}</span>
              </div>
            </div>
          </div>

          {/* Famous Clubs */}
          <div className="space-y-1.5">
            <span className="text-[11px] font-mono text-neutral-400 uppercase tracking-wider flex items-center space-x-1.5">
              <Building2 className="w-3.5 h-3.5 text-neutral-400" />
              <span>Key Club Tenures</span>
            </span>
            <div className="flex flex-wrap gap-1.5">
              {player.famousClubs.map((club) => (
                <span
                  key={club}
                  className="px-2.5 py-1 rounded-md bg-neutral-900/90 border border-amber-400/20 text-[11px] font-mono text-neutral-200 font-semibold shadow-sm"
                >
                  {club}
                </span>
              ))}
            </div>
          </div>

          {/* Attribution Footer */}
          <div className="pt-2 border-t border-white/10 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-1 text-[10px] font-mono text-neutral-500">
            <span>Card Asset: Official EA FC 27 Item / Minaram Cup Archives</span>
            <span className="text-amber-400/80">Interactive Collectible Dossier</span>
          </div>
        </div>
      </div>
    </div>
  );
};

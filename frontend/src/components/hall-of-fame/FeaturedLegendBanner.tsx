import React, { useState } from 'react';
import { HallOfFamePlayer } from '../../data/hallOfFamePlayers';
import { Sparkles, Shuffle, ChevronLeft, ChevronRight, Award, Shield, ArrowRight } from 'lucide-react';

interface FeaturedLegendBannerProps {
  featuredPlayers: HallOfFamePlayer[];
  onSelectPlayer: (player: HallOfFamePlayer) => void;
}

export const FeaturedLegendBanner: React.FC<FeaturedLegendBannerProps> = ({
  featuredPlayers,
  onSelectPlayer,
}) => {
  const [index, setIndex] = useState(0);

  if (!featuredPlayers || featuredPlayers.length === 0) return null;

  const current = featuredPlayers[index] || featuredPlayers[0];

  const handleNext = () => {
    setIndex((prev) => (prev + 1) % featuredPlayers.length);
  };

  const handlePrev = () => {
    setIndex((prev) => (prev - 1 + featuredPlayers.length) % featuredPlayers.length);
  };

  const handleRandom = () => {
    const candidates = featuredPlayers
      .map((_, i) => i)
      .filter((i) => i !== index);
    const chosen = candidates[Math.floor(Math.random() * candidates.length)] || 0;
    setIndex(chosen);
  };

  return (
    <div className="relative rounded-3xl overflow-hidden border border-amber-400/40 bg-gradient-to-b from-[#09101E] via-[#050811] to-[#04060B] shadow-[0_10px_50px_rgba(212,175,55,0.18)] mb-12">
      {/* Subtle Ambient Radial Lighting */}
      <div className="absolute top-0 right-1/4 w-96 h-96 bg-amber-400/10 rounded-full blur-[100px] pointer-events-none" />
      <div className="absolute bottom-0 left-1/4 w-96 h-96 bg-rose-500/10 rounded-full blur-[100px] pointer-events-none" />

      <div className="relative z-10 flex flex-col lg:flex-row items-center justify-between p-6 sm:p-10 lg:p-12 gap-8">
        {/* Left: Headline & Bio */}
        <div className="flex-1 space-y-5 text-center lg:text-left">
          {/* Eyebrow Pill */}
          <div className="inline-flex items-center space-x-2 px-3.5 py-1.5 rounded-full bg-amber-950/60 border border-amber-400/50 text-xs font-mono text-amber-300 uppercase tracking-widest backdrop-blur-md shadow-sm">
            <Sparkles className="w-3.5 h-3.5 text-amber-400 fill-current" />
            <span className="font-bold text-white">SPOTLIGHT TITAN · ICON OF THE ERA</span>
            <span className="text-amber-400 font-bold">({index + 1}/{featuredPlayers.length})</span>
          </div>

          {/* Player Name */}
          <div className="space-y-1">
            <div className="flex items-center justify-center lg:justify-start space-x-2.5 text-sm sm:text-base font-mono text-amber-300 font-bold uppercase tracking-wider">
              <span>{current.flagEmoji}</span>
              <span>{current.nationality}</span>
              <span>•</span>
              <span>{current.position}</span>
              <span>•</span>
              <span className="text-neutral-400">{current.era}</span>
            </div>
            <h2 className="font-display text-5xl sm:text-6xl md:text-7xl lg:text-8xl text-white uppercase tracking-tight leading-[0.92] drop-shadow-2xl">
              {current.name}
            </h2>
          </div>

          {/* Bio Summary */}
          <p className="max-w-2xl text-neutral-200 text-sm sm:text-base md:text-lg font-normal leading-relaxed drop-shadow mx-auto lg:mx-0">
            {current.bio}
          </p>

          {/* Key Clubs */}
          <div className="flex flex-wrap items-center justify-center lg:justify-start gap-2 pt-1">
            <span className="text-xs font-mono text-neutral-400 uppercase tracking-wider mr-1">Defining Clubs:</span>
            {current.famousClubs.map((club) => (
              <span
                key={club}
                className="px-3 py-1 rounded-lg bg-black/60 border border-white/15 text-xs font-mono text-neutral-200 font-semibold"
              >
                {club}
              </span>
            ))}
          </div>

          {/* Actions: View Dossier & Rotate */}
          <div className="flex flex-wrap items-center justify-center lg:justify-start gap-3.5 pt-4">
            <button
              type="button"
              onClick={() => onSelectPlayer(current)}
              className="px-6 py-3 rounded-xl bg-gradient-to-r from-amber-500 to-amber-600 hover:from-amber-400 hover:to-amber-500 text-black font-display text-lg tracking-wider transition-all shadow-[0_0_25px_rgba(212,175,55,0.4)] flex items-center space-x-2 cursor-pointer"
            >
              <span>EXPLORE FULL DOSSIER</span>
              <ArrowRight className="w-5 h-5" />
            </button>

            <button
              type="button"
              onClick={handleRandom}
              className="px-4 py-3 rounded-xl bg-neutral-900/90 hover:bg-neutral-800 border border-amber-400/30 text-amber-300 font-mono text-xs uppercase tracking-wider transition-all flex items-center space-x-2 cursor-pointer"
              title="Shuffle featured legend"
            >
              <Shuffle className="w-4 h-4 text-amber-400" />
              <span>ROTATE TITAN</span>
            </button>
          </div>
        </div>

        {/* Right: Dramatic Showcase Card */}
        <div className="relative w-full max-w-xs sm:max-w-sm lg:max-w-md shrink-0 flex flex-col items-center">
          <div
            role="button"
            tabIndex={0}
            onClick={() => onSelectPlayer(current)}
            onKeyDown={(e) => {
              if (e.key === 'Enter' || e.key === ' ') {
                e.preventDefault();
                onSelectPlayer(current);
              }
            }}
            className="group relative w-72 sm:w-80 h-[440px] flex items-center justify-center cursor-pointer transition-transform duration-500 hover:scale-105"
          >
            {/* Glowing Golden Aura Behind Card */}
            <div className="absolute inset-4 bg-gradient-to-tr from-amber-500/25 via-yellow-500/15 to-amber-600/25 rounded-full blur-2xl group-hover:blur-3xl transition-all duration-700 pointer-events-none" />

            {/* Authentic Collectible Card */}
            <img
              src={current.image}
              alt={current.name}
              className="max-h-full max-w-full object-contain filter drop-shadow-[0_20px_45px_rgba(0,0,0,0.95)] transition-transform duration-500 group-hover:-translate-y-2"
            />
          </div>

          {/* Carousel Next/Prev Controls */}
          <div className="flex items-center space-x-3 mt-4">
            <button
              type="button"
              onClick={handlePrev}
              aria-label="Previous featured legend"
              className="p-2 rounded-full bg-black/80 border border-white/20 text-neutral-300 hover:text-white hover:border-amber-400/50 transition-colors cursor-pointer"
            >
              <ChevronLeft className="w-5 h-5" />
            </button>

            <div className="flex items-center space-x-1.5">
              {featuredPlayers.slice(0, 10).map((_, i) => (
                <button
                  key={i}
                  type="button"
                  onClick={() => setIndex(i)}
                  aria-label={`Go to slide ${i + 1}`}
                  className={`w-2 h-2 rounded-full transition-all cursor-pointer ${
                    i === index ? 'w-6 bg-amber-400 shadow-[0_0_8px_rgba(212,175,55,0.8)]' : 'bg-neutral-600 hover:bg-neutral-400'
                  }`}
                />
              ))}
            </div>

            <button
              type="button"
              onClick={handleNext}
              aria-label="Next featured legend"
              className="p-2 rounded-full bg-black/80 border border-white/20 text-neutral-300 hover:text-white hover:border-amber-400/50 transition-colors cursor-pointer"
            >
              <ChevronRight className="w-5 h-5" />
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

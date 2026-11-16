import React, { useState } from 'react';

export const HERO_BACKGROUNDS: string[] = [
  '/assets/backgrounds/lionel-messi-world-3840x2160-19207.jpg',
  '/assets/backgrounds/cristiano-ronaldo-3840x2160-14010.jpg',
  '/assets/backgrounds/kylian-mbappe-real-3840x2160-27350.jpg',
  '/assets/backgrounds/lamine-yamal-fifa-3840x2160-27561.jpg',
  '/assets/backgrounds/real-madrid-cf-8k-3840x2160-15503.jpg',
  '/assets/backgrounds/lamine-yamal-lionel-3840x2160-27106.jpg',
  '/assets/backgrounds/cristiano-ronaldo-5120x2880-17335.webp',
  '/assets/backgrounds/neymar-black-studio.webp',
  '/assets/backgrounds/wp4900925-football-pc-4k-wallpapers.jpg',
  '/assets/backgrounds/cristiano-ronaldo-5120x2880-17345.webp',
  '/assets/backgrounds/neymar-debut-celebration.webp',
  '/assets/backgrounds/ea-sports-fc-26-standard-edition-game-dz-1366x768.jpg',
];

interface CinematicHeroBackgroundProps {
  fallbackImage?: string;
  overlayOpacity?: number;
}

export const CinematicHeroBackground: React.FC<CinematicHeroBackgroundProps> = ({
  fallbackImage = '/assets/backgrounds/lionel-messi-world-3840x2160-19207.jpg',
  overlayOpacity = 0.72,
}) => {
  // Random selection on initial visit/refresh from Bgs
  const [bgSrc] = useState<string>(() => {
    try {
      const last = sessionStorage.getItem('minaram_hero_bg');
      const filtered = HERO_BACKGROUNDS.filter((b) => b !== last);
      const chosen = filtered[Math.floor(Math.random() * filtered.length)] || HERO_BACKGROUNDS[0];
      sessionStorage.setItem('minaram_hero_bg', chosen);
      return chosen;
    } catch {
      return fallbackImage;
    }
  });

  return (
    <div className="absolute inset-0 z-0 overflow-hidden pointer-events-none select-none">
      {/* Pristine Fullscreen Hero Background — 100% Free of any slide options or controls */}
      <img
        src={bgSrc || fallbackImage}
        alt="Minaram Cup Hero Background"
        className="absolute inset-0 w-full h-full object-cover object-center filter brightness-65 contrast-110 pointer-events-none"
        fetchPriority="high"
        decoding="sync"
      />

      {/* Cinematic Dark Navy & Obsidian Color Grading Overlays */}
      <div
        className="absolute inset-0 bg-gradient-to-t from-[#04060B] via-[#04060B]/60 to-[#04060B]/40 pointer-events-none"
        style={{ opacity: overlayOpacity }}
      />
      <div className="absolute inset-0 bg-[radial-gradient(circle_at_center,transparent_0%,#04060B_82%)] pointer-events-none" />
    </div>
  );
};

// Aliases for compatibility
export const CinematicSlideshowBackground = CinematicHeroBackground;
export const CinematicVideoBackground = CinematicHeroBackground;

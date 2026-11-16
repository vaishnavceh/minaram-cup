import React, { useState, useEffect } from 'react';

export const HERO_BACKGROUNDS: string[] = [
  '/assets/backgrounds/lionel-messi-world-3840x2160-19207.jpg',
  '/assets/backgrounds/cristiano-ronaldo-3840x2160-14010.jpg',
  '/assets/backgrounds/kylian-mbappe-real-3840x2160-27350.jpg',
  '/assets/backgrounds/neymar-debut-celebration.webp',
  '/assets/backgrounds/lamine-yamal-fifa-3840x2160-27561.jpg',
  '/assets/backgrounds/real-madrid-cf-8k-3840x2160-15503.jpg',
  '/assets/backgrounds/cristiano-ronaldo-5120x2880-17335.webp',
  '/assets/backgrounds/neymar-black-studio.webp',
  '/assets/backgrounds/lamine-yamal-lionel-3840x2160-27106.jpg',
  '/assets/backgrounds/cristiano-ronaldo-5120x2880-17345.webp',
  '/assets/backgrounds/wp4900925-football-pc-4k-wallpapers.jpg',
  '/assets/backgrounds/cristiano-ronaldo-manchester-united-4k-ti-1366x768.jpg',
  '/assets/backgrounds/ea-sports-fc-26-standard-edition-game-dz-1366x768.jpg',
  '/assets/backgrounds/ea-sports-fc-27-game-r8-1366x768.jpg',
  '/assets/backgrounds/gerard-pique-aw-1366x768.jpg',
  '/assets/backgrounds/kylian-mbappe-new-0c-1366x768.jpg',
  '/assets/backgrounds/07.webp',
  '/assets/backgrounds/647955465162470813.webp',
  '/assets/backgrounds/843228730252078209.webp',
];

interface CinematicHeroBackgroundProps {
  fallbackImage?: string;
  overlayOpacity?: number;
  slideInterval?: number; // Slide change time in ms (default: 3000ms = 3 seconds)
}

export const CinematicHeroBackground: React.FC<CinematicHeroBackgroundProps> = ({
  fallbackImage = '/assets/backgrounds/lionel-messi-world-3840x2160-19207.jpg',
  overlayOpacity = 0.72,
  slideInterval = 3000,
}) => {
  const [currentIdx, setCurrentIdx] = useState(0);
  const [underIdx, setUnderIdx] = useState(0);

  // Preload all background images on mount to ensure instant 3-second transitions with zero lag
  useEffect(() => {
    HERO_BACKGROUNDS.forEach((src) => {
      const img = new Image();
      img.src = src;
    });
  }, []);

  // Automatic slide rotation every 3 seconds with zero controls or buttons
  useEffect(() => {
    const timer = setInterval(() => {
      setCurrentIdx((prev) => {
        setUnderIdx(prev);
        return (prev + 1) % HERO_BACKGROUNDS.length;
      });
    }, slideInterval);

    return () => clearInterval(timer);
  }, [slideInterval]);

  const underSrc = HERO_BACKGROUNDS[underIdx] || fallbackImage;
  const currentSrc = HERO_BACKGROUNDS[currentIdx] || fallbackImage;

  return (
    <div className="absolute inset-0 z-0 overflow-hidden pointer-events-none select-none">
      {/* Base Layer: Sustains visual continuity underneath during crossfades */}
      <img
        src={underSrc}
        alt="Hero Background Layer Base"
        className="absolute inset-0 w-full h-full object-cover object-center filter brightness-65 contrast-110 pointer-events-none z-0"
        decoding="async"
      />

      {/* Active Layer: Crossfades smoothly on each 3-second slide transition */}
      <img
        key={currentSrc}
        src={currentSrc}
        alt="Hero Background Layer Active"
        className="absolute inset-0 w-full h-full object-cover object-center filter brightness-65 contrast-110 pointer-events-none z-10 animate-hero-crossfade"
        fetchPriority="high"
        decoding="async"
      />

      {/* Cinematic Dark Navy & Obsidian Color Grading Overlays */}
      <div
        className="absolute inset-0 z-20 bg-gradient-to-t from-[#04060B] via-[#04060B]/60 to-[#04060B]/40 pointer-events-none"
        style={{ opacity: overlayOpacity }}
      />
      <div className="absolute inset-0 z-20 bg-[radial-gradient(circle_at_center,transparent_0%,#04060B_82%)] pointer-events-none" />
    </div>
  );
};

// Aliases for compatibility
export const CinematicSlideshowBackground = CinematicHeroBackground;
export const CinematicVideoBackground = CinematicHeroBackground;

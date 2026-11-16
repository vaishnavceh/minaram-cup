import React, { useState, useEffect, useRef, useCallback } from 'react';
import { Sparkles, ChevronLeft, ChevronRight, Pause, Play, Images } from 'lucide-react';

export interface LegendSlide {
  id: string;
  image: string;
  mobileImage?: string;
  legend: string;
  title: string;
  badge: string;
  era: string;
  tagline: string;
}

export const LEGEND_SLIDES: LegendSlide[] = [
  // LIONEL MESSI
  {
    id: 'messi-world-cup',
    image: '/assets/backgrounds/legends/messi-world-cup-neon.webp',
    mobileImage: '/assets/backgrounds/legends/mobile/messi-world-cup-neon.webp',
    legend: 'Lionel Messi',
    title: 'World Champion — Lusail 2022',
    badge: 'ALBICELESTE · #10',
    era: 'World Cup 2022 Champion',
    tagline: 'The crowning glory of the Greatest of All Time.',
  },
  {
    id: 'messi-hero',
    image: '/assets/backgrounds/legends/efootball-messi-hero.webp',
    mobileImage: '/assets/backgrounds/legends/mobile/efootball-messi-hero.webp',
    legend: 'Lionel Messi',
    title: 'The Master of eFootball',
    badge: 'ALBICELESTE · #10',
    era: '8x Ballon d’Or Legacy',
    tagline: 'Pure football genius in motion.',
  },
  {
    id: 'messi-trophy',
    image: '/assets/backgrounds/legends/messi-trophy-crowd.webp',
    mobileImage: '/assets/backgrounds/legends/mobile/messi-trophy-crowd.webp',
    legend: 'Lionel Messi',
    title: 'Glory Beyond Time',
    badge: 'CHAMPION · ICON',
    era: 'Immortal Captain',
    tagline: 'Carried the dreams of millions to the pinnacle.',
  },
  {
    id: 'messi-heaven',
    image: '/assets/backgrounds/legends/messi-heaven-pointing.webp',
    mobileImage: '/assets/backgrounds/legends/mobile/messi-heaven-pointing.webp',
    legend: 'Lionel Messi',
    title: 'To The Heavens',
    badge: 'LEGACY · ICON',
    era: 'Signature Celebration',
    tagline: 'Every goal dedicated to where it all began.',
  },

  // CRISTIANO RONALDO
  {
    id: 'ronaldo-victory',
    image: '/assets/backgrounds/legends/ronaldo-victory-fist.webp',
    mobileImage: '/assets/backgrounds/legends/mobile/ronaldo-victory-fist.webp',
    legend: 'Cristiano Ronaldo',
    title: 'The Unstoppable Quinas',
    badge: 'PORTUGAL · #7',
    era: 'Euro Champion & Record Scorer',
    tagline: 'Relentless work ethic, unmatched hunger, eternal greatness.',
  },
  {
    id: 'ronaldo-anthem',
    image: '/assets/backgrounds/legends/ronaldo-anthem-smile.webp',
    mobileImage: '/assets/backgrounds/legends/mobile/ronaldo-anthem-smile.webp',
    legend: 'Cristiano Ronaldo',
    title: 'Pride of a Nation',
    badge: 'QUINAS · #7',
    era: 'All-Time International Top Scorer',
    tagline: 'Leading with fire, passion, and pride.',
  },
  {
    id: 'ronaldo-pitch-walk',
    image: '/assets/backgrounds/legends/ronaldo-pitch-walk.webp',
    mobileImage: '/assets/backgrounds/legends/mobile/ronaldo-pitch-walk.webp',
    legend: 'Cristiano Ronaldo',
    title: 'The Colosseum Walks',
    badge: 'CR7 · COMMANDER',
    era: '5x Champions League Winner',
    tagline: 'Step onto any pitch in the world and conquer it.',
  },
  {
    id: 'ronaldo-messi-rivalry',
    image: '/assets/backgrounds/legends/ronaldo-messi-tribute-walk.webp',
    mobileImage: '/assets/backgrounds/legends/mobile/ronaldo-messi-tribute-walk.webp',
    legend: 'The Dual Kings',
    title: 'The Golden Rivalry',
    badge: 'CR7 × LM10',
    era: 'An Unrepeatable Era',
    tagline: 'Two titans pushed each other to superhuman heights.',
  },

  // NEYMAR JR
  {
    id: 'neymar-debut',
    image: '/assets/backgrounds/legends/neymar-debut-celebration.webp',
    mobileImage: '/assets/backgrounds/legends/mobile/neymar-debut-celebration.webp',
    legend: 'Neymar Jr',
    title: 'The Soul of Samba',
    badge: 'SELEÇÃO · #10',
    era: 'Brazil All-Time Top Scorer',
    tagline: 'Dancing past defenders with the rhythm of Brazil.',
  },
  {
    id: 'neymar-rain',
    image: '/assets/backgrounds/legends/neymar-rain-portrait.webp',
    mobileImage: '/assets/backgrounds/legends/mobile/neymar-rain-portrait.webp',
    legend: 'Neymar Jr',
    title: 'Through The Storm',
    badge: 'SANTOS TO PARIS · #11',
    era: 'Treble Winner & Olympic Gold',
    tagline: 'Pure flair, breathtaking artistry, fearless creativity.',
  },
  {
    id: 'neymar-black',
    image: '/assets/backgrounds/legends/neymar-black-studio.webp',
    mobileImage: '/assets/backgrounds/legends/mobile/neymar-black-studio.webp',
    legend: 'Neymar Jr',
    title: 'Modern Football Art',
    badge: 'MAGICIAN · #10',
    era: 'Global Icon',
    tagline: 'The joy of street football brought to the world stage.',
  },
];

interface CinematicSlideshowBackgroundProps {
  fallbackImage?: string;
  overlayOpacity?: number;
  autoPlayInterval?: number; // milliseconds per slide (default 5000ms)
}

export const CinematicSlideshowBackground: React.FC<CinematicSlideshowBackgroundProps> = ({
  fallbackImage = '/assets/backgrounds/legends/efootball-messi-hero.webp',
  overlayOpacity = 0.72,
  autoPlayInterval = 5500,
}) => {
  // Start on a randomized slide on first load for variety
  const [currentIndex, setCurrentIndex] = useState<number>(() => {
    try {
      const last = sessionStorage.getItem('minaram_last_slide_idx');
      const lastIdx = last !== null ? parseInt(last, 10) : -1;
      const candidates = Array.from({ length: LEGEND_SLIDES.length }, (_, i) => i).filter(
        (i) => i !== lastIdx
      );
      const chosen = candidates[Math.floor(Math.random() * candidates.length)];
      sessionStorage.setItem('minaram_last_slide_idx', String(chosen));
      return chosen;
    } catch {
      return 0;
    }
  });

  const [isPlaying, setIsPlaying] = useState<boolean>(true);
  const [progress, setProgress] = useState<number>(0);
  const progressIntervalRef = useRef<any>(null);
  const timerStartRef = useRef<number>(Date.now());

  // Slide navigation handlers
  const nextSlide = useCallback(() => {
    setCurrentIndex((prev) => {
      const next = (prev + 1) % LEGEND_SLIDES.length;
      try {
        sessionStorage.setItem('minaram_last_slide_idx', String(next));
      } catch {}
      return next;
    });
    setProgress(0);
    timerStartRef.current = Date.now();
  }, []);

  const prevSlide = useCallback(() => {
    setCurrentIndex((prev) => {
      const next = (prev - 1 + LEGEND_SLIDES.length) % LEGEND_SLIDES.length;
      try {
        sessionStorage.setItem('minaram_last_slide_idx', String(next));
      } catch {}
      return next;
    });
    setProgress(0);
    timerStartRef.current = Date.now();
  }, []);

  // Preload upcoming slide images for instantaneous crossfade
  useEffect(() => {
    const nextIdx = (currentIndex + 1) % LEGEND_SLIDES.length;
    const prevIdx = (currentIndex - 1 + LEGEND_SLIDES.length) % LEGEND_SLIDES.length;

    [LEGEND_SLIDES[nextIdx].image, LEGEND_SLIDES[prevIdx].image].forEach((src) => {
      if (src) {
        const img = new Image();
        img.src = src;
      }
    });
  }, [currentIndex]);

  // Smooth progress bar and automated slide progression
  useEffect(() => {
    if (!isPlaying) {
      if (progressIntervalRef.current) clearInterval(progressIntervalRef.current);
      return;
    }

    timerStartRef.current = Date.now();
    setProgress(0);

    const stepMs = 50;
    progressIntervalRef.current = setInterval(() => {
      const elapsed = Date.now() - timerStartRef.current;
      const pct = Math.min(100, (elapsed / autoPlayInterval) * 100);
      setProgress(pct);

      if (elapsed >= autoPlayInterval) {
        nextSlide();
      }
    }, stepMs);

    return () => {
      if (progressIntervalRef.current) clearInterval(progressIntervalRef.current);
    };
  }, [currentIndex, isPlaying, autoPlayInterval, nextSlide]);

  const currentSlide = LEGEND_SLIDES[currentIndex];

  return (
    <div className="absolute inset-0 z-0 overflow-hidden pointer-events-none select-none">
      {/* Fallback base image */}
      <img
        src={fallbackImage}
        alt="Minaram Cup Hero"
        className="absolute inset-0 w-full h-full object-cover object-center filter brightness-60 contrast-115 scale-105 pointer-events-none"
        fetchPriority="high"
        decoding="sync"
      />

      {/* Render all slides with smooth CSS cross-fade and Ken Burns scale effect */}
      {LEGEND_SLIDES.map((slide, idx) => {
        const isActive = idx === currentIndex;
        return (
          <div
            key={slide.id}
            className={`absolute inset-0 transition-opacity duration-1000 ease-in-out pointer-events-none ${
              isActive ? 'opacity-100' : 'opacity-0'
            }`}
          >
            <picture>
              {slide.mobileImage && (
                <source media="(max-width: 640px)" srcSet={slide.mobileImage} type="image/webp" />
              )}
              <img
                src={slide.image}
                alt={`${slide.legend} — ${slide.title}`}
                className={`w-full h-full object-cover object-center filter brightness-65 contrast-115 transition-transform duration-[6500ms] ease-out ${
                  isActive ? 'scale-105' : 'scale-100'
                }`}
                loading={idx === 0 ? 'eager' : 'lazy'}
                decoding="async"
              />
            </picture>
          </div>
        );
      })}

      {/* Cinematic Dark Navy & Obsidian Color Grading Overlays */}
      <div
        className="absolute inset-0 bg-gradient-to-t from-[#04060B] via-[#04060B]/60 to-[#04060B]/40 pointer-events-none"
        style={{ opacity: overlayOpacity }}
      />
      <div className="absolute inset-0 bg-[radial-gradient(circle_at_center,transparent_0%,#04060B_82%)] pointer-events-none" />

      {/* Interactive Slideshow Control Badge & Progress Bar (Bottom Left) */}
      <div className="absolute bottom-4 left-4 sm:bottom-6 sm:left-6 z-20 pointer-events-auto flex flex-col gap-1.5 p-2 px-3 sm:px-4 rounded-xl bg-black/85 border border-white/10 hover:border-amber-400/40 text-[10px] font-mono text-neutral-300 backdrop-blur-md shadow-[0_4px_30px_rgba(0,0,0,0.85)] transition-all group">
        <div className="flex items-center space-x-2.5">
          <div className="flex items-center space-x-1.5">
            <Images className="w-3.5 h-3.5 text-amber-400 shrink-0" />
            <span className="font-bold text-white uppercase tracking-wider">
              {currentSlide.legend}
            </span>
          </div>

          <span className="text-neutral-500">·</span>

          <span className="text-neutral-400 font-normal">
            {currentIndex + 1} / {LEGEND_SLIDES.length}
          </span>

          <span className="text-neutral-500">·</span>

          {/* Previous Slide Button */}
          <button
            type="button"
            onClick={(e) => {
              e.stopPropagation();
              prevSlide();
            }}
            className="p-1 hover:text-amber-300 transition-colors cursor-pointer rounded"
            title="Previous slide"
            aria-label="Previous slide"
          >
            <ChevronLeft className="w-3.5 h-3.5 text-neutral-300 hover:text-amber-300" />
          </button>

          {/* Play / Pause Toggle Button */}
          <button
            type="button"
            onClick={(e) => {
              e.stopPropagation();
              setIsPlaying((p) => !p);
            }}
            className="p-1 hover:text-amber-300 transition-colors cursor-pointer rounded"
            title={isPlaying ? 'Pause slideshow' : 'Play slideshow'}
            aria-label={isPlaying ? 'Pause slideshow' : 'Play slideshow'}
          >
            {isPlaying ? (
              <Pause className="w-3 h-3 text-amber-400" />
            ) : (
              <Play className="w-3 h-3 text-emerald-400" />
            )}
          </button>

          {/* Next Slide Button */}
          <button
            type="button"
            onClick={(e) => {
              e.stopPropagation();
              nextSlide();
            }}
            className="p-1 hover:text-amber-300 transition-colors cursor-pointer rounded"
            title="Next slide"
            aria-label="Next slide"
          >
            <ChevronRight className="w-3.5 h-3.5 text-neutral-300 hover:text-amber-300" />
          </button>
        </div>

        {/* Progress Bar indicating time left on current slide */}
        <div className="w-full h-1 bg-white/10 rounded-full overflow-hidden">
          <div
            className="h-full bg-gradient-to-r from-amber-500 to-amber-300 transition-all duration-75 ease-linear rounded-full"
            style={{ width: `${progress}%` }}
          />
        </div>
      </div>
    </div>
  );
};

// Aliases for full backward compatibility
export const CinematicVideoBackground = CinematicSlideshowBackground;

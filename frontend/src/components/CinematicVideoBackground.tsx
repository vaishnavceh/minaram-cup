import React, { useState, useEffect, useRef } from 'react';
import { Film, Shuffle } from 'lucide-react';

export interface TributeVideo {
  id: string;
  src: string;
  title: string;
  legend: string;
  badge: string;
  poster: string;
}

export const TRIBUTE_VIDEOS: TributeVideo[] = [
  {
    id: 'messi',
    src: '/assets/videos/messi-tribute.mp4',
    title: 'Lionel Messi — Way Down We Go',
    legend: 'Lionel Messi',
    badge: 'ALBICELESTE · #10',
    poster: '/assets/backgrounds/legends/efootball-messi-hero.webp',
  },
  {
    id: 'ronaldo',
    src: '/assets/videos/ronaldo-tribute.mp4',
    title: 'Cristiano Ronaldo — Portugal Masterclass',
    legend: 'Cristiano Ronaldo',
    badge: 'QUINAS · #7',
    poster: '/assets/backgrounds/legends/ronaldo-victory-fist.webp',
  },
  {
    id: 'neymar',
    src: '/assets/videos/neymar-tribute.mp4',
    title: 'Neymar Jr — The Soul of Samba',
    legend: 'Neymar Jr',
    badge: 'SELEÇÃO · #11',
    poster: '/assets/backgrounds/legends/neymar-debut-celebration.webp',
  },
];

// Alias for backwards compatibility
export const YOUTUBE_TRIBUTE_VIDEOS = TRIBUTE_VIDEOS;

function getRandomTributeIndex(): number {
  try {
    const lastIdxStr = sessionStorage.getItem('minaram_last_tribute_idx');
    const lastIdx = lastIdxStr !== null ? parseInt(lastIdxStr, 10) : -1;
    // Exclude the previous video to guarantee fresh randomized variety on refresh
    const candidates = [0, 1, 2].filter((i) => i !== lastIdx);
    const chosen = candidates[Math.floor(Math.random() * candidates.length)];
    sessionStorage.setItem('minaram_last_tribute_idx', String(chosen));
    return chosen;
  } catch {
    return Math.floor(Math.random() * TRIBUTE_VIDEOS.length);
  }
}

interface CinematicVideoBackgroundProps {
  fallbackImage?: string;
  overlayOpacity?: number;
}

export const CinematicVideoBackground: React.FC<CinematicVideoBackgroundProps> = ({
  fallbackImage = '/assets/backgrounds/legends/efootball-messi-hero.webp',
  overlayOpacity = 0.72,
}) => {
  const [videoIndex, setVideoIndex] = useState<number>(getRandomTributeIndex);
  const [isReady, setIsReady] = useState<boolean>(false);
  const videoRef = useRef<HTMLVideoElement>(null);

  const currentVideo = TRIBUTE_VIDEOS[videoIndex];

  // Attempt instant autoplay when video index changes
  useEffect(() => {
    setIsReady(false);
    const video = videoRef.current;
    if (video) {
      video.currentTime = 0;
      const playPromise = video.play();
      if (playPromise !== undefined) {
        playPromise
          .then(() => {
            setIsReady(true);
          })
          .catch((err) => {
            // Autoplay policy or abort; muted video will still play once user engages
            console.debug('Autoplay video notice:', err);
          });
      }
    }
  }, [videoIndex]);

  // Handle switching to next tribute video
  const handleNextVideo = (e?: React.MouseEvent) => {
    if (e) e.stopPropagation();
    setIsReady(false);
    setVideoIndex((prev) => {
      const next = (prev + 1) % TRIBUTE_VIDEOS.length;
      try {
        sessionStorage.setItem('minaram_last_tribute_idx', String(next));
      } catch {}
      return next;
    });
  };

  return (
    <div className="absolute inset-0 z-0 overflow-hidden pointer-events-none select-none">
      {/* High-Fidelity Static Poster Artwork (Visible immediately with zero lag or black flashes) */}
      <img
        src={currentVideo.poster || fallbackImage}
        alt={currentVideo.title}
        className="absolute inset-0 w-full h-full object-cover object-center filter brightness-60 contrast-115 scale-105 pointer-events-none"
        fetchPriority="high"
        decoding="sync"
      />

      {/* Native HTML5 Background Video — 100% Free of YouTube Controls, Watermarks, or Pause Buttons */}
      <video
        ref={videoRef}
        key={currentVideo.src}
        src={currentVideo.src}
        poster={currentVideo.poster}
        autoPlay
        loop
        muted
        playsInline
        preload="auto"
        disablePictureInPicture
        disableRemotePlayback
        onPlaying={() => setIsReady(true)}
        onLoadedData={() => {
          if (videoRef.current) {
            videoRef.current.play().catch(() => {});
          }
        }}
        className={`absolute inset-0 w-full h-full object-cover object-center pointer-events-none transition-opacity duration-700 ease-out ${
          isReady ? 'opacity-85' : 'opacity-0'
        }`}
      />

      {/* Cinematic Dark Navy & Obsidian Color Grading Overlays */}
      <div
        className="absolute inset-0 bg-gradient-to-t from-[#04060B] via-[#04060B]/65 to-[#04060B]/45 pointer-events-none"
        style={{ opacity: overlayOpacity }}
      />
      <div className="absolute inset-0 bg-[radial-gradient(circle_at_center,transparent_0%,#04060B_82%)] pointer-events-none" />

      {/* Interactive Tribute Video Switcher & Status Pill */}
      <div className="absolute bottom-4 left-4 sm:bottom-6 sm:left-6 z-20 pointer-events-auto flex items-center space-x-2 px-3.5 py-1.5 rounded-full bg-black/85 border border-white/10 hover:border-amber-400/50 text-[10px] font-mono text-neutral-300 backdrop-blur-md shadow-[0_4px_25px_rgba(0,0,0,0.8)] transition-all group">
        <Film className="w-3.5 h-3.5 text-amber-400 shrink-0" />
        <span className="font-bold text-white uppercase tracking-wider">
          {currentVideo.legend}
        </span>
        <span className="text-neutral-500">·</span>
        <span className="text-neutral-400 font-normal">
          Tribute {videoIndex + 1}/3
        </span>

        {/* Switch Next Video Button */}
        <button
          type="button"
          onClick={handleNextVideo}
          className="p-1 hover:text-amber-300 transition-colors cursor-pointer rounded flex items-center space-x-1"
          title="Switch to next tribute video"
          aria-label="Switch to next tribute video"
        >
          <Shuffle className="w-3 h-3 text-amber-400 group-hover:rotate-180 transition-transform duration-300" />
          <span className="text-[9px] text-neutral-400 group-hover:text-amber-300 uppercase">NEXT</span>
        </button>
      </div>
    </div>
  );
};

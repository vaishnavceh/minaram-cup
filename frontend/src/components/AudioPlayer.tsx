import React, { useState, useEffect, useRef } from 'react';
import {
  Volume2,
  Volume1,
  VolumeX,
  Play,
  Pause,
  Square,
  Music,
  ChevronDown,
  ChevronUp,
  Info,
  Sparkles,
  Disc3
} from 'lucide-react';

export const AudioPlayer: React.FC = () => {
  const audioRef = useRef<HTMLAudioElement | null>(null);

  const [isPlaying, setIsPlaying] = useState<boolean>(false);
  const [volume, setVolume] = useState<number>(0.5); // Default 50% volume
  const [isMuted, setIsMuted] = useState<boolean>(false);
  const [currentTime, setCurrentTime] = useState<number>(0);
  const [duration, setDuration] = useState<number>(0);
  const [isMinimized, setIsMinimized] = useState<boolean>(true); // Start in minimized pill state like uploaded screenshot
  const [showCredits, setShowCredits] = useState<boolean>(false); // Expandable only
  const [autoplayBlocked, setAutoplayBlocked] = useState<boolean>(false);

  // Sync volume with HTML audio element
  useEffect(() => {
    if (audioRef.current) {
      audioRef.current.volume = isMuted ? 0 : volume;
    }
  }, [volume, isMuted]);

  // Autoplay on mount at 50% volume with robust browser policy unlock
  useEffect(() => {
    let unmounted = false;

    const startPlayback = async () => {
      const el = audioRef.current;
      if (!el) return;

      el.volume = 0.5;
      setVolume(0.5);

      // Attempt 1: Direct unmuted playback at 50% volume
      try {
        await el.play();
        if (!unmounted) {
          setIsPlaying(true);
          setIsMuted(false);
          setAutoplayBlocked(false);
        }
        return;
      } catch (err) {
        // Direct unmuted playback blocked by browser Media Engagement policy
      }

      // Attempt 2: Start playing muted immediately so timeline advances & buffers
      try {
        el.muted = true;
        await el.play();
        if (!unmounted) {
          setIsPlaying(true);
          setAutoplayBlocked(true);
        }
      } catch {
        if (!unmounted) {
          setAutoplayBlocked(true);
        }
      }

      // Global capture-phase unlocker on first user gesture anywhere
      const unlockSound = () => {
        if (el) {
          el.muted = false;
          el.volume = 0.5;
          el.play()
            .then(() => {
              if (!unmounted) {
                setIsPlaying(true);
                setIsMuted(false);
                setAutoplayBlocked(false);
              }
            })
            .catch(() => {});
        }

        const events = ['pointerdown', 'mousedown', 'touchstart', 'click', 'keydown'];
        events.forEach((ev) => {
          document.removeEventListener(ev, unlockSound, true);
          window.removeEventListener(ev, unlockSound, true);
        });
      };

      const events = ['pointerdown', 'mousedown', 'touchstart', 'click', 'keydown'];
      events.forEach((ev) => {
        document.addEventListener(ev, unlockSound, { capture: true, once: true });
        window.addEventListener(ev, unlockSound, { capture: true, once: true });
      });
    };

    startPlayback();

    return () => {
      unmounted = true;
    };
  }, []);

  const togglePlay = () => {
    if (!audioRef.current) return;
    if (isPlaying) {
      audioRef.current.pause();
      setIsPlaying(false);
    } else {
      audioRef.current
        .play()
        .then(() => {
          setIsPlaying(true);
          setAutoplayBlocked(false);
        })
        .catch(() => {
          setAutoplayBlocked(true);
        });
    }
  };

  const handleStop = () => {
    if (!audioRef.current) return;
    audioRef.current.pause();
    audioRef.current.currentTime = 0;
    setCurrentTime(0);
    setIsPlaying(false);
  };

  const toggleMute = () => {
    setIsMuted((prev) => !prev);
  };

  const handleVolumeChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const newVol = parseFloat(e.target.value);
    setVolume(newVol);
    if (newVol > 0 && isMuted) {
      setIsMuted(false);
    }
  };

  const handleTimeUpdate = () => {
    if (audioRef.current) {
      setCurrentTime(audioRef.current.currentTime);
    }
  };

  const handleLoadedMetadata = () => {
    if (audioRef.current) {
      setDuration(audioRef.current.duration);
    }
  };

  const handleSeek = (e: React.ChangeEvent<HTMLInputElement>) => {
    const time = parseFloat(e.target.value);
    setCurrentTime(time);
    if (audioRef.current) {
      audioRef.current.currentTime = time;
    }
  };

  const formatTime = (seconds: number): string => {
    if (isNaN(seconds) || seconds <= 0) return '0:00';
    const mins = Math.floor(seconds / 60);
    const secs = Math.floor(seconds % 60);
    return `${mins}:${secs < 10 ? '0' : ''}${secs}`;
  };

  const currentPercent = isMuted ? 0 : Math.round(volume * 100);

  return (
    <>
      {/* Hidden HTML5 Audio Element */}
      <audio
        ref={audioRef}
        src="/assets/audio/viva_la_vida.mp3"
        autoPlay
        playsInline
        preload="auto"
        loop
        onPlay={() => setIsPlaying(true)}
        onPause={() => setIsPlaying(false)}
        onTimeUpdate={handleTimeUpdate}
        onLoadedMetadata={handleLoadedMetadata}
        onEnded={() => setIsPlaying(false)}
      />

      {/* Floating Audio Player Widget */}
      <div
        className="fixed bottom-4 right-4 sm:bottom-6 sm:right-6 z-40 transition-all duration-300 font-sans select-none"
        role="region"
        aria-label="Tournament Theme Audio Player"
      >
        {isMinimized ? (
          /* Minimized Disc Pill — Starts like this on page load */
          <button
            type="button"
            onClick={() => {
              if (audioRef.current) {
                audioRef.current.muted = false;
                audioRef.current.volume = 0.5;
                audioRef.current
                  .play()
                  .then(() => {
                    setIsPlaying(true);
                    setIsMuted(false);
                    setAutoplayBlocked(false);
                  })
                  .catch(() => {});
              }
              setIsMinimized(false);
            }}
            className="flex items-center space-x-3 px-4 py-2 rounded-full bg-black/95 border border-amber-400/60 text-white backdrop-blur-xl shadow-[0_4px_30px_rgba(212,175,55,0.3)] hover:border-amber-300 hover:scale-105 transition-all duration-200 group cursor-pointer"
            title="Click to open audio controls"
            aria-label="Expand Viva la Vida audio controls"
          >
            {/* Spinning Disc Badge */}
            <div className="relative w-8 h-8 rounded-full border border-amber-400/80 bg-amber-950/50 flex items-center justify-center text-amber-400 shadow-[0_0_12px_rgba(212,175,55,0.4)] shrink-0">
              <Disc3 className={`w-5 h-5 ${isPlaying ? 'animate-spin' : ''}`} style={{ animationDuration: '3s' }} />
            </div>

            {/* Song Title & Live Status */}
            <div className="flex flex-col text-left pr-1">
              <span className="text-xs font-display uppercase tracking-wider text-white group-hover:text-amber-300 transition-colors font-bold leading-none">
                VIVA LA VIDA
              </span>
              <span className="text-[10px] font-mono text-neutral-400 tracking-wider uppercase leading-none mt-1 flex items-center space-x-1">
                {autoplayBlocked ? (
                  <>
                    <span className="w-1.5 h-1.5 rounded-full bg-amber-400 animate-ping inline-block" />
                    <span className="text-amber-300">CLICK TO UNMUTE</span>
                  </>
                ) : isPlaying ? (
                  <span>{formatTime(currentTime)} · PLAYING</span>
                ) : (
                  <span>0:00 · CLICK TO PLAY</span>
                )}
              </span>
            </div>

            {/* Expand Indicator */}
            <ChevronUp className="w-4 h-4 text-neutral-400 group-hover:text-amber-300 transition-colors shrink-0" />
          </button>
        ) : (
          /* Expanded Player Console */
          <div className="w-[320px] sm:w-[360px] max-w-[calc(100vw-32px)] rounded-2xl bg-[#04060B]/95 border border-amber-400/30 backdrop-blur-xl shadow-[0_12px_40px_rgba(0,0,0,0.85)] p-4 text-white relative overflow-hidden transition-all duration-300">
            {/* Top Shimmer Border */}
            <div className="absolute top-0 left-0 right-0 h-[2px] bg-gradient-to-r from-transparent via-amber-400 to-transparent opacity-75" />

            {/* Header: Title, Artist, Minimize Button */}
            <div className="flex items-center justify-between pb-3 border-b border-white/10">
              <div className="flex items-center space-x-2.5 overflow-hidden">
                <div className={`w-8 h-8 rounded-lg bg-amber-950/40 border border-amber-400/40 flex items-center justify-center text-amber-400 shrink-0 ${isPlaying ? 'shadow-[0_0_12px_rgba(212,175,55,0.3)]' : ''}`}>
                  <Music className="w-4 h-4" />
                </div>
                <div className="flex flex-col truncate">
                  <div className="flex items-center space-x-1.5">
                    <span className="font-display text-sm tracking-wider text-white truncate">
                      VIVA LA VIDA
                    </span>
                    <Sparkles className="w-3 h-3 text-amber-400 shrink-0" />
                  </div>
                  <span className="text-[10px] font-mono tracking-widest text-neutral-400 uppercase truncate">
                    Coldplay · Legends Anthem
                  </span>
                </div>
              </div>

              <div className="flex items-center space-x-1">
                {/* Expandable Credits Toggle */}
                <button
                  type="button"
                  onClick={() => setShowCredits((prev) => !prev)}
                  className={`p-1.5 rounded-lg border text-xs font-mono transition-colors flex items-center space-x-1 ${
                    showCredits
                      ? 'bg-amber-400/20 border-amber-400/60 text-amber-300'
                      : 'bg-neutral-900 border-white/10 text-neutral-400 hover:text-white hover:border-white/20'
                  }`}
                  title={showCredits ? 'Hide Credits' : 'View Credits'}
                  aria-expanded={showCredits}
                >
                  <Info className="w-3.5 h-3.5" />
                  <span className="text-[10px] uppercase tracking-wider font-semibold">Credits</span>
                </button>

                {/* Minimize Player Button */}
                <button
                  type="button"
                  onClick={() => setIsMinimized(true)}
                  className="p-1.5 rounded-lg text-neutral-400 hover:text-white hover:bg-neutral-800 transition-colors"
                  title="Minimize Player"
                  aria-label="Minimize Audio Player"
                >
                  <ChevronDown className="w-4 h-4" />
                </button>
              </div>
            </div>

            {/* EXPANDABLE ONLY: Song Credits & Attribution */}
            {showCredits && (
              <div className="mt-3 p-3 rounded-xl bg-gradient-to-b from-neutral-900/90 to-black/90 border border-amber-400/25 text-[11px] font-mono space-y-2 animate-fadeIn transition-all">
                <div className="flex items-center justify-between pb-1.5 border-b border-white/10 text-amber-300 font-bold uppercase tracking-wider text-[10px]">
                  <span>OFFICIAL SONG CREDITS</span>
                  <span className="text-neutral-500 font-normal">EXPANDABLE</span>
                </div>
                <div className="space-y-1 text-neutral-300 leading-snug">
                  <div>
                    <span className="text-neutral-500 uppercase tracking-widest text-[9px] block">Title & Artist</span>
                    <strong className="text-white">Viva la Vida</strong> — Coldplay
                  </div>
                  <div>
                    <span className="text-neutral-500 uppercase tracking-widest text-[9px] block">Album</span>
                    <span>Viva la Vida or Death and All His Friends (2008)</span>
                  </div>
                  <div>
                    <span className="text-neutral-500 uppercase tracking-widest text-[9px] block">Writers</span>
                    <span>Guy Berryman, Jonny Buckland, Will Champion, Chris Martin</span>
                  </div>
                  <div>
                    <span className="text-neutral-500 uppercase tracking-widest text-[9px] block">Producers</span>
                    <span>Brian Eno, Markus Dravs, Rik Simpson</span>
                  </div>
                  <div className="pt-1 text-[10px] text-amber-200/80 italic border-t border-white/5">
                    Tribute anthem celebrating the immortal football era of Lionel Messi, Cristiano Ronaldo, and Neymar Jr. Non-commercial collegiate presentation for Minaram Cup 2026.
                  </div>
                </div>
              </div>
            )}

            {/* Scrub Progress Bar & Timers */}
            <div className="mt-3 space-y-1">
              <input
                type="range"
                min="0"
                max={duration || 100}
                step="0.25"
                value={currentTime}
                onChange={handleSeek}
                className="w-full h-1 bg-neutral-800 rounded-lg appearance-none cursor-pointer accent-amber-400"
                aria-label="Track Progress Slider"
              />
              <div className="flex items-center justify-between text-[10px] font-mono text-neutral-400 px-0.5">
                <span>{formatTime(currentTime)}</span>
                <span>{formatTime(duration)}</span>
              </div>
            </div>

            {/* Main Controls: Play, Stop, Volume Slider */}
            <div className="mt-3 flex items-center justify-between gap-3">
              {/* Play / Pause / Stop Buttons */}
              <div className="flex items-center space-x-2 shrink-0">
                <button
                  type="button"
                  onClick={togglePlay}
                  className="px-3.5 py-1.5 rounded-xl bg-gradient-to-r from-amber-500 to-amber-600 hover:from-amber-400 hover:to-amber-500 text-black font-display text-xs tracking-wider uppercase transition-all shadow-[0_0_15px_rgba(212,175,55,0.35)] flex items-center space-x-1.5 cursor-pointer font-bold"
                  title={isPlaying ? 'Pause Anthem' : 'Play Anthem'}
                >
                  {isPlaying ? (
                    <>
                      <Pause className="w-3.5 h-3.5 fill-current" />
                      <span>PAUSE</span>
                    </>
                  ) : (
                    <>
                      <Play className="w-3.5 h-3.5 fill-current ml-0.5" />
                      <span>PLAY</span>
                    </>
                  )}
                </button>

                <button
                  type="button"
                  onClick={handleStop}
                  className="p-1.5 rounded-xl bg-neutral-900 border border-white/10 hover:border-rose-500/50 hover:bg-rose-950/30 text-neutral-400 hover:text-rose-400 transition-colors cursor-pointer"
                  title="Stop and Reset to Start"
                  aria-label="Stop Anthem"
                >
                  <Square className="w-3.5 h-3.5 fill-current" />
                </button>
              </div>

              {/* Volume Strip */}
              <div className="flex items-center space-x-2 flex-grow justify-end">
                <button
                  type="button"
                  onClick={toggleMute}
                  className="p-1.5 rounded-lg hover:bg-neutral-800 text-neutral-300 hover:text-amber-400 transition-colors shrink-0"
                  title={isMuted ? 'Unmute' : 'Mute'}
                  aria-label={isMuted ? 'Unmute' : 'Mute'}
                >
                  {isMuted || volume === 0 ? (
                    <VolumeX className="w-4 h-4 text-rose-400" />
                  ) : volume < 0.5 ? (
                    <Volume1 className="w-4 h-4 text-amber-400" />
                  ) : (
                    <Volume2 className="w-4 h-4 text-amber-400" />
                  )}
                </button>

                <input
                  type="range"
                  min="0"
                  max="1"
                  step="0.02"
                  value={isMuted ? 0 : volume}
                  onChange={handleVolumeChange}
                  className="w-16 sm:w-20 h-1 bg-neutral-800 rounded-lg appearance-none cursor-pointer accent-amber-400"
                  aria-label="Volume Slider"
                />

                <span className="text-[11px] font-mono font-bold text-white min-w-[32px] text-right tabular-nums">
                  {currentPercent}%
                </span>
              </div>
            </div>

            {/* Autoplay blocked notice */}
            {autoplayBlocked && (
              <div className="mt-2.5 p-1.5 rounded bg-amber-950/60 border border-amber-500/40 text-[10px] font-mono text-amber-300 text-center flex items-center justify-center space-x-1">
                <span>Click PLAY to start official anthem</span>
              </div>
            )}
          </div>
        )}
      </div>
    </>
  );
};

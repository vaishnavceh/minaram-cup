import React, { useState, useEffect, useRef } from 'react';
import {
  Volume2,
  Volume1,
  VolumeX,
  Play,
  Pause,
  Moon,
  Sun,
  ChevronDown,
  ChevronUp,
  Music,
  Minus,
  Plus
} from 'lucide-react';

export const AudioPlayer: React.FC = () => {
  const audioRef = useRef<HTMLAudioElement | null>(null);

  // Time-based default volume calculation
  // Morning / daytime: 50% (0.50). Night: same percent (50%) but stabilized for night (not too loud)
  const getInitialNightStatus = () => {
    const hour = new Date().getHours();
    return hour >= 20 || hour < 6; // Night between 8 PM and 6 AM
  };

  const [isNightTime, setIsNightTime] = useState<boolean>(getInitialNightStatus());
  const [nightStabilizer, setNightStabilizer] = useState<boolean>(getInitialNightStatus());
  const [isPlaying, setIsPlaying] = useState<boolean>(false);
  const [volume, setVolume] = useState<number>(0.5); // Default 50%
  const [isMuted, setIsMuted] = useState<boolean>(false);
  const [currentTime, setCurrentTime] = useState<number>(0);
  const [duration, setDuration] = useState<number>(0);
  const [isMinimized, setIsMinimized] = useState<boolean>(false);
  const [autoplayBlocked, setAutoplayBlocked] = useState<boolean>(false);

  // Night-stabilized effective volume calculation:
  // When night stabilizer is active, softly compress/attenuate upper range so peak orchestral brass doesn't blast
  const effectiveVolume = isMuted ? 0 : nightStabilizer ? volume * 0.72 : volume;

  useEffect(() => {
    if (audioRef.current) {
      audioRef.current.volume = Math.max(0, Math.min(1, effectiveVolume));
    }
  }, [effectiveVolume]);

  // Update night time every 10 minutes in background
  useEffect(() => {
    const timer = setInterval(() => {
      const night = getInitialNightStatus();
      setIsNightTime(night);
    }, 600000);
    return () => clearInterval(timer);
  }, []);

  // Sync playback state with audio element
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
    const seekTime = parseFloat(e.target.value);
    if (audioRef.current) {
      audioRef.current.currentTime = seekTime;
      setCurrentTime(seekTime);
    }
  };

  const handleVolumeChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const newVol = parseFloat(e.target.value);
    setVolume(newVol);
    if (newVol > 0 && isMuted) {
      setIsMuted(false);
    }
  };

  const adjustVolumeBy = (delta: number) => {
    setVolume((prev) => {
      const updated = Math.max(0, Math.min(1, Math.round((prev + delta) * 100) / 100));
      if (updated > 0 && isMuted) setIsMuted(false);
      return updated;
    });
  };

  const toggleMute = () => {
    setIsMuted(!isMuted);
  };

  const formatTime = (secs: number) => {
    if (isNaN(secs)) return '0:00';
    const m = Math.floor(secs / 60);
    const s = Math.floor(secs % 60);
    return `${m}:${s < 10 ? '0' : ''}${s}`;
  };

  const currentPercent = Math.round(volume * 100);

  return (
    <>
      {/* Hidden audio element loading local UEFA Champions League Anthem */}
      <audio
        ref={audioRef}
        src="/assets/audio/uefa_champions_league_anthem.mp3"
        onTimeUpdate={handleTimeUpdate}
        onLoadedMetadata={handleLoadedMetadata}
        onEnded={() => setIsPlaying(false)}
        loop
        preload="metadata"
      />

      {/* Floating Bottom Audio Player */}
      <div className="fixed bottom-4 right-4 z-50 transition-all duration-300">
        {isMinimized ? (
          /* Minimized Compact Pill */
          <div className="flex items-center space-x-3 px-3.5 py-2 rounded-full bg-black/90 border border-brand-gold/50 shadow-[0_4px_25px_rgba(212,175,55,0.25)] backdrop-blur-md">
            <button
              onClick={togglePlay}
              className="w-8 h-8 rounded-full bg-gradient-to-r from-brand-gold to-amber-600 hover:from-amber-400 hover:to-amber-500 text-black flex items-center justify-center transition-transform hover:scale-105 cursor-pointer shadow-md"
              title={isPlaying ? 'Pause UCL Anthem' : 'Play UCL Anthem'}
            >
              {isPlaying ? <Pause className="w-4 h-4 fill-current" /> : <Play className="w-4 h-4 fill-current ml-0.5" />}
            </button>

            <div className="flex items-center space-x-2 cursor-pointer" onClick={() => setIsMinimized(false)}>
              <span className="font-display text-xs tracking-wider text-white">UCL ANTHEM</span>
              {/* Equalizer animation bars if playing */}
              {isPlaying && (
                <div className="flex items-end space-x-0.5 h-3">
                  <span className="w-0.5 bg-brand-gold animate-[bounce_0.6s_ease-in-out_infinite] h-full" />
                  <span className="w-0.5 bg-brand-gold animate-[bounce_0.9s_ease-in-out_infinite] h-2" />
                  <span className="w-0.5 bg-brand-gold animate-[bounce_0.4s_ease-in-out_infinite] h-full" />
                </div>
              )}
              <span className="text-[10px] font-mono text-brand-gold font-bold">
                {currentPercent}%
              </span>
            </div>

            <button
              onClick={() => setIsMinimized(false)}
              className="p-1 rounded text-neutral-400 hover:text-white"
              title="Expand Anthem Player"
            >
              <ChevronUp className="w-4 h-4" />
            </button>
          </div>
        ) : (
          /* Expanded Full Player */
          <div className="w-[320px] sm:w-[380px] rounded-2xl bg-gradient-to-b from-[#0c101c] via-[#080b14] to-[#04060c] border-2 border-brand-gold/60 p-4 shadow-[0_8px_35px_rgba(0,0,0,0.8),0_0_30px_rgba(212,175,55,0.18)] backdrop-blur-xl animate-fade-in">
            {/* Header / Track Info */}
            <div className="flex items-start justify-between mb-3 pb-2.5 border-b border-[#1c2438]">
              <div className="flex items-center space-x-2.5">
                <div className="w-9 h-9 rounded-xl bg-gradient-to-br from-brand-gold to-amber-700 flex items-center justify-center text-black shadow-md shrink-0">
                  <Music className="w-5 h-5" />
                </div>
                <div className="overflow-hidden">
                  <div className="flex items-center space-x-2">
                    <span className="text-[9px] font-mono font-bold tracking-widest uppercase px-1.5 py-0.5 rounded bg-brand-gold/20 text-brand-gold border border-brand-gold/40">
                      OFFICIAL ANTHEM
                    </span>
                  </div>
                  <h4 className="font-display text-sm text-white tracking-wide truncate mt-0.5">
                    UEFA CHAMPIONS LEAGUE
                  </h4>
                  <p className="text-[10px] font-mono text-neutral-400 truncate">
                    Full Orchestral & Choir Version
                  </p>
                </div>
              </div>

              <div className="flex items-center space-x-1 shrink-0">
                <button
                  onClick={() => setIsMinimized(true)}
                  className="p-1.5 rounded-lg hover:bg-neutral-800 text-neutral-400 hover:text-white transition-colors"
                  title="Minimize Player"
                >
                  <ChevronDown className="w-4 h-4" />
                </button>
              </div>
            </div>

            {/* Time-Based Night Stabilization Strip */}
            <div className="mb-3 px-2.5 py-1.5 rounded-lg bg-[#0f1626] border border-[#1e2c47] flex items-center justify-between text-[11px] font-mono">
              <div className="flex items-center space-x-2">
                {nightStabilizer ? (
                  <Moon className="w-3.5 h-3.5 text-indigo-400 shrink-0" />
                ) : (
                  <Sun className="w-3.5 h-3.5 text-amber-400 shrink-0" />
                )}
                <span className="text-neutral-300">
                  {nightStabilizer
                    ? 'Night Limiter (Not Too Loud)'
                    : 'Daytime Standard Dynamics'}
                </span>
              </div>
              <button
                type="button"
                onClick={() => setNightStabilizer(!nightStabilizer)}
                className={`text-[9px] uppercase px-1.5 py-0.5 rounded font-bold transition-colors ${
                  nightStabilizer
                    ? 'bg-indigo-950 text-indigo-300 border border-indigo-700'
                    : 'bg-amber-950 text-amber-300 border border-amber-700'
                }`}
                title="Toggle night-time acoustic limiter"
              >
                {nightStabilizer ? 'ON' : 'OFF'}
              </button>
            </div>

            {/* Scrub Progress Bar */}
            <div className="mb-3 space-y-1">
              <input
                type="range"
                min="0"
                max={duration || 100}
                step="0.5"
                value={currentTime}
                onChange={handleSeek}
                className="w-full h-1.5 bg-neutral-800 rounded-lg appearance-none cursor-pointer accent-brand-gold"
              />
              <div className="flex items-center justify-between text-[10px] font-mono text-neutral-400 px-0.5">
                <span>{formatTime(currentTime)}</span>
                <span>{formatTime(duration)}</span>
              </div>
            </div>

            {/* Main Controls & Volume Strip */}
            <div className="flex items-center justify-between gap-3 pt-1">
              {/* Play / Pause Primary Button */}
              <button
                onClick={togglePlay}
                className="px-4 py-2 rounded-xl bg-gradient-to-r from-brand-gold to-amber-600 hover:from-amber-400 hover:to-amber-500 text-black font-display text-sm tracking-wider uppercase transition-all shadow-[0_0_15px_rgba(212,175,55,0.4)] flex items-center space-x-2 shrink-0 cursor-pointer"
              >
                {isPlaying ? (
                  <>
                    <Pause className="w-4 h-4 fill-current" />
                    <span>PAUSE</span>
                  </>
                ) : (
                  <>
                    <Play className="w-4 h-4 fill-current ml-0.5" />
                    <span>PLAY</span>
                  </>
                )}
              </button>

              {/* Volume Slider & Increments */}
              <div className="flex items-center space-x-2 flex-grow justify-end">
                <button
                  onClick={toggleMute}
                  className="p-1.5 rounded-lg hover:bg-neutral-800 text-neutral-300 hover:text-brand-gold transition-colors shrink-0"
                  title={isMuted ? 'Unmute' : 'Mute'}
                >
                  {isMuted || volume === 0 ? (
                    <VolumeX className="w-4 h-4 text-rose-400" />
                  ) : volume < 0.5 ? (
                    <Volume1 className="w-4 h-4 text-amber-400" />
                  ) : (
                    <Volume2 className="w-4 h-4 text-brand-gold" />
                  )}
                </button>

                {/* Decrease Button */}
                <button
                  onClick={() => adjustVolumeBy(-0.1)}
                  className="w-6 h-6 rounded bg-neutral-900 border border-neutral-700 hover:border-brand-gold text-neutral-300 hover:text-white flex items-center justify-center text-xs transition-colors shrink-0"
                  title="Reduce Volume -10%"
                >
                  <Minus className="w-3 h-3" />
                </button>

                {/* Range Slider */}
                <input
                  type="range"
                  min="0"
                  max="1"
                  step="0.05"
                  value={isMuted ? 0 : volume}
                  onChange={handleVolumeChange}
                  className="w-20 sm:w-24 h-1.5 bg-neutral-800 rounded-lg appearance-none cursor-pointer accent-brand-gold"
                />

                {/* Increase Button */}
                <button
                  onClick={() => adjustVolumeBy(0.1)}
                  className="w-6 h-6 rounded bg-neutral-900 border border-neutral-700 hover:border-brand-gold text-neutral-300 hover:text-white flex items-center justify-center text-xs transition-colors shrink-0"
                  title="Increase Volume +10%"
                >
                  <Plus className="w-3 h-3" />
                </button>

                {/* Percent Display */}
                <span className="text-xs font-mono font-bold text-white min-w-[36px] text-right tabular-nums">
                  {isMuted ? '0%' : `${currentPercent}%`}
                </span>
              </div>
            </div>

            {/* Hint Notice */}
            {autoplayBlocked && (
              <div className="mt-2.5 p-1.5 rounded bg-amber-950/60 border border-amber-600/50 text-[10px] font-mono text-amber-300 text-center">
                Click PLAY to listen to the official anthem
              </div>
            )}
          </div>
        )}
      </div>
    </>
  );
};

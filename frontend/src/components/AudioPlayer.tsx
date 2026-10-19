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

  // Time-based automatic night stabilization:
  // Daytime (6 AM to 8 PM): Standard dynamic playback at 50% default volume.
  // Nighttime (8 PM to 6 AM): Automatically stabilized for nighttime so peak brass & choir don't blast.
  const getTimeState = () => {
    const now = new Date();
    const hour = now.getHours();
    const minute = now.getMinutes();
    const isNight = hour >= 20 || hour < 6;
    const ampm = hour >= 12 ? 'PM' : 'AM';
    const displayHour = hour % 12 === 0 ? 12 : hour % 12;
    const formattedMinute = minute < 10 ? `0${minute}` : minute;
    const timeString = `${displayHour}:${formattedMinute} ${ampm}`;
    return {
      isNight,
      timeString
    };
  };

  const [timeState, setTimeState] = useState(getTimeState());
  const [userOverride, setUserOverride] = useState<boolean | null>(null); // null = auto detect
  const [isPlaying, setIsPlaying] = useState<boolean>(false);
  const [volume, setVolume] = useState<number>(0.5); // Default 50% base volume
  const [isMuted, setIsMuted] = useState<boolean>(false);
  const [currentTime, setCurrentTime] = useState<number>(0);
  const [duration, setDuration] = useState<number>(0);
  const [isMinimized, setIsMinimized] = useState<boolean>(false);
  const [autoplayBlocked, setAutoplayBlocked] = useState<boolean>(false);

  // Active night stabilizer status (user override takes precedence if set, otherwise auto follows time)
  const isNightStabilizerActive = userOverride !== null ? userOverride : timeState.isNight;

  // Night-stabilized effective volume calculation:
  // At night: volume is attenuated and stabilized (0.70x, yielding ~0.35 max when slider is 50%)
  // so the anthem is soft and respectful at night, not loud.
  const effectiveVolume = isMuted ? 0 : isNightStabilizerActive ? volume * 0.70 : volume;

  useEffect(() => {
    if (audioRef.current) {
      audioRef.current.volume = Math.max(0, Math.min(1, effectiveVolume));
    }
  }, [effectiveVolume]);

  // Periodically check local time every 15 seconds to automatically react when time changes
  useEffect(() => {
    const check = () => {
      setTimeState(getTimeState());
    };
    const timer = setInterval(check, 15000);
    return () => clearInterval(timer);
  }, []);

  // Automatically play anthem on start:
  // First attempt immediate playback. If browser autoplay policy blocks unprompted audio,
  // register a one-time global user gesture listener (click, keydown, touch) so it starts instantly on first interaction.
  useEffect(() => {
    let unmounted = false;

    const startPlayback = async () => {
      if (!audioRef.current) return;
      try {
        await audioRef.current.play();
        if (!unmounted) {
          setIsPlaying(true);
          setAutoplayBlocked(false);
        }
      } catch {
        if (!unmounted) {
          setAutoplayBlocked(true);
        }
        const onFirstInteraction = () => {
          if (audioRef.current && audioRef.current.paused) {
            audioRef.current
              .play()
              .then(() => {
                if (!unmounted) {
                  setIsPlaying(true);
                  setAutoplayBlocked(false);
                }
              })
              .catch(() => {});
          }
          window.removeEventListener('click', onFirstInteraction);
          window.removeEventListener('keydown', onFirstInteraction);
          window.removeEventListener('touchstart', onFirstInteraction);
        };

        window.addEventListener('click', onFirstInteraction, { once: true });
        window.addEventListener('keydown', onFirstInteraction, { once: true });
        window.addEventListener('touchstart', onFirstInteraction, { once: true });
      }
    };

    startPlayback();

    return () => {
      unmounted = true;
    };
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
        autoPlay
        preload="auto"
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
              <span className="text-[10px] font-mono text-brand-gold font-bold flex items-center space-x-1">
                <span>{currentPercent}%</span>
                {isNightStabilizerActive ? (
                  <span title="Night Acoustic Limiter Active">
                    <Moon className="w-2.5 h-2.5 text-indigo-400" />
                  </span>
                ) : (
                  <span title="Daytime Standard Dynamics Active">
                    <Sun className="w-2.5 h-2.5 text-amber-400" />
                  </span>
                )}
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
                {isNightStabilizerActive ? (
                  <Moon className="w-3.5 h-3.5 text-indigo-400 shrink-0 animate-pulse" />
                ) : (
                  <Sun className="w-3.5 h-3.5 text-amber-400 shrink-0" />
                )}
                <div>
                  <div className="flex items-center space-x-1.5">
                    <span className="text-white font-bold">{timeState.timeString}</span>
                    <span className="text-[8px] uppercase px-1 rounded bg-black/60 text-neutral-400 border border-neutral-700">
                      {userOverride === null ? 'AUTO DETECTED' : 'MANUAL'}
                    </span>
                  </div>
                  <span className="text-[10px] text-neutral-300">
                    {isNightStabilizerActive
                      ? 'Night Mode: Stabilized for Night (Not Too Loud)'
                      : 'Daytime Mode: Standard 50% Dynamics'}
                  </span>
                </div>
              </div>
              <div className="flex items-center space-x-1 shrink-0">
                <button
                  type="button"
                  onClick={() => setUserOverride(!isNightStabilizerActive)}
                  className={`text-[9px] uppercase px-1.5 py-0.5 rounded font-bold transition-colors cursor-pointer ${
                    isNightStabilizerActive
                      ? 'bg-indigo-950 text-indigo-300 border border-indigo-700'
                      : 'bg-amber-950 text-amber-300 border border-amber-700'
                  }`}
                  title="Toggle night-time acoustic limiter"
                >
                  {isNightStabilizerActive ? 'NIGHT ON' : 'DAY ON'}
                </button>
                {userOverride !== null && (
                  <button
                    type="button"
                    onClick={() => setUserOverride(null)}
                    className="text-[8px] uppercase px-1 py-0.5 rounded bg-neutral-900 hover:bg-neutral-800 text-neutral-400 hover:text-white border border-neutral-700 cursor-pointer"
                    title="Reset to auto time detection"
                  >
                    AUTO
                  </button>
                )}
              </div>
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

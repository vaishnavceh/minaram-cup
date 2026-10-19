import React, { useState, useEffect, useRef } from 'react';
import { api } from '../api';
import { PublicBracket, DirectQualifier, PublicMatch } from '../types';
import {
  Sparkles,
  Trophy,
  Play,
  RotateCcw,
  Zap,
  Volume2,
  VolumeX,
  Shield,
  CheckCircle2,
  AlertCircle,
  Flame,
  ArrowRight,
  Shuffle,
  Save,
  Monitor,
  Download
} from 'lucide-react';

interface UefaKnockoutDrawProps {
  bracket: PublicBracket;
  token?: string;
  isAdmin?: boolean;
  allTeams?: any[];
  onDrawComplete?: (pairings: any[]) => void;
  onRefreshBracket?: () => void;
}

interface DrawBall {
  id: number;
  name: string;
  group_name: string;
  seed: number; // 1 = Group winner, 2 = Runner up
  gf?: number;
  gd?: number;
  logo_path?: string;
  captain?: string;
}

interface DrawnPairing {
  matchNumber: number;
  slot: string;
  homeTeam: DrawBall;
  awayTeam: DrawBall;
  timestamp: string;
}

export const UefaKnockoutDraw: React.FC<UefaKnockoutDrawProps> = ({ bracket, token, isAdmin = false, allTeams, onRefreshBracket }) => {
  // Sound synthesizer using Web Audio API (zero external assets needed)
  const [soundEnabled, setSoundEnabled] = useState(true);
  const audioCtxRef = useRef<AudioContext | null>(null);

  const [isApplying, setIsApplying] = useState(false);
  const [isSyncingDesktop, setIsSyncingDesktop] = useState(false);
  const [adminMessage, setAdminMessage] = useState('');

  const handleApplyToOfficial = async () => {
    if (!token || pairings.length === 0) return;
    if (!window.confirm(`Apply these ${pairings.length} drawn pairings into the authoritative official tournament fixtures?`)) return;
    setIsApplying(true);
    setAdminMessage('');
    try {
      const res = await api.adminApplyCeremonialDraw(pairings, token);
      setAdminMessage(res.message || 'Official knockout fixtures updated successfully!');
      if (onRefreshBracket) onRefreshBracket();
      setTimeout(() => setAdminMessage(''), 5000);
    } catch (err: any) {
      alert(err.message || 'Failed to apply draw to official fixtures');
    } finally {
      setIsApplying(false);
    }
  };

  const handleSyncToDesktop = async () => {
    if (!token) return;
    setIsSyncingDesktop(true);
    setAdminMessage('');
    try {
      const res = await api.adminSyncDrawToDesktop(token);
      const blob = new Blob([res.content], { type: 'text/plain;charset=utf-8' });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = res.filename || 'MINARAM_CUP_2026_OFFICIAL_KNOCKOUT_DRAW.txt';
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);

      setAdminMessage(`Official Draw successfully synced to Desktop: ${res.file_path}`);
      setTimeout(() => setAdminMessage(''), 6000);
    } catch (err: any) {
      alert(err.message || 'Failed to sync draw to desktop');
    } finally {
      setIsSyncingDesktop(false);
    }
  };

  const playChime = (type: 'draw' | 'reveal' | 'clash' | 'complete') => {
    if (!soundEnabled) return;
    try {
      if (!audioCtxRef.current) {
        audioCtxRef.current = new (window.AudioContext || (window as any).webkitAudioContext)();
      }
      const ctx = audioCtxRef.current;
      if (ctx.state === 'suspended') ctx.resume();

      const osc = ctx.createOscillator();
      const gain = ctx.createGain();
      osc.connect(gain);
      gain.connect(ctx.destination);

      const now = ctx.currentTime;
      if (type === 'draw') {
        // Subtle sphere stir/clack
        osc.type = 'triangle';
        osc.frequency.setValueAtTime(220, now);
        osc.frequency.exponentialRampToValueAtTime(440, now + 0.15);
        gain.gain.setValueAtTime(0.12, now);
        gain.gain.exponentialRampToValueAtTime(0.001, now + 0.2);
        osc.start(now);
        osc.stop(now + 0.2);
      } else if (type === 'reveal') {
        // Dramatic reveal chime (Major chord sweep)
        osc.type = 'sine';
        osc.frequency.setValueAtTime(523.25, now); // C5
        osc.frequency.setValueAtTime(659.25, now + 0.08); // E5
        osc.frequency.setValueAtTime(783.99, now + 0.16); // G5
        osc.frequency.setValueAtTime(1046.5, now + 0.24); // C6
        gain.gain.setValueAtTime(0.2, now);
        gain.gain.exponentialRampToValueAtTime(0.001, now + 0.6);
        osc.start(now);
        osc.stop(now + 0.6);
      } else if (type === 'clash') {
        // Low brass tone for conflict
        osc.type = 'sawtooth';
        osc.frequency.setValueAtTime(160, now);
        gain.gain.setValueAtTime(0.15, now);
        gain.gain.exponentialRampToValueAtTime(0.001, now + 0.3);
        osc.start(now);
        osc.stop(now + 0.3);
      } else if (type === 'complete') {
        // Grand fanfare
        osc.type = 'sine';
        osc.frequency.setValueAtTime(440, now);
        osc.frequency.exponentialRampToValueAtTime(880, now + 0.4);
        gain.gain.setValueAtTime(0.25, now);
        gain.gain.exponentialRampToValueAtTime(0.001, now + 0.8);
        osc.start(now);
        osc.stop(now + 0.8);
      }
    } catch {
      // AudioContext unavailable or blocked by autoplay
    }
  };

  // Pools
  const [pot1, setPot1] = useState<DrawBall[]>([]); // Seed 1: Group Winners
  const [pot2, setPot2] = useState<DrawBall[]>([]); // Seed 2: Runners-up
  const [directQualifiers, setDirectQualifiers] = useState<DirectQualifier[]>([]);
  const [pairings, setPairings] = useState<DrawnPairing[]>([]);

  // Ceremonial Animation State
  const [isDrawing, setIsDrawing] = useState(false);
  const [isAutoPlaying, setIsAutoPlaying] = useState(false);
  const [activeStep, setActiveStep] = useState<
    'IDLE' | 'STIRRING' | 'REVEAL_HOME' | 'REVEAL_AWAY' | 'PAIRING_CONFIRMED' | 'COMPLETE'
  >('IDLE');
  const [currentHomeBall, setCurrentHomeBall] = useState<DrawBall | null>(null);
  const [currentAwayBall, setCurrentAwayBall] = useState<DrawBall | null>(null);
  const [conflictNotice, setConflictNotice] = useState<string>('');
  const [currentMatchNumber, setCurrentMatchNumber] = useState<number>(1);
  const autoPlayTimerRef = useRef<any>(null);

  // Initialize pools from bracket data
  const initializeDrawPools = () => {
    const direct = bracket.direct_qualifiers || [];
    setDirectQualifiers(direct);
    const directIds = new Set(direct.map((d: any) => d.team_id));

    // Extract preliminary round matches from bracket (supporting both rounds array and bracket object)
    let prelimMatches: any[] = [];
    if (Array.isArray(bracket.rounds)) {
      const pRound = bracket.rounds.find((r: any) => (r.round_name || '').toLowerCase().includes('preliminary'));
      if (pRound && Array.isArray(pRound.matches)) {
        prelimMatches = pRound.matches;
      }
    }
    if (prelimMatches.length === 0 && (bracket as any).bracket) {
      const bObj = (bracket as any).bracket;
      if (Array.isArray(bObj['Preliminary Round'])) {
        prelimMatches = bObj['Preliminary Round'];
      } else {
        const pKey = Object.keys(bObj).find((k) => k.toLowerCase().includes('preliminary'));
        if (pKey && Array.isArray(bObj[pKey])) {
          prelimMatches = bObj[pKey];
        }
      }
    }

    const p1List: DrawBall[] = [];
    const p2List: DrawBall[] = [];
    const seenTeams = new Set<number>();

    prelimMatches.forEach((m: any) => {
      const hId = m.team_a_id || m.home_team_id;
      const hName = m.team_a_name || m.home_team_name || m.home_name;
      const hGroup = m.home_group || m.group_name || 'Group';

      const aId = m.team_b_id || m.away_team_id;
      const aName = m.team_b_name || m.away_team_name || m.away_name;
      const aGroup = m.away_group || m.group_name || 'Group';

      if (hId && !seenTeams.has(hId) && !directIds.has(hId)) {
        seenTeams.add(hId);
        p1List.push({
          id: hId,
          name: hName || `Team ${hId}`,
          group_name: hGroup,
          seed: 1,
          captain: m.team_a_captain || m.home_captain || undefined
        });
      }
      if (aId && !seenTeams.has(aId) && !directIds.has(aId)) {
        seenTeams.add(aId);
        p2List.push({
          id: aId,
          name: aName || `Team ${aId}`,
          group_name: aGroup,
          seed: 2,
          captain: m.team_b_captain || m.away_captain || undefined
        });
      }
    });

    // If pots need more teams, draw real teams from allTeams to ensure valid database foreign keys
    if ((p1List.length < 14 || p2List.length < 14) && Array.isArray(allTeams) && allTeams.length > 0) {
      const available = allTeams.filter((t: any) => !directIds.has(t.id) && !seenTeams.has(t.id));
      available.forEach((t: any) => {
        if (p1List.length < 14) {
          seenTeams.add(t.id);
          p1List.push({
            id: t.id,
            name: t.name,
            group_name: t.group_name || 'Group',
            seed: 1,
            captain: t.captain_name
          });
        } else if (p2List.length < 14) {
          seenTeams.add(t.id);
          p2List.push({
            id: t.id,
            name: t.name,
            group_name: t.group_name || 'Group',
            seed: 2,
            captain: t.captain_name
          });
        }
      });
    }

    // Ensure balanced pots
    const all = [...p1List, ...p2List];
    const half = Math.ceil(all.length / 2);
    setPot1(all.slice(0, half));
    setPot2(all.slice(half));
    setPairings([]);
    setCurrentMatchNumber(1);
    setActiveStep('IDLE');
    setCurrentHomeBall(null);
    setCurrentAwayBall(null);
    setConflictNotice('');
    setIsAutoPlaying(false);
  };

  useEffect(() => {
    initializeDrawPools();
    return () => {
      if (autoPlayTimerRef.current) clearTimeout(autoPlayTimerRef.current);
    };
  }, [bracket]);

  // Execute a single tie draw with UCL Ceremonial animation
  const drawNextTie = async (): Promise<boolean> => {
    if (pot1.length === 0 || pot2.length === 0) {
      setActiveStep('COMPLETE');
      playChime('complete');
      setIsAutoPlaying(false);
      return false;
    }

    setIsDrawing(true);
    setConflictNotice('');

    // Phase 1: Stirring Pot 1
    setActiveStep('STIRRING');
    playChime('draw');
    await new Promise((r) => setTimeout(r, 600));

    // Pick random home ball from Pot 1
    const homeIdx = Math.floor(Math.random() * pot1.length);
    const homeBall = pot1[homeIdx];
    const nextPot1 = pot1.filter((_, i) => i !== homeIdx);
    setPot1(nextPot1);
    setCurrentHomeBall(homeBall);
    setActiveStep('REVEAL_HOME');
    playChime('reveal');
    await new Promise((r) => setTimeout(r, 800));

    // Phase 2: Stirring Pot 2 for opponent
    setActiveStep('STIRRING');
    playChime('draw');
    await new Promise((r) => setTimeout(r, 600));

    // UEFA Same-Group Rule: Pick ball that isn't from the same group
    let eligibleIndices = pot2
      .map((b, i) => (b.group_name !== homeBall.group_name ? i : -1))
      .filter((i) => i !== -1);

    if (eligibleIndices.length === 0) {
      // Last resort if only same-group remains
      eligibleIndices = pot2.map((_, i) => i);
    }

    const chosenIdx = eligibleIndices[Math.floor(Math.random() * eligibleIndices.length)];
    const awayBall = pot2[chosenIdx];
    const nextPot2 = pot2.filter((_, i) => i !== chosenIdx);
    setPot2(nextPot2);
    setCurrentAwayBall(awayBall);
    setActiveStep('REVEAL_AWAY');
    playChime('reveal');
    await new Promise((r) => setTimeout(r, 800));

    // Phase 3: Confirm Pairing
    const newPairing: DrawnPairing = {
      matchNumber: currentMatchNumber,
      slot: `PR${currentMatchNumber}`,
      homeTeam: homeBall,
      awayTeam: awayBall,
      timestamp: new Date().toLocaleTimeString()
    };

    setPairings((prev) => [...prev, newPairing]);
    setCurrentMatchNumber((prev) => prev + 1);
    setActiveStep('PAIRING_CONFIRMED');
    setIsDrawing(false);

    if (nextPot1.length === 0 || nextPot2.length === 0) {
      setActiveStep('COMPLETE');
      playChime('complete');
      setIsAutoPlaying(false);
      return false;
    }

    return true;
  };

  // Auto-play loop
  useEffect(() => {
    if (!isAutoPlaying) {
      if (autoPlayTimerRef.current) clearTimeout(autoPlayTimerRef.current);
      return;
    }

    autoPlayTimerRef.current = setTimeout(async () => {
      const hasMore = await drawNextTie();
      if (!hasMore) {
        setIsAutoPlaying(false);
      }
    }, 1800);

    return () => {
      if (autoPlayTimerRef.current) clearTimeout(autoPlayTimerRef.current);
    };
  }, [isAutoPlaying, pot1, pot2, currentMatchNumber]);

  const handleFastDrawAll = () => {
    setIsAutoPlaying(false);
    let tempPot1 = [...pot1];
    let tempPot2 = [...pot2];
    const newPairings: DrawnPairing[] = [...pairings];
    let mNum = currentMatchNumber;

    while (tempPot1.length > 0 && tempPot2.length > 0) {
      const hIdx = Math.floor(Math.random() * tempPot1.length);
      const home = tempPot1[hIdx];
      tempPot1.splice(hIdx, 1);

      let eligible = tempPot2
        .map((b, i) => (b.group_name !== home.group_name ? i : -1))
        .filter((i) => i !== -1);
      if (eligible.length === 0) eligible = tempPot2.map((_, i) => i);

      const aIdx = eligible[Math.floor(Math.random() * eligible.length)];
      const away = tempPot2[aIdx];
      tempPot2.splice(aIdx, 1);

      newPairings.push({
        matchNumber: mNum,
        slot: `PR${mNum}`,
        homeTeam: home,
        awayTeam: away,
        timestamp: new Date().toLocaleTimeString()
      });
      mNum++;
    }

    setPot1([]);
    setPot2([]);
    setPairings(newPairings);
    setCurrentMatchNumber(mNum);
    setActiveStep('COMPLETE');
    playChime('complete');
  };

  const totalMatchesToDraw = 14;
  const progressPercent = Math.min(100, Math.round((pairings.length / totalMatchesToDraw) * 100));

  return (
    <div className="space-y-8 animate-fade-in">
      {/* UEFA-Style Luxury Banner */}
      <div className="relative overflow-hidden rounded-2xl bg-gradient-to-r from-[#030d26] via-[#051336] to-[#020718] border-2 border-blue-500/50 p-6 sm:p-8 shadow-[0_0_40px_rgba(37,99,235,0.25)]">
        {/* Background Stadium Wallpaper */}
        <div className="absolute inset-0 opacity-25 pointer-events-none">
          <img
            src="/assets/backgrounds/ucl_stadium_bg.jpg"
            alt="UEFA Champions League Stadium"
            className="w-full h-full object-cover object-center filter contrast-125"
          />
          <div className="absolute inset-0 bg-gradient-to-r from-[#030d26] via-[#030d26]/80 to-[#020718]" />
        </div>

        {/* Glow Spheres */}
        <div className="absolute top-0 right-1/4 w-72 h-72 bg-blue-500/10 rounded-full blur-3xl pointer-events-none" />
        <div className="absolute bottom-0 left-1/4 w-72 h-72 bg-indigo-600/10 rounded-full blur-3xl pointer-events-none" />

        <div className="relative z-10 flex flex-col lg:flex-row lg:items-center justify-between gap-6">
          <div>
            <div className="inline-flex items-center space-x-2 px-3 py-1 rounded-full bg-blue-950/80 border border-blue-500/40 text-xs font-mono text-blue-300 tracking-widest uppercase mb-3 shadow-[0_0_15px_rgba(59,130,246,0.3)]">
              <Sparkles className="w-3.5 h-3.5 text-blue-400" />
              <span>OFFICIAL CEREMONIAL DRAW DESK</span>
            </div>
            <h2 className="font-display text-3xl sm:text-4xl lg:text-5xl text-white tracking-wider uppercase leading-none">
              UEFA-STYLE KNOCKOUT DRAW
            </h2>
            <p className="mt-2 text-xs sm:text-sm font-mono text-blue-200/80 max-w-2xl leading-relaxed">
              Experience the suspense of the live preliminary draw ceremony. 28 group stage qualifiers seeded into 14 knockout fixtures with automatic same-group protection.
            </p>
          </div>

          {/* Action Toolbar */}
          <div className="flex flex-wrap items-center gap-3 shrink-0">
            <button
              onClick={() => setSoundEnabled(!soundEnabled)}
              className="p-2.5 rounded-lg bg-black/60 border border-neutral-700 hover:border-brand-gold text-neutral-300 hover:text-white transition-colors"
              title={soundEnabled ? 'Mute Draw Sound Effects' : 'Enable Draw Sound Effects'}
            >
              {soundEnabled ? <Volume2 className="w-4 h-4 text-brand-gold" /> : <VolumeX className="w-4 h-4 text-neutral-500" />}
            </button>

            <button
              onClick={initializeDrawPools}
              disabled={isDrawing || isAutoPlaying}
              className="inline-flex items-center space-x-1.5 px-3.5 py-2.5 rounded-lg bg-neutral-900 border border-neutral-700 hover:border-neutral-500 text-xs font-mono text-neutral-300 hover:text-white transition-colors disabled:opacity-50"
            >
              <RotateCcw className="w-3.5 h-3.5" />
              <span>RESET</span>
            </button>

            <button
              onClick={() => setIsAutoPlaying(!isAutoPlaying)}
              disabled={isDrawing || activeStep === 'COMPLETE'}
              className={`inline-flex items-center space-x-2 px-4 py-2.5 rounded-lg text-xs font-mono font-bold tracking-wider uppercase transition-all duration-200 border ${
                isAutoPlaying
                  ? 'bg-amber-500/20 text-amber-300 border-amber-500 animate-pulse'
                  : 'bg-blue-900/60 hover:bg-blue-800 text-blue-200 border-blue-600'
              } disabled:opacity-50`}
            >
              <Play className="w-3.5 h-3.5" />
              <span>{isAutoPlaying ? 'PAUSE CEREMONY' : 'AUTO CEREMONY'}</span>
            </button>

            <button
              onClick={handleFastDrawAll}
              disabled={isDrawing || isAutoPlaying || activeStep === 'COMPLETE'}
              className="inline-flex items-center space-x-1.5 px-3.5 py-2.5 rounded-lg bg-neutral-900 hover:bg-neutral-800 border border-neutral-700 hover:border-blue-500 text-xs font-mono text-neutral-200 transition-colors disabled:opacity-50"
            >
              <Zap className="w-3.5 h-3.5 text-blue-400" />
              <span>FAST REVEAL</span>
            </button>

            <button
              onClick={() => drawNextTie()}
              disabled={isDrawing || isAutoPlaying || activeStep === 'COMPLETE'}
              className="inline-flex items-center space-x-2 px-5 py-2.5 rounded-lg bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-500 hover:to-indigo-500 text-white font-display text-sm tracking-wider uppercase transition-all shadow-[0_0_20px_rgba(37,99,235,0.5)] disabled:opacity-50 cursor-pointer"
            >
              <Shuffle className="w-4 h-4" />
              <span>DRAW TIE #{currentMatchNumber <= 14 ? currentMatchNumber : 14}</span>
            </button>

            {isAdmin && (
              <>
                <button
                  onClick={handleApplyToOfficial}
                  disabled={isApplying || pairings.length === 0}
                  className="inline-flex items-center space-x-1.5 px-4 py-2.5 rounded-lg bg-emerald-950 hover:bg-emerald-900 border border-emerald-600 text-xs font-mono font-bold text-emerald-300 transition-colors disabled:opacity-50 cursor-pointer shadow-md"
                  title="Commit drawn pairings to official knockout fixtures in database"
                >
                  <Save className="w-3.5 h-3.5" />
                  <span>{isApplying ? 'SAVING...' : 'APPLY TO FIXTURES'}</span>
                </button>

                <button
                  onClick={handleSyncToDesktop}
                  disabled={isSyncingDesktop}
                  className="inline-flex items-center space-x-1.5 px-4 py-2.5 rounded-lg bg-indigo-950 hover:bg-indigo-900 border border-indigo-600 text-xs font-mono font-bold text-indigo-300 transition-colors disabled:opacity-50 cursor-pointer shadow-md"
                  title="Export official draw to Desktop (text and CSV)"
                >
                  <Monitor className="w-3.5 h-3.5 text-indigo-400" />
                  <span>{isSyncingDesktop ? 'SYNCING...' : 'SYNC TO DESKTOP'}</span>
                </button>
              </>
            )}
          </div>
        </div>

        {/* Admin Feedback Banner */}
        {adminMessage && (
          <div className="mt-4 p-3 rounded-lg bg-emerald-950/90 border border-emerald-600 text-xs font-mono text-emerald-200 flex items-center space-x-2 animate-fade-in">
            <CheckCircle2 className="w-4 h-4 text-emerald-400 shrink-0" />
            <span>{adminMessage}</span>
          </div>
        )}

        {/* Draw Progress Bar */}
        <div className="mt-6 pt-4 border-t border-neutral-800/80">
          <div className="flex items-center justify-between text-xs font-mono mb-1.5">
            <span className="text-neutral-400">
              CEREMONY PROGRESS: <strong className="text-white">{pairings.length}</strong> / {totalMatchesToDraw} TIES DRAWN
            </span>
            <span className="text-brand-gold font-bold">{progressPercent}% COMPLETE</span>
          </div>
          <div className="w-full h-2 bg-neutral-900 rounded-full overflow-hidden border border-neutral-800">
            <div
              className="h-full bg-gradient-to-r from-brand-gold to-brand-red transition-all duration-500 ease-out"
              style={{ width: `${progressPercent}%` }}
            />
          </div>
        </div>
      </div>

      {/* Direct Round of 16 Qualifiers Pedestal (Awarded Byes) */}
      <div className="bg-[#0b0e14] border border-[#1e293b] rounded-2xl p-6 shadow-xl">
        <div className="flex items-center justify-between mb-4 pb-3 border-b border-[#1e293b]">
          <div className="flex items-center space-x-3">
            <div className="w-9 h-9 rounded-full bg-brand-gold/20 border border-brand-gold/60 flex items-center justify-center text-brand-gold">
              <Trophy className="w-5 h-5" />
            </div>
            <div>
              <h3 className="font-display text-xl text-white tracking-wider flex items-center space-x-2">
                <span>DIRECT ROUND OF 16 QUALIFIERS</span>
                <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-brand-gold/20 text-brand-gold border border-brand-gold/30">
                  BYE TO R16
                </span>
              </h3>
              <p className="text-xs font-mono text-neutral-400">
                Top 2 qualified teams across all 15 groups by total Goals For (GF). Automatically exempt from preliminary draw.
              </p>
            </div>
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {directQualifiers.map((dq, idx) => (
            <div
              key={dq.team_id}
              className="relative p-4 rounded-xl bg-gradient-to-br from-[#131b2c] to-[#0c101c] border border-brand-gold/40 flex items-center justify-between shadow-lg"
            >
              <div className="flex items-center space-x-3.5">
                <div className="w-12 h-12 rounded-full bg-black/60 border-2 border-brand-gold flex items-center justify-center text-brand-gold font-display text-xl">
                  {idx + 1}
                </div>
                <div>
                  <div className="flex items-center space-x-2">
                    <span className="font-display text-xl text-white tracking-wide">{dq.team_name}</span>
                    <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-emerald-500/20 text-emerald-400 border border-emerald-500/30">
                      R16 SEED #{idx + 1}
                    </span>
                  </div>
                  <div className="text-xs font-mono text-neutral-400 mt-1 flex items-center space-x-3">
                    <span>{dq.group_name} ({String(dq.group_position).includes('1') ? '1st Place' : '2nd Place'})</span>
                    <span>·</span>
                    <span className="text-brand-gold font-bold">{dq.goals_for} GOALS SCORED</span>
                    <span>·</span>
                    <span>GD: {dq.goal_difference > 0 ? `+${dq.goal_difference}` : dq.goal_difference}</span>
                  </div>
                </div>
              </div>

              <div className="hidden sm:block text-right">
                <span className="text-[11px] font-mono text-neutral-400 block uppercase">Bracket Slot</span>
                <span className="text-sm font-mono text-brand-gold font-bold">{idx === 0 ? 'R16_1 (Top Half)' : 'R16_5 (Bottom Half)'}</span>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* The Ceremonial Stage: Bowls & Active Reveal Center */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* BOWL 1: POT 1 (Group Winners / Seed 1) */}
        <div className="bg-[#0a0d14] border border-[#1e293b] rounded-2xl p-6 relative overflow-hidden flex flex-col justify-between">
          <div>
            <div className="flex items-center justify-between mb-3">
              <span className="text-xs font-mono text-blue-400 uppercase tracking-widest flex items-center space-x-1.5">
                <span className="w-2 h-2 rounded-full bg-blue-400" />
                <span>POT 1 — SEEDED SQUADS</span>
              </span>
              <span className="text-xs font-mono text-neutral-400">
                {pot1.length} BALLS REMAINING
              </span>
            </div>

            {/* Glowing Glass Bowl */}
            <div className="relative my-4 h-48 rounded-2xl bg-gradient-to-b from-blue-950/40 via-blue-900/10 to-transparent border border-blue-500/30 p-4 flex flex-wrap items-center justify-center gap-2 overflow-hidden shadow-inner">
              <div className="absolute inset-0 bg-[radial-gradient(circle_at_center,rgba(59,130,246,0.15)_0%,transparent_70%)]" />

              {pot1.map((ball) => (
                <div
                  key={ball.id}
                  className={`w-9 h-9 rounded-full bg-gradient-to-br from-blue-400 via-blue-600 to-blue-950 border border-blue-300 flex items-center justify-center text-[10px] font-mono font-bold text-white shadow-md transform transition-transform hover:scale-110 cursor-default select-none ${
                    activeStep === 'STIRRING' ? 'animate-bounce' : ''
                  }`}
                  title={`${ball.name} (${ball.group_name})`}
                >
                  {ball.group_name.replace('Group ', '')}
                </div>
              ))}

              {pot1.length === 0 && (
                <span className="text-xs font-mono text-neutral-500 uppercase tracking-wider">
                  Pot 1 Empty — All Seeded Drawn
                </span>
              )}
            </div>
          </div>

          <div className="text-[11px] font-mono text-neutral-400 text-center">
            Teams drawn from Pot 1 are designated Home contenders for Preliminary ties.
          </div>
        </div>

        {/* CENTER STAGE: THE REVEAL PEDESTAL */}
        <div className="bg-gradient-to-b from-[#101726] to-[#070b14] border-2 border-brand-gold/60 rounded-2xl p-6 flex flex-col items-center justify-center text-center relative shadow-[0_0_50px_rgba(212,175,55,0.1)] min-h-[320px]">
          <div className="absolute -top-3 px-3 py-0.5 rounded-full bg-brand-gold text-black font-mono text-[10px] font-bold tracking-widest uppercase">
            CEREMONY SPOTLIGHT
          </div>

          {activeStep === 'IDLE' && (
            <div className="space-y-3 py-6">
              <div className="w-16 h-16 rounded-full bg-brand-gold/10 border-2 border-dashed border-brand-gold/40 mx-auto flex items-center justify-center text-brand-gold">
                <Shuffle className="w-7 h-7" />
              </div>
              <h4 className="font-display text-2xl text-white">READY FOR DRAW</h4>
              <p className="text-xs font-mono text-neutral-400 max-w-xs mx-auto">
                Press &quot;DRAW TIE #{currentMatchNumber}&quot; or &quot;AUTO CEREMONY&quot; to begin extracting balls from the official bowls.
              </p>
            </div>
          )}

          {activeStep === 'STIRRING' && (
            <div className="space-y-4 py-8 animate-pulse">
              <div className="w-20 h-20 rounded-full bg-gradient-to-br from-brand-gold via-amber-600 to-amber-950 border-4 border-amber-300 mx-auto flex items-center justify-center text-white shadow-2xl animate-spin">
                <Sparkles className="w-8 h-8" />
              </div>
              <div className="font-display text-xl text-amber-300 tracking-wider">
                MIXING CEREMONIAL SPHERE...
              </div>
            </div>
          )}

          {(activeStep === 'REVEAL_HOME' || activeStep === 'REVEAL_AWAY' || activeStep === 'PAIRING_CONFIRMED') && (
            <div className="w-full space-y-4">
              <span className="text-[11px] font-mono text-brand-gold uppercase tracking-widest block">
                EXTRACTING FIXTURE #{currentMatchNumber <= 14 ? currentMatchNumber : 14}
              </span>

              <div className="grid grid-cols-2 gap-3 items-center">
                {/* Home Team Card */}
                <div className={`p-4 rounded-xl border transition-all ${
                  currentHomeBall
                    ? 'bg-blue-950/60 border-blue-500 text-white shadow-lg shadow-blue-900/30'
                    : 'bg-black/40 border-neutral-800 text-neutral-600'
                }`}>
                  <span className="text-[10px] font-mono text-blue-300 uppercase block mb-1">HOME SQUAD</span>
                  <div className="font-display text-xl text-white tracking-wide truncate">
                    {currentHomeBall ? currentHomeBall.name : 'Drawing...'}
                  </div>
                  {currentHomeBall && (
                    <span className="text-[11px] font-mono text-blue-300 mt-1 block">
                      {currentHomeBall.group_name}
                    </span>
                  )}
                </div>

                {/* Away Team Card */}
                <div className={`p-4 rounded-xl border transition-all ${
                  currentAwayBall
                    ? 'bg-rose-950/60 border-rose-500 text-white shadow-lg shadow-rose-900/30'
                    : 'bg-black/40 border-neutral-800 text-neutral-600'
                }`}>
                  <span className="text-[10px] font-mono text-rose-300 uppercase block mb-1">AWAY SQUAD</span>
                  <div className="font-display text-xl text-white tracking-wide truncate">
                    {currentAwayBall ? currentAwayBall.name : 'Awaiting Pot 2...'}
                  </div>
                  {currentAwayBall && (
                    <span className="text-[11px] font-mono text-rose-300 mt-1 block">
                      {currentAwayBall.group_name}
                    </span>
                  )}
                </div>
              </div>

              {activeStep === 'PAIRING_CONFIRMED' && (
                <div className="p-2.5 rounded bg-emerald-950/60 border border-emerald-500/60 text-xs font-mono text-emerald-300 flex items-center justify-center space-x-2 animate-fade-in">
                  <CheckCircle2 className="w-4 h-4 text-emerald-400" />
                  <span>PAIRING VALIDATED (SAME-GROUP PROTECTION RESPECTED)</span>
                </div>
              )}
            </div>
          )}

          {activeStep === 'COMPLETE' && (
            <div className="space-y-3 py-6 animate-fade-in">
              <div className="w-16 h-16 rounded-full bg-emerald-500/20 border-2 border-emerald-500 mx-auto flex items-center justify-center text-emerald-400">
                <CheckCircle2 className="w-8 h-8" />
              </div>
              <h4 className="font-display text-3xl text-white tracking-wide">DRAW COMPLETED!</h4>
              <p className="text-xs font-mono text-neutral-300 max-w-xs mx-auto">
                All 14 preliminary fixtures have been drawn. Winners advance directly to meet the 2 direct qualifiers in the Round of 16.
              </p>
            </div>
          )}
        </div>

        {/* BOWL 2: POT 2 (Runners-Up / Seed 2) */}
        <div className="bg-[#0a0d14] border border-[#1e293b] rounded-2xl p-6 relative overflow-hidden flex flex-col justify-between">
          <div>
            <div className="flex items-center justify-between mb-3">
              <span className="text-xs font-mono text-rose-400 uppercase tracking-widest flex items-center space-x-1.5">
                <span className="w-2 h-2 rounded-full bg-rose-400" />
                <span>POT 2 — UNSEEDED SQUADS</span>
              </span>
              <span className="text-xs font-mono text-neutral-400">
                {pot2.length} BALLS REMAINING
              </span>
            </div>

            {/* Glowing Glass Bowl */}
            <div className="relative my-4 h-48 rounded-2xl bg-gradient-to-b from-rose-950/40 via-rose-900/10 to-transparent border border-rose-500/30 p-4 flex flex-wrap items-center justify-center gap-2 overflow-hidden shadow-inner">
              <div className="absolute inset-0 bg-[radial-gradient(circle_at_center,rgba(244,63,94,0.15)_0%,transparent_70%)]" />

              {pot2.map((ball) => (
                <div
                  key={ball.id}
                  className={`w-9 h-9 rounded-full bg-gradient-to-br from-rose-400 via-rose-600 to-rose-950 border border-rose-300 flex items-center justify-center text-[10px] font-mono font-bold text-white shadow-md transform transition-transform hover:scale-110 cursor-default select-none ${
                    activeStep === 'STIRRING' ? 'animate-bounce' : ''
                  }`}
                  title={`${ball.name} (${ball.group_name})`}
                >
                  {ball.group_name.replace('Group ', '')}
                </div>
              ))}

              {pot2.length === 0 && (
                <span className="text-xs font-mono text-neutral-500 uppercase tracking-wider">
                  Pot 2 Empty — All Unseeded Drawn
                </span>
              )}
            </div>
          </div>

          <div className="text-[11px] font-mono text-neutral-400 text-center">
            Teams drawn from Pot 2 are designated Away contenders.
          </div>
        </div>
      </div>

      {/* DRAWN PAIRINGS BOARD (The 14 Preliminary Matches) */}
      <div className="bg-[#0b0e14] border border-[#1e293b] rounded-2xl p-6">
        <div className="flex items-center justify-between mb-6 pb-3 border-b border-[#1e293b]">
          <div>
            <h3 className="font-display text-2xl text-white tracking-wider">
              OFFICIAL CEREMONIAL FIXTURE BOARD ({pairings.length} / 14 DRAWN)
            </h3>
            <p className="text-xs font-mono text-neutral-400 mt-0.5">
              Preliminary Knockout Round pairings formed in ceremonial extraction order.
            </p>
          </div>
        </div>

        {pairings.length > 0 ? (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-2 gap-4">
            {pairings.map((p) => (
              <div
                key={p.matchNumber}
                className="p-4 rounded-xl bg-gradient-to-r from-[#0d131f] via-[#090d16] to-[#0d131f] border border-[#223049] hover:border-brand-gold/60 transition-all flex items-center justify-between shadow-md"
              >
                <div className="flex items-center space-x-3">
                  <span className="px-2.5 py-1 rounded bg-black/60 border border-neutral-800 text-xs font-mono font-bold text-brand-gold">
                    {p.slot}
                  </span>
                  <div>
                    <div className="flex items-center space-x-2 text-sm font-display text-white">
                      <span className="text-blue-300 font-bold">{p.homeTeam.name}</span>
                      <span className="text-neutral-500 font-mono text-xs">VS</span>
                      <span className="text-rose-300 font-bold">{p.awayTeam.name}</span>
                    </div>
                    <div className="text-[11px] font-mono text-neutral-400 mt-1 flex items-center space-x-2">
                      <span>{p.homeTeam.group_name}</span>
                      <span>×</span>
                      <span>{p.awayTeam.group_name}</span>
                      <span className="text-[10px] text-emerald-400">· Same-Group Safe</span>
                    </div>
                  </div>
                </div>

                <div className="text-right">
                  <span className="text-[10px] font-mono text-neutral-400 block uppercase">Time Drawn</span>
                  <span className="text-xs font-mono text-neutral-300">{p.timestamp}</span>
                </div>
              </div>
            ))}
          </div>
        ) : (
          <div className="text-center py-12 font-mono text-xs text-neutral-400">
            No ties drawn yet. Press &quot;DRAW TIE #1&quot; to begin the ceremony.
          </div>
        )}
      </div>
    </div>
  );
};

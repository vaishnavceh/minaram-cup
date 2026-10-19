import React, { useEffect, useState, useRef } from 'react';
import { api } from '../api';
import { PublicBracket, DirectQualifier, KnockoutConflict } from '../types';
import { BracketTree } from '../components/BracketTree';
import {
  GitFork,
  Trophy,
  Download,
  Check,
  Loader2,
  Sparkles,
  AlertCircle,
  Shield,
  Clock,
  Info,
  ChevronDown,
  ChevronUp,
  FileText,
  AlertTriangle,
  RefreshCw,
  Flame,
  Scale
} from 'lucide-react';

export const BracketPage: React.FC = () => {
  const [bracket, setBracket] = useState<PublicBracket>({ rounds: [] });
  const [rules, setRules] = useState<Record<string, string>>({});
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [isExporting, setIsExporting] = useState(false);
  const [downloadSuccess, setDownloadSuccess] = useState(false);
  const [activeStageTab, setActiveStageTab] = useState<string>('ALL');
  const [showRulesPanel, setShowRulesPanel] = useState(false);
  const [lastNotification, setLastNotification] = useState<string>('');
  const exportRef = useRef<HTMLDivElement>(null);

  const loadData = async (isManualRefresh: boolean = false) => {
    if (isManualRefresh) setRefreshing(true);
    try {
      const [bracketData, rulesData] = await Promise.all([
        api.getKnockoutBracket().catch(() => api.getBracket()),
        api.getKnockoutRules().catch(() => ({})),
      ]);
      setBracket(bracketData);
      setRules(rulesData);
      if (isManualRefresh) {
        setLastNotification('Prediction updated from latest standings.');
        setTimeout(() => setLastNotification(''), 4000);
      }
    } catch (err) {
      console.error('Failed to load knockout tournament data', err);
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  useEffect(() => {
    loadData();

    // Listen for live Server-Sent Events updates
    const RAW_BASE = (import.meta.env.VITE_API_URL as string) || '';
    const sseUrl = RAW_BASE ? `${RAW_BASE.replace(/\/+$/, '')}/api/events` : '/api/events';
    let es: EventSource | null = null;
    try {
      es = new EventSource(sseUrl);
      es.addEventListener('knockout_updated', () => {
        loadData();
        setLastNotification('Prediction updated from latest standings.');
        setTimeout(() => setLastNotification(''), 4500);
      });
      es.addEventListener('standings_updated', () => {
        loadData();
        setLastNotification('Prediction updated from latest standings.');
        setTimeout(() => setLastNotification(''), 4500);
      });
    } catch (e) {
      // Fallback
    }

    return () => {
      if (es) es.close();
    };
  }, []);

  const handleDownloadPng = async () => {
    if (!exportRef.current || isExporting) return;
    try {
      setIsExporting(true);
      const { downloadBracketAsPng } = await import('../utils/exportBracket');
      await downloadBracketAsPng(exportRef.current);
      setDownloadSuccess(true);
      setTimeout(() => setDownloadSuccess(false), 2500);
    } catch (err) {
      console.error('Failed to download bracket as PNG', err);
    } finally {
      setIsExporting(false);
    }
  };

  const directQualifiers: DirectQualifier[] = bracket.direct_qualifiers || [];
  const isProvisional = bracket.is_provisional ?? true;
  const conflicts: KnockoutConflict[] = bracket.conflicts || [];

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-10">
      {/* Toast Notification */}
      {lastNotification && (
        <div className="mb-6 p-3.5 rounded-xl bg-amber-950/80 border border-amber-600/60 text-amber-300 text-xs font-mono flex items-center justify-between shadow-lg animate-fade-in">
          <div className="flex items-center space-x-2.5">
            <Sparkles className="w-4 h-4 text-amber-400 shrink-0 animate-pulse" />
            <span>{lastNotification}</span>
          </div>
          <span className="text-[10px] text-amber-400/80 uppercase">Live Sync</span>
        </div>
      )}

      {/* Conflicts Alert Banner if administrator attention required */}
      {conflicts.length > 0 && (
        <div className="mb-8 p-4 rounded-xl bg-rose-950/60 border border-rose-600/70 text-rose-200 text-xs font-mono shadow-xl">
          <div className="flex items-start space-x-3">
            <AlertTriangle className="w-5 h-5 text-rose-400 shrink-0 mt-0.5" />
            <div>
              <strong className="text-white block uppercase tracking-wider mb-1">
                ADMINISTRATOR REVIEW REQUIRED: Standings & Fixture Conflicts Detected
              </strong>
              <p className="text-rose-300 mb-2">
                Recent changes to group stage standings have impacted positions of squads previously confirmed in official fixtures. Official fixtures are preserved and have not been silently modified.
              </p>
              <ul className="list-disc list-inside space-y-1 text-rose-300/90 text-[11px]">
                {conflicts.map((c, i) => (
                  <li key={i}>{c.message}</li>
                ))}
              </ul>
            </div>
          </div>
        </div>
      )}

      {/* Header */}
      <div className="mb-8 pb-6 border-b border-[#222222] flex flex-col md:flex-row md:items-end justify-between gap-6">
        <div>
          <div className="flex items-center space-x-2 text-xs font-mono uppercase tracking-widest text-brand-red mb-2">
            <Trophy className="w-4 h-4 text-brand-gold" />
            <span>MINARAM CUP 2026 PLAYOFFS</span>
          </div>
          <h1 className="font-display text-4xl sm:text-5xl text-white tracking-wider">
            KNOCKOUT / QUALIFIERS
          </h1>
          <p className="text-sm text-neutral-400 mt-2 max-w-2xl">
            Complete 30-team championship structure: 28 preliminary contenders battle through 14 matches to join the 2 Direct Round of 16 Qualifiers.
          </p>
        </div>

        {/* Action Controls */}
        <div className="flex flex-wrap items-center gap-3 shrink-0">
          {/* Provisional vs Final Badge */}
          <div className="flex items-center space-x-2 px-3.5 py-2 rounded bg-neutral-900 border border-neutral-800 text-xs font-mono text-neutral-300">
            <span className={`w-2 h-2 rounded-full ${isProvisional ? 'bg-amber-400 animate-pulse' : 'bg-emerald-400'}`} />
            <span className={`${isProvisional ? 'text-amber-400' : 'text-emerald-400'} font-bold uppercase tracking-wider`}>
              {isProvisional ? 'GROUP STAGE IN PROGRESS' : 'GROUP STAGE FINALIZED'}
            </span>
          </div>

          {/* Refresh Action */}
          <button
            type="button"
            onClick={() => loadData(true)}
            disabled={refreshing}
            className="inline-flex items-center space-x-1.5 px-3.5 py-2 rounded text-xs font-mono font-bold tracking-wider uppercase transition-colors bg-neutral-900 hover:bg-neutral-800 text-neutral-300 hover:text-white border border-neutral-800 hover:border-neutral-700 cursor-pointer"
            title="Recalculate predictions from latest standings"
          >
            <RefreshCw className={`w-3.5 h-3.5 text-neutral-400 ${refreshing ? 'animate-spin' : ''}`} />
            <span>{refreshing ? 'CALCULATING...' : 'REFRESH'}</span>
          </button>

          {/* Download PNG Action */}
          <button
            type="button"
            onClick={handleDownloadPng}
            disabled={isExporting}
            className={`inline-flex items-center space-x-2 px-4 py-2 rounded text-xs font-mono font-bold tracking-wider uppercase transition-all duration-200 border cursor-pointer select-none shadow-sm ${
              downloadSuccess
                ? 'bg-emerald-950/90 text-emerald-300 border-emerald-600/80 shadow-emerald-900/30'
                : 'bg-neutral-900 hover:bg-neutral-800 text-neutral-300 hover:text-white border-neutral-700 hover:border-amber-500/60'
            } disabled:opacity-50`}
            title="Download tournament knockout bracket as a PNG image"
            aria-label="Download Knockout Bracket as PNG"
          >
            {isExporting ? (
              <Loader2 className="w-3.5 h-3.5 animate-spin text-amber-400" />
            ) : downloadSuccess ? (
              <Check className="w-3.5 h-3.5 text-emerald-400" />
            ) : (
              <Download className="w-3.5 h-3.5 text-amber-400" />
            )}
            <span>{downloadSuccess ? 'PNG SAVED' : 'DOWNLOAD PNG'}</span>
          </button>
        </div>
      </div>

      {/* Mandatory Prominent Predicted Bracket Banner (Section 7) */}
      <div className="mb-8 p-5 rounded-2xl bg-gradient-to-r from-[#181105] via-[#120d04] to-[#0a0a0a] border border-amber-500/40 shadow-xl">
        <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3">
          <div className="flex items-start space-x-3.5">
            <div className="w-8 h-8 rounded-lg bg-amber-500/20 border border-amber-500/40 flex items-center justify-center text-amber-400 shrink-0 mt-0.5">
              <Sparkles className="w-4 h-4" />
            </div>
            <div>
              <div className="flex items-center space-x-2 flex-wrap gap-y-1">
                <h2 className="font-display text-lg sm:text-xl text-amber-300 tracking-wide">
                  PREDICTED KNOCKOUT BRACKET — NOT OFFICIAL
                </h2>
                {isProvisional && (
                  <span className="text-[10px] font-mono font-bold px-2 py-0.5 rounded bg-amber-500/20 text-amber-300 border border-amber-500/30 uppercase tracking-widest">
                    PROVISIONAL — GROUP STAGE IN PROGRESS
                  </span>
                )}
              </div>
              <p className="text-xs sm:text-sm font-mono text-neutral-300 mt-1 max-w-3xl leading-relaxed">
                Fixtures, direct qualifiers and advancement scenarios are generated from the current standings. They remain predictions until confirmed or manually updated by the tournament administrator.
              </p>
            </div>
          </div>

          <div className="shrink-0 text-right font-mono text-[11px] text-neutral-400 pl-11 sm:pl-0">
            <div>Draw Seed: <span className="text-amber-400 uppercase font-bold">{bracket.draw_method || 'Seeded'}</span></div>
            {bracket.last_updated && (
              <div className="text-[10px] text-neutral-400">Snapshot: {bracket.last_updated}</div>
            )}
          </div>
        </div>
      </div>

      {/* DIRECT ROUND OF 16 QUALIFIERS SECTION (Section 2) */}
      <div className="mb-10">
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center space-x-2.5">
            <Flame className="w-5 h-5 text-amber-400" />
            <h2 className="font-display text-2xl text-white tracking-wide uppercase">
              DIRECT ROUND OF 16 QUALIFIERS
            </h2>
          </div>
          <span className="text-xs font-mono text-neutral-400 hidden sm:inline-block">
            Top 2 Goalscoring Squads Bypass Preliminary Round
          </span>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
          {directQualifiers.length > 0 ? (
            directQualifiers.map((dq, idx) => (
              <div
                key={dq.team_id || idx}
                className="relative overflow-hidden rounded-2xl bg-gradient-to-br from-[#181308] via-[#100e08] to-[#0a0a0a] border border-amber-500/50 p-5 shadow-xl hover:border-amber-400 transition-all duration-300"
              >
                {/* Top Row: Rank Badge & Status Pill */}
                <div className="flex items-center justify-between mb-3.5">
                  <div className="flex items-center space-x-2">
                    <span className="w-7 h-7 rounded-full bg-amber-500/20 border border-amber-500/40 text-amber-300 font-mono font-bold text-xs flex items-center justify-center">
                      #{idx + 1}
                    </span>
                    <span className="text-[11px] font-mono uppercase tracking-wider text-amber-400 font-bold">
                      Direct Qualifier Seed {idx === 0 ? 'Top Half (R16_1)' : 'Bottom Half (R16_5)'}
                    </span>
                  </div>

                  {dq.is_override ? (
                    <span className="text-[10px] font-mono font-bold px-2 py-0.5 rounded bg-purple-950/80 text-purple-300 border border-purple-700/60 uppercase">
                      Admin Manual Override
                    </span>
                  ) : (
                    <span className="text-[10px] font-mono font-bold px-2 py-0.5 rounded bg-amber-950/60 text-amber-300 border border-amber-600/50 uppercase tracking-widest">
                      PREDICTED DIRECT QUALIFIER
                    </span>
                  )}
                </div>

                {/* Team Name and Group Location */}
                <div className="mb-4">
                  <h3 className="font-display text-3xl text-white tracking-wide truncate">
                    {dq.team_name}
                  </h3>
                  <div className="flex items-center space-x-2 mt-1 text-xs font-mono text-neutral-400">
                    <span className="text-amber-400 font-bold">{dq.group_name}</span>
                    <span>·</span>
                    <span className="text-neutral-300">{dq.group_position} in Group</span>
                    {dq.is_provisional && (
                      <>
                        <span>·</span>
                        <span className="text-amber-500 italic text-[11px]">Matches Pending</span>
                      </>
                    )}
                  </div>
                </div>

                {/* Stats Matrix Grid */}
                <div className="grid grid-cols-4 sm:grid-cols-6 gap-2 pt-3 border-t border-neutral-800 text-center font-mono">
                  <div className="p-2 rounded bg-black/50 border border-neutral-800/80">
                    <span className="block text-[10px] text-neutral-400 uppercase">Played</span>
                    <span className="text-sm font-bold text-white">{dq.played}</span>
                  </div>
                  <div className="p-2 rounded bg-amber-950/30 border border-amber-600/40">
                    <span className="block text-[10px] text-amber-400 font-bold uppercase">GF (Goals)</span>
                    <span className="text-base font-bold text-amber-300">{dq.goals_for}</span>
                  </div>
                  <div className="p-2 rounded bg-black/50 border border-neutral-800/80">
                    <span className="block text-[10px] text-neutral-400 uppercase">GA (Conceded)</span>
                    <span className="text-sm font-bold text-neutral-300">{dq.goals_against}</span>
                  </div>
                  <div className="p-2 rounded bg-black/50 border border-neutral-800/80">
                    <span className="block text-[10px] text-neutral-400 uppercase">GD</span>
                    <span className={`text-sm font-bold ${dq.goal_difference >= 0 ? 'text-emerald-400' : 'text-rose-400'}`}>
                      {dq.goal_difference >= 0 ? `+${dq.goal_difference}` : dq.goal_difference}
                    </span>
                  </div>
                  <div className="p-2 rounded bg-black/50 border border-neutral-800/80 col-span-2 sm:col-span-1">
                    <span className="block text-[10px] text-neutral-400 uppercase">Points</span>
                    <span className="text-sm font-bold text-white">{dq.points}</span>
                  </div>
                  <div className="p-2 rounded bg-black/50 border border-neutral-800/80 col-span-2 sm:col-span-1">
                    <span className="block text-[10px] text-neutral-400 uppercase">GF / Match</span>
                    <span className="text-sm font-bold text-amber-400">{dq.goals_per_match?.toFixed(2) || '0.00'}</span>
                  </div>
                </div>

                {/* Qualification Criteria Footer */}
                <div className="mt-3.5 pt-2.5 border-t border-neutral-800/60 flex items-center justify-between text-[11px] font-mono text-neutral-400">
                  <span className="truncate max-w-[280px]">
                    Criteria: <strong className="text-neutral-300">Highest Goals For (GF)</strong>
                  </span>
                  <span className="text-amber-400/90 font-bold">
                    Direct R16 Entry
                  </span>
                </div>
              </div>
            ))
          ) : (
            <div className="col-span-2 text-center py-8 rounded-xl bg-neutral-900/50 border border-neutral-800 text-neutral-400 font-mono text-xs">
              Calculating Direct Qualifiers from current standings...
            </div>
          )}
        </div>
      </div>

      {/* Stage Navigation Filter Tabs */}
      <div className="mb-6 flex flex-wrap items-center justify-between gap-4 border-b border-neutral-800 pb-4">
        <div className="flex flex-wrap items-center gap-2">
          {[
            { id: 'ALL', label: 'All Rounds (Tree)' },
            { id: 'preliminary', label: 'Preliminary (14)' },
            { id: '16', label: 'Round of 16 (8)' },
            { id: 'quarter', label: 'Quarter-Finals (4)' },
            { id: 'semi', label: 'Semi-Finals (2)' },
            { id: 'final', label: 'Grand Final (1)' },
          ].map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveStageTab(tab.id)}
              className={`px-3 py-1.5 rounded-lg text-xs font-mono font-bold tracking-wider uppercase transition-all duration-200 border cursor-pointer select-none ${
                activeStageTab === tab.id
                  ? 'bg-amber-500/20 text-amber-300 border-amber-500/60 shadow-[0_0_15px_rgba(245,158,11,0.15)]'
                  : 'bg-neutral-900 text-neutral-400 hover:text-white border-neutral-800 hover:border-neutral-700'
              }`}
            >
              {tab.label}
            </button>
          ))}
        </div>

        {/* Toggle Knockout Rules Button */}
        <button
          type="button"
          onClick={() => setShowRulesPanel(!showRulesPanel)}
          className="inline-flex items-center space-x-2 px-3 py-1.5 rounded-lg text-xs font-mono font-bold tracking-wider uppercase transition-colors bg-neutral-900 hover:bg-neutral-800 text-neutral-300 hover:text-white border border-neutral-800 hover:border-neutral-700 cursor-pointer"
        >
          <FileText className="w-3.5 h-3.5 text-amber-400" />
          <span>OFFICIAL KNOCKOUT RULES</span>
          {showRulesPanel ? <ChevronUp className="w-3.5 h-3.5" /> : <ChevronDown className="w-3.5 h-3.5" />}
        </button>
      </div>

      {/* PUBLIC OFFICIAL KNOCKOUT RULES PANEL (Section 9) */}
      {showRulesPanel && (
        <div className="mb-10 rounded-2xl bg-[#111114] border border-amber-500/30 p-6 shadow-2xl transition-all animate-fade-in">
          <div className="flex items-center justify-between pb-4 mb-5 border-b border-neutral-800">
            <div className="flex items-center space-x-2.5">
              <Scale className="w-5 h-5 text-amber-400" />
              <h2 className="font-display text-2xl text-white tracking-wide uppercase">
                MINARAM CUP 2026 — OFFICIAL KNOCKOUT MATCH RULES
              </h2>
            </div>
            <span className="text-[11px] font-mono text-neutral-400">
              Last Updated: {rules.rules_updated_at || '2026-10-18'}
            </span>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 text-xs font-mono text-neutral-300 leading-relaxed">
            {/* Rule 9.1 */}
            <div className="p-4 rounded-xl bg-black/40 border border-neutral-800/80">
              <span className="font-bold text-amber-400 block mb-1.5 uppercase tracking-wider text-[11px]">
                9.1 Match Format
              </span>
              <p>
                Every knockout fixture is a single-elimination match. The losing squad is immediately eliminated from the championship bracket. The winning squad advances directly into the designated next round slot.
              </p>
            </div>

            {/* Rule 9.2 */}
            <div className="p-4 rounded-xl bg-black/40 border border-neutral-800/80">
              <span className="font-bold text-amber-400 block mb-1.5 uppercase tracking-wider text-[11px]">
                9.2 Game Settings
              </span>
              <p>
                All knockout matches use official tournament eFootball authentic mobile settings. Standard match duration: <strong>{rules.match_duration_minutes || '90'} Minutes</strong>. Gameplay conditions and squad restrictions apply equally to all competitors.
              </p>
            </div>

            {/* Rule 9.3 */}
            <div className="p-4 rounded-xl bg-black/40 border border-neutral-800/80">
              <span className="font-bold text-amber-400 block mb-1.5 uppercase tracking-wider text-[11px]">
                9.3 Drawn Matches & Shootouts
              </span>
              <p>
                Every completed knockout clash must produce exactly one official winner. If tied at full time, matches proceed to Extra Time and/or Penalty Shootouts according to the configured rule. Draws are strictly forbidden in knockout rounds.
              </p>
            </div>

            {/* Rule 9.4 */}
            <div className="p-4 rounded-xl bg-black/40 border border-neutral-800/80">
              <span className="font-bold text-amber-400 block mb-1.5 uppercase tracking-wider text-[11px]">
                9.4 Result Submission
              </span>
              <p>
                Scores must be officially submitted and confirmed by authorized tournament desk officials. Both scores are validated before confirmation. Confirmed winners advance automatically to the next round slot.
              </p>
            </div>

            {/* Rule 9.5 & 9.6 */}
            <div className="p-4 rounded-xl bg-black/40 border border-neutral-800/80">
              <span className="font-bold text-amber-400 block mb-1.5 uppercase tracking-wider text-[11px]">
                9.5 Disconnections & Technical Issues
              </span>
              <p>
                If a disconnect or crash occurs during a fixture, the status is flagged as <strong>UNDER REVIEW</strong>. Desk officials determine whether to replay, resume with existing scoreline, or accept an agreed outcome. Automatic walkovers are prohibited without desk review.
              </p>
            </div>

            {/* Rule 9.7 & 9.8 */}
            <div className="p-4 rounded-xl bg-black/40 border border-neutral-800/80">
              <span className="font-bold text-amber-400 block mb-1.5 uppercase tracking-wider text-[11px]">
                9.6 Walkovers & Disputes
              </span>
              <p>
                Walkovers require verified documentation and authorized desk approval. Awarded 3–0 walkover scores are audited with reasons. Disputed matches are held under review until officially resolved.
              </p>
            </div>
          </div>
        </div>
      )}

      {/* Main Bracket Tree Display Area */}
      {loading ? (
        <div className="text-center py-20 font-mono text-sm text-neutral-500">
          <Loader2 className="w-6 h-6 animate-spin text-amber-400 mx-auto mb-2" />
          Loading dynamic knockout tournament bracket...
        </div>
      ) : (
        <div ref={exportRef} className="p-4 sm:p-6 rounded-2xl bg-[#0c0c0c] border border-neutral-800/80 shadow-2xl relative">
          <BracketTree
            bracket={bracket}
            selectedStageFilter={activeStageTab}
            showTrophyPedestal={activeStageTab === 'ALL'}
          />

          {/* Status Legend (Section 11) */}
          <div className="mt-8 pt-4 border-t border-neutral-800/80 flex flex-wrap items-center justify-between text-xs font-mono gap-3">
            <div className="flex flex-wrap items-center gap-3">
              <span className="text-neutral-400 uppercase tracking-widest text-[10px]">LEGEND:</span>
              <span className="inline-flex items-center space-x-1 px-2 py-0.5 rounded bg-amber-950/40 border border-dashed border-amber-600/50 text-[10px] text-amber-300">
                <Sparkles className="w-2.5 h-2.5 text-amber-400" />
                <span>PREDICTED</span>
              </span>
              <span className="inline-flex items-center space-x-1 px-2 py-0.5 rounded bg-cyan-950/80 border border-cyan-700/60 text-[10px] text-cyan-300">
                <Shield className="w-2.5 h-2.5 text-cyan-400" />
                <span>CONFIRMED</span>
              </span>
              <span className="inline-flex items-center space-x-1 px-2 py-0.5 rounded bg-rose-950/80 border border-rose-600/70 text-[10px] text-rose-300">
                <span className="w-1.5 h-1.5 rounded-full bg-rose-400 animate-pulse" />
                <span>LIVE</span>
              </span>
              <span className="inline-flex items-center space-x-1 px-2 py-0.5 rounded bg-purple-950/80 border border-purple-600/70 text-[10px] text-purple-300">
                <span>UNDER REVIEW</span>
              </span>
              <span className="inline-flex items-center space-x-1 px-2 py-0.5 rounded bg-emerald-950/80 border border-emerald-700/60 text-[10px] text-emerald-300">
                <span>FT (COMPLETED)</span>
              </span>
            </div>

            {/* Timestamp */}
            <div className="text-neutral-400 text-[11px]">
              Minaram Cup 2026 · TKMCE eFootball Championship
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

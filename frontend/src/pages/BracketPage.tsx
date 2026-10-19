import React, { useEffect, useState, useRef } from 'react';
import { api } from '../api';
import { PublicBracket, DirectQualifier, KnockoutConflict } from '../types';
import { BracketTree } from '../components/BracketTree';
import { UefaKnockoutDraw } from '../components/UefaKnockoutDraw';
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
import { useLiveUpdates } from '../hooks/useLiveUpdates';

export const BracketPage: React.FC = () => {
  const [bracket, setBracket] = useState<PublicBracket>({ rounds: [] });
  const [rules, setRules] = useState<Record<string, string>>({});
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [isExporting, setIsExporting] = useState(false);
  const [downloadSuccess, setDownloadSuccess] = useState(false);
  const [activeStageTab, setActiveStageTab] = useState<string>('ALL');
  const [showRulesPanel, setShowRulesPanel] = useState(false);
  const [showDrawDesk, setShowDrawDesk] = useState(false);
  const [allTeams, setAllTeams] = useState<any[]>([]);
  const [lastNotification, setLastNotification] = useState<string>('');
  const exportRef = useRef<HTMLDivElement>(null);

  const loadData = async (isManualRefresh: boolean = false) => {
    if (isManualRefresh) setRefreshing(true);
    try {
      const [bracketData, rulesData, teamsData] = await Promise.all([
        api.getKnockoutBracket().catch(() => api.getBracket()),
        api.getKnockoutRules().catch(() => ({})),
        api.getTeams().catch(() => []),
      ]);
      setBracket(bracketData);
      setRules(rulesData);
      setAllTeams(teamsData);
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
  }, []);

  useLiveUpdates((evt) => {
    const evType = evt.event || (evt as any).type;
    if (['knockout_updated', 'standings_updated', 'ceremonial_draw_applied', 'ceremonial_draw_reset', 'knockout_fixtures_cleared', 'fixtures_status_updated', 'result_updated'].includes(evType)) {
      loadData();
      setLastNotification('Live update received: tournament bracket refreshed.');
      setTimeout(() => setLastNotification(''), 4500);
    }
  });

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
  const conflicts: KnockoutConflict[] = bracket.conflicts || [];

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-10 relative">
      {/* UCL Ambient Background Glow */}
      <div className="ucl-ambient" aria-hidden />

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

      {/* Knockout Banner with UCL Stadium Wallpaper */}
      <div className="mb-8 relative rounded-2xl overflow-hidden border border-blue-500/30 bg-gradient-to-r from-[#030d26] via-[#051336] to-[#020718] p-6 sm:p-8 shadow-2xl">
        <div className="absolute right-0 top-0 bottom-0 w-full sm:w-2/3 opacity-30 sm:opacity-50 pointer-events-none">
          <img
            src="/assets/backgrounds/ucl_stadium_bg.jpg"
            alt="UEFA Champions League Stadium"
            className="w-full h-full object-cover object-center filter contrast-125"
          />
          <div className="absolute inset-0 bg-gradient-to-r from-[#030d26] via-[#030d26]/80 to-transparent" />
        </div>

        <div className="relative z-10 flex flex-col md:flex-row md:items-end justify-between gap-6">
          <div>
            <div className="flex items-center space-x-2 text-xs font-mono uppercase tracking-widest text-blue-400 mb-2">
              <Trophy className="w-4 h-4 text-amber-400" />
              <span>MINARAM CUP 2026 PLAYOFFS · UEFA CHAMPIONS LEAGUE STAGE</span>
            </div>
            <h1 className="font-display text-4xl sm:text-5xl text-white tracking-wider">
              KNOCKOUT / QUALIFIERS
            </h1>
            <p className="text-sm text-blue-200/80 mt-2 max-w-2xl">
              Complete 30-team championship structure: 28 preliminary contenders battle through 14 matches to join the 2 Direct Round of 16 Qualifiers.
            </p>
          </div>

          {/* Action Controls */}
          <div className="flex flex-wrap items-center gap-3 shrink-0">
            {/* Bracket Sync Status Badge */}
            <div className="flex items-center space-x-2 px-3.5 py-2 rounded bg-blue-950/80 border border-blue-500/50 text-xs font-mono text-blue-200 shadow-[0_0_15px_rgba(59,130,246,0.3)]">
              <span className="w-2 h-2 rounded-full bg-blue-400 animate-pulse" />
              <span className="text-blue-300 font-bold uppercase tracking-wider">ADMIN DRAW SYNCED</span>
            </div>

            {/* Toggle Ceremonial Draw Desk Action */}
            <button
              type="button"
              onClick={() => setShowDrawDesk(!showDrawDesk)}
              className={`inline-flex items-center space-x-1.5 px-3.5 py-2 rounded text-xs font-mono font-bold tracking-wider uppercase transition-all duration-200 border cursor-pointer select-none shadow-sm ${
                showDrawDesk
                  ? 'bg-amber-500/25 text-amber-300 border-amber-500/80 shadow-[0_0_15px_rgba(245,158,11,0.25)]'
                  : 'bg-gradient-to-r from-amber-600 to-amber-700 hover:from-amber-500 hover:to-amber-600 text-white border-amber-500/60'
              }`}
              title="Open or close the interactive UEFA Ceremonial Draw Desk"
            >
              <Sparkles className="w-3.5 h-3.5 text-amber-300" />
              <span>{showDrawDesk ? 'HIDE DRAW DESK' : 'CEREMONIAL DRAW DESK'}</span>
            </button>

            {/* Refresh Action */}
            <button
              type="button"
              onClick={() => loadData(true)}
              disabled={refreshing}
              className="inline-flex items-center space-x-1.5 px-3.5 py-2 rounded text-xs font-mono font-bold tracking-wider uppercase transition-colors bg-blue-950/60 hover:bg-blue-900/60 text-blue-200 hover:text-white border border-blue-700/50 cursor-pointer"
              title="Recalculate predictions from latest standings"
            >
              <RefreshCw className={`w-3.5 h-3.5 text-blue-400 ${refreshing ? 'animate-spin' : ''}`} />
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
                  : 'bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-500 hover:to-indigo-500 text-white border-blue-500/60 shadow-[0_0_20px_rgba(37,99,235,0.4)]'
              } disabled:opacity-50`}
              title="Download tournament knockout bracket as a PNG image"
              aria-label="Download Knockout Bracket as PNG"
            >
              {isExporting ? (
                <Loader2 className="w-3.5 h-3.5 animate-spin text-white" />
              ) : downloadSuccess ? (
                <Check className="w-3.5 h-3.5 text-emerald-400" />
              ) : (
                <Download className="w-3.5 h-3.5 text-white" />
              )}
              <span>{downloadSuccess ? 'PNG SAVED' : 'DOWNLOAD PNG'}</span>
            </button>
          </div>
        </div>
      </div>

      {/* Interactive UEFA Ceremonial Draw Desk (when toggled) */}
      {showDrawDesk && (
        <div className="mb-10 animate-fade-in">
          <UefaKnockoutDraw
            bracket={bracket}
            token={typeof window !== 'undefined' ? localStorage.getItem('minaram_admin_token') || localStorage.getItem('admin_token') || '' : ''}
            isAdmin={typeof window !== 'undefined' && Boolean(localStorage.getItem('minaram_admin_token') || localStorage.getItem('admin_token'))}
            allTeams={allTeams}
            onRefreshBracket={() => loadData(true)}
          />
        </div>
      )}

      {/* Live Draw Sync Status Banner */}
      <div className="mb-8 p-4 rounded-xl bg-gradient-to-r from-[#050f28] via-[#08143a] to-[#050f28] border border-blue-700/40 shadow-xl shadow-blue-950/30">
        <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3">
          <div className="flex items-start space-x-3">
            <div className="w-8 h-8 rounded-lg bg-blue-500/10 border border-blue-500/30 flex items-center justify-center text-blue-400 shrink-0 mt-0.5">
              <GitFork className="w-4 h-4" />
            </div>
            <div>
              <h2 className="font-display text-lg sm:text-xl text-blue-200 tracking-wide">
                OFFICIAL KNOCKOUT BRACKET
              </h2>
              <p className="text-xs font-mono text-blue-300/60 mt-0.5">
                Fixtures are synced live from the official administrator draw. Draw method: <strong className="text-blue-300">{bracket.draw_method?.toUpperCase() || 'SEEDED'}</strong>
                {bracket.last_updated && <span className="ml-2 text-neutral-500">· Snapshot: {bracket.last_updated}</span>}
              </p>
            </div>
          </div>
          <div className="flex items-center space-x-2 shrink-0">
            <span className="w-2 h-2 rounded-full bg-blue-400 animate-pulse" />
            <span className="text-[11px] font-mono text-blue-300 uppercase tracking-widest">Live Synced</span>
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

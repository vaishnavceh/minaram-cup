import React, { useState, useEffect } from 'react';
import { api } from '../api';
import { PublicBracket, DirectQualifier, KnockoutConflict, KnockoutAuditEntry } from '../types';
import {
  Trophy,
  Shield,
  Sparkles,
  RefreshCw,
  CheckCircle2,
  AlertTriangle,
  Radio,
  FileText,
  Clock,
  Edit,
  Save,
  Trash2,
  Flame,
  Check,
  X,
  Shuffle,
  Users,
  RotateCcw,
  ChevronDown
} from 'lucide-react';
import { UefaKnockoutDraw } from './UefaKnockoutDraw';
import { useLiveUpdates } from '../hooks/useLiveUpdates';

interface AdminKnockoutManagerProps {
  token: string;
  onRefreshParent?: () => void;
}

export const AdminKnockoutManager: React.FC<AdminKnockoutManagerProps> = ({ token, onRefreshParent }) => {
  const [bracket, setBracket] = useState<PublicBracket>({ rounds: [] });
  const [allTeams, setAllTeams] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [adminSection, setAdminSection] = useState<'fixtures' | 'draw_ceremony'>('fixtures');
  const [activeStage, setActiveStage] = useState('ALL');
  const [statusFilter, setStatusFilter] = useState('ALL');
  const [successMessage, setSuccessMessage] = useState('');
  const [errorMessage, setErrorMessage] = useState('');
  const [showAuditLogs, setShowAuditLogs] = useState(false);
  const [auditLogs, setAuditLogs] = useState<KnockoutAuditEntry[]>([]);

  // Modals
  const [resultModalSlot, setResultModalSlot] = useState<string | null>(null);
  const [homeScore, setHomeScore] = useState<number>(0);
  const [awayScore, setAwayScore] = useState<number>(0);
  const [homePenalty, setHomePenalty] = useState<string>('');
  const [awayPenalty, setAwayPenalty] = useState<string>('');
  const [winnerMethod, setWinnerMethod] = useState<string>('Regular Time');
  const [resultNotes, setResultNotes] = useState<string>('');

  const [walkoverModalSlot, setWalkoverModalSlot] = useState<string | null>(null);
  const [walkoverWinnerId, setWalkoverWinnerId] = useState<number | null>(null);
  const [walkoverReason, setWalkoverReason] = useState<string>('');

  const [editFixtureSlot, setEditFixtureSlot] = useState<string | null>(null);
  const [editHomeId, setEditHomeId] = useState<number | ''>('');
  const [editAwayId, setEditAwayId] = useState<number | ''>('');
  const [editDate, setEditDate] = useState<string>('');
  const [editTime, setEditTime] = useState<string>('');
  const [editVenue, setEditVenue] = useState<string>('');

  const [showOverrideModal, setShowOverrideModal] = useState<boolean>(false);
  const [overrideSlotIndex, setOverrideSlotIndex] = useState<number>(0);
  const [overrideTeamId, setOverrideTeamId] = useState<number | ''>('');
  const [overrideReason, setOverrideReason] = useState<string>('');

  const loadData = async () => {
    try {
      const [bData, tData] = await Promise.all([
        api.getKnockoutBracket(),
        api.getTeams().catch(() => []),
      ]);
      setBracket(bData);
      setAllTeams(tData);
    } catch (err: any) {
      setErrorMessage(err.message || 'Failed to load knockout data.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  useLiveUpdates((evt) => {
    const evType = evt.event || (evt as any).type;
    if (['knockout_updated', 'standings_updated', 'ceremonial_draw_applied', 'ceremonial_draw_reset', 'knockout_fixtures_cleared', 'fixtures_status_updated'].includes(evType)) {
      loadData();
    }
  });

  const showSuccess = (msg: string) => {
    setSuccessMessage(msg);
    setTimeout(() => setSuccessMessage(''), 4500);
  };

  const showError = (msg: string) => {
    setErrorMessage(msg);
    setTimeout(() => setErrorMessage(''), 5500);
  };

  const handleRecalculate = async () => {
    try {
      setLoading(true);
      const res = await api.adminRecalculateKnockout(token);
      showSuccess(res.message || 'Knockout predictions recalculated from latest standings.');
      await loadData();
      if (onRefreshParent) onRefreshParent();
    } catch (err: any) {
      showError(err.message || 'Recalculation failed.');
    } finally {
      setLoading(false);
    }
  };

  const handleDrawMethodToggle = async () => {
    const nextMethod = bracket.draw_method === 'random' ? 'seeded' : 'random';
    if (!window.confirm(`Switch preliminary draw method to '${nextMethod.toUpperCase()}'?`)) return;
    try {
      setLoading(true);
      await api.adminUpdateDrawConfig(nextMethod, token);
      showSuccess(`Draw method updated to ${nextMethod.toUpperCase()}.`);
      await loadData();
    } catch (err: any) {
      showError(err.message || 'Failed to update draw method.');
    } finally {
      setLoading(false);
    }
  };

  const handleThirdPlaceToggle = async () => {
    const isCurrentlyEnabled = bracket.rules?.third_place_enabled?.toLowerCase() === 'true';
    const nextState = !isCurrentlyEnabled;
    try {
      setLoading(true);
      await api.adminToggleThirdPlace(nextState, token);
      showSuccess(`Third-place playoff match ${nextState ? 'ENABLED' : 'DISABLED'}.`);
      await loadData();
    } catch (err: any) {
      showError(err.message || 'Failed to toggle third-place playoff.');
    } finally {
      setLoading(false);
    }
  };

  const handleBatchConfirm = async (stage: string) => {
    if (!window.confirm(`Officially confirm all fixtures in '${stage}' into the tournament bracket?`)) return;
    try {
      setLoading(true);
      const res = await api.adminBatchConfirmStage(stage, token);
      showSuccess(`Confirmed ${res.count} fixtures in ${stage}.`);
      await loadData();
    } catch (err: any) {
      showError(err.message || 'Batch confirm failed.');
    } finally {
      setLoading(false);
    }
  };

  const handleConfirmSingle = async (slot: string) => {
    try {
      await api.adminConfirmFixture(slot, token);
      showSuccess(`Fixture ${slot} officially CONFIRMED.`);
      await loadData();
    } catch (err: any) {
      showError(err.message || 'Failed to confirm fixture.');
    }
  };

  const handleUnconfirmSingle = async (slot: string) => {
    if (!window.confirm(`Revert fixture ${slot} back to PREDICTED?`)) return;
    try {
      await api.adminUnconfirmFixture(slot, token);
      showSuccess(`Fixture ${slot} reverted to unconfirmed prediction.`);
      await loadData();
    } catch (err: any) {
      showError(err.message || 'Failed to unconfirm fixture.');
    }
  };

  const handleResetPredictions = async () => {
    if (!window.confirm('Reset unconfirmed predictions? This will not affect any confirmed fixtures or completed scores.')) return;
    try {
      setLoading(true);
      await api.adminResetPredictions(token);
      showSuccess('Unconfirmed predictions successfully reset.');
      await loadData();
    } catch (err: any) {
      showError(err.message || 'Failed to reset predictions.');
    } finally {
      setLoading(false);
    }
  };

  const [showClearDropdown, setShowClearDropdown] = useState(false);

  const handleClearKnockoutFixtures = async (mode: 'ALL' | 'PREDICTED' | 'CONFIRMED') => {
    const labels: Record<string, string> = {
      ALL: 'ALL preliminary fixtures (both Predicted & Confirmed)',
      PREDICTED: 'only unconfirmed PREDICTED / LIVE DRAW fixtures',
      CONFIRMED: 'only CONFIRMED preliminary fixtures'
    };
    if (!window.confirm(`Clear ${labels[mode]} from the knockout bracket?`)) return;
    try {
      setLoading(true);
      const res = await api.adminClearKnockoutFixtures(mode, token);
      showSuccess(res.message || `Cleared ${mode} fixtures successfully.`);
      setShowClearDropdown(false);
      await loadData();
      if (onRefreshParent) onRefreshParent();
    } catch (err: any) {
      showError(err.message || `Failed to clear ${mode} fixtures.`);
    } finally {
      setLoading(false);
    }
  };

  const handleResetCeremonialDraw = async () => {
    await handleClearKnockoutFixtures('ALL');
  };

  const handleBatchSetStatus = async (stage: string, statusMode: string) => {
    try {
      setLoading(true);
      const res = await api.adminSetFixturesStatus(stage, statusMode, token);
      showSuccess(res.message || `Fixtures set to ${statusMode}.`);
      await loadData();
    } catch (err: any) {
      showError(err.message || 'Failed to update fixture statuses.');
    } finally {
      setLoading(false);
    }
  };

  const openResultModal = (m: any) => {
    setResultModalSlot(m.bracket_slot);
    setHomeScore(m.home_score ?? 0);
    setAwayScore(m.away_score ?? 0);
    setHomePenalty(m.home_penalty !== null && m.home_penalty !== undefined ? String(m.home_penalty) : '');
    setAwayPenalty(m.away_penalty !== null && m.away_penalty !== undefined ? String(m.away_penalty) : '');
    setWinnerMethod(m.winner_method || 'Regular Time');
    setResultNotes(m.notes || '');
  };

  const submitResult = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!resultModalSlot) return;
    try {
      const payload: any = {
        home_score: homeScore,
        away_score: awayScore,
        winner_method: winnerMethod,
        notes: resultNotes,
      };
      if (homePenalty !== '' && awayPenalty !== '') {
        payload.home_penalty = parseInt(homePenalty, 10);
        payload.away_penalty = parseInt(awayPenalty, 10);
      }
      await api.adminRecordKnockoutResult(resultModalSlot, payload, token);
      showSuccess(`Score recorded for ${resultModalSlot}. Winner advanced to next round!`);
      setResultModalSlot(null);
      await loadData();
    } catch (err: any) {
      showError(err.message || 'Failed to record knockout score.');
    }
  };

  const openWalkoverModal = (m: any) => {
    setWalkoverModalSlot(m.bracket_slot);
    setWalkoverWinnerId(m.home_team_id || null);
    setWalkoverReason('');
  };

  const submitWalkover = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!walkoverModalSlot || !walkoverWinnerId) return;
    if (!walkoverReason || walkoverReason.trim().length < 5) {
      showError('Please provide a documented justification for the walkover.');
      return;
    }
    try {
      await api.adminRecordWalkover(walkoverModalSlot, walkoverWinnerId, walkoverReason, token);
      showSuccess(`Walkover recorded for ${walkoverModalSlot}. 3–0 score and winner recorded.`);
      setWalkoverModalSlot(null);
      await loadData();
    } catch (err: any) {
      showError(err.message || 'Failed to record walkover.');
    }
  };

  const openEditModal = (m: any) => {
    setEditFixtureSlot(m.bracket_slot);
    setEditHomeId(m.home_team_id || '');
    setEditAwayId(m.away_team_id || '');
    setEditDate(m.scheduled_date || '');
    setEditTime(m.scheduled_time || '');
    setEditVenue(m.venue || 'Minaram Stadium');
  };

  const submitEdit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!editFixtureSlot) return;
    try {
      await api.adminEditFixture(
        editFixtureSlot,
        {
          home_team_id: editHomeId !== '' ? Number(editHomeId) : null,
          away_team_id: editAwayId !== '' ? Number(editAwayId) : null,
          scheduled_date: editDate,
          scheduled_time: editTime,
          venue: editVenue,
        },
        token
      );
      showSuccess(`Fixture ${editFixtureSlot} updated successfully.`);
      setEditFixtureSlot(null);
      await loadData();
    } catch (err: any) {
      showError(err.message || 'Failed to edit fixture.');
    }
  };

  const openOverrideModal = (slotIdx: number) => {
    setOverrideSlotIndex(slotIdx);
    setOverrideTeamId('');
    setOverrideReason('');
    setShowOverrideModal(true);
  };

  const submitOverride = async (e: React.FormEvent) => {
    e.preventDefault();
    if (overrideTeamId === '') return;
    try {
      await api.adminOverrideDirectQualifier(overrideSlotIndex, Number(overrideTeamId), overrideReason, token);
      showSuccess(`Direct Qualifier #${overrideSlotIndex + 1} overridden.`);
      setShowOverrideModal(false);
      await loadData();
    } catch (err: any) {
      showError(err.message || 'Failed to override qualifier.');
    }
  };

  const handleClearDirectOverrides = async () => {
    if (!window.confirm('Clear all manual overrides and restore calculated direct qualifiers?')) return;
    try {
      await api.adminClearDirectOverride(token);
      showSuccess('Manual direct qualifier overrides cleared.');
      await loadData();
    } catch (err: any) {
      showError(err.message || 'Failed to clear overrides.');
    }
  };

  const handleOpenAuditLog = async () => {
    try {
      const logs = await api.adminGetKnockoutAuditLog(token);
      setAuditLogs(logs);
      setShowAuditLogs(true);
    } catch (err: any) {
      showError(err.message || 'Failed to fetch audit log.');
    }
  };

  // Flatten all matches for fixture manager table
  // ONLY include matches that are published / official fixtures from the draw!
  const allMatchesList: any[] = [];
  (bracket.rounds || []).forEach((r) => {
    (r.matches || []).forEach((m) => {
      // Must be an officially published fixture in the tournament (not an un-drawn placeholder)
      if (m.is_published || m.is_official || (m.team_a_id && m.team_b_id)) {
        allMatchesList.push({ ...m, round_name: r.round_name });
      }
    });
  });

  const filteredMatches = allMatchesList.filter((m) => {
    if (activeStage !== 'ALL') {
      if (!m.round_name.toLowerCase().includes(activeStage.toLowerCase())) return false;
    }
    if (statusFilter !== 'ALL') {
      if (m.status !== statusFilter) return false;
    }
    return true;
  });

  return (
    <div className="space-y-8 select-none">
      {/* Toast Notifications */}
      {successMessage && (
        <div className="p-3.5 rounded-xl bg-emerald-950/70 border border-emerald-600/70 text-emerald-300 text-xs font-mono flex items-center space-x-2">
          <CheckCircle2 className="w-4 h-4 shrink-0" />
          <span>{successMessage}</span>
        </div>
      )}
      {errorMessage && (
        <div className="p-3.5 rounded-xl bg-rose-950/70 border border-rose-600/70 text-rose-300 text-xs font-mono flex items-center space-x-2">
          <AlertTriangle className="w-4 h-4 shrink-0" />
          <span>{errorMessage}</span>
        </div>
      )}

      {/* Knockout Admin Views Switcher */}
      <div className="flex border-b border-[#222222] mb-6">
        <button
          onClick={() => setAdminSection('fixtures')}
          className={`flex items-center space-x-2 px-5 py-2.5 font-display text-sm tracking-wider transition-colors border-b-2 -mb-px ${
            adminSection === 'fixtures'
              ? 'border-brand-red text-white bg-neutral-900/60'
              : 'border-transparent text-neutral-400 hover:text-white'
          }`}
        >
          <Trophy className="w-4 h-4 text-brand-gold" />
          <span>OFFICIAL FIXTURES & SCORING DESK</span>
        </button>

        <button
          onClick={() => setAdminSection('draw_ceremony')}
          className={`flex items-center space-x-2 px-5 py-2.5 font-display text-sm tracking-wider transition-colors border-b-2 -mb-px ${
            adminSection === 'draw_ceremony'
              ? 'border-brand-gold text-white bg-neutral-900/60'
              : 'border-transparent text-neutral-400 hover:text-white'
          }`}
        >
          <Sparkles className="w-4 h-4 text-brand-gold animate-pulse" />
          <span>UEFA CEREMONIAL DRAW DESK (ADMIN ONLY)</span>
        </button>
      </div>

      {adminSection === 'draw_ceremony' ? (
        <div className="space-y-4">
          <div className="p-3.5 rounded-xl bg-blue-950/40 border border-blue-700/40 text-blue-200 text-xs font-mono flex items-start space-x-2">
            <Shield className="w-4 h-4 text-blue-400 shrink-0 mt-0.5" />
            <div>
              <span className="font-bold text-blue-100 block">ADMIN ONLY — UEFA CEREMONIAL DRAW DESK</span>
              <span className="text-blue-300/70">Complete the ceremonial draw below, then click APPLY TO FIXTURES to sync results live to the public Knockout Bracket. Players do not have access to this draw.</span>
            </div>
          </div>
          <UefaKnockoutDraw
            bracket={bracket}
            token={token}
            isAdmin={true}
            allTeams={allTeams}
            onRefreshBracket={loadData}
          />
        </div>
      ) : (
        <>
          {/* Knockout Master Toolbar */}
          <div className="p-5 rounded-2xl bg-[#121214] border border-neutral-800 shadow-xl flex flex-wrap items-center justify-between gap-4">
        <div>
          <div className="flex items-center space-x-2 text-xs font-mono text-amber-400 uppercase tracking-widest">
            <Trophy className="w-4 h-4" />
            <span>KNOCKOUT CONTROLS</span>
          </div>
          <h2 className="font-display text-2xl text-white tracking-wide mt-1">
            TOURNAMENT MANAGEMENT DESK
          </h2>
        </div>

        <div className="flex flex-wrap items-center gap-2.5">
          {/* Recalculate */}
          <button
            type="button"
            onClick={handleRecalculate}
            disabled={loading}
            className="px-3.5 py-2 rounded-lg bg-neutral-900 hover:bg-neutral-800 text-neutral-200 border border-neutral-700 text-xs font-mono font-bold flex items-center space-x-1.5 cursor-pointer"
          >
            <RefreshCw className={`w-3.5 h-3.5 text-amber-400 ${loading ? 'animate-spin' : ''}`} />
            <span>RECALCULATE</span>
          </button>

          {/* Draw Method Switch */}
          <button
            type="button"
            onClick={handleDrawMethodToggle}
            className="px-3.5 py-2 rounded-lg bg-neutral-900 hover:bg-neutral-800 text-neutral-200 border border-neutral-700 text-xs font-mono font-bold flex items-center space-x-1.5 cursor-pointer"
          >
            <Shuffle className="w-3.5 h-3.5 text-cyan-400" />
            <span>DRAW: {bracket.draw_method?.toUpperCase() || 'SEEDED'}</span>
          </button>

          {/* 3rd Place Toggle */}
          <button
            type="button"
            onClick={handleThirdPlaceToggle}
            className="px-3.5 py-2 rounded-lg bg-neutral-900 hover:bg-neutral-800 text-neutral-200 border border-neutral-700 text-xs font-mono font-bold flex items-center space-x-1.5 cursor-pointer"
          >
            <span>3RD PLACE: {bracket.rules?.third_place_enabled?.toLowerCase() === 'true' ? 'ON' : 'OFF'}</span>
          </button>

          {/* Batch Confirm Preliminary */}
          <button
            type="button"
            onClick={() => handleBatchConfirm('Preliminary Round')}
            className="px-3.5 py-2 rounded-lg bg-cyan-950/60 hover:bg-cyan-900/60 text-cyan-300 border border-cyan-700/60 text-xs font-mono font-bold flex items-center space-x-1.5 cursor-pointer"
            title="Set all preliminary fixtures to CONFIRMED"
          >
            <Shield className="w-3.5 h-3.5" />
            <span>CONFIRM ALL PRELIM</span>
          </button>

          {/* Batch Set Preliminary as Predicted */}
          <button
            type="button"
            onClick={() => handleBatchSetStatus('Preliminary Round', 'PREDICTED')}
            className="px-3.5 py-2 rounded-lg bg-amber-950/50 hover:bg-amber-900/60 text-amber-300 border border-amber-700/60 text-xs font-mono font-bold flex items-center space-x-1.5 cursor-pointer"
            title="Set all preliminary fixtures to PREDICTED (Live Draw)"
          >
            <Sparkles className="w-3.5 h-3.5 text-amber-400" />
            <span>SET PRELIM AS PREDICTED</span>
          </button>

          {/* Clear Fixtures Dropdown */}
          <div className="relative">
            <button
              type="button"
              onClick={() => setShowClearDropdown(!showClearDropdown)}
              className="px-3.5 py-2 rounded-lg bg-red-950/70 hover:bg-red-900/80 text-red-200 border border-red-700 text-xs font-mono font-bold flex items-center space-x-1.5 cursor-pointer shadow-sm"
              title="Clear preliminary knockout fixtures by status (All, Predicted, or Confirmed)"
            >
              <Trash2 className="w-3.5 h-3.5 text-red-400" />
              <span>CLEAR FIXTURES</span>
              <ChevronDown className="w-3 h-3 text-red-300 ml-0.5" />
            </button>

            {showClearDropdown && (
              <div className="absolute right-0 top-full mt-2 w-72 rounded-xl bg-[#101726] border-2 border-red-600/70 shadow-2xl p-2 z-50 space-y-1 animate-scale-in">
                <div className="px-2.5 py-1.5 text-[10px] font-mono text-neutral-400 uppercase tracking-wider border-b border-neutral-800">
                  Select Clear Mode
                </div>
                <button
                  type="button"
                  onClick={() => handleClearKnockoutFixtures('ALL')}
                  className="w-full text-left px-3 py-2 rounded-lg hover:bg-red-950/80 text-xs font-mono text-red-200 hover:text-white transition-colors cursor-pointer flex flex-col"
                >
                  <span className="font-bold flex items-center space-x-1.5">
                    <Trash2 className="w-3 h-3 text-red-400" />
                    <span>Clear All Preliminary Fixtures</span>
                  </span>
                  <span className="text-[10px] text-neutral-400 mt-0.5">Wipes both Predicted & Confirmed preliminary ties</span>
                </button>
                <button
                  type="button"
                  onClick={() => handleClearKnockoutFixtures('PREDICTED')}
                  className="w-full text-left px-3 py-2 rounded-lg hover:bg-amber-950/80 text-xs font-mono text-amber-200 hover:text-white transition-colors cursor-pointer flex flex-col"
                >
                  <span className="font-bold flex items-center space-x-1.5">
                    <Sparkles className="w-3 h-3 text-amber-400" />
                    <span>Clear Predicted Only</span>
                  </span>
                  <span className="text-[10px] text-neutral-400 mt-0.5">Removes unconfirmed live draw fixtures</span>
                </button>
                <button
                  type="button"
                  onClick={() => handleClearKnockoutFixtures('CONFIRMED')}
                  className="w-full text-left px-3 py-2 rounded-lg hover:bg-cyan-950/80 text-xs font-mono text-cyan-200 hover:text-white transition-colors cursor-pointer flex flex-col"
                >
                  <span className="font-bold flex items-center space-x-1.5">
                    <Shield className="w-3 h-3 text-cyan-400" />
                    <span>Clear Confirmed Only</span>
                  </span>
                  <span className="text-[10px] text-neutral-400 mt-0.5">Removes confirmed unplayed fixtures</span>
                </button>
              </div>
            )}
          </div>

          {/* Reset Predictions */}
          <button
            type="button"
            onClick={handleResetPredictions}
            className="px-3.5 py-2 rounded-lg bg-neutral-900 hover:bg-neutral-800 text-neutral-300 border border-neutral-700 text-xs font-mono font-bold flex items-center space-x-1.5 cursor-pointer"
            title="Reset predictions snapshot cache"
          >
            <Trash2 className="w-3.5 h-3.5" />
            <span>RESET PREDICTIONS</span>
          </button>

          {/* Audit Logs */}
          <button
            type="button"
            onClick={handleOpenAuditLog}
            className="px-3.5 py-2 rounded-lg bg-neutral-900 hover:bg-neutral-800 text-neutral-200 border border-neutral-700 text-xs font-mono font-bold flex items-center space-x-1.5 cursor-pointer"
          >
            <FileText className="w-3.5 h-3.5 text-amber-400" />
            <span>AUDIT LOG</span>
          </button>
        </div>
      </div>

      {/* Direct Round of 16 Qualifiers Management */}
      <div className="p-5 rounded-2xl bg-[#121214] border border-neutral-800 shadow-xl space-y-4">
        <div className="flex items-center justify-between border-b border-neutral-800 pb-3">
          <div className="flex items-center space-x-2">
            <Flame className="w-4 h-4 text-amber-400" />
            <h3 className="font-display text-xl text-white tracking-wide uppercase">
              DIRECT ROUND OF 16 QUALIFIERS DESK
            </h3>
          </div>
          {bracket.has_direct_override && (
            <button
              onClick={handleClearDirectOverrides}
              className="text-xs font-mono text-purple-400 hover:underline cursor-pointer"
            >
              Clear Manual Overrides & Restore Recommended
            </button>
          )}
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {(bracket.direct_qualifiers || []).map((dq, idx) => (
            <div
              key={idx}
              className="p-4 rounded-xl bg-black/40 border border-neutral-800 flex items-start justify-between gap-3"
            >
              <div>
                <div className="flex items-center space-x-2 mb-1">
                  <span className="text-[10px] font-mono font-bold px-2 py-0.5 rounded bg-amber-500/20 text-amber-300 border border-amber-500/40">
                    SEED #{idx + 1} ({idx === 0 ? 'Top Half' : 'Bottom Half'})
                  </span>
                  {dq.is_override && (
                    <span className="text-[10px] font-mono text-purple-300 bg-purple-950/80 px-2 py-0.5 rounded border border-purple-800">
                      OVERRIDE ACTIVE
                    </span>
                  )}
                </div>
                <h4 className="font-display text-2xl text-white tracking-wide">{dq.team_name}</h4>
                <div className="text-xs font-mono text-neutral-400 mt-1">
                  {dq.group_name} · GF: {dq.goals_for} · GD: {dq.goal_difference} · PTS: {dq.points}
                </div>
                {dq.override_reason && (
                  <div className="text-[11px] font-mono text-purple-300/90 italic mt-1.5">
                    Reason: {dq.override_reason}
                  </div>
                )}
              </div>

              <button
                type="button"
                onClick={() => openOverrideModal(idx)}
                className="px-3 py-1.5 rounded bg-neutral-900 hover:bg-neutral-800 border border-neutral-700 text-xs font-mono text-neutral-300 hover:text-white shrink-0 cursor-pointer"
              >
                Change Squad
              </button>
            </div>
          ))}
        </div>
      </div>

      {/* Knockout Fixtures Table */}
      <div className="p-5 rounded-2xl bg-[#121214] border border-neutral-800 shadow-xl space-y-4">
        {/* Table Filters */}
        <div className="flex flex-wrap items-center justify-between gap-3 border-b border-neutral-800 pb-3">
          <div className="flex flex-wrap items-center gap-2">
            {['ALL', 'preliminary', '16', 'quarter', 'semi', 'final'].map((stageKey) => (
              <button
                key={stageKey}
                onClick={() => setActiveStage(stageKey)}
                className={`px-3 py-1 rounded-lg text-xs font-mono font-bold tracking-wider uppercase border cursor-pointer ${
                  activeStage === stageKey
                    ? 'bg-amber-500/20 text-amber-300 border-amber-500/60'
                    : 'bg-neutral-900 text-neutral-400 border-neutral-800 hover:text-white'
                }`}
              >
                {stageKey === 'ALL' ? 'All Stages' : stageKey}
              </button>
            ))}
          </div>

          <div className="flex items-center space-x-2 text-xs font-mono">
            <span className="text-neutral-400">Status:</span>
            <select
              value={statusFilter}
              onChange={(e) => setStatusFilter(e.target.value)}
              className="bg-black/60 border border-neutral-800 rounded px-2.5 py-1 text-white focus:outline-none"
            >
              <option value="ALL">All Statuses</option>
              <option value="PREDICTED">PREDICTED</option>
              <option value="CONFIRMED">CONFIRMED</option>
              <option value="LIVE">LIVE</option>
              <option value="COMPLETED">COMPLETED</option>
            </select>
          </div>
        </div>

        {/* Fixtures List */}
        <div className="space-y-3">
          {filteredMatches.length === 0 ? (
            <div className="py-14 text-center space-y-4">
              <div className="w-16 h-16 rounded-full bg-blue-950/60 border border-blue-500/40 text-blue-400 mx-auto flex items-center justify-center shadow-lg shadow-blue-950/40">
                <Trophy className="w-8 h-8 text-brand-gold" />
              </div>
              <div className="space-y-1">
                <h3 className="font-display text-2xl text-white tracking-wide">
                  {allMatchesList.length === 0 ? 'NO KNOCKOUT FIXTURES PUBLISHED YET' : 'NO FIXTURES MATCH FILTER'}
                </h3>
                <p className="text-xs font-mono text-neutral-400 max-w-md mx-auto">
                  {allMatchesList.length === 0
                    ? 'No fixtures have been published to the knockout bracket. Open the UEFA Ceremonial Draw Desk, review the extracted ties, and click "Apply to Fixtures" to move them here.'
                    : `No fixtures found matching Stage: "${activeStage}" and Status: "${statusFilter}".`}
                </p>
              </div>
              {allMatchesList.length === 0 && (
                <button
                  type="button"
                  onClick={() => setAdminSection('draw_ceremony')}
                  className="inline-flex items-center space-x-2 px-5 py-2.5 rounded-xl bg-gradient-to-r from-brand-gold to-amber-600 hover:from-brand-gold-bright hover:to-amber-500 text-black font-mono font-bold text-xs uppercase tracking-wider transition-all cursor-pointer shadow-lg shadow-amber-950/40"
                >
                  <Sparkles className="w-4 h-4" />
                  <span>OPEN UEFA CEREMONIAL DRAW DESK</span>
                </button>
              )}
            </div>
          ) : (
            filteredMatches.map((m) => (
              <div
                key={m.bracket_slot}
              className="p-3.5 rounded-xl bg-black/40 border border-neutral-800/90 flex flex-col md:flex-row md:items-center justify-between gap-4"
            >
              {/* Fixture Identifiers & Teams */}
              <div className="flex items-start sm:items-center space-x-3 min-w-[280px]">
                <span className="px-2 py-1 rounded bg-neutral-900 border border-neutral-800 text-xs font-mono font-bold text-amber-300 shrink-0">
                  {m.bracket_slot}
                </span>
                <div>
                  <div className="text-xs font-mono text-neutral-400 uppercase tracking-widest text-[10px]">
                    {m.round_name} {m.match_number ? `· M#${m.match_number}` : ''}
                  </div>
                  <div className="font-display text-lg text-white tracking-wide mt-0.5">
                    <span className={m.team_a_name?.includes('Winner') ? 'text-neutral-400 italic font-mono text-sm' : ''}>
                      {m.team_a_name || 'TBD'}
                    </span>{' '}
                    <span className="text-neutral-500 font-mono text-sm mx-1">vs</span>{' '}
                    <span className={m.team_b_name?.includes('Winner') ? 'text-neutral-400 italic font-mono text-sm' : ''}>
                      {m.team_b_name || 'TBD'}
                    </span>
                  </div>
                </div>
              </div>

              {/* Status and Score */}
              <div className="flex items-center space-x-4">
                <span
                  className={`text-[10px] font-mono font-bold px-2 py-0.5 rounded border uppercase ${
                    m.status === 'COMPLETED'
                      ? 'bg-emerald-950/80 text-emerald-300 border-emerald-700/60'
                      : m.status === 'CONFIRMED'
                      ? 'bg-cyan-950/80 text-cyan-300 border-cyan-700/60'
                      : m.status === 'LIVE'
                      ? 'bg-rose-950/90 text-rose-300 border-rose-600 animate-pulse'
                      : 'bg-amber-950/40 text-amber-300 border-amber-600/50'
                  }`}
                >
                  {m.status}
                </span>

                <div className="text-base font-mono font-bold text-white tabular-nums min-w-[50px] text-center">
                  {m.status === 'COMPLETED' && m.home_score !== null ? `${m.home_score} – ${m.away_score}` : '—'}
                </div>
              </div>

              {/* Action Buttons */}
              <div className="flex flex-wrap items-center gap-2 shrink-0">
                {m.status === 'PREDICTED' || m.status === 'LIVE_DRAW' ? (
                  <button
                    onClick={() => handleConfirmSingle(m.bracket_slot)}
                    className="px-2.5 py-1.5 rounded bg-cyan-950/60 hover:bg-cyan-900/60 border border-cyan-700 text-cyan-300 text-xs font-mono font-bold cursor-pointer"
                    title="Promote fixture to CONFIRMED"
                  >
                    Confirm
                  </button>
                ) : (
                  m.status !== 'COMPLETED' && (
                    <button
                      onClick={() => handleUnconfirmSingle(m.bracket_slot)}
                      className="px-2.5 py-1.5 rounded bg-amber-950/50 hover:bg-amber-900/60 border border-amber-700 text-amber-300 text-xs font-mono font-bold cursor-pointer"
                      title="Set fixture status to PREDICTED (Live Draw)"
                    >
                      Set Predicted
                    </button>
                  )
                )}

                <button
                  onClick={() => openEditModal(m)}
                  className="px-2.5 py-1.5 rounded bg-neutral-900 hover:bg-neutral-800 border border-neutral-700 text-neutral-300 text-xs font-mono flex items-center space-x-1 cursor-pointer"
                >
                  <Edit className="w-3 h-3" />
                  <span>Edit</span>
                </button>

                <button
                  onClick={() => openResultModal(m)}
                  className="px-2.5 py-1.5 rounded bg-brand-red hover:bg-brand-red-bright text-white text-xs font-mono font-bold flex items-center space-x-1 cursor-pointer"
                >
                  <Save className="w-3 h-3" />
                  <span>Score</span>
                </button>

                <button
                  onClick={() => openWalkoverModal(m)}
                  className="px-2.5 py-1.5 rounded bg-neutral-900 hover:bg-neutral-800 border border-neutral-700 text-amber-400 text-xs font-mono cursor-pointer"
                >
                  Walkover
                </button>
              </div>
            </div>
          )))}
        </div>
      </div>
      </>
      )}

      {/* MODAL 1: RECORD SCORE & CONFIRM RESULT */}
      {resultModalSlot && (
        <div className="fixed inset-0 z-50 bg-black/80 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="w-full max-w-lg bg-[#141417] border border-neutral-800 rounded-2xl p-6 shadow-2xl">
            <div className="flex items-center justify-between pb-4 mb-4 border-b border-neutral-800">
              <h3 className="font-display text-2xl text-white tracking-wide">
                RECORD SCORE & ADVANCE: {resultModalSlot}
              </h3>
              <button onClick={() => setResultModalSlot(null)} className="text-neutral-400 hover:text-white">
                <X className="w-5 h-5" />
              </button>
            </div>

            <form onSubmit={submitResult} className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-xs font-mono text-neutral-400 mb-1">Home Score</label>
                  <input
                    type="number"
                    min="0"
                    value={homeScore}
                    onChange={(e) => setHomeScore(parseInt(e.target.value, 10) || 0)}
                    required
                    className="w-full px-3 py-2 bg-black/60 border border-neutral-700 rounded text-base font-mono text-white focus:outline-none focus:border-brand-red"
                  />
                </div>
                <div>
                  <label className="block text-xs font-mono text-neutral-400 mb-1">Away Score</label>
                  <input
                    type="number"
                    min="0"
                    value={awayScore}
                    onChange={(e) => setAwayScore(parseInt(e.target.value, 10) || 0)}
                    required
                    className="w-full px-3 py-2 bg-black/60 border border-neutral-700 rounded text-base font-mono text-white focus:outline-none focus:border-brand-red"
                  />
                </div>
              </div>

              {/* Penalties (Mandatory if drawn) */}
              <div className="p-3.5 rounded-xl bg-black/50 border border-neutral-800 space-y-2.5">
                <span className="text-[11px] font-mono text-amber-400 font-bold uppercase block">
                  Penalties Shootout (Required if Regular Score is Tied)
                </span>
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="block text-[10px] font-mono text-neutral-400 mb-1">Home Penalties</label>
                    <input
                      type="number"
                      min="0"
                      value={homePenalty}
                      onChange={(e) => setHomePenalty(e.target.value)}
                      placeholder="e.g. 5"
                      className="w-full px-3 py-1.5 bg-neutral-900 border border-neutral-700 rounded text-xs font-mono text-white"
                    />
                  </div>
                  <div>
                    <label className="block text-[10px] font-mono text-neutral-400 mb-1">Away Penalties</label>
                    <input
                      type="number"
                      min="0"
                      value={awayPenalty}
                      onChange={(e) => setAwayPenalty(e.target.value)}
                      placeholder="e.g. 4"
                      className="w-full px-3 py-1.5 bg-neutral-900 border border-neutral-700 rounded text-xs font-mono text-white"
                    />
                  </div>
                </div>
              </div>

              <div>
                <label className="block text-xs font-mono text-neutral-400 mb-1">Winner Determination Method</label>
                <select
                  value={winnerMethod}
                  onChange={(e) => setWinnerMethod(e.target.value)}
                  className="w-full px-3 py-2 bg-black/60 border border-neutral-700 rounded text-xs font-mono text-white"
                >
                  <option value="Regular Time">Regular Time</option>
                  <option value="Extra Time">Extra Time</option>
                  <option value="Penalties">Penalties Shootout</option>
                </select>
              </div>

              <div>
                <label className="block text-xs font-mono text-neutral-400 mb-1">Match Official Notes</label>
                <input
                  type="text"
                  value={resultNotes}
                  onChange={(e) => setResultNotes(e.target.value)}
                  placeholder="Optional match official remarks"
                  className="w-full px-3 py-2 bg-black/60 border border-neutral-700 rounded text-xs font-mono text-white"
                />
              </div>

              <div className="flex items-center justify-end space-x-3 pt-2">
                <button
                  type="button"
                  onClick={() => setResultModalSlot(null)}
                  className="px-4 py-2 bg-neutral-900 text-neutral-400 hover:text-white rounded text-xs font-mono"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="px-5 py-2 bg-brand-red hover:bg-brand-red-bright text-white font-mono text-xs font-bold rounded"
                >
                  Confirm Result & Advance Winner
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* MODAL 2: ABRUPT WALKOVER AWARD */}
      {walkoverModalSlot && (
        <div className="fixed inset-0 z-50 bg-black/80 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="w-full max-w-lg bg-[#141417] border border-amber-600/60 rounded-2xl p-6 shadow-2xl">
            <div className="flex items-center justify-between pb-4 mb-4 border-b border-neutral-800">
              <h3 className="font-display text-2xl text-amber-300 tracking-wide">
                AWARD WALKOVER: {walkoverModalSlot}
              </h3>
              <button onClick={() => setWalkoverModalSlot(null)} className="text-neutral-400 hover:text-white">
                <X className="w-5 h-5" />
              </button>
            </div>

            <form onSubmit={submitWalkover} className="space-y-4">
              <p className="text-xs font-mono text-neutral-300">
                A 3–0 walkover scoreline will be officially recorded in accordance with tournament rules. Documented desk authorization is required.
              </p>

              <div>
                <label className="block text-xs font-mono text-neutral-400 mb-1">Select Awarded Winner</label>
                <select
                  value={walkoverWinnerId || ''}
                  onChange={(e) => setWalkoverWinnerId(Number(e.target.value))}
                  required
                  className="w-full px-3 py-2 bg-black/60 border border-neutral-700 rounded text-xs font-mono text-white"
                >
                  {allTeams.map((t) => (
                    <option key={t.id} value={t.id}>
                      {t.name} (ID: #{t.id})
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-xs font-mono text-neutral-400 mb-1">
                  Mandatory Policy Justification / Rule Reason
                </label>
                <textarea
                  value={walkoverReason}
                  onChange={(e) => setWalkoverReason(e.target.value)}
                  placeholder="e.g. Rule 9.6: Opponent failed to check in to match lobby within 15-minute grace window."
                  required
                  rows={3}
                  className="w-full px-3 py-2 bg-black/60 border border-neutral-700 rounded text-xs font-mono text-white focus:outline-none focus:border-amber-500"
                />
              </div>

              <div className="flex items-center justify-end space-x-3 pt-2">
                <button
                  type="button"
                  onClick={() => setWalkoverModalSlot(null)}
                  className="px-4 py-2 bg-neutral-900 text-neutral-400 hover:text-white rounded text-xs font-mono"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="px-5 py-2 bg-amber-600 hover:bg-amber-500 text-white font-mono text-xs font-bold rounded"
                >
                  Officially Confirm Walkover
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* MODAL 3: EDIT FIXTURE */}
      {editFixtureSlot && (
        <div className="fixed inset-0 z-50 bg-black/80 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="w-full max-w-lg bg-[#141417] border border-neutral-800 rounded-2xl p-6 shadow-2xl">
            <div className="flex items-center justify-between pb-4 mb-4 border-b border-neutral-800">
              <h3 className="font-display text-2xl text-white tracking-wide">
                EDIT FIXTURE: {editFixtureSlot}
              </h3>
              <button onClick={() => setEditFixtureSlot(null)} className="text-neutral-400 hover:text-white">
                <X className="w-5 h-5" />
              </button>
            </div>

            <form onSubmit={submitEdit} className="space-y-4">
              <div>
                <label className="block text-xs font-mono text-neutral-400 mb-1">Home Squad</label>
                <select
                  value={editHomeId}
                  onChange={(e) => setEditHomeId(e.target.value === '' ? '' : Number(e.target.value))}
                  className="w-full px-3 py-2 bg-black/60 border border-neutral-700 rounded text-xs font-mono text-white"
                >
                  <option value="">Unassigned / Placeholder</option>
                  {allTeams.map((t) => (
                    <option key={t.id} value={t.id}>
                      {t.name}
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-xs font-mono text-neutral-400 mb-1">Away Squad</label>
                <select
                  value={editAwayId}
                  onChange={(e) => setEditAwayId(e.target.value === '' ? '' : Number(e.target.value))}
                  className="w-full px-3 py-2 bg-black/60 border border-neutral-700 rounded text-xs font-mono text-white"
                >
                  <option value="">Unassigned / Placeholder</option>
                  {allTeams.map((t) => (
                    <option key={t.id} value={t.id}>
                      {t.name}
                    </option>
                  ))}
                </select>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-xs font-mono text-neutral-400 mb-1">Date</label>
                  <input
                    type="date"
                    value={editDate}
                    onChange={(e) => setEditDate(e.target.value)}
                    className="w-full px-3 py-2 bg-black/60 border border-neutral-700 rounded text-xs font-mono text-white"
                  />
                </div>
                <div>
                  <label className="block text-xs font-mono text-neutral-400 mb-1">Time</label>
                  <input
                    type="text"
                    value={editTime}
                    onChange={(e) => setEditTime(e.target.value)}
                    placeholder="e.g. 17:00"
                    className="w-full px-3 py-2 bg-black/60 border border-neutral-700 rounded text-xs font-mono text-white"
                  />
                </div>
              </div>

              <div>
                <label className="block text-xs font-mono text-neutral-400 mb-1">Venue / Pitch</label>
                <input
                  type="text"
                  value={editVenue}
                  onChange={(e) => setEditVenue(e.target.value)}
                  className="w-full px-3 py-2 bg-black/60 border border-neutral-700 rounded text-xs font-mono text-white"
                />
              </div>

              <div className="flex items-center justify-end space-x-3 pt-2">
                <button
                  type="button"
                  onClick={() => setEditFixtureSlot(null)}
                  className="px-4 py-2 bg-neutral-900 text-neutral-400 hover:text-white rounded text-xs font-mono"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="px-5 py-2 bg-cyan-700 hover:bg-cyan-600 text-white font-mono text-xs font-bold rounded"
                >
                  Save Fixture
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* MODAL 4: DIRECT QUALIFIER MANUAL OVERRIDE */}
      {showOverrideModal && (
        <div className="fixed inset-0 z-50 bg-black/80 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="w-full max-w-lg bg-[#141417] border border-purple-800/80 rounded-2xl p-6 shadow-2xl">
            <div className="flex items-center justify-between pb-4 mb-4 border-b border-neutral-800">
              <h3 className="font-display text-2xl text-purple-300 tracking-wide">
                OVERRIDE DIRECT QUALIFIER #{overrideSlotIndex + 1}
              </h3>
              <button onClick={() => setShowOverrideModal(false)} className="text-neutral-400 hover:text-white">
                <X className="w-5 h-5" />
              </button>
            </div>

            <form onSubmit={submitOverride} className="space-y-4">
              <p className="text-xs font-mono text-neutral-300">
                Assign a specific squad directly into Round of 16 Seed #{overrideSlotIndex + 1}. The automatically calculated recommendation will be preserved separately.
              </p>

              <div>
                <label className="block text-xs font-mono text-neutral-400 mb-1">Select Squad</label>
                <select
                  value={overrideTeamId}
                  onChange={(e) => setOverrideTeamId(e.target.value === '' ? '' : Number(e.target.value))}
                  required
                  className="w-full px-3 py-2 bg-black/60 border border-neutral-700 rounded text-xs font-mono text-white"
                >
                  <option value="">Select a squad...</option>
                  {allTeams.map((t) => (
                    <option key={t.id} value={t.id}>
                      {t.name}
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-xs font-mono text-neutral-400 mb-1">Administrative Reason</label>
                <textarea
                  value={overrideReason}
                  onChange={(e) => setOverrideReason(e.target.value)}
                  placeholder="Document ruling rationale..."
                  required
                  rows={3}
                  className="w-full px-3 py-2 bg-black/60 border border-neutral-700 rounded text-xs font-mono text-white focus:outline-none focus:border-purple-500"
                />
              </div>

              <div className="flex items-center justify-end space-x-3 pt-2">
                <button
                  type="button"
                  onClick={() => setShowOverrideModal(false)}
                  className="px-4 py-2 bg-neutral-900 text-neutral-400 hover:text-white rounded text-xs font-mono"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="px-5 py-2 bg-purple-700 hover:bg-purple-600 text-white font-mono text-xs font-bold rounded"
                >
                  Apply Override
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* MODAL 5: AUDIT LOG VIEWER */}
      {showAuditLogs && (
        <div className="fixed inset-0 z-50 bg-black/80 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="w-full max-w-3xl max-h-[85vh] bg-[#141417] border border-neutral-800 rounded-2xl p-6 shadow-2xl flex flex-col">
            <div className="flex items-center justify-between pb-4 mb-4 border-b border-neutral-800 shrink-0">
              <div className="flex items-center space-x-2">
                <FileText className="w-5 h-5 text-amber-400" />
                <h3 className="font-display text-2xl text-white tracking-wide">
                  KNOCKOUT ADMINISTRATIVE AUDIT TRAIL
                </h3>
              </div>
              <button onClick={() => setShowAuditLogs(false)} className="text-neutral-400 hover:text-white">
                <X className="w-5 h-5" />
              </button>
            </div>

            <div className="overflow-y-auto flex-grow space-y-2.5 pr-2">
              {auditLogs.length > 0 ? (
                auditLogs.map((log) => (
                  <div key={log.id} className="p-3 rounded-lg bg-black/50 border border-neutral-800/80 text-xs font-mono">
                    <div className="flex items-center justify-between text-neutral-400 mb-1 text-[11px]">
                      <span className="text-amber-400 font-bold">{log.action}</span>
                      <span>{log.timestamp} · by {log.admin_username}</span>
                    </div>
                    <div className="text-neutral-200">
                      Entity: <span className="text-cyan-300 font-bold">{log.entity_id || log.entity_type}</span>
                    </div>
                    {log.new_value && (
                      <div className="text-neutral-300 mt-0.5 truncate">
                        Details: {log.new_value}
                      </div>
                    )}
                    {log.reason && (
                      <div className="text-neutral-400 italic mt-0.5">
                        Reason: {log.reason}
                      </div>
                    )}
                  </div>
                ))
              ) : (
                <div className="text-center py-8 text-neutral-500 font-mono text-xs">
                  No administrative audit records found.
                </div>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

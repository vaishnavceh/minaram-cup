import React, { useState, useEffect } from 'react';
import { api } from '../api';
import { PublicMatch } from '../types';
import { Lock, LogOut, CheckCircle, RefreshCw, AlertCircle, Trophy, Save, Shield, Tv } from 'lucide-react';
import { AdminKnockoutManager } from '../components/AdminKnockoutManager';
import { AdminLiveStreamManager } from '../components/AdminLiveStreamManager';

export const AdminPage: React.FC = () => {
  const [token, setToken] = useState<string | null>(localStorage.getItem('minaram_admin_token'));
  const [username, setUsername] = useState('admin');
  const [password, setPassword] = useState('');
  const [loginError, setLoginError] = useState('');
  const [loading, setLoading] = useState(false);
  const [activeTab, setActiveTab] = useState<'knockout' | 'matches' | 'livestream'>('knockout');

  // Admin Dashboard State
  const [tournament, setTournament] = useState<any>(null);
  const [matches, setMatches] = useState<PublicMatch[]>([]);
  const [selectedMatchId, setSelectedMatchId] = useState<number | null>(null);
  const [teamAScore, setTeamAScore] = useState<number>(0);
  const [teamBScore, setTeamBScore] = useState<number>(0);
  const [penaltyA, setPenaltyA] = useState<string>('');
  const [penaltyB, setPenaltyB] = useState<string>('');
  const [matchStatus, setMatchStatus] = useState<string>('Completed');
  const [walkoverWinnerId, setWalkoverWinnerId] = useState<number | null>(null);
  const [notes, setNotes] = useState<string>('');
  const [actionSuccess, setActionSuccess] = useState<string>('');
  const [actionError, setActionError] = useState<string>('');

  const loadMatches = async () => {
    try {
      const [tData, data] = await Promise.all([
        api.getTournament(),
        api.getFixtures(),
      ]);
      setTournament(tData);
      setMatches(data);
      if (data.length > 0 && !selectedMatchId) {
        setSelectedMatchId(data[0].id);
        setTeamAScore(data[0].team_a_score ?? 0);
        setTeamBScore(data[0].team_b_score ?? 0);
        setMatchStatus(data[0].raw_status === 'Walkover' ? 'Walkover' : 'Completed');
        setWalkoverWinnerId(data[0].winner_id ?? null);
        setNotes(data[0].notes || '');
      }
    } catch (err) {
      console.error('Failed to load matches for admin', err);
    }
  };

  useEffect(() => {
    if (token) {
      loadMatches();
    }
  }, [token]);

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoginError('');
    setLoading(true);
    try {
      const params = new URLSearchParams();
      params.append('username', username);
      params.append('password', password);
      const res = await api.adminLogin(params);
      localStorage.setItem('minaram_admin_token', res.access_token);
      setToken(res.access_token);
    } catch (err: any) {
      setLoginError(err.message || 'Invalid credentials');
    } finally {
      setLoading(false);
    }
  };

  const handleLogout = () => {
    localStorage.removeItem('minaram_admin_token');
    setToken(null);
  };

  const selectedMatch = matches.find((m) => m.id === selectedMatchId);

  const handleSelectMatch = (mId: number) => {
    setSelectedMatchId(mId);
    const m = matches.find((match) => match.id === mId);
    if (m) {
      setTeamAScore(m.team_a_score ?? 0);
      setTeamBScore(m.team_b_score ?? 0);
      setPenaltyA(m.penalty_a !== null ? String(m.penalty_a) : '');
      setPenaltyB(m.penalty_b !== null ? String(m.penalty_b) : '');
      setMatchStatus(m.raw_status === 'Walkover' ? 'Walkover' : 'Completed');
      setWalkoverWinnerId(m.winner_id ?? null);
      setNotes(m.notes || '');
    }
    setActionSuccess('');
    setActionError('');
  };

  const applyRule2Walkover = (awardedTo: 'A' | 'B') => {
    if (!selectedMatch) return;
    if (awardedTo === 'A') {
      setTeamAScore(3);
      setTeamBScore(0);
      setMatchStatus('Walkover');
      setWalkoverWinnerId(selectedMatch.team_a_id ?? null);
      setNotes(`Rule 2 Walkover: 3–0 awarded to ${selectedMatch.team_a_name || 'Team A'} (opponent failed to play within deadline)`);
    } else {
      setTeamAScore(0);
      setTeamBScore(3);
      setMatchStatus('Walkover');
      setWalkoverWinnerId(selectedMatch.team_b_id ?? null);
      setNotes(`Rule 2 Walkover: 3–0 awarded to ${selectedMatch.team_b_name || 'Team B'} (opponent failed to play within deadline)`);
    }
  };

  const applyRule3BothFailed = () => {
    if (!selectedMatch) return;
    setTeamAScore(0);
    setTeamBScore(0);
    setMatchStatus('Completed');
    setWalkoverWinnerId(null);
    setNotes('Rule 3: Both teams failed to play within given deadline (0–0 recorded, 1 point awarded to each team)');
  };

  const handleRecordResult = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!token || !selectedMatchId) return;
    setActionError('');
    setActionSuccess('');
    setLoading(true);
    try {
      const payload: any = {
        team_a_score: teamAScore,
        team_b_score: teamBScore,
        status: matchStatus,
        walkover_winner_id: matchStatus === 'Walkover' ? walkoverWinnerId : null,
        notes: notes,
      };
      if (penaltyA !== '' && penaltyB !== '') {
        payload.penalty_a = parseInt(penaltyA, 10);
        payload.penalty_b = parseInt(penaltyB, 10);
      }
      await api.adminRecordResult(selectedMatchId, payload, token);
      setActionSuccess(`Match #${selectedMatchId} result recorded successfully! Broadcast sent to live feed.`);
      await loadMatches();
    } catch (err: any) {
      setActionError(err.message || 'Failed to record result');
    } finally {
      setLoading(false);
    }
  };

  const handleResetResult = async () => {
    if (!token || !selectedMatchId) return;
    if (!window.confirm('Reset this match to scheduled?')) return;
    setActionError('');
    setActionSuccess('');
    setLoading(true);
    try {
      await api.adminResetResult(selectedMatchId, token);
      setActionSuccess(`Match #${selectedMatchId} result reset to SCHEDULED.`);
      await loadMatches();
    } catch (err: any) {
      setActionError(err.message || 'Failed to reset match');
    } finally {
      setLoading(false);
    }
  };

  const handleAdvanceStage = async () => {
    if (!token) return;
    if (!window.confirm('Advance tournament to next stage? If Group Stage is completed, Round of 16 (RO16) knockouts will be generated.')) return;
    setActionError('');
    setActionSuccess('');
    setLoading(true);
    try {
      const res = await api.adminAdvanceStage(token);
      setActionSuccess(res.message || 'Tournament stage advanced successfully!');
      await loadMatches();
    } catch (err: any) {
      setActionError(err.message || 'Failed to advance stage');
    } finally {
      setLoading(false);
    }
  };

  // If not authenticated, show Login Dialog
  if (!token) {
    return (
      <div className="min-h-[75vh] flex items-center justify-center px-4">
        <div className="w-full max-w-md bg-[#121212] border border-[#222222] rounded-xl p-8 shadow-2xl">
          <div className="flex items-center space-x-3 mb-6">
            <div className="w-10 h-10 rounded-full bg-brand-red/20 border border-brand-red flex items-center justify-center text-brand-red">
              <Lock className="w-5 h-5" />
            </div>
            <div>
              <h2 className="font-display text-2xl text-white tracking-wide">ADMIN PORTAL</h2>
              <span className="text-[11px] font-mono text-neutral-400 uppercase tracking-widest">
                Minaram Cup Officials
              </span>
            </div>
          </div>

          {loginError && (
            <div className="mb-4 p-3 rounded bg-rose-950/40 border border-rose-800 text-xs font-mono text-rose-300 flex items-center space-x-2">
              <AlertCircle className="w-4 h-4 shrink-0" />
              <span>{loginError}</span>
            </div>
          )}

          <form onSubmit={handleLogin} className="space-y-4">
            <div>
              <label className="block text-xs font-mono text-neutral-400 uppercase mb-1">
                Admin Username
              </label>
              <input
                type="text"
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                required
                className="w-full px-3 py-2 bg-black/60 border border-neutral-800 rounded text-sm text-white focus:outline-none focus:border-brand-red font-mono"
              />
            </div>

            <div>
              <label className="block text-xs font-mono text-neutral-400 uppercase mb-1">
                Password
              </label>
              <input
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="••••••••"
                required
                className="w-full px-3 py-2 bg-black/60 border border-neutral-800 rounded text-sm text-white focus:outline-none focus:border-brand-red font-mono"
              />
            </div>

            <button
              type="submit"
              disabled={loading}
              className="w-full py-2.5 rounded bg-brand-red hover:bg-brand-red-bright text-white font-display text-base tracking-wider uppercase transition-colors shadow-glow-red mt-2"
            >
              {loading ? 'AUTHENTICATING...' : 'SIGN IN'}
            </button>
          </form>

          <p className="mt-6 text-[11px] font-mono text-neutral-400 text-center">
            Authorized tournament desk administrators only.
          </p>
        </div>
      </div>
    );
  }

  // Admin Dashboard
  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
      {/* Admin Top Bar */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between pb-6 border-b border-[#222222] mb-8 gap-4">
        <div>
          <span className="text-xs font-mono text-emerald-400 tracking-widest uppercase">
            AUTHENTICATED SESSION
          </span>
          <h1 className="font-display text-4xl text-white tracking-wider">
            ADMINISTRATOR CONTROLS
          </h1>
        </div>

        <div className="flex items-center space-x-3">
          <button
            onClick={handleAdvanceStage}
            className="px-4 py-2 bg-neutral-900 border border-neutral-700 hover:border-brand-gold text-xs font-mono text-brand-gold rounded transition-colors flex items-center space-x-1.5"
          >
            <Trophy className="w-3.5 h-3.5" />
            <span>ADVANCE STAGE</span>
          </button>
          <button
            onClick={handleLogout}
            className="px-4 py-2 bg-neutral-900 border border-neutral-700 hover:border-neutral-500 text-xs font-mono text-neutral-300 rounded transition-colors flex items-center space-x-1.5"
          >
            <LogOut className="w-3.5 h-3.5" />
            <span>LOGOUT</span>
          </button>
        </div>
      </div>

      {/* Live Tournament Overview Strip */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 mb-8">
        <div className="bg-[#121212] border border-[#222222] p-4 rounded-lg">
          <span className="text-[11px] font-mono text-neutral-400 uppercase tracking-widest block">
            Teams Registered
          </span>
          <span className="font-display text-3xl text-white mt-1 block">
            {tournament?.team_count ?? 21}
          </span>
          <span className="text-[10px] font-mono text-emerald-400 mt-0.5 block flex items-center">
            <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse inline-block mr-1" />
            Confirmed Squads
          </span>
        </div>
        <div className="bg-[#121212] border border-[#222222] p-4 rounded-lg">
          <span className="text-[11px] font-mono text-neutral-400 uppercase tracking-widest block">
            Groups Active
          </span>
          <span className="font-display text-3xl text-brand-red mt-1 block">
            {tournament?.groups_count ?? 6}
          </span>
          <span className="text-[10px] font-mono text-neutral-400 mt-0.5 block">
            Max 4 Teams / Group
          </span>
        </div>
        <div className="bg-[#121212] border border-[#222222] p-4 rounded-lg">
          <span className="text-[11px] font-mono text-neutral-400 uppercase tracking-widest block">
            Total Matches
          </span>
          <span className="font-display text-3xl text-white mt-1 block">
            {matches.length}
          </span>
          <span className="text-[10px] font-mono text-neutral-400 mt-0.5 block">
            {matches.filter((m) => m.status === 'COMPLETED').length} Finished
          </span>
        </div>
        <div className="bg-[#121212] border border-[#222222] p-4 rounded-lg">
          <span className="text-[11px] font-mono text-neutral-400 uppercase tracking-widest block">
            Sync Status
          </span>
          <span className="font-display text-xl sm:text-2xl text-emerald-400 mt-1 block">
            ONLINE
          </span>
          <span className="text-[10px] font-mono text-emerald-400 mt-0.5 block">
            SSE Live Stream Connected
          </span>
        </div>
      </div>

      {/* Admin Tabs */}
      <div className="flex border-b border-[#222222] mb-8">
        <button
          onClick={() => setActiveTab('knockout')}
          className={`flex items-center space-x-2 px-6 py-3 font-display text-base tracking-wider transition-colors border-b-2 -mb-px ${
            activeTab === 'knockout'
              ? 'border-brand-red text-white bg-neutral-900/60'
              : 'border-transparent text-neutral-400 hover:text-neutral-200'
          }`}
        >
          <Trophy className="w-4 h-4 text-brand-gold" />
          <span>LIVE KNOCKOUT MANAGEMENT</span>
        </button>
        <button
          onClick={() => setActiveTab('matches')}
          className={`flex items-center space-x-2 px-6 py-3 font-display text-base tracking-wider transition-colors border-b-2 -mb-px ${
            activeTab === 'matches'
              ? 'border-brand-red text-white bg-neutral-900/60'
              : 'border-transparent text-neutral-400 hover:text-neutral-200'
          }`}
        >
          <Shield className="w-4 h-4 text-neutral-400" />
          <span>GROUP MATCH SCORING</span>
        </button>
        <button
          onClick={() => setActiveTab('livestream')}
          className={`flex items-center space-x-2 px-6 py-3 font-display text-base tracking-wider transition-colors border-b-2 -mb-px ${
            activeTab === 'livestream'
              ? 'border-brand-red text-white bg-neutral-900/60'
              : 'border-transparent text-neutral-400 hover:text-neutral-200'
          }`}
        >
          <Tv className="w-4 h-4 text-brand-red" />
          <span>LIVE STREAM SETTINGS</span>
        </button>
      </div>

      {activeTab === 'knockout' ? (
        <AdminKnockoutManager token={token} onRefreshParent={loadMatches} />
      ) : activeTab === 'livestream' ? (
        <AdminLiveStreamManager token={token} />
      ) : (
        <>
          {/* Notifications */}
          {actionSuccess && (
            <div className="mb-6 p-4 rounded-lg bg-emerald-950/40 border border-emerald-800 text-xs font-mono text-emerald-300 flex items-center space-x-2">
              <CheckCircle className="w-4 h-4 shrink-0" />
              <span>{actionSuccess}</span>
            </div>
          )}
          {actionError && (
            <div className="mb-6 p-4 rounded-lg bg-rose-950/40 border border-rose-800 text-xs font-mono text-rose-300 flex items-center space-x-2">
              <AlertCircle className="w-4 h-4 shrink-0" />
              <span>{actionError}</span>
            </div>
          )}

          {/* Match Management Form */}
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* Match Selector List */}
        <div className="bg-[#121212] border border-[#222222] rounded-lg p-4 max-h-[600px] overflow-y-auto">
          <h3 className="font-display text-lg text-white mb-3">SELECT MATCH</h3>
          <div className="space-y-2">
            {matches.map((m) => {
              const selected = m.id === selectedMatchId;
              return (
                <button
                  key={m.id}
                  onClick={() => handleSelectMatch(m.id)}
                  className={`w-full text-left p-2.5 rounded text-xs font-mono transition-colors border ${
                    selected
                      ? 'bg-neutral-800 border-brand-red text-white'
                      : 'bg-black/40 border-neutral-800 text-neutral-400 hover:text-white'
                  }`}
                >
                  <div className="flex justify-between items-center mb-1">
                    <span className="font-bold text-[10px] text-neutral-400">{m.stage}</span>
                    <span className={m.status === 'COMPLETED' ? 'text-emerald-400' : 'text-neutral-400'}>
                      {m.status}
                    </span>
                  </div>
                  <div className="truncate font-semibold text-white">
                    {m.team_a_name || 'TBD'} vs {m.team_b_name || 'TBD'}
                  </div>
                  {m.status === 'COMPLETED' && (
                    <div className="text-[10px] text-neutral-400 mt-0.5">
                      Score: {m.team_a_score} - {m.team_b_score}
                    </div>
                  )}
                </button>
              );
            })}
          </div>
        </div>

        {/* Score Recording Form */}
        <div className="lg:col-span-2 bg-[#121212] border border-[#222222] rounded-lg p-6 sm:p-8">
          {selectedMatch ? (
            <form onSubmit={handleRecordResult} className="space-y-6">
              <div className="pb-4 border-b border-[#222222]">
                <span className="text-xs font-mono text-brand-red uppercase font-bold">
                  MATCH #{selectedMatch.match_number || selectedMatch.id} · {selectedMatch.stage}
                </span>
                <h2 className="font-display text-3xl text-white mt-1">
                  {selectedMatch.team_a_name || 'TBD'} vs {selectedMatch.team_b_name || 'TBD'}
                </h2>
                <div className="text-xs font-mono text-neutral-400 mt-1">
                  Status: <strong className="text-white">{selectedMatch.status}</strong>
                </div>
              </div>

              {/* Fixture Rules Presets */}
              <div className="p-3 bg-black/60 rounded-lg border border-neutral-800 space-y-2">
                <div className="flex items-center justify-between">
                  <span className="text-[11px] font-mono text-neutral-400 uppercase font-semibold flex items-center gap-1.5">
                    <Shield className="w-3.5 h-3.5 text-brand-red" />
                    Fixture Rules Quick Actions (Walkovers & Forfeits)
                  </span>
                  <span className="text-[10px] font-mono text-neutral-500">
                    Auto-populates scores & audit note
                  </span>
                </div>
                <div className="grid grid-cols-1 sm:grid-cols-3 gap-2">
                  <button
                    type="button"
                    onClick={() => applyRule2Walkover('A')}
                    className="p-2.5 text-left bg-neutral-900/80 hover:bg-neutral-800 border border-neutral-700/60 rounded text-xs transition-colors"
                  >
                    <span className="text-brand-red font-mono font-bold block text-[10px]">
                      RULE 2: WALKOVER
                    </span>
                    <span className="text-white font-medium truncate block">
                      3–0 to {selectedMatch.team_a_name || 'Team A'}
                    </span>
                  </button>

                  <button
                    type="button"
                    onClick={() => applyRule2Walkover('B')}
                    className="p-2.5 text-left bg-neutral-900/80 hover:bg-neutral-800 border border-neutral-700/60 rounded text-xs transition-colors"
                  >
                    <span className="text-brand-red font-mono font-bold block text-[10px]">
                      RULE 2: WALKOVER
                    </span>
                    <span className="text-white font-medium truncate block">
                      3–0 to {selectedMatch.team_b_name || 'Team B'}
                    </span>
                  </button>

                  <button
                    type="button"
                    onClick={applyRule3BothFailed}
                    className="p-2.5 text-left bg-neutral-900/80 hover:bg-neutral-800 border border-neutral-700/60 rounded text-xs transition-colors"
                  >
                    <span className="text-amber-400 font-mono font-bold block text-[10px]">
                      RULE 3: BOTH FAILED
                    </span>
                    <span className="text-white font-medium truncate block">
                      0–0 (1 Point Each)
                    </span>
                  </button>
                </div>
              </div>

              {/* Score Input Fields */}
              <div className="grid grid-cols-2 gap-6">
                <div className="bg-black/50 p-4 rounded-lg border border-neutral-800 text-center">
                  <label className="block text-xs font-mono text-neutral-400 mb-2 truncate">
                    {selectedMatch.team_a_name || 'Team A'} Score
                  </label>
                  <input
                    type="number"
                    min="0"
                    max="99"
                    value={teamAScore}
                    onChange={(e) => setTeamAScore(parseInt(e.target.value, 10) || 0)}
                    className="w-24 text-center font-display text-4xl bg-neutral-900 border border-neutral-700 rounded py-2 text-white tabular-nums focus:border-brand-red focus:outline-none"
                  />
                </div>

                <div className="bg-black/50 p-4 rounded-lg border border-neutral-800 text-center">
                  <label className="block text-xs font-mono text-neutral-400 mb-2 truncate">
                    {selectedMatch.team_b_name || 'Team B'} Score
                  </label>
                  <input
                    type="number"
                    min="0"
                    max="99"
                    value={teamBScore}
                    onChange={(e) => setTeamBScore(parseInt(e.target.value, 10) || 0)}
                    className="w-24 text-center font-display text-4xl bg-neutral-900 border border-neutral-700 rounded py-2 text-white tabular-nums focus:border-brand-red focus:outline-none"
                  />
                </div>
              </div>

              {/* Outcome Status & Walkover Winner */}
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <div>
                  <label className="block text-xs font-mono text-neutral-400 mb-1">
                    Match Outcome Status
                  </label>
                  <select
                    value={matchStatus}
                    onChange={(e) => {
                      const val = e.target.value;
                      setMatchStatus(val);
                      if (val === 'Walkover' && !walkoverWinnerId) {
                        setWalkoverWinnerId(selectedMatch.team_a_id ?? null);
                      }
                    }}
                    className="w-full px-3 py-2 bg-neutral-900 border border-neutral-700 rounded text-xs font-mono text-white focus:outline-none"
                  >
                    <option value="Completed">Completed (Normal Match / Double Forfeit)</option>
                    <option value="Walkover">Walkover (Awarded to One Team)</option>
                  </select>
                </div>

                {matchStatus === 'Walkover' ? (
                  <div>
                    <label className="block text-xs font-mono text-neutral-400 mb-1">
                      Walkover Awarded To
                    </label>
                    <select
                      value={walkoverWinnerId ?? ''}
                      onChange={(e) => setWalkoverWinnerId(Number(e.target.value))}
                      className="w-full px-3 py-2 bg-neutral-900 border border-brand-red/60 rounded text-xs font-mono text-white focus:outline-none"
                    >
                      <option value={selectedMatch.team_a_id ?? ''}>
                        {selectedMatch.team_a_name || 'Team A'}
                      </option>
                      <option value={selectedMatch.team_b_id ?? ''}>
                        {selectedMatch.team_b_name || 'Team B'}
                      </option>
                    </select>
                  </div>
                ) : (
                  <div>
                    <label className="block text-xs font-mono text-neutral-400 mb-1">
                      Match Classification
                    </label>
                    <div className="px-3 py-2 bg-neutral-900/60 border border-neutral-800 rounded text-xs font-mono text-neutral-400">
                      Standard Result (Win = 3 pts, Draw = 1 pt)
                    </div>
                  </div>
                )}
              </div>

              {/* Notes / Reason */}
              <div>
                <label className="block text-xs font-mono text-neutral-400 mb-1">
                  Notes / Audit Reference / Rule Applied
                </label>
                <input
                  type="text"
                  value={notes}
                  onChange={(e) => setNotes(e.target.value)}
                  placeholder="e.g. Rule 2 Walkover verified after deadline, or normal play"
                  className="w-full px-3 py-2 bg-neutral-900 border border-neutral-700 rounded text-xs font-mono text-white focus:outline-none"
                />
              </div>

              {/* Optional Penalty Shootout */}
              <div className="p-4 bg-black/40 rounded-lg border border-neutral-800 space-y-3">
                <span className="text-xs font-mono text-neutral-400 uppercase block font-semibold">
                  Penalty Shootout (Optional - for tied knockout matches)
                </span>
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="block text-[11px] font-mono text-neutral-400 mb-1">
                      {selectedMatch.team_a_name || 'Team A'} Penalties
                    </label>
                    <input
                      type="number"
                      min="0"
                      value={penaltyA}
                      onChange={(e) => setPenaltyA(e.target.value)}
                      placeholder="e.g. 5"
                      className="w-full px-3 py-1.5 bg-neutral-900 border border-neutral-700 rounded text-xs font-mono text-white focus:outline-none"
                    />
                  </div>
                  <div>
                    <label className="block text-[11px] font-mono text-neutral-400 mb-1">
                      {selectedMatch.team_b_name || 'Team B'} Penalties
                    </label>
                    <input
                      type="number"
                      min="0"
                      value={penaltyB}
                      onChange={(e) => setPenaltyB(e.target.value)}
                      placeholder="e.g. 4"
                      className="w-full px-3 py-1.5 bg-neutral-900 border border-neutral-700 rounded text-xs font-mono text-white focus:outline-none"
                    />
                  </div>
                </div>
              </div>

              {/* Action Buttons */}
              <div className="flex flex-wrap items-center gap-3 pt-2">
                <button
                  type="submit"
                  disabled={loading}
                  className="px-6 py-2.5 bg-brand-red hover:bg-brand-red-bright text-white font-display text-lg tracking-wider rounded transition-colors flex items-center space-x-2 shadow-glow-red"
                >
                  <Save className="w-4 h-4" />
                  <span>RECORD SCORE & BROADCAST</span>
                </button>

                {selectedMatch.status === 'COMPLETED' && (
                  <button
                    type="button"
                    onClick={handleResetResult}
                    disabled={loading}
                    className="px-4 py-2.5 bg-neutral-900 hover:bg-neutral-800 border border-neutral-700 text-neutral-300 text-xs font-mono rounded transition-colors"
                  >
                    RESET MATCH TO SCHEDULED
                  </button>
                )}
              </div>
            </form>
          ) : (
            <div className="text-center py-20 font-mono text-sm text-neutral-400">
              Select a match from the list to enter or modify its score.
            </div>
          )}
        </div>
      </div>
      </>
      )}
    </div>
  );
};

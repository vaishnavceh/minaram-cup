import React, { useState } from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { ThemeProvider } from './ThemeContext';
import { Navbar } from './components/Navbar';
import { Footer } from './components/Footer';
import { HomePage } from './pages/HomePage';
import { FixturesPage } from './pages/FixturesPage';
import { ResultsPage } from './pages/ResultsPage';
import { StandingsPage } from './pages/StandingsPage';
import { TeamsPage } from './pages/TeamsPage';
import { TeamDetailPage } from './pages/TeamDetailPage';
import { BracketPage } from './pages/BracketPage';
import { RulesPage } from './pages/RulesPage';
import { AdminPage } from './pages/AdminPage';
import { AudioPlayer } from './components/AudioPlayer';
import { useLiveUpdates } from './hooks/useLiveUpdates';
import { Radio } from 'lucide-react';

export const App: React.FC = () => {
  const [liveToast, setLiveToast] = useState<string | null>(null);

  const { isConnected } = useLiveUpdates((evt) => {
    const evType = evt.event || (evt as any).type;
    if (evType === 'result_updated' || evType === 'match_updated') {
      const match = evt.data || {};
      const home = match.team_a_name || match.home_team_name || 'Home';
      const away = match.team_b_name || match.away_team_name || 'Away';
      const hScore = match.team_a_score ?? match.home_score ?? 0;
      const aScore = match.team_b_score ?? match.away_score ?? 0;
      setLiveToast(`MATCH UPDATE: ${home} ${hScore} - ${aScore} ${away}`);
      setTimeout(() => setLiveToast(null), 5000);
    } else if (evType === 'standings_updated') {
      setLiveToast('STANDINGS UPDATED: Group tables recalculated.');
      setTimeout(() => setLiveToast(null), 4000);
    } else if (evType === 'knockout_updated' || evType === 'ceremonial_draw_applied' || evType === 'knockout_fixtures_cleared') {
      const action = evt.data?.action || 'updated';
      setLiveToast(`KNOCKOUT UPDATE: Bracket ${String(action).replace(/_/g, ' ')}.`);
      setTimeout(() => setLiveToast(null), 4000);
    }
  });

  return (
    <ThemeProvider>
      <BrowserRouter>
        <div className="flex flex-col min-h-screen theme-bg text-[#F5F5F5]">
          {/* Floating Live Notification Toast */}
          {liveToast && (
            <div className="fixed top-24 right-4 z-50 bg-brand-red text-white px-4 py-2.5 rounded-lg shadow-glow-red font-mono text-xs flex items-center space-x-2 animate-bounce">
              <Radio className="w-4 h-4 animate-pulse" />
              <span>{liveToast}</span>
            </div>
          )}

          <Navbar isLiveConnected={isConnected} />

          <main className="flex-grow">
            <Routes>
              <Route path="/" element={<HomePage />} />
              <Route path="/fixtures" element={<FixturesPage />} />
              <Route path="/results" element={<ResultsPage />} />
              <Route path="/standings" element={<StandingsPage />} />
              <Route path="/teams" element={<TeamsPage />} />
              <Route path="/teams/:id" element={<TeamDetailPage />} />
              <Route path="/bracket" element={<BracketPage />} />
              <Route path="/knockout" element={<BracketPage />} />
              <Route path="/rules" element={<RulesPage />} />
              <Route path="/admin" element={<AdminPage />} />
              <Route path="*" element={<Navigate to="/" replace />} />
            </Routes>
          </main>

          <Footer />
          <AudioPlayer />
        </div>
      </BrowserRouter>
    </ThemeProvider>
  );
};

export default App;

import React, { useState } from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
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
import { useLiveUpdates } from './hooks/useLiveUpdates';
import { Radio } from 'lucide-react';

export const App: React.FC = () => {
  const [liveToast, setLiveToast] = useState<string | null>(null);

  const { isConnected } = useLiveUpdates((evt) => {
    if (evt.event === 'result_updated') {
      const match = evt.data;
      setLiveToast(`MATCH UPDATE: ${match.team_a_name} ${match.team_a_score} - ${match.team_b_score} ${match.team_b_name}`);
      setTimeout(() => setLiveToast(null), 5000);
    } else if (evt.event === 'standings_updated') {
      setLiveToast('STANDINGS UPDATED: Group table recalculated.');
      setTimeout(() => setLiveToast(null), 4000);
    }
  });

  return (
    <BrowserRouter>
      <div className="flex flex-col min-h-screen bg-[#080808] text-[#F5F5F5]">
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
      </div>
    </BrowserRouter>
  );
};

export default App;

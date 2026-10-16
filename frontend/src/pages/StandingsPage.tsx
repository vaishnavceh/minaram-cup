import React, { useEffect, useState } from 'react';
import { api } from '../api';
import { PublicGroupStandings } from '../types';
import { StandingsTable } from '../components/StandingsTable';
import { GoldenBootShowcase } from '../components/GoldenBootShowcase';
import { BarChart3, HelpCircle, ShieldCheck, FileDown, Check, Loader2 } from 'lucide-react';

export const StandingsPage: React.FC = () => {
  const [standings, setStandings] = useState<PublicGroupStandings[]>([]);
  const [loading, setLoading] = useState(true);
  const [isExportingPdf, setIsExportingPdf] = useState(false);
  const [pdfExportSuccess, setPdfExportSuccess] = useState(false);

  const loadStandings = async () => {
    try {
      const data = await api.getStandings();
      setStandings(data);
    } catch (err) {
      console.error('Failed to load standings', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadStandings();
  }, []);

  const handleExportAllPdf = async () => {
    if (isExportingPdf || standings.length === 0) return;
    try {
      setIsExportingPdf(true);
      const { exportAllStandingsPdf } = await import('../utils/standingsPdf');
      exportAllStandingsPdf(standings);
      setPdfExportSuccess(true);
      setTimeout(() => setPdfExportSuccess(false), 2500);
    } catch (err) {
      console.error('Failed to export standings PDF', err);
    } finally {
      setIsExportingPdf(false);
    }
  };

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
      {/* Header */}
      <div className="mb-10 pb-6 border-b border-[#222222] flex flex-col md:flex-row md:items-end justify-between gap-6">
        <div>
          <div className="flex items-center space-x-2 text-xs font-mono uppercase tracking-widest text-brand-red mb-2">
            <BarChart3 className="w-4 h-4" />
            <span>POINTS TABLES & RANKINGS</span>
          </div>
          <h1 className="font-display text-4xl sm:text-5xl text-white tracking-wider">
            GROUP STANDINGS
          </h1>
          <p className="text-sm text-neutral-400 mt-2 max-w-xl">
            Live group standings and points calculations. The top two teams from each group
            earn a direct ticket into the championship knockout quarter-finals.
          </p>
        </div>

        {/* PDF Exporter Button */}
        <div className="shrink-0 flex items-center">
          <button
            type="button"
            onClick={handleExportAllPdf}
            disabled={isExportingPdf || loading || standings.length === 0}
            className={`inline-flex items-center space-x-2.5 px-4 py-2.5 rounded text-xs font-mono font-bold uppercase tracking-wider transition-all duration-200 border cursor-pointer shadow-md select-none ${
              pdfExportSuccess
                ? 'bg-emerald-950/90 text-emerald-300 border-emerald-600/80 shadow-emerald-900/30'
                : 'bg-neutral-900 hover:bg-neutral-800 text-white hover:text-brand-red border-neutral-700 hover:border-brand-red/60'
            } disabled:opacity-50 disabled:cursor-not-allowed`}
            title="Download complete tournament standings document as PDF"
            aria-label="Export standings as PDF"
          >
            {isExportingPdf ? (
              <Loader2 className="w-4 h-4 animate-spin text-brand-red" />
            ) : pdfExportSuccess ? (
              <Check className="w-4 h-4 text-emerald-400" />
            ) : (
              <FileDown className="w-4 h-4 text-brand-red" />
            )}
            <span>
              {pdfExportSuccess ? 'STANDINGS PDF DOWNLOADED' : 'EXPORT STANDINGS (PDF)'}
            </span>
          </button>
        </div>
      </div>

      {/* Standings Grid */}
      {loading ? (
        <div className="text-center py-20 font-mono text-sm text-neutral-500">
          Calculating standings...
        </div>
      ) : (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          {(Array.isArray(standings) ? standings : []).map((grp) => (
            <StandingsTable key={grp.group_name} groupData={grp} />
          ))}
        </div>
      )}

      {/* Golden Boot Leaderboard Section */}
      <div className="mt-16">
        <GoldenBootShowcase />
      </div>

      {/* Tie-breaker & Rules Callout */}
      <div className="mt-14 bg-[#121212] border border-[#222222] rounded-lg p-6 sm:p-8">
        <div className="flex items-center space-x-2 text-sm font-mono text-white mb-4">
          <HelpCircle className="w-4 h-4 text-brand-red" />
          <span className="font-bold uppercase tracking-wider">OFFICIAL TIE-BREAKER PROTOCOL</span>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4 text-xs font-mono text-neutral-400">
          <div className="bg-black/50 p-4 rounded border border-neutral-800">
            <span className="text-brand-red font-bold text-sm block mb-1">1. TOTAL POINTS</span>
            <span>Win: 3 points • Draw: 1 point • Loss: 0 points</span>
          </div>
          <div className="bg-black/50 p-4 rounded border border-neutral-800">
            <span className="text-brand-red font-bold text-sm block mb-1">2. GOAL DIFFERENCE</span>
            <span>Total goals scored minus total goals conceded (GD)</span>
          </div>
          <div className="bg-black/50 p-4 rounded border border-neutral-800">
            <span className="text-brand-red font-bold text-sm block mb-1">3. GOALS SCORED</span>
            <span>Highest total goals scored in all group matches (GF)</span>
          </div>
          <div className="bg-black/50 p-4 rounded border border-neutral-800">
            <span className="text-brand-red font-bold text-sm block mb-1">4. HEAD-TO-HEAD</span>
            <span>Direct match outcome between the tied teams</span>
          </div>
        </div>
      </div>
    </div>
  );
};

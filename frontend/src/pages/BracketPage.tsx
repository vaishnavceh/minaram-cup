import React, { useEffect, useState, useRef } from 'react';
import { api } from '../api';
import { PublicBracket } from '../types';
import { BracketTree } from '../components/BracketTree';
import { GitFork, Trophy, Download, Check, Loader2, Sparkles, AlertCircle } from 'lucide-react';

export const BracketPage: React.FC = () => {
  const [bracket, setBracket] = useState<PublicBracket>({ rounds: [] });
  const [loading, setLoading] = useState(true);
  const [isExporting, setIsExporting] = useState(false);
  const [downloadSuccess, setDownloadSuccess] = useState(false);
  const exportRef = useRef<HTMLDivElement>(null);

  const loadBracket = async () => {
    try {
      const data = await api.getBracket();
      setBracket(data);
    } catch (err) {
      console.error('Failed to load bracket', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadBracket();
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

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
      {/* Header */}
      <div className="mb-8 pb-6 border-b border-[#222222] flex flex-col md:flex-row md:items-end justify-between gap-6">
        <div>
          <div className="flex items-center space-x-2 text-xs font-mono uppercase tracking-widest text-brand-red mb-2">
            <GitFork className="w-4 h-4" />
            <span>ROAD TO THE TROPHY</span>
          </div>
          <h1 className="font-display text-4xl sm:text-5xl text-white tracking-wider">
            KNOCKOUT CHAMPIONSHIP
          </h1>
          <p className="text-sm text-neutral-400 mt-2 max-w-xl">
            Single-elimination playoff bracket featuring the top qualified teams.
            Quarter-Finals, Semi-Finals, and the Grand Final.
          </p>
        </div>

        {/* Download Action & Live Status */}
        <div className="flex flex-wrap items-center gap-3 shrink-0">
          <div className="flex items-center space-x-2 px-3.5 py-2 rounded bg-neutral-900 border border-neutral-800 text-xs font-mono text-neutral-300">
            <span className="w-2 h-2 rounded-full bg-amber-400 animate-pulse" />
            <span className="text-amber-400 font-bold uppercase tracking-wider">GROUP STAGE LIVE</span>
          </div>

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
            <span>{downloadSuccess ? 'BRACKET PNG SAVED' : 'DOWNLOAD BRACKET (PNG)'}</span>
          </button>
        </div>
      </div>

      {/* Group Stage Notice Banner */}
      <div className="mb-8 p-4 rounded-xl bg-[#111111] border border-neutral-800/80 flex items-start sm:items-center justify-between flex-wrap gap-3">
        <div className="flex items-center space-x-3 text-xs font-mono text-neutral-300">
          <Sparkles className="w-4 h-4 text-amber-400 shrink-0" />
          <span>
            <strong className="text-white">KNOCKOUT SLOTS UNSEEDED:</strong> All bracket positions currently say{' '}
            <span className="text-amber-400 font-semibold italic">"Yet to decide"</span> while group stage matches are in progress. Qualifying squads will advance here automatically upon group conclusion.
          </span>
        </div>
      </div>

      {loading ? (
        <div className="text-center py-20 font-mono text-sm text-neutral-500">
          Loading tournament bracket...
        </div>
      ) : (
        <div ref={exportRef} className="p-4 sm:p-6 rounded-2xl bg-[#0c0c0c] border border-neutral-800/80 shadow-2xl relative">
          <BracketTree bracket={bracket} />

          {/* Tournament Watermark Signature for Export Graphic & Footer */}
          <div className="mt-8 pt-4 border-t border-neutral-900 flex flex-wrap items-center justify-between text-[11px] font-mono text-neutral-500 gap-2">
            <div className="flex items-center space-x-2">
              <span className="w-1.5 h-1.5 rounded-full bg-amber-400" />
              <span className="text-neutral-300 font-bold">MINARAM CUP 2026</span>
              <span className="text-neutral-500">· OFFICIAL EFOOTBALL CHAMPIONSHIP</span>
            </div>
            <span className="text-neutral-400 font-medium">TKM COLLEGE OF ENGINEERING · KNOCKOUT PLAYOFFS</span>
          </div>
        </div>
      )}
    </div>
  );
};

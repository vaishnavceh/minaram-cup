import React, { useState } from 'react';
import { PublicGroupStandings } from '../types';
import { Download, Check } from 'lucide-react';

interface StandingsTableProps {
  groupData: PublicGroupStandings;
}

export const StandingsTable: React.FC<StandingsTableProps> = ({ groupData }) => {
  const [pdfSaved, setPdfSaved] = useState(false);

  const handleExportGroupPdf = async (e: React.MouseEvent) => {
    e.stopPropagation();
    try {
      const { exportSingleGroupPdf } = await import('../utils/standingsPdf');
      exportSingleGroupPdf(groupData);
      setPdfSaved(true);
      setTimeout(() => setPdfSaved(false), 2000);
    } catch (err) {
      console.error('Failed to export single group PDF', err);
    }
  };

  return (
    <div className="bg-[#121212] border border-[#222222] rounded-lg overflow-hidden">
      {/* Header */}
      <div className="px-5 py-3.5 bg-black/60 border-b border-[#1f1f1f] flex items-center justify-between">
        <div className="flex items-center space-x-2.5">
          <span className="w-2.5 h-2.5 bg-brand-red inline-block" />
          <h3 className="font-display text-xl tracking-wider text-white uppercase">
            GROUP {groupData.group_name}
          </h3>
        </div>
        <div className="flex items-center space-x-3">
          <span className="text-[11px] font-mono text-neutral-400 uppercase tracking-widest hidden sm:inline">
            TOP 2 ADVANCE TO PLAYOFFS
          </span>
          <button
            type="button"
            onClick={handleExportGroupPdf}
            title={`Export Group ${groupData.group_name} Standings as PDF`}
            className={`inline-flex items-center space-x-1 px-2 py-0.5 rounded text-[10px] font-mono transition-all border cursor-pointer select-none ${
              pdfSaved
                ? 'bg-emerald-950/80 text-emerald-400 border-emerald-700/60'
                : 'bg-neutral-900 hover:bg-neutral-800 text-neutral-400 hover:text-white border-neutral-800 hover:border-neutral-600'
            }`}
          >
            {pdfSaved ? <Check className="w-2.5 h-2.5 text-emerald-400" /> : <Download className="w-2.5 h-2.5" />}
            <span className="text-[9px] uppercase font-bold">{pdfSaved ? 'SAVED' : 'PDF'}</span>
          </button>
        </div>
      </div>

      {/* Table */}
      <div className="overflow-x-auto">
        <table className="w-full text-left text-sm">
          <thead>
            <tr className="border-b border-[#222222] bg-[#161616]/70 text-[11px] font-mono uppercase tracking-wider text-neutral-400">
              <th className="py-2.5 px-3 text-center w-12">POS</th>
              <th className="py-2.5 px-4">CLUB / TEAM</th>
              <th className="py-2.5 px-2 text-center w-10">MP</th>
              <th className="py-2.5 px-2 text-center w-10">W</th>
              <th className="py-2.5 px-2 text-center w-10">D</th>
              <th className="py-2.5 px-2 text-center w-10">L</th>
              <th className="py-2.5 px-2 text-center w-12 hidden sm:table-cell">GF</th>
              <th className="py-2.5 px-2 text-center w-12 hidden sm:table-cell">GA</th>
              <th className="py-2.5 px-2 text-center w-12">GD</th>
              <th className="py-2.5 px-3 text-center w-14 font-bold text-white">PTS</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-[#1c1c1c] font-sans">
            {(groupData?.standings || []).map((row, idx) => {
              const qualifies = idx < 2;
              return (
                <tr
                  key={row.team_id}
                  className={`hover:bg-[#181818] transition-colors ${
                    qualifies ? 'bg-emerald-950/10' : ''
                  }`}
                >
                  {/* Position */}
                  <td className="py-3 px-3 text-center font-mono text-xs font-bold">
                    <span
                      className={`inline-flex items-center justify-center w-6 h-6 rounded ${
                        qualifies
                          ? 'bg-emerald-900/60 text-emerald-300 border border-emerald-700/60'
                          : 'text-neutral-400'
                      }`}
                    >
                      {row.rank || idx + 1}
                    </span>
                  </td>

                  {/* Team */}
                  <td className="py-3 px-4 font-medium text-white flex items-center space-x-2.5">
                    <div className="w-6 h-6 rounded-full bg-neutral-800 border border-neutral-700 flex items-center justify-center text-[10px] font-display text-neutral-300 shrink-0">
                      {row.team_name.substring(0, 2).toUpperCase()}
                    </div>
                    <span className="truncate max-w-[160px] sm:max-w-[220px]" title={row.team_name}>
                      {row.team_name}
                    </span>
                  </td>

                  {/* Stats */}
                  <td className="py-3 px-2 text-center font-mono text-xs tabular-nums text-neutral-300">
                    {row.played}
                  </td>
                  <td className="py-3 px-2 text-center font-mono text-xs tabular-nums text-neutral-300">
                    {row.won}
                  </td>
                  <td className="py-3 px-2 text-center font-mono text-xs tabular-nums text-neutral-400">
                    {row.drawn}
                  </td>
                  <td className="py-3 px-2 text-center font-mono text-xs tabular-nums text-neutral-400">
                    {row.lost}
                  </td>
                  <td className="py-3 px-2 text-center font-mono text-xs tabular-nums text-neutral-400 hidden sm:table-cell">
                    {row.goals_for}
                  </td>
                  <td className="py-3 px-2 text-center font-mono text-xs tabular-nums text-neutral-400 hidden sm:table-cell">
                    {row.goals_against}
                  </td>
                  <td
                    className={`py-3 px-2 text-center font-mono text-xs tabular-nums font-semibold ${
                      row.goal_difference > 0
                        ? 'text-emerald-400'
                        : row.goal_difference < 0
                        ? 'text-rose-400'
                        : 'text-neutral-400'
                    }`}
                  >
                    {row.goal_difference > 0 ? `+${row.goal_difference}` : row.goal_difference}
                  </td>
                  <td className="py-3 px-3 text-center font-mono text-sm tabular-nums font-bold text-white bg-black/30">
                    {row.points}
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>

      <div className="px-4 py-2 bg-black/40 border-t border-[#1a1a1a] flex items-center space-x-2 text-[10px] font-mono text-neutral-400">
        <span className="w-2 h-2 rounded bg-emerald-500/70 inline-block" />
        <span>Top 2 advance directly to Quarter-Final knockouts</span>
      </div>
    </div>
  );
};

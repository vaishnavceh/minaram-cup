import { PublicBracket } from '../types';
import { Trophy, Crown, Sparkles } from 'lucide-react';

interface BracketTreeProps {
  bracket: PublicBracket;
}

export const BracketTree: React.FC<BracketTreeProps> = ({ bracket }) => {
  const { rounds, champion } = bracket;

  if (!rounds || rounds.length === 0) {
    return (
      <div className="text-center py-16 px-4 bg-[#111111] border border-[#222222] rounded-lg">
        <Trophy className="w-12 h-12 text-neutral-600 mx-auto mb-3" />
        <h3 className="font-display text-2xl text-white tracking-wider">KNOCKOUT BRACKET PENDING</h3>
        <p className="text-sm text-neutral-400 max-w-md mx-auto mt-2">
          The knockout stage bracket will be seeded automatically once the group stage fixtures conclude.
        </p>
      </div>
    );
  }

  return (
    <div className="space-y-8">
      {/* Champion Banner if decided */}
      {champion && (
        <div className="relative overflow-hidden rounded-xl border border-brand-gold/60 bg-gradient-to-r from-black via-[#1c1608] to-black p-6 sm:p-8 text-center shadow-[0_0_50px_rgba(229,184,66,0.15)]">
          <div className="flex flex-col items-center justify-center space-y-3">
            <div className="w-16 h-16 rounded-full bg-brand-gold/20 border border-brand-gold flex items-center justify-center text-brand-gold animate-bounce">
              <Crown className="w-8 h-8" />
            </div>
            <span className="text-xs font-mono uppercase tracking-widest text-brand-gold flex items-center space-x-1">
              <Sparkles className="w-3.5 h-3.5 inline" />
              <span>MINARAM CUP TOURNAMENT CHAMPION</span>
              <Sparkles className="w-3.5 h-3.5 inline" />
            </span>
            <h2 className="font-display text-4xl sm:text-5xl text-white tracking-wider">
              {champion.name}
            </h2>
            <p className="text-sm text-neutral-400">
              Manager: <span className="text-white font-medium">{champion.manager_name}</span> ({champion.department} · Year {champion.year})
            </p>
          </div>
        </div>
      )}

      {/* Bracket Rounds Columns */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6 relative">
        {rounds.map((round) => (
          <div key={round.round_name} className="flex flex-col space-y-4">
            {/* Round Title */}
            <div className="bg-black/60 border border-[#262626] rounded-md py-2.5 px-4 text-center">
              <h4 className="font-display text-lg tracking-wider text-white uppercase">
                {round.round_name}
              </h4>
              <span className="text-[10px] font-mono text-neutral-400 uppercase tracking-widest">
                {(round.matches || []).length} {(round.matches || []).length === 1 ? 'Match' : 'Matches'}
              </span>
            </div>

            {/* Matches in Round */}
            <div className="flex flex-col justify-around flex-grow space-y-4">
              {(round.matches || []).map((m) => {
                const isCompleted = m.status === 'COMPLETED';
                const teamAWon = isCompleted && (
                  (m.team_a_score ?? 0) > (m.team_b_score ?? 0) ||
                  ((m.team_a_score ?? 0) === (m.team_b_score ?? 0) && (m.penalty_a ?? 0) > (m.penalty_b ?? 0))
                );
                const teamBWon = isCompleted && (
                  (m.team_b_score ?? 0) > (m.team_a_score ?? 0) ||
                  ((m.team_a_score ?? 0) === (m.team_b_score ?? 0) && (m.penalty_b ?? 0) > (m.penalty_a ?? 0))
                );

                return (
                  <div
                    key={m.id}
                    className="bg-[#141414] border border-[#242424] rounded-lg p-3 hover:border-neutral-600 transition-colors shadow-sm"
                  >
                    <div className="text-[10px] font-mono text-neutral-400 mb-2 flex items-center justify-between">
                      <span>M#{m.match_number}</span>
                      <span className={isCompleted ? 'text-neutral-400' : 'text-amber-500'}>
                        {m.status}
                      </span>
                    </div>

                    {/* Team A */}
                    <div
                      className={`flex items-center justify-between py-1 px-2 rounded ${
                        teamAWon ? 'bg-neutral-800/80 font-bold text-white' : 'text-neutral-300'
                      }`}
                    >
                      <span className="truncate max-w-[130px] text-xs">
                        {m.team_a_name || 'TBD'}
                      </span>
                      <span className="font-mono text-xs tabular-nums">
                        {isCompleted ? m.team_a_score : '-'}
                      </span>
                    </div>

                    {/* Team B */}
                    <div
                      className={`flex items-center justify-between py-1 px-2 rounded mt-1 ${
                        teamBWon ? 'bg-neutral-800/80 font-bold text-white' : 'text-neutral-300'
                      }`}
                    >
                      <span className="truncate max-w-[130px] text-xs">
                        {m.team_b_name || 'TBD'}
                      </span>
                      <span className="font-mono text-xs tabular-nums">
                        {isCompleted ? m.team_b_score : '-'}
                      </span>
                    </div>

                    {isCompleted && (m.penalty_a !== null && m.penalty_b !== null) && (
                      <div className="text-right text-[10px] font-mono text-neutral-400 mt-1">
                        pen: {m.penalty_a} - {m.penalty_b}
                      </div>
                    )}
                  </div>
                );
              })}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

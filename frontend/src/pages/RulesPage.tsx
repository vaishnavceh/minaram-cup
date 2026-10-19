import React from 'react';
import { Shield, Clock, Award, Users, AlertTriangle, CheckCircle } from 'lucide-react';

export const RulesPage: React.FC = () => {
  return (
    <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
      {/* Header Banner */}
      <div className="mb-10 relative rounded-2xl overflow-hidden border border-blue-500/30 bg-gradient-to-r from-[#030d26] via-[#051336] to-[#020718] p-6 sm:p-8 shadow-2xl">
        <div className="absolute right-0 top-0 bottom-0 w-full sm:w-2/3 opacity-25 sm:opacity-40 pointer-events-none">
          <img
            src="/assets/backgrounds/ucl_stadium_bg.jpg"
            alt="UEFA Champions League Stadium"
            className="w-full h-full object-cover object-center filter contrast-125"
          />
          <div className="absolute inset-0 bg-gradient-to-r from-[#030d26] via-[#030d26]/80 to-transparent" />
        </div>
        <div className="relative z-10">
          <div className="flex items-center space-x-2 text-xs font-mono uppercase tracking-widest text-blue-400 mb-2">
            <Shield className="w-4 h-4 text-amber-400" />
            <span>GOVERNANCE & FAIR PLAY · UEFA STAGE</span>
          </div>
          <h1 className="font-display text-4xl sm:text-5xl text-white tracking-wider">
            OFFICIAL RULEBOOK
          </h1>
          <p className="text-sm text-blue-200/80 mt-2">
            Rules and regulations governing the MINARAM CUP eFootball Championship.
            All participants must abide by these tournament directives.
          </p>
        </div>
      </div>

      {/* Rules Content */}
      <div className="space-y-8 font-sans">
        {/* Section 1: Tournament Format */}
        <div className="bg-[#121212] border border-[#222222] rounded-lg p-6">
          <div className="flex items-center space-x-3 mb-4">
            <Award className="w-5 h-5 text-brand-red" />
            <h2 className="font-display text-2xl text-white tracking-wide">
              1. TOURNAMENT STRUCTURE & ADVANCEMENT
            </h2>
          </div>
          <ul className="space-y-2.5 text-sm text-neutral-300">
            <li className="flex items-start space-x-2">
              <span className="text-brand-red font-bold">•</span>
              <span><strong>Group Stage:</strong> 16 teams seeded into 4 Groups (A, B, C, D) of 4 teams each. Single round-robin format where every team plays 3 matches.</span>
            </li>
            <li className="flex items-start space-x-2">
              <span className="text-brand-red font-bold">•</span>
              <span><strong>Points System:</strong> 3 points for a win, 1 point for a draw, 0 points for a loss.</span>
            </li>
            <li className="flex items-start space-x-2">
              <span className="text-brand-red font-bold">•</span>
              <span><strong>Qualification:</strong> The top two teams from each group qualify for the Quarter-Finals.</span>
            </li>
            <li className="flex items-start space-x-2">
              <span className="text-brand-red font-bold">•</span>
              <span><strong>Knockout Phase:</strong> Single-elimination bracket (Quarter-Finals ➔ Semi-Finals ➔ Grand Final).</span>
            </li>
          </ul>
        </div>

        {/* Section 2: Match Settings */}
        <div className="bg-[#121212] border border-[#222222] rounded-lg p-6">
          <div className="flex items-center space-x-3 mb-4">
            <Clock className="w-5 h-5 text-brand-red" />
            <h2 className="font-display text-2xl text-white tracking-wide">
              2. MATCH SETTINGS & CONFIGURATION
            </h2>
          </div>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 text-xs font-mono text-neutral-300">
            <div className="p-3 bg-black/50 rounded border border-neutral-800">
              <span className="text-neutral-500 block">MATCH LENGTH</span>
              <span className="text-white font-bold text-sm">10 Minutes (5 min halves)</span>
            </div>
            <div className="p-3 bg-black/50 rounded border border-neutral-800">
              <span className="text-neutral-500 block">SUBSTITUTIONS</span>
              <span className="text-white font-bold text-sm">5 Substitutions (3 intervals)</span>
            </div>
            <div className="p-3 bg-black/50 rounded border border-neutral-800">
              <span className="text-neutral-500 block">GROUP STAGE EXTRA TIME</span>
              <span className="text-white font-bold text-sm">OFF (Draws permitted)</span>
            </div>
            <div className="p-3 bg-black/50 rounded border border-neutral-800">
              <span className="text-neutral-500 block">KNOCKOUT EXTRA TIME & PK</span>
              <span className="text-white font-bold text-sm">ON (ET + Penalties mandatory)</span>
            </div>
          </div>
        </div>

        {/* Section 3: Official Fixture Rules */}
        <div className="bg-[#121212] border-2 border-brand-red/40 rounded-lg p-6 relative overflow-hidden shadow-glow-red/5">
          <div className="flex items-center space-x-3 mb-6">
            <Clock className="w-5 h-5 text-brand-red" />
            <div>
              <h2 className="font-display text-2xl text-white tracking-wide">
                3. OFFICIAL FIXTURE RULES
              </h2>
              <span className="text-xs font-mono text-neutral-400">
                Points system, walkovers, deadlines, and forfeiture policy
              </span>
            </div>
          </div>

          <div className="space-y-4">
            {/* Rule 1: Points System */}
            <div className="p-4 bg-black/60 rounded-lg border border-neutral-800">
              <div className="flex items-center justify-between mb-2">
                <span className="text-xs font-mono uppercase tracking-wider text-brand-red font-bold">
                  1. POINTS SYSTEM
                </span>
                <span className="text-[10px] font-mono text-neutral-400 bg-neutral-900 px-2 py-0.5 rounded border border-neutral-800">
                  STANDARD ALLOCATION
                </span>
              </div>
              <p className="text-xs text-neutral-300 mb-3">
                Tournament standings and group rankings are determined based on the following match points:
              </p>
              <div className="grid grid-cols-3 gap-3 text-center font-mono">
                <div className="p-2.5 bg-neutral-900/80 rounded border border-neutral-800">
                  <span className="text-xs text-neutral-400 block uppercase">WIN</span>
                  <span className="text-white font-bold text-lg text-emerald-400">3 Points</span>
                </div>
                <div className="p-2.5 bg-neutral-900/80 rounded border border-neutral-800">
                  <span className="text-xs text-neutral-400 block uppercase">DRAW</span>
                  <span className="text-white font-bold text-lg text-amber-400">1 Point</span>
                  <span className="text-[10px] text-neutral-500 block">per team</span>
                </div>
                <div className="p-2.5 bg-neutral-900/80 rounded border border-neutral-800">
                  <span className="text-xs text-neutral-400 block uppercase">LOSS</span>
                  <span className="text-white font-bold text-lg text-rose-400">0 Points</span>
                </div>
              </div>
            </div>

            {/* Rule 2: One Team Fails to Play */}
            <div className="p-4 bg-black/60 rounded-lg border border-brand-red/30">
              <div className="flex items-center justify-between mb-2">
                <span className="text-xs font-mono uppercase tracking-wider text-brand-red font-bold">
                  2. ONE TEAM FAILS TO PLAY
                </span>
                <span className="text-[10px] font-mono text-brand-red bg-brand-red/10 px-2 py-0.5 rounded border border-brand-red/30 font-bold">
                  3–0 WALKOVER
                </span>
              </div>
              <p className="text-sm text-neutral-200 leading-relaxed">
                If one team fails to play within the given deadline, the opposing team will be awarded a{' '}
                <strong className="text-white font-bold bg-neutral-900 px-1.5 py-0.5 rounded border border-neutral-700">3–0 walkover victory</strong>{' '}
                and receive <strong className="text-emerald-400">3 points</strong>. The defaulting squad will be assessed a 0–3 loss and 0 points.
              </p>
            </div>

            {/* Rule 3: Both Teams Fail to Play */}
            <div className="p-4 bg-black/60 rounded-lg border border-neutral-800">
              <div className="flex items-center justify-between mb-2">
                <span className="text-xs font-mono uppercase tracking-wider text-neutral-300 font-bold">
                  3. BOTH TEAMS FAIL TO PLAY
                </span>
                <span className="text-[10px] font-mono text-amber-400 bg-amber-400/10 px-2 py-0.5 rounded border border-amber-400/30 font-bold">
                  0–0 · 1 PT EACH
                </span>
              </div>
              <p className="text-sm text-neutral-200 leading-relaxed">
                If neither team plays within the given deadline, the match will be recorded as{' '}
                <strong className="text-white font-bold bg-neutral-900 px-1.5 py-0.5 rounded border border-neutral-700">0–0</strong>,{' '}
                and both teams will receive <strong className="text-amber-400">1 point each</strong>.
              </p>
            </div>

            {/* Rule 4: Walkover Claims */}
            <div className="p-4 bg-black/60 rounded-lg border border-neutral-800">
              <div className="flex items-center justify-between mb-2">
                <span className="text-xs font-mono uppercase tracking-wider text-neutral-300 font-bold">
                  4. WALKOVER CLAIMS
                </span>
                <span className="text-[10px] font-mono text-neutral-400 bg-neutral-900 px-2 py-0.5 rounded border border-neutral-800">
                  VERIFICATION MANDATORY
                </span>
              </div>
              <p className="text-sm text-neutral-200 leading-relaxed mb-3">
                If Rule 2 applies, contact the admins <strong className="text-white underline underline-offset-2">only after the fixture deadline has passed</strong> and provide proof (e.g., chat logs, communication attempts, and proof of opponent unavailability or unresponsiveness).
              </p>
              <div>
                <a
                  href="https://wa.me/919746603975"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="inline-flex items-center space-x-2 px-3 py-1.5 rounded bg-emerald-950/80 hover:bg-emerald-900 border border-emerald-700/60 text-emerald-400 font-mono text-xs font-bold transition-colors shadow-sm"
                >
                  <span>Submit Walkover Proof / Raise Complaint on WhatsApp (+91 97466 03975) ➔</span>
                </a>
              </div>
            </div>

            {/* Rule 5: Deadline */}
            <div className="p-4 bg-black/60 rounded-lg border border-neutral-800">
              <div className="flex items-center justify-between mb-2">
                <span className="text-xs font-mono uppercase tracking-wider text-neutral-300 font-bold">
                  5. DEADLINE
                </span>
                <span className="text-[10px] font-mono text-neutral-400 bg-neutral-900 px-2 py-0.5 rounded border border-neutral-800">
                  STRICT TIMELINE
                </span>
              </div>
              <p className="text-sm text-neutral-200 leading-relaxed">
                All fixtures must be completed within the specified time. Teams are responsible for coordinating with their opponents and completing their matches before the deadline.
              </p>
            </div>
          </div>
        </div>

        {/* Section 4: Eligibility & Student Integrity */}
        <div className="bg-[#121212] border border-[#222222] rounded-lg p-6">
          <div className="flex items-center space-x-3 mb-4">
            <Users className="w-5 h-5 text-brand-red" />
            <h2 className="font-display text-2xl text-white tracking-wide">
              4. PLAYER ELIGIBILITY
            </h2>
          </div>
          <p className="text-sm text-neutral-300 leading-relaxed">
            All participating squad managers must be currently enrolled bona fide students of
            <strong> TKM College of Engineering</strong>. College identity verification may be requested
            prior to knockout stage matches. Impersonation or unauthorized subbing results in instant disqualification.
          </p>
        </div>

        {/* Section 5: Disconnections & Network Issues */}
        <div className="bg-[#121212] border border-[#222222] rounded-lg p-6">
          <div className="flex items-center space-x-3 mb-4">
            <AlertTriangle className="w-5 h-5 text-amber-500" />
            <h2 className="font-display text-2xl text-white tracking-wide">
              5. DISCONNECTIONS & DISPUTES
            </h2>
          </div>
          <p className="text-sm text-neutral-300 leading-relaxed mb-4">
            If an unintentional network error or connection interruption occurs during any 10-minute match, the following protocol must be strictly observed:
          </p>
          <ul className="space-y-3.5 text-sm text-neutral-300">
            <li className="flex items-start space-x-2.5">
              <span className="text-brand-red font-bold text-base leading-none">•</span>
              <div>
                <strong className="text-white">Mandatory Screenshot Proof:</strong> When a network cut occurs, either side (or both players) must immediately take a clear screenshot showing the scoreline and game clock up to that exact disconnection moment. Submitting screenshot verification to the tournament desk is mandatory.
              </div>
            </li>
            <li className="flex items-start space-x-2.5">
              <span className="text-brand-red font-bold text-base leading-none">•</span>
              <div>
                <strong className="text-white">Additional 5-Minute Continuation Match:</strong> The match will immediately continue from that point by playing an additional 5-minute match between the two teams.
              </div>
            </li>
            <li className="flex items-start space-x-2.5">
              <span className="text-brand-red font-bold text-base leading-none">•</span>
              <div>
                <strong className="text-white">Aggregate Final Score:</strong> The official final scoreline will be calculated as the combined aggregate:
                <div className="mt-2 p-3 bg-black/60 border border-neutral-800 rounded font-mono text-xs text-neutral-200">
                  <span className="text-brand-gold font-bold">OFFICIAL FINAL SCORE</span> = (Pre-Disconnect Score from Screenshot) + (Score from 5-Minute Continuation Match)
                </div>
              </div>
            </li>
            <li className="flex items-start space-x-2.5">
              <span className="text-brand-red font-bold text-base leading-none">•</span>
              <div>
                <strong className="text-white">Intentional Rage-Quit & Dispute Resolution:</strong> Intentionally quitting, disconnecting to manipulate results, refusing to play the continuation match, or failing to produce screenshot proof will result in an immediate match forfeiture (awarded a 3-0 loss) and disciplinary review by tournament organizers.
              </div>
            </li>
          </ul>
        </div>

        {/* Section 6: Organizers & Sponsors */}
        <div className="bg-[#121212] border border-[#222222] rounded-lg p-6">
          <div className="flex items-center space-x-3 mb-4">
            <CheckCircle className="w-5 h-5 text-emerald-500" />
            <h2 className="font-display text-2xl text-white tracking-wide">
              6. ORGANIZATIONAL AUTHORITY
            </h2>
          </div>
          <p className="text-sm text-neutral-300 leading-relaxed">
            The decision of the tournament administration (<strong className="text-white">minarathintememe</strong>)
            and official referees is final and binding on all matters of gameplay, scheduling, and disputes.
            Title sponsorship is proudly presented by <strong className="text-white">AKHADHA</strong>.
          </p>
        </div>
      </div>
    </div>
  );
};

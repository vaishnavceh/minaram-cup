import React from 'react';
import { Shield, Clock, Award, Users, AlertTriangle, CheckCircle } from 'lucide-react';

export const RulesPage: React.FC = () => {
  return (
    <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
      {/* Header */}
      <div className="mb-10 pb-6 border-b border-[#222222]">
        <div className="flex items-center space-x-2 text-xs font-mono uppercase tracking-widest text-brand-red mb-2">
          <Shield className="w-4 h-4" />
          <span>GOVERNANCE & FAIR PLAY</span>
        </div>
        <h1 className="font-display text-4xl sm:text-5xl text-white tracking-wider">
          OFFICIAL RULEBOOK
        </h1>
        <p className="text-sm text-neutral-400 mt-2">
          Rules and regulations governing the MINARAM CUP eFootball Championship.
          All participants must abide by these tournament directives.
        </p>
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

        {/* Section 3: Eligibility & Student Integrity */}
        <div className="bg-[#121212] border border-[#222222] rounded-lg p-6">
          <div className="flex items-center space-x-3 mb-4">
            <Users className="w-5 h-5 text-brand-red" />
            <h2 className="font-display text-2xl text-white tracking-wide">
              3. PLAYER ELIGIBILITY
            </h2>
          </div>
          <p className="text-sm text-neutral-300 leading-relaxed">
            All participating squad managers must be currently enrolled bona fide students of
            <strong> TKM College of Engineering</strong>. College identity verification may be requested
            prior to knockout stage matches. Impersonation or unauthorized subbing results in instant disqualification.
          </p>
        </div>

        {/* Section 4: Disconnections & Network Issues */}
        <div className="bg-[#121212] border border-[#222222] rounded-lg p-6">
          <div className="flex items-center space-x-3 mb-4">
            <AlertTriangle className="w-5 h-5 text-amber-500" />
            <h2 className="font-display text-2xl text-white tracking-wide">
              4. DISCONNECTIONS & DISPUTES
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

        {/* Section 5: Organizers & Sponsors */}
        <div className="bg-[#121212] border border-[#222222] rounded-lg p-6">
          <div className="flex items-center space-x-3 mb-4">
            <CheckCircle className="w-5 h-5 text-emerald-500" />
            <h2 className="font-display text-2xl text-white tracking-wide">
              5. ORGANIZATIONAL AUTHORITY
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

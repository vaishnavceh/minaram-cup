/**
 * Tournament configuration and constants for MINARAM CUP.
 * Update tournament dates, deadlines, and prize pools here in one centralized location.
 */

// Official registration deadline in ISO format with fixed IST offset (+05:30)
// Tuesday, 13 October 2026, 6:00 PM IST
export const REGISTRATION_DEADLINE = '2026-10-13T18:00:00+05:30';

export interface PrizeTier {
  id: string;
  place: number;
  label: string;
  title: string;
  amount: number;
  featured?: boolean;
}

export const PRIZE_POOL: PrizeTier[] = [
  {
    id: 'winner',
    place: 1,
    label: '1ST',
    title: 'WINNER',
    amount: 200,
    featured: true,
  },
  {
    id: 'runner_up',
    place: 2,
    label: '2ND',
    title: 'SECOND PLACE',
    amount: 100,
    featured: false,
  },
  {
    id: 'third_place',
    place: 3,
    label: '3RD',
    title: 'THIRD PLACE',
    amount: 50,
    featured: false,
  },
];

export const TOTAL_PRIZE_POOL = PRIZE_POOL.reduce((total, tier) => total + tier.amount, 0);

export interface GoldenBootEntry {
  rank: number;
  placeLabel: string;
  awardTitle: string;
  awardSub: string;
  playerName: string;
  teamName: string;
  groupName: string;
  goals: number;
  matchesPlayed: number;
  goalsPerMatch: number;
  featured?: boolean;
}

export const INITIAL_GOLDEN_BOOT_PODIUM: GoldenBootEntry[] = [
  {
    rank: 1,
    placeLabel: '1ST',
    awardTitle: 'GOLDEN BOOT WINNER',
    awardSub: 'TOURNAMENT TOP SCORER',
    playerName: 'Aromal',
    teamName: 'Fury FC',
    groupName: 'Group E',
    goals: 11,
    matchesPlayed: 2,
    goalsPerMatch: 5.5,
    featured: true,
  },
  {
    rank: 2,
    placeLabel: '2ND',
    awardTitle: 'SECOND PLACE',
    awardSub: 'SILVER BOOT',
    playerName: 'Brian',
    teamName: 'Zeltic Fc',
    groupName: 'Group L',
    goals: 10,
    matchesPlayed: 1,
    goalsPerMatch: 10.0,
    featured: false,
  },
  {
    rank: 3,
    placeLabel: '3RD',
    awardTitle: 'THIRD PLACE',
    awardSub: 'BRONZE BOOT',
    playerName: 'Akshay T Geevarghese',
    teamName: 'Imperium',
    groupName: 'Group B',
    goals: 8,
    matchesPlayed: 2,
    goalsPerMatch: 4.0,
    featured: false,
  },
];


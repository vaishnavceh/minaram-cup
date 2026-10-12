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

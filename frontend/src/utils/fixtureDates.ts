import { PublicMatch } from '../types';

const MONTH_NAMES_SHORT = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];
const MONTH_NAMES_UPPER = ['JAN', 'FEB', 'MAR', 'APR', 'MAY', 'JUN', 'JUL', 'AUG', 'SEP', 'OCT', 'NOV', 'DEC'];
const WEEKDAYS_SHORT = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'];

export interface MatchTimelineInfo {
  hasDates: boolean;
  startDateIso: string | null;
  endDateIso: string | null;
  startDateFormatted: string;       // e.g. "Wed, 14 Oct"
  endDateFormatted: string;         // e.g. "Sat, 17 Oct"
  startDateFull: string;            // e.g. "Wed, 14 Oct 2026"
  endDateFull: string;              // e.g. "Sat, 17 Oct 2026"
  windowCompact: string;            // e.g. "14 OCT ➔ 17 OCT"
  lastDayBadge: string;             // e.g. "LAST DAY: 17 OCT"
  lastDayFullBadge: string;         // e.g. "LAST DAY TO PLAY: 17 OCT"
  daysCount: number;
}

/**
 * Parses YYYY-MM-DD safely into local Date without UTC midnight timezone distortion.
 */
export function parseIsoDateSafe(dateStr?: string | null): Date | null {
  if (!dateStr) return null;
  const match = String(dateStr).match(/(\d{4})-(\d{2})-(\d{2})/);
  if (match) {
    const y = parseInt(match[1], 10);
    const m = parseInt(match[2], 10) - 1;
    const d = parseInt(match[3], 10);
    return new Date(y, m, d);
  }
  const parsed = new Date(dateStr);
  return isNaN(parsed.getTime()) ? null : parsed;
}

/**
 * Formats a Date object to "Wed, 14 Oct"
 */
export function formatShortDate(d: Date, includeYear = false): string {
  const weekday = WEEKDAYS_SHORT[d.getDay()];
  const month = MONTH_NAMES_SHORT[d.getMonth()];
  const day = d.getDate();
  return includeYear ? `${weekday}, ${day} ${month} ${d.getFullYear()}` : `${weekday}, ${day} ${month}`;
}

/**
 * Formats a Date object to "14 OCT"
 */
export function formatBadgeDate(d: Date): string {
  const month = MONTH_NAMES_UPPER[d.getMonth()];
  const day = d.getDate();
  return `${day} ${month}`;
}

/**
 * Extracts or computes the playing timeline window (Start Date to End Date / Last Day of Playing)
 * for any given match.
 */
export function getMatchTimeline(match: PublicMatch, defaultDaysPerMW = 3): MatchTimelineInfo {
  // 1. Resolve Start Date
  let startDateObj = parseIsoDateSafe(match.start_date || match.scheduled_date);

  // If date missing but round_number exists, estimate based on tournament base (2026-10-14)
  if (!startDateObj && match.round_number && match.round_number > 0) {
    const base = new Date(2026, 9, 14); // Oct 14, 2026
    base.setDate(base.getDate() + (match.round_number - 1) * defaultDaysPerMW);
    startDateObj = base;
  }

  // 2. Resolve End Date (Last Day to Play)
  let endDateObj = parseIsoDateSafe(match.end_date || match.scheduled_end_date);

  if (startDateObj && !endDateObj) {
    // End date is start date + matchweek duration (e.g. Oct 14 + 3 days = Oct 17)
    endDateObj = new Date(startDateObj.getTime());
    endDateObj.setDate(endDateObj.getDate() + defaultDaysPerMW);
  }

  if (!startDateObj || !endDateObj) {
    return {
      hasDates: false,
      startDateIso: null,
      endDateIso: null,
      startDateFormatted: 'Date TBA',
      endDateFormatted: 'Date TBA',
      startDateFull: 'Date TBA',
      endDateFull: 'Date TBA',
      windowCompact: 'WINDOW TBA',
      lastDayBadge: 'LAST DAY: TBA',
      lastDayFullBadge: 'LAST DAY TO PLAY: TBA',
      daysCount: defaultDaysPerMW,
    };
  }

  const sIso = startDateObj.toISOString().split('T')[0];
  const eIso = endDateObj.toISOString().split('T')[0];
  const sShort = formatShortDate(startDateObj, false);
  const eShort = formatShortDate(endDateObj, false);
  const sFull = formatShortDate(startDateObj, true);
  const eFull = formatShortDate(endDateObj, true);
  const sBadge = formatBadgeDate(startDateObj);
  const eBadge = formatBadgeDate(endDateObj);

  return {
    hasDates: true,
    startDateIso: sIso,
    endDateIso: eIso,
    startDateFormatted: sShort,
    endDateFormatted: eShort,
    startDateFull: sFull,
    endDateFull: eFull,
    windowCompact: `${sBadge} ➔ ${eBadge}`,
    lastDayBadge: `LAST DAY: ${eBadge}`,
    lastDayFullBadge: `LAST DAY TO PLAY: ${eBadge}`,
    daysCount: defaultDaysPerMW,
  };
}

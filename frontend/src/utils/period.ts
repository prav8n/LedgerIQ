// Shared period model used by the Dashboard, Analytics and module summaries.
// Granularity covers calendar month/quarter/year plus the Indian financial
// year (1 April → 31 March). A period is anchored by a (year, month) pair —
// "a date inside the period" — which mirrors how the backend resolves bounds.

export type Granularity = 'monthly' | 'quarterly' | 'yearly' | 'financial_year';

export interface PeriodState {
  granularity: Granularity;
  year: number;
  month: number; // 1-12, anchor month
}

export const MONTH_LABELS = [
  'January', 'February', 'March', 'April', 'May', 'June',
  'July', 'August', 'September', 'October', 'November', 'December',
];

const MONTH_ABBR = [
  'Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
  'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec',
];

export const GRANULARITY_OPTIONS: { value: Granularity; label: string }[] = [
  { value: 'monthly', label: 'Monthly' },
  { value: 'quarterly', label: 'Quarterly' },
  { value: 'yearly', label: 'Yearly' },
  { value: 'financial_year', label: 'Financial Year' },
];

export function defaultPeriod(granularity: Granularity = 'monthly'): PeriodState {
  const now = new Date();
  return { granularity, year: now.getFullYear(), month: now.getMonth() + 1 };
}

function addMonths(year: number, month: number, delta: number): { year: number; month: number } {
  const total = year * 12 + (month - 1) + delta;
  return { year: Math.floor(total / 12), month: (total % 12) + 1 };
}

/** Step to the previous (-1) or next (+1) period of the same granularity. */
export function shiftPeriod(p: PeriodState, dir: 1 | -1): PeriodState {
  const step: Record<Granularity, number> = {
    monthly: 1,
    quarterly: 3,
    yearly: 12,
    financial_year: 12,
  };
  const { year, month } = addMonths(p.year, p.month, dir * step[p.granularity]);
  return { ...p, year, month };
}

/** Start year of the Indian financial year containing the anchor. */
export function fyStartYear(p: { year: number; month: number }): number {
  return p.month >= 4 ? p.year : p.year - 1;
}

/** "FY 2025-26" from a financial-year start year. */
export function fyLabel(startYear: number): string {
  return `FY ${startYear}-${String((startYear + 1) % 100).padStart(2, '0')}`;
}

export function periodLabel(p: PeriodState): string {
  switch (p.granularity) {
    case 'monthly':
      return `${MONTH_LABELS[p.month - 1]} ${p.year}`;
    case 'quarterly': {
      const q = Math.floor((p.month - 1) / 3); // 0-3
      const s = q * 3;
      return `Q${q + 1} ${p.year} (${MONTH_ABBR[s]}–${MONTH_ABBR[s + 2]})`;
    }
    case 'yearly':
      return `${p.year}`;
    case 'financial_year':
      return fyLabel(fyStartYear(p));
  }
}

export interface PeriodQuery {
  period: Granularity;
  year: number;
  month: number;
}

/** Query params understood by the dashboard / analytics endpoints. */
export function periodQuery(p: PeriodState): PeriodQuery {
  return { period: p.granularity, year: p.year, month: p.month };
}

const iso = (y: number, m: number, d: number): string =>
  `${y}-${String(m).padStart(2, '0')}-${String(d).padStart(2, '0')}`;

const lastDay = (y: number, m: number): number => new Date(y, m, 0).getDate();

/** Inclusive ISO date bounds for client-side filtering (matches the backend). */
export function periodBounds(p: PeriodState): { start: string; end: string } {
  switch (p.granularity) {
    case 'monthly':
      return { start: iso(p.year, p.month, 1), end: iso(p.year, p.month, lastDay(p.year, p.month)) };
    case 'quarterly': {
      const q = Math.floor((p.month - 1) / 3);
      const sm = q * 3 + 1;
      const em = sm + 2;
      return { start: iso(p.year, sm, 1), end: iso(p.year, em, lastDay(p.year, em)) };
    }
    case 'yearly':
      return { start: iso(p.year, 1, 1), end: iso(p.year, 12, 31) };
    case 'financial_year': {
      const sy = fyStartYear(p);
      return { start: iso(sy, 4, 1), end: iso(sy + 1, 3, 31) };
    }
  }
}

/** True when the ISO date (YYYY-MM-DD) falls inside the period (inclusive). */
export function isInPeriod(isoDate: string, p: PeriodState): boolean {
  const { start, end } = periodBounds(p);
  return isoDate >= start && isoDate <= end;
}

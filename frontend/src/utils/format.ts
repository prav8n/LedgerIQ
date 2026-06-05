// Indian Rupee + locale formatting helpers.

const inr = new Intl.NumberFormat('en-IN', {
  style: 'currency',
  currency: 'INR',
  maximumFractionDigits: 0,
});

const inrCompact = new Intl.NumberFormat('en-IN', {
  notation: 'compact',
  maximumFractionDigits: 1,
});

export function toNumber(value: string | number | null | undefined): number {
  if (typeof value === 'number') return value;
  const n = Number(value ?? 0);
  return Number.isFinite(n) ? n : 0;
}

/** "₹1,23,456" */
export function formatINR(value: string | number | null | undefined): string {
  return inr.format(toNumber(value));
}

/** Compact form for axis ticks: "₹1.2L", "₹3Cr". */
export function formatINRCompact(value: string | number | null | undefined): string {
  return `₹${inrCompact.format(toNumber(value))}`;
}

/** "13.8%" */
export function formatPercent(
  value: string | number | null | undefined,
  digits = 1,
): string {
  return `${toNumber(value).toFixed(digits)}%`;
}

/** "+12.5%" / "-4.0%" with sign, for growth indicators. */
export function formatSignedPercent(value: number, digits = 1): string {
  const sign = value > 0 ? '+' : '';
  return `${sign}${value.toFixed(digits)}%`;
}

const dateFmt = new Intl.DateTimeFormat('en-IN', {
  day: '2-digit',
  month: 'short',
  year: 'numeric',
});

/** "03 Jun 2026" from an ISO date string. */
export function formatDate(iso: string | null | undefined): string {
  if (!iso) return '—';
  const d = new Date(iso);
  return Number.isNaN(d.getTime()) ? '—' : dateFmt.format(d);
}

/** Title-case a snake_case category/enum value: "credit_card" -> "Credit Card". */
export function humanize(value: string): string {
  return value
    .split('_')
    .map((w) => w.charAt(0).toUpperCase() + w.slice(1))
    .join(' ');
}

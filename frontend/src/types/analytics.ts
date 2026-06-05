export type AnalyticsPeriod = 'monthly' | 'quarterly' | 'yearly' | 'financial_year';

export interface PeriodKpis {
  income: string;
  expense: string;
  cashback: string;
  savings: string;
  savings_rate: number;
}

export interface TopCategory {
  category: string;
  amount: string;
  percent: number;
}

export interface BudgetAdherence {
  category: string;
  amount: string;
  spent: string;
  remaining: string;
  percent_used: number;
  status: 'green' | 'yellow' | 'red';
}

export interface CardCashback {
  card_id: number;
  card_name: string;
  spend: string;
  cashback_earned: string;
  effective_rate: number;
  cap: string | null;
  cap_used: string | null;
  cap_remaining: string | null;
}

export interface CashbackOptimization {
  total_cashback: string;
  by_card: CardCashback[];
}

export interface Growth {
  income: number;
  expense: number;
  savings: number;
  cashback: number;
}

export interface DateRange {
  start: string;
  end: string;
}

export interface AnalyticsResponse {
  period: AnalyticsPeriod;
  range: DateRange;
  kpis: PeriodKpis;
  previous: PeriodKpis;
  growth: Growth;
  top_categories: TopCategory[];
  budget_adherence: BudgetAdherence[];
  cashback_optimization: CashbackOptimization;
}

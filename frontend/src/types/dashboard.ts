// Money values arrive as strings (backend Decimal -> JSON string).

export interface DashboardKpis {
  income: string;
  expenses: string;
  effective_expense: string;
  cashback: string;
  cc_spend: string;
  savings: string;
  savings_rate: number;
  investments: string;
  net_worth: string;
}

export interface CategoryAmount {
  category: string;
  amount: string;
}

export interface FixedVariable {
  fixed: string;
  variable: string;
}

export interface MonthlyTrendPoint {
  label: string;
  income: string;
  expense: string;
  savings: string;
}

export interface SavingsTrendPoint {
  label: string;
  savings: string;
}

export interface CashbackTrendPoint {
  label: string;
  cashback: string;
}

export interface InvestmentTrendPoint {
  label: string;
  invested: string;
}

export interface CreditCardWidget {
  card_id: number;
  card_name: string;
  issuer: string;
  network: string;
  last_four: string | null;
  card_color: string | null;
  credit_limit: string;
  current_balance: string;
  available_credit: string;
  utilization_percent: number;
  spend_this_month: string;
  cashback_this_month: string;
  cashback_cap: string | null;
  cashback_cap_used: string | null;
  cashback_cap_remaining: string | null;
}

export interface DashboardResponse {
  month: string;
  kpis: DashboardKpis;
  expense_by_category: CategoryAmount[];
  fixed_vs_variable: FixedVariable;
  credit_cards: CreditCardWidget[];
  monthly_trend: MonthlyTrendPoint[];
  savings_trend: SavingsTrendPoint[];
  cashback_trend: CashbackTrendPoint[];
  investment_trend: InvestmentTrendPoint[];
}

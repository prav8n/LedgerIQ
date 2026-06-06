// Read types use string for money (backend Decimal -> JSON string).
// Create/Update use number for money (sent as JSON numbers).

// ---------------- Income ----------------
export interface Income {
  id: number;
  source: string;
  amount: string;
  category: string;
  frequency: string;
  received_date: string;
  is_recurring: boolean;
  is_taxable: boolean;
  notes: string | null;
  created_at: string;
  updated_at: string;
}
export interface IncomeInput {
  source: string;
  amount: number;
  category: string;
  frequency?: string;
  received_date: string;
  is_recurring?: boolean;
  is_taxable?: boolean;
  notes?: string | null;
}

// ---------------- Credit cards & reward rules ----------------
export interface RewardRule {
  id: number;
  card_id: number;
  rule_name: string;
  reward_type: string;
  reward_rate: string;
  point_value: string | null;
  applies_to: string;
  merchant_match: string | null;
  category_match: string | null;
  min_txn_amount: string | null;
  monthly_cap: string | null;
  milestone_threshold: string | null;
  milestone_reward: string | null;
  notes: string | null;
}
export interface RewardRuleInput {
  rule_name: string;
  reward_type: string;
  reward_rate: number;
  point_value?: number | null;
  applies_to: string;
  merchant_match?: string | null;
  category_match?: string | null;
  min_txn_amount?: number | null;
  monthly_cap?: number | null;
  milestone_threshold?: number | null;
  milestone_reward?: number | null;
  notes?: string | null;
}
export interface RuleEarning {
  rule_id: number;
  rule_name: string;
  reward_type: string;
  reward_units: string;
  reward_value_inr: string;
  monthly_cap: string | null;
  capped: boolean;
}
export interface MilestoneProgress {
  rule_id: number;
  rule_name: string;
  threshold: string;
  progress: string;
  reward: string | null;
  met: boolean;
  percent: number;
}
export interface FeeWaiverProgress {
  threshold: string;
  spent: string;
  met: boolean;
  percent: number;
}
export interface CardRewardSummary {
  month_label: string;
  month_spend: string;
  total_reward_value_inr: string;
  earnings: RuleEarning[];
  milestones: MilestoneProgress[];
  fee_waiver: FeeWaiverProgress | null;
  benefits: string[];
}
export interface CreditCard {
  id: number;
  card_name: string;
  issuer: string;
  network: string;
  last_four: string | null;
  card_color: string | null;
  credit_limit: string;
  current_balance: string;
  statement_day: number | null;
  due_day: number | null;
  billing_cycle_day: number | null;
  interest_rate: string | null;
  annual_fee: string;
  fee_waiver_spend_threshold: string | null;
  reward_type: string;
  reward_rate: string;
  valid_thru: string | null;
  is_active: boolean;
  reward_rules: RewardRule[];
  available_credit: string;
  utilization_percent: number;
  next_statement_date: string | null;
  next_due_date: string | null;
  reward_summary: CardRewardSummary;
}
export interface CreditCardInput {
  card_name: string;
  issuer: string;
  network?: string;
  last_four?: string | null;
  card_color?: string | null;
  credit_limit?: number;
  current_balance?: number;
  statement_day?: number | null;
  due_day?: number | null;
  billing_cycle_day?: number | null;
  annual_fee?: number;
  fee_waiver_spend_threshold?: number | null;
  is_active?: boolean;
  reward_rules?: RewardRuleInput[];
}

// ---------------- Budgets ----------------
export interface Budget {
  id: number;
  category: string;
  amount: string;
  period: string;
  spent: string;
  start_date: string;
  end_date: string | null;
  rollover: boolean;
  is_active: boolean;
  remaining: string;
  percent_used: number;
  status: 'green' | 'yellow' | 'red';
}
export interface BudgetInput {
  category: string;
  amount: number;
  period: string;
  start_date: string;
  end_date?: string | null;
  is_active?: boolean;
}

// ---------------- Goals ----------------
export interface Goal {
  id: number;
  name: string;
  description: string | null;
  category: string;
  target_amount: string;
  current_amount: string;
  monthly_contribution: string;
  target_date: string | null;
  priority: string;
  status: string;
  icon: string | null;
  color: string | null;
  remaining: string;
  progress_percent: number;
  required_monthly_contribution: string;
}
export interface GoalInput {
  name: string;
  category: string;
  target_amount: number;
  current_amount?: number;
  monthly_contribution?: number;
  target_date?: string | null;
  priority?: string;
  status?: string;
}

// ---------------- Investments ----------------
export interface Investment {
  id: number;
  name: string;
  investment_type: string;
  platform: string | null;
  symbol: string | null;
  invested_amount: string;
  current_value: string;
  units: string | null;
  avg_buy_price: string | null;
  interest_rate: string | null;
  purchase_date: string | null;
  maturity_date: string | null;
  notes: string | null;
  returns_value: string;
  returns_percent: number;
}
export interface InvestmentInput {
  name: string;
  investment_type: string;
  platform?: string | null;
  invested_amount: number;
  current_value?: number;
  purchase_date?: string | null;
}
export interface PortfolioTypeBreakdown {
  investment_type: string;
  invested_amount: string;
  current_value: string;
  returns_value: string;
  returns_percent: number;
}
export interface PortfolioSummary {
  total_invested: string;
  total_current_value: string;
  total_returns: string;
  total_returns_percent: number;
  by_type: PortfolioTypeBreakdown[];
}

// ---------------- Subscriptions ----------------
export interface Subscription {
  id: number;
  name: string;
  category: string;
  amount: string;
  billing_cycle: string;
  start_date: string;
  next_billing_date: string;
  payment_method: string;
  reminder_days: number;
  auto_renew: boolean;
  is_active: boolean;
  monthly_cost: string;
  yearly_cost: string;
}
export interface SubscriptionInput {
  name: string;
  category: string;
  amount: number;
  billing_cycle: string;
  start_date: string;
  next_billing_date: string;
  payment_method?: string;
  reminder_days?: number;
  auto_renew?: boolean;
  is_active?: boolean;
}
export interface SubscriptionSummary {
  active_count: number;
  total_monthly_cost: string;
  total_yearly_cost: string;
}

// ---------------- EMIs ----------------
export interface EMI {
  id: number;
  loan_name: string;
  loan_type: string;
  lender: string | null;
  principal_amount: string;
  emi_amount: string;
  interest_rate: string;
  tenure_months: number;
  months_paid: number;
  start_date: string;
  next_due_date: string;
  total_payable: string | null;
  amount_paid: string;
  is_active: boolean;
  outstanding: string;
  remaining_months: number;
  progress_percent: number;
}
export interface EMIInput {
  loan_name: string;
  loan_type: string;
  lender?: string | null;
  principal_amount: number;
  emi_amount?: number;
  interest_rate: number;
  tenure_months: number;
  start_date: string;
  next_due_date: string;
}

// ---------------- Net Worth ----------------
export interface NetWorth {
  cash: string;
  investments_value: string;
  property_value: string;
  other_assets: string;
  credit_card_debt: string;
  loans_debt: string;
  other_liabilities: string;
  total_assets: string;
  total_liabilities: string;
  net_worth: string;
}
export interface NetWorthSnapshot extends NetWorth {
  id: number;
  snapshot_date: string;
  created_at: string;
}
export interface NetWorthSnapshotInput {
  cash?: number;
  property_value?: number;
  other_assets?: number;
  other_liabilities?: number;
  snapshot_date?: string | null;
}

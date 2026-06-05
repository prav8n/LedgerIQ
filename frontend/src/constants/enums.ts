// Option lists mirroring the backend string enums (value === API value).
import { humanize } from '@/utils/format';

export interface Option {
  value: string;
  label: string;
}

const opts = (values: string[]): Option[] =>
  values.map((v) => ({ value: v, label: humanize(v) }));

export const incomeCategories = opts([
  'salary', 'bonus', 'freelance', 'business', 'rental', 'interest',
  'dividend', 'capital_gains', 'gift', 'refund', 'other',
]);

export const expenseCategories = opts([
  'food', 'groceries', 'transport', 'shopping', 'entertainment', 'utilities',
  'rent', 'health', 'education', 'travel', 'insurance', 'investment', 'emi',
  'subscription', 'personal_care', 'gifts', 'taxes', 'fees', 'other',
]);

export const paymentMethods = opts([
  'cash', 'upi', 'debit_card', 'credit_card', 'net_banking', 'wallet',
  'auto_debit', 'other',
]);

export const frequencies = opts([
  'one_time', 'daily', 'weekly', 'monthly', 'quarterly', 'yearly',
]);

export const cardNetworks = opts(['visa', 'mastercard', 'rupay', 'amex', 'diners', 'other']);
export const cardRewardTypes = opts(['cashback', 'points', 'miles', 'none']);
export const budgetPeriods = opts(['weekly', 'monthly', 'quarterly', 'yearly']);

export const goalCategories = opts([
  'emergency_fund', 'vacation', 'home', 'car', 'education', 'wedding',
  'gadget', 'retirement', 'investment', 'other',
]);
export const goalStatuses = opts(['active', 'completed', 'paused', 'abandoned']);
export const priorities = opts(['low', 'medium', 'high']);

export const investmentTypes = opts([
  'stocks', 'mutual_funds', 'etf', 'fixed_deposit', 'recurring_deposit',
  'ppf', 'epf', 'nps', 'bonds', 'gold', 'real_estate', 'crypto', 'other',
]);

export const subscriptionCategories = opts([
  'streaming', 'music', 'software', 'cloud', 'news', 'fitness', 'gaming',
  'utilities', 'education', 'other',
]);

export const loanTypes = opts([
  'home', 'car', 'personal', 'education', 'business', 'gold', 'credit_card', 'other',
]);

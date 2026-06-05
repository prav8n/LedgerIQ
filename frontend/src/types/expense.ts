export interface Expense {
  id: number;
  amount: string;
  category: string;
  subcategory: string | null;
  merchant: string | null;
  description: string | null;
  payment_method: string;
  transaction_date: string;
  credit_card_id: number | null;
  is_online: boolean;
  is_recurring: boolean;
  is_ai_categorized: boolean;
  cashback_eligible: boolean;
  cashback_amount: string;
  cashback_type: string | null;
  cashback_rule: string | null;
  created_at: string;
  updated_at: string;
}

export interface ExpenseInput {
  amount: number;
  category?: string | null;
  merchant?: string | null;
  description?: string | null;
  payment_method: string;
  transaction_date: string;
  credit_card_id?: number | null;
  is_online?: boolean;
  is_recurring?: boolean;
  notes?: string | null;
}

export interface PaginatedExpenses {
  items: Expense[];
  total: number;
  page: number;
  size: number;
  pages: number;
}

export interface ExpenseFilters {
  page?: number;
  size?: number;
  q?: string;
  category?: string;
  payment_method?: string;
  date_from?: string;
  date_to?: string;
}

import { api } from '@/services/api';
import type {
  Expense,
  ExpenseFilters,
  ExpenseInput,
  PaginatedExpenses,
} from '@/types/expense';

export const expenseService = {
  list: async (filters?: ExpenseFilters): Promise<PaginatedExpenses> =>
    (await api.get<PaginatedExpenses>('/expenses', { params: filters })).data,
  create: async (body: ExpenseInput): Promise<Expense> =>
    (await api.post<Expense>('/expenses', body)).data,
  update: async (id: number, body: Partial<ExpenseInput>): Promise<Expense> =>
    (await api.put<Expense>(`/expenses/${id}`, body)).data,
  remove: async (id: number): Promise<void> => {
    await api.delete(`/expenses/${id}`);
  },
};

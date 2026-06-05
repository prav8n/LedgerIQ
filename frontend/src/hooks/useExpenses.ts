import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { expenseService } from '@/services/expenseService';
import type { ExpenseFilters, ExpenseInput, PaginatedExpenses } from '@/types/expense';

export function useExpenses(filters: ExpenseFilters) {
  return useQuery<PaginatedExpenses>({
    queryKey: ['expenses', filters],
    queryFn: () => expenseService.list(filters),
  });
}

function invalidate(qc: ReturnType<typeof useQueryClient>) {
  void qc.invalidateQueries({ queryKey: ['expenses'] });
  void qc.invalidateQueries({ queryKey: ['dashboard'] });
}

export function useCreateExpense() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (body: ExpenseInput) => expenseService.create(body),
    onSuccess: () => invalidate(qc),
  });
}

export function useUpdateExpense() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (vars: { id: number; body: Partial<ExpenseInput> }) =>
      expenseService.update(vars.id, vars.body),
    onSuccess: () => invalidate(qc),
  });
}

export function useDeleteExpense() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (id: number) => expenseService.remove(id),
    onSuccess: () => invalidate(qc),
  });
}

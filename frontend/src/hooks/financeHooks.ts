import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { createCrudHooks } from '@/hooks/createCrudHooks';
import {
  budgetService,
  emiService,
  goalService,
  incomeService,
  investmentService,
  networthService,
  subscriptionService,
} from '@/services/financeServices';
import type {
  Budget,
  BudgetInput,
  EMI,
  EMIInput,
  Goal,
  GoalInput,
  Income,
  IncomeInput,
  Investment,
  InvestmentInput,
  NetWorth,
  NetWorthSnapshot,
  NetWorthSnapshotInput,
  PortfolioSummary,
  Subscription,
  SubscriptionInput,
  SubscriptionSummary,
} from '@/types/finance';

// ---- CRUD hook bundles ----
export const incomeHooks = createCrudHooks<Income, IncomeInput, Partial<IncomeInput>>(
  'income',
  incomeService,
);
export const budgetHooks = createCrudHooks<Budget, BudgetInput, Partial<BudgetInput>>(
  'budgets',
  budgetService,
);
export const goalHooks = createCrudHooks<Goal, GoalInput, Partial<GoalInput>>(
  'goals',
  goalService,
);
export const investmentHooks = createCrudHooks<
  Investment,
  InvestmentInput,
  Partial<InvestmentInput>
>('investments', investmentService);
export const subscriptionHooks = createCrudHooks<
  Subscription,
  SubscriptionInput,
  Partial<SubscriptionInput>
>('subscriptions', subscriptionService);
export const emiHooks = createCrudHooks<EMI, EMIInput, Partial<EMIInput>>('emis', emiService);

// ---- Income mutations ----
// Income feeds the Dashboard "Income" KPI and the Savings = Income − Expenses
// calculation, so every mutation also refreshes those derived views.
function useInvalidateIncome() {
  const qc = useQueryClient();
  return () => {
    void qc.invalidateQueries({ queryKey: ['income'] });
    void qc.invalidateQueries({ queryKey: ['dashboard'] });
    void qc.invalidateQueries({ queryKey: ['analytics'] });
  };
}

export function useCreateIncome() {
  const invalidate = useInvalidateIncome();
  return useMutation({
    mutationFn: (body: IncomeInput) => incomeService.create(body),
    onSuccess: invalidate,
  });
}

export function useUpdateIncome() {
  const invalidate = useInvalidateIncome();
  return useMutation({
    mutationFn: (vars: { id: number; body: Partial<IncomeInput> }) =>
      incomeService.update(vars.id, vars.body),
    onSuccess: invalidate,
  });
}

export function useRemoveIncome() {
  const invalidate = useInvalidateIncome();
  return useMutation({
    mutationFn: (id: number) => incomeService.remove(id),
    onSuccess: invalidate,
  });
}

// ---- Custom actions / aggregates ----
export function useGoalContribute() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (vars: { id: number; amount: number }) =>
      goalService.contribute(vars.id, vars.amount),
    onSuccess: () => void qc.invalidateQueries({ queryKey: ['goals'] }),
  });
}

export function usePortfolioSummary() {
  return useQuery<PortfolioSummary>({
    queryKey: ['investments', 'summary'],
    queryFn: () => investmentService.summary(),
  });
}

export function useSubscriptionSummary() {
  return useQuery<SubscriptionSummary>({
    queryKey: ['subscriptions', 'summary'],
    queryFn: () => subscriptionService.summary(),
  });
}

export function useEmiPay() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (id: number) => emiService.pay(id),
    onSuccess: () => void qc.invalidateQueries({ queryKey: ['emis'] }),
  });
}

export function useNetWorthCurrent() {
  return useQuery<NetWorth>({
    queryKey: ['net-worth', 'current'],
    queryFn: () => networthService.current(),
  });
}

export function useNetWorthHistory() {
  return useQuery<NetWorthSnapshot[]>({
    queryKey: ['net-worth', 'history'],
    queryFn: () => networthService.history(),
  });
}

export function useNetWorthSnapshot() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (body: NetWorthSnapshotInput) => networthService.snapshot(body),
    onSuccess: () => void qc.invalidateQueries({ queryKey: ['net-worth'] }),
  });
}

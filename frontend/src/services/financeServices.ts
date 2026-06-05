import { api } from '@/services/api';
import { makeCrudService } from '@/services/crud';
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

export const incomeService = makeCrudService<Income, IncomeInput, Partial<IncomeInput>>(
  '/income',
);

export const budgetService = makeCrudService<Budget, BudgetInput, Partial<BudgetInput>>(
  '/budgets',
);

export const goalService = {
  ...makeCrudService<Goal, GoalInput, Partial<GoalInput>>('/goals'),
  contribute: async (id: number, amount: number): Promise<Goal> =>
    (await api.post<Goal>(`/goals/${id}/contribute`, { amount })).data,
};

export const investmentService = {
  ...makeCrudService<Investment, InvestmentInput, Partial<InvestmentInput>>('/investments'),
  summary: async (): Promise<PortfolioSummary> =>
    (await api.get<PortfolioSummary>('/investments/summary')).data,
};

export const subscriptionService = {
  ...makeCrudService<Subscription, SubscriptionInput, Partial<SubscriptionInput>>(
    '/subscriptions',
  ),
  summary: async (): Promise<SubscriptionSummary> =>
    (await api.get<SubscriptionSummary>('/subscriptions/summary')).data,
};

export const emiService = {
  ...makeCrudService<EMI, EMIInput, Partial<EMIInput>>('/emis'),
  pay: async (id: number): Promise<EMI> =>
    (await api.post<EMI>(`/emis/${id}/pay`)).data,
};

export const networthService = {
  current: async (): Promise<NetWorth> =>
    (await api.get<NetWorth>('/net-worth/current')).data,
  history: async (): Promise<NetWorthSnapshot[]> =>
    (await api.get<NetWorthSnapshot[]>('/net-worth')).data,
  snapshot: async (body: NetWorthSnapshotInput): Promise<NetWorthSnapshot> =>
    (await api.post<NetWorthSnapshot>('/net-worth/snapshot', body)).data,
  remove: async (id: number): Promise<void> => {
    await api.delete(`/net-worth/${id}`);
  },
};

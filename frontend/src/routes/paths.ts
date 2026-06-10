export const paths = {
  login: '/login',
  register: '/register',
  dashboard: '/dashboard',
  income: '/income',
  expenses: '/expenses',
  creditCards: '/credit-cards',
  budgets: '/budgets',
  goals: '/goals',
  investments: '/investments',
  subscriptions: '/subscriptions',
  emis: '/emis',
  netWorth: '/net-worth',
  notifications: '/notifications',
  analytics: '/analytics',
  settings: '/settings',
} as const;

export type AppPath = (typeof paths)[keyof typeof paths];

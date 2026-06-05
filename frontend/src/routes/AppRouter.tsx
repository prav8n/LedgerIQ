import { Navigate, Route, Routes } from 'react-router-dom';
import { PrivateRoute } from '@/routes/PrivateRoute';
import { MainLayout } from '@/layouts/MainLayout';
import { paths } from '@/routes/paths';

import { LoginPage } from '@/pages/auth/LoginPage';
import { RegisterPage } from '@/pages/auth/RegisterPage';
import { DashboardPage } from '@/pages/DashboardPage';
import { IncomePage } from '@/pages/IncomePage';
import { ExpensesPage } from '@/pages/ExpensesPage';
import { CreditCardsPage } from '@/pages/CreditCardsPage';
import { BudgetsPage } from '@/pages/BudgetsPage';
import { GoalsPage } from '@/pages/GoalsPage';
import { InvestmentsPage } from '@/pages/InvestmentsPage';
import { SubscriptionsPage } from '@/pages/SubscriptionsPage';
import { EMIsPage } from '@/pages/EMIsPage';
import { NetWorthPage } from '@/pages/NetWorthPage';
import { NotificationsPage } from '@/pages/NotificationsPage';
import { AnalyticsPage } from '@/pages/AnalyticsPage';
import { NotFoundPage } from '@/pages/NotFoundPage';

export function AppRouter() {
  return (
    <Routes>
      {/* Public */}
      <Route path={paths.login} element={<LoginPage />} />
      <Route path={paths.register} element={<RegisterPage />} />

      {/* Protected */}
      <Route element={<PrivateRoute />}>
        <Route element={<MainLayout />}>
          <Route index element={<Navigate to={paths.dashboard} replace />} />
          <Route path={paths.dashboard} element={<DashboardPage />} />
          <Route path={paths.income} element={<IncomePage />} />
          <Route path={paths.expenses} element={<ExpensesPage />} />
          <Route path={paths.creditCards} element={<CreditCardsPage />} />
          <Route path={paths.budgets} element={<BudgetsPage />} />
          <Route path={paths.goals} element={<GoalsPage />} />
          <Route path={paths.investments} element={<InvestmentsPage />} />
          <Route path={paths.subscriptions} element={<SubscriptionsPage />} />
          <Route path={paths.emis} element={<EMIsPage />} />
          <Route path={paths.netWorth} element={<NetWorthPage />} />
          <Route path={paths.notifications} element={<NotificationsPage />} />
          <Route path={paths.analytics} element={<AnalyticsPage />} />
        </Route>
      </Route>

      <Route path="*" element={<NotFoundPage />} />
    </Routes>
  );
}

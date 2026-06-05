import { useState } from 'react';
import { Box, Stack, Typography } from '@mui/material';
import PaymentsRoundedIcon from '@mui/icons-material/PaymentsRounded';
import ReceiptLongRoundedIcon from '@mui/icons-material/ReceiptLongRounded';
import RedeemRoundedIcon from '@mui/icons-material/RedeemRounded';
import SavingsRoundedIcon from '@mui/icons-material/SavingsRounded';
import PercentRoundedIcon from '@mui/icons-material/PercentRounded';
import TrendingUpRoundedIcon from '@mui/icons-material/TrendingUpRounded';
import AccountBalanceRoundedIcon from '@mui/icons-material/AccountBalanceRounded';

import { useDashboard } from '@/hooks/useDashboard';
import { useChartColors } from '@/components/charts/useChartColors';
import { LoadingSkeleton } from '@/components/LoadingSkeleton';
import { EmptyState } from '@/components/EmptyState';
import { KpiCard } from '@/components/dashboard/KpiCard';
import { InsightsSection } from '@/components/dashboard/InsightsSection';
import { CreditCardWidgetCard } from '@/components/dashboard/CreditCardWidgetCard';
import { ChartCard } from '@/components/charts/ChartCard';
import { ExpenseCategoryPie } from '@/components/charts/ExpenseCategoryPie';
import { FixedVsVariableBar } from '@/components/charts/FixedVsVariableBar';
import { TrendChart } from '@/components/charts/TrendChart';
import { PeriodSelector } from '@/components/PeriodSelector';
import { defaultPeriod, type PeriodState } from '@/utils/period';
import { formatINR, formatPercent, toNumber } from '@/utils/format';

export function DashboardPage() {
  const [period, setPeriod] = useState<PeriodState>(defaultPeriod('monthly'));
  const { data, isLoading, isError, refetch } = useDashboard(6, period.year, period.month);
  const colors = useChartColors();

  const header = (
    <Stack
      direction={{ xs: 'column', sm: 'row' }}
      justifyContent="space-between"
      alignItems={{ xs: 'stretch', sm: 'center' }}
      spacing={2}
      mb={3}
    >
      <Box>
        <Typography variant="h4">Dashboard</Typography>
        <Typography variant="body2" color="text.secondary">
          {data ? `${data.month} overview` : 'Loading…'}
        </Typography>
      </Box>
      <PeriodSelector value={period} onChange={setPeriod} granularities={['monthly']} />
    </Stack>
  );

  if (isLoading || !data) {
    return (
      <Box>
        {header}
        {isError ? (
          <EmptyState
            title="Couldn't load your dashboard"
            description="There was a problem fetching your data."
            actionLabel="Retry"
            onAction={() => void refetch()}
          />
        ) : (
          <LoadingSkeleton cards={4} rows={4} />
        )}
      </Box>
    );
  }

  const k = data.kpis;
  const monthly = data.monthly_trend.map((p) => ({
    label: p.label,
    income: toNumber(p.income),
    expense: toNumber(p.expense),
    savings: toNumber(p.savings),
  }));
  const savings = data.savings_trend.map((p) => ({ label: p.label, savings: toNumber(p.savings) }));
  const cashback = data.cashback_trend.map((p) => ({
    label: p.label,
    cashback: toNumber(p.cashback),
  }));
  const investment = data.investment_trend.map((p) => ({
    label: p.label,
    invested: toNumber(p.invested),
  }));

  return (
    <Box>
      {header}

      {/* KPIs */}
      <Box
        sx={{
          display: 'grid',
          gap: 2,
          gridTemplateColumns: { xs: '1fr 1fr', sm: 'repeat(3, 1fr)', lg: 'repeat(4, 1fr)' },
          mb: 3,
        }}
      >
        <KpiCard title="Income" value={formatINR(k.income)} icon={<PaymentsRoundedIcon />} accent="success.main" />
        <KpiCard title="Expenses" value={formatINR(k.expenses)} icon={<ReceiptLongRoundedIcon />} accent="error.main" />
        <KpiCard title="Cashback" value={formatINR(k.cashback)} icon={<RedeemRoundedIcon />} accent="secondary.main" />
        <KpiCard
          title="Savings"
          value={formatINR(k.savings)}
          icon={<SavingsRoundedIcon />}
          accent="primary.main"
          caption={`Rate ${formatPercent(k.savings_rate)}`}
        />
        <KpiCard title="Savings Rate" value={formatPercent(k.savings_rate)} icon={<PercentRoundedIcon />} accent="info.main" />
        <KpiCard title="Investments" value={formatINR(k.investments)} icon={<TrendingUpRoundedIcon />} accent="secondary.main" />
        <KpiCard title="Net Worth" value={formatINR(k.net_worth)} icon={<AccountBalanceRoundedIcon />} accent="primary.main" />
      </Box>

      {/* AI Insights */}
      <InsightsSection />

      {/* Charts */}
      <Box
        sx={{
          display: 'grid',
          gap: 2,
          gridTemplateColumns: { xs: '1fr', md: '1fr 1fr' },
          mb: 3,
        }}
      >
        <ChartCard title="Expenses by Category">
          <ExpenseCategoryPie items={data.expense_by_category} />
        </ChartCard>
        <ChartCard title="Fixed vs Variable">
          <FixedVsVariableBar data={data.fixed_vs_variable} />
        </ChartCard>
        <ChartCard title="Monthly Trend">
          <TrendChart
            data={monthly}
            variant="line"
            series={[
              { key: 'income', name: 'Income', color: colors.success },
              { key: 'expense', name: 'Expense', color: colors.error },
              { key: 'savings', name: 'Savings', color: colors.primary },
            ]}
          />
        </ChartCard>
        <ChartCard title="Savings Trend">
          <TrendChart
            data={savings}
            variant="area"
            showLegend={false}
            series={[{ key: 'savings', name: 'Savings', color: colors.primary }]}
          />
        </ChartCard>
        <ChartCard title="Cashback Trend">
          <TrendChart
            data={cashback}
            variant="area"
            showLegend={false}
            series={[{ key: 'cashback', name: 'Cashback', color: colors.secondary }]}
          />
        </ChartCard>
        <ChartCard title="Investment Trend">
          <TrendChart
            data={investment}
            variant="area"
            showLegend={false}
            series={[{ key: 'invested', name: 'Invested', color: colors.info }]}
          />
        </ChartCard>
      </Box>

      {/* Credit cards */}
      <Stack direction="row" alignItems="center" justifyContent="space-between" mb={1.5}>
        <Typography variant="h5">Credit Cards</Typography>
      </Stack>
      {data.credit_cards.length === 0 ? (
        <EmptyState title="No credit cards yet" description="Add a card to track spend, cashback and utilization." />
      ) : (
        <Box
          sx={{
            display: 'grid',
            gap: 2,
            gridTemplateColumns: { xs: '1fr', sm: '1fr 1fr', lg: 'repeat(3, 1fr)' },
          }}
        >
          {data.credit_cards.map((card) => (
            <CreditCardWidgetCard key={card.card_id} card={card} />
          ))}
        </Box>
      )}
    </Box>
  );
}

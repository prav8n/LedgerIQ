import { useState } from 'react';
import {
  Box,
  Card,
  CardContent,
  Divider,
  LinearProgress,
  Stack,
  Typography,
} from '@mui/material';
import PaymentsRoundedIcon from '@mui/icons-material/PaymentsRounded';
import ReceiptLongRoundedIcon from '@mui/icons-material/ReceiptLongRounded';
import SavingsRoundedIcon from '@mui/icons-material/SavingsRounded';
import RedeemRoundedIcon from '@mui/icons-material/RedeemRounded';

import { useAnalytics } from '@/hooks/useAnalytics';
import { LoadingSkeleton } from '@/components/LoadingSkeleton';
import { EmptyState } from '@/components/EmptyState';
import { KpiCard } from '@/components/dashboard/KpiCard';
import { PeriodSelector } from '@/components/PeriodSelector';
import { defaultPeriod, periodLabel, type PeriodState } from '@/utils/period';
import { formatINR, formatPercent, humanize } from '@/utils/format';
import type { BudgetAdherence } from '@/types/analytics';

const statusColor: Record<BudgetAdherence['status'], 'success' | 'warning' | 'error'> = {
  green: 'success',
  yellow: 'warning',
  red: 'error',
};

export function AnalyticsPage() {
  const [period, setPeriod] = useState<PeriodState>(defaultPeriod('monthly'));
  const { data, isLoading, isError, refetch } = useAnalytics(period);

  return (
    <Box>
      <Stack
        direction={{ xs: 'column', sm: 'row' }}
        justifyContent="space-between"
        alignItems={{ xs: 'flex-start', sm: 'center' }}
        spacing={2}
        mb={3}
      >
        <Box>
          <Typography variant="h4">Analytics</Typography>
          <Typography variant="body2" color="text.secondary">
            {periodLabel(period)}
            {data ? ` · ${data.range.start} → ${data.range.end}` : ''}
          </Typography>
        </Box>
        <PeriodSelector value={period} onChange={setPeriod} />
      </Stack>

      {isLoading && <LoadingSkeleton cards={4} rows={5} />}

      {!isLoading && (isError || !data) && (
        <EmptyState
          title="Couldn't load analytics"
          description="There was a problem fetching your data."
          actionLabel="Retry"
          onAction={() => void refetch()}
        />
      )}

      {!isLoading && data && (
        <>
          {/* KPIs with period-over-period growth */}
          <Box
            sx={{
              display: 'grid',
              gap: 2,
              gridTemplateColumns: { xs: '1fr 1fr', md: 'repeat(4, 1fr)' },
              mb: 3,
            }}
          >
            <KpiCard
              title="Income"
              value={formatINR(data.kpis.income)}
              icon={<PaymentsRoundedIcon />}
              accent="success.main"
              delta={data.growth.income}
            />
            <KpiCard
              title="Expenses"
              value={formatINR(data.kpis.expense)}
              icon={<ReceiptLongRoundedIcon />}
              accent="error.main"
              delta={data.growth.expense}
            />
            <KpiCard
              title="Savings"
              value={formatINR(data.kpis.savings)}
              icon={<SavingsRoundedIcon />}
              accent="primary.main"
              delta={data.growth.savings}
              caption={`Rate ${formatPercent(data.kpis.savings_rate)}`}
            />
            <KpiCard
              title="Cashback"
              value={formatINR(data.kpis.cashback)}
              icon={<RedeemRoundedIcon />}
              accent="secondary.main"
              delta={data.growth.cashback}
            />
          </Box>

          <Box
            sx={{
              display: 'grid',
              gap: 2,
              gridTemplateColumns: { xs: '1fr', md: '1fr 1fr' },
            }}
          >
            {/* Top categories */}
            <Card>
              <CardContent>
                <Typography variant="h6" mb={2}>
                  Top Categories
                </Typography>
                {data.top_categories.length === 0 ? (
                  <Typography variant="body2" color="text.secondary">
                    No spending in this period.
                  </Typography>
                ) : (
                  <Stack spacing={2}>
                    {data.top_categories.map((c) => (
                      <Box key={c.category}>
                        <Stack direction="row" justifyContent="space-between" mb={0.5}>
                          <Typography variant="body2">{humanize(c.category)}</Typography>
                          <Typography variant="body2" fontWeight={700}>
                            {formatINR(c.amount)} · {formatPercent(c.percent)}
                          </Typography>
                        </Stack>
                        <LinearProgress
                          variant="determinate"
                          value={Math.min(c.percent, 100)}
                          sx={{ height: 8, borderRadius: 4 }}
                        />
                      </Box>
                    ))}
                  </Stack>
                )}
              </CardContent>
            </Card>

            {/* Budget adherence */}
            <Card>
              <CardContent>
                <Typography variant="h6" mb={2}>
                  Budget Adherence
                </Typography>
                {data.budget_adherence.length === 0 ? (
                  <Typography variant="body2" color="text.secondary">
                    No active budgets.
                  </Typography>
                ) : (
                  <Stack spacing={2}>
                    {data.budget_adherence.map((b) => (
                      <Box key={b.category}>
                        <Stack direction="row" justifyContent="space-between" mb={0.5}>
                          <Typography variant="body2">{humanize(b.category)}</Typography>
                          <Typography variant="body2" fontWeight={700}>
                            {formatINR(b.spent)} / {formatINR(b.amount)}
                          </Typography>
                        </Stack>
                        <LinearProgress
                          variant="determinate"
                          value={Math.min(b.percent_used, 100)}
                          color={statusColor[b.status]}
                          sx={{ height: 8, borderRadius: 4 }}
                        />
                      </Box>
                    ))}
                  </Stack>
                )}
              </CardContent>
            </Card>

            {/* Cashback optimization */}
            <Card sx={{ gridColumn: { md: '1 / -1' } }}>
              <CardContent>
                <Stack direction="row" justifyContent="space-between" alignItems="center" mb={2}>
                  <Typography variant="h6">Cashback Optimization</Typography>
                  <Typography variant="h6" color="success.main">
                    {formatINR(data.cashback_optimization.total_cashback)}
                  </Typography>
                </Stack>
                {data.cashback_optimization.by_card.length === 0 ? (
                  <Typography variant="body2" color="text.secondary">
                    No credit cards to analyze.
                  </Typography>
                ) : (
                  <Stack divider={<Divider flexItem />} spacing={1.5}>
                    {data.cashback_optimization.by_card.map((c) => (
                      <Stack
                        key={c.card_id}
                        direction="row"
                        justifyContent="space-between"
                        alignItems="center"
                      >
                        <Box>
                          <Typography variant="body2" fontWeight={600}>
                            {c.card_name}
                          </Typography>
                          <Typography variant="caption" color="text.secondary">
                            Spend {formatINR(c.spend)} · {formatPercent(c.effective_rate)} effective
                            {c.cap !== null
                              ? ` · ${formatINR(c.cap_remaining)} cap left`
                              : ''}
                          </Typography>
                        </Box>
                        <Typography variant="subtitle1" fontWeight={700} color="success.main">
                          {formatINR(c.cashback_earned)}
                        </Typography>
                      </Stack>
                    ))}
                  </Stack>
                )}
              </CardContent>
            </Card>
          </Box>
        </>
      )}
    </Box>
  );
}

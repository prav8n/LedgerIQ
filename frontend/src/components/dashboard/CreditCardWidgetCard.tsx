import { Box, Card, CardContent, Chip, LinearProgress, Stack, Typography } from '@mui/material';
import { formatINR, formatPercent, toNumber } from '@/utils/format';
import type { CreditCardWidget } from '@/types/dashboard';

interface Props {
  card: CreditCardWidget;
}

function utilizationColor(pct: number): 'success' | 'warning' | 'error' {
  if (pct >= 75) return 'error';
  if (pct >= 40) return 'warning';
  return 'success';
}

export function CreditCardWidgetCard({ card }: Props) {
  const util = card.utilization_percent;
  const hasCap = card.cashback_cap !== null;
  const capUsedPct = hasCap
    ? Math.min(
        (toNumber(card.cashback_cap_used) / Math.max(toNumber(card.cashback_cap), 1)) * 100,
        100,
      )
    : 0;

  return (
    <Card sx={{ height: '100%' }}>
      <CardContent>
        <Stack direction="row" justifyContent="space-between" alignItems="flex-start" mb={2}>
          <Box>
            <Typography variant="h6" noWrap>
              {card.card_name}
            </Typography>
            <Typography variant="caption" color="text.secondary">
              {card.issuer}
              {card.last_four ? ` •••• ${card.last_four}` : ''}
            </Typography>
          </Box>
          <Chip label={card.network.toUpperCase()} size="small" variant="outlined" />
        </Stack>

        <Stack direction="row" spacing={3} mb={2}>
          <Box>
            <Typography variant="caption" color="text.secondary">
              Spend (mo)
            </Typography>
            <Typography variant="subtitle1" fontWeight={700}>
              {formatINR(card.spend_this_month)}
            </Typography>
          </Box>
          <Box>
            <Typography variant="caption" color="text.secondary">
              Cashback (mo)
            </Typography>
            <Typography variant="subtitle1" fontWeight={700} color="success.main">
              {formatINR(card.cashback_this_month)}
            </Typography>
          </Box>
        </Stack>

        <Box mb={hasCap ? 1.5 : 0}>
          <Stack direction="row" justifyContent="space-between" mb={0.5}>
            <Typography variant="caption" color="text.secondary">
              Utilization
            </Typography>
            <Typography variant="caption" fontWeight={700}>
              {formatPercent(util)} · {formatINR(card.available_credit)} left
            </Typography>
          </Stack>
          <LinearProgress
            variant="determinate"
            value={Math.min(util, 100)}
            color={utilizationColor(util)}
            sx={{ height: 8, borderRadius: 4 }}
          />
        </Box>

        {hasCap && (
          <Box>
            <Stack direction="row" justifyContent="space-between" mb={0.5}>
              <Typography variant="caption" color="text.secondary">
                Cashback cap
              </Typography>
              <Typography variant="caption" fontWeight={700}>
                {formatINR(card.cashback_cap_remaining)} of {formatINR(card.cashback_cap)} left
              </Typography>
            </Stack>
            <LinearProgress
              variant="determinate"
              value={capUsedPct}
              color="secondary"
              sx={{ height: 8, borderRadius: 4 }}
            />
          </Box>
        )}
      </CardContent>
    </Card>
  );
}

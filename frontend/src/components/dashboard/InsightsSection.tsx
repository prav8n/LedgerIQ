import type { ReactNode } from 'react';
import { Box, Card, CardContent, Chip, Stack, Typography } from '@mui/material';
import TrendingUpRoundedIcon from '@mui/icons-material/TrendingUpRounded';
import WarningAmberRoundedIcon from '@mui/icons-material/WarningAmberRounded';
import LightbulbRoundedIcon from '@mui/icons-material/LightbulbRounded';
import InfoRoundedIcon from '@mui/icons-material/InfoRounded';
import { useInsights } from '@/hooks/useInsights';
import type { Insight, InsightType } from '@/types/insight';

const meta: Record<InsightType, { icon: ReactNode; color: string }> = {
  positive: { icon: <TrendingUpRoundedIcon />, color: 'success.main' },
  warning: { icon: <WarningAmberRoundedIcon />, color: 'error.main' },
  tip: { icon: <LightbulbRoundedIcon />, color: 'warning.main' },
  info: { icon: <InfoRoundedIcon />, color: 'info.main' },
};

function InsightCard({ insight }: { insight: Insight }) {
  const m = meta[insight.type];
  return (
    <Card sx={{ height: '100%', borderLeft: 4, borderColor: m.color }}>
      <CardContent>
        <Stack direction="row" spacing={1.5} alignItems="flex-start">
          <Box sx={{ color: m.color, mt: 0.25, '& svg': { fontSize: 22 } }}>{m.icon}</Box>
          <Box flex={1}>
            <Stack direction="row" justifyContent="space-between" alignItems="center" mb={0.5}>
              <Typography variant="subtitle2" fontWeight={700}>
                {insight.title}
              </Typography>
              {insight.metric && (
                <Chip label={insight.metric} size="small" sx={{ color: m.color }} variant="outlined" />
              )}
            </Stack>
            <Typography variant="body2" color="text.secondary">
              {insight.description}
            </Typography>
          </Box>
        </Stack>
      </CardContent>
    </Card>
  );
}

export function InsightsSection() {
  const { data, isLoading } = useInsights('monthly');

  if (isLoading || !data || data.insights.length === 0) return null;

  return (
    <Box mb={3}>
      <Typography variant="h5" mb={1.5}>
        AI Insights
      </Typography>
      <Box
        sx={{
          display: 'grid',
          gap: 2,
          gridTemplateColumns: { xs: '1fr', md: '1fr 1fr' },
        }}
      >
        {data.insights.map((insight) => (
          <InsightCard key={insight.id} insight={insight} />
        ))}
      </Box>
    </Box>
  );
}

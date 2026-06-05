import type { ReactNode } from 'react';
import { Box, Card, CardContent, Stack, Typography } from '@mui/material';
import ArrowUpwardRoundedIcon from '@mui/icons-material/ArrowUpwardRounded';
import ArrowDownwardRoundedIcon from '@mui/icons-material/ArrowDownwardRounded';

interface Props {
  title: string;
  value: string;
  icon?: ReactNode;
  /** Accent color for the icon chip (theme palette key or hex). */
  accent?: string;
  /** Optional secondary line, e.g. "Savings rate 13.8%". */
  caption?: string;
  /** Optional period-over-period change (percent). */
  delta?: number;
}

export function KpiCard({ title, value, icon, accent = 'primary.main', caption, delta }: Props) {
  const positive = (delta ?? 0) >= 0;

  return (
    <Card sx={{ height: '100%' }}>
      <CardContent>
        <Stack direction="row" alignItems="flex-start" justifyContent="space-between">
          <Box>
            <Typography variant="body2" color="text.secondary">
              {title}
            </Typography>
            <Typography variant="h4" sx={{ mt: 0.5, fontWeight: 800, letterSpacing: -0.5 }}>
              {value}
            </Typography>
          </Box>
          {icon && (
            <Box
              sx={{
                width: 44,
                height: 44,
                borderRadius: 2,
                display: 'grid',
                placeItems: 'center',
                bgcolor: accent,
                color: '#fff',
                '& svg': { fontSize: 22 },
              }}
            >
              {icon}
            </Box>
          )}
        </Stack>

        {(caption || delta !== undefined) && (
          <Stack direction="row" alignItems="center" spacing={0.75} sx={{ mt: 1.25 }}>
            {delta !== undefined && (
              <Stack
                direction="row"
                alignItems="center"
                sx={{ color: positive ? 'success.main' : 'error.main' }}
              >
                {positive ? (
                  <ArrowUpwardRoundedIcon sx={{ fontSize: 16 }} />
                ) : (
                  <ArrowDownwardRoundedIcon sx={{ fontSize: 16 }} />
                )}
                <Typography variant="caption" fontWeight={700}>
                  {Math.abs(delta).toFixed(1)}%
                </Typography>
              </Stack>
            )}
            {caption && (
              <Typography variant="caption" color="text.secondary">
                {caption}
              </Typography>
            )}
          </Stack>
        )}
      </CardContent>
    </Card>
  );
}

import type { ReactNode } from 'react';
import { Box, Card, CardContent, Stack, Typography } from '@mui/material';

interface Props {
  title: string;
  action?: ReactNode;
  height?: number;
  children: ReactNode;
}

/** Card shell with a title and a fixed-height chart area. */
export function ChartCard({ title, action, height = 300, children }: Props) {
  return (
    <Card sx={{ height: '100%' }}>
      <CardContent>
        <Stack direction="row" alignItems="center" justifyContent="space-between" mb={1}>
          <Typography variant="h6">{title}</Typography>
          {action}
        </Stack>
        <Box sx={{ width: '100%', height }}>{children}</Box>
      </CardContent>
    </Card>
  );
}

import type { ReactNode } from 'react';
import { Box, Stack, Typography } from '@mui/material';
import { EmptyState } from '@/components/EmptyState';

interface Props {
  title: string;
  subtitle?: string;
  icon?: ReactNode;
}

/**
 * Standard page scaffold used by module pages until their data/UI lands in a
 * later phase: a page header plus a "coming soon" empty state.
 */
export function ModulePlaceholder({ title, subtitle, icon }: Props) {
  return (
    <Box>
      <Stack spacing={0.5} sx={{ mb: 3 }}>
        <Typography variant="h4">{title}</Typography>
        {subtitle && (
          <Typography variant="body2" color="text.secondary">
            {subtitle}
          </Typography>
        )}
      </Stack>
      <EmptyState
        title="Coming soon"
        description={`The ${title} module is wired into the app shell. Its data and visualizations arrive in an upcoming phase.`}
        icon={icon}
      />
    </Box>
  );
}

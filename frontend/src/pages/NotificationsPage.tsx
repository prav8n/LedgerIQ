import { useState } from 'react';
import type { ReactNode } from 'react';
import {
  Box,
  Button,
  Card,
  CardContent,
  IconButton,
  Stack,
  ToggleButton,
  ToggleButtonGroup,
  Tooltip,
  Typography,
} from '@mui/material';
import DoneAllRoundedIcon from '@mui/icons-material/DoneAllRounded';
import RefreshRoundedIcon from '@mui/icons-material/RefreshRounded';
import DeleteRoundedIcon from '@mui/icons-material/DeleteRounded';
import MarkEmailReadRoundedIcon from '@mui/icons-material/MarkEmailReadRounded';
import InfoRoundedIcon from '@mui/icons-material/InfoRounded';
import CheckCircleRoundedIcon from '@mui/icons-material/CheckCircleRounded';
import WarningAmberRoundedIcon from '@mui/icons-material/WarningAmberRounded';
import ErrorRoundedIcon from '@mui/icons-material/ErrorRounded';
import NotificationsActiveRoundedIcon from '@mui/icons-material/NotificationsActiveRounded';

import { PageHeader } from '@/components/PageHeader';
import { LoadingSkeleton } from '@/components/LoadingSkeleton';
import { EmptyState } from '@/components/EmptyState';
import {
  useDeleteNotification,
  useMarkAllRead,
  useMarkRead,
  useNotifications,
  useScanNotifications,
} from '@/hooks/useNotifications';
import { useToast } from '@/hooks/useToast';
import { getErrorMessage } from '@/services/api';
import { formatDate, humanize } from '@/utils/format';
import type { Notification } from '@/types/notification';

const typeMeta: Record<Notification['type'], { icon: ReactNode; color: string }> = {
  info: { icon: <InfoRoundedIcon />, color: 'info.main' },
  success: { icon: <CheckCircleRoundedIcon />, color: 'success.main' },
  warning: { icon: <WarningAmberRoundedIcon />, color: 'warning.main' },
  alert: { icon: <ErrorRoundedIcon />, color: 'error.main' },
  reminder: { icon: <NotificationsActiveRoundedIcon />, color: 'primary.main' },
};

export function NotificationsPage() {
  const toast = useToast();
  const [filter, setFilter] = useState<'all' | 'unread'>('all');
  const { data, isLoading } = useNotifications(filter === 'unread' ? { is_read: false } : undefined);

  const scanM = useScanNotifications();
  const markReadM = useMarkRead();
  const markAllM = useMarkAllRead();
  const deleteM = useDeleteNotification();

  const run = async (fn: () => Promise<unknown>, msg: string) => {
    try {
      await fn();
      toast.success(msg);
    } catch (e) {
      toast.error(getErrorMessage(e));
    }
  };

  return (
    <Box>
      <PageHeader
        title="Notifications"
        subtitle="Due dates, renewals, budgets and milestones"
        action={
          <Stack direction="row" spacing={1}>
            <Button variant="outlined" startIcon={<RefreshRoundedIcon />} disabled={scanM.isPending} onClick={() => void run(() => scanM.mutateAsync(), 'Scan complete')}>
              Scan now
            </Button>
            <Button variant="outlined" startIcon={<DoneAllRoundedIcon />} disabled={markAllM.isPending} onClick={() => void run(() => markAllM.mutateAsync(), 'All marked read')}>
              Mark all read
            </Button>
          </Stack>
        }
      />

      <ToggleButtonGroup
        value={filter}
        exclusive
        size="small"
        onChange={(_, v: 'all' | 'unread' | null) => v && setFilter(v)}
        sx={{ mb: 2 }}
      >
        <ToggleButton value="all">All</ToggleButton>
        <ToggleButton value="unread">Unread</ToggleButton>
      </ToggleButtonGroup>

      {isLoading && <LoadingSkeleton cards={0} rows={5} />}
      {!isLoading && data && data.length === 0 && (
        <EmptyState title="You're all caught up" description="No notifications to show. Run a scan to generate new ones." />
      )}

      {!isLoading && data && data.length > 0 && (
        <Stack spacing={1.5}>
          {data.map((n) => {
            const m = typeMeta[n.type];
            return (
              <Card key={n.id} sx={{ opacity: n.is_read ? 0.7 : 1, borderLeft: 4, borderColor: m.color }}>
                <CardContent sx={{ py: 1.5 }}>
                  <Stack direction="row" spacing={1.5} alignItems="flex-start">
                    <Box sx={{ color: m.color, mt: 0.25, '& svg': { fontSize: 22 } }}>{m.icon}</Box>
                    <Box flex={1} minWidth={0}>
                      <Stack direction="row" justifyContent="space-between" alignItems="center">
                        <Typography variant="subtitle2" fontWeight={n.is_read ? 500 : 700}>
                          {n.title}
                        </Typography>
                        <Typography variant="caption" color="text.secondary">
                          {humanize(n.category)} · {formatDate(n.created_at)}
                        </Typography>
                      </Stack>
                      <Typography variant="body2" color="text.secondary">
                        {n.message}
                      </Typography>
                    </Box>
                    <Stack direction="row">
                      {!n.is_read && (
                        <Tooltip title="Mark read">
                          <IconButton size="small" onClick={() => void run(() => markReadM.mutateAsync(n.id), 'Marked read')}>
                            <MarkEmailReadRoundedIcon fontSize="small" />
                          </IconButton>
                        </Tooltip>
                      )}
                      <Tooltip title="Delete">
                        <IconButton size="small" onClick={() => void run(() => deleteM.mutateAsync(n.id), 'Deleted')}>
                          <DeleteRoundedIcon fontSize="small" />
                        </IconButton>
                      </Tooltip>
                    </Stack>
                  </Stack>
                </CardContent>
              </Card>
            );
          })}
        </Stack>
      )}
    </Box>
  );
}

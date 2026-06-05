import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { notificationService } from '@/services/notificationService';
import type { Notification, UnreadCount } from '@/types/notification';

export function useNotifications(params?: { is_read?: boolean; category?: string }) {
  return useQuery<Notification[]>({
    queryKey: ['notifications', params ?? {}],
    queryFn: () => notificationService.list(params),
  });
}

export function useUnreadCount() {
  return useQuery<UnreadCount>({
    queryKey: ['notifications', 'unread-count'],
    queryFn: () => notificationService.unreadCount(),
  });
}

function useNotifMutation<TArgs>(fn: (args: TArgs) => Promise<unknown>) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: fn,
    onSuccess: () => void qc.invalidateQueries({ queryKey: ['notifications'] }),
  });
}

export function useScanNotifications() {
  return useNotifMutation<void>(() => notificationService.scan());
}
export function useMarkRead() {
  return useNotifMutation<number>((id) => notificationService.markRead(id));
}
export function useMarkAllRead() {
  return useNotifMutation<void>(() => notificationService.markAllRead());
}
export function useDeleteNotification() {
  return useNotifMutation<number>((id) => notificationService.remove(id));
}

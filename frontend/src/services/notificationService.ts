import { api } from '@/services/api';
import type { Notification, ScanResult, UnreadCount } from '@/types/notification';

export const notificationService = {
  list: async (params?: { is_read?: boolean; category?: string }): Promise<Notification[]> =>
    (await api.get<Notification[]>('/notifications', { params })).data,
  unreadCount: async (): Promise<UnreadCount> =>
    (await api.get<UnreadCount>('/notifications/unread-count')).data,
  scan: async (): Promise<ScanResult> =>
    (await api.post<ScanResult>('/notifications/scan')).data,
  markRead: async (id: number): Promise<Notification> =>
    (await api.patch<Notification>(`/notifications/${id}/read`)).data,
  markAllRead: async (): Promise<UnreadCount> =>
    (await api.post<UnreadCount>('/notifications/read-all')).data,
  remove: async (id: number): Promise<void> => {
    await api.delete(`/notifications/${id}`);
  },
};

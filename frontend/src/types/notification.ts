export interface Notification {
  id: number;
  title: string;
  message: string;
  type: 'info' | 'success' | 'warning' | 'alert' | 'reminder';
  category: string;
  is_read: boolean;
  action_url: string | null;
  related_entity_type: string | null;
  related_entity_id: number | null;
  created_at: string;
}

export interface UnreadCount {
  unread: number;
}

export interface ScanResult {
  created: number;
}

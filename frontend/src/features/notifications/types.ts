export type NotificationData = {
  id: number;
  user_id: number;
  type: string;
  title: string;
  body: string;
  payload: Record<string, unknown>;
  is_read: boolean;
  read_at: string | null;
  created_at: string;
};

export type NotificationsListData = {
  items: NotificationData[];
  unread_count: number;
};

export type ReadAllNotificationsData = {
  updated_count: number;
};

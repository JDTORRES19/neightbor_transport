import { apiGet, apiPost } from "../../shared/api/httpClient";

import { NotificationsListData, ReadAllNotificationsData } from "./types";

export async function fetchNotifications(params?: {
  unreadOnly?: boolean;
  page?: number;
  pageSize?: number;
}) {
  const query = new URLSearchParams();

  if (params?.unreadOnly !== undefined) {
    query.set("unread_only", String(params.unreadOnly));
  }
  if (params?.page !== undefined) {
    query.set("page", String(params.page));
  }
  if (params?.pageSize !== undefined) {
    query.set("page_size", String(params.pageSize));
  }

  const suffix = query.toString() ? `?${query.toString()}` : "";
  return apiGet<NotificationsListData>(`/notifications${suffix}`);
}

export async function markAllNotificationsRead() {
  return apiPost<ReadAllNotificationsData, Record<string, never>>("/notifications/read-all", {});
}

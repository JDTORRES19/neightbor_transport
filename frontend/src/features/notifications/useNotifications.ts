import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { fetchNotifications, markAllNotificationsRead } from "./api";

export function useUnreadNotificationsQuery() {
  return useQuery({
    queryKey: ["notifications", "unread"],
    queryFn: () =>
      fetchNotifications({
        unreadOnly: true,
        page: 1,
        pageSize: 10,
      }),
    refetchInterval: 15000,
  });
}

export function useMarkAllNotificationsReadMutation() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: markAllNotificationsRead,
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ["notifications"] });
    },
  });
}

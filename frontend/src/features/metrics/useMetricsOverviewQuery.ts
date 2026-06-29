import { useQuery } from "@tanstack/react-query";

import { fetchMetricsOverview } from "./api";

export function useMetricsOverviewQuery(params?: { windowSeconds?: number; limit?: number }) {
  const windowSeconds = params?.windowSeconds ?? 300;
  const limit = params?.limit ?? 12;

  return useQuery({
    queryKey: ["metrics", "overview", windowSeconds, limit],
    queryFn: () => fetchMetricsOverview({ windowSeconds, limit }),
    refetchInterval: 20000,
  });
}

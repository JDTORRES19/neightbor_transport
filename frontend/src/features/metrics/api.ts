import { apiGet } from "../../shared/api/httpClient";

import { MetricsOverviewData } from "./types";

export async function fetchMetricsOverview(params?: { windowSeconds?: number; limit?: number }) {
  const query = new URLSearchParams();
  if (params?.windowSeconds !== undefined) {
    query.set("window_seconds", String(params.windowSeconds));
  }
  if (params?.limit !== undefined) {
    query.set("limit", String(params.limit));
  }

  const suffix = query.toString() ? `?${query.toString()}` : "";
  return apiGet<MetricsOverviewData>(`/metrics/overview${suffix}`);
}

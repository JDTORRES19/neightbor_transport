import { useQuery } from "@tanstack/react-query";

import { apiGet } from "../../../shared/api/httpClient";
import { HealthData, HealthQueryResult } from "./types";

async function fetchHealth(): Promise<HealthQueryResult> {
  const result = await apiGet<HealthData>("/health");
  return result;
}

export function useHealthQuery() {
  return useQuery({
    queryKey: ["health"],
    queryFn: fetchHealth,
  });
}

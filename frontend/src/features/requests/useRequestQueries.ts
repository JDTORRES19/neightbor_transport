import { useQuery } from "@tanstack/react-query";

import { fetchMyRequests, fetchTripRequests } from "./api";

export function useTripRequestsQuery(tripId?: number) {
  return useQuery({
    queryKey: ["requests", "trip", tripId ?? "none"],
    queryFn: () => fetchTripRequests(tripId as number),
    enabled: Boolean(tripId),
  });
}

export function useMyRequestsQuery() {
  return useQuery({
    queryKey: ["requests", "mine"],
    queryFn: fetchMyRequests,
  });
}

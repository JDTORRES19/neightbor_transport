import { useQuery } from "@tanstack/react-query";

import { fetchMyActiveTrip, fetchTripsBoard } from "./api";

export function useTripsBoardQuery(direction?: string) {
  return useQuery({
    queryKey: ["trips", "board", direction ?? "all"],
    queryFn: () => fetchTripsBoard(direction),
  });
}

export function useMyActiveTripQuery() {
  return useQuery({
    queryKey: ["trips", "mine", "active"],
    queryFn: fetchMyActiveTrip,
  });
}

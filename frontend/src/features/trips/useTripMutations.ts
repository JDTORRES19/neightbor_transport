import { useMutation, useQueryClient } from "@tanstack/react-query";

import { cancelTrip, createTrip, finalizeTrip } from "./api";
import { CreateTripPayload } from "./types";

async function invalidateTrips(queryClient: ReturnType<typeof useQueryClient>) {
  await Promise.all([
    queryClient.invalidateQueries({ queryKey: ["trips", "board"] }),
    queryClient.invalidateQueries({ queryKey: ["trips", "mine", "active"] }),
  ]);
}

export function useCreateTripMutation() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (payload: CreateTripPayload) => createTrip(payload),
    onSuccess: async () => {
      await invalidateTrips(queryClient);
    },
  });
}

export function useCancelTripMutation() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (tripId: number) => cancelTrip(tripId),
    onSuccess: async () => {
      await invalidateTrips(queryClient);
    },
  });
}

export function useFinalizeTripMutation() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (tripId: number) => finalizeTrip(tripId),
    onSuccess: async () => {
      await invalidateTrips(queryClient);
    },
  });
}

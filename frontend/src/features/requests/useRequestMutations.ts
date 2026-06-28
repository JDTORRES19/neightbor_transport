import { useMutation, useQueryClient } from "@tanstack/react-query";

import {
  acceptTripRequest,
  cancelTripRequest,
  createTripRequest,
  rejectTripRequest,
} from "./api";
import { CreateTripRequestPayload } from "./types";

type CreateRequestInput = {
  tripId: number;
  payload: CreateTripRequestPayload;
};

async function invalidateRequestAndTripViews(queryClient: ReturnType<typeof useQueryClient>) {
  await Promise.all([
    queryClient.invalidateQueries({ queryKey: ["requests"] }),
    queryClient.invalidateQueries({ queryKey: ["trips", "board"] }),
    queryClient.invalidateQueries({ queryKey: ["trips", "mine", "active"] }),
  ]);
}

export function useCreateTripRequestMutation() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ tripId, payload }: CreateRequestInput) => createTripRequest(tripId, payload),
    onSuccess: async () => {
      await invalidateRequestAndTripViews(queryClient);
    },
  });
}

export function useAcceptTripRequestMutation() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (requestId: number) => acceptTripRequest(requestId),
    onSuccess: async () => {
      await invalidateRequestAndTripViews(queryClient);
    },
  });
}

export function useRejectTripRequestMutation() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (requestId: number) => rejectTripRequest(requestId),
    onSuccess: async () => {
      await invalidateRequestAndTripViews(queryClient);
    },
  });
}

export function useCancelTripRequestMutation() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (requestId: number) => cancelTripRequest(requestId),
    onSuccess: async () => {
      await invalidateRequestAndTripViews(queryClient);
    },
  });
}

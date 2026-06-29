import { QueryClient, useMutation, useQueryClient } from "@tanstack/react-query";

import { REQUEST_STATUS, TRIP_STATUS } from "../../shared/constants/trips";
import { TripMaybeData, TripsListData } from "../trips/types";
import {
  acceptTripRequest,
  cancelTripRequest,
  createTripRequest,
  rejectTripRequest,
} from "./api";
import { CreateTripRequestPayload, TripRequestData, TripRequestsListData } from "./types";

type ApiResult<TData> = {
  data: TData;
  requestId?: string;
};

type QuerySnapshot<TData> = {
  key: readonly unknown[];
  data: TData | undefined;
};

type RequestMutationContext = {
  mineRequestsSnapshot: ApiResult<TripRequestsListData> | undefined;
  tripRequestsSnapshots: QuerySnapshot<ApiResult<TripRequestsListData>>[];
  boardSnapshots: QuerySnapshot<ApiResult<TripsListData>>[];
  myActiveTripSnapshot: ApiResult<TripMaybeData> | undefined;
};

function snapshotQueries<TData>(
  queryClient: QueryClient,
  queryKey: readonly unknown[],
): QuerySnapshot<TData>[] {
  return queryClient
    .getQueriesData<TData>({ queryKey })
    .map(([key, data]) => ({ key, data }));
}

function restoreQuerySnapshots<TData>(queryClient: QueryClient, snapshots: QuerySnapshot<TData>[]) {
  snapshots.forEach(({ key, data }) => {
    queryClient.setQueryData(key, data);
  });
}

function updateRequestStatus(
  oldData: ApiResult<TripRequestsListData> | undefined,
  requestId: number,
  status: string,
  decidedAt?: string,
) {
  if (!oldData) {
    return oldData;
  }

  return {
    ...oldData,
    data: {
      ...oldData.data,
      items: oldData.data.items.map((item) =>
        item.id === requestId
          ? {
              ...item,
              status,
              decided_at: decidedAt ?? item.decided_at,
            }
          : item,
      ),
    },
  };
}

function updateRequestStatuses(
  oldData: ApiResult<TripRequestsListData> | undefined,
  transform: (item: TripRequestData) => TripRequestData,
) {
  if (!oldData) {
    return oldData;
  }

  return {
    ...oldData,
    data: {
      ...oldData.data,
      items: oldData.data.items.map((item) => transform(item)),
    },
  };
}

function applyAcceptWithCascade(
  oldData: ApiResult<TripRequestsListData> | undefined,
  requestId: number,
  requesterUserId: number | undefined,
  decidedAt: string,
) {
  return updateRequestStatuses(oldData, (item) => {
    if (item.id === requestId) {
      return {
        ...item,
        status: REQUEST_STATUS.ACCEPTED,
        decided_at: decidedAt,
      };
    }

    if (
      requesterUserId !== undefined &&
      item.id !== requestId &&
      item.requester.user_id === requesterUserId &&
      item.status === REQUEST_STATUS.PENDING
    ) {
      return {
        ...item,
        status: REQUEST_STATUS.CANCELLED,
        decided_at: decidedAt,
      };
    }

    return item;
  });
}

function adjustTripSeats(
  queryClient: QueryClient,
  tripId: number,
  seatDelta: number,
  fallbackStatus: string,
) {
  const boardQueries = queryClient.getQueriesData<ApiResult<TripsListData>>({
    queryKey: ["trips", "board"],
  });

  boardQueries.forEach(([key]) => {
    queryClient.setQueryData<ApiResult<TripsListData>>(key, (oldData) => {
      if (!oldData) {
        return oldData;
      }

      return {
        ...oldData,
        data: {
          ...oldData.data,
          items: oldData.data.items.map((trip) => {
            if (trip.id !== tripId) {
              return trip;
            }

            const nextAvailableSeats = Math.max(
              0,
              Math.min(trip.total_seats, trip.available_seats + seatDelta),
            );

            let nextStatus = fallbackStatus;
            if (trip.status === TRIP_STATUS.CANCELLED || trip.status === TRIP_STATUS.FINALIZED) {
              nextStatus = trip.status;
            } else if (nextAvailableSeats <= 0) {
              nextStatus = TRIP_STATUS.FULL;
            } else if (trip.status === TRIP_STATUS.FULL) {
              nextStatus = TRIP_STATUS.ACTIVE;
            } else {
              nextStatus = trip.status;
            }

            return {
              ...trip,
              available_seats: nextAvailableSeats,
              status: nextStatus,
            };
          }),
        },
      };
    });
  });

  queryClient.setQueryData<ApiResult<TripMaybeData>>(["trips", "mine", "active"], (oldData) => {
    if (!oldData?.data || oldData.data.id !== tripId) {
      return oldData;
    }

    const nextAvailableSeats = Math.max(
      0,
      Math.min(oldData.data.total_seats, oldData.data.available_seats + seatDelta),
    );

    let nextStatus = fallbackStatus;
    if (oldData.data.status === TRIP_STATUS.CANCELLED || oldData.data.status === TRIP_STATUS.FINALIZED) {
      nextStatus = oldData.data.status;
    } else if (nextAvailableSeats <= 0) {
      nextStatus = TRIP_STATUS.FULL;
    } else if (oldData.data.status === TRIP_STATUS.FULL) {
      nextStatus = TRIP_STATUS.ACTIVE;
    } else {
      nextStatus = oldData.data.status;
    }

    return {
      ...oldData,
      data: {
        ...oldData.data,
        available_seats: nextAvailableSeats,
        status: nextStatus,
      },
    };
  });
}

function findRequestInCache(
  queryClient: QueryClient,
  requestId: number,
): TripRequestData | undefined {
  const mineRequests = queryClient.getQueryData<ApiResult<TripRequestsListData>>([
    "requests",
    "mine",
  ]);
  const mineMatch = mineRequests?.data.items.find((item) => item.id === requestId);
  if (mineMatch) {
    return mineMatch;
  }

  const tripQueries = queryClient.getQueriesData<ApiResult<TripRequestsListData>>({
    queryKey: ["requests", "trip"],
  });

  for (const [, queryData] of tripQueries) {
    const match = queryData?.data.items.find((item) => item.id === requestId);
    if (match) {
      return match;
    }
  }

  return undefined;
}

async function invalidateRequestsAndTrips(queryClient: QueryClient) {
  await Promise.all([
    queryClient.invalidateQueries({ queryKey: ["requests"] }),
    queryClient.invalidateQueries({ queryKey: ["trips", "board"] }),
    queryClient.invalidateQueries({ queryKey: ["trips", "mine", "active"] }),
  ]);
}

function createBaseMutationContext(queryClient: QueryClient): RequestMutationContext {
  return {
    mineRequestsSnapshot: queryClient.getQueryData<ApiResult<TripRequestsListData>>([
      "requests",
      "mine",
    ]),
    tripRequestsSnapshots: snapshotQueries<ApiResult<TripRequestsListData>>(queryClient, [
      "requests",
      "trip",
    ]),
    boardSnapshots: snapshotQueries<ApiResult<TripsListData>>(queryClient, ["trips", "board"]),
    myActiveTripSnapshot: queryClient.getQueryData<ApiResult<TripMaybeData>>([
      "trips",
      "mine",
      "active",
    ]),
  };
}

function rollbackMutationContext(queryClient: QueryClient, context: RequestMutationContext | undefined) {
  if (!context) {
    return;
  }

  queryClient.setQueryData(["requests", "mine"], context.mineRequestsSnapshot);
  restoreQuerySnapshots(queryClient, context.tripRequestsSnapshots);
  restoreQuerySnapshots(queryClient, context.boardSnapshots);
  queryClient.setQueryData(["trips", "mine", "active"], context.myActiveTripSnapshot);
}

export function useCreateTripRequestMutation() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ tripId, payload }: { tripId: number; payload: CreateTripRequestPayload }) =>
      createTripRequest(tripId, payload),
    onMutate: async ({ tripId, payload }) => {
      await Promise.all([
        queryClient.cancelQueries({ queryKey: ["requests", "mine"] }),
        queryClient.cancelQueries({ queryKey: ["requests", "trip", tripId] }),
      ]);

      const mineRequestsSnapshot = queryClient.getQueryData<ApiResult<TripRequestsListData>>([
        "requests",
        "mine",
      ]);
      const tripRequestsSnapshot = queryClient.getQueryData<ApiResult<TripRequestsListData>>([
        "requests",
        "trip",
        tripId,
      ]);

      const now = new Date().toISOString();
      const optimisticRequest: TripRequestData = {
        id: -Date.now(),
        trip_id: tripId,
        pickup_label: payload.pickup_label,
        requested_seats: payload.requested_seats,
        comment: payload.comment ?? null,
        status: REQUEST_STATUS.PENDING,
        created_at: now,
        decided_at: null,
        requester:
          mineRequestsSnapshot?.data.items[0]?.requester ??
          ({
            user_id: 0,
            display_name: "Tu solicitud",
            photo_url: null,
          } as TripRequestData["requester"]),
      };

      queryClient.setQueryData<ApiResult<TripRequestsListData>>(["requests", "mine"], (oldData) => {
        if (!oldData) {
          return {
            data: { items: [optimisticRequest] },
          };
        }

        return {
          ...oldData,
          data: {
            ...oldData.data,
            items: [optimisticRequest, ...oldData.data.items],
          },
        };
      });

      queryClient.setQueryData<ApiResult<TripRequestsListData>>(
        ["requests", "trip", tripId],
        (oldData) => {
          if (!oldData) {
            return oldData;
          }

          return {
            ...oldData,
            data: {
              ...oldData.data,
              items: [optimisticRequest, ...oldData.data.items],
            },
          };
        },
      );

      return {
        mineRequestsSnapshot,
        tripRequestsSnapshot,
        tripId,
      };
    },
    onError: (_error, _variables, context) => {
      if (!context) {
        return;
      }

      queryClient.setQueryData(["requests", "mine"], context.mineRequestsSnapshot);
      queryClient.setQueryData(["requests", "trip", context.tripId], context.tripRequestsSnapshot);
    },
    onSettled: async () => {
      await invalidateRequestsAndTrips(queryClient);
    },
  });
}

export function useAcceptTripRequestMutation() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (requestId: number) => acceptTripRequest(requestId),
    onMutate: async (requestId) => {
      await Promise.all([
        queryClient.cancelQueries({ queryKey: ["requests"] }),
        queryClient.cancelQueries({ queryKey: ["trips", "board"] }),
        queryClient.cancelQueries({ queryKey: ["trips", "mine", "active"] }),
      ]);

      const context = createBaseMutationContext(queryClient);
      const targetRequest = findRequestInCache(queryClient, requestId);
      const requesterUserId = targetRequest?.requester.user_id;
      const decidedAt = new Date().toISOString();

      queryClient.setQueryData<ApiResult<TripRequestsListData>>(["requests", "mine"], (oldData) =>
        applyAcceptWithCascade(oldData, requestId, requesterUserId, decidedAt),
      );

      context.tripRequestsSnapshots.forEach(({ key }) => {
        queryClient.setQueryData<ApiResult<TripRequestsListData>>(key, (oldData) =>
          applyAcceptWithCascade(oldData, requestId, requesterUserId, decidedAt),
        );
      });

      if (targetRequest && targetRequest.status !== REQUEST_STATUS.ACCEPTED) {
        adjustTripSeats(queryClient, targetRequest.trip_id, -targetRequest.requested_seats, TRIP_STATUS.FULL);
      }

      return context;
    },
    onError: (_error, _variables, context) => {
      rollbackMutationContext(queryClient, context);
    },
    onSettled: async () => {
      await invalidateRequestsAndTrips(queryClient);
    },
  });
}

export function useRejectTripRequestMutation() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (requestId: number) => rejectTripRequest(requestId),
    onMutate: async (requestId) => {
      await Promise.all([
        queryClient.cancelQueries({ queryKey: ["requests"] }),
        queryClient.cancelQueries({ queryKey: ["trips", "board"] }),
        queryClient.cancelQueries({ queryKey: ["trips", "mine", "active"] }),
      ]);

      const context = createBaseMutationContext(queryClient);
      const decidedAt = new Date().toISOString();

      queryClient.setQueryData<ApiResult<TripRequestsListData>>(["requests", "mine"], (oldData) =>
        updateRequestStatus(oldData, requestId, REQUEST_STATUS.REJECTED, decidedAt),
      );

      context.tripRequestsSnapshots.forEach(({ key }) => {
        queryClient.setQueryData<ApiResult<TripRequestsListData>>(key, (oldData) =>
          updateRequestStatus(oldData, requestId, REQUEST_STATUS.REJECTED, decidedAt),
        );
      });

      return context;
    },
    onError: (_error, _variables, context) => {
      rollbackMutationContext(queryClient, context);
    },
    onSettled: async () => {
      await invalidateRequestsAndTrips(queryClient);
    },
  });
}

export function useCancelTripRequestMutation() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (requestId: number) => cancelTripRequest(requestId),
    onMutate: async (requestId) => {
      await Promise.all([
        queryClient.cancelQueries({ queryKey: ["requests"] }),
        queryClient.cancelQueries({ queryKey: ["trips", "board"] }),
        queryClient.cancelQueries({ queryKey: ["trips", "mine", "active"] }),
      ]);

      const context = createBaseMutationContext(queryClient);
      const targetRequest = findRequestInCache(queryClient, requestId);
      const decidedAt = new Date().toISOString();

      queryClient.setQueryData<ApiResult<TripRequestsListData>>(["requests", "mine"], (oldData) =>
        updateRequestStatus(oldData, requestId, REQUEST_STATUS.CANCELLED, decidedAt),
      );

      context.tripRequestsSnapshots.forEach(({ key }) => {
        queryClient.setQueryData<ApiResult<TripRequestsListData>>(key, (oldData) =>
          updateRequestStatus(oldData, requestId, REQUEST_STATUS.CANCELLED, decidedAt),
        );
      });

      if (targetRequest?.status === REQUEST_STATUS.ACCEPTED) {
        adjustTripSeats(queryClient, targetRequest.trip_id, targetRequest.requested_seats, TRIP_STATUS.ACTIVE);
      }

      return context;
    },
    onError: (_error, _variables, context) => {
      rollbackMutationContext(queryClient, context);
    },
    onSettled: async () => {
      await invalidateRequestsAndTrips(queryClient);
    },
  });
}

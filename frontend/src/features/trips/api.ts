import { apiGet, apiPost } from "../../shared/api/httpClient";

import { CreateTripPayload, TripData, TripMaybeData, TripsListData } from "./types";

export async function fetchTripsBoard(direction?: string) {
  const suffix = direction ? `?direction=${encodeURIComponent(direction)}` : "";
  return apiGet<TripsListData>(`/trips${suffix}`);
}

export async function fetchMyActiveTrip() {
  return apiGet<TripMaybeData>("/trips/mine/active");
}

export async function createTrip(payload: CreateTripPayload) {
  return apiPost<TripData, CreateTripPayload>("/trips", payload);
}

export async function cancelTrip(tripId: number) {
  return apiPost<TripData, Record<string, never>>(`/trips/${tripId}/cancel`, {});
}

export async function finalizeTrip(tripId: number) {
  return apiPost<TripData, Record<string, never>>(`/trips/${tripId}/finalize`, {});
}

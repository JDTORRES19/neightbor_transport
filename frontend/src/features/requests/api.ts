import { apiGet, apiPost } from "../../shared/api/httpClient";

import { CreateTripRequestPayload, TripRequestData, TripRequestsListData } from "./types";

export async function fetchTripRequests(tripId: number) {
  return apiGet<TripRequestsListData>(`/trips/${tripId}/requests`);
}

export async function fetchMyRequests() {
  return apiGet<TripRequestsListData>("/requests/mine");
}

export async function createTripRequest(tripId: number, payload: CreateTripRequestPayload) {
  return apiPost<TripRequestData, CreateTripRequestPayload>(`/trips/${tripId}/requests`, payload);
}

export async function acceptTripRequest(requestId: number) {
  return apiPost<TripRequestData, Record<string, never>>(`/requests/${requestId}/accept`, {});
}

export async function rejectTripRequest(requestId: number) {
  return apiPost<TripRequestData, Record<string, never>>(`/requests/${requestId}/reject`, {});
}

export async function cancelTripRequest(requestId: number) {
  return apiPost<TripRequestData, Record<string, never>>(`/requests/${requestId}/cancel`, {});
}

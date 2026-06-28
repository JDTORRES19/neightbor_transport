import { apiDelete, apiGet, apiPatch, apiPost } from "../../shared/api/httpClient";

import { CreateVehiclePayload, ListVehiclesData, UpdateVehiclePayload, VehicleData } from "./types";

export async function fetchVehicles() {
  return apiGet<ListVehiclesData>("/vehicles");
}

export async function createVehicle(payload: CreateVehiclePayload) {
  return apiPost<VehicleData, CreateVehiclePayload>("/vehicles", payload);
}

export async function updateVehicle(vehicleId: number, payload: UpdateVehiclePayload) {
  return apiPatch<VehicleData, UpdateVehiclePayload>(`/vehicles/${vehicleId}`, payload);
}

export async function deactivateVehicle(vehicleId: number) {
  return apiDelete<VehicleData>(`/vehicles/${vehicleId}`);
}

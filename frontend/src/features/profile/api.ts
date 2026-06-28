import { apiGet, apiPatch } from "../../shared/api/httpClient";

import { ProfileData, UpdateProfilePayload } from "./types";

export async function fetchMyProfile() {
  return apiGet<ProfileData>("/me");
}

export async function updateMyProfile(payload: UpdateProfilePayload) {
  return apiPatch<ProfileData, UpdateProfilePayload>("/me", payload);
}

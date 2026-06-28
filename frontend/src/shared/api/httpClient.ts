import { API_BASE_URL } from "./config";
import { ApiEnvelope, ApiRequestError } from "./types";

type HttpMethod = "GET" | "POST" | "PATCH" | "DELETE";

function mergeHeaders(headers?: HeadersInit): Headers {
  const merged = new Headers(headers);
  if (!merged.has("Accept")) {
    merged.set("Accept", "application/json");
  }
  return merged;
}

async function apiRequest<TData>(method: HttpMethod, path: string, body?: unknown) {
  const headers = mergeHeaders();
  const init: RequestInit = { method, headers };

  if (body !== undefined) {
    headers.set("Content-Type", "application/json");
    init.body = JSON.stringify(body);
  }

  const response = await fetch(`${API_BASE_URL}${path}`, init);
  const requestId = response.headers.get("x-request-id") ?? undefined;
  const payload = (await response.json()) as ApiEnvelope<TData>;

  if (!response.ok || !payload.ok) {
    const error = "error" in payload ? payload.error : undefined;
    throw new ApiRequestError({
      message: error?.message ?? "Error no controlado de API.",
      code: error?.code ?? `ERR_HTTP_${response.status}`,
      status: response.status,
      requestId: error?.request_id ?? requestId,
      details: error?.details,
    });
  }

  return { data: payload.data, requestId };
}

export async function apiGet<TData>(path: string) {
  return apiRequest<TData>("GET", path);
}

export async function apiPost<TData, TPayload>(path: string, payload: TPayload) {
  return apiRequest<TData>("POST", path, payload);
}

export async function apiPatch<TData, TPayload>(path: string, payload: TPayload) {
  return apiRequest<TData>("PATCH", path, payload);
}

export async function apiDelete<TData>(path: string) {
  return apiRequest<TData>("DELETE", path);
}

export type ApiErrorPayload = {
  code: string;
  message: string;
  details?: Record<string, unknown>;
  request_id?: string;
};

export type ApiSuccessEnvelope<TData> = {
  ok: true;
  data: TData;
};

export type ApiErrorEnvelope = {
  ok: false;
  error: ApiErrorPayload;
};

export type ApiEnvelope<TData> = ApiSuccessEnvelope<TData> | ApiErrorEnvelope;

export class ApiRequestError extends Error {
  code: string;
  status: number;
  requestId?: string;
  details?: Record<string, unknown>;

  constructor(params: {
    message: string;
    code: string;
    status: number;
    requestId?: string;
    details?: Record<string, unknown>;
  }) {
    super(params.message);
    this.name = "ApiRequestError";
    this.code = params.code;
    this.status = params.status;
    this.requestId = params.requestId;
    this.details = params.details;
  }
}

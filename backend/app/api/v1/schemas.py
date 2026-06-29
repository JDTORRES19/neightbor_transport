from typing import Any, Literal

from pydantic import BaseModel, Field


class HealthData(BaseModel):
    status: str
    service: str


class HealthSuccessEnvelope(BaseModel):
    ok: Literal[True] = True
    data: HealthData


class ApiErrorPayload(BaseModel):
    code: str
    message: str
    details: dict[str, Any] = Field(default_factory=dict)
    request_id: str | None = None


class ApiErrorEnvelope(BaseModel):
    ok: Literal[False] = False
    error: ApiErrorPayload


class ProfileData(BaseModel):
    user_id: int
    display_name: str
    photo_url: str | None = None
    country_code: str
    phone_prefix: str
    phone_number: str
    phone_e164: str


class ProfileEnvelope(BaseModel):
    ok: Literal[True] = True
    data: ProfileData


class ProfileUpdateRequest(BaseModel):
    display_name: str | None = Field(default=None, min_length=2, max_length=120)
    photo_url: str | None = Field(default=None, max_length=400)
    country_code: str | None = Field(default=None, min_length=2, max_length=8)
    phone_prefix: str | None = Field(default=None, min_length=2, max_length=8)
    phone_number: str | None = Field(default=None, min_length=6, max_length=32)


class VehicleData(BaseModel):
    id: int
    brand: str
    reference: str
    color: str
    plate: str
    is_active: bool


class VehiclesListData(BaseModel):
    items: list[VehicleData]


class VehicleEnvelope(BaseModel):
    ok: Literal[True] = True
    data: VehicleData


class VehiclesListEnvelope(BaseModel):
    ok: Literal[True] = True
    data: VehiclesListData


class VehicleCreateRequest(BaseModel):
    brand: str = Field(min_length=1, max_length=100)
    reference: str = Field(min_length=1, max_length=120)
    color: str = Field(min_length=1, max_length=60)
    plate: str = Field(min_length=5, max_length=12)


class VehicleUpdateRequest(BaseModel):
    brand: str | None = Field(default=None, min_length=1, max_length=100)
    reference: str | None = Field(default=None, min_length=1, max_length=120)
    color: str | None = Field(default=None, min_length=1, max_length=60)
    plate: str | None = Field(default=None, min_length=5, max_length=12)


class TripDriverData(BaseModel):
    user_id: int
    display_name: str
    photo_url: str | None = None


class TripVehicleData(BaseModel):
    id: int
    brand: str
    reference: str
    color: str
    plate: str


class TripData(BaseModel):
    id: int
    direction: str
    origin_label: str
    departure_at: str
    published_at: str
    status: str
    total_seats: int
    available_seats: int
    driver: TripDriverData
    vehicle: TripVehicleData


class TripEnvelope(BaseModel):
    ok: Literal[True] = True
    data: TripData


class TripsListData(BaseModel):
    items: list[TripData]


class TripsListEnvelope(BaseModel):
    ok: Literal[True] = True
    data: TripsListData


class TripMaybeEnvelope(BaseModel):
    ok: Literal[True] = True
    data: TripData | None


class TripCreateRequest(BaseModel):
    direction: str = Field(min_length=3, max_length=20)
    origin_label: str = Field(min_length=3, max_length=160)
    departure_at: str = Field(min_length=8, max_length=64)
    total_seats: int = Field(ge=1, le=12)
    vehicle_id: int = Field(ge=1)


class TripRequestCreateRequest(BaseModel):
    pickup_label: str = Field(min_length=3, max_length=160)
    requested_seats: int = Field(ge=1, le=12)
    comment: str | None = Field(default=None, max_length=500)


class TripRequestRequesterData(BaseModel):
    user_id: int
    display_name: str
    photo_url: str | None = None


class TripRequestData(BaseModel):
    id: int
    trip_id: int
    pickup_label: str
    requested_seats: int
    comment: str | None = None
    status: str
    created_at: str
    decided_at: str | None = None
    requester: TripRequestRequesterData


class TripRequestEnvelope(BaseModel):
    ok: Literal[True] = True
    data: TripRequestData


class TripRequestsListData(BaseModel):
    items: list[TripRequestData]


class TripRequestsListEnvelope(BaseModel):
    ok: Literal[True] = True
    data: TripRequestsListData


class NotificationData(BaseModel):
    id: int
    user_id: int
    type: str
    title: str
    body: str
    payload: dict[str, Any] = Field(default_factory=dict)
    is_read: bool
    read_at: str | None = None
    created_at: str


class NotificationsListData(BaseModel):
    items: list[NotificationData]
    unread_count: int


class NotificationsListEnvelope(BaseModel):
    ok: Literal[True] = True
    data: NotificationsListData


class NotificationEnvelope(BaseModel):
    ok: Literal[True] = True
    data: NotificationData


class ReadAllNotificationsData(BaseModel):
    updated_count: int


class ReadAllNotificationsEnvelope(BaseModel):
    ok: Literal[True] = True
    data: ReadAllNotificationsData


class SchedulerJobRunData(BaseModel):
    id: int
    job_name: str
    status: str
    processed_count: int
    started_at: str
    finished_at: str | None = None


class EndpointLatencyData(BaseModel):
    method: str
    path: str
    status_code: int
    count: int
    avg_ms: float
    p95_ms: float
    max_ms: float


class MetricsOverviewData(BaseModel):
    trips_by_status: dict[str, int] = Field(default_factory=dict)
    requests_by_status: dict[str, int] = Field(default_factory=dict)
    total_notifications: int
    unread_notifications: int
    total_audit_events: int
    last_scheduler_run: SchedulerJobRunData | None = None
    latency_window_seconds: int
    endpoint_latency_ms: list[EndpointLatencyData] = Field(default_factory=list)


class MetricsOverviewEnvelope(BaseModel):
    ok: Literal[True] = True
    data: MetricsOverviewData

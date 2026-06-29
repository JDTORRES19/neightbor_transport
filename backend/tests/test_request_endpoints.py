from datetime import datetime, timezone
from concurrent.futures import ThreadPoolExecutor
import threading
import time

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import delete
from sqlalchemy import select

from app.main import app
from app.api.v1.routes import requests as requests_route
from app.infrastructure.database import SessionLocal, init_db
from app.infrastructure.models import Profile, Trip, TripRequest, Vehicle

client = TestClient(app)
SEEDED_VEHICLE_ID = 1


@pytest.fixture(autouse=True)
def reset_db_state() -> None:
    global SEEDED_VEHICLE_ID

    init_db()
    with SessionLocal() as db:
        db.execute(delete(TripRequest))
        db.execute(delete(Trip))
        db.execute(delete(Vehicle))
        db.execute(delete(Profile))

        db.add(
            Profile(
                user_id=1,
                display_name="Conductor Demo",
                photo_url=None,
                country_code="CO",
                phone_prefix="+57",
                phone_number="3001234567",
                phone_e164="+573001234567",
            )
        )
        db.add(
            Vehicle(
                user_id=1,
                brand="Mazda",
                reference="3 Touring",
                color="Rojo",
                plate="ABC123",
                is_active=True,
            )
        )
        db.commit()

        seeded_vehicle = db.scalar(
            select(Vehicle)
            .where(Vehicle.user_id == 1)
            .order_by(Vehicle.id.asc())
            .limit(1)
        )
        assert seeded_vehicle is not None
        SEEDED_VEHICLE_ID = seeded_vehicle.id


def _create_trip(total_seats: int = 2) -> int:
    response = client.post(
        "/api/v1/trips",
        json={
            "direction": "to_cali",
            "origin_label": "Unidad La Arboleda",
            "departure_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
            "total_seats": total_seats,
            "vehicle_id": SEEDED_VEHICLE_ID,
        },
    )
    assert response.status_code == 201
    return response.json()["data"]["id"]


def _create_request(trip_id: int, seats: int = 1) -> dict:
    response = client.post(
        f"/api/v1/trips/{trip_id}/requests",
        json={
            "pickup_label": "Porteria principal",
            "requested_seats": seats,
            "comment": "Voy con maleta",
        },
    )
    assert response.status_code == 201
    return response.json()["data"]


def _create_manual_trip(status: str = "cancelado", total_seats: int = 2) -> int:
    with SessionLocal() as db:
        manual_trip = Trip(
            user_id=1,
            vehicle_id=SEEDED_VEHICLE_ID,
            direction="to_cali",
            origin_label="Manual trip",
            departure_at=datetime.now(timezone.utc),
            total_seats=total_seats,
            status=status,
        )
        db.add(manual_trip)
        db.commit()
        db.refresh(manual_trip)
        return manual_trip.id


def _create_manual_request(
    trip_id: int,
    requester_user_id: int,
    seats: int = 1,
    status: str = "pendiente",
) -> int:
    with SessionLocal() as db:
        manual_request = TripRequest(
            trip_id=trip_id,
            requester_user_id=requester_user_id,
            pickup_label="Manual pickup",
            requested_seats=seats,
            comment="Manual request",
            status=status,
        )
        db.add(manual_request)
        db.commit()
        db.refresh(manual_request)
        return manual_request.id


def test_create_request_and_list_mine() -> None:
    trip_id = _create_trip(total_seats=3)
    created = _create_request(trip_id, seats=1)

    mine = client.get("/api/v1/requests/mine")
    assert mine.status_code == 200
    assert mine.json()["data"]["items"][0]["id"] == created["id"]
    assert mine.json()["data"]["items"][0]["status"] == "pendiente"


def test_duplicate_pending_request_is_rejected() -> None:
    trip_id = _create_trip(total_seats=3)
    _create_request(trip_id, seats=1)

    duplicate = client.post(
        f"/api/v1/trips/{trip_id}/requests",
        json={
            "pickup_label": "Porteria principal",
            "requested_seats": 1,
        },
    )
    assert duplicate.status_code == 409
    assert duplicate.json()["error"]["code"] == "ERR_TRIP_REQUEST_DUPLICATED"


def test_accept_request_marks_trip_full_when_capacity_reaches_zero() -> None:
    trip_id = _create_trip(total_seats=2)
    request_data = _create_request(trip_id, seats=2)

    accepted = client.post(f"/api/v1/requests/{request_data['id']}/accept")
    assert accepted.status_code == 200
    assert accepted.json()["data"]["status"] == "aceptada"

    my_trip = client.get("/api/v1/trips/mine/active")
    assert my_trip.status_code == 200
    assert my_trip.json()["data"]["status"] == "lleno"
    assert my_trip.json()["data"]["available_seats"] == 0


def test_cancel_accepted_request_reopens_trip_capacity() -> None:
    trip_id = _create_trip(total_seats=2)
    request_data = _create_request(trip_id, seats=2)
    accepted = client.post(f"/api/v1/requests/{request_data['id']}/accept")
    assert accepted.status_code == 200

    cancelled = client.post(f"/api/v1/requests/{request_data['id']}/cancel")
    assert cancelled.status_code == 200
    assert cancelled.json()["data"]["status"] == "cancelada"

    my_trip = client.get("/api/v1/trips/mine/active")
    assert my_trip.status_code == 200
    assert my_trip.json()["data"]["status"] == "activo"
    assert my_trip.json()["data"]["available_seats"] == 2


def test_reject_pending_request_changes_status() -> None:
    trip_id = _create_trip(total_seats=3)
    request_data = _create_request(trip_id, seats=1)

    rejected = client.post(f"/api/v1/requests/{request_data['id']}/reject")
    assert rejected.status_code == 200
    assert rejected.json()["data"]["status"] == "rechazada"


def test_accept_request_returns_concurrent_update_when_trip_row_locked() -> None:
    trip_id = _create_trip(total_seats=2)
    request_data = _create_request(trip_id, seats=1)

    locker = SessionLocal()
    try:
        locked_trip = locker.scalar(
            select(Trip)
            .where(Trip.id == trip_id)
            .with_for_update()
        )
        assert locked_trip is not None

        conflict = client.post(f"/api/v1/requests/{request_data['id']}/accept")
        assert conflict.status_code == 409
        assert conflict.json()["error"]["code"] == "ERR_CONCURRENT_UPDATE"
    finally:
        locker.rollback()
        locker.close()

    accepted = client.post(f"/api/v1/requests/{request_data['id']}/accept")
    assert accepted.status_code == 200
    assert accepted.json()["data"]["status"] == "aceptada"


def test_accept_request_returns_concurrent_update_when_request_row_locked() -> None:
    trip_id = _create_trip(total_seats=2)
    request_data = _create_request(trip_id, seats=1)

    locker = SessionLocal()
    try:
        locked_request = locker.scalar(
            select(TripRequest)
            .where(TripRequest.id == request_data["id"])
            .with_for_update()
        )
        assert locked_request is not None

        conflict = client.post(f"/api/v1/requests/{request_data['id']}/accept")
        assert conflict.status_code == 409
        assert conflict.json()["error"]["code"] == "ERR_CONCURRENT_UPDATE"
    finally:
        locker.rollback()
        locker.close()

    accepted = client.post(f"/api/v1/requests/{request_data['id']}/accept")
    assert accepted.status_code == 200
    assert accepted.json()["data"]["status"] == "aceptada"


def test_accept_request_returns_concurrent_update_when_same_requester_rows_locked() -> None:
    trip_id = _create_trip(total_seats=2)
    request_data = _create_request(trip_id, seats=1)

    other_trip_id = _create_manual_trip(status="cancelado", total_seats=2)
    locked_request_id = _create_manual_request(other_trip_id, requester_user_id=2)

    locker = SessionLocal()
    try:
        locked_request = locker.scalar(
            select(TripRequest)
            .where(TripRequest.id == locked_request_id)
            .with_for_update()
        )
        assert locked_request is not None

        conflict = client.post(f"/api/v1/requests/{request_data['id']}/accept")
        assert conflict.status_code == 409
        assert conflict.json()["error"]["code"] == "ERR_CONCURRENT_UPDATE"
    finally:
        locker.rollback()
        locker.close()

    accepted = client.post(f"/api/v1/requests/{request_data['id']}/accept")
    assert accepted.status_code == 200
    assert accepted.json()["data"]["status"] == "aceptada"


def test_accept_request_is_not_blocked_by_other_requester_lock() -> None:
    trip_id = _create_trip(total_seats=2)
    request_data = _create_request(trip_id, seats=1)

    other_trip_id = _create_manual_trip(status="cancelado", total_seats=2)
    locked_request_id = _create_manual_request(other_trip_id, requester_user_id=3)

    locker = SessionLocal()
    try:
        locked_request = locker.scalar(
            select(TripRequest)
            .where(TripRequest.id == locked_request_id)
            .with_for_update()
        )
        assert locked_request is not None

        accepted = client.post(f"/api/v1/requests/{request_data['id']}/accept")
        assert accepted.status_code == 200
        assert accepted.json()["data"]["status"] == "aceptada"
    finally:
        locker.rollback()
        locker.close()


def test_double_accept_same_request_returns_not_pending_on_second_attempt() -> None:
    trip_id = _create_trip(total_seats=2)
    request_data = _create_request(trip_id, seats=1)

    first_accept = client.post(f"/api/v1/requests/{request_data['id']}/accept")
    assert first_accept.status_code == 200
    assert first_accept.json()["data"]["status"] == "aceptada"

    second_accept = client.post(f"/api/v1/requests/{request_data['id']}/accept")
    assert second_accept.status_code == 409
    assert second_accept.json()["error"]["code"] == "ERR_REQUEST_NOT_PENDING"


def test_competing_requesters_for_last_seat_accepts_only_one() -> None:
    trip_id = _create_trip(total_seats=1)
    request_a = _create_request(trip_id, seats=1)
    request_b_id = _create_manual_request(trip_id, requester_user_id=3, seats=1)

    first_accept = client.post(f"/api/v1/requests/{request_a['id']}/accept")
    assert first_accept.status_code == 200
    assert first_accept.json()["data"]["status"] == "aceptada"

    second_accept = client.post(f"/api/v1/requests/{request_b_id}/accept")
    assert second_accept.status_code == 409
    assert second_accept.json()["error"]["code"] == "ERR_TRIP_NOT_ACCEPTING_REQUESTS"

    my_trip = client.get("/api/v1/trips/mine/active")
    assert my_trip.status_code == 200
    assert my_trip.json()["data"]["status"] == "lleno"
    assert my_trip.json()["data"]["available_seats"] == 0


def test_competing_requesters_lock_then_first_accept_blocks_second_by_capacity() -> None:
    trip_id = _create_trip(total_seats=1)
    request_a = _create_request(trip_id, seats=1)
    request_b_id = _create_manual_request(trip_id, requester_user_id=3, seats=1)

    locker = SessionLocal()
    try:
        locked_trip = locker.scalar(
            select(Trip)
            .where(Trip.id == trip_id)
            .with_for_update()
        )
        assert locked_trip is not None

        conflict = client.post(f"/api/v1/requests/{request_b_id}/accept")
        assert conflict.status_code == 409
        assert conflict.json()["error"]["code"] == "ERR_CONCURRENT_UPDATE"
    finally:
        locker.rollback()
        locker.close()

    first_accept = client.post(f"/api/v1/requests/{request_a['id']}/accept")
    assert first_accept.status_code == 200
    assert first_accept.json()["data"]["status"] == "aceptada"

    second_accept = client.post(f"/api/v1/requests/{request_b_id}/accept")
    assert second_accept.status_code == 409
    assert second_accept.json()["error"]["code"] == "ERR_TRIP_NOT_ACCEPTING_REQUESTS"


def test_parallel_accepts_do_not_overbook_last_seat() -> None:
    trip_id = _create_trip(total_seats=1)
    request_a = _create_request(trip_id, seats=1)
    request_b_id = _create_manual_request(trip_id, requester_user_id=3, seats=1)

    start_barrier = threading.Barrier(2)

    def _accept(request_id: int) -> tuple[int, str | None]:
        with TestClient(app) as local_client:
            start_barrier.wait(timeout=5)
            response = local_client.post(f"/api/v1/requests/{request_id}/accept")
            payload = response.json()
            if response.status_code == 200:
                return response.status_code, payload["data"]["status"]
            return response.status_code, payload.get("error", {}).get("code")

    with ThreadPoolExecutor(max_workers=2) as executor:
        result_a = executor.submit(_accept, request_a["id"])
        result_b = executor.submit(_accept, request_b_id)
        outcomes = [result_a.result(timeout=10), result_b.result(timeout=10)]

    success_count = sum(1 for status_code, status_or_code in outcomes if status_code == 200 and status_or_code == "aceptada")
    conflict_count = sum(1 for status_code, _ in outcomes if status_code == 409)

    assert success_count == 1
    assert conflict_count == 1

    by_trip = client.get(f"/api/v1/trips/{trip_id}/requests")
    assert by_trip.status_code == 200
    items = by_trip.json()["data"]["items"]
    accepted = [item for item in items if item["status"] == "aceptada"]
    assert len(accepted) == 1

    my_trip = client.get("/api/v1/trips/mine/active")
    assert my_trip.status_code == 200
    assert my_trip.json()["data"]["status"] == "lleno"
    assert my_trip.json()["data"]["available_seats"] == 0


def test_parallel_same_request_with_latency_returns_single_success_and_conflict(monkeypatch: pytest.MonkeyPatch) -> None:
    trip_id = _create_trip(total_seats=1)
    request_data = _create_request(trip_id, seats=1)

    original_accept = requests_route.accept_request_with_lock

    def delayed_accept_with_lock(db, request_id: int):
        result = original_accept(db, request_id)
        # Hold transaction open slightly longer to force NOWAIT lock contention.
        time.sleep(0.2)
        return result

    monkeypatch.setattr(requests_route, "accept_request_with_lock", delayed_accept_with_lock)

    start_barrier = threading.Barrier(2)

    def _accept_same_request() -> tuple[int, str | None]:
        with TestClient(app) as local_client:
            start_barrier.wait(timeout=5)
            response = local_client.post(f"/api/v1/requests/{request_data['id']}/accept")
            payload = response.json()
            if response.status_code == 200:
                return response.status_code, payload["data"]["status"]
            return response.status_code, payload.get("error", {}).get("code")

    with ThreadPoolExecutor(max_workers=2) as executor:
        first = executor.submit(_accept_same_request)
        second = executor.submit(_accept_same_request)
        outcomes = [first.result(timeout=10), second.result(timeout=10)]

    assert sum(1 for status_code, status_or_code in outcomes if status_code == 200 and status_or_code == "aceptada") == 1
    assert sum(1 for status_code, status_or_code in outcomes if status_code == 409 and status_or_code == "ERR_CONCURRENT_UPDATE") == 1


def test_parallel_competing_requesters_with_latency_conflict_then_capacity_reject(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    trip_id = _create_trip(total_seats=1)
    request_a = _create_request(trip_id, seats=1)
    request_b_id = _create_manual_request(trip_id, requester_user_id=3, seats=1)

    original_accept = requests_route.accept_request_with_lock

    def delayed_accept_with_lock(db, request_id: int):
        result = original_accept(db, request_id)
        # Hold transaction open slightly longer to force NOWAIT lock contention.
        time.sleep(0.2)
        return result

    monkeypatch.setattr(requests_route, "accept_request_with_lock", delayed_accept_with_lock)

    start_barrier = threading.Barrier(2)

    def _accept(request_id: int) -> tuple[int, int, str | None]:
        with TestClient(app) as local_client:
            start_barrier.wait(timeout=5)
            response = local_client.post(f"/api/v1/requests/{request_id}/accept")
            payload = response.json()
            if response.status_code == 200:
                return request_id, response.status_code, payload["data"]["status"]
            return request_id, response.status_code, payload.get("error", {}).get("code")

    with ThreadPoolExecutor(max_workers=2) as executor:
        result_a = executor.submit(_accept, request_a["id"])
        result_b = executor.submit(_accept, request_b_id)
        outcomes = [result_a.result(timeout=10), result_b.result(timeout=10)]

    assert sum(1 for _, status_code, status_or_code in outcomes if status_code == 200 and status_or_code == "aceptada") == 1
    assert sum(
        1
        for _, status_code, status_or_code in outcomes
        if status_code == 409 and status_or_code == "ERR_CONCURRENT_UPDATE"
    ) == 1

    loser_request_id = next(request_id for request_id, status_code, _ in outcomes if status_code == 409)
    retry = client.post(f"/api/v1/requests/{loser_request_id}/accept")
    assert retry.status_code == 409
    assert retry.json()["error"]["code"] == "ERR_TRIP_NOT_ACCEPTING_REQUESTS"

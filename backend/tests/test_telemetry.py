from time import time

from app.core.telemetry import endpoint_latency_snapshot, record_request_latency, reset_latency_registry


def test_latency_snapshot_filters_old_samples_by_window() -> None:
    reset_latency_registry()

    now_s = time()
    record_request_latency("GET", "/api/v1/trips", 200, 120.0, recorded_at_s=now_s - 1200)
    record_request_latency("GET", "/api/v1/trips", 200, 20.0, recorded_at_s=now_s - 5)

    snapshot_short = endpoint_latency_snapshot(limit=5, window_seconds=60)
    assert len(snapshot_short) == 1
    assert snapshot_short[0]["count"] == 1
    assert snapshot_short[0]["avg_ms"] == 20.0

    snapshot_long = endpoint_latency_snapshot(limit=5, window_seconds=1800)
    assert len(snapshot_long) == 1
    assert snapshot_long[0]["count"] == 2
    assert snapshot_long[0]["max_ms"] == 120.0

from collections import deque
from dataclasses import dataclass, field
from threading import Lock
from time import time


@dataclass
class EndpointLatencyStats:
    samples: deque[tuple[float, float]] = field(default_factory=lambda: deque(maxlen=500))


_latency_lock = Lock()
_latency_registry: dict[tuple[str, str, int], EndpointLatencyStats] = {}


def record_request_latency(
    method: str,
    path: str,
    status_code: int,
    duration_ms: float,
    *,
    recorded_at_s: float | None = None,
) -> None:
    key = (method.upper(), path, int(status_code))
    sample_time = recorded_at_s if recorded_at_s is not None else time()
    with _latency_lock:
        stats = _latency_registry.get(key)
        if stats is None:
            stats = EndpointLatencyStats()
            _latency_registry[key] = stats

        stats.samples.append((sample_time, max(0.0, duration_ms)))


def _p95(samples: list[float]) -> float:
    if not samples:
        return 0.0
    ordered = sorted(samples)
    index = int(round((len(ordered) - 1) * 0.95))
    return ordered[index]


def endpoint_latency_snapshot(
    *,
    limit: int = 10,
    window_seconds: int = 300,
) -> list[dict[str, float | int | str]]:
    rows: list[dict[str, float | int | str]] = []
    safe_limit = max(1, limit)
    safe_window_seconds = max(1, window_seconds)
    cutoff_s = time() - safe_window_seconds

    with _latency_lock:
        for (method, path, status_code), stats in _latency_registry.items():
            durations = [duration for sample_time, duration in stats.samples if sample_time >= cutoff_s]
            if len(durations) == 0:
                continue

            count = len(durations)
            avg_ms = sum(durations) / count
            p95_ms = _p95(durations)
            max_ms = max(durations)
            rows.append(
                {
                    "method": method,
                    "path": path,
                    "status_code": status_code,
                    "count": count,
                    "avg_ms": round(avg_ms, 2),
                    "p95_ms": round(p95_ms, 2),
                    "max_ms": round(max_ms, 2),
                }
            )

    rows.sort(key=lambda item: float(item["avg_ms"]), reverse=True)
    return rows[:safe_limit]


def reset_latency_registry() -> None:
    with _latency_lock:
        _latency_registry.clear()

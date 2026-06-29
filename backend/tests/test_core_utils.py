from datetime import datetime, timezone

from app.core.utils import normalize_plate, parse_iso_datetime_to_utc, utc_isoformat


def test_utc_isoformat_returns_none_for_none() -> None:
    assert utc_isoformat(None) is None


def test_utc_isoformat_converts_offset_datetime_to_z_suffix() -> None:
    dt = datetime.fromisoformat("2026-06-29T10:30:00-05:00")

    assert utc_isoformat(dt) == "2026-06-29T15:30:00Z"


def test_normalize_plate_removes_spaces_and_uppercases() -> None:
    assert normalize_plate(" ab c 123 ") == "ABC123"


def test_parse_iso_datetime_to_utc_from_z_string() -> None:
    parsed = parse_iso_datetime_to_utc("2026-06-29T15:30:00Z")

    assert parsed.isoformat() == "2026-06-29T15:30:00+00:00"


def test_parse_iso_datetime_to_utc_from_naive_string_assumes_utc() -> None:
    parsed = parse_iso_datetime_to_utc("2026-06-29T15:30:00")

    assert parsed.tzinfo == timezone.utc
    assert parsed.isoformat() == "2026-06-29T15:30:00+00:00"


def test_parse_iso_datetime_to_utc_from_offset_string() -> None:
    parsed = parse_iso_datetime_to_utc("2026-06-29T10:30:00-05:00")

    assert parsed.isoformat() == "2026-06-29T15:30:00+00:00"

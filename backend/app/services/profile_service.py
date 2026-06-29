from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.exceptions import DomainValidationException
from app.core.constants import DEFAULT_USER_ID
from app.infrastructure.models import Profile


def normalize_phone(phone_prefix: str, phone_number: str) -> str:
    if not phone_prefix or not phone_prefix.startswith("+"):
        raise DomainValidationException(
            code="ERR_PHONE_PREFIX_INVALID",
            message="El prefijo telefonico debe iniciar con +.",
        )

    normalized_number = "".join(ch for ch in phone_number if ch.isdigit())
    if not normalized_number:
        raise DomainValidationException(
            code="ERR_PHONE_INVALID",
            message="El numero de telefono no es valido.",
        )

    return f"{phone_prefix}{normalized_number}"


def ensure_profile_for_user(db: Session, user_id: int, fallback_name: str) -> Profile:
    profile = db.scalar(select(Profile).where(Profile.user_id == user_id))
    if profile is not None:
        return profile

    profile = Profile(
        user_id=user_id,
        display_name=fallback_name,
        photo_url=None,
        country_code="CO",
        phone_prefix="+57",
        phone_number="3001234567",
        phone_e164="+573001234567",
    )
    db.add(profile)
    db.commit()
    db.refresh(profile)
    return profile


def ensure_profile(db: Session) -> Profile:
    return ensure_profile_for_user(db, DEFAULT_USER_ID, "Usuario Demo")


def profile_payload(profile: Profile) -> dict[str, Any]:
    return {
        "user_id": profile.user_id,
        "display_name": profile.display_name,
        "photo_url": profile.photo_url,
        "country_code": profile.country_code,
        "phone_prefix": profile.phone_prefix,
        "phone_number": profile.phone_number,
        "phone_e164": profile.phone_e164,
    }

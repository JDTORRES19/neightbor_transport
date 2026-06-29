from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.v1.schemas import ApiErrorEnvelope, ProfileEnvelope, ProfileUpdateRequest
from app.core.responses import success_response
from app.infrastructure.database import get_db
from app.services.profile_service import ensure_profile, normalize_phone, profile_payload

router = APIRouter()


@router.patch(
    "/me",
    tags=["profile"],
    response_model=ProfileEnvelope,
    responses={422: {"model": ApiErrorEnvelope}},
)
def update_my_profile(payload: ProfileUpdateRequest, db: Session = Depends(get_db)):
    profile = ensure_profile(db)

    if payload.display_name is not None:
        profile.display_name = payload.display_name.strip() or profile.display_name
    if payload.photo_url is not None:
        profile.photo_url = payload.photo_url
    if payload.country_code is not None:
        profile.country_code = payload.country_code

    prefix = payload.phone_prefix if payload.phone_prefix is not None else profile.phone_prefix
    number = payload.phone_number if payload.phone_number is not None else profile.phone_number
    if payload.phone_prefix is not None or payload.phone_number is not None:
        profile.phone_prefix = prefix
        profile.phone_number = number
        profile.phone_e164 = normalize_phone(prefix, number)

    db.add(profile)
    db.commit()
    db.refresh(profile)
    return success_response(profile_payload(profile))


@router.get(
    "/me",
    tags=["profile"],
    response_model=ProfileEnvelope,
    responses={422: {"model": ApiErrorEnvelope}},
)
def get_my_profile(db: Session = Depends(get_db)):
    profile = ensure_profile(db)
    return success_response(profile_payload(profile))

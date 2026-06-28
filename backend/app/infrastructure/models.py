from datetime import datetime, timezone

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class Profile(Base):
    __tablename__ = "profiles"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(Integer, unique=True, index=True)
    display_name: Mapped[str] = mapped_column(String(120))
    photo_url: Mapped[str | None] = mapped_column(String(400), nullable=True)
    country_code: Mapped[str] = mapped_column(String(8), default="CO")
    phone_prefix: Mapped[str] = mapped_column(String(8), default="+57")
    phone_number: Mapped[str] = mapped_column(String(32))
    phone_e164: Mapped[str] = mapped_column(String(32), index=True)


class Vehicle(Base):
    __tablename__ = "vehicles"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(Integer, index=True)
    brand: Mapped[str] = mapped_column(String(100))
    reference: Mapped[str] = mapped_column(String(120))
    color: Mapped[str] = mapped_column(String(60))
    plate: Mapped[str] = mapped_column(String(12), index=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)


class Trip(Base):
    __tablename__ = "trips"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(Integer, index=True)
    vehicle_id: Mapped[int] = mapped_column(ForeignKey("vehicles.id"), index=True)
    direction: Mapped[str] = mapped_column(String(20), index=True)
    origin_label: Mapped[str] = mapped_column(String(160))
    departure_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    published_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        index=True,
    )
    status: Mapped[str] = mapped_column(String(20), index=True, default="activo")
    total_seats: Mapped[int] = mapped_column(Integer)


class TripRequest(Base):
    __tablename__ = "trip_requests"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    trip_id: Mapped[int] = mapped_column(ForeignKey("trips.id"), index=True)
    requester_user_id: Mapped[int] = mapped_column(Integer, index=True)
    pickup_label: Mapped[str] = mapped_column(String(160))
    requested_seats: Mapped[int] = mapped_column(Integer)
    comment: Mapped[str | None] = mapped_column(String(500), nullable=True)
    status: Mapped[str] = mapped_column(String(20), index=True, default="pendiente")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        index=True,
    )
    decided_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

from __future__ import annotations

from datetime import datetime
from typing import Any

from geoalchemy2 import Geometry
from sqlalchemy import JSON, BigInteger, DateTime, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class Amenity(Base):
    """Point-of-interest ingested from OSM or municipal datasets."""

    __tablename__ = "amenities"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    osm_id: Mapped[int] = mapped_column(BigInteger, unique=True, nullable=False)
    category: Mapped[str] = mapped_column(String(64), index=True, nullable=False)
    name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    metadata_: Mapped[dict[str, Any]] = mapped_column(
        "metadata", JSON, default=dict, nullable=False
    )
    location: Mapped[Any] = mapped_column(
        Geometry(geometry_type="POINT", srid=4326), nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    travel_time_cache = relationship(
        "HexagonAmenityTravelTime", back_populates="amenity", lazy="selectin"
    )

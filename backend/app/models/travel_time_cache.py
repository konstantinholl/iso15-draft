from __future__ import annotations

from datetime import datetime
from typing import Any

from geoalchemy2 import Geometry
from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class HexagonAmenityTravelTime(Base):
    """Precomputed travel-time relation between an H3 cell and an amenity."""

    __tablename__ = "hexagon_amenity_travel_times"
    __table_args__ = (
        UniqueConstraint("h3_cell_id", "amenity_id", "travel_mode", name="uq_hex_amenity_mode"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    h3_cell_id: Mapped[int] = mapped_column(
        ForeignKey("h3_grid_cells.id", ondelete="CASCADE"), nullable=False
    )
    amenity_id: Mapped[int] = mapped_column(
        ForeignKey("amenities.id", ondelete="CASCADE"), nullable=False
    )
    travel_mode: Mapped[str] = mapped_column(String(32), nullable=False)
    duration_seconds: Mapped[int] = mapped_column(Integer, nullable=False)
    distance_meters: Mapped[float | None] = mapped_column(Float, nullable=True)
    route_geometry: Mapped[Any] = mapped_column(
        Geometry(geometry_type="MULTILINESTRING", srid=4326),
        nullable=True,
    )
    computed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    h3_cell = relationship("H3GridCell", back_populates="travel_time_cache", lazy="joined")
    amenity = relationship("Amenity", back_populates="travel_time_cache", lazy="joined")

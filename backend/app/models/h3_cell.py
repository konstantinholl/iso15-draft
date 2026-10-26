from __future__ import annotations

from datetime import datetime
from typing import Any

from geoalchemy2 import Geometry
from sqlalchemy import DateTime, Integer, SmallInteger, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class H3GridCell(Base):
    """Hexagonal grid cell used for citywide accessibility surfaces."""

    __tablename__ = "h3_grid_cells"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    h3_index: Mapped[str] = mapped_column(String(32), unique=True, nullable=False)
    resolution: Mapped[int] = mapped_column(SmallInteger, index=True, nullable=False)
    population_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    geometry: Mapped[Any] = mapped_column(
        Geometry(geometry_type="POLYGON", srid=4326), nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    travel_time_cache = relationship(
        "HexagonAmenityTravelTime", back_populates="h3_cell", lazy="selectin"
    )

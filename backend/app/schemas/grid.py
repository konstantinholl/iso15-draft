from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.schemas.common import BottleneckAmenity, TravelMode


class GridRequest(BaseModel):
    """Citywide H3 heatmap request payload."""

    model_config = ConfigDict(extra="forbid")

    resolution: int = Field(description="H3 resolution; currently supported: 9 or 10")
    transport_mode: TravelMode
    categories: list[str] = Field(default_factory=list)
    max_travel_time_minutes: int = Field(default=15, ge=1, le=120)

    @field_validator("resolution")
    @classmethod
    def validate_resolution(cls, value: int) -> int:
        if value not in {9, 10}:
            raise ValueError("resolution must be one of: 9, 10")
        return value


class GridCellAccessibility(BaseModel):
    """H3-indexed aggregate accessibility metrics for one cell."""

    model_config = ConfigDict(extra="forbid")

    h3_index: str
    mean_travel_time_seconds: float = Field(ge=0)
    bottleneck_amenity: BottleneckAmenity


class GridFeatureCollection(BaseModel):
    """GeoJSON FeatureCollection carrying H3 accessibility properties."""

    model_config = ConfigDict(extra="forbid")

    type: Literal["FeatureCollection"] = "FeatureCollection"
    features: list[dict] = Field(default_factory=list)


class GridResponse(BaseModel):
    """Combined citywide accessibility map contract."""

    model_config = ConfigDict(extra="forbid")

    cells: list[GridCellAccessibility] = Field(default_factory=list)
    geojson: GridFeatureCollection

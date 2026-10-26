from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.common import BottleneckAmenity, GeoJSONLineString, TravelMode


class InspectorRequest(BaseModel):
    """Micro-level pin-drop request for nearest amenity travel-time analysis."""

    model_config = ConfigDict(extra="forbid")

    lat: float = Field(ge=-90.0, le=90.0)
    lon: float = Field(ge=-180.0, le=180.0)
    travel_mode: TravelMode


class InspectorResponse(BaseModel):
    """Inspector response contract consumed by frontend detail panels."""

    model_config = ConfigDict(extra="forbid")

    bottleneck_amenity: BottleneckAmenity
    travel_times_by_category: dict[str, int] = Field(
        default_factory=dict,
        description="Category-to-travel-time map in seconds.",
    )
    is_compliant: bool
    route_geometry: GeoJSONLineString

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.schemas.common import GeoJSONLineString, TravelMode

INSPECTOR_CATEGORIES = (
    "food",
    "healthcare",
    "education",
    "transit",
    "recreation",
    "civic_services",
)


class InspectorRequest(BaseModel):
    """Micro-level pin-drop request for nearest amenity travel-time analysis."""

    model_config = ConfigDict(extra="forbid")

    latitude: float | None = Field(default=None, ge=-90.0, le=90.0)
    longitude: float | None = Field(default=None, ge=-180.0, le=180.0)
    lat: float | None = Field(default=None, ge=-90.0, le=90.0)
    lon: float | None = Field(default=None, ge=-180.0, le=180.0)
    travel_mode: TravelMode

    @model_validator(mode="after")
    def normalize_coordinates(self) -> InspectorRequest:
        if self.latitude is None:
            self.latitude = self.lat
        if self.longitude is None:
            self.longitude = self.lon
        if self.latitude is None or self.longitude is None:
            raise ValueError("latitude and longitude are required")
        return self


class InspectorResponse(BaseModel):
    """Inspector response contract consumed by frontend detail panels."""

    model_config = ConfigDict(extra="forbid")

    latitude: float
    longitude: float
    travel_mode: TravelMode
    is_15_min_compliant: bool
    bottleneck_category: str | None
    categories: dict[str, CategoryInspection]
    missing_categories: list[str] = Field(default_factory=list)
    bottleneck_route: GeoJSONLineString | None = None


class CategoryInspection(BaseModel):
    """Closest reachable amenity result and its actual map location."""

    model_config = ConfigDict(extra="forbid")

    amenity_id: int
    name: str | None
    latitude: float
    longitude: float
    duration_seconds: int
    duration_minutes: float
    distance_meters: float


InspectorResponse.model_rebuild()

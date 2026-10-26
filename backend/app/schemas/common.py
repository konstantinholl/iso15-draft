from __future__ import annotations

from enum import StrEnum
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class TravelMode(StrEnum):
    pedestrian = "pedestrian"
    bicycle = "bicycle"


class BottleneckAmenity(StrEnum):
    grocery = "grocery"
    healthcare = "healthcare"
    education = "education"
    recreation = "recreation"
    public_transport = "public_transport"
    other = "other"


class GeoJSONLineString(BaseModel):
    """GeoJSON line string used for route geometry responses."""

    model_config = ConfigDict(extra="forbid")

    type: Literal["LineString"] = "LineString"
    coordinates: list[tuple[float, float]] = Field(min_length=2)

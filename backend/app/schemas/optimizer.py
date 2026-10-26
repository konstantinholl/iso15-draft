from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.common import TravelMode


class OptimizerRequest(BaseModel):
    """Amenity placement optimization request for candidate H3 cells."""

    model_config = ConfigDict(extra="forbid")

    target_amenity_type: str = Field(min_length=1, max_length=64)
    candidate_budget_k: int = Field(ge=1, le=100)
    land_use_exclusions: list[str] = Field(default_factory=list)
    transport_mode: TravelMode


class RecommendedCell(BaseModel):
    """One recommended H3 centroid with utility score and rank."""

    model_config = ConfigDict(extra="forbid")

    rank: int = Field(ge=1)
    h3_index: str
    centroid_lat: float = Field(ge=-90.0, le=90.0)
    centroid_lon: float = Field(ge=-180.0, le=180.0)
    utility_score: float = Field(ge=0)


class OptimizerResponse(BaseModel):
    """Ordered optimization output for frontend scenario analysis."""

    model_config = ConfigDict(extra="forbid")

    recommendations: list[RecommendedCell] = Field(default_factory=list)

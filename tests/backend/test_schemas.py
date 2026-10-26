from __future__ import annotations

import pytest
from app.schemas.grid import GridRequest
from app.schemas.inspector import (
    CategoryInspection,
    InspectorRequest,
    InspectorResponse,
)
from app.schemas.optimizer import OptimizerRequest
from pydantic import ValidationError


def test_inspector_request_accepts_valid_payload() -> None:
    payload = InspectorRequest(lat=48.5216, lon=9.0576, travel_mode="pedestrian")
    assert payload.travel_mode.value == "pedestrian"


def test_inspector_response_includes_amenity_location() -> None:
    result = CategoryInspection(
        amenity_id=1,
        name="Central Library",
        latitude=48.5217,
        longitude=9.0577,
        duration_seconds=420,
        duration_minutes=7.0,
        distance_meters=650.0,
    )

    response = InspectorResponse(
        latitude=48.5216,
        longitude=9.0576,
        travel_mode="pedestrian",
        is_15_min_compliant=True,
        bottleneck_category="civic_services",
        categories={"civic_services": result},
    )

    assert response.categories["civic_services"].name == "Central Library"
    assert response.categories["civic_services"].longitude == 9.0577


def test_grid_request_rejects_invalid_resolution() -> None:
    with pytest.raises(ValidationError):
        GridRequest(resolution=8, transport_mode="bicycle")


def test_optimizer_request_requires_budget() -> None:
    with pytest.raises(ValidationError):
        OptimizerRequest(
            target_amenity_type="grocery",
            candidate_budget_k=0,
            land_use_exclusions=[],
            transport_mode="pedestrian",
        )

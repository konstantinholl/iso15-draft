from __future__ import annotations

import pytest
from pydantic import ValidationError

from app.schemas.grid import GridRequest
from app.schemas.inspector import InspectorRequest
from app.schemas.optimizer import OptimizerRequest


def test_inspector_request_accepts_valid_payload() -> None:
    payload = InspectorRequest(lat=48.5216, lon=9.0576, travel_mode="pedestrian")
    assert payload.travel_mode.value == "pedestrian"


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

from __future__ import annotations

from fastapi.testclient import TestClient

from app.main import create_app


def test_health_endpoint_responds() -> None:
    client = TestClient(create_app())

    response = client.get("/health")

    assert response.status_code == 200
    body = response.json()
    assert body["status"] in {"ok", "degraded"}
    assert set(body["dependencies"]) == {"postgis", "valhalla"}


def test_route_stubs_are_not_implemented_yet() -> None:
    client = TestClient(create_app())

    response = client.post(
        "/api/v1/inspector", json={"lat": 48.5, "lon": 9.0, "travel_mode": "pedestrian"}
    )

    assert response.status_code == 501
    assert "next_step" in response.json()["detail"]

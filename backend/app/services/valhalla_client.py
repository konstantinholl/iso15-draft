from __future__ import annotations

from collections.abc import Sequence
from http import HTTPStatus

import httpx

from app.core.config import settings
from app.schemas.common import TravelMode


class ValhallaClientError(RuntimeError):
    """Raised when Valhalla requests fail and no fallback response is available."""


class ValhallaClient:
    """Async HTTP client for Valhalla route and matrix APIs."""

    def __init__(self, base_url: str | None = None, timeout_seconds: float | None = None) -> None:
        self.base_url = (base_url or settings.valhalla_url).rstrip("/")
        self.timeout_seconds = timeout_seconds or settings.valhalla_timeout_seconds

    async def healthcheck(self) -> bool:
        """Return True if Valhalla status endpoint responds with success."""

        endpoint = f"{self.base_url}/status"
        try:
            async with httpx.AsyncClient(timeout=self.timeout_seconds) as client:
                response = await client.get(endpoint)
                return response.status_code == HTTPStatus.OK
        except httpx.HTTPError:
            return False

    async def route_one_to_one(
        self,
        *,
        origin: tuple[float, float],
        destination: tuple[float, float],
        mode: TravelMode,
    ) -> dict:
        """Call Valhalla route API for one origin and one destination."""

        payload = {
            "locations": [self._format_location(origin), self._format_location(destination)],
            "costing": mode.value,
            "format": "geojson",
            "directions_options": {"units": "kilometers"},
        }
        return await self._post_json("/route", payload)

    async def route_matrix_one_to_many(
        self,
        *,
        origin: tuple[float, float],
        destinations: Sequence[tuple[float, float]],
        mode: TravelMode,
    ) -> dict:
        """Call Valhalla matrix API for one origin and multiple destinations."""

        if not destinations:
            raise ValueError("destinations must contain at least one coordinate pair")

        payload = {
            "sources": [self._format_location(origin)],
            "targets": [self._format_location(destination) for destination in destinations],
            "costing": mode.value,
            "units": "kilometers",
        }
        return await self._post_json("/sources_to_targets", payload)

    async def _post_json(self, path: str, payload: dict) -> dict:
        endpoint = f"{self.base_url}{path}"
        try:
            async with httpx.AsyncClient(timeout=self.timeout_seconds) as client:
                response = await client.post(endpoint, json=payload)
                response.raise_for_status()
                return response.json()
        except (httpx.TimeoutException, httpx.HTTPStatusError, httpx.TransportError) as exc:
            raise ValhallaClientError(f"Valhalla request failed at {path}: {exc}") from exc

    @staticmethod
    def _format_location(point: tuple[float, float]) -> dict[str, float]:
        lat, lon = point
        return {"lat": lat, "lon": lon}

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import Any

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import SessionLocal
from app.schemas.common import GeoJSONLineString, TravelMode
from app.schemas.inspector import INSPECTOR_CATEGORIES, CategoryInspection, InspectorResponse
from app.services.valhalla_client import ValhallaClient

SEARCH_RADIUS_METERS = 5_000.0
CANDIDATES_PER_CATEGORY = 3
CATEGORY_POI_TYPES: dict[str, tuple[str, ...]] = {
    "food": ("supermarket", "bakery", "convenience", "greengrocer"),
    "healthcare": ("pharmacy", "doctors", "clinic"),
    "education": (
        "kindergarten",
        "school",
        "primary_school",
        "secondary_school",
        "primary_secondary_school",
    ),
    "transit": (
        "bus_stop",
        "bus stop",
        "tram_stop",
        "tram stop",
        "train_platform",
        "train platform",
        "train_station",
        "train station",
    ),
    "recreation": ("park", "public_park", "playground", "sports_centre", "sports_center"),
    "civic_services": ("post_office", "post office", "bank", "atm", "library"),
}


class InspectorError(RuntimeError):
    """Base error for a pin inspection that cannot produce a valid result."""


class MissingAmenitiesError(InspectorError):
    """Raised when one or more required categories have no nearby facilities."""

    def __init__(self, categories: Sequence[str]) -> None:
        self.categories = list(categories)
        super().__init__(f"No nearby amenities for categories: {', '.join(self.categories)}")


@dataclass(frozen=True)
class Candidate:
    amenity_id: int
    category: str
    latitude: float
    longitude: float


async def inspect_point(
    lat: float,
    lon: float,
    mode: TravelMode,
    *,
    db: AsyncSession | None = None,
    valhalla: ValhallaClient | None = None,
) -> InspectorResponse:
    """Inspect the nearest reachable amenity in each essential category."""

    owns_session = db is None
    session = db or SessionLocal()
    try:
        candidates = await _find_candidates(session, lat, lon)
    finally:
        if owns_session:
            await session.close()

    missing = [category for category in INSPECTOR_CATEGORIES if not candidates[category]]
    if missing:
        raise MissingAmenitiesError(missing)

    client = valhalla or ValhallaClient()
    flattened = [
        candidate for category in INSPECTOR_CATEGORIES for candidate in candidates[category]
    ]
    matrix = await client.route_matrix_one_to_many(
        origin=(lat, lon),
        destinations=[(candidate.latitude, candidate.longitude) for candidate in flattened],
        mode=mode,
    )
    durations, distances = _parse_matrix(matrix, len(flattened))

    results: dict[str, CategoryInspection] = {}
    best_candidates: dict[str, Candidate] = {}
    offset = 0
    for category in INSPECTOR_CATEGORIES:
        category_candidates = flattened[offset : offset + len(candidates[category])]
        category_durations = durations[offset : offset + len(category_candidates)]
        category_distances = distances[offset : offset + len(category_candidates)]
        offset += len(category_candidates)
        best_index = min(
            range(len(category_candidates)),
            key=lambda index: category_durations[index],
        )
        best = category_candidates[best_index]
        duration = category_durations[best_index]
        results[category] = CategoryInspection(
            amenity_id=best.amenity_id,
            duration_seconds=duration,
            duration_minutes=round(duration / 60, 1),
            distance_meters=category_distances[best_index],
        )
        best_candidates[category] = best

    bottleneck = max(INSPECTOR_CATEGORIES, key=lambda category: results[category].duration_seconds)
    route = await _route_geometry(
        client,
        origin=(lat, lon),
        destination=(
            best_candidates[bottleneck].latitude,
            best_candidates[bottleneck].longitude,
        ),
        mode=mode,
    )
    return InspectorResponse(
        latitude=lat,
        longitude=lon,
        travel_mode=mode,
        is_15_min_compliant=all(result.duration_seconds <= 900 for result in results.values()),
        bottleneck_category=bottleneck,
        categories=results,
        bottleneck_route=route,
    )


async def _find_candidates(
    session: AsyncSession, lat: float, lon: float
) -> dict[str, list[Candidate]]:
    query = text(
        """
        SELECT id, category, ST_Y(location) AS latitude, ST_X(location) AS longitude
        FROM amenities
        WHERE regexp_replace(lower(category), '[ /-]+', '_', 'g')
            = ANY(CAST(:poi_types AS text[]))
          AND ST_DWithin(
              location::geography,
              ST_SetSRID(ST_MakePoint(:lon, :lat), 4326)::geography,
              :radius
          )
        ORDER BY location::geography <-> ST_SetSRID(
            ST_MakePoint(:lon, :lat), 4326
        )::geography
        """
    )
    result = await session.execute(
        query,
        {
            "lat": lat,
            "lon": lon,
            "radius": SEARCH_RADIUS_METERS,
            "poi_types": [
                _normalize_poi_type(poi_type)
                for types in CATEGORY_POI_TYPES.values()
                for poi_type in types
            ],
        },
    )
    candidates = {category: [] for category in INSPECTOR_CATEGORIES}
    for row in result:
        category = _category_for_type(row.category)
        if category and len(candidates[category]) < CANDIDATES_PER_CATEGORY:
            candidates[category].append(
                Candidate(row.id, category, float(row.latitude), float(row.longitude))
            )
    return candidates


def _category_for_type(poi_type: str) -> str | None:
    normalized = _normalize_poi_type(poi_type)
    return next(
        (category for category, types in CATEGORY_POI_TYPES.items() if normalized in types),
        None,
    )


def _normalize_poi_type(poi_type: str) -> str:
    return poi_type.casefold().replace(" ", "_").replace("-", "_").replace("/", "_")


def _parse_matrix(matrix: dict[str, Any], count: int) -> tuple[list[int], list[float]]:
    sources = matrix.get("sources_to_targets")
    if not isinstance(sources, list) or not sources or not isinstance(sources[0], list):
        raise InspectorError("Valhalla returned an invalid matrix response")
    targets = sources[0]
    if len(targets) != count:
        raise InspectorError("Valhalla matrix response does not match candidate count")
    durations: list[int] = []
    distances: list[float] = []
    for target in targets:
        if target.get("time") is None or target.get("distance") is None:
            raise InspectorError("Valhalla could not route to a nearby amenity")
        durations.append(round(float(target["time"])))
        distances.append(float(target["distance"]) * 1000)
    return durations, distances


async def _route_geometry(
    client: ValhallaClient,
    *,
    origin: tuple[float, float],
    destination: tuple[float, float],
    mode: TravelMode,
) -> GeoJSONLineString:
    response = await client.route_one_to_one(origin=origin, destination=destination, mode=mode)
    geometry = response.get("geometry") or response.get("trip", {}).get("geometry")
    if geometry and geometry.get("type") == "LineString":
        return GeoJSONLineString(coordinates=[tuple(point) for point in geometry["coordinates"]])
    for feature in response.get("features", []):
        geometry = feature.get("geometry", {})
        if geometry.get("type") == "LineString":
            return GeoJSONLineString(
                coordinates=[tuple(point) for point in geometry["coordinates"]]
            )
    raise InspectorError("Valhalla returned no GeoJSON route geometry")

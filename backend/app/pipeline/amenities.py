from __future__ import annotations

import argparse
import asyncio
from collections.abc import Iterable
from dataclasses import dataclass
from typing import Any

import httpx
from sqlalchemy import text

from app.core.config import settings
from app.db.session import SessionLocal

OVERPASS_TIMEOUT_SECONDS = 180.0
OVERPASS_HEADERS = {
    "Accept": "application/json",
    "User-Agent": "iso15-draft/0.1 (amenity ingestion)",
}
OSM_TAG_TO_CATEGORY: tuple[tuple[str, str, str], ...] = (
    ("amenity", "clinic", "healthcare"),
    ("amenity", "doctors", "healthcare"),
    ("amenity", "kindergarten", "education"),
    ("amenity", "library", "civic_services"),
    ("amenity", "post_office", "civic_services"),
    ("amenity", "school", "education"),
    ("amenity", "university", "education"),
    ("amenity", "bank", "civic_services"),
    ("amenity", "pharmacy", "healthcare"),
    ("amenity", "bus_station", "transit"),
    ("amenity", "parking", "civic_services"),
    ("shop", "supermarket", "food"),
    ("shop", "bakery", "food"),
    ("shop", "convenience", "food"),
    ("shop", "greengrocer", "food"),
    ("leisure", "park", "recreation"),
    ("leisure", "playground", "recreation"),
    ("leisure", "sports_centre", "recreation"),
    ("highway", "bus_stop", "transit"),
    ("railway", "station", "transit"),
    ("railway", "halt", "transit"),
    ("railway", "tram_stop", "transit"),
)


@dataclass(frozen=True)
class AmenityRecord:
    """Normalized OSM amenity ready for insertion into PostGIS."""

    osm_id: int
    category: str
    name: str | None
    latitude: float
    longitude: float
    metadata: dict[str, Any]


def build_overpass_query(latitude: float, longitude: float, radius_km: float) -> str:
    """Build an Overpass query for all supported amenity tags around a point."""

    radius_meters = round(radius_km * 1_000)
    clauses = "\n".join(
        f'  nwr["{key}"="{value}"](around:{radius_meters},{latitude},{longitude});'
        for key, value, _ in OSM_TAG_TO_CATEGORY
    )
    return (
        f"[out:json][timeout:{int(OVERPASS_TIMEOUT_SECONDS)}];\n(\n{clauses}\n);\nout center tags;"
    )


def normalize_elements(elements: Iterable[dict[str, Any]]) -> list[AmenityRecord]:
    """Convert Overpass elements into deduplicated records with point locations."""

    records: dict[int, AmenityRecord] = {}
    for element in elements:
        tags = element.get("tags")
        if not isinstance(tags, dict):
            continue
        category = _category_for_tags(tags)
        coordinates = _coordinates_for_element(element)
        osm_id = element.get("id")
        if category is None or coordinates is None or not isinstance(osm_id, int):
            continue
        latitude, longitude = coordinates
        records[osm_id] = AmenityRecord(
            osm_id=osm_id,
            category=category,
            name=_optional_string(tags.get("name")),
            latitude=latitude,
            longitude=longitude,
            metadata={"osm_type": element.get("type"), "tags": dict(tags)},
        )
    return list(records.values())


async def fetch_amenities(
    latitude: float,
    longitude: float,
    radius_km: float,
    *,
    overpass_url: str = settings.overpass_url,
    client: httpx.AsyncClient | None = None,
) -> list[AmenityRecord]:
    """Fetch and normalize supported amenities from the Overpass API."""

    query = build_overpass_query(latitude, longitude, radius_km)
    owns_client = client is None
    http_client = client or httpx.AsyncClient(timeout=OVERPASS_TIMEOUT_SECONDS)
    try:
        response = await http_client.post(
            overpass_url,
            data={"data": query},
            headers=OVERPASS_HEADERS,
        )
        response.raise_for_status()
        payload = response.json()
    finally:
        if owns_client:
            await http_client.aclose()
    elements = payload.get("elements") if isinstance(payload, dict) else None
    if not isinstance(elements, list):
        raise ValueError("Overpass returned a response without an elements list")
    return normalize_elements(elements)


async def upsert_amenities(records: Iterable[AmenityRecord]) -> int:
    """Insert or update normalized amenities and return the number processed."""

    records = list(records)
    if not records:
        return 0
    query = text(
        """
        INSERT INTO amenities (osm_id, category, name, metadata, location)
        VALUES (
            :osm_id, :category, :name, CAST(:metadata AS json),
            ST_SetSRID(ST_MakePoint(:longitude, :latitude), 4326)
        )
        ON CONFLICT (osm_id) DO UPDATE SET
            category = EXCLUDED.category,
            name = EXCLUDED.name,
            metadata = EXCLUDED.metadata,
            location = EXCLUDED.location
        """
    )
    async with SessionLocal.begin() as session:
        for record in records:
            await session.execute(
                query,
                {
                    "osm_id": record.osm_id,
                    "category": record.category,
                    "name": record.name,
                    "metadata": _json_dumps(record.metadata),
                    "latitude": record.latitude,
                    "longitude": record.longitude,
                },
            )
    return len(records)


async def load_amenities(
    *,
    latitude: float = settings.default_lat,
    longitude: float = settings.default_lon,
    radius_km: float = settings.amenity_ingestion_radius_km,
    overpass_url: str = settings.overpass_url,
) -> int:
    """Fetch amenities for the study area and persist them in PostGIS."""

    records = await fetch_amenities(latitude, longitude, radius_km, overpass_url=overpass_url)
    return await upsert_amenities(records)


def _category_for_tags(tags: dict[str, Any]) -> str | None:
    for key, value, category in OSM_TAG_TO_CATEGORY:
        if tags.get(key) == value:
            return value if category != "transit" else _transit_type(tags)
    return None


def _transit_type(tags: dict[str, Any]) -> str:
    if tags.get("highway") == "bus_stop" or tags.get("amenity") == "bus_station":
        return "bus_stop"
    if tags.get("railway") == "tram_stop":
        return "tram_stop"
    return "train_station"


def _coordinates_for_element(element: dict[str, Any]) -> tuple[float, float] | None:
    if isinstance(element.get("lat"), (float, int)) and isinstance(
        element.get("lon"), (float, int)
    ):
        return float(element["lat"]), float(element["lon"])
    center = element.get("center")
    if (
        isinstance(center, dict)
        and isinstance(center.get("lat"), (float, int))
        and isinstance(center.get("lon"), (float, int))
    ):
        return float(center["lat"]), float(center["lon"])
    return None


def _optional_string(value: Any) -> str | None:
    return value if isinstance(value, str) and value else None


def _json_dumps(value: dict[str, Any]) -> str:
    import json

    return json.dumps(value, separators=(",", ":"))


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Load OSM amenities into PostGIS.")
    parser.add_argument("--latitude", type=float, default=settings.default_lat)
    parser.add_argument("--longitude", type=float, default=settings.default_lon)
    parser.add_argument("--radius-km", type=float, default=settings.amenity_ingestion_radius_km)
    parser.add_argument("--overpass-url", default=settings.overpass_url)
    return parser.parse_args()


if __name__ == "__main__":
    arguments = _parse_args()
    loaded_count = asyncio.run(
        load_amenities(
            latitude=arguments.latitude,
            longitude=arguments.longitude,
            radius_km=arguments.radius_km,
            overpass_url=arguments.overpass_url,
        )
    )
    print(f"Loaded {loaded_count} amenities.")

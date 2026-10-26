from __future__ import annotations

from app.pipeline.amenities import OVERPASS_HEADERS, build_overpass_query, normalize_elements


def test_build_overpass_query_contains_radius_and_supported_tags() -> None:
    query = build_overpass_query(48.5, 9.0, 2.5)

    assert "[out:json]" in query
    assert "around:2500,48.5,9.0" in query
    assert '["amenity"="school"]' in query
    assert '["shop"="supermarket"]' in query
    assert OVERPASS_HEADERS["Accept"] == "application/json"


def test_normalize_elements_handles_nodes_and_centers() -> None:
    records = normalize_elements(
        [
            {
                "type": "node",
                "id": 1,
                "lat": 48.5,
                "lon": 9.0,
                "tags": {"amenity": "school", "name": "Primary School"},
            },
            {
                "type": "way",
                "id": 2,
                "center": {"lat": 48.51, "lon": 9.01},
                "tags": {"shop": "supermarket"},
            },
            {"type": "node", "id": 3, "tags": {"amenity": "school"}},
        ]
    )

    assert [(record.osm_id, record.category) for record in records] == [
        (1, "school"),
        (2, "supermarket"),
    ]
    assert records[1].latitude == 48.51
    assert records[0].metadata["tags"]["name"] == "Primary School"

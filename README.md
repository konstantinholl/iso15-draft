# The 15-Minute City — Measuring and Improving Neighborhood Accessibility

Production-grade scaffold for a geospatial data science platform that evaluates and improves neighborhood accessibility.

## Architecture

- **backend/** — FastAPI + Pydantic v2 + SQLAlchemy 2.0/GeoAlchemy2
  - `app/api/` route stubs for `inspector`, `grid`, and `optimizer`
  - `app/schemas/` strict request/response contracts shared with frontend
  - `app/models/` PostGIS-backed domain models and travel-time cache tables
  - `app/services/valhalla_client.py` async routing client wrapper
  - `alembic/` migration foundation + initial schema migration
- **frontend/** — React + Vite + TypeScript app shell for deck.gl + MapLibre integration
- **data/** — raw/interim/processed datasets (tracked via `.gitkeep`; data files ignored)
- **docker/** — backend/frontend Dockerfiles + PostGIS init scripts
- **tests/** — focused backend contract and API skeleton tests

## Prerequisites

- Docker + Docker Compose
- Python 3.11+
- Node.js 20+
- [uv](https://github.com/astral-sh/uv)

## Quickstart

1. Copy and adapt environment values:
   ```bash
   cp .env.example .env
   ```
2. Start local stack:
   ```bash
   make run
   ```
3. Backend health check:
   ```bash
   curl http://localhost:8000/health
   ```
4. Frontend dev UI:
   - open `http://localhost:5173`

## Developer Commands

- `make run` — build and run all services locally
- `make test` — run backend tests with pytest
- `make lint` — run Ruff lint + format checks
- `make ingest-osm` — fetch supported OSM amenities around the configured study location and upsert them into PostGIS

## Environment Highlights

- Default study location is set to **Tübingen** (`48.5216`, `9.0576`).
- `DATABASE_URL` targets PostGIS-enabled PostgreSQL.
- `VALHALLA_URL` points to the local Valhalla container.
- `VALHALLA_TILES_URL` defaults to the Baden-Württemberg OSM extract, which includes Tübingen and keeps local Valhalla initialization smaller than a Germany-wide extract.
- `OVERPASS_URL` selects the Overpass API endpoint used by amenity ingestion.
- `AMENITY_INGESTION_RADIUS_KM` controls the default loading radius around `DEFAULT_LAT`/`DEFAULT_LON` (10 km by default).

## Loading amenities

After the database is running and migrations have completed, load the default Tübingen study area:

```bash
make ingest-osm
```

The loader is idempotent: rerunning it updates existing OSM records by `osm_id` instead of creating duplicates. A custom area can be supplied with:

```bash
cd backend
python -m app.pipeline.amenities --latitude 48.5216 --longitude 9.0576 --radius-km 10
```

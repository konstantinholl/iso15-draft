.PHONY: run test lint ingest-osm

run:
	docker compose up --build

test:
	cd backend && python -m pytest ../tests/backend

lint:
	cd backend && python -m ruff check app ../tests/backend
	cd backend && python -m ruff format --check app ../tests/backend

ingest-osm:
	cd backend && python -m app.pipeline.amenities

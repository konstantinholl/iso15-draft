"""Initial PostGIS schema scaffold."""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from geoalchemy2 import Geometry

revision = "20261026_000001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "amenities",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("osm_id", sa.BigInteger(), nullable=False, unique=True),
        sa.Column("category", sa.String(length=64), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=True),
        sa.Column("metadata", sa.JSON(), nullable=False, server_default=sa.text("'{}'::json")),
        sa.Column("location", Geometry(geometry_type="POINT", srid=4326), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_amenities_category", "amenities", ["category"], unique=False)

    op.create_table(
        "h3_grid_cells",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("h3_index", sa.String(length=32), nullable=False, unique=True),
        sa.Column("resolution", sa.SmallInteger(), nullable=False),
        sa.Column("population_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("geometry", Geometry(geometry_type="POLYGON", srid=4326), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_h3_grid_resolution", "h3_grid_cells", ["resolution"], unique=False)

    op.create_table(
        "hexagon_amenity_travel_times",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("h3_cell_id", sa.Integer(), sa.ForeignKey("h3_grid_cells.id", ondelete="CASCADE"), nullable=False),
        sa.Column("amenity_id", sa.Integer(), sa.ForeignKey("amenities.id", ondelete="CASCADE"), nullable=False),
        sa.Column("travel_mode", sa.String(length=32), nullable=False),
        sa.Column("duration_seconds", sa.Integer(), nullable=False),
        sa.Column("distance_meters", sa.Float(), nullable=True),
        sa.Column("route_geometry", Geometry(geometry_type="MULTILINESTRING", srid=4326), nullable=True),
        sa.Column("computed_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("h3_cell_id", "amenity_id", "travel_mode", name="uq_hex_amenity_mode"),
    )


def downgrade() -> None:
    op.drop_table("hexagon_amenity_travel_times")
    op.drop_index("ix_h3_grid_resolution", table_name="h3_grid_cells")
    op.drop_table("h3_grid_cells")
    op.drop_index("ix_amenities_category", table_name="amenities")
    op.drop_table("amenities")

from __future__ import annotations

from fastapi import APIRouter, HTTPException, status

from app.schemas.grid import GridRequest, GridResponse

router = APIRouter(prefix="/grid", tags=["grid"])


@router.post("", response_model=GridResponse)
async def get_citywide_grid(payload: GridRequest) -> GridResponse:
    """Return citywide H3 accessibility aggregations for map rendering."""

    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail={
            "message": "Grid pipeline not implemented yet.",
            "next_step": "Connect to precomputed cache and H3 feature serialization.",
            "request_sample": payload.model_dump(),
        },
    )

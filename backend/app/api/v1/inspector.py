from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db_session
from app.schemas.inspector import InspectorRequest, InspectorResponse
from app.services.pin_inspector import InspectorError, MissingAmenitiesError, inspect_point

router = APIRouter(prefix="/inspector", tags=["inspector"])


@router.post("/evaluate", response_model=InspectorResponse)
async def evaluate_inspector(
    payload: InspectorRequest,
    db: AsyncSession = Depends(get_db_session),  # noqa: B008
) -> InspectorResponse:
    """Evaluate accessibility from one dropped map pin."""

    try:
        return await inspect_point(
            payload.latitude,
            payload.longitude,
            payload.travel_mode,
            db=db,
        )
    except MissingAmenitiesError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={"message": str(exc), "missing_categories": exc.categories},
        ) from exc
    except InspectorError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail={"message": str(exc)},
        ) from exc


@router.post("", response_model=InspectorResponse)
async def run_inspector(payload: InspectorRequest) -> InspectorResponse:
    """Run pin-drop accessibility analysis for a single coordinate input."""

    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail={
            "message": "Inspector pipeline not implemented yet.",
            "next_step": "Wire request into accessibility service and Valhalla adapter.",
            "request_sample": payload.model_dump(),
        },
    )

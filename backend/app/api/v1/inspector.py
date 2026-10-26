from __future__ import annotations

from fastapi import APIRouter, HTTPException, status

from app.schemas.inspector import InspectorRequest, InspectorResponse

router = APIRouter(prefix="/inspector", tags=["inspector"])


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

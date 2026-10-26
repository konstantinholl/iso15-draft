from __future__ import annotations

from fastapi import APIRouter, HTTPException, status

from app.schemas.optimizer import OptimizerRequest, OptimizerResponse

router = APIRouter(prefix="/optimizer", tags=["optimizer"])


@router.post("", response_model=OptimizerResponse)
async def run_optimizer(payload: OptimizerRequest) -> OptimizerResponse:
    """Rank candidate H3 cells for new amenity placement."""

    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail={
            "message": "Optimization pipeline not implemented yet.",
            "next_step": "Add objective function and budget-constrained selection logic.",
            "request_sample": payload.model_dump(),
        },
    )

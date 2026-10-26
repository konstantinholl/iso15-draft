from fastapi import APIRouter

from app.api.v1.grid import router as grid_router
from app.api.v1.inspector import router as inspector_router
from app.api.v1.optimizer import router as optimizer_router

api_router = APIRouter(prefix="/api/v1")
api_router.include_router(inspector_router)
api_router.include_router(grid_router)
api_router.include_router(optimizer_router)

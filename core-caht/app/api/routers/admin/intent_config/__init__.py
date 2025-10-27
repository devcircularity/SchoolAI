# app/api/routers/admin/intent_config/__init__.py
from fastapi import APIRouter

from .versions import router as versions_router
from .patterns import router as patterns_router
from .templates import router as templates_router
from .logs import router as logs_router
from .testing import router as testing_router
from .utils import router as utils_router

router = APIRouter(prefix="/admin/intent-config", tags=["Admin - Intent Configuration"])

# Include all sub-routers
router.include_router(versions_router)
router.include_router(patterns_router) 
router.include_router(templates_router)
router.include_router(logs_router)
router.include_router(testing_router)
router.include_router(utils_router)

__all__ = ["router"]
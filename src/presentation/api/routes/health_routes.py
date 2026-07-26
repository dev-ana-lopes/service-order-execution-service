from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

from ....infrastructure.config.settings import Settings
from ....infrastructure.readiness import ReadinessChecker

router = APIRouter(tags=["health"])


def get_app_settings(request: Request) -> Settings:
    return request.app.state.settings


def get_readiness_checker(request: Request) -> ReadinessChecker:
    return request.app.state.readiness_checker


@router.get("/health")
async def health_check(request: Request) -> dict:
    settings = get_app_settings(request)
    return {
        "status": "ok",
        "service": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "environment": settings.ENVIRONMENT,
    }


@router.get("/health/live")
async def live_check(request: Request) -> dict:
    settings = get_app_settings(request)
    return {
        "status": "ok",
        "service": settings.APP_NAME,
        "version": settings.APP_VERSION,
    }


@router.get("/health/ready")
async def readiness_check(request: Request) -> JSONResponse:
    readiness = get_readiness_checker(request).check()
    return JSONResponse(status_code=readiness.status_code, content=readiness.payload)

from fastapi import APIRouter

from app.core.config import APP_VERSION
from app.schemas.health import HealthResponse

router = APIRouter(tags=["Estado"])


@router.get("/health", response_model=HealthResponse, summary="Consultar salud del proceso")
def health() -> HealthResponse:
    """Comprueba disponibilidad; no certifica una base de datos ni un modelo."""
    return HealthResponse(version=APP_VERSION)

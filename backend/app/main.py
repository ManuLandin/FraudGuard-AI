from contextlib import asynccontextmanager
from fastapi import FastAPI
from starlette.responses import JSONResponse
from sqlalchemy.exc import SQLAlchemyError
from fastapi.middleware.cors import CORSMiddleware

from app.api.ml_dashboard import router as ml_dashboard_router
from app.api.transactions import router as transactions_router
from app.database.session import setup_database
from app.core.body_limit import UploadBodyLimit

from app.api.health import router as health_router
from app.core.config import APP_VERSION, Settings


def create_app(settings: Settings | None = None) -> FastAPI:
    settings = settings if settings is not None else Settings()
    @asynccontextmanager
    async def lifespan(application):
        engine, factory = setup_database(settings.database_url)
        application.state.session_factory = factory
        try:
            yield
        finally:
            engine.dispose()

    application = FastAPI(
        lifespan=lifespan,
        title="FraudGuard AI",
        version=APP_VERSION,
        description="Proyecto académico de detección de anomalías. Importación de transacciones sintéticas y salud del proceso.",
    )
    application.state.settings = settings
    application.add_middleware(UploadBodyLimit, max_bytes=settings.max_upload_bytes + 65536)
    application.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=False,
        allow_methods=["GET", "POST"],
        allow_headers=["Accept", "Content-Type"],
    )
    @application.exception_handler(SQLAlchemyError)
    async def database_error(_request, _exc):
        return JSONResponse({"detail": "La base de datos no está disponible. Vuelve a intentarlo."}, status_code=503)

    application.include_router(health_router)
    application.include_router(transactions_router)
    application.include_router(ml_dashboard_router)
    return application


app = create_app()

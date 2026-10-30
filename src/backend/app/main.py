from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from datetime import datetime
from typing import Literal

from fastapi import APIRouter, FastAPI, Response
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, ConfigDict
from pydantic.alias_generators import to_camel

from app.api_router import api_router
from app.core.config import Settings
from app.core.container import Container, build_container
from app.core.database import DatabaseUnavailableError
from app.core.deps import ContainerDep
from app.core.errors import UnexpectedErrorMiddleware, register_error_handlers
from app.core.logging import RequestLogMiddleware, configure_logging

API_PREFIX = "/api/v1"


class Health(BaseModel):
    model_config = ConfigDict(alias_generator=to_camel, validate_by_name=True)

    status: Literal["OK", "DEGRADED"]
    database: Literal["OK", "UNAVAILABLE"]
    worker_last_job_at: datetime | None


health_router = APIRouter(tags=["Health"])


@health_router.get("/health", response_model=Health, responses={503: {"model": Health}})
def get_health(container: ContainerDep, response: Response) -> Health:
    try:
        last_job_at = container.health.last_job_finished_at()
    except DatabaseUnavailableError:
        response.status_code = 503
        return Health(status="DEGRADED", database="UNAVAILABLE", worker_last_job_at=None)
    return Health(status="OK", database="OK", worker_last_job_at=last_job_at)


def create_app(container: Container | None = None) -> FastAPI:
    container = container or build_container(Settings())
    configure_logging(container.settings.log_level)

    @asynccontextmanager
    async def lifespan(_: FastAPI) -> AsyncIterator[None]:
        yield
        container.engine.dispose()

    app = FastAPI(title="CIC API", version="1.0.0", lifespan=lifespan)
    app.state.container = container
    app.add_middleware(UnexpectedErrorMiddleware)
    if container.settings.cors_origins:
        app.add_middleware(
            CORSMiddleware,
            allow_origins=container.settings.cors_origins,
            allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE"],
            allow_headers=["Authorization", "Content-Type"],
        )
    app.add_middleware(RequestLogMiddleware)
    register_error_handlers(app)
    app.include_router(health_router)
    app.include_router(api_router, prefix=API_PREFIX)
    return app

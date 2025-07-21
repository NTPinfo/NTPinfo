from contextlib import asynccontextmanager
from typing import Union, Any, AsyncGenerator
from fastapi import FastAPI, Request, Response
from fastapi.exceptions import HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware

from server.app.utils.load_config_data import verify_if_config_is_set
from server.app.db_config import init_engine
from server.app.models.Base import Base
from server.app.api.routing import router
from server.app.rate_limiter import limiter
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
import os


def create_app(dev: bool = True) -> FastAPI:
    """
    Create and configure a FastAPI application instance.

    This function sets up the FastAPI app with necessary middleware, routes,
    and lifecycle event handlers. It optionally initializes the database engine
    and verifies configuration during development mode.

    Args:
        dev (bool): Flag indicating whether the app runs in development mode.
                    If True, config verification and database initialization are performed.

    Returns:
        FastAPI: Configured FastAPI application instance.

    Raises:
        Exception: If configuration verification fails in development mode.
    """
    if dev:
        try:
            verify_if_config_is_set()
        except Exception as e:
            print(f"Configuration error: {e}")
            raise

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncGenerator[None, Any]:
        """
        Application lifespan context manager.

        Initializes the database schema if in development mode.

        Args:
            app (FastAPI): The FastAPI application instance.

        Yields:
            None
        """
        if dev:
            engine = init_engine()
            Base.metadata.create_all(bind=engine)
        yield

    app = FastAPI(
        lifespan=lifespan,
        title="NTPInfo API",
        root_path="/api",
        description=(
            "API of the NTPInfo website. Through this API measurements of NTP servers "
            "can be performed based on IP or domain name. The API has 4 main routes "
            "that are presented in more detail below:"
        ),
        version="1.0.0",
        docs_url="/docs" if dev else None,
        redoc_url="/redoc" if dev else None,
        openapi_url="/openapi.json" if dev else None,
    )

    app.state.limiter = limiter
    app.include_router(router)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[os.getenv("CLIENT_URL", "http://127.0.0.1:5173"), "http://localhost"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.exception_handler(RateLimitExceeded)
    async def rate_limit_handler(request: Request, exc: RateLimitExceeded) -> Union[JSONResponse, Response]:
        """
        Handle rate limit exceeded exceptions by returning HTTP 429.

        Args:
            request (Request): The incoming HTTP request that triggered the exception.
            exc (RateLimitExceeded): The rate limit exception.

        Returns:
            Union[JSONResponse, Response]: Response indicating too many requests (HTTP 429).
        """
        return _rate_limit_exceeded_handler(request, exc)

    return app


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("server.app.main:create_app", reload=True)

if __name__ != "__main__":
    app = create_app(dev=False)

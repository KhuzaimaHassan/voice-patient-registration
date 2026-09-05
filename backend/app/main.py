"""
app/main.py
-----------
FastAPI application entry point.

Includes:
  - GET /health endpoint (system check)
  - /patients router (CRUD endpoints)
  - Global unified envelope error handlers (404, 422, 500)

Reference: docs/03-api-spec.md
"""

import logging

from fastapi import FastAPI, HTTPException, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.config import get_settings
from app.routers import patients, vapi_webhook
from app.schemas import APIResponse

# ---------------------------------------------------------------------------
# Logging setup
# ---------------------------------------------------------------------------

settings = get_settings()

logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL, logging.INFO),
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)

from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info(
        "Starting Voice Patient Registration API | env=%s | log_level=%s",
        settings.ENVIRONMENT,
        settings.LOG_LEVEL,
    )
    yield
    logger.info("Shutting down Voice Patient Registration API.")


# ---------------------------------------------------------------------------
# FastAPI app instance
# ---------------------------------------------------------------------------

app = FastAPI(
    title="Voice Patient Registration API",
    description=(
        "REST backend for the voice-AI patient registration system. "
        "Receives tool calls from Vapi.ai and persists patient records "
        "to Supabase Postgres."
    ),
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# ---------------------------------------------------------------------------
# CORS
# ---------------------------------------------------------------------------

if settings.allowed_origins_list:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.allowed_origins_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

# ---------------------------------------------------------------------------
# Global Exception Handlers
# Enforce the unified envelope shape: {"data": null, "error": "<message>"}
# ---------------------------------------------------------------------------

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(
    request: Request,
    exc: RequestValidationError,
) -> JSONResponse:
    """
    Handle Pydantic/FastAPI validation errors (HTTP 422).
    Extracts the first meaningful validation error message instead of dumping raw JSON.
    """
    errors = exc.errors()
    if errors:
        first_err = errors[0]
        loc = [str(l) for l in first_err.get("loc", []) if l != "body"]
        field_name = ".".join(loc) if loc else "request"
        msg = first_err.get("msg", "Invalid value")

        # Strip Pydantic's "Value error, " prefix if present
        if msg.startswith("Value error, "):
            msg = msg[len("Value error, "):]

        if msg.lower() == "field required":
            error_message = f"Validation failed: {field_name} is required."
        elif field_name and field_name.lower() in msg.lower():
            error_message = f"Validation failed: {msg}"
        elif field_name and field_name != "request":
            error_message = f"Validation failed: {field_name} - {msg}"
        else:
            error_message = f"Validation failed: {msg}"
    else:
        error_message = "Validation failed."

    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={"data": None, "error": error_message},
    )


from starlette.exceptions import HTTPException as StarletteHTTPException


@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(
    request: Request,
    exc: StarletteHTTPException,
) -> JSONResponse:
    """
    Handle HTTP exceptions (e.g. 404, 403) ensuring {"data": null, "error": "..."}.
    Covers both FastAPI-raised HTTPExceptions and Starlette routing 404s.
    """
    message = exc.detail if isinstance(exc.detail, str) else str(exc.detail)
    return JSONResponse(
        status_code=exc.status_code,
        content={"data": None, "error": message},
        headers=getattr(exc, "headers", None),
    )


@app.exception_handler(Exception)
async def generic_exception_handler(
    request: Request,
    exc: Exception,
) -> JSONResponse:
    """
    Handle unhandled exceptions (HTTP 500) ensuring {"data": null, "error": "..."}.
    """
    logger.exception("Unhandled server exception: %s", exc)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"data": None, "error": "Internal server error."},
    )




# ---------------------------------------------------------------------------
# Root & Health endpoints
# ---------------------------------------------------------------------------

@app.get(
    "/",
    response_model=APIResponse,
    summary="Root service status",
    tags=["system"],
)
async def root() -> APIResponse:
    """
    Returns service metadata and available endpoints.
    """
    return APIResponse(
        data={
            "name": "Voice Patient Registration API",
            "status": "ok",
            "version": "0.1.0",
            "health_check": "/health",
            "patients": "/patients",
        },
        error=None,
    )


@app.get(
    "/health",
    response_model=APIResponse,
    summary="Health check",
    tags=["system"],
)
async def health() -> APIResponse:
    """
    Returns a simple OK response.
    Does not touch the database.
    """
    return APIResponse(data={"status": "ok"}, error=None)


# ---------------------------------------------------------------------------
# Routers
# /patients endpoints mounted with prefix "" so paths remain /patients
# ---------------------------------------------------------------------------

app.include_router(patients.router)
app.include_router(vapi_webhook.router)

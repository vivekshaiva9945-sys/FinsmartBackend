import time
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.v1.router import api_router
from app.core.config import settings

app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description=(
        "Industrial-Grade Multi-Tenant Financial Literacy and Budget Planner API for Public & Educational Institutions. "
        "Complies with India's DPDP Act 2023, RBI Financial Education Standards, and OWASP ASVS L2."
    ),
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json"
)

# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def add_process_time_and_security_headers(request: Request, call_next):
    """Adds X-Process-Time header and security headers."""
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    response.headers["X-Process-Time-Ms"] = str(round(process_time * 1000, 2))
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    return response


# Mount API Version 1
app.include_router(api_router, prefix="/v1")


@app.get("/health", tags=["Health & Diagnostics"])
async def health_check():
    """Healthcheck endpoint for Docker Compose and Kubernetes readiness/liveness probes."""
    return {
        "status": "healthy",
        "service": settings.app_name,
        "version": settings.app_version,
        "environment": settings.environment
    }

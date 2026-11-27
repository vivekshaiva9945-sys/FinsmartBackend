import collections
import time
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, RedirectResponse

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

# Rate limiting storage: IP -> deque of timestamps
rate_limit_records = collections.defaultdict(collections.deque)
RATE_LIMIT_WINDOW = 60  # seconds
RATE_LIMITS = {
    "/v1/auth/login": 15,
    "/v1/auth/register": 10,
    "/v1/ai/chat": 20,
    "/v1/profiles/erasure": 5,
    "/v1/profiles/dsar-export": 10,
    "default": 300,
}


@app.middleware("http")
async def security_and_rate_limiting_middleware(request: Request, call_next):
    """
    Production security enforcement:
    1. Force HTTPS redirect when behind a reverse proxy in production.
    2. Rate limiting per IP to prevent brute-force and bot spam.
    3. OWASP ASVS L2 security headers (HSTS, nosniff, DENY, Referrer-Policy).
    """
    # 1. Force HTTPS in production
    if settings.environment == "production":
        forwarded_proto = request.headers.get("x-forwarded-proto", "")
        if forwarded_proto == "http":
            url = request.url.replace(scheme="https")
            return RedirectResponse(url=str(url), status_code=301)

    # 2. IP Rate Limiting
    client_ip = request.client.host if request.client else "127.0.0.1"
    path = request.url.path
    limit = RATE_LIMITS.get(path, RATE_LIMITS["default"])

    now = time.time()
    key = f"{client_ip}:{path}"
    history = rate_limit_records[key]

    # Purge timestamps outside the 60-second window
    while history and history[0] < now - RATE_LIMIT_WINDOW:
        history.popleft()

    if len(history) >= limit:
        return JSONResponse(
            status_code=429,
            content={
                "detail": "Rate limit exceeded. Too many requests. Please wait 60 seconds before retrying.",
                "retry_after_seconds": 60,
            },
            headers={"Retry-After": "60"}
        )

    history.append(now)

    # 3. Process Request and Apply Security Headers
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time

    response.headers["X-Process-Time-Ms"] = str(round(process_time * 1000, 2))
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Strict-Transport-Security"] = "max-age=63072000; includeSubDomains; preload"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=(), payment=()"

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

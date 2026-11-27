import logging
import time
from collections import defaultdict
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, HTTPException, status
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from app.config import get_settings
from app.rag.embed import get_embedding_model
from app.routers import auth, documents, ask, history, admin

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("searchlab")
settings = get_settings()

# In-memory sliding-window rate limiter
REQUEST_HISTORY = defaultdict(list)
RATE_LIMITS = {
    "/auth/login": (15, 60),     # 15 attempts per 60 seconds
    "/auth/register": (15, 60),  # 15 registrations per 60 seconds
    "/ask": (60, 60),            # 60 queries per 60 seconds
}

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Pre-load the fastembed embedding model once to prevent per-request overhead
    logger.info("Initializing SearchLab.AI backend services...")
    try:
        get_embedding_model()
        logger.info("Embedding model pre-loaded successfully.")
    except Exception as e:
        logger.warning(f"Embedding model pre-loading warning: {e}")
    yield
    logger.info("Shutting down SearchLab.AI backend services...")

app = FastAPI(
    title=settings.app_name,
    description="SearchLab.AI – Semantic Search with Grounded Answers & Citations",
    version="1.0.0",
    lifespan=lifespan
)

# CORS Middleware
origins = settings.cors_origins
# Also allow local frontend ports
for port in [5173, 3000, 8000]:
    local_url = f"http://localhost:{port}"
    if local_url not in origins:
        origins.append(local_url)
    local_ip = f"http://127.0.0.1:{port}"
    if local_ip not in origins:
        origins.append(local_ip)

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.middleware("http")
async def security_and_rate_limit_middleware(request: Request, call_next):
    # 1. Rate Limiting Check
    client_ip = request.client.host if request.client else "unknown"
    path = request.url.path
    now = time.time()

    for endpoint, (max_reqs, window_sec) in RATE_LIMITS.items():
        if path.startswith(endpoint):
            history = REQUEST_HISTORY[(client_ip, endpoint)]
            REQUEST_HISTORY[(client_ip, endpoint)] = [t for t in history if now - t < window_sec]
            if len(REQUEST_HISTORY[(client_ip, endpoint)]) >= max_reqs:
                return JSONResponse(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    content={
                        "error": "rate_limit_exceeded",
                        "message": f"Rate limit exceeded. Maximum {max_reqs} requests per {window_sec} seconds."
                    }
                )
            REQUEST_HISTORY[(client_ip, endpoint)].append(now)
            break

    response = await call_next(request)

    # 2. Add Production Security Headers
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["Permissions-Policy"] = "geolocation=(), camera=(), microphone=()"
    return response

# Global standardized error response handler
@app.exception_handler(HTTPException)
async def custom_http_exception_handler(request: Request, exc: HTTPException):
    if isinstance(exc.detail, dict) and "error" in exc.detail:
        return JSONResponse(status_code=exc.status_code, content=exc.detail)
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": "http_error", "message": str(exc.detail)}
    )

# Register routers
app.include_router(auth.router)
app.include_router(documents.router)
app.include_router(ask.router)
app.include_router(history.router)
app.include_router(admin.router)

@app.get("/health", tags=["system"])
async def health_check():
    """
    Production health check and keep-alive ping endpoint.
    Wakes the Render server from cold sleep.
    """
    return {
        "status": "healthy",
        "app": settings.app_name,
        "environment": settings.app_env
    }

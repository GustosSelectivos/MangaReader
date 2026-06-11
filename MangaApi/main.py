"""
main.py
=======
Entrypoint principal de MangaApiV2 (FastAPI).

Reemplaza:
  - MangaApi/MangaApi/wsgi.py (WSGI → ASGI)
  - MangaApi/MangaApi/urls.py (Django URL patterns → FastAPI APIRouter)
  - INSTALLED_APPS, MIDDLEWARE de settings.py

Flujo:
  Request → CORSMiddleware → APICallCounterMiddleware → DACAuditMiddleware
  → FastAPI Router → Depends(get_db) → Repository → Response

Lifespan:
  - Startup: verificar conexión a BD
  - Shutdown: cerrar engine async
"""

import logging
from contextlib import asynccontextmanager

import sentry_sdk
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware

from core.config import settings
from core.exceptions import register_exception_handlers
from middlewares.counter import APICallCounterMiddleware
from middlewares.audit import DACAuditMiddleware
from middlewares.request_logger import RequestLoggerMiddleware
from middlewares.security import SecurityHeadersMiddleware

from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from core.limiter import limiter

# ── Logging ───────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.DEBUG if settings.DEBUG else logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


# ── Sentry (equivalente al bloque sentry_sdk.init de settings.py de Django) ───
if settings.SENTRY_DSN:
    sentry_sdk.init(
        dsn=settings.SENTRY_DSN,
        traces_sample_rate=1.0,
        send_default_pii=True,
    )
    logger.info("Sentry inicializado.")


# ── Lifespan (reemplaza AppConfig.ready() y señales de Django) ───────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Startup y shutdown del servidor.
    Equivale al post_migrate signal y al AppConfig.ready() de Django.
    """
    logger.info("🚀 Iniciando MangaApiV2...")

    # Verificar conexión a BD
    from core.database import engine
    from sqlalchemy import text
    try:
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        logger.info("✅ Conexión a BD verificada.")
    except Exception as exc:
        logger.error("❌ No se pudo conectar a la BD: %s", exc)
        raise  # Fallo rápido: no arrancar sin BD

    yield  # ← servidor activo aquí

    # Shutdown
    logger.info("🛑 Cerrando MangaApiV2...")
    await engine.dispose()
    logger.info("✅ Engine de BD cerrado.")


# ── App ───────────────────────────────────────────────────────────────────────
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="API de Manga/Manhwa/Manhua – Migrado de Django REST Framework a FastAPI.",
    docs_url="/docs" if settings.DEBUG else None,   # Ocultar Swagger en producción
    redoc_url="/redoc" if settings.DEBUG else None,
    openapi_url="/openapi.json" if settings.DEBUG else None,
    lifespan=lifespan,
)


# ── Exception Handlers ────────────────────────────────────────────────────────
register_exception_handlers(app)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)


# ── Middlewares ───────────────────────────────────────────────────────────────
# Orden de capas (de afuera hacia adentro):


# 1. Security Headers (debe ir antes del ruteo para inyectar en toda respuesta)
app.add_middleware(SecurityHeadersMiddleware)

# 2. GZip (equivale a django.middleware.gzip.GZipMiddleware)
app.add_middleware(GZipMiddleware, minimum_size=1000)

# 3. DAC Audit (equivale a DACAuditMiddleware de Django – CORREGIDO)
app.add_middleware(DACAuditMiddleware)

# 4. API Call Counter (equivale a APICallCounterMiddleware de Django – MEJORADO)
app.add_middleware(APICallCounterMiddleware)

# 5. Request Logger (para visualizar detalles de tiempo, ip, status)
app.add_middleware(RequestLoggerMiddleware)

# 1. CORS (Debe ser el ÚLTIMO en añadirse para que sea la capa más externa y atrape OPTIONS)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_origin_regex=r"^https://.*\.(miswebtoons\.uk|up\.railway\.app|pages\.dev)$",
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["authorization", "content-type", "accept", "origin",
                   "user-agent", "x-requested-with"],
)


# ── Routers ───────────────────────────────────────────────────────────────────
from domains.mangas.router import router as mangas_router, home_router, b2_router
from domains.chapters.router import router as chapters_router
from domains.catalog.router import router as catalog_router
from domains.users.router import router as users_router
from domains.dac.router import router as dac_router
from domains.stats.router import router as stats_router

API_PREFIX = "/api"

app.include_router(mangas_router, prefix=API_PREFIX)      # /api/mangas/...
app.include_router(home_router, prefix=API_PREFIX)         # /api/home
app.include_router(b2_router, prefix=API_PREFIX)           # /api/b2/sign
app.include_router(chapters_router, prefix=API_PREFIX)     # /api/chapters/...
app.include_router(catalog_router, prefix=API_PREFIX)      # /api/catalog/...
app.include_router(users_router, prefix=API_PREFIX)        # /api/auth/...
app.include_router(dac_router, prefix=API_PREFIX)          # /api/dac/...
app.include_router(stats_router, prefix=API_PREFIX)        # /api/stats/...


# ── Health Check ──────────────────────────────────────────────────────────────
@app.get("/health", tags=["System"])
async def health_check():
    """
    Equivale a HealthCheckView de Django.
    Verifica estado de la BD.
    """
    from core.database import engine
    from sqlalchemy import text
    db_status = "ok"
    try:
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
    except Exception:
        db_status = "error"
    return {"status": "ok", "db": db_status}


# ── Dev runner ────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG,
        workers=1 if settings.DEBUG else 4,
    )

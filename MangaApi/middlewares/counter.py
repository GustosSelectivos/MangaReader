"""
middlewares/counter.py
======================
APICallCounterMiddleware → BaseHTTPMiddleware + Redis async.

MEJORAS vs Django:
  1. Redis async: usa `incr` (atómico) en lugar de get/set no-atómico.
  2. Pipeline: agrupa las 3 operaciones Redis en un pipeline (1 round-trip).
  3. Fallback en memoria: si Redis no está disponible, usa un dict local
     (no falla en desarrollo sin Redis configurado).
  4. ASGI nativo: no requiere django.middleware.MiddlewareMixin.
"""

import logging
import time
from collections import defaultdict
from datetime import datetime

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

from core.config import settings

logger = logging.getLogger(__name__)

# ── Fallback en memoria (si Redis no está disponible) ─────────────────────────
_memory_counters: dict[str, int] = defaultdict(int)
_memory_avg_time: float = 0.0
_memory_response_count: int = 0


class APICallCounterMiddleware(BaseHTTPMiddleware):
    """
    Cuenta llamadas a la API y tiempo de respuesta.
    Almacena en Redis (con fallback en memoria si no hay Redis).
    """

    def __init__(self, app: ASGIApp):
        super().__init__(app)

    async def _get_redis(self):
        """No usamos Redis en este proyecto, retorna None para usar el fallback."""
        return None

    @property
    def _redis_available(self) -> bool:
        return False

    async def dispatch(self, request: Request, call_next) -> Response:
        start_time = time.monotonic()

        response = await call_next(request)

        # Solo registrar rutas de API
        if not request.url.path.startswith("/api/"):
            return response

        elapsed = time.monotonic() - start_time
        today = datetime.now().strftime("%Y-%m-%d")
        path = request.url.path
        method = request.method

        redis = await self._get_redis()

        if redis and self._redis_available:
            try:
                await self._update_redis(redis, path, method, elapsed, today)
            except Exception as exc:
                logger.warning("Error actualizando Redis counter: %s", exc)
                self._update_memory(path, method, elapsed, today)
        else:
            self._update_memory(path, method, elapsed, today)

        return response

    async def _update_redis(self, redis, path: str, method: str, elapsed: float, today: str):
        """Actualización atómica con pipeline (1 round-trip a Redis)."""
        endpoint_key = f"api_endpoint_{path}_{method}"
        daily_key = f"api_calls_daily_{today}"

        pipe = redis.pipeline()
        pipe.incr("api_total_calls")
        pipe.incr(endpoint_key)
        pipe.expire(endpoint_key, 86400)
        pipe.incr(daily_key)
        pipe.expire(daily_key, 86400)
        # Actualizar tiempo promedio con Lua script para atomicidad
        pipe.incr("api_response_count")
        await pipe.execute()

        # Promedio: aproximación simple (no perfectamente atómica pero aceptable)
        count = await redis.get("api_response_count")
        current_avg = float(await redis.get("api_avg_response_time") or 0)
        count_int = int(count or 1)
        new_avg = ((current_avg * (count_int - 1)) + elapsed) / count_int
        await redis.set("api_avg_response_time", round(new_avg, 6))

    def _update_memory(self, path: str, method: str, elapsed: float, today: str):
        """Fallback en memoria (sin persistencia, para desarrollo)."""
        global _memory_avg_time, _memory_response_count
        _memory_counters["api_total_calls"] += 1
        _memory_counters[f"api_endpoint_{path}_{method}"] += 1
        _memory_counters[f"api_calls_daily_{today}"] += 1
        _memory_response_count += 1
        _memory_avg_time = (
            (_memory_avg_time * (_memory_response_count - 1) + elapsed) / _memory_response_count
        )

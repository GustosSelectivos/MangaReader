"""
domains/stats/router.py
========================
APIRouter para estadísticas de la API.

Reemplaza: APIStatsView + APIStatsResetView + get_recommendations() (DRF).
Lee los contadores desde Redis (o fallback en memoria del counter middleware).
"""

from datetime import datetime
from fastapi import APIRouter, Depends, status
from fastapi.responses import JSONResponse

from core.config import settings
from core.security import get_current_user, require_staff

router = APIRouter(prefix="/stats", tags=["API Stats"])


async def _get_redis():
    """Obtiene cliente Redis si está disponible."""
    if not settings.REDIS_ENABLED:
        return None
    try:
        import redis.asyncio as aioredis
        client = aioredis.from_url(settings.REDIS_URL, decode_responses=True)
        await client.ping()
        return client
    except Exception:
        return None


def _get_recommendations(stats: dict) -> list[dict]:
    """Equivale a get_recommendations() de stats_view.py de Django."""
    recommendations = []

    avg_time = stats.get("avg_response_time", 0)
    if avg_time > 1.0:
        recommendations.append({
            "type": "performance", "level": "warning",
            "message": f"Tiempo de respuesta promedio alto: {avg_time}s. Considera optimizar queries o agregar caché.",
        })
    elif avg_time > 0.5:
        recommendations.append({
            "type": "performance", "level": "info",
            "message": f"Tiempo de respuesta aceptable: {avg_time}s. Monitorea si aumenta.",
        })

    daily = stats.get("daily_calls", 0)
    if daily > 10000:
        recommendations.append({
            "type": "usage", "level": "warning",
            "message": f"{daily} llamadas hoy. Alto tráfico, considera rate limiting.",
        })
    elif daily > 5000:
        recommendations.append({
            "type": "usage", "level": "info",
            "message": f"{daily} llamadas hoy. Tráfico moderado-alto.",
        })

    endpoints = stats.get("endpoints_ranked", {})
    if endpoints:
        top_path, top_data = next(iter(endpoints.items()))
        recommendations.append({
            "type": "optimization", "level": "info",
            "message": f"Endpoint más usado: {top_path} con {top_data['total']} llamadas.",
        })

    return recommendations


@router.get("")
async def get_stats():
    """
    Equivale a APIStatsView.get() de DRF.
    Lee desde Redis si está disponible, fallback en memoria.
    """
    today = datetime.now().strftime("%Y-%m-%d")
    redis = await _get_redis()

    if redis:
        total_calls = int(await redis.get("api_total_calls") or 0)
        daily_calls = int(await redis.get(f"api_calls_daily_{today}") or 0)
        avg_response_time = round(float(await redis.get("api_avg_response_time") or 0), 3)
        response_count = int(await redis.get("api_response_count") or 0)

        # Obtener todas las keys de endpoints
        endpoint_keys = await redis.keys("api_endpoint_*")
        endpoints: dict = {}
        for key in endpoint_keys:
            parts = key.replace("api_endpoint_", "").rsplit("_", 1)
            if len(parts) == 2:
                path, method = parts
                count = int(await redis.get(key) or 0)
                endpoints.setdefault(path, {})[method] = count
    else:
        from middlewares.counter import _memory_counters, _memory_avg_time, _memory_response_count
        total_calls = _memory_counters.get("api_total_calls", 0)
        daily_calls = _memory_counters.get(f"api_calls_daily_{today}", 0)
        avg_response_time = round(_memory_avg_time, 3)
        response_count = _memory_response_count
        endpoints = {}
        for k, v in _memory_counters.items():
            if k.startswith("api_endpoint_"):
                parts = k.replace("api_endpoint_", "").rsplit("_", 1)
                if len(parts) == 2:
                    path, method = parts
                    endpoints.setdefault(path, {})[method] = v

    # Rankear endpoints
    endpoints_ranked = dict(
        sorted(
            {
                path: {"methods": methods, "total": sum(methods.values())}
                for path, methods in endpoints.items()
            }.items(),
            key=lambda x: x[1]["total"],
            reverse=True,
        )
    )

    stats = {
        "total_calls": total_calls,
        "daily_calls": daily_calls,
        "avg_response_time": avg_response_time,
        "response_count": response_count,
        "endpoints_ranked": endpoints_ranked,
    }
    stats["recommendations"] = _get_recommendations(stats)
    return stats


@router.post("/reset", status_code=status.HTTP_200_OK,
             dependencies=[Depends(require_staff)])
async def reset_stats():
    """Equivale a APIStatsResetView.post() de DRF. Solo staff."""
    today = datetime.now().strftime("%Y-%m-%d")
    redis = await _get_redis()

    if redis:
        keys_to_delete = ["api_total_calls", "api_avg_response_time", "api_response_count",
                          f"api_calls_daily_{today}"]
        endpoint_keys = await redis.keys("api_endpoint_*")
        keys_to_delete.extend(endpoint_keys)
        if keys_to_delete:
            await redis.delete(*keys_to_delete)
    else:
        from middlewares.counter import _memory_counters
        _memory_counters.clear()

    return {"message": "Estadísticas reseteadas correctamente"}

import sqlalchemy as sa
from fastapi import APIRouter, Depends, Query
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime, timezone, timedelta
from app.database import get_db
from app.auth import verify_token
from app.models.api_key import ApiKey
from app.models.request_log import RequestLog

router = APIRouter(prefix="/dashboard", tags=["dashboard"])

RANGE_MAP = {
    "24h": timedelta(hours=24),
    "7d": timedelta(days=7),
    "30d": timedelta(days=30),
}

@router.get("/stats")
async def get_stats(
    range: str = Query(default="7d", pattern="^(24h|7d|30d)$"),
    api_key: ApiKey = Depends(verify_token),
    db: AsyncSession = Depends(get_db),
):
    since = datetime.now(timezone.utc) - RANGE_MAP[range]

    base_filter = (RequestLog.api_key_id == api_key.id, RequestLog.created_at >= since)

    totals_result = await db.execute(
        select(
            func.count(RequestLog.id),
            func.coalesce(func.sum(RequestLog.cost), 0.0),
            func.coalesce(func.avg(RequestLog.latency_ms), 0.0),
            func.sum(func.cast(RequestLog.cache_hit, sa.Integer)),
        ).where(*base_filter)
    )
    total_requests, total_cost, avg_latency, cache_hits = totals_result.one()

    cache_hit_rate = (cache_hits / total_requests * 100) if total_requests else 0.0

    provider_result = await db.execute(
        select(RequestLog.provider, func.count(RequestLog.id))
        .where(*base_filter)
        .group_by(RequestLog.provider)
    )
    provider_breakdown = {provider: count for provider, count in provider_result.all()}

    return {
        "total_requests": total_requests,
        "total_cost": round(total_cost, 4),
        "cache_hit_rate": round(cache_hit_rate, 2),
        "avg_latency_ms": round(avg_latency, 2),
        "provider_breakdown": provider_breakdown,
    }
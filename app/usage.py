from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.request_log import RequestLog
from app.models.usage_summary import UsageSummary


async def record_usage(db: AsyncSession,
                       api_key_id: int,
                       model: str,
                       provider: str,
                       prompt_tokens: int,
                       completion_tokens: int,
                       cost: float,
                       cache_hit: bool = False,
                       latency_ms: int = 0) -> None:

    db.add(RequestLog(api_key_id=api_key_id,
                        model=model,
                        provider=provider,
                        prompt_tokens=prompt_tokens,
                        completion_tokens=completion_tokens,
                        cost=cost,
                        cache_hit=cache_hit,
                        latency_ms=latency_ms))

    today = datetime.now(UTC).date()

    result = await db.execute(select(UsageSummary).where(UsageSummary.api_key_id == api_key_id,
                                                          UsageSummary.usage_date == today))
    
    summary = result.scalar_one_or_none()

    if summary is None:
        summary = UsageSummary(
            api_key_id=api_key_id,
            usage_date=today,
            total_requests=1,
            total_cost=cost,
            total_tokens=prompt_tokens + completion_tokens,
        )
        db.add(summary)

    else:
        summary.total_requests += 1
        summary.total_cost += cost
        summary.total_tokens += prompt_tokens + completion_tokens

    await db.commit()


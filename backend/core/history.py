from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from backend.core.database import ChatHistory


async def save_turn(
    db: AsyncSession,
    profile_id: str,
    user_text: str,
    bot_text: str,
    domain: str,
):
    db.add(ChatHistory(
        profile_id=profile_id,
        role="user",
        content=user_text,
        domain=domain,
    ))
    db.add(ChatHistory(
        profile_id=profile_id,
        role="assistant",
        content=bot_text,
        domain=domain,
    ))
    await db.commit()


async def get_recent(
    db: AsyncSession,
    profile_id: str,
    limit: int = 8,
) -> list[dict]:
    result = await db.execute(
        select(ChatHistory)
        .where(ChatHistory.profile_id == profile_id)
        .order_by(ChatHistory.timestamp.desc())
        .limit(limit)
    )
    rows = result.scalars().all()
    return [{"role": r.role, "content": r.content} for r in reversed(rows)]
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import DiagramHistory


async def save_diagram_history(
    db: AsyncSession,
    *,
    title: str,
    source_code: str,
    classes: list,
    plantuml: str,
) -> DiagramHistory:
    history = DiagramHistory(
        title=title,
        source_code=source_code,
        classes=classes,
        plantuml=plantuml,
    )

    db.add(history)
    await db.commit()
    await db.refresh(history)

    return history


async def list_diagram_history(db: AsyncSession) -> list[DiagramHistory]:
    result = await db.execute(
        select(DiagramHistory).order_by(DiagramHistory.created_at.desc())
    )
    return list(result.scalars().all())
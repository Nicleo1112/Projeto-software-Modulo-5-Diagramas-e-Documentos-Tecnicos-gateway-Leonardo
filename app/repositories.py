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
    diagram_type: str | None = None,
    project_id: str | None = None,
    project_name: str | None = None,
) -> DiagramHistory:
    history = DiagramHistory(
        title=title,
        source_code=source_code,
        classes=classes,
        plantuml=plantuml,
        diagram_type=diagram_type,
        project_id=project_id,
        project_name=project_name,
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


async def list_diagrams_by_project(
    db: AsyncSession,
    project_id: str,
) -> list[DiagramHistory]:
    result = await db.execute(
        select(DiagramHistory)
        .where(DiagramHistory.project_id == project_id)
        .order_by(DiagramHistory.created_at.desc())
    )
    return list(result.scalars().all())

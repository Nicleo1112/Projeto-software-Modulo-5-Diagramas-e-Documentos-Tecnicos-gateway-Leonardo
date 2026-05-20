import logging
from typing import List

from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db, init_db, is_database_configured
from app.repositories import (
    list_diagram_history,
    list_diagrams_by_project,
    save_diagram_history,
)
from app.schemas import (
    ApiDocsRequest,
    ApiDocsResponse,
    DiagramHistoryItem,
    DiagramRequest,
    DiagramResponse,
)
from app.services.api_docs_flow import generate_api_documentation
from app.services.diagram_flow import generate_class_diagram

logger = logging.getLogger(__name__)

app = FastAPI(
    title="DoculA Gateway API",
    description="Microsservico orquestrador do Modulo 5. Integra Parser API e Diagram API.",
    version="0.3.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
async def startup():
    await init_db()


@app.get("/")
def root():
    return {
        "message": "DoculA Gateway API online",
        "docs": "/docs",
        "health": "/health",
        "history": "/diagram/history",
        "projects_history": "/projects/{project_id}/diagrams",
    }


@app.get("/health")
def health():
    return {
        "status": "ok",
        "service": "docula-gateway-api",
        "version": "0.3.0",
        "database": {
            "configured": is_database_configured()
        },
    }


@app.post("/api-docs/generate", response_model=ApiDocsResponse)
async def create_api_documentation(request: ApiDocsRequest):
    result = await generate_api_documentation(request.source_code)

    return {
        "title": request.title,
        "project_id": request.project_id,
        "project_name": request.project_name,
        "endpoints": result["endpoints"],
    }


@app.post("/diagram/class", response_model=DiagramResponse)
async def create_class_diagram(
    request: DiagramRequest,
    db: AsyncSession | None = Depends(get_db),
):
    result = await generate_class_diagram(request.source_code)

    if db is not None:
        try:
            await save_diagram_history(
                db,
                title=request.title,
                source_code=request.source_code,
                classes=result["classes"],
                plantuml=result["plantuml"],
                diagram_type=request.diagram_type,
                project_id=request.project_id,
                project_name=request.project_name,
            )
        except Exception as exc:
            await db.rollback()
            logger.warning("Falha ao salvar historico do diagrama: %s", exc)

    return {
        "title": request.title,
        "diagram_type": request.diagram_type or "uml-class",
        "project_id": request.project_id,
        "project_name": request.project_name,
        "classes": result["classes"],
        "plantuml": result["plantuml"],
    }


@app.get("/diagram/history", response_model=List[DiagramHistoryItem])
async def get_diagram_history(db: AsyncSession | None = Depends(get_db)):
    if db is None:
        raise HTTPException(
            status_code=503,
            detail="Banco de dados nao configurado. Defina DATABASE_URL para usar o historico.",
        )

    return await list_diagram_history(db)


@app.get("/projects/{project_id}/diagrams", response_model=List[DiagramHistoryItem])
async def get_project_diagrams(
    project_id: str,
    db: AsyncSession | None = Depends(get_db),
):
    if db is None:
        raise HTTPException(
            status_code=503,
            detail="Banco de dados nao configurado. Defina DATABASE_URL para usar o historico por projeto.",
        )

    return await list_diagrams_by_project(db, project_id)

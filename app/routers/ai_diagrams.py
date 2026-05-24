import logging

from fastapi import APIRouter, Depends, HTTPException, status

from app.schemas import AiDiagramGenerateRequest, AiDiagramGenerateResponse
from app.services.ai_diagram_service import gerar_diagrama_com_ia
from app.services.auth_token_service import exigir_token_bearer
from app.services.external_database_service import buscar_dados_bancos, listar_artefatos_modulo2


router = APIRouter(prefix="/api/modulo5/diagramas", tags=["Diagramas com IA"])
logger = logging.getLogger(__name__)


@router.get("/projetos/{projeto_id}/artefatos")
async def listar_artefatos_projeto(
    projeto_id: str,
    usuario: dict = Depends(exigir_token_bearer),
):
    return await listar_artefatos_modulo2(
        projeto_id=projeto_id,
        token=usuario.get("token"),
    )


@router.post("/gerar-ia", response_model=AiDiagramGenerateResponse)
async def gerar_diagrama_ia(
    request: AiDiagramGenerateRequest,
    usuario: dict = Depends(exigir_token_bearer),
):
    dados_bancos = await buscar_dados_bancos(
        projeto_id=request.projeto_id,
        token=usuario.get("token"),
        artifact_ids=request.artifact_ids,
    )

    try:
        return gerar_diagrama_com_ia(
            tipo_diagrama=request.tipo_diagrama,
            titulo=request.titulo,
            codigo_fonte=request.codigo_fonte,
            dados_bancos=dados_bancos,
        )
    except Exception as exc:
        logger.exception("Falha ao gerar diagrama com IA: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Nao foi possivel gerar o diagrama com IA agora. Tente novamente em instantes.",
        )

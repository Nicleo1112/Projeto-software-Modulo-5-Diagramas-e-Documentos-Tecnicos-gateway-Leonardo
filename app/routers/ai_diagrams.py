from fastapi import APIRouter, Depends, HTTPException, status

from app.schemas import AiDiagramGenerateRequest, AiDiagramGenerateResponse
from app.services.ai_diagram_service import gerar_diagrama_com_ia
from app.services.auth_token_service import exigir_token_bearer
from app.services.external_database_service import buscar_dados_bancos


router = APIRouter(prefix="/api/modulo5/diagramas", tags=["Diagramas com IA"])


@router.post("/gerar-ia", response_model=AiDiagramGenerateResponse)
async def gerar_diagrama_ia(
    request: AiDiagramGenerateRequest,
    _usuario: dict = Depends(exigir_token_bearer),
):
    dados_bancos = await buscar_dados_bancos(request.projeto_id)

    try:
        return gerar_diagrama_com_ia(
            tipo_diagrama=request.tipo_diagrama,
            titulo=request.titulo,
            codigo_fonte=request.codigo_fonte,
            dados_bancos=dados_bancos,
        )
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Nao foi possivel gerar o diagrama com IA agora. Tente novamente em instantes.",
        )

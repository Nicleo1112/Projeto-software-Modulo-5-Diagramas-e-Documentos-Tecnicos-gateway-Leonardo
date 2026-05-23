import os
from typing import Any

import httpx


MODULE2_UPLOAD_API_URL = os.getenv(
    "MODULE2_UPLOAD_API_URL",
    "https://docuia-api-upload.azurewebsites.net",
).rstrip("/")
MAX_ARTIFACTS = int(os.getenv("MODULE2_MAX_ARTIFACTS", "12"))
MAX_ARTIFACT_CHARS = int(os.getenv("MODULE2_MAX_ARTIFACT_CHARS", "6000"))
REQUEST_TIMEOUT_SECONDS = float(os.getenv("MODULE2_API_TIMEOUT_SECONDS", "15"))
TEXT_EXTENSIONS = {
    ".java",
    ".py",
    ".js",
    ".ts",
    ".tsx",
    ".jsx",
    ".cs",
    ".php",
    ".rb",
    ".go",
    ".kt",
    ".swift",
    ".sql",
    ".json",
    ".yaml",
    ".yml",
    ".xml",
    ".md",
    ".txt",
}
TEXT_TYPES = {
    "codigo-fonte",
    "código-fonte",
    "codigo fonte",
    "código fonte",
    "requisito",
    "documento",
    "ata",
}


async def buscar_dados_bancos(projeto_id: str | None, token: str | None = None) -> dict[str, Any]:
    if not projeto_id:
        return _mock_context("Projeto nao informado.")

    if not token:
        return _mock_context("Token JWT nao informado para consultar o Modulo 2.")

    headers = {"Authorization": f"Bearer {token}"}
    artefatos_url = f"{MODULE2_UPLOAD_API_URL}/api/projeto/{projeto_id}/artefatos"

    try:
        async with httpx.AsyncClient(timeout=REQUEST_TIMEOUT_SECONDS, follow_redirects=True) as client:
            response = await client.get(artefatos_url, headers=headers)
            response.raise_for_status()
            payload = response.json()

            artefatos = payload.get("artefatos", [])
            selected_artifacts = _select_relevant_artifacts(artefatos)
            files = []

            for artifact in selected_artifacts:
                files.append(await _build_artifact_context(client, artifact))
    except Exception as exc:
        return {
            "source": "module2_upload_api",
            "status": "unavailable",
            "project_id": projeto_id,
            "artifacts_endpoint": artefatos_url,
            "message": "Nao foi possivel consultar os artefatos do Modulo 2.",
            "error": str(exc),
            "files": [],
        }

    return {
        "source": "module2_upload_api",
        "status": "ok",
        "project_id": projeto_id,
        "artifacts_endpoint": artefatos_url,
        "artifacts_count": len(artefatos),
        "selected_artifacts_count": len(selected_artifacts),
        "files": files,
    }


async def _build_artifact_context(client: httpx.AsyncClient, artifact: dict[str, Any]) -> dict[str, Any]:
    document_url = artifact.get("url_documento")
    context = {
        "id": artifact.get("id"),
        "nome_arquivo": artifact.get("nome_arquivo"),
        "tipo": artifact.get("tipo"),
        "url_documento": document_url,
    }

    if not document_url:
        context["content_status"] = "missing_url"
        return context

    try:
        file_response = await client.get(document_url)
        file_response.raise_for_status()
        content = file_response.text
        context["content_status"] = "loaded"
        context["content"] = _truncate_content(content)
    except Exception as exc:
        context["content_status"] = "unavailable"
        context["error"] = str(exc)

    return context


def _select_relevant_artifacts(artefatos: list[dict[str, Any]]) -> list[dict[str, Any]]:
    relevant = [artifact for artifact in artefatos if _is_text_artifact(artifact)]

    if not relevant:
        relevant = artefatos

    return relevant[:MAX_ARTIFACTS]


def _is_text_artifact(artifact: dict[str, Any]) -> bool:
    file_name = str(artifact.get("nome_arquivo") or "").lower()
    artifact_type = str(artifact.get("tipo") or "").lower()

    return any(file_name.endswith(extension) for extension in TEXT_EXTENSIONS) or any(
        text_type in artifact_type for text_type in TEXT_TYPES
    )


def _truncate_content(content: str) -> str:
    if len(content) <= MAX_ARTIFACT_CHARS:
        return content

    return content[:MAX_ARTIFACT_CHARS] + "\n... conteudo truncado ..."


def _mock_context(message: str) -> dict[str, Any]:
    return {
        "source": "module2_upload_api",
        "status": "mock",
        "message": message,
        "files": [],
    }

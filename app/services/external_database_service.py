import os
import re
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


async def listar_artefatos_modulo2(projeto_id: str | None, token: str | None = None) -> dict[str, Any]:
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
    except Exception as exc:
        return {
            "source": "module2_upload_api",
            "status": "unavailable",
            "project_id": projeto_id,
            "artifacts_endpoint": artefatos_url,
            "message": "Nao foi possivel consultar os artefatos do Modulo 2.",
            "error": str(exc),
            "artifacts": [],
        }

    return {
        "source": "module2_upload_api",
        "status": "ok",
        "project_id": projeto_id,
        "artifacts_endpoint": artefatos_url,
        "artifacts_count": len(artefatos),
        "artifacts": [_summarize_artifact(artifact) for artifact in artefatos],
    }


async def buscar_dados_bancos(
    projeto_id: str | None,
    token: str | None = None,
    artifact_ids: list[int] | None = None,
) -> dict[str, Any]:
    artifacts_response = await listar_artefatos_modulo2(projeto_id=projeto_id, token=token)

    if artifacts_response.get("status") != "ok":
        return {
            **artifacts_response,
            "files": [],
        }

    artefatos = artifacts_response.get("artifacts", [])
    selected_artifacts = _select_relevant_artifacts(artefatos, artifact_ids)
    files = []

    async with httpx.AsyncClient(timeout=REQUEST_TIMEOUT_SECONDS, follow_redirects=True) as client:
        for artifact in selected_artifacts:
            files.append(await _build_artifact_context(client, artifact))

    return {
        "source": "module2_upload_api",
        "status": "ok",
        "project_id": projeto_id,
        "artifacts_endpoint": artifacts_response.get("artifacts_endpoint"),
        "artifacts_count": artifacts_response.get("artifacts_count", 0),
        "selected_artifacts_count": len(selected_artifacts),
        "selected_artifact_ids": [artifact.get("id") for artifact in selected_artifacts],
        "files": files,
    }


async def salvar_diagrama_modulo_upload(
    projeto_id: str | None,
    token: str | None,
    titulo: str,
    plantuml: str,
    resumo_ia: str,
) -> dict[str, Any]:
    if not projeto_id:
        return {
            "status": "skipped",
            "message": "Projeto nao informado para salvar no Modulo 2.",
        }

    if not token:
        return {
            "status": "skipped",
            "message": "Token JWT nao informado para salvar no Modulo 2.",
        }

    if not plantuml:
        return {
            "status": "skipped",
            "message": "PlantUML vazio, nada para enviar ao Modulo 2.",
        }

    upload_url = f"{MODULE2_UPLOAD_API_URL}/api/upload-diagrama"
    filename = f"{_slugify(titulo or 'diagrama')}.puml"
    headers = {"Authorization": f"Bearer {token}"}
    data = {
        "projeto_id": str(projeto_id),
        "resumo_ia": resumo_ia or "Diagrama PlantUML gerado pelo Modulo 5 com IA.",
    }
    files = {
        "documento": (filename, plantuml.encode("utf-8"), "text/plain"),
    }

    try:
        async with httpx.AsyncClient(timeout=REQUEST_TIMEOUT_SECONDS, follow_redirects=True) as client:
            response = await client.post(upload_url, headers=headers, data=data, files=files)
            response.raise_for_status()

            try:
                response_payload: Any = response.json()
            except ValueError:
                response_payload = response.text
    except Exception as exc:
        return {
            "status": "failed",
            "message": "Diagrama gerado, mas nao foi possivel salvar no Modulo 2.",
            "endpoint": upload_url,
            "error": str(exc),
        }

    return {
        "status": "saved",
        "message": "Diagrama salvo no Modulo 2.",
        "endpoint": upload_url,
        "filename": filename,
        "response": response_payload,
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


def _select_relevant_artifacts(
    artefatos: list[dict[str, Any]],
    artifact_ids: list[int] | None = None,
) -> list[dict[str, Any]]:
    if artifact_ids:
        selected_ids = {str(artifact_id) for artifact_id in artifact_ids}
        selected = [artifact for artifact in artefatos if str(artifact.get("id")) in selected_ids]
        return selected[:MAX_ARTIFACTS]

    relevant = [artifact for artifact in artefatos if _is_text_artifact(artifact)]

    if not relevant:
        relevant = artefatos

    return relevant[:MAX_ARTIFACTS]


def _summarize_artifact(artifact: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": artifact.get("id"),
        "nome_arquivo": artifact.get("nome_arquivo"),
        "tipo": artifact.get("tipo"),
        "url_documento": artifact.get("url_documento"),
    }


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


def _slugify(value: str) -> str:
    slug = re.sub(r"[^a-zA-Z0-9_-]+", "_", value).strip("_").lower()
    return slug[:80] or "diagrama"


def _mock_context(message: str) -> dict[str, Any]:
    return {
        "source": "module2_upload_api",
        "status": "mock",
        "message": message,
        "files": [],
    }

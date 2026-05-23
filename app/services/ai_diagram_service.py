import json
import os
import re
from typing import Any


DEFAULT_OPENAI_MODEL = "gpt-4.1-mini"


def gerar_diagrama_com_ia(
    tipo_diagrama: str,
    titulo: str,
    codigo_fonte: str,
    dados_bancos: dict,
) -> dict:
    api_key = os.getenv("OPENAI_API_KEY")

    if not api_key:
        raise RuntimeError("OPENAI_API_KEY nao configurada no servidor.")

    from openai import OpenAI

    client = OpenAI(api_key=api_key)
    model = os.getenv("OPENAI_MODEL", DEFAULT_OPENAI_MODEL)

    response = client.responses.create(
        model=model,
        input=[
            {
                "role": "system",
                "content": (
                    "Voce e um engenheiro de software especialista em arquitetura, UML, "
                    "documentacao tecnica e engenharia reversa visual."
                ),
            },
            {
                "role": "user",
                "content": _build_prompt(
                    tipo_diagrama=tipo_diagrama,
                    titulo=titulo,
                    codigo_fonte=codigo_fonte,
                    dados_bancos=dados_bancos,
                ),
            },
        ],
        max_output_tokens=3000,
    )

    raw_text = _extract_output_text(response)
    payload = _parse_json_response(raw_text)

    plantuml = _normalize_plantuml(str(payload.get("plantuml") or ""))

    return {
        "title": str(payload.get("title") or titulo),
        "diagram_type": str(payload.get("diagram_type") or tipo_diagrama),
        "plantuml": plantuml,
        "technical_explanation": str(
            payload.get("technical_explanation")
            or "Diagrama gerado automaticamente por IA a partir do contexto informado."
        ),
        "elements_count": _normalize_elements_count(
            payload.get("elements_count"),
            plantuml,
        ),
    }


def _build_prompt(
    tipo_diagrama: str,
    titulo: str,
    codigo_fonte: str,
    dados_bancos: dict,
) -> str:
    bancos_json = json.dumps(dados_bancos, ensure_ascii=False, indent=2, default=str)

    return f"""
Analise o codigo-fonte informado e os artefatos externos do Modulo 2 para gerar um diagrama PlantUML coerente.

Tipo do diagrama: {tipo_diagrama}
Titulo: {titulo}

Codigo-fonte:
{codigo_fonte}

Artefatos externos do Modulo 2:
{bancos_json}

Regras obrigatorias:
- Responder somente JSON valido.
- Nao usar markdown.
- Nao explicar fora do JSON.
- Gerar PlantUML completo.
- O campo plantuml deve comecar com @startuml e terminar com @enduml.
- Nao inventar informacoes absurdas.
- Quando nao souber alguma relacao, usar relacao simples ou comentario.
- Priorizar clareza para documentacao de software.

Formato obrigatorio da resposta:
{{
  "title": "string",
  "diagram_type": "string",
  "plantuml": "string",
  "technical_explanation": "string",
  "elements_count": 1
}}
""".strip()


def _extract_output_text(response: Any) -> str:
    output_text = getattr(response, "output_text", None)
    if output_text:
        return output_text

    chunks: list[str] = []
    for output in getattr(response, "output", []) or []:
        for content in getattr(output, "content", []) or []:
            text = getattr(content, "text", None)
            if text:
                chunks.append(text)

    return "\n".join(chunks)


def _parse_json_response(raw_text: str) -> dict:
    if not raw_text:
        raise ValueError("Resposta vazia da IA.")

    text = raw_text.strip()
    match = re.search(r"\{[\s\S]*\}", text)
    if match:
        text = match.group(0)

    parsed = json.loads(text)

    if not isinstance(parsed, dict):
        raise ValueError("A IA nao retornou um objeto JSON.")

    return parsed


def _normalize_plantuml(plantuml: str) -> str:
    text = plantuml.strip()

    if not text.startswith("@startuml"):
        text = "@startuml\n" + text

    if not text.endswith("@enduml"):
        text = text + "\n@enduml"

    return text


def _count_plantuml_elements(plantuml: str) -> int:
    patterns = [
        r"^\s*class\s+",
        r"^\s*interface\s+",
        r"^\s*entity\s+",
        r"^\s*component\s+",
        r"^\s*database\s+",
        r"^\s*actor\s+",
        r"^\s*usecase\s+",
        r"^\s*\[.+\]",
    ]

    count = 0
    for line in plantuml.splitlines():
        if any(re.search(pattern, line, re.IGNORECASE) for pattern in patterns):
            count += 1

    return count


def _normalize_elements_count(value: Any, plantuml: str) -> int:
    try:
        count = int(value)
    except (TypeError, ValueError):
        count = 0

    return count if count > 0 else _count_plantuml_elements(plantuml)

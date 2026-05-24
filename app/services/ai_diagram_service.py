import json
import os
import re
from typing import Any


DEFAULT_OPENAI_MODEL = "gpt-4.1-mini"
DEFAULT_GROQ_MODEL = "llama-3.1-8b-instant"
DEFAULT_MAX_OUTPUT_TOKENS = 1400
DEFAULT_PROMPT_CONTEXT_MAX_CHARS = 4500
SYSTEM_PROMPT = (
    "Voce e um engenheiro de software especialista em arquitetura, UML, "
    "documentacao tecnica e engenharia reversa visual."
)


def gerar_diagrama_com_ia(
    tipo_diagrama: str,
    titulo: str,
    codigo_fonte: str,
    dados_bancos: dict,
) -> dict:
    prompt = _build_prompt(
        tipo_diagrama=tipo_diagrama,
        titulo=titulo,
        codigo_fonte=codigo_fonte,
        dados_bancos=dados_bancos,
    )

    raw_text = _generate_ai_response(prompt)
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


def _generate_ai_response(prompt: str) -> str:
    provider = os.getenv("AI_PROVIDER", "openai").lower()

    if provider == "groq":
        return _generate_with_groq(prompt)

    return _generate_with_openai(prompt)


def _generate_with_openai(prompt: str) -> str:
    api_key = os.getenv("OPENAI_API_KEY")

    if not api_key:
        raise RuntimeError("OPENAI_API_KEY nao configurada no servidor.")

    from openai import OpenAI

    client = OpenAI(api_key=api_key)
    response = client.responses.create(
        model=os.getenv("OPENAI_MODEL", DEFAULT_OPENAI_MODEL),
        input=[
            {
                "role": "system",
                "content": SYSTEM_PROMPT,
            },
            {
                "role": "user",
                "content": prompt,
            },
        ],
        max_output_tokens=_get_int_env("AI_MAX_OUTPUT_TOKENS", DEFAULT_MAX_OUTPUT_TOKENS),
    )

    return _extract_response_text(response)


def _generate_with_groq(prompt: str) -> str:
    api_key = os.getenv("GROQ_API_KEY")

    if not api_key:
        raise RuntimeError("GROQ_API_KEY nao configurada no servidor.")

    from groq import Groq

    client = Groq(api_key=api_key)
    response = client.chat.completions.create(
        model=os.getenv("GROQ_MODEL") or os.getenv("AI_MODEL", DEFAULT_GROQ_MODEL),
        messages=[
            {
                "role": "system",
                "content": SYSTEM_PROMPT,
            },
            {
                "role": "user",
                "content": prompt,
            },
        ],
        temperature=0.1,
        max_tokens=_get_int_env("AI_MAX_OUTPUT_TOKENS", DEFAULT_MAX_OUTPUT_TOKENS),
        response_format={"type": "json_object"},
    )

    return response.choices[0].message.content or ""


def _diagram_specific_rules(tipo_diagrama: str) -> str:
    tipo = (tipo_diagrama or "").lower()

    if "uml" in tipo or "classe" in tipo or "class" in tipo:
        return """
Tipo: UML de Classes.
Use class/interface/enum/abstract class.
Inclua atributos/metodos claros e relacoes UML.
Nao use participant, start/stop ou sequencia.
Relacoes: Filho --|> Pai, Classe ..|> Interface, A --> B, A ..> B.
""".strip()

    if "arquitetura" in tipo or "architecture" in tipo or "sistema" in tipo:
        return """
Tipo: Arquitetura de Sistema.
Use package/component/database/queue/cloud/node.
Mostre camadas como Frontend, Gateway/API, Controllers, Services, Repositories e Banco.
Mostre dependencias entre componentes, nao ordem temporal.
Nao use participant, start/stop ou sequencia.
""".strip()

    if "cloud" in tipo or "nuvem" in tipo or "aws" in tipo or "azure" in tipo or "gcp" in tipo:
        return """
Tipo: Infraestrutura Cloud.
Use cloud/node/database/storage/component/queue.
Mostre provedor, frontend, backend, banco, storage e servicos externos quando existirem.
Use aliases sem espaco. Nao use participant, start/stop ou sequencia.
""".strip()

    if "er" in tipo or "entidade" in tipo or "relacionamento" in tipo or "dados" in tipo or "database" in tipo:
        return """
Tipo: Diagrama ER.
Use entity e cardinalidade.
Crie entidades a partir de models/tabelas/classes de dominio.
Inclua campos claros e id quando fizer sentido.
Relacoes: Usuario ||--o{ Pedido, Pedido ||--o{ Item.
Nao use participant, start/stop ou sequencia.
""".strip()

    if "perfil" in tipo or "usuario" in tipo or "persona" in tipo or "rbac" in tipo:
        return """
Tipo: Perfis de Usuario.
Use actor/usecase/rectangle.
Perfis viram actors; funcionalidades viram usecases.
Nao use class, participant, start/stop ou sequencia.
Use aliases para nomes com espaco.
""".strip()

    if "fluxo" in tipo or "processo" in tipo or "workflow" in tipo or "bpm" in tipo:
        return """
Tipo: Fluxo de Processo.
Use diagrama de atividades com start, :acao;, if/then/else/endif e stop.
Cada acao termina com ponto e virgula.
Nao use participant, lifelines, class ou sequencia.
""".strip()

    return """
Tipo: Diagrama tecnico generico.
Escolha a sintaxe PlantUML mais adequada, sem misturar tipos.
Priorize clareza e documentacao tecnica.
""".strip()


def _get_int_env(name: str, default: int) -> int:
    try:
        value = int(os.getenv(name, str(default)))
    except ValueError:
        return default

    return value if value > 0 else default


def _truncate_text(value: str, max_chars: int) -> str:
    if len(value) <= max_chars:
        return value

    return value[:max_chars] + "\n... contexto truncado para respeitar limite de tokens ..."


def _build_prompt(
    tipo_diagrama: str,
    titulo: str,
    codigo_fonte: str,
    dados_bancos: dict,
) -> str:
    bancos_json = _truncate_text(
        json.dumps(dados_bancos, ensure_ascii=False, indent=2, default=str),
        _get_int_env("AI_PROMPT_CONTEXT_MAX_CHARS", DEFAULT_PROMPT_CONTEXT_MAX_CHARS),
    )
    regras_tipo = _diagram_specific_rules(tipo_diagrama)

    return f"""
Gere UM UNICO diagrama PlantUML valido para documentacao tecnica.

Tipo do diagrama solicitado: {tipo_diagrama}
Titulo solicitado: {titulo}

Codigo-fonte informado:
{codigo_fonte}

Artefatos externos do Modulo 2:
{bancos_json}

REGRAS ESPECIFICAS DO TIPO DE DIAGRAMA:
{regras_tipo}

REGRAS GERAIS OBRIGATORIAS:
- Responda somente JSON valido, sem markdown e sem texto fora do JSON.
- plantuml deve comecar com @startuml e terminar com @enduml.
- Nao misture tipos de diagrama.
- Priorize codigo e artefatos; se faltar dado, gere versao simples.
- Nomes com espaco/acento/hifen devem usar aspas e alias sem espaco.
- Exemplo de alias: component "API Gateway" as APIGateway; Frontend --> APIGateway.

FORMATO OBRIGATORIO DA RESPOSTA:
{{
  "title": "string",
  "diagram_type": "string",
  "plantuml": "string",
  "technical_explanation": "string",
  "elements_count": 1
}}
""".strip()


def _extract_response_text(response: Any) -> str:
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

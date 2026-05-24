import json
import os
import re
from typing import Any


DEFAULT_OPENAI_MODEL = "gpt-4.1-mini"
DEFAULT_GROQ_MODEL = "llama-3.1-8b-instant"
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
        max_output_tokens=3000,
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
        max_tokens=3000,
        response_format={"type": "json_object"},
    )

    return response.choices[0].message.content or ""


def _diagram_specific_rules(tipo_diagrama: str) -> str:
    tipo = (tipo_diagrama or "").lower()

    if "uml" in tipo or "classe" in tipo or "class" in tipo:
        return """
TIPO ESCOLHIDO: UML DE CLASSES

Gere um diagrama de classes PlantUML.

Use apenas estes elementos quando fizer sentido:
- class
- interface
- enum
- abstract class
- relacionamentos UML

Regras:
- Representar classes reais do dominio do projeto.
- Incluir atributos e metodos quando estiverem claros no codigo.
- Nao transformar bibliotecas externas em classes principais do sistema.
- Nao gerar diagrama de sequencia.
- Nao usar participant.
- Nao usar start/stop.
- Para heranca, usar: Filho --|> Pai
- Para implementacao de interface, usar: Classe ..|> Interface
- Para associacao, usar: ClasseA --> ClasseB
- Para dependencia, usar: ClasseA ..> ClasseB

Exemplo de sintaxe valida:
@startuml
class Usuario {
  - nome
  - email
  + login()
}

class Pedido {
  - status
  + finalizar()
}

Pedido --> Usuario
@enduml
""".strip()

    if "arquitetura" in tipo or "architecture" in tipo or "sistema" in tipo:
        return """
TIPO ESCOLHIDO: ARQUITETURA DE SISTEMA

Gere um diagrama de componentes/camadas do sistema.

Use preferencialmente:
- package
- component
- database
- queue
- cloud
- node
- retangulos/componentes

Regras:
- Mostrar visao geral do sistema.
- Mostrar camadas como Frontend, API/Gateway, Controllers, Services, Repositories e Banco.
- Mostrar integracoes externas se aparecerem no contexto.
- Nao gerar diagrama de sequencia.
- Nao usar participant.
- Nao usar start/stop.
- Nao mostrar ordem temporal de chamadas.
- O objetivo e mostrar componentes e dependencias, nao fluxo passo a passo.

Exemplo de sintaxe valida:
@startuml
title Arquitetura de Sistema

package "Camada de Apresentacao" {
  [Frontend Web] as Frontend
}

package "Backend" {
  [API Gateway] as Gateway
  [Controllers] as Controllers
  [Services] as Services
  [Repositories] as Repositories
}

database "PostgreSQL" as DB

Frontend --> Gateway
Gateway --> Controllers
Controllers --> Services
Services --> Repositories
Repositories --> DB
@enduml
""".strip()

    if "cloud" in tipo or "nuvem" in tipo or "aws" in tipo or "azure" in tipo or "gcp" in tipo:
        return """
TIPO ESCOLHIDO: INFRAESTRUTURA CLOUD

Gere um diagrama de infraestrutura em nuvem.

Use preferencialmente:
- cloud
- node
- database
- storage
- component
- queue

Regras:
- Mostrar provedor de nuvem quando possivel: Azure, AWS ou GCP.
- Se nao houver provedor claro, usar "Cloud Provider".
- Mostrar frontend, backend, banco, storage, monitoramento e servicos externos quando existirem.
- Nao gerar diagrama de sequencia.
- Nao usar participant.
- Nao usar start/stop.
- Usar nomes entre aspas quando tiverem espaco.
- Usar aliases sem espaco.

Exemplo de sintaxe valida:
@startuml
title Infraestrutura Cloud

cloud "Azure" {
  node "App Service Frontend" as Frontend
  node "App Service Gateway API" as Gateway
  node "App Service Backend" as Backend
  database "Azure PostgreSQL" as DB
  storage "Azure Blob Storage" as Blob
}

Frontend --> Gateway
Gateway --> Backend
Backend --> DB
Backend --> Blob
@enduml
""".strip()

    if "er" in tipo or "entidade" in tipo or "relacionamento" in tipo or "dados" in tipo or "database" in tipo:
        return """
TIPO ESCOLHIDO: DIAGRAMA ER

Gere um Diagrama Entidade-Relacionamento em PlantUML.

Use preferencialmente:
- entity
- relacionamentos com cardinalidade

Regras:
- Criar entidades a partir de models, tabelas ou classes de dominio.
- Incluir campos principais quando estiverem claros.
- Inferir chaves primarias como id quando fizer sentido.
- Inferir relacionamentos a partir de atributos como usuario, pedido, produto, itens etc.
- Nao gerar diagrama de sequencia.
- Nao usar participant.
- Nao usar start/stop.
- Usar cardinalidade quando possivel:
  Usuario ||--o{ Pedido
  Pedido ||--o{ PedidoItem
  Produto ||--o{ PedidoItem

Exemplo de sintaxe valida:
@startuml
title Diagrama ER

entity Usuario {
  * id
  --
  nome
  email
}

entity Pedido {
  * id
  --
  status
  valorTotal
}

entity Produto {
  * id
  --
  nome
  preco
}

Usuario ||--o{ Pedido
Pedido ||--o{ Produto
@enduml
""".strip()

    if "perfil" in tipo or "usuario" in tipo or "persona" in tipo or "rbac" in tipo:
        return """
TIPO ESCOLHIDO: PERFIS DE USUARIO

Gere um diagrama de atores e casos de uso.

Use preferencialmente:
- actor
- usecase
- rectangle

Regras:
- Representar perfis de usuario como actors.
- Representar funcionalidades como usecases.
- Nao gerar diagrama de classes.
- Nao gerar diagrama de sequencia.
- Nao usar participant.
- Nao usar start/stop.
- Usar aliases para atores ou casos de uso com espaco.

Exemplo de sintaxe valida:
@startuml
title Perfis de Usuario

actor "Cliente" as Cliente
actor "Administrador" as Admin
actor "Gerente de Vendas" as Gerente

rectangle "Sistema E-commerce" {
  usecase "Realizar Pedido" as UC1
  usecase "Gerenciar Produtos" as UC2
  usecase "Consultar Relatorios" as UC3
}

Cliente --> UC1
Admin --> UC2
Gerente --> UC3
@enduml
""".strip()

    if "fluxo" in tipo or "processo" in tipo or "workflow" in tipo or "bpm" in tipo:
        return """
TIPO ESCOLHIDO: FLUXO DE PROCESSO

Gere um diagrama de atividades/processo.

Use preferencialmente:
- start
- :acao;
- if/else/endif
- stop

Regras:
- Mostrar o fluxo do processo de negocio ou workflow.
- Nao gerar diagrama de sequencia.
- Nao usar participant.
- Nao criar lifelines.
- Nao usar setas entre participantes.
- Cada acao deve terminar com ponto e virgula.
- Usar decisoes com if/then/else/endif quando fizer sentido.
- O objetivo e mostrar etapas do processo, nao arquitetura de componentes.

Exemplo de sintaxe valida:
@startuml
title Fluxo de Processo

start
:Cliente escolhe produtos;
:Sistema cria pedido;
:Processar pagamento;

if (Pagamento aprovado?) then (sim)
  :Atualizar status do pedido;
  :Enviar confirmacao;
else (nao)
  :Informar falha no pagamento;
endif

stop
@enduml
""".strip()

    return """
TIPO ESCOLHIDO: DIAGRAMA TECNICO GENERICO

Gere um PlantUML simples, valido e coerente com o tipo solicitado.

Regras:
- Escolher a sintaxe PlantUML mais adequada ao tipo pedido.
- Nao misturar tipos de diagrama.
- Priorizar clareza e documentacao tecnica.
""".strip()


def _build_prompt(
    tipo_diagrama: str,
    titulo: str,
    codigo_fonte: str,
    dados_bancos: dict,
) -> str:
    bancos_json = json.dumps(dados_bancos, ensure_ascii=False, indent=2, default=str)
    regras_tipo = _diagram_specific_rules(tipo_diagrama)

    return f"""
Voce e um engenheiro de software especialista em engenharia reversa visual, arquitetura de software, UML, PlantUML e documentacao tecnica.

Sua tarefa e gerar UM UNICO diagrama PlantUML valido, de acordo com o tipo solicitado.

Tipo do diagrama solicitado: {tipo_diagrama}
Titulo solicitado: {titulo}

Codigo-fonte informado:
{codigo_fonte}

Artefatos externos do Modulo 2:
{bancos_json}

REGRAS ESPECIFICAS DO TIPO DE DIAGRAMA:
{regras_tipo}

REGRAS GERAIS OBRIGATORIAS:
- Responder somente JSON valido.
- Nao usar markdown.
- Nao explicar fora do JSON.
- O campo plantuml deve conter PlantUML completo.
- O campo plantuml deve comecar exatamente com @startuml.
- O campo plantuml deve terminar exatamente com @enduml.
- Nao inventar informacoes absurdas.
- Priorizar elementos encontrados no codigo-fonte e nos artefatos.
- Se faltar informacao, gerar uma versao simples e coerente em vez de inventar detalhes complexos.
- Nao misturar tipos de diagrama.
- Se o tipo solicitado for arquitetura, nao gerar sequencia.
- Se o tipo solicitado for fluxo, gerar atividade/processo, nao sequencia.
- Se o tipo solicitado for UML de Classes, gerar classes e relacionamentos, nao atores.
- Se o tipo solicitado for ER, gerar entidades e relacionamentos, nao classes UML comuns.
- Se o tipo solicitado for perfis de usuario, gerar atores e casos de uso.
- Qualquer nome com espaco, acento, hifen ou caractere especial deve ser declarado com aspas e alias.
- Use aliases sem espaco nas conexoes.
- Exemplo correto:
  component "Frontend Web" as FrontendWeb
  component "API Gateway" as APIGateway
  database "Banco PostgreSQL" as BancoPostgreSQL
  FrontendWeb --> APIGateway
  APIGateway --> BancoPostgreSQL
- Nunca use nomes com espaco diretamente em setas.
- Evite caracteres especiais desnecessarios dentro dos aliases.
- O JSON final deve ser parseavel com json.loads.

FORMATO OBRIGATORIO DA RESPOSTA:
{{
  "title": "string",
  "diagram_type": "string",
  "plantuml": "string",
  "technical_explanation": "string",
  "elements_count": 1
}}

EXEMPLO DE RESPOSTA VALIDA:
{{
  "title": "Diagrama de Exemplo",
  "diagram_type": "{tipo_diagrama}",
  "plantuml": "@startuml\\ntitle Diagrama de Exemplo\\n[Frontend] --> [Gateway]\\n@enduml",
  "technical_explanation": "Diagrama gerado a partir do contexto informado.",
  "elements_count": 2
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

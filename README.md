# DoculA Gateway API

## Descrição

O DoculA Gateway API é o ponto central de orquestração do Módulo 5 - Diagramas e Documentos Técnicos da plataforma DoculA.

Ele recebe requisições do frontend e coordena a integração entre autenticação, análise de código, geração de diagramas, documentação técnica, histórico PostgreSQL e comunicação com outros módulos da plataforma.

Responsabilidades principais:

- Receber requisições do frontend.
- Validar autenticação JWT.
- Integrar com a Parser API.
- Integrar com a Diagram API.
- Integrar IA para geração de diagramas.
- Consultar artefatos do Módulo 2.
- Salvar diagramas gerados no Módulo 2.
- Manter histórico de diagramas quando `DATABASE_URL` estiver configurado.

## Arquitetura

Fluxo principal de integração:

```txt
Módulo 1
   ↓ JWT, project_id, company_id
Frontend
   ↓
Gateway API
   ↓
Parser API
   ↓
Diagram API
   ↓
Módulo 2 Upload/Ingestão
```

Fluxo de geração com IA:

```txt
Frontend
   ↓
Gateway API
   ↓
Módulo 2 Artefatos
   ↓
IA
   ↓
PlantUML
   ↓
Módulo 2 Upload
```

## Deploy Em Produção

Gateway API:

```txt
https://docula-gateway-api-dzgfg8ghghadeedd.eastus-01.azurewebsites.net/
```

Swagger/OpenAPI:

```txt
https://docula-gateway-api-dzgfg8ghghadeedd.eastus-01.azurewebsites.net/docs
```

Parser API:

```txt
https://diagramas-parser-e6dzc7f5ateae3ce.canadacentral-01.azurewebsites.net
```

Diagram API:

```txt
https://diagramas-diagram-eugce0h0bygfdqhf.canadacentral-01.azurewebsites.net
```

Módulo 2 Upload API:

```txt
https://docuia-api-upload.azurewebsites.net
```

## Requisitos

- Python 3.10+
- FastAPI
- Uvicorn
- HTTPX
- Pydantic
- SQLAlchemy
- PostgreSQL opcional
- PyJWT
- OpenAI ou Groq para IA

## Instalação Local

```powershell
pip install -r requirements.txt
```

## Como Executar Localmente

Gateway API:

```powershell
python -m uvicorn app.main:app --reload --port 8000
```

Parser API recomendada:

```powershell
python -m uvicorn app.main:app --reload --port 8001
```

Diagram API recomendada:

```powershell
python -m uvicorn app.main:app --reload --port 8002
```

Swagger/OpenAPI local:

```txt
http://127.0.0.1:8000/docs
```

## Variáveis De Ambiente

```txt
PARSER_API_URL=https://diagramas-parser-e6dzc7f5ateae3ce.canadacentral-01.azurewebsites.net
DIAGRAM_API_URL=https://diagramas-diagram-eugce0h0bygfdqhf.canadacentral-01.azurewebsites.net
DATABASE_URL=postgresql://usuario:senha@host:5432/banco
JWT_SECRET_KEY=sua_chave_do_modulo_1
JWT_ALGORITHM=HS256
AUTH_REQUIRED=false
MODULE2_UPLOAD_API_URL=https://docuia-api-upload.azurewebsites.net
MODULE2_MAX_ARTIFACTS=12
MODULE2_MAX_ARTIFACT_CHARS=6000
MODULE2_API_TIMEOUT_SECONDS=15
AI_PROVIDER=groq
OPENAI_API_KEY=sua_chave_openai
OPENAI_MODEL=gpt-4.1-mini
GROQ_API_KEY=sua_chave_groq
GROQ_MODEL=llama-3.1-8b-instant
```

Observações:

- `JWT_SECRET_KEY` não deve ir para o GitHub.
- `OPENAI_API_KEY` e `GROQ_API_KEY` não devem ir para o frontend nem para o GitHub.
- `AUTH_REQUIRED=false` permite modo desenvolvimento para os endpoints protegidos do Gateway.
- `AUTH_REQUIRED=true` exige token JWT nos endpoints protegidos.
- `DATABASE_URL` é opcional. Quando configurada, habilita persistência de histórico PostgreSQL.
- `MODULE2_UPLOAD_API_URL` aponta para o serviço de Upload/Ingestão do Módulo 2.

## Endpoints Principais

Endpoints públicos:

```http
GET /
GET /health
```

Autenticação:

```http
GET /auth/me
```

Diagramas:

```http
POST /diagram/class
POST /diagram/architecture
POST /diagram/cloud
POST /diagram/profiles
POST /diagram/flow
```

Documentação e análise:

```http
POST /api-docs/generate
POST /ai/analyze
```

Histórico:

```http
GET /diagram/history
GET /projects/{project_id}/diagrams
```

Integração com Módulo 2 e IA:

```http
GET /api/modulo5/diagramas/projetos/{projeto_id}/artefatos
POST /api/modulo5/diagramas/gerar-ia
```

## Exemplos De Uso

### GET /auth/me

```http
GET /auth/me
Authorization: Bearer TOKEN
```

Exemplo de resposta:

```json
{
  "valido": true,
  "user_id": "123",
  "email": "usuario@docula.com",
  "nome": "Usuário DoculA"
}
```

### POST /diagram/class

```json
{
  "title": "Diagrama Pedido",
  "diagram_type": "uml-class",
  "project_id": "10",
  "company_id": "6",
  "project_name": "Projeto DoculA",
  "source_code": "public class Usuario { private String nome; public void login() { } } public class Pedido extends Entidade { private Usuario usuario; public void finalizar() { } }"
}
```

Exemplo de resposta:

```json
{
  "title": "Diagrama Pedido",
  "diagram_type": "uml-class",
  "project_id": "10",
  "company_id": "6",
  "project_name": "Projeto DoculA",
  "classes": [
    {
      "name": "Usuario",
      "attributes": ["nome"],
      "methods": ["login"]
    },
    {
      "name": "Pedido",
      "attributes": ["usuario"],
      "methods": ["finalizar"]
    }
  ],
  "plantuml": "@startuml\nclass Entidade\nclass Usuario {\n  nome\n  login()\n}\nclass Pedido {\n  usuario\n  finalizar()\n}\nPedido --|> Entidade\nPedido --> Usuario\n@enduml"
}
```

### POST /api-docs/generate

```json
{
  "title": "Documentação API Usuários",
  "project_id": "10",
  "company_id": "6",
  "project_name": "Projeto DoculA",
  "source_code": "from fastapi import FastAPI\napp = FastAPI()\n@app.get('/users')\ndef list_users(): pass\n@app.post('/users')\ndef create_user(): pass"
}
```

Exemplo de resposta:

```json
{
  "title": "Documentação API Usuários",
  "project_id": "10",
  "company_id": "6",
  "project_name": "Projeto DoculA",
  "endpoints": [
    {
      "method": "GET",
      "path": "/users",
      "framework": "FastAPI",
      "description": "Endpoint GET detectado automaticamente em /users"
    },
    {
      "method": "POST",
      "path": "/users",
      "framework": "FastAPI",
      "description": "Endpoint POST detectado automaticamente em /users"
    }
  ]
}
```

### GET /api/modulo5/diagramas/projetos/{projeto_id}/artefatos

```http
GET /api/modulo5/diagramas/projetos/10/artefatos
Authorization: Bearer TOKEN
```

Esse endpoint consulta o Módulo 2 em:

```txt
GET /api/projeto/{projeto_id}/artefatos
```

Exemplo de resposta:

```json
{
  "source": "module2_upload_api",
  "status": "ok",
  "project_id": "10",
  "artifacts_count": 2,
  "artifacts": [
    {
      "id": 1,
      "nome_arquivo": "Usuario.java",
      "tipo": "codigo-fonte",
      "url_documento": "https://exemplo/Usuario.java"
    }
  ]
}
```

### POST /api/modulo5/diagramas/gerar-ia

```json
{
  "tipo_diagrama": "UML de Classes",
  "titulo": "Diagrama com artefatos",
  "codigo_fonte": "",
  "projeto_id": "10",
  "artifact_ids": [1, 2],
  "save_to_upload_module": true
}
```

Exemplo de resposta:

```json
{
  "title": "Diagrama com artefatos",
  "diagram_type": "UML de Classes",
  "plantuml": "@startuml\nclass Usuario\nclass Pedido\nPedido --> Usuario\n@enduml",
  "technical_explanation": "Diagrama gerado por IA a partir do código e dos artefatos do Módulo 2.",
  "elements_count": 2,
  "upload_status": "saved",
  "upload_message": "Diagrama salvo no Modulo 2."
}
```

Quando `save_to_upload_module=true`, o Gateway envia o PlantUML gerado para o Módulo 2 pelo endpoint:

```txt
POST /api/upload-diagrama
```

O arquivo salvo atualmente é um `.puml` com MIME `text/plain`.

## Integração Com Módulo 1

O Módulo 1 autentica o usuário e redireciona para o Frontend do Módulo 5 com os dados do projeto e o token JWT.

Fluxo:

- O Módulo 1 envia `id`, `companyId` e `token` para o Frontend.
- O Frontend salva o token e envia `Authorization: Bearer TOKEN` para o Gateway.
- O Gateway valida o token com `JWT_SECRET_KEY`.
- `project_id` vem do parâmetro `id`.
- `company_id` vem do parâmetro `companyId`.

URL de integração:

```txt
https://docula-modulo5-front-gabriel-gcgmcjbeg2dze3bs.canadacentral-01.azurewebsites.net/projetos?id={PROJECT_ID}&token={JWT_TOKEN}&companyId={COMPANY_ID}
```

## Integração Com Módulo 2

O Gateway integra com o serviço de Upload/Ingestão do Módulo 2.

Fluxo:

- O Gateway consulta os artefatos pelo endpoint do Módulo 2:

```txt
GET /api/projeto/{projeto_id}/artefatos
```

- O Gateway baixa os arquivos textuais pela `url_documento`.
- O Gateway envia os artefatos para a IA como contexto.
- O Gateway pode salvar o diagrama gerado no Módulo 2:

```txt
POST /api/upload-diagrama
```

- O arquivo salvo atualmente é um `.puml` com MIME `text/plain`.

## IA

O Gateway possui geração de diagramas com IA a partir de código-fonte e artefatos externos do Módulo 2.

O provider pode ser:

- OpenAI
- Groq

A IA retorna JSON com:

```txt
title
diagram_type
plantuml
technical_explanation
elements_count
```

O PlantUML deve começar com:

```txt
@startuml
```

E terminar com:

```txt
@enduml
```

## Histórico

Se `DATABASE_URL` estiver configurada, o Gateway salva o histórico dos diagramas gerados.

Endpoints:

```http
GET /diagram/history
GET /projects/{project_id}/diagrams
```

`GET /diagram/history` lista o histórico geral.

`GET /projects/{project_id}/diagrams` lista o histórico por projeto.

## Tecnologias Utilizadas

- Python
- FastAPI
- Uvicorn
- HTTPX
- Pydantic
- SQLAlchemy
- PostgreSQL
- PyJWT
- OpenAI SDK
- Groq SDK
- Azure App Service
- PlantUML

## Deploy

O serviço está preparado para deploy em Azure App Service.

Startup command:

```bash
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000
```

## Versionamento

Versão final:

```txt
v1.0.0
```

Histórico:

```txt
v0.1.0 - Integração inicial Parser API e Diagram API
v0.2.0 - Histórico PostgreSQL
v0.3.0 - Documentação de API e vínculo com projetos
v0.4.0 - Análise inteligente de código
v0.5.0 - Integração dos tipos architecture, cloud, profiles e flow
v0.6.0 - Validação JWT para integração com Módulo 1
v0.6.1 - Suporte a company_id no contrato com Módulo 1
v0.7.0 - Integração com artefatos do Módulo 2
v1.0.0 - Versão final do Gateway API para entrega do Módulo 5
```

## Status Atual

```txt
Gateway online
JWT funcionando
Parser integrado
Diagram integrado
IA integrada
Módulo 1 integrado
Módulo 2 integrado
Histórico PostgreSQL configurável
Deploy em Azure funcionando
```

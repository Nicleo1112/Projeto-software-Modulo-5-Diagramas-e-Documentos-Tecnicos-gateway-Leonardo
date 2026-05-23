# DoculA Gateway API

Microsserviço orquestrador do **Módulo 5 — Diagramas e Documentos Técnicos** da plataforma DoculA.

O Gateway API é responsável por integrar a **Parser API** e a **Diagram API**, coordenando o fluxo completo de geração de diagramas UML a partir de código-fonte enviado pelo frontend.

## Arquitetura

```txt
Frontend
   ↓
Gateway API
   ↓
Parser API
   ↓
Diagram API
````

## Responsabilidades do Gateway

* Receber requisições do frontend;
* Encaminhar código-fonte para a Parser API;
* Receber classes, atributos e métodos extraídos;
* Enviar os dados estruturados para a Diagram API;
* Retornar o PlantUML gerado ao frontend;
* Centralizar a integração entre os microsserviços do módulo;
* Disponibilizar um ponto único de comunicação para outros módulos da plataforma.

## Deploy em Produção

### Gateway API

```txt
https://docula-gateway-api-dzgfg8ghghadeedd.eastus-01.azurewebsites.net/
```

### Swagger/OpenAPI do Gateway

```txt
https://docula-gateway-api-dzgfg8ghghadeedd.eastus-01.azurewebsites.net/docs
```

### Parser API

```txt
https://diagramas-parser-e6dzc7f5ateae3ce.canadacentral-01.azurewebsites.net
```

### Diagram API

```txt
https://diagramas-diagram-eugce0h0bygfdqhf.canadacentral-01.azurewebsites.net
```

## Requisitos

* Python 3.10+
* Parser API disponível
* Diagram API disponível
* Opcional: PostgreSQL configurado em `DATABASE_URL`

## Instalação

```powershell
pip install -r requirements.txt
```

## Como executar localmente

Execute os microsserviços em terminais separados.

### Parser API

```powershell
python -m uvicorn app.main:app --reload --port 8001
```

### Diagram API

```powershell
python -m uvicorn app.main:app --reload --port 8002
```

### Gateway API

```powershell
python -m uvicorn app.main:app --reload --port 8000
```

Swagger/OpenAPI local:

```txt
http://127.0.0.1:8000/docs
```

## Variáveis de ambiente

Em ambiente local ou produção, configure:

```txt
PARSER_API_URL=https://diagramas-parser-e6dzc7f5ateae3ce.canadacentral-01.azurewebsites.net

DIAGRAM_API_URL=https://diagramas-diagram-eugce0h0bygfdqhf.canadacentral-01.azurewebsites.net

DATABASE_URL=postgresql://usuario:senha@servidor.postgres.database.azure.com:5432/nome_do_banco

MODULE2_DATABASE_URL_1=postgresql://usuario:senha@host:5432/banco_1

MODULE2_DATABASE_URL_2=postgresql://usuario:senha@host:5432/banco_2

MODULE2_DB_SAMPLE_ROWS=3

MODULE2_DB_MAX_TABLES=20

OPENAI_API_KEY=sua_chave_openai

OPENAI_MODEL=gpt-4.1-mini
```

Observação: `DATABASE_URL` é opcional na versão atual. Caso configurada, pode ser usada para persistir o histórico de diagramas gerados.

`MODULE2_DATABASE_URL_1` e `MODULE2_DATABASE_URL_2` são opcionais. Quando configuradas, o Gateway coleta tabelas, colunas e pequenas amostras mascaradas dos bancos do Módulo 2 e envia esse contexto para o Diagram API gerar diagramas com IA.

`OPENAI_API_KEY` deve ser configurada somente no backend. Nunca exponha essa chave no frontend ou no repositório.

## Endpoints

### Health check

```http
GET /health
```

### Gerar diagrama com IA

```http
POST /api/modulo5/diagramas/gerar-ia
Authorization: Bearer TOKEN
```

Exemplo de entrada:

```json
{
  "tipo_diagrama": "UML de Classes",
  "titulo": "Diagrama de usuarios",
  "codigo_fonte": "public class Usuario { private String nome; private String email; }",
  "projeto_id": "7"
}
```

Exemplo de resposta:

```json
{
  "title": "Diagrama de Classes - Usuarios",
  "diagram_type": "UML de Classes",
  "plantuml": "@startuml\nclass Usuario {\n  +String nome\n  +String email\n}\n@enduml",
  "technical_explanation": "O diagrama representa a classe Usuario com seus principais atributos.",
  "elements_count": 1
}
```

Exemplo de resposta:

```json
{
  "status": "ok",
  "service": "docula-gateway-api"
}
```

### Gerar diagrama UML de classes

```http
POST /diagram/class
```

Exemplo de entrada:

```json
{
  "title": "Diagrama Usuario",
  "source_code": "public class Usuario { private String nome; private String email; public void login() { } public void logout() { } }"
}
```

Exemplo de resposta:

```json
{
  "title": "Diagrama Usuario",
  "classes": [
    {
      "name": "Usuario",
      "attributes": ["nome", "email"],
      "methods": ["login", "logout"]
    }
  ],
  "plantuml": "@startuml\nclass Usuario {\n  nome\n  email\n  login()\n  logout()\n}\n@enduml"
}
```

### Histórico de diagramas

Caso o banco de dados esteja configurado, o Gateway pode salvar e consultar o histórico de diagramas gerados.

```http
GET /diagram/history
```

## Fluxo de funcionamento

```txt
1. O usuário envia código-fonte pelo frontend.
2. O frontend chama o Gateway API.
3. O Gateway envia o código para a Parser API.
4. A Parser API extrai classes, atributos e métodos.
5. O Gateway envia os dados estruturados para a Diagram API.
6. A Diagram API gera o PlantUML.
7. O Gateway retorna o resultado para o frontend.
```

## Papel na integração com outros módulos

O Gateway API atua como ponto central de integração do Módulo 5.

Outros módulos da plataforma podem consumir este serviço para gerar e recuperar diagramas automaticamente, incluindo:

* Módulo de Relatórios;
* Módulo de Apresentações;
* Módulo de Consulta;
* Plataforma HUB;
* Módulo de Ingestão de Dados.

Exemplo de uso por outros módulos:

```txt
Relatórios → Gateway API → Diagrama UML → PDF/DOCX
Apresentações → Gateway API → Diagrama UML → Slides
Consulta → Gateway API → Estrutura do código → Respostas sobre arquitetura
HUB → Gateway API → Diagramas do projeto
```

## Tecnologias utilizadas

* Python
* FastAPI
* Uvicorn
* HTTPX
* Pydantic
* PostgreSQL
* SQLAlchemy
* Azure App Service

## Deploy

O serviço está preparado para deploy em **Azure App Service**.

Startup command utilizado:

```bash
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000
```

## Versionamento

O projeto utiliza versionamento semântico.

Versão atual:

```txt
v0.1.1
```

Histórico inicial:

```txt
v0.1.0 - Integração inicial entre Parser API e Diagram API
v0.1.1 - Preparação para deploy Azure
```

## Observação

Este microsserviço não é responsável por fazer o parsing do código nem gerar diretamente o PlantUML.

Essas responsabilidades são separadas em outros microsserviços:

```txt
Parser API → análise do código-fonte
Diagram API → geração do PlantUML
Gateway API → orquestração do fluxo
```

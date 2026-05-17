# DoculA Gateway API

Microsservico orquestrador do Modulo 5. Integra a Parser API e a Diagram API para gerar diagramas de classes a partir de codigo-fonte.

## Requisitos

- Python 3.10+
- Parser API rodando na porta `8001`
- Diagram API rodando na porta `8002`

## Instalacao

```powershell
pip install -r requirements.txt
```

## Como rodar

Em tres terminais diferentes, rode os microsservicos:

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

Depois abra:

```txt
http://127.0.0.1:8000/docs
```

## Teste

Use o endpoint `POST /diagram/class` com este corpo:

```json
{
  "title": "Diagrama Usuario",
  "source_code": "public class Usuario { private String nome; private String email; public void login() { } public void logout() { } }"
}
```

A resposta esperada contem as classes extraidas e o PlantUML gerado.

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.schemas import DiagramRequest, DiagramResponse
from app.services.diagram_flow import generate_class_diagram

app = FastAPI(
    title="DoculA Gateway API",
    description="Microsserviço orquestrador do Módulo 5. Integra Parser API e Diagram API.",
    version="0.1.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health():
    return {
        "status": "ok",
        "service": "docula-gateway-api"
    }


@app.post("/diagram/class", response_model=DiagramResponse)
async def create_class_diagram(request: DiagramRequest):
    result = await generate_class_diagram(request.source_code)

    return {
        "title": request.title,
        "classes": result["classes"],
        "plantuml": result["plantuml"]
    }

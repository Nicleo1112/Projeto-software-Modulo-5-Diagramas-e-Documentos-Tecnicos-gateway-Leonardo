from typing import Any

from app.services.module2_database_context import collect_module2_database_context


async def buscar_dados_bancos(projeto_id: str | None) -> dict[str, Any]:
    context = await collect_module2_database_context(project_id=projeto_id)

    if not context:
        return {
            "source": "module2_ingestion_databases",
            "status": "mock",
            "message": "Bancos externos ainda nao configurados no Gateway.",
            "databases": [],
        }

    return context

import os

import httpx

from app.services.module2_database_context import collect_module2_database_context


DIAGRAM_API_URL = os.getenv(
    "DIAGRAM_API_URL",
    "https://diagramas-diagram-eugce0h0bygfdqhf.canadacentral-01.azurewebsites.net",
)


async def generate_generic_diagram(diagram_type: str, payload: dict):
    payload = dict(payload)
    module2_context = await collect_module2_database_context(
        project_id=payload.get("project_id"),
        company_id=payload.get("company_id"),
    )

    if module2_context:
        payload["external_context"] = module2_context

    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.post(
            f"{DIAGRAM_API_URL}/generate/{diagram_type}",
            json=payload,
        )

        response.raise_for_status()

        return response.json()

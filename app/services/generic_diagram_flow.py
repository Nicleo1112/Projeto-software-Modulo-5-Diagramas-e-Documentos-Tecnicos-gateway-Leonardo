import os

import httpx


DIAGRAM_API_URL = os.getenv(
    "DIAGRAM_API_URL",
    "https://diagramas-diagram-eugce0h0bygfdqhf.canadacentral-01.azurewebsites.net",
)


async def generate_generic_diagram(diagram_type: str, payload: dict):
    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.post(
            f"{DIAGRAM_API_URL}/generate/{diagram_type}",
            json=payload,
        )

        response.raise_for_status()

        return response.json()

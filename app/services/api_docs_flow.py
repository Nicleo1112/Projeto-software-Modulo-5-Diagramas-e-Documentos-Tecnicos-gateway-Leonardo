import os

import httpx


PARSER_API_URL = os.getenv(
    "PARSER_API_URL",
    "https://diagramas-parser-e6dzc7f5ateae3ce.canadacentral-01.azurewebsites.net",
)


async def generate_api_documentation(source_code: str):
    async with httpx.AsyncClient(timeout=30.0) as client:
        parser_response = await client.post(
            f"{PARSER_API_URL}/parse/api",
            json={"source_code": source_code},
        )

        parser_response.raise_for_status()

        return parser_response.json()

import os
import httpx


PARSER_API_URL = os.getenv("PARSER_API_URL", "http://127.0.0.1:8001")
DIAGRAM_API_URL = os.getenv("DIAGRAM_API_URL", "http://127.0.0.1:8002")


async def generate_class_diagram(source_code: str):
    async with httpx.AsyncClient() as client:
        parser_response = await client.post(
            f"{PARSER_API_URL}/parse/class",
            json={"source_code": source_code}
        )
        parser_response.raise_for_status()
        parsed_data = parser_response.json()

        diagram_response = await client.post(
            f"{DIAGRAM_API_URL}/generate/uml",
            json=parsed_data
        )
        diagram_response.raise_for_status()
        diagram_data = diagram_response.json()

        return {
            "classes": parsed_data["classes"],
            "plantuml": diagram_data["plantuml"]
        }

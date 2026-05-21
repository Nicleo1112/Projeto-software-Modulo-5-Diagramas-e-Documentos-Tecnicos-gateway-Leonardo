import re


def _collect_source_code(source_code: str | None, files: list | None) -> str:
    parts = []

    if source_code:
        parts.append(source_code)

    if files:
        for file in files:
            content = getattr(file, "content", None)
            if content:
                parts.append(content)

    return "\n\n".join(parts)


def analyze_code(
    source_code: str | None = None,
    files: list | None = None,
) -> dict:
    code = _collect_source_code(source_code, files)

    class_names = re.findall(r"\bclass\s+(\w+)", code)
    fastapi_routes = re.findall(
        r"@\w+\.(get|post|put|delete|patch)\(['\"]([^'\"]+)['\"]\)",
        code,
        re.IGNORECASE,
    )
    spring_routes = re.findall(
        r"@(GetMapping|PostMapping|PutMapping|DeleteMapping|PatchMapping)\(['\"]([^'\"]+)['\"]\)",
        code,
    )

    detected_profiles = ["Desenvolvedor"]

    if class_names or fastapi_routes or spring_routes:
        detected_profiles.append("Tech Lead")

    if fastapi_routes or spring_routes:
        detected_profiles.append("PM")

    architecture_notes = []

    if class_names:
        architecture_notes.append(
            "Foram detectadas classes no código-fonte, indicando estrutura orientada a objetos."
        )

    if fastapi_routes or spring_routes:
        architecture_notes.append(
            "Foram detectados endpoints REST, indicando uma camada de API."
        )

    if "Repository" in code or "repository" in code:
        architecture_notes.append("Possível padrão Repository detectado.")

    if "Service" in code or "service" in code:
        architecture_notes.append("Possível camada de serviço detectada.")

    if "Controller" in code or "controller" in code:
        architecture_notes.append("Possível camada Controller detectada.")

    possible_relationships = []

    for class_name in class_names:
        pattern = rf"private\s+{class_name}\s+\w+;"
        if re.search(pattern, code):
            possible_relationships.append(
                f"Relacionamento com {class_name} detectado por atributo."
            )

    if class_names and (fastapi_routes or spring_routes):
        suggested_diagram_type = "architecture"
    elif class_names:
        suggested_diagram_type = "uml-class"
    elif fastapi_routes or spring_routes:
        suggested_diagram_type = "api-docs"
    else:
        suggested_diagram_type = "uml-class"

    if not code.strip():
        summary = "Nenhum código-fonte foi informado para análise."
    elif class_names:
        summary = (
            f"O código contém {len(class_names)} classe(s): "
            f"{', '.join(class_names)}. "
            "A estrutura pode ser usada para gerar diagramas UML e apoiar a documentação técnica."
        )
    elif fastapi_routes or spring_routes:
        total_routes = len(fastapi_routes) + len(spring_routes)
        summary = (
            f"O código contém {total_routes} endpoint(s) REST detectado(s), "
            "podendo ser usado para gerar documentação de API."
        )
    else:
        summary = (
            "O código foi analisado, mas não foram detectadas classes ou endpoints REST claros. "
            "Ainda assim, pode ser usado como base para documentação manual."
        )

    return {
        "summary": summary,
        "suggested_diagram_type": suggested_diagram_type,
        "detected_profiles": list(dict.fromkeys(detected_profiles)),
        "architecture_notes": architecture_notes,
        "possible_entities": class_names,
        "possible_relationships": possible_relationships,
    }

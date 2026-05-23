import logging
import os
from typing import Any

import asyncpg


logger = logging.getLogger(__name__)

MAX_TABLES_PER_DATABASE = int(os.getenv("MODULE2_DB_MAX_TABLES", "20"))
MAX_SAMPLE_ROWS = int(os.getenv("MODULE2_DB_SAMPLE_ROWS", "3"))
QUERY_TIMEOUT_SECONDS = float(os.getenv("MODULE2_DB_TIMEOUT_SECONDS", "6"))


def get_module2_database_urls() -> list[tuple[str, str]]:
    candidates = [
        ("module2_database_1", os.getenv("MODULE2_DATABASE_URL_1") or os.getenv("SANCHES_DATABASE_URL_1")),
        ("module2_database_2", os.getenv("MODULE2_DATABASE_URL_2") or os.getenv("SANCHES_DATABASE_URL_2")),
    ]

    return [(name, _normalize_database_url(url)) for name, url in candidates if url]


async def collect_module2_database_context(
    project_id: str | None = None,
    company_id: str | None = None,
) -> dict[str, Any] | None:
    database_urls = get_module2_database_urls()

    if not database_urls:
        return None

    databases = []

    for name, url in database_urls:
        try:
            databases.append(
                await _collect_single_database_context(
                    name=name,
                    url=url,
                    project_id=project_id,
                    company_id=company_id,
                )
            )
        except Exception as exc:
            logger.warning("Falha ao coletar contexto do banco %s: %s", name, exc)
            databases.append(
                {
                    "name": name,
                    "status": "unavailable",
                    "error": str(exc),
                }
            )

    return {
        "source": "module2_ingestion_databases",
        "project_id": project_id,
        "company_id": company_id,
        "databases": databases,
    }


async def _collect_single_database_context(
    name: str,
    url: str,
    project_id: str | None,
    company_id: str | None,
) -> dict[str, Any]:
    connection = await asyncpg.connect(url, timeout=QUERY_TIMEOUT_SECONDS)

    try:
        tables = await connection.fetch(
            """
            select table_schema, table_name
            from information_schema.tables
            where table_type = 'BASE TABLE'
              and table_schema not in ('pg_catalog', 'information_schema')
            order by table_schema, table_name
            limit $1
            """,
            MAX_TABLES_PER_DATABASE,
            timeout=QUERY_TIMEOUT_SECONDS,
        )

        table_context = []

        for table in tables:
            schema_name = table["table_schema"]
            table_name = table["table_name"]
            columns = await _fetch_columns(connection, schema_name, table_name)

            table_context.append(
                {
                    "schema": schema_name,
                    "table": table_name,
                    "columns": columns,
                    "sample_rows": await _fetch_sample_rows(
                        connection=connection,
                        schema_name=schema_name,
                        table_name=table_name,
                        columns=columns,
                        project_id=project_id,
                        company_id=company_id,
                    ),
                }
            )

        return {
            "name": name,
            "status": "ok",
            "tables": table_context,
        }
    finally:
        await connection.close()


async def _fetch_columns(
    connection: asyncpg.Connection,
    schema_name: str,
    table_name: str,
) -> list[dict[str, Any]]:
    rows = await connection.fetch(
        """
        select column_name, data_type
        from information_schema.columns
        where table_schema = $1
          and table_name = $2
        order by ordinal_position
        """,
        schema_name,
        table_name,
        timeout=QUERY_TIMEOUT_SECONDS,
    )

    return [
        {
            "name": row["column_name"],
            "type": row["data_type"],
        }
        for row in rows
    ]


async def _fetch_sample_rows(
    connection: asyncpg.Connection,
    schema_name: str,
    table_name: str,
    columns: list[dict[str, Any]],
    project_id: str | None,
    company_id: str | None,
) -> list[dict[str, Any]]:
    if MAX_SAMPLE_ROWS <= 0:
        return []

    column_names = {column["name"] for column in columns}
    filters = []
    values = []

    if project_id and "project_id" in column_names:
        values.append(project_id)
        filters.append(f"project_id::text = ${len(values)}")

    if company_id and "company_id" in column_names:
        values.append(company_id)
        filters.append(f"company_id::text = ${len(values)}")

    where_clause = f" where {' and '.join(filters)}" if filters else ""
    query = (
        f"select * from {_quote_identifier(schema_name)}.{_quote_identifier(table_name)}"
        f"{where_clause}"
        f" limit {MAX_SAMPLE_ROWS}"
    )

    rows = await connection.fetch(query, *values, timeout=QUERY_TIMEOUT_SECONDS)
    return [_sanitize_row(dict(row)) for row in rows]


def _sanitize_row(row: dict[str, Any]) -> dict[str, Any]:
    sanitized = {}

    for key, value in row.items():
        lowered = key.lower()

        if any(secret in lowered for secret in ["password", "senha", "token", "secret", "key"]):
            sanitized[key] = "***"
        elif isinstance(value, str) and len(value) > 180:
            sanitized[key] = value[:180] + "..."
        else:
            sanitized[key] = value

    return sanitized


def _quote_identifier(identifier: str) -> str:
    return '"' + identifier.replace('"', '""') + '"'


def _normalize_database_url(url: str) -> str:
    if url.startswith("postgresql+asyncpg://"):
        return url.replace("postgresql+asyncpg://", "postgresql://", 1)

    return url

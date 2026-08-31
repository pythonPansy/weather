"""Normalise Postgres URLs for SQLAlchemy asyncpg (including Neon)."""

from __future__ import annotations

from urllib.parse import parse_qs, urlencode, urlparse, urlunparse


def normalise_database_url(url: str) -> str:
    """Convert vendor URLs to asyncpg and drop unsupported query params."""
    if url.startswith("postgresql://"):
        url = url.replace("postgresql://", "postgresql+asyncpg://", 1)
    parsed = urlparse(url)
    query = parse_qs(parsed.query, keep_blank_values=True)
    for key in ("channel_binding", "sslmode"):
        query.pop(key, None)
    clean_query = urlencode({key: values[0] for key, values in query.items()})
    return urlunparse(parsed._replace(query=clean_query))


def asyncpg_connect_args(url: str) -> dict[str, object]:
    """SSL settings required for Neon and other hosted Postgres."""
    if "neon.tech" in url:
        return {"ssl": "require"}
    return {}

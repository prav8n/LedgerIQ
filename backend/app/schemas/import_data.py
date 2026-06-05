"""Pydantic v2 schemas for CSV/XLSX import."""

from __future__ import annotations

from pydantic import BaseModel


class ImportPreview(BaseModel):
    headers: list[str]
    suggested_mapping: dict[str, str | None]
    sample_rows: list[dict[str, str]]
    total_rows: int


class ImportRowError(BaseModel):
    row: int
    error: str


class ImportResult(BaseModel):
    created: int
    skipped: int
    errors: list[ImportRowError]

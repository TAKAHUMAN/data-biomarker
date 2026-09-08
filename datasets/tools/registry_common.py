"""Small deterministic utilities shared by registry importers and readers."""

from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
DATASETS = ROOT / "datasets"
SCHEMA_PATH = DATASETS / "schema" / "dataset_schema_v1.json"


def schema() -> dict[str, list[str]]:
    return json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))["tables"]


def stable_id(prefix: str, *parts: object) -> str:
    """Create a semantic, content-stable identifier without using row position."""
    text = "|".join("" if part is None else str(part).strip() for part in parts)
    readable = re.sub(r"[^a-z0-9]+", "_", text.lower()).strip("_")[:72].strip("_") or "record"
    digest = hashlib.sha256(text.encode("utf-8")).hexdigest()[:12]
    return f"{prefix}_{readable}_{digest}"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def relative(path: Path) -> str:
    return path.resolve().relative_to(ROOT.resolve()).as_posix()


def clean_number(value: object) -> float | None:
    if value is None or value == "":
        return None
    if isinstance(value, (int, float)):
        return float(value)
    text = str(value).strip()
    if text.startswith("~"):
        text = text[1:]
    try:
        return float(text)
    except ValueError:
        return None


class Registry:
    def __init__(self) -> None:
        self.tables: dict[str, list[dict[str, Any]]] = {name: [] for name in schema()}

    def add(self, table_name: str, **row: Any) -> dict[str, Any]:
        columns = schema()[table_name]
        unknown = set(row).difference(columns)
        if unknown:
            raise KeyError(f"Unexpected {table_name} columns: {sorted(unknown)}")
        normalized = {column: row.get(column) for column in columns}
        self.tables[table_name].append(normalized)
        return normalized

    def has(self, table: str, field: str, value: object) -> bool:
        return any(row[field] == value for row in self.tables[table])

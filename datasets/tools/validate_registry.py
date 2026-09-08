"""Validate registry schema, keys, controlled vocabularies, and semantic determinism."""

from __future__ import annotations

import json
import hashlib
import math
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any

import pyarrow.parquet as pq

from registry_common import DATASETS, ROOT, schema

REGISTRY = DATASETS / "registry"
VOCAB = json.loads((DATASETS / "schema" / "controlled_vocabularies.json").read_text(encoding="utf-8"))


def _rows(table: str) -> list[dict[str, Any]]:
    return pq.read_table(REGISTRY / f"{table}.parquet").to_pylist()


def _ids(rows: list[dict[str, Any]], field: str) -> set[str]:
    values = [row[field] for row in rows]
    if any(value is None for value in values) or len(values) != len(set(values)):
        raise ValueError(f"{field} must be non-null and unique")
    return set(values)


def validate() -> dict[str, int]:
    tables = {name: _rows(name) for name in schema()}
    for name, columns in schema().items():
        if list(tables[name][0]) != columns if tables[name] else list(pq.read_schema(REGISTRY / f"{name}.parquet").names) != columns:
            raise ValueError(f"{name} schema columns differ from dataset_schema_v1.json")
        id_field = next((column for column in columns if column.endswith("_id")), None)
        if id_field:
            _ids(tables[name], id_field)
    for table, column, vocabulary in (("observations", "extraction_method", "extraction_method"), ("observations", "quality_class", "quality_class"), ("context_alterations", "alteration_type", "alteration_type"), ("source_artifacts", "artifact_type", "artifact_type"), ("model_mappings", "mapping_type", "mapping_type")):
        invalid = sorted({row[column] for row in tables[table] if row[column] not in VOCAB[vocabulary]})
        if invalid:
            raise ValueError(f"Invalid {table}.{column}: {invalid}")
    keys = {name: _ids(rows, next(column for column in schema()[name] if column.endswith("_id"))) for name, rows in tables.items() if any(column.endswith("_id") for column in schema()[name])}
    def fk(table: str, column: str, target: str) -> None:
        missing = {row[column] for row in tables[table] if row[column] is not None}.difference(keys[target])
        if missing:
            raise ValueError(f"Orphan {table}.{column}: {sorted(missing)[:3]}")
    fk("source_artifacts", "paper_id", "papers")
    fk("context_alterations", "context_id", "contexts")
    fk("conditions", "context_id", "contexts")
    fk("condition_steps", "condition_id", "conditions")
    fk("condition_steps", "perturbation_id", "perturbations")
    fk("assays", "paper_id", "papers")
    for column, target in (("paper_id", "papers"), ("context_id", "contexts"), ("condition_id", "conditions"), ("assay_id", "assays"), ("source_artifact_id", "source_artifacts")):
        fk("observations", column, target)
    fk("measurements", "observation_id", "observations")
    fk("measurements", "source_artifact_id", "source_artifacts")
    fk("extraction_runs", "observation_id", "observations")
    fk("extraction_runs", "source_artifact_id", "source_artifacts")
    missing_steps = keys["conditions"].difference({row["condition_id"] for row in tables["condition_steps"]})
    if missing_steps:
        raise ValueError(f"Conditions without steps: {sorted(missing_steps)[:3]}")
    for row in tables["source_artifacts"]:
        source = ROOT / row["path"]
        if not source.is_file():
            raise ValueError(f"Missing source artifact: {row['path']}")
        if hashlib.sha256(source.read_bytes()).hexdigest() != row["sha256"]:
            raise ValueError(f"Source artifact SHA-256 mismatch: {row['path']}")
    numeric_columns = {"dose_value", "start_time", "end_time", "reported_time", "value", "time_value", "uncertainty_value", "censoring_limit", "raw_intensity", "background_corrected_intensity", "total_protein_intensity", "ratio"}
    for table_name, rows in tables.items():
        for row in rows:
            for column in numeric_columns.intersection(row):
                value = row[column]
                if value is not None and (not isinstance(value, (int, float)) or not math.isfinite(value)):
                    raise ValueError(f"Invalid numeric/null value at {table_name}.{column}")
    for row in tables["model_mappings"]:
        if not row["observable"] or not row["model_id"] or not row["model_symbol_or_expression"]:
            raise ValueError("Model mappings require observable, model ID, and expression.")
    return {name: len(rows) for name, rows in tables.items()}


def semantic_snapshot() -> dict[str, list[dict[str, Any]]]:
    return {name: _rows(name) for name in schema()}


if __name__ == "__main__":
    counts = validate()
    for name, count in counts.items():
        print(f"validated {name}: {count}")

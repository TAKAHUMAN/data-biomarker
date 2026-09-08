"""Deterministically build authoritative Parquet registry tables from source/extracted inputs."""

from __future__ import annotations

import json
import shutil
from pathlib import Path
from typing import Any

import pyarrow as pa
import pyarrow.parquet as pq

from registry_common import DATASETS, ROOT, Registry, schema
from importers import alisertib, amg900, barasertib, birinapant, cilengitide, dactolisib_mm, dactolisib_ovarian, defactinib, dinaciclib, foretinib, luminespib, pemigatinib, tepotinib

REGISTRY_DIR = DATASETS / "registry"
EXTRACTED = DATASETS / "extracted"

DOUBLE = {"dose_value", "start_time", "end_time", "reported_time", "value", "time_value", "uncertainty_value", "censoring_limit", "raw_intensity", "background_corrected_intensity", "total_protein_intensity", "ratio"}
INT = {"sequence_index", "replicate_count", "replicate_index", "year"}
BOOL = {"is_censored"}


def _field(name: str) -> pa.Field:
    if name in DOUBLE:
        kind = pa.float64()
    elif name in INT:
        kind = pa.int64()
    elif name in BOOL:
        kind = pa.bool_()
    else:
        kind = pa.string()
    return pa.field(name, kind, nullable=True)


def _sort_key(row: dict[str, Any], id_field: str) -> tuple[str, ...]:
    return tuple("" if row.get(name) is None else str(row[name]) for name in (id_field, *sorted(row)))


def _write_intermediate_manifest(registry: Registry) -> None:
    """Keep deterministic parsing summaries separate from the raw source files."""
    by_study = {
        "alisertib": "paper_PMID22302096",
        "amg900": "paper_PMID29197031",
        "barasertib": "paper_PMID27496133",
        "birinapant": "paper_PMID23403634",
        "cilengitide": "paper_PMID23229276",
        "dactolisib_mm": "paper_PMID19584292",
        "dactolisib_ovarian": "paper_PMID32061787",
        "defactinib": "paper_PMID29314097",
        "dinaciclib_shao": "paper_PMID31561409",
        "dinaciclib_xu": "paper_PMID31349793",
        "foretinib": "paper_foretinib_flt3_itd_workbook",
        "luminespib": "paper_luminespib_hsp90_workbook",
        "pemigatinib": "paper_PMID32315352",
        "tepotinib": "paper_PMID33818908",
    }
    for study, paper_id in by_study.items():
        payload = {
            "schema_version": 1,
            "paper_id": paper_id,
            "source_artifacts": [row for row in registry.tables["source_artifacts"] if row["paper_id"] == paper_id],
            "parsed_observation_count": sum(row["paper_id"] == paper_id for row in registry.tables["observations"]),
            "note": "Deterministic parsing manifest generated from preserved raw and extracted source artifacts.",
        }
        directory = study.split("_")[0] if study.startswith("dinaciclib_") else study
        suffix = f"_{study.split('_', 1)[1]}" if study.startswith("dinaciclib_") else ""
        target = EXTRACTED / directory / f"registry_import_manifest{suffix}.json"
        target.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def build() -> dict[str, int]:
    registry = Registry()
    alisertib.collect(registry)
    amg900.collect(registry)
    barasertib.collect(registry)
    birinapant.collect(registry)
    cilengitide.collect(registry)
    dactolisib_mm.collect(registry)
    dactolisib_ovarian.collect(registry)
    defactinib.collect(registry)
    dinaciclib.collect(registry)
    foretinib.collect(registry)
    luminespib.collect(registry)
    pemigatinib.collect(registry)
    tepotinib.collect(registry)
    _write_intermediate_manifest(registry)
    REGISTRY_DIR.mkdir(parents=True, exist_ok=True)
    counts: dict[str, int] = {}
    for table_name, columns in schema().items():
        rows = registry.tables[table_name]
        id_field = next((column for column in columns if column.endswith("_id")), columns[0])
        rows = sorted(rows, key=lambda row: _sort_key(row, id_field))
        normalized = [{column: row.get(column) for column in columns} for row in rows]
        table = pa.Table.from_pylist(normalized, schema=pa.schema([_field(column) for column in columns]))
        pq.write_table(table, REGISTRY_DIR / f"{table_name}.parquet", compression="zstd", version="2.6")
        counts[table_name] = len(rows)
    return counts


if __name__ == "__main__":
    for name, count in build().items():
        print(f"{name}: {count}")

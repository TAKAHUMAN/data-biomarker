"""Freeze read-only registry selections into reproducible cohort manifests and exports."""

from __future__ import annotations

import argparse
import csv
import datetime as dt
import hashlib
import json
from pathlib import Path
from typing import Any

import pyarrow as pa
import pyarrow.parquet as pq

from query_registry import add_query_arguments, filters_from_args, flatten_records, query_observations
from registry_access import table
from registry_common import DATASETS, schema

ANALYSIS_EXPORTS = DATASETS / "exports" / "analysis"


def _safe_cohort_id(cohort_id: str) -> str:
    if not cohort_id or Path(cohort_id).name != cohort_id or cohort_id in {".", ".."}:
        raise ValueError("cohort_id must be a non-empty filename stem without path separators.")
    return cohort_id


def registry_semantic_digest() -> str:
    """Digest registry contents, not Parquet serialization metadata."""
    payload = {name: table(name) for name in schema()}
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"), allow_nan=False).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def create_cohort_manifest(cohort_id: str, description: str, query_filters: dict[str, Any]) -> dict[str, Any]:
    cohort_id = _safe_cohort_id(cohort_id)
    records = query_observations(**query_filters)
    observation_ids = [record["observation"]["observation_id"] for record in records]
    return {
        "cohort_id": cohort_id,
        "description": description,
        "created_from_registry_schema_version": 1,
        "registry_semantic_digest": registry_semantic_digest(),
        "query_filters": query_filters,
        "observation_ids": observation_ids,
        "observation_count": len(observation_ids),
        "paper_ids": sorted({record["observation"]["paper_id"] for record in records}),
        "context_ids": sorted({record["observation"]["context_id"] for record in records}),
        "observable_summary": {name: sum(record["observation"]["observable"] == name for record in records) for name in sorted({record["observation"]["observable"] for record in records})},
        "created_at": dt.datetime.now(dt.UTC).isoformat(),
    }


def write_cohort_manifest(manifest: dict[str, Any], path: Path | None = None) -> Path:
    target = path or ANALYSIS_EXPORTS / f"{manifest['cohort_id']}.cohort.json"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return target


def resolve_cohort_manifest(manifest: dict[str, Any], *, require_current_digest: bool = True) -> list[dict[str, Any]]:
    if require_current_digest and manifest["registry_semantic_digest"] != registry_semantic_digest():
        raise ValueError("Registry semantic digest differs from the frozen cohort manifest.")
    expected = list(manifest["observation_ids"])
    if len(expected) != len(set(expected)):
        raise ValueError("Frozen cohort manifest contains duplicate observation IDs.")
    records = query_observations(observation_ids=set(expected))
    actual = [record["observation"]["observation_id"] for record in records]
    if actual != sorted(expected):
        missing = sorted(set(expected).difference(actual))
        unexpected = sorted(set(actual).difference(expected))
        raise ValueError(f"Frozen cohort no longer resolves exactly (missing={missing}, unexpected={unexpected}).")
    return records


def export_cohort(manifest: dict[str, Any], export_format: str, output_dir: Path | None = None) -> tuple[Path, Path]:
    if export_format not in {"csv", "parquet"}:
        raise ValueError("export_format must be 'csv' or 'parquet'")
    records = resolve_cohort_manifest(manifest)
    rows = flatten_records(records)
    destination = output_dir or ANALYSIS_EXPORTS
    destination.mkdir(parents=True, exist_ok=True)
    data_path = destination / f"{manifest['cohort_id']}.{export_format}"
    if export_format == "csv":
        fields = sorted({field for row in rows for field in row})
        with data_path.open("w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore")
            writer.writeheader()
            writer.writerows(rows)
    else:
        pq.write_table(pa.Table.from_pylist(rows), data_path, compression="zstd", version="2.6")
    sidecar = {"cohort_id": manifest["cohort_id"], "registry_semantic_digest": manifest["registry_semantic_digest"], "observation_ids": manifest["observation_ids"], "schema_version": manifest["created_from_registry_schema_version"], "filters": manifest["query_filters"], "generation_timestamp": dt.datetime.now(dt.UTC).isoformat(), "export_path": data_path.name}
    sidecar_path = destination / f"{manifest['cohort_id']}.{export_format}.manifest.json"
    sidecar_path.write_text(json.dumps(sidecar, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return data_path, sidecar_path


def main() -> None:
    parser = argparse.ArgumentParser(description="Freeze a registry query and optionally export it.")
    parser.add_argument("--cohort-id", required=True)
    parser.add_argument("--description", required=True)
    parser.add_argument("--manifest", type=Path, help="Default: datasets/exports/analysis/<cohort_id>.cohort.json")
    parser.add_argument("--export", choices=("csv", "parquet"))
    add_query_arguments(parser)
    args = parser.parse_args()
    filters = filters_from_args(args)
    manifest = create_cohort_manifest(args.cohort_id, args.description, filters)
    path = write_cohort_manifest(manifest, args.manifest)
    print(path)
    if args.export:
        data_path, sidecar_path = export_cohort(manifest, args.export)
        print(data_path)
        print(sidecar_path)


if __name__ == "__main__":
    main()

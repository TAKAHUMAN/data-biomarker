"""Read-only, deterministic queries over biology-native registry observations.

One-to-many relations are represented as nested lists (``context_alterations``
and ``condition_steps``), so joining metadata never duplicates an observation.
"""

from __future__ import annotations

import argparse
import csv
import json
import math
import sys
from pathlib import Path
from typing import Any, Iterable

from registry_access import table


def _as_values(value: object | None) -> tuple[object, ...] | None:
    if value is None:
        return None
    if isinstance(value, (str, bytes)):
        return (value,)
    try:
        return tuple(value)  # type: ignore[arg-type]
    except TypeError:
        return (value,)


def _text_match(actual: object | None, wanted: object | None, *, substring: bool = False) -> bool:
    values = _as_values(wanted)
    if values is None:
        return True
    if actual is None:
        return False
    text = str(actual).casefold()
    return any((str(candidate).casefold() in text if substring else text == str(candidate).casefold()) for candidate in values)


def _number_match(actual: object | None, wanted: object | None) -> bool:
    values = _as_values(wanted)
    if values is None:
        return True
    if actual is None:
        return False
    return any(math.isclose(float(actual), float(candidate), rel_tol=0.0, abs_tol=1e-12) for candidate in values)


def _indexed_rows(rows: list[dict[str, Any]], field: str) -> dict[str, dict[str, Any]]:
    return {row[field]: row for row in rows}


def _linked_observations(*, include_model_mappings: bool) -> list[dict[str, Any]]:
    """Read tables and attach nested metadata while preserving one row per observation."""
    papers = _indexed_rows(table("papers"), "paper_id")
    contexts = _indexed_rows(table("contexts"), "context_id")
    conditions = _indexed_rows(table("conditions"), "condition_id")
    assays = _indexed_rows(table("assays"), "assay_id")
    artifacts = _indexed_rows(table("source_artifacts"), "source_artifact_id")
    perturbations = _indexed_rows(table("perturbations"), "perturbation_id")

    alterations: dict[str, list[dict[str, Any]]] = {}
    for row in table("context_alterations"):
        alterations.setdefault(row["context_id"], []).append(row)
    for rows in alterations.values():
        rows.sort(key=lambda row: row["context_alteration_id"])

    steps: dict[str, list[dict[str, Any]]] = {}
    for row in table("condition_steps"):
        linked = dict(row)
        linked["perturbation"] = perturbations[row["perturbation_id"]]
        steps.setdefault(row["condition_id"], []).append(linked)
    for rows in steps.values():
        rows.sort(key=lambda row: (row["sequence_index"], row["condition_step_id"]))

    mappings: dict[str, list[dict[str, Any]]] = {}
    if include_model_mappings:
        for row in table("model_mappings"):
            mappings.setdefault(row["observable"], []).append(row)
        for rows in mappings.values():
            rows.sort(key=lambda row: row["mapping_id"])

    output = []
    for observation in table("observations"):
        context = dict(contexts[observation["context_id"]])
        context["alterations"] = alterations.get(observation["context_id"], [])
        condition = dict(conditions[observation["condition_id"]])
        condition["steps"] = steps.get(observation["condition_id"], [])
        record = {
            "observation": observation,
            "paper": papers[observation["paper_id"]],
            "context": context,
            "condition": condition,
            "assay": assays[observation["assay_id"]],
            "source_artifact": artifacts[observation["source_artifact_id"]],
        }
        if include_model_mappings:
            record["model_mappings"] = mappings.get(observation["observable"], [])
        output.append(record)
    return output


def query_observations(
    *,
    paper_id: str | Iterable[str] | None = None,
    pmid: str | Iterable[str] | None = None,
    context_id: str | Iterable[str] | None = None,
    cell_line: str | Iterable[str] | None = None,
    species: str | Iterable[str] | None = None,
    gene: str | Iterable[str] | None = None,
    alteration_type: str | Iterable[str] | None = None,
    alteration: str | Iterable[str] | None = None,
    perturbation: str | Iterable[str] | None = None,
    observable: str | Iterable[str] | None = None,
    assay_type: str | Iterable[str] | None = None,
    time: float | Iterable[float] | None = None,
    time_unit: str | Iterable[str] | None = None,
    dose: float | Iterable[float] | None = None,
    dose_unit: str | Iterable[str] | None = None,
    extraction_method: str | Iterable[str] | None = None,
    quality_class: str | Iterable[str] | None = None,
    is_censored: bool | None = None,
    has_numeric_value: bool | None = None,
    observation_ids: str | Iterable[str] | None = None,
    include_model_mappings: bool = False,
) -> list[dict[str, Any]]:
    """Return deterministically ordered, nested biology-native observation records.

    Gene/alteration filters use an ``any alteration`` rule.  An
    ``alteration_type`` token also matches an alteration text token, which lets
    the common ``alteration_type='ITD'`` shorthand recover the registry's
    ``FLT3-ITD`` record even though its controlled type is ``MUTATION``.
    """
    selected = []
    for record in _linked_observations(include_model_mappings=include_model_mappings):
        obs, paper, context, condition, assay = (record["observation"], record["paper"], record["context"], record["condition"], record["assay"])
        if not (_text_match(obs["paper_id"], paper_id) and _text_match(paper["pmid"], pmid) and _text_match(obs["context_id"], context_id) and _text_match(context["cell_line"], cell_line, substring=True) and _text_match(context["species"], species) and _text_match(obs["observable"], observable, substring=True) and _text_match(assay["assay_type"], assay_type, substring=True) and _number_match(obs["time_value"], time) and _text_match(obs["time_unit"], time_unit) and _text_match(obs["extraction_method"], extraction_method) and _text_match(obs["quality_class"], quality_class) and _text_match(obs["observation_id"], observation_ids)):
            continue
        if is_censored is not None and obs["is_censored"] is not is_censored:
            continue
        if has_numeric_value is not None and (obs["value"] is not None) is not has_numeric_value:
            continue
        matching_alterations = context["alterations"]
        if gene is not None:
            matching_alterations = [row for row in matching_alterations if _text_match(row["gene"], gene)]
        if alteration is not None:
            matching_alterations = [row for row in matching_alterations if _text_match(row["alteration"], alteration, substring=True)]
        if alteration_type is not None:
            matching_alterations = [row for row in matching_alterations if _text_match(row["alteration_type"], alteration_type) or _text_match(row["alteration"], alteration_type, substring=True)]
        if any(value is not None for value in (gene, alteration_type, alteration)) and not matching_alterations:
            continue
        matching_steps = condition["steps"]
        if perturbation is not None:
            matching_steps = [row for row in matching_steps if _text_match(row["perturbation"]["name"], perturbation, substring=True) or _text_match(row["perturbation"]["source_name"], perturbation, substring=True)]
        if dose is not None:
            matching_steps = [row for row in matching_steps if _number_match(row["dose_value"], dose)]
        if dose_unit is not None:
            matching_steps = [row for row in matching_steps if _text_match(row["dose_unit"], dose_unit)]
        if any(value is not None for value in (perturbation, dose, dose_unit)) and not matching_steps:
            continue
        selected.append(record)
    return sorted(selected, key=lambda record: record["observation"]["observation_id"])


def flatten_records(records: Iterable[dict[str, Any]]) -> list[dict[str, Any]]:
    """Create a non-authoritative one-row-per-observation export representation."""
    output = []
    for record in records:
        row = dict(record["observation"])
        row.update({"paper_pmid": record["paper"]["pmid"], "paper_title": record["paper"]["title"], "context_cell_line": record["context"]["cell_line"], "context_species": record["context"]["species"], "assay_type": record["assay"]["assay_type"], "assay_name": record["assay"]["assay_name"], "source_artifact_path": record["source_artifact"]["path"], "context_alterations_json": json.dumps(record["context"]["alterations"], sort_keys=True), "condition_steps_json": json.dumps(record["condition"]["steps"], sort_keys=True)})
        if "model_mappings" in record:
            row["model_mappings_json"] = json.dumps(record["model_mappings"], sort_keys=True)
        output.append(row)
    return output


def add_query_arguments(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--paper-id")
    parser.add_argument("--pmid")
    parser.add_argument("--context-id")
    parser.add_argument("--cell-line")
    parser.add_argument("--species")
    parser.add_argument("--gene")
    parser.add_argument("--alteration-type")
    parser.add_argument("--alteration")
    parser.add_argument("--perturbation", "--drug", dest="perturbation")
    parser.add_argument("--observable")
    parser.add_argument("--assay-type")
    parser.add_argument("--time", type=float)
    parser.add_argument("--time-h", type=float, dest="time_h")
    parser.add_argument("--time-unit")
    parser.add_argument("--dose", type=float)
    parser.add_argument("--dose-unit")
    parser.add_argument("--extraction-method")
    parser.add_argument("--quality", dest="quality_class")
    parser.add_argument("--is-censored", choices=("true", "false"))
    parser.add_argument("--has-numeric-value", action="store_true", default=None)
    parser.add_argument("--include-model-mappings", action="store_true")


def filters_from_args(args: argparse.Namespace) -> dict[str, Any]:
    filters = {key: value for key, value in vars(args).items() if key in query_observations.__annotations__ and value is not None}
    if args.time_h is not None:
        filters["time"] = args.time_h
        filters["time_unit"] = "h"
    if args.is_censored is not None:
        filters["is_censored"] = args.is_censored == "true"
    return filters


def _write_csv(records: list[dict[str, Any]], stream: Any) -> None:
    rows = flatten_records(records)
    fields = sorted({field for row in rows for field in row})
    writer = csv.DictWriter(stream, fieldnames=fields, extrasaction="ignore")
    writer.writeheader()
    writer.writerows(rows)


def main() -> None:
    parser = argparse.ArgumentParser(description="Read-only registry observation query")
    add_query_arguments(parser)
    parser.add_argument("--format", choices=("json", "csv"), default="json")
    parser.add_argument("--output", type=Path, help="Optional output file; stdout is the default.")
    args = parser.parse_args()
    records = query_observations(**filters_from_args(args))
    if args.output is None:
        if args.format == "json":
            print(json.dumps(records, indent=2, sort_keys=True))
        else:
            _write_csv(records, sys.stdout)
        return
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", newline="", encoding="utf-8") as handle:
        if args.format == "json":
            json.dump(records, handle, indent=2, sort_keys=True)
            handle.write("\n")
        else:
            _write_csv(records, handle)


if __name__ == "__main__":
    main()

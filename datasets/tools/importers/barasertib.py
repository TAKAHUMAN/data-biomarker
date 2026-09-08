"""Import the curated Barasertib/AZD1152 study for PMID 27496133."""

from __future__ import annotations

import csv
import json
from pathlib import Path

from registry_common import DATASETS, Registry, clean_number, relative, sha256, stable_id


PAPER = "paper_PMID27496133"
DATA = DATASETS / "extracted" / "barasertib"
RAW_WORKBOOK = DATASETS / "raw" / "workbooks" / "BARASERTIB_OBSERVATIONS.xlsx"
RAW_PAPER = DATASETS / "raw" / "papers" / "PMID_27496133_PMC5050114.html"
FIGURE_DIR = DATASETS / "raw" / "images" / "barasertib"

EXTRACTION_METHODS = {"DIRECT_SOURCE", "TEXT_DERIVED", "PLOT_DIGITIZED", "BLOT_DENSITOMETRY", "IMAGE_DERIVED", "COMPUTED_FROM_SOURCE_VALUES"}
QUALITY_CLASSES = {"QUANTITATIVE", "SEMI_QUANTITATIVE", "QUALITATIVE_VALIDATION", "NOT_MODEL_READY"}


def _rows(name: str) -> list[dict[str, str]]:
    with (DATA / name).open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def _optional(value: str | None) -> str | None:
    return value if value not in (None, "") else None


def _integer(value: str | None) -> int | None:
    number = clean_number(value)
    return int(number) if number is not None else None


def _boolean(value: str | None) -> bool:
    return str(value).strip().lower() == "true"


def _context_id(key: str) -> str:
    return stable_id("context", PAPER, key)


def _condition_id(key: str) -> str:
    return stable_id("condition", PAPER, key)


def _assay_id(key: str) -> str:
    return stable_id("assay", PAPER, key)


def _perturbation(registry: Registry, name: str) -> str:
    perturbation_id = stable_id("perturbation", name)
    if not registry.has("perturbations", "perturbation_id", perturbation_id):
        registry.add(
            "perturbations", perturbation_id=perturbation_id, name=name,
            type="CONTROL" if name in {"Vehicle", "No perturbation"} else "DRUG",
            target_if_reported={"Barasertib-HQPA": "AURKB", "Barasertib": "AURKB", "Paclitaxel": "microtubules"}.get(name),
            source_name=name, notes="Barasertib-HQPA is the active metabolite used in vitro." if name == "Barasertib-HQPA" else None,
        )
    return perturbation_id


def collect(registry: Registry) -> None:
    metadata = json.loads((DATA / "extraction_metadata.json").read_text(encoding="utf-8"))
    registry.add(
        "papers", paper_id=PAPER, pmid="27496133", pmcid="PMC5050114",
        doi="10.1158/1535-7163.MCT-16-0298",
        title="Barasertib (AZD1152), a small molecule Aurora B inhibitor, inhibits the growth of SCLC cell lines in vitro and in vivo",
        year=2016, journal="Molecular Cancer Therapeutics",
        citation="Helfrich BA, et al. Mol Cancer Ther. 2016;15(10):2314-2322.",
        notes="In vitro experiments used active metabolite barasertib-HQPA; xenografts used parent barasertib.",
    )

    artifact_specs: list[tuple[str, Path, str, str, str | None]] = [
        ("artifact_PMID27496133_paper", RAW_PAPER, "PAPER", "PMC full-text HTML.", None),
        ("artifact_PMID27496133_workbook", RAW_WORKBOOK, "WORKBOOK", "Supplied workbook, preserved unchanged.", None),
        ("artifact_PMID27496133_json", DATA / "REGISTRY_IMPORT_DATA_BARASERTIB.json", "EXTRACTION_ARTIFACT", "Supplied JSON, preserved unchanged.", None),
        ("artifact_PMID27496133_supplied_importer", DATA / "supplied_barasertib_importer.py", "EXTRACTION_ARTIFACT", "Supplied draft importer; preserved but not executed.", None),
    ]
    for number in range(1, 5):
        artifact_specs.append((f"artifact_PMID27496133_figure_{number}", FIGURE_DIR / f"Helfrich_2016_Figure_{number}.jpg", "IMAGE", f"PMC Figure {number}.", f"Figure {number}"))
    for artifact_id, path, artifact_type, description, figure in artifact_specs:
        registry.add(
            "source_artifacts", source_artifact_id=artifact_id, paper_id=PAPER,
            artifact_type=artifact_type, path=relative(path), original_filename=path.name,
            sha256=sha256(path), figure=figure, panel=None, supplement_identifier=None,
            source_description=description,
        )

    for row in _rows("contexts.csv"):
        context_id = _context_id(row["context_key"])
        registry.add(
            "contexts", context_id=context_id, species=row["species"], cell_line=row["cell_line"],
            cell_type=_optional(row["cell_type"]), tissue=_optional(row["tissue"]),
            disease=_optional(row["disease"]), culture_context=_optional(row["culture_context"]),
            notes=_optional(row["notes"]),
        )
        match = next((gene for gene in ("MYC", "MYCL", "MYCN") if f"amplification: {gene}." in (row["notes"] or "")), None)
        if match:
            registry.add(
                "context_alterations",
                context_alteration_id=stable_id("context_alteration", context_id, match, "AMPLIFICATION"),
                context_id=context_id, gene=match, alteration_type="AMPLIFICATION",
                alteration=f"{match} amplification", zygosity_or_copy_context=None,
                source="PMID27496133 Table 1 and cited source datasets", notes=None,
            )

    for row in _rows("conditions.csv"):
        registry.add(
            "conditions", condition_id=_condition_id(row["condition_key"]),
            context_id=_context_id(row["context_key"]), condition_label=row["condition_label"],
            notes=_optional(row["notes"]),
        )
    for row in _rows("condition_steps.csv"):
        registry.add(
            "condition_steps", condition_step_id=stable_id("condition_step", PAPER, row["condition_step_key"]),
            condition_id=_condition_id(row["condition_key"]), perturbation_id=_perturbation(registry, row["perturbation_name"]),
            dose_value=clean_number(row["dose_value"]), dose_unit=_optional(row["dose_unit"]),
            start_time=clean_number(row["start_time"]), end_time=clean_number(row["end_time"]),
            time_unit=_optional(row["time_unit"]), sequence_index=_integer(row["sequence_index"]),
            notes=_optional(row["notes"]),
        )
    for row in _rows("assays.csv"):
        registry.add(
            "assays", assay_id=_assay_id(row["assay_key"]), paper_id=PAPER,
            assay_type=row["assay_type"], assay_name=row["assay_name"],
            sample_type=_optional(row["sample_type"]), measurement_platform=_optional(row["measurement_platform"]),
            figure=_optional(row["figure"]), panel=_optional(row["panel"]),
            reported_time=clean_number(row["reported_time"]), reported_time_unit=_optional(row["reported_time_unit"]),
            replicate_count=_integer(row["replicate_count"]), notes=_optional(row["notes"]),
        )

    for row in _rows("observations.csv"):
        method, quality = row["extraction_method"], row["quality_class"]
        if method not in EXTRACTION_METHODS or quality not in QUALITY_CLASSES:
            raise ValueError(f"Unsupported Barasertib method/quality: {method}/{quality}")
        source_key = row["source_key"]
        source_artifact_id = f"artifact_PMID27496133_{source_key}"
        observation_id = stable_id("obs", PAPER, row["record_id"])
        registry.add(
            "observations", observation_id=observation_id, paper_id=PAPER,
            context_id=_context_id(row["context_key"]), condition_id=_condition_id(row["condition_key"]),
            assay_id=_assay_id(row["assay_key"]), observable=row["observable"],
            observable_raw_label=row["observable_raw_label"], value=clean_number(row["value"]),
            value_unit=_optional(row["value_unit"]), time_value=clean_number(row["time_value"]),
            time_unit=_optional(row["time_unit"]), statistic=_optional(row["statistic"]),
            uncertainty_type=_optional(row["uncertainty_type"]), uncertainty_value=clean_number(row["uncertainty_value"]),
            replicate_count=_integer(row["replicate_count"]), normalization=_optional(row["normalization"]),
            normalization_reference=_optional(row["normalization_reference"]), source_artifact_id=source_artifact_id,
            figure=_optional(row["figure"]), panel=_optional(row["panel"]), table=_optional(row["table"]),
            lane=_optional(row["lane"]), extraction_method=method, quality_class=quality,
            is_censored=_boolean(row["is_censored"]), censoring_limit=clean_number(row["censoring_limit"]),
            notes=_optional(row["notes"]),
        )
        registry.add(
            "extraction_runs", extraction_run_id=stable_id("extraction", observation_id, "barasertib_v1"),
            source_artifact_id=source_artifact_id, observation_id=observation_id, method=method,
            software_or_script="prepare_barasertib.py with source-backed corrections",
            roi_information=None, background_method=None, raw_intensity=None,
            background_corrected_intensity=None, total_protein_intensity=None, ratio=None,
            normalization_method=_optional(row["normalization"]),
            operator_or_process="supplied extraction normalized against PMC5050114 full text",
            timestamp=metadata["extraction_date"], notes="See datasets/extracted/barasertib/extraction_metadata.json.",
        )

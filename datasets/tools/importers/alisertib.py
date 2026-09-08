"""Import the curated Alisertib/MLN8237 dataset for PMID 22302096."""

from __future__ import annotations

import csv
import json
from pathlib import Path

from registry_common import DATASETS, Registry, clean_number, relative, sha256, stable_id


PAPER = "paper_PMID22302096"
DATA = DATASETS / "extracted" / "alisertib"
RAW_WORKBOOK = DATASETS / "raw" / "workbooks" / "Alisertib_MLN8237_Registry_Ready.xlsx"
RAW_PDF = DATASETS / "raw" / "papers" / "PMID_22302096_PMC3297687.pdf"
SUPPLIED_JSON = DATA / "REGISTRY_IMPORT_DATA.json"

ARTIFACT_WORKBOOK = "artifact_PMID22302096_workbook"
ARTIFACT_IMPORT_JSON = "artifact_PMID22302096_import_json"
ARTIFACT_PAPER = "artifact_PMID22302096_paper"

EXTRACTION_METHODS = {
    "DIRECT_SOURCE", "TEXT_DERIVED", "PLOT_DIGITIZED", "BLOT_DENSITOMETRY",
    "IMAGE_DERIVED", "COMPUTED_FROM_SOURCE_VALUES",
}
QUALITY_CLASSES = {
    "QUANTITATIVE", "SEMI_QUANTITATIVE", "QUALITATIVE_VALIDATION", "NOT_MODEL_READY",
}


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
            "perturbations",
            perturbation_id=perturbation_id,
            name=name,
            type="CONTROL" if name == "Vehicle" else "DRUG",
            target_if_reported={"MLN8237": "AURKA", "Cisplatin": "DNA"}.get(name),
            source_name="MLN8237 (alisertib)" if name == "MLN8237" else name,
            notes=None,
        )
    return perturbation_id


def collect(registry: Registry) -> None:
    metadata = json.loads((DATA / "extraction_metadata.json").read_text(encoding="utf-8"))

    registry.add(
        "papers",
        paper_id=PAPER,
        pmid="22302096",
        pmcid="PMC3297687",
        doi="10.1158/1535-7163.MCT-11-0623",
        title="The Aurora kinase A inhibitor MLN8237 enhances cisplatin-induced cell death in esophageal adenocarcinoma cells",
        year=2012,
        journal="Molecular Cancer Therapeutics",
        citation="Sehdev V, et al. Mol Cancer Ther. 2012;11(3):763-774.",
        notes="Alisertib is also identified by its development code MLN8237.",
    )

    artifacts = [
        (
            ARTIFACT_WORKBOOK, RAW_WORKBOOK, "WORKBOOK",
            "Supplied curator workbook containing long-format annotations and extraction estimates.",
        ),
        (
            ARTIFACT_IMPORT_JSON, SUPPLIED_JSON, "EXTRACTION_ARTIFACT",
            "Supplied structured Figure 4 Day-21 endpoint extraction.",
        ),
    ]
    if RAW_PDF.is_file():
        artifacts.append((ARTIFACT_PAPER, RAW_PDF, "PAPER", "Preserved full paper, PMCID PMC3297687."))
    for artifact_id, path, artifact_type, description in artifacts:
        registry.add(
            "source_artifacts",
            source_artifact_id=artifact_id,
            paper_id=PAPER,
            artifact_type=artifact_type,
            path=relative(path),
            original_filename=path.name,
            sha256=sha256(path),
            figure=None,
            panel=None,
            supplement_identifier=None,
            source_description=description,
        )

    context_rows = _rows("contexts.csv")
    for row in context_rows:
        context_id = _context_id(row["context_key"])
        registry.add(
            "contexts",
            context_id=context_id,
            species=row["species"],
            cell_line=row["cell_line"],
            cell_type=_optional(row["cell_type"]),
            tissue=_optional(row["tissue"]),
            disease=_optional(row["disease"]),
            culture_context=_optional(row["culture_context"]),
            notes=_optional(row["notes"]),
        )
        for gene, alteration_type, alteration in (
            ("TP53", "MUTATION", "p53 mutant; specific variant not encoded in supplied extraction"),
            ("AURKA", "OVEREXPRESSION", "high AURKA expression"),
        ):
            registry.add(
                "context_alterations",
                context_alteration_id=stable_id(
                    "context_alteration", context_id, gene, alteration_type, alteration
                ),
                context_id=context_id,
                gene=gene,
                alteration_type=alteration_type,
                alteration=alteration,
                zygosity_or_copy_context=None,
                source="PMID22302096 Figure 1 and supplied study metadata",
                notes=None,
            )

    for row in _rows("conditions.csv"):
        registry.add(
            "conditions",
            condition_id=_condition_id(row["condition_key"]),
            context_id=_context_id(row["context_key"]),
            condition_label=row["condition_label"],
            notes=_optional(row["notes"]),
        )

    for row in _rows("condition_steps.csv"):
        name = row["perturbation_name"]
        registry.add(
            "condition_steps",
            condition_step_id=stable_id("condition_step", PAPER, row["condition_step_key"]),
            condition_id=_condition_id(row["condition_key"]),
            perturbation_id=_perturbation(registry, name),
            dose_value=clean_number(row["dose_value"]),
            dose_unit=_optional(row["dose_unit"]),
            start_time=clean_number(row["start_time"]),
            end_time=clean_number(row["end_time"]),
            time_unit=_optional(row["time_unit"]),
            sequence_index=_integer(row["sequence_index"]),
            notes=_optional(row["notes"]),
        )

    for row in _rows("assays.csv"):
        registry.add(
            "assays",
            assay_id=_assay_id(row["assay_key"]),
            paper_id=PAPER,
            assay_type=row["assay_type"],
            assay_name=row["assay_name"],
            sample_type=_optional(row["sample_type"]),
            measurement_platform=_optional(row["measurement_platform"]),
            figure=_optional(row["figure"]),
            panel=_optional(row["panel"]),
            reported_time=clean_number(row["reported_time"]),
            reported_time_unit=_optional(row["reported_time_unit"]),
            replicate_count=_integer(row["replicate_count"]),
            notes=_optional(row["notes"]),
        )

    artifact_by_source = {
        "workbook": ARTIFACT_WORKBOOK,
        "import_json": ARTIFACT_IMPORT_JSON,
    }
    for row in _rows("observations.csv"):
        method = row["extraction_method"]
        quality = row["quality_class"]
        if method not in EXTRACTION_METHODS:
            raise ValueError(f"Unsupported Alisertib extraction method: {method}")
        if quality not in QUALITY_CLASSES:
            raise ValueError(f"Unsupported Alisertib quality class: {quality}")
        source_artifact_id = artifact_by_source[row["source_key"]]
        observation_id = stable_id("obs", PAPER, row["record_id"])
        registry.add(
            "observations",
            observation_id=observation_id,
            paper_id=PAPER,
            context_id=_context_id(row["context_key"]),
            condition_id=_condition_id(row["condition_key"]),
            assay_id=_assay_id(row["assay_key"]),
            observable=row["observable"],
            observable_raw_label=row["observable_raw_label"],
            value=clean_number(row["value"]),
            value_unit=_optional(row["value_unit"]),
            time_value=clean_number(row["time_value"]),
            time_unit=_optional(row["time_unit"]),
            statistic=_optional(row["statistic"]),
            uncertainty_type=_optional(row["uncertainty_type"]),
            uncertainty_value=clean_number(row["uncertainty_value"]),
            replicate_count=_integer(row["replicate_count"]),
            normalization=_optional(row["normalization"]),
            normalization_reference=_optional(row["normalization_reference"]),
            source_artifact_id=source_artifact_id,
            figure=_optional(row["figure"]),
            panel=_optional(row["panel"]),
            table=_optional(row["table"]),
            lane=_optional(row["lane"]),
            extraction_method=method,
            quality_class=quality,
            is_censored=_boolean(row["is_censored"]),
            censoring_limit=clean_number(row["censoring_limit"]),
            notes=_optional(row["notes"]),
        )
        registry.add(
            "extraction_runs",
            extraction_run_id=stable_id("extraction", observation_id, "alisertib_v1"),
            source_artifact_id=source_artifact_id,
            observation_id=observation_id,
            method=method,
            software_or_script={
                "DIRECT_SOURCE": "manual transcription recorded in supplied extraction",
                "PLOT_DIGITIZED": "manual plot reading recorded in supplied extraction",
                "IMAGE_DERIVED": "manual visual annotation recorded in supplied workbook",
                "COMPUTED_FROM_SOURCE_VALUES": "normalization encoded in supplied workbook",
            }.get(method, "supplied extraction process"),
            roi_information=None,
            background_method=None,
            raw_intensity=None,
            background_corrected_intensity=None,
            total_protein_intensity=None,
            ratio=None,
            normalization_method=_optional(row["normalization"]),
            operator_or_process="supplied human-curated extraction normalized by prepare_alisertib.py",
            timestamp=metadata["extraction_date"],
            notes="See datasets/extracted/alisertib/extraction_metadata.json for limitations.",
        )

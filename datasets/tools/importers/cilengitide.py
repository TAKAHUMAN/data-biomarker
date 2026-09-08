"""Import the curated Cilengitide study for PMID 23229276."""

from __future__ import annotations

import csv
import json
from pathlib import Path

from registry_common import DATASETS, Registry, clean_number, relative, sha256, stable_id


PAPER = "paper_PMID23229276"
DATA = DATASETS / "extracted" / "cilengitide"
RAW_WORKBOOK = DATASETS / "raw" / "workbooks" / "cilengitide_pd_qsp_inputs.xlsx"
RAW_PDF = DATASETS / "raw" / "papers" / "PMID_23229276_PMC11824361.pdf"
RAW_HTML = DATASETS / "raw" / "papers" / "PMID_23229276_PMC11824361.html"
FIGURE_2 = DATASETS / "raw" / "images" / "cilengitide" / "Bretschi_2013_Figure_2.jpg"

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
            type="CONTROL" if name == "Sham treatment" else "DRUG",
            target_if_reported="integrins alpha-v beta-3 and alpha-v beta-5" if name == "Cilengitide" else None,
            source_name="EMD 121974" if name == "Cilengitide" else name,
            notes="Cyclic RGD pentapeptide integrin inhibitor." if name == "Cilengitide" else "No active drug.",
        )
    return perturbation_id


def collect(registry: Registry) -> None:
    metadata = json.loads((DATA / "extraction_metadata.json").read_text(encoding="utf-8"))
    registry.add(
        "papers", paper_id=PAPER, pmid="23229276", pmcid="PMC11824361",
        doi="10.1007/s00432-012-1360-6",
        title="Cilengitide affects tumor compartment, vascularization and microenvironment in experimental bone metastases as shown by longitudinal 18F-FDG PET and gene expression analysis",
        year=2013, journal="Journal of Cancer Research and Clinical Oncology",
        citation="Bretschi M, et al. J Cancer Res Clin Oncol. 2013;139(4):573-583.",
        notes="PD-only in-vivo dataset; Figure 2 PET values are approximate digitizations.",
    )

    artifact_specs = [
        ("artifact_PMID23229276_paper", RAW_PDF, "PAPER", "Article PDF obtained through Europe PMC.", None, None),
        ("artifact_PMID23229276_paper_html", RAW_HTML, "PAPER", "PMC full-text HTML used for text verification.", None, None),
        ("artifact_PMID23229276_workbook", RAW_WORKBOOK, "WORKBOOK", "Supplied annotated workbook, preserved unchanged.", None, None),
        ("artifact_PMID23229276_figure_2", FIGURE_2, "IMAGE", "PMC Figure 2 source image for PET digitization.", "Figure 2", "a-f"),
    ]
    for artifact_id, path, artifact_type, description, figure, panel in artifact_specs:
        registry.add(
            "source_artifacts", source_artifact_id=artifact_id, paper_id=PAPER,
            artifact_type=artifact_type, path=relative(path), original_filename=path.name,
            sha256=sha256(path), figure=figure, panel=panel, supplement_identifier=None,
            source_description=description,
        )

    for row in _rows("contexts.csv"):
        registry.add(
            "contexts", context_id=_context_id(row["context_key"]), species=row["species"],
            cell_line=row["cell_line"], cell_type=_optional(row["cell_type"]),
            tissue=_optional(row["tissue"]), disease=_optional(row["disease"]),
            culture_context=_optional(row["culture_context"]), notes=_optional(row["notes"]),
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
            condition_id=_condition_id(row["condition_key"]),
            perturbation_id=_perturbation(registry, row["perturbation_name"]),
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
            raise ValueError(f"Unsupported Cilengitide method/quality: {method}/{quality}")
        source_artifact_id = f"artifact_PMID23229276_{row['source_key']}"
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
            "extraction_runs", extraction_run_id=stable_id("extraction", observation_id, "cilengitide_v1"),
            source_artifact_id=source_artifact_id, observation_id=observation_id, method=method,
            software_or_script="prepare_cilengitide.py", roi_information=None,
            background_method=None, raw_intensity=None, background_corrected_intensity=None,
            total_protein_intensity=None, ratio=None,
            normalization_method=_optional(row["normalization"]),
            operator_or_process="supplied workbook normalized and checked against PMID 23229276",
            timestamp=metadata["extraction_date"],
            notes="See datasets/extracted/cilengitide/extraction_metadata.json.",
        )

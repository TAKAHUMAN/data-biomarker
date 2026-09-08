"""Import the curated Birinapant (TL32711) melanoma study for PMID 23403634."""

from __future__ import annotations

import csv
import json
import re
from pathlib import Path

from registry_common import DATASETS, Registry, clean_number, relative, sha256, stable_id


PAPER = "paper_PMID23403634"
DATA = DATASETS / "extracted" / "birinapant"
RAW_WORKBOOK = DATASETS / "raw" / "workbooks" / "BIRINAPANT_OBSERVATIONS.xlsx"
RAW_QSP_WORKBOOK = DATASETS / "raw" / "workbooks" / "birinapant_qsp_biomarker_digitization.xlsx"
RAW_PAPER = DATASETS / "raw" / "papers" / "PMID_23403634_PMC3618495.html"
RAW_SUPPLEMENT = DATASETS / "raw" / "supplementary" / "birinapant" / "NIHMS446445-supplement-1.docx"
FIGURE_DIR = DATASETS / "raw" / "images" / "birinapant"

EXTRACTION_METHODS = {"DIRECT_SOURCE", "TEXT_DERIVED", "PLOT_DIGITIZED", "BLOT_DENSITOMETRY", "IMAGE_DERIVED", "COMPUTED_FROM_SOURCE_VALUES"}
QUALITY_CLASSES = {"QUANTITATIVE", "SEMI_QUANTITATIVE", "QUALITATIVE_VALIDATION", "NOT_MODEL_READY"}

GENOTYPE_PATTERN = re.compile(r"\b(BRAF|NRAS)([A-Z]\d+[A-Z])\b")

PERTURBATION_INFO = {
    "Birinapant": ("DRUG", "cIAP1/cIAP2 (SMAC mimetic)", "SMAC mimetic; bivalent Kd cIAP-1 <1 nM, XIAP 45 nM; also known as TL32711."),
    "TNF-alpha": ("PERTURBAGEN", None, "Tumor necrosis factor alpha; endogenous in WM9, exogenous stimulus in combination-sensitive lines."),
    "Z-VAD-FMK": ("INHIBITOR", "pan-caspase", "Broad-spectrum caspase inhibitor used to test caspase-dependence of birinapant+TNF-alpha killing."),
    "Necrostatin-1": ("INHIBITOR", "RIP1 kinase", "RIP1 kinase inhibitor used to test RIP1-kinase-dependence of birinapant+TNF-alpha killing."),
    "TNF-alpha blocking antibody": ("INHIBITOR", "TNF-alpha", "Neutralizing monoclonal antibody against endogenous TNF-alpha."),
    "Cisplatin": ("DRUG", "DNA crosslinking", "Platinum-based chemotherapeutic used in combination with birinapant."),
    "Vehicle": ("CONTROL", None, "No active drug."),
    "No perturbation": ("CONTROL", None, "Untreated/analytical condition."),
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
        ptype, target, notes = PERTURBATION_INFO.get(name, ("DRUG", None, None))
        registry.add(
            "perturbations", perturbation_id=perturbation_id, name=name, type=ptype,
            target_if_reported=target, source_name="TL32711" if name == "Birinapant" else name,
            notes=notes,
        )
    return perturbation_id


def collect(registry: Registry) -> None:
    metadata = json.loads((DATA / "extraction_metadata.json").read_text(encoding="utf-8"))
    registry.add(
        "papers", paper_id=PAPER, pmid="23403634", pmcid="PMC3618495",
        doi="10.1158/1078-0432.CCR-12-2518",
        title="The novel SMAC mimetic birinapant exhibits potent activity against human melanoma cells",
        year=2013, journal="Clinical Cancer Research",
        citation="Krepler C, et al. Clin Cancer Res. 2013;19(7):1784-1794.",
        notes="Three-tiered melanoma sensitivity phenotype: single-agent sensitive (WM9, 1/17), "
              "combination (birinapant+TNF-alpha) sensitive (9/17), resistant (7/17); cIAP1 degradation "
              "occurs in all lines tested, so resistance is downstream of target engagement.",
    )

    artifact_specs: list[tuple[str, Path, str, str, str | None]] = [
        ("artifact_PMID23403634_paper", RAW_PAPER, "PAPER", "PMC full-text HTML.", None),
        ("artifact_PMID23403634_workbook", RAW_WORKBOOK, "WORKBOOK", "Supplied curated observations workbook, preserved unchanged.", None),
        ("artifact_PMID23403634_qsp_workbook", RAW_QSP_WORKBOOK, "WORKBOOK", "Supplied QSP/biomarker digitization workbook, preserved unchanged.", None),
        ("artifact_PMID23403634_supplement", RAW_SUPPLEMENT, "SUPPLEMENT", "Supplementary material (NIHMS446445-supplement-1.docx), preserved unchanged.", None),
        ("artifact_PMID23403634_json", DATA / "REGISTRY_IMPORT_DATA_BIRINAPANT.json", "EXTRACTION_ARTIFACT", "Supplied draft JSON, preserved but not authoritative.", None),
        ("artifact_PMID23403634_supplied_importer", DATA / "supplied_birinapant_importer.py", "EXTRACTION_ARTIFACT", "Supplied draft importer (old API); preserved but not executed.", None),
        ("artifact_PMID23403634_moa_doc", DATA / "BIRINAPANT_SMAC_MIMETIC_MOA.md", "EXTRACTION_ARTIFACT", "Supplied mechanism-of-action/study-summary reference document.", None),
    ]
    for number in range(1, 7):
        artifact_specs.append((f"artifact_PMID23403634_figure_{number}", FIGURE_DIR / f"Krepler_2013_Figure_{number}.jpg", "IMAGE", f"PMC Figure {number}.", f"Figure {number}"))
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
        match = GENOTYPE_PATTERN.search(row["notes"] or "")
        if match:
            gene, alteration = match.groups()
            registry.add(
                "context_alterations",
                context_alteration_id=stable_id("context_alteration", context_id, gene, alteration),
                context_id=context_id, gene=gene, alteration_type="MUTATION",
                alteration=f"{gene}{alteration}", zygosity_or_copy_context=None,
                source="PMID23403634 Figure 1 phenotype annotation", notes=None,
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
            raise ValueError(f"Unsupported Birinapant method/quality: {method}/{quality}")
        source_artifact_id = f"artifact_PMID23403634_{row['source_key']}"
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
            "extraction_runs", extraction_run_id=stable_id("extraction", observation_id, "birinapant_v1"),
            source_artifact_id=source_artifact_id, observation_id=observation_id, method=method,
            software_or_script="prepare_birinapant.py",
            roi_information=None, background_method=None, raw_intensity=None,
            background_corrected_intensity=None, total_protein_intensity=None, ratio=None,
            normalization_method=_optional(row["normalization"]),
            operator_or_process="supplied workbook normalized and spot-checked against PMID23403634/PMC3618495",
            timestamp=metadata["extraction_date"],
            notes="See datasets/extracted/birinapant/extraction_metadata.json.",
        )

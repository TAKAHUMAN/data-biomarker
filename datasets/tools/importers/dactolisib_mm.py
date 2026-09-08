"""Import the curated Dactolisib (NVP-BEZ235) multiple myeloma study for PMID 19584292.

No local paper PDF/HTML file exists for this study (no PMCID; publisher-only full
text) -- this importer therefore does not register a PAPER-type source_artifacts
row, mirroring importers/pemigatinib.py's pattern for a real-PMID study without a
local paper file. All data comes from the supplied curated workbook and the
companion human-written MOA cascade doc + its annotation workbook, all preserved
unchanged as EXTRACTION_ARTIFACT/WORKBOOK source_artifacts.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

from registry_common import DATASETS, Registry, clean_number, relative, sha256, stable_id

import csv


PAPER = "paper_PMID19584292"
DATA = DATASETS / "extracted" / "dactolisib_mm"
RAW_WORKBOOK = DATASETS / "raw" / "workbooks" / "dactolisib_multipleMyeloma_extracted.xlsx"
RAW_ANNOTATION_WORKBOOK = DATASETS / "raw" / "workbooks" / "BEZ235_QSP_PD_Biomarker_Cascade_Annotations.xlsx"
MOA_DOC = DATA / "BEZ235_QSP_PD_Biomarker_Cascade.md"

EXTRACTION_METHODS = {"DIRECT_SOURCE", "TEXT_DERIVED", "PLOT_DIGITIZED", "BLOT_DENSITOMETRY", "IMAGE_DERIVED", "COMPUTED_FROM_SOURCE_VALUES"}
QUALITY_CLASSES = {"QUANTITATIVE", "SEMI_QUANTITATIVE", "QUALITATIVE_VALIDATION", "NOT_MODEL_READY"}

GENE_PATTERN = re.compile(r"\b(Akt|Bcl-2)\b(?:[^.]*?)\boverexpression", re.IGNORECASE)

PERTURBATION_INFO = {
    "Dactolisib": ("DRUG", "PI3K/mTOR (dual)", "Dual PI3K/mTOR inhibitor; also known as NVP-BEZ235/BEZ235."),
    "Vehicle": ("CONTROL", None, "No active drug."),
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
            target_if_reported=target, source_name="NVP-BEZ235" if name == "Dactolisib" else name,
            notes=notes,
        )
    return perturbation_id


def collect(registry: Registry) -> None:
    metadata = json.loads((DATA / "extraction_metadata.json").read_text(encoding="utf-8"))
    registry.add(
        "papers", paper_id=PAPER, pmid="19584292", pmcid=None,
        doi="10.1158/0008-5472.CAN-09-0715",
        title="Antimyeloma Activity of the Orally Bioavailable Dual Phosphatidylinositol 3-Kinase/Mammalian "
              "Target of Rapamycin Inhibitor NVP-BEZ235",
        year=2009, journal="Cancer Research",
        citation="McMillin DW, Ooi M, Delmore J, et al. Cancer Res. 2009;69(14):5835-5842.",
        notes="No PMCID; no local paper PDF/HTML available (publisher-only full text). Five-tier PD cascade "
              "(target modulation -> survival-signaling balance -> transcriptional output -> cell-death "
              "execution -> tumor/efficacy endpoint) documented in the companion MOA doc. Two engineered MM.1S "
              "sublines (myr-Akt, Bcl-2 overexpression) used as genetic-rescue probes of the survival-signaling "
              "tier; only Bcl-2 overexpression confers partial protection (non-zero survival plateau).",
    )

    artifact_specs: list[tuple[str, Path, str, str, str | None]] = [
        ("artifact_PMID19584292_workbook", RAW_WORKBOOK, "WORKBOOK", "Supplied curated per-figure digitization workbook, preserved unchanged.", None),
        ("artifact_PMID19584292_annotation_workbook", RAW_ANNOTATION_WORKBOOK, "WORKBOOK", "Supplied companion QSP/PD biomarker cascade annotation workbook (Cascade Map, Digitized Data, Figure Annotations, Modeling Notes), preserved unchanged.", None),
        ("artifact_PMID19584292_moa_doc", MOA_DOC, "EXTRACTION_ARTIFACT", "Supplied human-written mechanism-of-action / PD biomarker cascade reference document; source of the Fig1C/Fig2A/Fig2B digitized tables used here.", None),
    ]
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
        match = GENE_PATTERN.search(row["notes"] or "")
        if match:
            variant = match.group(1)
            gene = "AKT1" if "akt" in variant.lower() else "BCL2"
            registry.add(
                "context_alterations",
                context_alteration_id=stable_id("context_alteration", context_id, gene, "overexpression"),
                context_id=context_id, gene=gene, alteration_type="OVEREXPRESSION",
                alteration=f"{gene} stable overexpression ({variant})", zygosity_or_copy_context=None,
                source="PMID19584292 Figure 2 genetic-rescue subline", notes=None,
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
            raise ValueError(f"Unsupported Dactolisib MM method/quality: {method}/{quality}")
        source_artifact_id = f"artifact_PMID19584292_{row['source_key']}"
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
            "extraction_runs", extraction_run_id=stable_id("extraction", observation_id, "dactolisib_mm_v1"),
            source_artifact_id=source_artifact_id, observation_id=observation_id, method=method,
            software_or_script="prepare_dactolisib_mm.py",
            roi_information=None, background_method=None, raw_intensity=None,
            background_corrected_intensity=None, total_protein_intensity=None, ratio=None,
            normalization_method=_optional(row["normalization"]),
            operator_or_process="supplied workbook + companion MOA doc normalized into registry-v1 CSVs",
            timestamp=metadata["extraction_date"],
            notes="See datasets/extracted/dactolisib_mm/extraction_metadata.json.",
        )

"""Import the curated Dinaciclib hepatocellular carcinoma (HCC) study, spanning two
related papers (Xu et al. 2019, PMID 31349793; Shao et al. 2019, PMID 31561409),
registered as PAPER-less/workbook-driven (no local paper PDF/HTML for either study --
this is a workbook + companion-MOA-doc-only build, mirroring importers/pemigatinib.py's
pattern for a real-PMID study without a local paper file). All data comes from the
supplied curated workbook, the companion QSP/PD biomarker cascade annotation workbook
(covering both papers), and the human-written MOA cascade doc, all preserved unchanged
as WORKBOOK/EXTRACTION_ARTIFACT source_artifacts.

Every row is tagged with the correct paper_id via each CSV row's `paper_key` column
(contexts/conditions/condition_steps carry no explicit paper_key -- they are attributed
through the observations/assays that reference them, same as other single-paper
importers; assays and observations do carry an explicit paper_key).
"""

from __future__ import annotations

import csv
import json
from pathlib import Path

from registry_common import DATASETS, Registry, clean_number, relative, sha256, stable_id


PAPER_SHAO = "paper_PMID31561409"
PAPER_XU = "paper_PMID31349793"
DATA = DATASETS / "extracted" / "dinaciclib"
RAW_WORKBOOK = DATASETS / "raw" / "workbooks" / "dinaciclib_HCC_extracted.xlsx"
RAW_ANNOTATION_WORKBOOK = DATASETS / "raw" / "workbooks" / "Dinaciclib_QSP_PD_Biomarker_Cascade_Annotations.xlsx"
MOA_DOC = DATA / "Dinaciclib_QSP_PD_Biomarker_Cascade.md"

EXTRACTION_METHODS = {"DIRECT_SOURCE", "TEXT_DERIVED", "PLOT_DIGITIZED", "BLOT_DENSITOMETRY", "IMAGE_DERIVED", "COMPUTED_FROM_SOURCE_VALUES"}
QUALITY_CLASSES = {"QUANTITATIVE", "SEMI_QUANTITATIVE", "QUALITATIVE_VALIDATION", "NOT_MODEL_READY"}

PERTURBATION_INFO = {
    "Dinaciclib": ("DRUG", "CDK1/CDK2/CDK5/CDK9", "Pan-CDK inhibitor; composite CDK1/2/5/9 inhibition."),
    "Flavopiridol": ("DRUG", "CDK1/CDK2/CDK4/CDK6/CDK9", "Pan-CDK inhibitor used alongside dinaciclib as a second tool compound in Xu et al."),
    "Sorafenib": ("DRUG", "multi-kinase (VEGFR/PDGFR/RAF)", "Standard-of-care multi-kinase inhibitor comparator/combination partner."),
    "Regorafenib": ("DRUG", "multi-kinase (VEGFR/PDGFR/RAF/KIT)", "Standard-of-care multi-kinase inhibitor comparator/combination partner; second-line HCC therapy."),
    "Vehicle": ("CONTROL", None, "No active drug."),
    "siNT": ("GENETIC_PERTURBATION", None, "Non-targeting control siRNA."),
    "siCDK1": ("GENETIC_PERTURBATION", "CDK1", "siRNA knockdown of CDK1."),
    "siCDK2": ("GENETIC_PERTURBATION", "CDK2", "siRNA knockdown of CDK2."),
    "siCDK5": ("GENETIC_PERTURBATION", "CDK5", "siRNA knockdown of CDK5."),
    "siCDK9": ("GENETIC_PERTURBATION", "CDK9", "siRNA knockdown of CDK9."),
    "siCDK1+2+5+9": ("GENETIC_PERTURBATION", "CDK1/CDK2/CDK5/CDK9", "Composite siRNA knockdown of all four CDK targets."),
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
    return stable_id("context", "dinaciclib", key)


def _condition_id(key: str) -> str:
    return stable_id("condition", "dinaciclib", key)


def _assay_id(paper_id: str, key: str) -> str:
    return stable_id("assay", paper_id, key)


def _perturbation(registry: Registry, name: str) -> str:
    perturbation_id = stable_id("perturbation", name)
    if not registry.has("perturbations", "perturbation_id", perturbation_id):
        ptype, target, notes = PERTURBATION_INFO.get(name, ("DRUG", None, None))
        registry.add(
            "perturbations", perturbation_id=perturbation_id, name=name, type=ptype,
            target_if_reported=target, source_name=name, notes=notes,
        )
    return perturbation_id


def collect(registry: Registry) -> None:
    metadata = json.loads((DATA / "extraction_metadata.json").read_text(encoding="utf-8"))

    registry.add(
        "papers", paper_id=PAPER_SHAO, pmid="31561409", pmcid="PMC6827105", doi=None,
        title="Potent Activity of Composite Cyclin Dependent Kinase Inhibition against Hepatocellular Carcinoma",
        year=2019, journal="Cancers (Basel)",
        citation="Shao YY, Li YS, Hsu HW, et al. Cancers (Basel). 2019;11(10):1433.",
        notes="PMID/PMCID given directly in the supplied dinaciclib_HCC_extracted.xlsx workbook's Summary sheet. "
              "Richest quantitative target-engagement dataset of either paper (Fig3A printed densitometry grid, "
              "dose x time x cell line). One paper of a two-paper dinaciclib-in-HCC package; see paper_PMID31349793 "
              "(Xu et al.) for the companion cyclin-E1/sensitization story.",
    )
    registry.add(
        "papers", paper_id=PAPER_XU, pmid="31349793", pmcid="PMC6660968", doi="10.1186/s12964-019-0398-3",
        title="Inhibition of cyclin E1 sensitizes hepatocellular carcinoma cells to regorafenib by mcl-1 suppression",
        year=2019, journal="Cell Communication and Signaling",
        citation="Xu J, Huang F, Yao Z, et al. Cell Commun Signal. 2019;17:85.",
        notes="No PMID was stated anywhere in the two supplied workbooks or the companion MD doc for this paper; "
              "confirmed independently via web search (PMC6660968 -> PMID 31349793, DOI 10.1186/s12964-019-0398-3), "
              "not guessed. Establishes cyclin E1 (CCNE1) as a baseline predictive biomarker for sorafenib/"
              "regorafenib resistance (Tier 0, not a dinaciclib pharmacodynamic target) and dinaciclib/flavopiridol "
              "as sensitizers via STAT3->Mcl-1 suppression. One paper of a two-paper dinaciclib-in-HCC package; "
              "see paper_PMID31561409 (Shao et al.) for the companion composite-CDK-inhibition mechanism story.",
    )

    artifact_specs: list[tuple[str, Path, str, str]] = [
        ("artifact_dinaciclib_workbook", RAW_WORKBOOK, "WORKBOOK", "Supplied curated per-figure digitization workbook (Shao et al. only), preserved unchanged."),
        ("artifact_dinaciclib_annotation_workbook", RAW_ANNOTATION_WORKBOOK, "WORKBOOK", "Supplied companion QSP/PD biomarker cascade annotation workbook covering BOTH papers (Cascade Map, Digitized Data, Figure Annotations, Modeling Notes), preserved unchanged."),
        ("artifact_dinaciclib_moa_doc", MOA_DOC, "EXTRACTION_ARTIFACT", "Supplied human-written mechanism-of-action / PD biomarker cascade reference document spanning both papers."),
    ]
    for artifact_id, path, artifact_type, description in artifact_specs:
        for paper_id in (PAPER_SHAO, PAPER_XU):
            registry.add(
                "source_artifacts", source_artifact_id=f"{artifact_id}_{paper_id.replace('paper_', '')}",
                paper_id=paper_id, artifact_type=artifact_type, path=relative(path),
                original_filename=path.name, sha256=sha256(path), figure=None, panel=None,
                supplement_identifier=None, source_description=description,
            )

    def artifact_id_for(source_key: str, paper_id: str) -> str:
        name = {"workbook": "artifact_dinaciclib_workbook", "annotation_workbook": "artifact_dinaciclib_annotation_workbook", "moa_doc": "artifact_dinaciclib_moa_doc"}[source_key]
        return f"{name}_{paper_id.replace('paper_', '')}"

    for row in _rows("contexts.csv"):
        context_id = _context_id(row["context_key"])
        registry.add(
            "contexts", context_id=context_id, species=row["species"], cell_line=_optional(row["cell_line"]),
            cell_type=_optional(row["cell_type"]), tissue=_optional(row["tissue"]),
            disease=_optional(row["disease"]), culture_context=_optional(row["culture_context"]),
            notes=_optional(row["notes"]),
        )

    for row in _rows("context_alterations.csv"):
        context_id = _context_id(row["context_key"])
        registry.add(
            "context_alterations",
            context_alteration_id=stable_id("context_alteration", context_id, row["gene"], row["alteration_type"], row["alteration"]),
            context_id=context_id, gene=row["gene"], alteration_type=row["alteration_type"],
            alteration=row["alteration"], zygosity_or_copy_context=None, source=_optional(row["source"]), notes=None,
        )

    for row in _rows("conditions.csv"):
        registry.add(
            "conditions", condition_id=_condition_id(row["condition_key"]),
            context_id=_context_id(row["context_key"]), condition_label=row["condition_label"],
            notes=_optional(row["notes"]),
        )
    for row in _rows("condition_steps.csv"):
        registry.add(
            "condition_steps", condition_step_id=stable_id("condition_step", "dinaciclib", row["condition_step_key"]),
            condition_id=_condition_id(row["condition_key"]),
            perturbation_id=_perturbation(registry, row["perturbation_name"]),
            dose_value=clean_number(row["dose_value"]), dose_unit=_optional(row["dose_unit"]),
            start_time=clean_number(row["start_time"]), end_time=clean_number(row["end_time"]),
            time_unit=_optional(row["time_unit"]), sequence_index=_integer(row["sequence_index"]),
            notes=_optional(row["notes"]),
        )
    for row in _rows("assays.csv"):
        paper_id = row["paper_key"]
        registry.add(
            "assays", assay_id=_assay_id(paper_id, row["assay_key"]), paper_id=paper_id,
            assay_type=row["assay_type"], assay_name=row["assay_name"],
            sample_type=_optional(row["sample_type"]), measurement_platform=_optional(row["measurement_platform"]),
            figure=_optional(row["figure"]), panel=_optional(row["panel"]),
            reported_time=clean_number(row["reported_time"]), reported_time_unit=_optional(row["reported_time_unit"]),
            replicate_count=_integer(row["replicate_count"]), notes=_optional(row["notes"]),
        )

    for row in _rows("observations.csv"):
        method, quality = row["extraction_method"], row["quality_class"]
        if method not in EXTRACTION_METHODS or quality not in QUALITY_CLASSES:
            raise ValueError(f"Unsupported Dinaciclib method/quality: {method}/{quality}")
        paper_id = row["paper_key"]
        source_artifact_id = artifact_id_for(row["source_key"], paper_id)
        observation_id = stable_id("obs", paper_id, row["record_id"])
        registry.add(
            "observations", observation_id=observation_id, paper_id=paper_id,
            context_id=_context_id(row["context_key"]), condition_id=_condition_id(row["condition_key"]),
            assay_id=_assay_id(paper_id, row["assay_key"]), observable=row["observable"],
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
            "extraction_runs", extraction_run_id=stable_id("extraction", observation_id, "dinaciclib_v1"),
            source_artifact_id=source_artifact_id, observation_id=observation_id, method=method,
            software_or_script="prepare_dinaciclib.py",
            roi_information=None, background_method=None, raw_intensity=None,
            background_corrected_intensity=None, total_protein_intensity=None, ratio=None,
            normalization_method=_optional(row["normalization"]),
            operator_or_process="supplied workbooks + companion MOA doc normalized into registry-v1 CSVs",
            timestamp=metadata["extraction_date"],
            notes="See datasets/extracted/dinaciclib/extraction_metadata.json.",
        )

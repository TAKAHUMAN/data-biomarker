"""Import the curated Dactolisib (BEZ235) ABCB1-overexpressing ovarian/pancreatic
cancer study for PMID 32061787.

PMID 32061787 has a PMCID (PMC10845210) but no local PMC HTML/paper file is
available -- this importer therefore does not register a PAPER-type
source_artifacts row, mirroring importers/dactolisib_mm.py and
importers/pemigatinib.py. All data comes from the supplied curated workbook and
the companion QSP-recommendation workbook, both preserved unchanged as WORKBOOK
source_artifacts. There is no in vivo/tumour model in this paper.
"""

from __future__ import annotations

import csv
import json
from pathlib import Path

from registry_common import DATASETS, Registry, clean_number, relative, sha256, stable_id


PAPER = "paper_PMID32061787"
DATA = DATASETS / "extracted" / "dactolisib_ovarian"
RAW_WORKBOOK = DATASETS / "raw" / "workbooks" / "dactolisib_ABCB1ovarian_extracted.xlsx"
RAW_QSP_WORKBOOK = DATASETS / "raw" / "workbooks" / "bez235_dox_qsp_pd_digitization.xlsx"

EXTRACTION_METHODS = {"DIRECT_SOURCE", "TEXT_DERIVED", "PLOT_DIGITIZED", "BLOT_DENSITOMETRY", "IMAGE_DERIVED", "COMPUTED_FROM_SOURCE_VALUES"}
QUALITY_CLASSES = {"QUANTITATIVE", "SEMI_QUANTITATIVE", "QUALITATIVE_VALIDATION", "NOT_MODEL_READY"}

PERTURBATION_INFO = {
    "Dactolisib": ("DRUG", "PI3K/mTOR (dual)", "Dual PI3K/mTOR inhibitor; also known as NVP-BEZ235/BEZ235."),
    "Doxorubicin": ("DRUG", "Topoisomerase II / DNA intercalation", "Anthracycline chemotherapeutic; ABCB1 transport substrate; resistance driver in the ABCB1-overexpressing sublines used here."),
    "Vanadate": ("INHIBITOR", "ABCB1 ATPase (ATP-hydrolysis site)", "Orthovanadate; classic ATP-site inhibitor of ABCB1 ATPase activity, used as a negative-control probe."),
    "Verapamil": ("INHIBITOR", "ABCB1 (P-glycoprotein)", "Calcium-channel blocker; well-characterized ABCB1 substrate/positive-control stimulator of ABCB1 ATPase activity."),
    "Sildenafil": ("INHIBITOR", "ABCB1 (P-glycoprotein)", "PDE5 inhibitor with reported ABCB1-modulating activity; comparator probe alongside BEZ235."),
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
        "papers", paper_id=PAPER, pmid="32061787", pmcid="PMC10845210",
        doi="10.1016/j.bbagen.2020.129556",
        title="A Dual PI3 Kinase/mTOR Inhibitor BEZ235 reverses doxorubicin resistance in ABCB1 overexpressing "
              "ovarian and pancreatic cancer cell lines",
        year=2020, journal="Biochimica et Biophysica Acta - General Subjects",
        citation="Durrant DE, et al. Biochim Biophys Acta Gen Subj. 2020;1864(11):129556.",
        notes="PMCID exists (PMC10845210) but no local PMC HTML/paper file is available; workbook-only build. "
              "No in vivo/tumour model in this paper -- all data are in vitro (2D cell culture) or cell-free "
              "(isolated ABCB1 membrane ATPase assay). Two parental-vs-ABCB1-overexpressing (doxorubicin-"
              "resistant) cell-line pairs used throughout: MiaPaCa2/Mia-B1 (pancreatic) and A2780/A2780-dx "
              "(ovarian); Mia-dx is a third, ABCB1-independent doxorubicin-resistant pancreatic subline used as "
              "a specificity control.",
    )

    artifact_specs: list[tuple[str, Path, str, str, str | None]] = [
        ("artifact_PMID32061787_workbook", RAW_WORKBOOK, "WORKBOOK", "Supplied curated per-figure digitization workbook, preserved unchanged.", None),
        ("artifact_PMID32061787_qsp_workbook", RAW_QSP_WORKBOOK, "WORKBOOK", "Supplied companion QSP-recommendation workbook (Model map, per-figure digitized sheets, Read me), preserved unchanged. Read me sheet is authoritative for classifying each figure's data quality.", None),
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
            raise ValueError(f"Unsupported Dactolisib ovarian method/quality: {method}/{quality}")
        source_artifact_id = f"artifact_PMID32061787_{row['source_key']}"
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
            "extraction_runs", extraction_run_id=stable_id("extraction", observation_id, "dactolisib_ovarian_v1"),
            source_artifact_id=source_artifact_id, observation_id=observation_id, method=method,
            software_or_script="prepare_dactolisib_ovarian.py",
            roi_information=None, background_method=None, raw_intensity=None,
            background_corrected_intensity=None, total_protein_intensity=None, ratio=None,
            normalization_method=_optional(row["normalization"]),
            operator_or_process="supplied workbook + companion QSP workbook normalized into registry-v1 CSVs",
            timestamp=metadata["extraction_date"],
            notes="See datasets/extracted/dactolisib_ovarian/extraction_metadata.json.",
        )

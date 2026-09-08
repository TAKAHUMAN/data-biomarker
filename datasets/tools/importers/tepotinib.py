"""Import PMID 33818908 Tepotinib observations without mixing in source-model estimates."""

from __future__ import annotations

import csv
from pathlib import Path

from registry_common import DATASETS, Registry, clean_number, relative, sha256, stable_id

PAPER = "paper_PMID33818908"
RAW_PDF = DATASETS / "raw" / "papers" / "PMID_33818908_PMC8129711.pdf"
RAW_FIG2 = DATASETS / "raw" / "images" / "PMID_33818908_fig2.jpg"
DATA = DATASETS / "extracted" / "tepotinib" / "observations.csv"
FIG2A = DATASETS / "extracted" / "tepotinib" / "figure_2a_digitized.csv"
FIG2D = DATASETS / "extracted" / "tepotinib" / "figure_2d_digitized.csv"
FIG4 = DATASETS / "extracted" / "tepotinib" / "figure_4_digitized.csv"
ARTIFACT_PDF = "artifact_PMID33818908_paper"
ARTIFACT_FIG2 = "artifact_PMID33818908_fig2"


def _rows() -> list[dict[str, str]]:
    with DATA.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def _read(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def _artifact(source_key: str) -> str:
    return ARTIFACT_FIG2 if source_key == "fig2_image" else ARTIFACT_PDF


def _bool(value: str | None) -> bool:
    return str(value).strip().lower() == "true"


def _context(registry: Registry, row: dict[str, str]) -> str:
    context_id = stable_id("context", PAPER, row["context_key"])
    if not registry.has("contexts", "context_id", context_id):
        registry.add(
            "contexts", context_id=context_id, species=row["species"], cell_line=row["cell_line"],
            cell_type=None, tissue=row["tissue"], disease=row["disease"],
            culture_context="xenograft-bearing mouse", notes="Source context as reported in PMID 33818908.",
        )
        for alteration in filter(None, row["alterations"].split(";")):
            gene, alteration_type, detail = alteration.split(":", 2)
            registry.add(
                "context_alterations",
                context_alteration_id=stable_id("context_alteration", context_id, gene, alteration_type, detail),
                context_id=context_id, gene=gene, alteration_type=alteration_type, alteration=detail,
                zygosity_or_copy_context=None, source="PMID33818908 Table 1", notes=None,
            )
    return context_id


def _perturbation(registry: Registry, name: str) -> str:
    perturbation_id = stable_id("perturbation", name)
    if not registry.has("perturbations", "perturbation_id", perturbation_id):
        registry.add(
            "perturbations", perturbation_id=perturbation_id, name=name,
            type="CONTROL" if name == "Vehicle" else "DRUG", target_if_reported=None if name == "Vehicle" else "MET",
            source_name=name, notes=None,
        )
    return perturbation_id


def _condition(registry: Registry, row: dict[str, str], context_id: str) -> str:
    condition_id = stable_id("condition", PAPER, row["record_id"])
    if not registry.has("conditions", "condition_id", condition_id):
        registry.add("conditions", condition_id=condition_id, context_id=context_id, condition_label=row["condition_label"], notes=None)
        registry.add(
            "condition_steps", condition_step_id=stable_id("condition_step", condition_id), condition_id=condition_id,
            perturbation_id=_perturbation(registry, row["drug"]), dose_value=clean_number(row["dose_value"]),
            dose_unit=row["dose_unit"], start_time=clean_number(row["start_time"]), end_time=clean_number(row["end_time"]),
            time_unit=row["time_unit"], sequence_index=1, notes="Oral regimen frequency is retained in condition_label.",
        )
    return condition_id


def _simple_context(registry: Registry, key: str, *, species: str, cell_line: str, tissue: str, disease: str, notes: str, alterations: list[tuple[str, str, str]]) -> str:
    context_id = stable_id("context", PAPER, key)
    if registry.has("contexts", "context_id", context_id):
        return context_id
    registry.add("contexts", context_id=context_id, species=species, cell_line=cell_line, cell_type=None, tissue=tissue, disease=disease, culture_context="xenograft-bearing mouse" if key == "KP4" else "first-in-human paired tumor biopsy", notes=notes)
    for gene, alteration_type, alteration in alterations:
        registry.add("context_alterations", context_alteration_id=stable_id("context_alteration", context_id, gene, alteration_type, alteration), context_id=context_id, gene=gene, alteration_type=alteration_type, alteration=alteration, zygosity_or_copy_context=None, source="PMID33818908", notes=None)
    return context_id


def _add_digitized(registry: Registry, *, record_id: str, context_id: str, drug: str, dose: float, time: float | None, assay_id: str, artifact_id: str, figure: str, panel: str, value: float, value_unit: str, observable: str, raw_label: str, uncertainty_type: str | None = None, uncertainty_value: float | None = None, condition_note: str | None = None, observation_note: str | None = None) -> None:
    condition_id = stable_id("condition", PAPER, record_id)
    if not registry.has("conditions", "condition_id", condition_id):
        registry.add("conditions", condition_id=condition_id, context_id=context_id, condition_label=f"{drug} {dose:g} mg/kg" if value_unit == "mm3" else f"Tepotinib {dose:g} mg/day; AUC24h recorded with observation", notes=condition_note)
        registry.add("condition_steps", condition_step_id=stable_id("condition_step", condition_id), condition_id=condition_id, perturbation_id=_perturbation(registry, drug), dose_value=dose, dose_unit="mg/kg" if value_unit == "mm3" else "mg/day", start_time=0.0 if time is not None else None, end_time=time, time_unit="d" if time is not None else None, sequence_index=1, notes=condition_note)
    observation_id = stable_id("obs", PAPER, record_id)
    registry.add("observations", observation_id=observation_id, paper_id=PAPER, context_id=context_id, condition_id=condition_id, assay_id=assay_id, observable=observable, observable_raw_label=raw_label, value=value, value_unit=value_unit, time_value=time, time_unit="d" if time is not None else None, statistic="mean" if value_unit == "mm3" else "single plotted clinical biopsy value", uncertainty_type=uncertainty_type, uncertainty_value=uncertainty_value, replicate_count=None, normalization="none" if value_unit == "mm3" else "pMET Y1234-1235 / total MET / total protein / paired baseline", normalization_reference=None if value_unit == "mm3" else "paired pretreatment biopsy", source_artifact_id=artifact_id, figure=figure, panel=panel, table=None, lane=None, extraction_method="PLOT_DIGITIZED", quality_class="SEMI_QUANTITATIVE", is_censored=False, censoring_limit=None, notes=observation_note)
    registry.add("extraction_runs", extraction_run_id=stable_id("extraction", observation_id), source_artifact_id=artifact_id, observation_id=observation_id, method="PLOT_DIGITIZED", software_or_script="manual coordinate reading from vector PDF", roi_information=None, background_method=None, raw_intensity=None, background_corrected_intensity=None, total_protein_intensity=None, ratio=None, normalization_method="none" if value_unit == "mm3" else "published paired-biopsy normalization", operator_or_process="Codex extraction", timestamp="2026-09-03", notes="Digitized plotted marker; precision is limited by the source figure.")


def _collect_additional(registry: Registry) -> None:
    kp4 = _simple_context(registry, "KP4", species="human", cell_line="KP-4", tissue="pancreas", disease="pancreatic ductal carcinoma", notes="KP-4 xenograft; paper reports HGF/MET autocrine pathway activation.", alterations=[("MET", "OTHER", "HGF/MET autocrine")])
    f2a_assay = stable_id("assay", PAPER, "Figure 2", "a", "KP-4 tumor volume")
    f2d_assay = stable_id("assay", PAPER, "Figure 2", "d", "KP-4 metabolite tumor volume")
    registry.add("assays", assay_id=f2a_assay, paper_id=PAPER, assay_type="caliper tumor volume", assay_name="KP-4 xenograft efficacy", sample_type="xenograft tumor", measurement_platform="observed plotted mean", figure="Figure 2", panel="a", reported_time=None, reported_time_unit="d", replicate_count=10, notes="Two independent experiments; error bars not separated due to overlap.")
    registry.add("assays", assay_id=f2d_assay, paper_id=PAPER, assay_type="caliper tumor volume", assay_name="KP-4 metabolite efficacy", sample_type="xenograft tumor", measurement_platform="observed plotted mean ± SEM", figure="Figure 2", panel="d", reported_time=None, reported_time_unit="d", replicate_count=None, notes="Visible SEM bars digitized approximately.")
    for row in _read(FIG2A):
        drug = "Vehicle" if float(row["dose_mg_per_kg"]) == 0 else "Tepotinib"
        _add_digitized(registry, record_id=row["record_id"], context_id=kp4, drug=drug, dose=float(row["dose_mg_per_kg"]), time=float(row["time_day"]), assay_id=f2a_assay, artifact_id=ARTIFACT_FIG2, figure="Figure 2", panel="a", value=float(row["mean_tumor_volume_mm3"]), value_unit="mm3", observable="tumor_volume", raw_label="Tumor Volume (mm3)", condition_note=f"{row['experiment']} retained as a distinct study series.", observation_note=f"{row['experiment']} observed mean digitized from Figure 2a; error bars were not separately recoverable.")
    for row in _read(FIG2D):
        _add_digitized(registry, record_id=row["record_id"], context_id=kp4, drug=row["drug"], dose=float(row["dose_mg_per_kg"]), time=float(row["time_day"]), assay_id=f2d_assay, artifact_id=ARTIFACT_FIG2, figure="Figure 2", panel="d", value=float(row["mean_tumor_volume_mm3"]), value_unit="mm3", observable="tumor_volume", raw_label="Tumor volume (mean ± SEM)", uncertainty_type="SEM (plot digitized)", uncertainty_value=float(row["sem_tumor_volume_mm3"]), condition_note="QD oral dosing.", observation_note="Observed mean and approximate visible SEM digitized from Figure 2d.")
    clinical = _simple_context(registry, "FIH_solid_tumors", species="human", cell_line="not reported", tissue="tumor biopsy", disease="advanced solid tumors", notes="Individual patient tumor type is retained on the condition; on-treatment biopsy time was not reported in this paper.", alterations=[])
    f4_assay = stable_id("assay", PAPER, "Figure 4", "clinical_pMET")
    registry.add("assays", assay_id=f4_assay, paper_id=PAPER, assay_type="Luminex", assay_name="paired biopsy phospho-MET", sample_type="tumor biopsy", measurement_platform="pMET Y1234-1235 multiplex assay", figure="Figure 4", panel=None, reported_time=None, reported_time_unit=None, replicate_count=None, notes="13 evaluable paired biopsies reported; individual time and patient identifiers are not reported.")
    for row in _read(FIG4):
        _add_digitized(registry, record_id=row["record_id"], context_id=clinical, drug="Tepotinib", dose=float(row["dose_mg_per_day"]), time=None, assay_id=f4_assay, artifact_id=ARTIFACT_PDF, figure="Figure 4", panel=None, value=float(row["pMET_relative_to_baseline_percent"]), value_unit="percent of baseline", observable="pMET_Y1234_1235_relative_to_baseline", raw_label="Phospho-MET relative to baseline (%)", condition_note=f"Tumor type: {row['tumor_type']}; AUC24h: {row['auc24h_ng_h_per_ml']} ng*h/mL.", observation_note="Patient-level dose label, tumor type, AUC24h, and pMET marker digitized from Figure 4; no per-marker uncertainty or biopsy time reported.")


def collect(registry: Registry) -> None:
    registry.add(
        "papers", paper_id=PAPER, pmid="33818908", pmcid="PMC8129711", doi="10.1002/psp4.12602",
        title="Translational pharmacokinetic-pharmacodynamic modeling of preclinical and clinical data of the oral MET inhibitor tepotinib to determine the recommended phase II dose",
        year=2021, journal="CPT: Pharmacometrics & Systems Pharmacology",
        citation="Xiong W, et al. CPT Pharmacometrics Syst Pharmacol. 2021;10:428-440.",
        notes="Registry observations are only digitized observed Figure 2b/c tumor-volume means; published model estimates remain under datasets/extracted/tepotinib.",
    )
    registry.add("source_artifacts", source_artifact_id=ARTIFACT_PDF, paper_id=PAPER, artifact_type="PAPER", path=relative(RAW_PDF), original_filename=RAW_PDF.name, sha256=sha256(RAW_PDF), figure=None, panel=None, supplement_identifier=None, source_description="Open-access full text, PMCID PMC8129711.")
    registry.add("source_artifacts", source_artifact_id=ARTIFACT_FIG2, paper_id=PAPER, artifact_type="IMAGE", path=relative(RAW_FIG2), original_filename=RAW_FIG2.name, sha256=sha256(RAW_FIG2), figure="Figure 2", panel=None, supplement_identifier=None, source_description="PMC Figure 2 source image used for observed-point digitization.")
    assays: set[str] = set()
    for row in _rows():
        context_id = _context(registry, row)
        condition_id = _condition(registry, row, context_id)
        assay_id = stable_id("assay", PAPER, row["figure"], row["panel"], row["assay_type"], row["cell_line"])
        if assay_id not in assays:
            registry.add("assays", assay_id=assay_id, paper_id=PAPER, assay_type=row["assay_type"], assay_name=row["assay_name"], sample_type="xenograft tumor", measurement_platform=row["measurement_platform"], figure=row["figure"], panel=row["panel"], reported_time=None, reported_time_unit="d", replicate_count=None, notes="Figure shows observed means and error bars; individual values are unavailable.")
            assays.add(assay_id)
        artifact_id = _artifact(row["source_key"])
        observation_id = stable_id("obs", PAPER, row["record_id"])
        registry.add(
            "observations", observation_id=observation_id, paper_id=PAPER, context_id=context_id, condition_id=condition_id, assay_id=assay_id,
            observable=row["observable"], observable_raw_label=row["observable_raw_label"], value=clean_number(row["value"]), value_unit=row["value_unit"],
            time_value=clean_number(row["time_value"]), time_unit="d", statistic=row["statistic"], uncertainty_type=row["uncertainty_type"] or None,
            uncertainty_value=clean_number(row["uncertainty_value"]), replicate_count=int(row["replicate_count"]) if row["replicate_count"] else None,
            normalization=row["normalization"], normalization_reference=row["normalization_reference"] or None, source_artifact_id=artifact_id,
            figure=row["figure"], panel=row["panel"], table=None, lane=None, extraction_method=row["extraction_method"], quality_class=row["quality_class"],
            is_censored=_bool(row["is_censored"]), censoring_limit=clean_number(row["censoring_limit"]), notes=row["notes"],
        )
        registry.add(
            "extraction_runs", extraction_run_id=stable_id("extraction", observation_id), source_artifact_id=artifact_id, observation_id=observation_id,
            method="PLOT_DIGITIZED", software_or_script="manual coordinate reading from vector PDF / Figure 2 source image", roi_information=None,
            background_method=None, raw_intensity=None, background_corrected_intensity=None, total_protein_intensity=None, ratio=None,
            normalization_method="none; absolute tumor volume", operator_or_process="Codex extraction", timestamp="2026-09-03", notes="Mean marker digitized; visible error bars deliberately left unquantified.",
        )
    _collect_additional(registry)

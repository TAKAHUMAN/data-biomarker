"""Import PMID 32315352 observations and densitometry with full extraction provenance."""

from __future__ import annotations

import csv
from pathlib import Path

from registry_common import DATASETS, Registry, clean_number, relative, sha256, stable_id

PAPER = "paper_PMID32315352"
DRUG = "Pemigatinib"
DATA = DATASETS / "extracted" / "pemigatinib"
RAW = DATASETS / "raw"
ARTIFACT_PAPER = "artifact_PMID32315352_paper"
ARTIFACT_S1 = "artifact_PMID32315352_s1_raw_images"
ARTIFACT_S3 = "artifact_PMID32315352_s3_fig"


def _csv(name: str) -> list[dict[str, str]]:
    with (DATA / name).open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def _ensure_context(registry: Registry, label: str, *, species: str = "human", disease: str | None = None, culture_context: str | None = None, alteration: str | None = None) -> str:
    context_id = stable_id("context", label, species, culture_context)
    if not registry.has("contexts", "context_id", context_id):
        registry.add("contexts", context_id=context_id, species=species, cell_line=label, cell_type=None, tissue=None, disease=disease, culture_context=culture_context, notes=None)
        for gene, kind, value in _alteration_rows(label, alteration):
            registry.add("context_alterations", context_alteration_id=stable_id("context_alteration", context_id, gene, kind, value), context_id=context_id, gene=gene, alteration_type=kind, alteration=value, zygosity_or_copy_context=None, source="PMID:32315352", notes=None)
    return context_id


def _alteration_rows(label: str, explicit: str | None) -> list[tuple[str, str, str]]:
    text = (explicit or "").lower()
    if "n310r/n549k" in text:
        return [("FGFR2", "MUTATION", "N310R"), ("FGFR2", "MUTATION", "N549K")]
    fusion = {
        "FGFR1OP2-FGFR1": ("FGFR1", "FUSION", "FGFR1OP2-FGFR1"), "FGFR3-TACC3": ("FGFR3", "FUSION", "FGFR3-TACC3"),
        "FGFR2-CCDC6": ("FGFR2", "FUSION", "FGFR2-CCDC6"), "FGFR2-AHCYL": ("FGFR2", "FUSION", "FGFR2-AHCYL"),
        "FGFR2-TRA2B": ("FGFR2", "FUSION", "FGFR2-TRA2B"), "FGFR1-ZFN298": ("FGFR1", "FUSION", "FGFR1-ZFN298"),
        "FGFR1-TEL": ("FGFR1", "FUSION", "FGFR1-TEL"), "FGFR3-TEL": ("FGFR3", "FUSION", "FGFR3-TEL"),
    }
    for phrase, result in fusion.items():
        if phrase.lower() in text or phrase.lower() in label.lower():
            return [result]
    if "amplification" in text or label in {"H1581", "DMS-114", "KATO III", "KATO III xenograft", "KATO III tumor-bearing mouse"}:
        isoform = "FGFR1" if label in {"H1581", "DMS-114"} else "FGFR2"
        return [(isoform, "AMPLIFICATION", f"{isoform} amplification")]
    if "translocation" in text or label in {"KMS-11", "OPM-2"}:
        return [("FGFR3", "TRANSLOCATION", "IgH-FGFR3 translocation")]
    return []


def _condition(registry: Registry, context_id: str, dose: float | None, dose_unit: str | None, duration: float | None, time_unit: str | None, *, label: str, notes: str | None = None) -> str:
    condition_id = stable_id("condition", PAPER, context_id, label, dose, dose_unit, duration, time_unit)
    if not registry.has("conditions", "condition_id", condition_id):
        registry.add("conditions", condition_id=condition_id, context_id=context_id, condition_label=label, notes=notes)
        registry.add("condition_steps", condition_step_id=stable_id("condition_step", condition_id), condition_id=condition_id, perturbation_id=stable_id("perturbation", DRUG), dose_value=dose, dose_unit=dose_unit, start_time=0.0 if duration is not None else None, end_time=duration, time_unit=time_unit, sequence_index=1, notes=notes)
    return condition_id


def _assay(registry: Registry, *, assay_type: str, name: str, figure: str | None, panel: str | None, time: float | None, time_unit: str | None, replicate_count: int | None, notes: str | None = None) -> str:
    assay_id = stable_id("assay", PAPER, assay_type, name, figure, panel, time, time_unit)
    if not registry.has("assays", "assay_id", assay_id):
        registry.add("assays", assay_id=assay_id, paper_id=PAPER, assay_type=assay_type, assay_name=name, sample_type=None, measurement_platform=assay_type, figure=figure, panel=panel, reported_time=time, reported_time_unit=time_unit, replicate_count=replicate_count, notes=notes)
    return assay_id


def _observation(registry: Registry, **row: object) -> None:
    registry.add("observations", **row)


def collect(registry: Registry) -> None:
    paper_path = RAW / "papers" / "PMID_32315352_printable.pdf"
    s1_path = RAW / "supplementary" / "PMID_32315352_s002_S1_Raw_Images.docx"
    s3_path = RAW / "supplementary" / "PMID_32315352_s008_S3_Fig.docx"
    registry.add("papers", paper_id=PAPER, pmid="32315352", pmcid="PMC7313537", doi="10.1371/journal.pone.0231877", title="INCB054828 (pemigatinib), a potent and selective inhibitor of fibroblast growth factor receptors 1, 2, and 3, displays activity against genetically defined tumor models.", year=2020, journal="PLOS ONE", citation=None, notes=None)
    for artifact_id, path, kind, supplement, description in ((ARTIFACT_PAPER, paper_path, "PAPER", None, "Printable full paper."), (ARTIFACT_S1, s1_path, "SUPPLEMENT", "S1 Raw Images", "Original raw-blot supplement."), (ARTIFACT_S3, s3_path, "SUPPLEMENT", "S3 Fig", "Original target-engagement supplement.")):
        registry.add("source_artifacts", source_artifact_id=artifact_id, paper_id=PAPER, artifact_type=kind, path=relative(path), original_filename=path.name, sha256=sha256(path), figure=None, panel=None, supplement_identifier=supplement, source_description=description)
    registry.add("perturbations", perturbation_id=stable_id("perturbation", DRUG), name=DRUG, type="DRUG", target_if_reported="FGFR1/FGFR2/FGFR3", source_name="INCB054828", notes=None)

    # Main paper summaries and Table 1.
    for source in _csv("observations.csv"):
        label = source["cell_line"]
        genotype = source["genotype_mutation"]
        context_id = _ensure_context(registry, label, disease=None, culture_context=source["stimulus_ligand_conditions"] or None, alteration=genotype)
        duration = clean_number(source["exposure_time"].replace(" h", "")) if source["exposure_time"].endswith(" h") else None
        condition_id = _condition(registry, context_id, None, "nM", duration, "h" if duration is not None else None, label=f"Pemigatinib {source['drug_concentration']}", notes=source["stimulus_ligand_conditions"] or None)
        replicate = clean_number(source["replicate_count"])
        assay_id = _assay(registry, assay_type=source["assay_type"], name=source["measured_observable"], figure=source["figure_table_panel"], panel=None, time=duration, time_unit="h" if duration is not None else None, replicate_count=int(replicate) if replicate is not None else None)
        method = "DIRECT_SOURCE" if "directly tabulated" in source["value_provenance"].lower() else "TEXT_DERIVED"
        uncertainty = source["error_uncertainty"] or None
        uncertainty_value = None
        if uncertainty and uncertainty.startswith("SD "):
            uncertainty_value = clean_number(uncertainty.replace("SD", "").replace("nM", ""))
        _observation(registry, observation_id=f"obs_PMID32315352_{source['record_id']}", paper_id=PAPER, context_id=context_id, condition_id=condition_id, assay_id=assay_id, observable=source["measured_observable"], observable_raw_label=source["measured_observable"], value=clean_number(source["experimental_value"]), value_unit=source["value_unit"] or None, time_value=duration, time_unit="h" if duration is not None else None, statistic="IC50" if "IC50" in source["measured_observable"] else "GI50" if source["measured_observable"] == "GI50" else "reported summary", uncertainty_type="SD" if uncertainty_value is not None else None, uncertainty_value=uncertainty_value, replicate_count=int(replicate) if replicate is not None else None, normalization=source["normalization"] or None, normalization_reference=None, source_artifact_id=ARTIFACT_S3 if source["figure_table_panel"].startswith("S3") else ARTIFACT_PAPER, figure=source["figure_table_panel"].split()[0], panel=source["figure_table_panel"], table="Table 1" if source["figure_table_panel"] == "Table 1" else None, lane=None, extraction_method=method, quality_class="QUANTITATIVE", is_censored=False, censoring_limit=None, notes=source["notes"] or None)

    # Fig. 2A single-blot densitometry; raw values and ROI-specific details remain in extracted CSV/JSON.
    for source in _csv("kg1a_2h_blot_densitometry.csv"):
        context_id = _ensure_context(registry, source["cell_line"], disease="acute myeloid leukemia", alteration=source["alteration"])
        dose, duration = clean_number(source["pemigatinib_nM"]), clean_number(source["exposure_hours"])
        condition_id = _condition(registry, context_id, dose, "nM", duration, "h", label=f"Pemigatinib {source['pemigatinib_nM']} nM for 2 h")
        assay_id = _assay(registry, assay_type="Western blot", name="KG1a phosphoprotein blot", figure="Fig. 2A", panel="A", time=duration, time_unit="h", replicate_count=None, notes="Single-blot densitometry.")
        value = clean_number(source["vehicle_normalized_phospho_to_total"])
        _observation(registry, observation_id=f"obs_PMID32315352_{source['record_id']}", paper_id=PAPER, context_id=context_id, condition_id=condition_id, assay_id=assay_id, observable=source["phosphoprotein"], observable_raw_label=source["phosphoprotein"], value=value, value_unit="vehicle-normalized phospho/total ratio", time_value=duration, time_unit="h", statistic="single blot lane", uncertainty_type=None, uncertainty_value=None, replicate_count=None, normalization="background-corrected phospho / matched total", normalization_reference="0 nM vehicle ratio", source_artifact_id=ARTIFACT_PAPER, figure="Fig. 2A", panel="A", table=None, lane=None, extraction_method="BLOT_DENSITOMETRY", quality_class="SEMI_QUANTITATIVE", is_censored=bool(clean_number(source["signal_background_corrected"]) is not None and clean_number(source["signal_background_corrected"]) <= 0), censoring_limit=0.0 if value == 0.0 else None, notes=source["quantification_status"])
        registry.add("extraction_runs", extraction_run_id=stable_id("extraction", source["record_id"]), source_artifact_id=ARTIFACT_PAPER, observation_id=f"obs_PMID32315352_{source['record_id']}", method="BLOT_DENSITOMETRY", software_or_script="manual fixed-ROI integrated inverse grayscale", roi_information="Detailed ROI procedure: datasets/extracted/pemigatinib/kg1a_2h_blot_densitometry_metadata.json", background_method="mean inverted grayscale of adjacent vertical regions", raw_intensity=clean_number(source["signal_raw_integrated_inverse_gray_px"]), background_corrected_intensity=clean_number(source["signal_background_corrected"]), total_protein_intensity=clean_number(source["total_background_corrected"]), ratio=clean_number(source["phospho_to_total"]), normalization_method="divide phospho/total ratio by 0 nM ratio", operator_or_process="documented local extraction process", timestamp=None, notes=source["quantification_status"])

    for source in _csv("figure_2b.csv"):
        label, alteration = source["cell_line"], source["alteration"]
        context_id = _ensure_context(registry, label, alteration=alteration)
        duration, dose = clean_number(source["treatment_duration"].replace(" h", "")) if source["treatment_duration"].endswith(" h") else None, clean_number(source["dose"])
        condition_id = _condition(registry, context_id, dose, source["dose_units"], duration, "h" if duration else None, label=f"Pemigatinib {source['dose']} {source['dose_units']}", notes=source["notes"])
        assay_id = _assay(registry, assay_type=source["assay_type"], name=source["measured_observable"], figure=source["figure_panel"], panel=source["figure_panel"], time=duration, time_unit="h" if duration else None, replicate_count=None)
        _observation(registry, observation_id=stable_id("obs", PAPER, source["figure_panel"], label, source["measured_observable"], source["dose"]), paper_id=PAPER, context_id=context_id, condition_id=condition_id, assay_id=assay_id, observable=source["measured_observable"], observable_raw_label=source["measured_observable"], value=clean_number(source["quantitative_value"]), value_unit=None, time_value=duration, time_unit="h" if duration else None, statistic=None, uncertainty_type=None, uncertainty_value=None, replicate_count=None, normalization=None, normalization_reference=source["corresponding_total"] or None, source_artifact_id=ARTIFACT_S1 if source["figure_panel"] == "Fig.2B" else ARTIFACT_PAPER, figure=source["figure_panel"], panel=source["figure_panel"], table=None, lane=None, extraction_method="DIRECT_SOURCE", quality_class="QUALITATIVE_VALIDATION", is_censored=False, censoring_limit=None, notes=source["notes"])

    _collect_figure3(registry)
    _collect_figure4(registry)
    for observable, symbol, mapping_type in (("pFGFR_Y653_Y654", "model_pFGFR", "APPROXIMATE"), ("pERK1_2_T202_Y204", "ERK_double_phosphorylated", "DIRECT"), ("pAKT", "AKT_active_fraction", "DIRECT"), ("pSTAT5_Y694", "STAT5_cyt_phosphorylated + 2*STAT5_cyt_dimer + 2*STAT5_nuclear_dimer", "COMPOSITE")):
        registry.add("model_mappings", mapping_id=stable_id("mapping", observable, "pemigatinib_fgfr_aberrant_model_v0_1"), observable=observable, model_id="pemigatinib_fgfr_aberrant_model_v0_1", model_symbol_or_expression=symbol, mapping_type=mapping_type, mapping_version="v0_1", notes="Model-specific mapping kept separate from source observations.")


def _collect_figure3(registry: Registry) -> None:
    for source in _csv("figure_3.csv"):
        label, context = source["system"], source["fgfr_context"]
        species = "mouse" if "mouse" in label.lower() else "human"
        context_id = _ensure_context(registry, label, species=species, culture_context="in vivo", alteration=context)
        time = clean_number(source["time"].replace(" h", "")) if source["time"].endswith(" h") else None
        dose = clean_number(source["dose"])
        condition_id = _condition(registry, context_id, dose, source["dose_units"], time, "h" if time else None, label=f"Pemigatinib {source['dose']} {source['dose_units']}", notes=source["notes"])
        assay_id = _assay(registry, assay_type="PK/PD" if "plasma" in source["measured_observable"] or "tumor" in source["measured_observable"] else "Serum chemistry", name=source["measured_observable"], figure=source["figure_panel"], panel=source["figure_panel"], time=time, time_unit="h" if time else None, replicate_count=int(clean_number(source["replicate_count"])) if clean_number(source["replicate_count"]) else None)
        method = "PLOT_DIGITIZED" if "digitized" in source["value_provenance"] else "TEXT_DERIVED"
        _observation(registry, observation_id=stable_id("obs", PAPER, source["figure_panel"], label, source["dose"], source["time"], source["measured_observable"]), paper_id=PAPER, context_id=context_id, condition_id=condition_id, assay_id=assay_id, observable=source["measured_observable"], observable_raw_label=source["measured_observable"], value=clean_number(source["experimental_value"]), value_unit=source["value_unit"], time_value=time, time_unit="h" if time else None, statistic="IC50" if "IC50" in source["measured_observable"] else "reported point", uncertainty_type=None, uncertainty_value=None, replicate_count=int(clean_number(source["replicate_count"])) if clean_number(source["replicate_count"]) else None, normalization=None, normalization_reference=None, source_artifact_id=ARTIFACT_PAPER, figure=source["figure_panel"], panel=source["figure_panel"], table=None, lane=None, extraction_method=method, quality_class="NOT_MODEL_READY", is_censored="lower plotting limit" in source["notes"], censoring_limit=1.0 if "lower plotting limit" in source["notes"] else None, notes=source["notes"])


def _collect_figure4(registry: Registry) -> None:
    for source in _csv("figure_4.csv"):
        label = source["model"]
        species = source["species"]
        context_id = _ensure_context(registry, label, species=species, culture_context="in vivo", alteration=source["fgfr_alteration"])
        duration = clean_number(source["treatment_duration"].replace(" days", ""))
        dose = clean_number(source["dose"])
        condition_id = _condition(registry, context_id, dose, source["dose_units"], duration, "days", label=f"Pemigatinib {source['dose']} {source['dose_units']} {source['schedule']}", notes=source["notes"])
        assay_id = _assay(registry, assay_type="Tumor volume", name=source["endpoint"], figure=source["figure_panel"], panel=source["figure_panel"], time=duration, time_unit="days", replicate_count=int(clean_number(source["group_size"])) if clean_number(source["group_size"]) else None, notes=source["schedule"])
        _observation(registry, observation_id=stable_id("obs", PAPER, source["figure_panel"], label, source["dose"]), paper_id=PAPER, context_id=context_id, condition_id=condition_id, assay_id=assay_id, observable="tumor_volume", observable_raw_label=source["endpoint"], value=None, value_unit=None, time_value=duration, time_unit="days", statistic="mean tumor volume plus SEM", uncertainty_type="SEM", uncertainty_value=None, replicate_count=int(clean_number(source["group_size"])) if clean_number(source["group_size"]) else None, normalization=None, normalization_reference="vehicle", source_artifact_id=ARTIFACT_PAPER, figure=source["figure_panel"], panel=source["figure_panel"], table=None, lane=None, extraction_method="TEXT_DERIVED", quality_class="QUALITATIVE_VALIDATION", is_censored=False, censoring_limit=None, notes=source["notes"])


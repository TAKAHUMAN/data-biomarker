"""Import the immutable Foretinib workbook without modifying source values."""

from __future__ import annotations

import posixpath
import re
import xml.etree.ElementTree as ET
from pathlib import Path
from zipfile import ZipFile

from registry_common import DATASETS, Registry, clean_number, relative, sha256, stable_id

PAPER = "paper_foretinib_flt3_itd_workbook"
ARTIFACT = "artifact_foretinib_flt3_itd_workbook"
RAW = DATASETS / "raw" / "workbooks" / "foretinib_experimental_data.xlsx"
SHEETS = {"mv4_11": "WB - MV4-11 (Quantitative)", "molm13": "WB - MOLM13 (Quantitative)", "baf3_flt3_itd": "WB - BaF3 (Quantitative)"}
CONTEXTS = {"mv4_11": ("MV4-11", "human", "acute myeloid leukemia"), "molm13": ("MOLM13", "human", "acute myeloid leukemia"), "baf3_flt3_itd": ("Ba/F3 FLT3-ITD", "mouse", "engineered hematopoietic cell line")}
ROWS = {"pFLT3": 6, "pSTAT5": 8, "pAKT": 10, "pERK": 12}


def _cells(path: Path) -> dict[str, dict[str, object]]:
    main = "http://schemas.openxmlformats.org/spreadsheetml/2006/main"
    rel = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
    ns = {"m": main, "r": rel}
    with ZipFile(path) as package:
        names = set(package.namelist())
        shared = []
        if "xl/sharedStrings.xml" in names:
            root = ET.fromstring(package.read("xl/sharedStrings.xml"))
            shared = ["".join(node.text or "" for node in item.iter(f"{{{main}}}t")) for item in root.findall("m:si", ns)]
        workbook = ET.fromstring(package.read("xl/workbook.xml"))
        rels = ET.fromstring(package.read("xl/_rels/workbook.xml.rels"))
        targets = {node.attrib["Id"]: node.attrib["Target"] for node in rels}
        result: dict[str, dict[str, object]] = {}
        for sheet in workbook.find("m:sheets", ns) or []:
            target = targets[sheet.attrib[f"{{{rel}}}id"]].lstrip("/")
            if not target.startswith("xl/"):
                target = posixpath.normpath("xl/" + target)
            root = ET.fromstring(package.read(target))
            cells: dict[str, object] = {}
            for cell in root.findall(".//m:sheetData/m:row/m:c", ns):
                ref, kind = cell.attrib["r"], cell.attrib.get("t")
                raw = cell.findtext("m:v", namespaces=ns)
                inline = cell.find("m:is", ns)
                if kind == "s" and raw is not None:
                    value: object = shared[int(raw)]
                elif kind == "inlineStr" and inline is not None:
                    value = "".join(node.text or "" for node in inline.iter(f"{{{main}}}t"))
                elif raw is not None:
                    try:
                        value = float(raw)
                    except ValueError:
                        value = raw
                else:
                    continue
                cells[ref] = value
            result[sheet.attrib["name"]] = cells
    return result


def _dose(value: object) -> float:
    match = re.fullmatch(r"\s*([0-9.]+)\s*nmol/L\s*", str(value))
    if not match:
        raise ValueError(f"Cannot parse Foretinib dose {value!r}")
    return float(match.group(1))


def _condition(registry: Registry, context_id: str, name: str, dose: float | None, hours: float, *, second_step: str | None = None) -> str:
    condition_id = stable_id("condition", PAPER, context_id, name, dose, hours, second_step)
    if registry.has("conditions", "condition_id", condition_id):
        return condition_id
    registry.add("conditions", condition_id=condition_id, context_id=context_id, condition_label=f"{name} {dose if dose is not None else ''} nM for {hours:g} h".strip(), notes=None)
    perturbation_id = stable_id("perturbation", name)
    registry.add("condition_steps", condition_step_id=stable_id("condition_step", condition_id, 1), condition_id=condition_id, perturbation_id=perturbation_id, dose_value=dose, dose_unit="nM" if dose is not None else None, start_time=0.0, end_time=hours, time_unit="h", sequence_index=1, notes=None)
    if second_step:
        second_id = stable_id("perturbation", second_step)
        registry.add("condition_steps", condition_step_id=stable_id("condition_step", condition_id, 2), condition_id=condition_id, perturbation_id=second_id, dose_value=None, dose_unit=None, start_time=0.0, end_time=hours, time_unit="h", sequence_index=2, notes="Presence reported; concentration not reported.")
    return condition_id


def collect(registry: Registry) -> None:
    cells = _cells(RAW)
    registry.add("papers", paper_id=PAPER, pmid=None, pmcid=None, doi=None, title="Foretinib response in FLT3-ITD cell contexts", year=None, journal=None, citation=None, notes="Supplied immutable workbook; paper metadata not supplied.")
    registry.add("source_artifacts", source_artifact_id=ARTIFACT, paper_id=PAPER, artifact_type="WORKBOOK", path=relative(RAW), original_filename=RAW.name, sha256=sha256(RAW), figure=None, panel=None, supplement_identifier=None, source_description="Immutable Foretinib experiment workbook.")
    for name, target in (("Foretinib", "FLT3"), ("Gilteritinib", "FLT3"), ("No added drug", None), ("IL3", None)):
        perturbation_id = stable_id("perturbation", name)
        if not registry.has("perturbations", "perturbation_id", perturbation_id):
            registry.add("perturbations", perturbation_id=perturbation_id, name=name, type="DRUG" if name in {"Foretinib", "Gilteritinib"} else "CONTROL_OR_LIGAND", target_if_reported=target, source_name=name, notes=None)
    context_ids: dict[str, str] = {}
    for key, (line, species, disease) in CONTEXTS.items():
        context_id = stable_id("context", line, "FLT3_ITD")
        context_ids[key] = context_id
        registry.add("contexts", context_id=context_id, species=species, cell_line=line, cell_type=None, tissue=None, disease=disease, culture_context=None, notes=None)
        registry.add("context_alterations", context_alteration_id=stable_id("context_alteration", context_id, "FLT3", "ITD"), context_id=context_id, gene="FLT3", alteration_type="MUTATION", alteration="FLT3-ITD", zygosity_or_copy_context=None, source="experiment context", notes=None)

    wb_assay = stable_id("assay", PAPER, "western_blot", "2h")
    registry.add("assays", assay_id=wb_assay, paper_id=PAPER, assay_type="Western blot", assay_name="2 h phosphoprotein response", sample_type="cell lysate", measurement_platform="workbook quantitative band estimate", figure=None, panel=None, reported_time=2.0, reported_time_unit="h", replicate_count=None, notes="Workbook labels values as visual band-intensity estimates.")
    for key, sheet_name in SHEETS.items():
        sheet = cells[sheet_name]
        for column in "BCDEF":
            dose = _dose(sheet[f"{column}5"])
            condition_id = _condition(registry, context_ids[key], "Foretinib" if dose else "No added drug", dose, 2.0)
            for observable, row in ROWS.items():
                registry.add("observations", observation_id=stable_id("obs", PAPER, key, observable, dose, "2h"), paper_id=PAPER, context_id=context_ids[key], condition_id=condition_id, assay_id=wb_assay, observable=observable, observable_raw_label=observable, value=float(sheet[f"{column}{row}"]), value_unit="relative phosphosignal", time_value=2.0, time_unit="h", statistic="single reported estimate", uncertainty_type=None, uncertainty_value=None, replicate_count=None, normalization="relative band intensity", normalization_reference="untreated 0 nM control = 1.00", source_artifact_id=ARTIFACT, figure=None, panel=sheet_name, table=None, lane=column, extraction_method="IMAGE_DERIVED", quality_class="SEMI_QUANTITATIVE", is_censored=False, censoring_limit=None, notes="visually_estimated_from_band_darkness_and_thickness")

    flow_assay = stable_id("assay", PAPER, "flow_cytometry", "48h")
    registry.add("assays", assay_id=flow_assay, paper_id=PAPER, assay_type="Flow cytometry", assay_name="Annexin/PI apoptosis", sample_type="cells", measurement_platform="workbook table", figure=None, panel="Flow Cytometry", reported_time=48.0, reported_time_unit="h", replicate_count=None, notes=None)
    flow = cells["Flow Cytometry"]
    index_by_line = {"MV4-11": "mv4_11", "MOLM13": "molm13"}
    for row in range(5, 11):
        line, treatment = str(flow[f"A{row}"]), str(flow[f"B{row}"])
        drug = "Foretinib" if treatment.startswith("Foretinib") else "Gilteritinib" if treatment.startswith("Gilteritinib") else "No added drug"
        dose_match = re.search(r"([0-9.]+)\s*nmol/L", treatment)
        dose = float(dose_match.group(1)) if dose_match else 0.0
        condition_id = _condition(registry, context_ids[index_by_line[line]], drug, dose, 48.0)
        for observable, column in (("early_apoptotic_fraction", "C"), ("late_apoptotic_fraction", "D"), ("viable_fraction", "E"), ("necrotic_fraction", "F")):
            registry.add("observations", observation_id=stable_id("obs", PAPER, line, treatment, observable), paper_id=PAPER, context_id=context_ids[index_by_line[line]], condition_id=condition_id, assay_id=flow_assay, observable=observable, observable_raw_label=observable.replace("_fraction", " percent"), value=float(flow[f"{column}{row}"]), value_unit="percent", time_value=48.0, time_unit="h", statistic="single tabulated percentage", uncertainty_type=None, uncertainty_value=None, replicate_count=None, normalization=None, normalization_reference=None, source_artifact_id=ARTIFACT, figure=None, panel="Flow Cytometry", table=None, lane=str(row), extraction_method="DIRECT_SOURCE", quality_class="QUANTITATIVE", is_censored=False, censoring_limit=None, notes="directly_tabulated_percentage_no_digitization_note")

    viability_assay = stable_id("assay", PAPER, "viability", "48h")
    registry.add("assays", assay_id=viability_assay, paper_id=PAPER, assay_type="Viability", assay_name="48 h dose response", sample_type="cells", measurement_platform="workbook graph values", figure=None, panel="Panels E/G", reported_time=48.0, reported_time_unit="h", replicate_count=None, notes="Workbook values are approximate visual graph estimates.")
    series = (("Panel E - Dose Response", "B", "baf3_flt3_itd", "Foretinib", None), ("Panel E - Dose Response", "C", "baf3_flt3_itd", "Foretinib", "IL3"), ("Panel G - MV4-11 Plasma", "B", "mv4_11", "Foretinib", None), ("Panel G - MV4-11 Plasma", "C", "mv4_11", "Gilteritinib", None))
    for sheet_name, column, context_key, drug, second in series:
        sheet = cells[sheet_name]
        for row in range(5, 14):
            dose = 1000.0 * float(sheet[f"A{row}"])
            condition_id = _condition(registry, context_ids[context_key], drug, dose, 48.0, second_step=second)
            registry.add("observations", observation_id=stable_id("obs", PAPER, sheet_name, column, dose), paper_id=PAPER, context_id=context_ids[context_key], condition_id=condition_id, assay_id=viability_assay, observable="viability", observable_raw_label="viability_percent", value=float(sheet[f"{column}{row}"]), value_unit="percent", time_value=48.0, time_unit="h", statistic="single visual graph estimate", uncertainty_type=None, uncertainty_value=None, replicate_count=None, normalization="percent relative viability", normalization_reference=None, source_artifact_id=ARTIFACT, figure=None, panel=sheet_name, table=None, lane=str(row), extraction_method="PLOT_DIGITIZED", quality_class="SEMI_QUANTITATIVE", is_censored=False, censoring_limit=None, notes="visually_estimated_from_graph_data_points" + ("; IL3 present" if second else ""))

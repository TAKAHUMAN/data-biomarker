"""Import the immutable Luminespib workbook into model-independent observations."""

from __future__ import annotations

import re
import xml.etree.ElementTree as ET
from pathlib import Path
from zipfile import ZipFile

from registry_common import DATASETS, Registry, relative, sha256, stable_id

PAPER = "paper_luminespib_hsp90_workbook"
ARTIFACT = "artifact_luminespib_hsp90_workbook"
RAW = DATASETS / "raw" / "workbooks" / "luminespib_pd_drug_only.xlsx"
NS = {"m": "http://schemas.openxmlformats.org/spreadsheetml/2006/main", "r": "http://schemas.openxmlformats.org/officeDocument/2006/relationships"}


def _cells() -> dict[str, str | float]:
    with ZipFile(RAW) as archive:
        workbook = ET.fromstring(archive.read("xl/workbook.xml"))
        relationships = ET.fromstring(archive.read("xl/_rels/workbook.xml.rels"))
        targets = {item.attrib["Id"]: item.attrib["Target"] for item in relationships}
        sheet = next(item for item in workbook.find("m:sheets", NS) if item.attrib["name"] == "WB - Drug Dose Response")
        target = targets[sheet.attrib[f"{{{NS['r']}}}id"]].lstrip("/")
        target = target if target.startswith("xl/") else f"xl/{target}"
        xml = ET.fromstring(archive.read(target))
        result: dict[str, str | float] = {}
        for cell in xml.findall(".//m:sheetData/m:row/m:c", NS):
            reference = cell.attrib["r"]
            if cell.attrib.get("t") == "inlineStr":
                result[reference] = "".join(node.text or "" for node in cell.iter(f"{{{NS['m']}}}t"))
            else:
                value = cell.find("m:v", NS)
                if value is not None and value.text is not None:
                    result[reference] = float(value.text)
        return result


def _doses(cells: dict[str, str | float], row: int, columns: str) -> list[float]:
    output = []
    for column in columns:
        text = str(cells[f"{column}{row}"])
        output.append(0.0 if "Vehicle" in text else float(re.search(r"([0-9.]+)\s*nM", text).group(1)))
    return output


def _condition(registry: Registry, context_id: str, dose: float, hours: float = 24.0) -> str:
    name = "Luminespib" if dose else "No added drug"
    condition_id = stable_id("condition", PAPER, context_id, name, dose, hours)
    if not registry.has("conditions", "condition_id", condition_id):
        registry.add("conditions", condition_id=condition_id, context_id=context_id, condition_label=f"{name} {dose:g} nM for {hours:g} h", notes=None)
        registry.add("condition_steps", condition_step_id=stable_id("condition_step", condition_id), condition_id=condition_id, perturbation_id=stable_id("perturbation", name), dose_value=dose, dose_unit="nM", start_time=0.0, end_time=hours, time_unit="h", sequence_index=1, notes=None)
    return condition_id


def collect(registry: Registry) -> None:
    cells = _cells()
    registry.add("papers", paper_id=PAPER, pmid=None, pmcid=None, doi=None, title="Luminespib HSP90 drug-only pharmacodynamic workbook", year=None, journal=None, citation=None, notes="Supplied immutable workbook; paper metadata not supplied.")
    registry.add("source_artifacts", source_artifact_id=ARTIFACT, paper_id=PAPER, artifact_type="WORKBOOK", path=relative(RAW), original_filename=RAW.name, sha256=sha256(RAW), figure=None, panel=None, supplement_identifier=None, source_description="Immutable Luminespib experiment workbook.")
    for name, kind, target in (("Luminespib", "DRUG", "HSP90"), ("No added drug", "CONTROL", None)):
        perturbation_id = stable_id("perturbation", name)
        if not registry.has("perturbations", "perturbation_id", perturbation_id):
            registry.add("perturbations", perturbation_id=perturbation_id, name=name, type=kind, target_if_reported=target, source_name=name, notes=None)
    context_ids: dict[str, str] = {}
    for line in ("HeLa", "HN3"):
        context_id = stable_id("context", line, "luminespib_workbook")
        context_ids[line] = context_id
        registry.add("contexts", context_id=context_id, species="human", cell_line=line, cell_type=None, tissue=None, disease=None, culture_context=None, notes=None)
    assay = stable_id("assay", PAPER, "western_blot", "24h")
    registry.add("assays", assay_id=assay, paper_id=PAPER, assay_type="Western blot", assay_name="Luminespib dose response", sample_type="cell lysate", measurement_platform="workbook quantitative band estimate", figure=None, panel="WB - Drug Dose Response", reported_time=24.0, reported_time_unit="h", replicate_count=None, notes="Workbook stores normalized intensity values.")
    layouts = {"HeLa": (7, {"HSP72": 8, "pErbB2": 9, "total_ErbB2": 10, "cRAF": 11, "pAKT": 12, "total_AKT": 13, "gamma_tubulin": 14}), "HN3": (17, {"HSP72": 18, "pErbB2": 19, "total_ErbB2": 20, "cRAF": 21, "pAKT": 22, "total_AKT": 23, "gamma_tubulin": 24})}
    for line, (dose_row, observables) in layouts.items():
        for index, (column, dose) in enumerate(zip("BCDE", _doses(cells, dose_row, "BCDE"))):
            condition_id = _condition(registry, context_ids[line], dose)
            for raw_label, row in observables.items():
                registry.add("observations", observation_id=stable_id("obs", PAPER, line, raw_label, dose, "24h"), paper_id=PAPER, context_id=context_ids[line], condition_id=condition_id, assay_id=assay, observable=raw_label, observable_raw_label=raw_label, value=float(cells[f"{column}{row}"]), value_unit="relative band intensity", time_value=24.0, time_unit="h", statistic="single workbook value", uncertainty_type=None, uncertainty_value=None, replicate_count=None, normalization="relative band intensity", normalization_reference="vehicle = 1.00", source_artifact_id=ARTIFACT, figure=None, panel="WB - Drug Dose Response", table=None, lane=column, extraction_method="DIRECT_SOURCE", quality_class="QUANTITATIVE", is_censored=False, censoring_limit=None, notes=None)
    chk_assay = stable_id("assay", PAPER, "western_blot", "chk1_24h")
    registry.add("assays", assay_id=chk_assay, paper_id=PAPER, assay_type="Western blot", assay_name="Total CHK1", sample_type="cell lysate", measurement_platform="workbook quantitative band estimate", figure=None, panel="WB - Drug Dose Response", reported_time=24.0, reported_time_unit="h", replicate_count=None, notes=None)
    for line, row in (("HeLa", 29), ("HN3", 30)):
        for column, dose in zip("CDE", _doses(cells, 28, "CDE")):
            condition_id = _condition(registry, context_ids[line], dose)
            registry.add("observations", observation_id=stable_id("obs", PAPER, line, "total_CHK1", dose, "24h"), paper_id=PAPER, context_id=context_ids[line], condition_id=condition_id, assay_id=chk_assay, observable="total_CHK1", observable_raw_label="total_CHK1", value=float(cells[f"{column}{row}"]), value_unit="relative band intensity", time_value=24.0, time_unit="h", statistic="single workbook value", uncertainty_type=None, uncertainty_value=None, replicate_count=None, normalization="relative band intensity", normalization_reference="vehicle = 1.00", source_artifact_id=ARTIFACT, figure=None, panel="WB - Drug Dose Response", table=None, lane=column, extraction_method="DIRECT_SOURCE", quality_class="QUANTITATIVE", is_censored=False, censoring_limit=None, notes=None)

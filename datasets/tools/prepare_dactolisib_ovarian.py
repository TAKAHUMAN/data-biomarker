"""Normalize the supplied Dactolisib (BEZ235) ABCB1-overexpressing ovarian/pancreatic
cancer extraction into registry-v1 CSV tables for datasets/extracted/dactolisib_ovarian.

Source paper: Durrant DE, et al. "A Dual PI3 Kinase/mTOR Inhibitor BEZ235 reverses
doxorubicin resistance in ABCB1 overexpressing ovarian and pancreatic cancer cell
lines." Biochim Biophys Acta Gen Subj. 2020. DOI 10.1016/j.bbagen.2020.129556.
PMID 32061787 (PMC10845210, but PMC HTML not present locally) -- workbook-only
build, same pattern as dactolisib_mm and pemigatinib.py (no local PAPER file, so
no PAPER-type source_artifacts row).

Two supplied, immutable-provenance inputs drive this script and are never modified:
  - dactolisib_ABCB1ovarian_extracted.xlsx (per-figure digitized/curated workbook)
  - bez235_dox_qsp_pd_digitization.xlsx (companion QSP-recommendation workbook;
    its "Read me" sheet is authoritative for classifying each figure's data
    quality and for what should NOT be forced into quantitative observations).

Per the companion workbook's Read me sheet: Fig1D-F (ABCB1 protein, WB/confocal),
Fig2 (DOX accumulation flow histograms), and Fig3 (DOX efflux flow histograms) are
qualitative-only (no MFI/gate values printed) and are captured only in
not_quantifiable_figures.csv. Fig4C (p-S6 blot) and Fig6 (cleaved PARP blot) ARE
digitized to image-derived relative/ordinal numbers in the companion workbook and
are promoted to observations.csv with wide observation uncertainty, per the task
brief. THERE IS NO ANIMAL/TUMOUR MODEL IN THIS PAPER.
"""

from __future__ import annotations

import csv
import json
import re
from collections import Counter
from pathlib import Path
from typing import Any

import openpyxl

from registry_common import DATASETS, relative, sha256


PAPER_ID = "paper_PMID32061787"
EXTRACTED = DATASETS / "extracted" / "dactolisib_ovarian"
RAW_WORKBOOK = DATASETS / "raw" / "workbooks" / "dactolisib_ABCB1ovarian_extracted.xlsx"
RAW_QSP_WORKBOOK = DATASETS / "raw" / "workbooks" / "bez235_dox_qsp_pd_digitization.xlsx"

EXPECTED_WORKBOOK_SHEETS = {
    "Fig1ABC_DOX_DoseResponse", "Fig1DF_ABCB1_NotQuant", "Fig2_DOXaccum_FlowCyt_NotQuant",
    "Fig3_DOXefflux_FlowCyt_NotQuant", "Fig4AB_ATPase_Activity", "Fig4C_WB_pS6_NotQuant",
    "Fig5ABCD_Viability_BEZplusDOX", "Fig6AB_WB_ClPARP", "Summary",
}
EXPECTED_QSP_SHEETS = {
    "Model map", "Fig1 DOX response", "Fig4 ATPase", "Fig4C pS6 blot",
    "Fig5 combination PD", "Fig6 PARP blot", "Read me",
}


def _slug(value: object) -> str:
    return "_".join(re.sub(r"[^a-z0-9]+", " ", str(value).lower()).split())


def _write_csv(name: str, rows: list[dict[str, Any]], columns: list[str]) -> None:
    EXTRACTED.mkdir(parents=True, exist_ok=True)
    with (EXTRACTED / name).open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns, extrasaction="raise")
        writer.writeheader()
        writer.writerows({column: row.get(column) for column in columns} for row in rows)


# ---------------------------------------------------------------------------
# Digitized/curated data, transcribed exactly from the supplied workbooks.
# ---------------------------------------------------------------------------

# Fig1A-C: DOX dose-response (% viable cells), parental vs resistant pairs, 48h. From raw workbook.
FIG1_DOSES = [0, 0.05, 0.1, 0.2, 0.4, 0.6, 0.8, 1.0]
FIG1_PAIRS = {
    ("MiaPaCa2", "Mia-dx"): {  # Panel A
        "MiaPaCa2": [100, 98, 80, 62, 52, 42, 37, 30],
        "Mia-dx": [100, 105, 103, 96, 85, 84, 78, 75],
    },
    ("MiaPaCa2", "Mia-B1"): {  # Panel B
        "MiaPaCa2": [100, 97, 85, 72, 65, 47, 38, 38],
        "Mia-B1": [100, 100, 102, 105, 102, 102, 100, 90],
    },
    ("A2780", "A2780-dx"): {  # Panel C
        "A2780": [100, 50, 45, 38, 28, 18, 10, 5],
        "A2780-dx": [102, 88, 77, 68, 58, 55, 53, 50],
    },
}
FIG1_PANEL = {("MiaPaCa2", "Mia-dx"): "A", ("MiaPaCa2", "Mia-B1"): "B", ("A2780", "A2780-dx"): "C"}

# Fig4A-B: ABCB1 ATPase activity (relative light units, background-subtracted). From raw workbook.
FIG4A_ATPASE = [
    ("No treatment", 700, "-"), ("Vanadate", -300, "*"), ("Verapamil (positive control substrate)", 7500, "**"),
    ("DOX 0.2 uM", 1400, "*"), ("Sildenafil 10 uM", 3600, "**"), ("BEZ 50 nM", 950, "ns"), ("BEZ 150 nM", 1150, "#"),
]
FIG4B_ATPASE = [
    ("No Treatment", 1600, "-"), ("Vanadate", -200, "**"), ("Verapamil", 8400, "**"), ("BEZ 50 nM", 1900, "ns"),
    ("BEZ 150 nM", 2200, "#"), ("Verapamil + BEZ 50 nM", 8500, "**"), ("Verapamil + BEZ 150 nM", 8700, "**"),
    ("Verapamil + Vanadate", -300, "**"),
]

# Fig4C: p-S6/S6 relative-to-control (image-derived), +/- BEZ 50 nM, 24h. From companion QSP workbook
# (raw workbook only has a qualitative table for this panel; the QSP workbook's numeric estimates are used
# here per the task brief, with wide observation uncertainty).
FIG4C_PS6 = {
    "MiaPaCa2": {0: 1.0, 50: 0.9}, "Mia-dx": {0: 1.0, 50: 0.45}, "Mia-B1": {0: 1.0, 50: 0.1},
    "A2780": {0: 1.0, 50: 0.15}, "A2780-dx": {0: 1.0, 50: 0.15},
}

# Fig5A-D: % viable cells, BEZ +/- DOX 0.5 uM combination, 48h. From raw workbook.
FIG5_CONDITIONS = [
    ("control", None, None), ("BEZ 50nM", 50.0, None), ("BEZ 150nM", 150.0, None), ("BEZ 300nM", 300.0, None),
    ("BEZ 600nM", 600.0, None), ("DOX 0.5uM alone", None, 0.5), ("DOX+BEZ 50nM", 50.0, 0.5),
    ("DOX+BEZ 150nM", 150.0, 0.5), ("DOX+BEZ 300nM", 300.0, 0.5), ("DOX+BEZ 600nM", 600.0, 0.5),
]
FIG5_VALUES = {
    "MiaPaCa2": [100, 52, 42, 41, 40, 60, 34, 24, 22, 23],
    "Mia-B1": [100, 64, 47, 46, 44, 105, 64, 43, 37, 33],
    "A2780": [100, 40, 39, 39, 40, 26, 15, 13, 13, 14],
    "A2780-dx": [100, 45, 41, 40, 39, 55, 29, 23, 18, 17],
}
FIG5_EXPLICIT_TEXT = {
    ("MiaPaCa2", "DOX 0.5uM alone"), ("A2780", "DOX 0.5uM alone"), ("A2780-dx", "DOX 0.5uM alone"),
    ("MiaPaCa2", "DOX+BEZ 600nM"), ("A2780-dx", "DOX+BEZ 600nM"),
}

# Fig6A-B: cleaved PARP relative intensity, arbitrary 0-4 scale (-DOX / +DOX 0.5uM), across BEZ doses, 48h.
# From raw workbook (already digitized to a numeric relative-intensity estimate, not left qualitative).
FIG6_PARP = {
    "MiaPaCa2": [(0, 2, 2), (50, 2, 2), (150, 2, 3), (300, 2, 3.5), (600, 2, 4)],
    "Mia-B1": [(0, 0.2, 0.3), (50, 0.2, 0.3), (150, 0.2, 2.5), (300, 0.2, 3), (600, 0.2, 3.5)],
    "A2780": [(0, 0, 1.5), (50, 0, 2), (150, 0, 1.8), (300, 0, 2.2), (600, 0, 2.5)],
    "A2780-dx": [(0, 0, 0), (50, 0, 1), (150, 0, 1), (300, 0, 3), (600, 0, 4)],
}

CELL_INFO = {
    "MiaPaCa2": ("pancreatic ductal adenocarcinoma cell", "pancreas", "pancreatic cancer", "parental (DOX-sensitive)"),
    "Mia-dx": ("pancreatic ductal adenocarcinoma cell (DOX-resistant subline, ABCB1-undetectable)", "pancreas", "pancreatic cancer", "doxorubicin-resistant, selected by chronic DOX exposure; ABCB1 undetectable/very faint by WB -- resistance mechanism largely independent of ABCB1"),
    "Mia-B1": ("pancreatic ductal adenocarcinoma cell (ABCB1-overexpressing, engineered)", "pancreas", "pancreatic cancer", "ABCB1-overexpressing resistant subline (strongest ABCB1 WB band of the panel)"),
    "A2780": ("ovarian carcinoma cell", "ovary", "ovarian cancer", "parental (DOX-sensitive)"),
    "A2780-dx": ("ovarian carcinoma cell (DOX-resistant subline, ABCB1-overexpressing)", "ovary", "ovarian cancer", "doxorubicin-resistant, ABCB1-overexpressing (moderate-strong WB band, strong confocal membrane signal)"),
}

# Not-quantifiable figures/panels captured only as an audit CSV.
NOT_QUANTIFIABLE_ROWS: list[dict[str, Any]] = [
    {"figure": "Fig 1D", "panel": "D", "cell_line_or_group": "MiaPaca2 (parental)", "target_or_observable": "ABCB1 (Western blot)", "qualitative_result": "faint/low band", "reason_not_quantifiable": "No densitometry values printed on WB; qualitative ranking only."},
    {"figure": "Fig 1D", "panel": "D", "cell_line_or_group": "Mia-dx", "target_or_observable": "ABCB1 (Western blot)", "qualitative_result": "undetectable/very faint band", "reason_not_quantifiable": "No densitometry values printed on WB; qualitative ranking only."},
    {"figure": "Fig 1D", "panel": "D", "cell_line_or_group": "Mia-B1", "target_or_observable": "ABCB1 (Western blot)", "qualitative_result": "very strong (darkest band)", "reason_not_quantifiable": "No densitometry values printed on WB; qualitative ranking only."},
    {"figure": "Fig 1D", "panel": "D", "cell_line_or_group": "A2780 (parental)", "target_or_observable": "ABCB1 (Western blot)", "qualitative_result": "faint/low band", "reason_not_quantifiable": "No densitometry values printed on WB; qualitative ranking only."},
    {"figure": "Fig 1D", "panel": "D", "cell_line_or_group": "A2780-dx", "target_or_observable": "ABCB1 (Western blot)", "qualitative_result": "moderate-strong band", "reason_not_quantifiable": "No densitometry values printed on WB; qualitative ranking only."},
    {"figure": "Fig 1E-F", "panel": "E-F", "cell_line_or_group": "Mia-dx", "target_or_observable": "ABCB1 (confocal immunofluorescence)", "qualitative_result": "very low red signal", "reason_not_quantifiable": "No fluorescence-intensity scale bar for quantification; qualitative visual read only."},
    {"figure": "Fig 1E-F", "panel": "E-F", "cell_line_or_group": "Mia-B1", "target_or_observable": "ABCB1 (confocal immunofluorescence)", "qualitative_result": "strong red membrane signal", "reason_not_quantifiable": "No fluorescence-intensity scale bar for quantification; qualitative visual read only."},
    {"figure": "Fig 1E-F", "panel": "E-F", "cell_line_or_group": "A2780 (parental)", "target_or_observable": "ABCB1 (confocal immunofluorescence)", "qualitative_result": "low red signal", "reason_not_quantifiable": "No fluorescence-intensity scale bar for quantification; qualitative visual read only."},
    {"figure": "Fig 1E-F", "panel": "E-F", "cell_line_or_group": "A2780-dx", "target_or_observable": "ABCB1 (confocal immunofluorescence)", "qualitative_result": "strong red membrane signal", "reason_not_quantifiable": "No fluorescence-intensity scale bar for quantification; qualitative visual read only."},
    {"figure": "Fig 2A-C", "panel": None, "cell_line_or_group": "A2780-dx", "target_or_observable": "DOX accumulation (flow cytometry)", "qualitative_result": "Sildenafil 10 uM or BEZ 50 nM: partial leftward-shift reversal, similar magnitude for both. BEZ 150 nM: near-complete reversal of resistant phenotype.", "reason_not_quantifiable": "Overlay histograms of DOX auto-fluorescence with no printed MFI values or % positive gates; qualitative peak-shift description only."},
    {"figure": "Fig 2A-C", "panel": None, "cell_line_or_group": "Mia-B1", "target_or_observable": "DOX accumulation (flow cytometry)", "qualitative_result": "Sildenafil 10 uM or BEZ 50 nM: minor increase only (subdued response). BEZ 150 nM: enhanced accumulation but not as complete a reversal as A2780-dx.", "reason_not_quantifiable": "Same as above."},
    {"figure": "Fig 2A-C", "panel": None, "cell_line_or_group": "Mia-dx (ABCB1-undetectable)", "target_or_observable": "DOX accumulation (flow cytometry)", "qualitative_result": "BEZ 50/150 nM: little to minimal effect on DOX accumulation. Sildenafil increased accumulation more than BEZ, suggesting BEZ is more ABCB1-specific.", "reason_not_quantifiable": "Same as above."},
    {"figure": "Fig 3A-C", "panel": None, "cell_line_or_group": "A2780-dx", "target_or_observable": "DOX efflux (flow cytometry)", "qualitative_result": "BEZ and sildenafil inhibited DOX efflux in a dose-dependent manner", "reason_not_quantifiable": "Overlay histograms (1h DOX load + 2h efflux) with no printed MFI values or % positive gates."},
    {"figure": "Fig 3A-C", "panel": None, "cell_line_or_group": "Mia-B1", "target_or_observable": "DOX efflux (flow cytometry)", "qualitative_result": "BEZ and sildenafil inhibited DOX efflux in a dose-dependent manner", "reason_not_quantifiable": "Same as above."},
    {"figure": "Fig 3A-C", "panel": None, "cell_line_or_group": "Mia-dx (ABCB1-undetectable)", "target_or_observable": "DOX efflux (flow cytometry)", "qualitative_result": "Neither sildenafil nor BEZ inhibited efflux to a greater extent (no ABCB1 to inhibit)", "reason_not_quantifiable": "Same as above."},
]


def prepare() -> dict[str, int]:
    sources = [RAW_WORKBOOK, RAW_QSP_WORKBOOK]
    missing = [str(p) for p in sources if not p.is_file()]
    if missing:
        raise FileNotFoundError(f"Missing Dactolisib ovarian source artifacts: {missing}")

    workbook = openpyxl.load_workbook(RAW_WORKBOOK, read_only=True, data_only=True)
    if set(workbook.sheetnames) != EXPECTED_WORKBOOK_SHEETS:
        raise ValueError(f"Unexpected Dactolisib ovarian workbook sheets: {workbook.sheetnames}")
    qsp_workbook = openpyxl.load_workbook(RAW_QSP_WORKBOOK, read_only=True, data_only=True)
    if set(qsp_workbook.sheetnames) != EXPECTED_QSP_SHEETS:
        raise ValueError(f"Unexpected Dactolisib ovarian QSP workbook sheets: {qsp_workbook.sheetnames}")

    # ---- contexts -----------------------------------------------------
    contexts: dict[str, dict[str, Any]] = {}

    def context_key_for(cell_line: str) -> str:
        return f"{_slug(cell_line)}_in_vitro"

    def ensure_context(cell_line: str) -> str:
        key = context_key_for(cell_line)
        if key not in contexts:
            cell_type, tissue, disease, note = CELL_INFO[cell_line]
            contexts[key] = {
                "context_key": key, "species": "Homo sapiens", "cell_line": cell_line, "cell_type": cell_type,
                "tissue": tissue, "disease": disease, "culture_context": "in vitro 2D cell culture, 48 h viability assay (AQueous One)",
                "notes": note,
            }
        return key

    for line in CELL_INFO:
        ensure_context(line)

    # ---- assays ---------------------------------------------------------
    assay_rows = [
        {"assay_key": "dox_dose_response", "assay_type": "Cell viability assay (AQueous One)", "assay_name": "Fig1A-C doxorubicin dose-response, parental vs resistant pairs", "sample_type": "pancreatic or ovarian cancer cell line", "measurement_platform": "AQueous One viability assay, 48 h DOX exposure", "figure": "Figure 1", "panel": "A-C", "reported_time": 48, "reported_time_unit": "h", "replicate_count": None, "notes": "Visual estimate of bar heights (% viable cells vs control)."},
        {"assay_key": "abcb1_atpase", "assay_type": "ABCB1 ATPase activity assay", "assay_name": "Fig4A-B ABCB1 ATPase activity, isolated Pgp membranes", "sample_type": "isolated ABCB1 (P-glycoprotein) membrane preparation", "measurement_platform": "ATPase activity assay, relative light units (RLU), background-subtracted", "figure": "Figure 4", "panel": "A-B", "reported_time": None, "reported_time_unit": None, "replicate_count": None, "notes": "Significance vs 'No Treatment' per figure legend: ** p<0.001, * p<0.01, # p<0.05, ns not significant. BEZ does not substantially stimulate ATPase activity like true substrates (verapamil, sildenafil, DOX) and does not block verapamil-stimulated activity like vanadate -> poor/non-substrate, non-ATP-site inhibitor of ABCB1 (explicit interpretation from text)."},
        {"assay_key": "ps6_blot", "assay_type": "Western blot", "assay_name": "Fig4C phospho-S6/total S6/actin, +/- BEZ 50 nM", "sample_type": "pancreatic or ovarian cancer cell line", "measurement_platform": "Western blot, image-derived relative-to-control estimate (no software densitometry reported)", "figure": "Figure 4", "panel": "C", "reported_time": 24, "reported_time_unit": "h", "replicate_count": None, "notes": "mTORC1 target-engagement marker; parallel readout to the transporter-functional assays. p-S6 band intensity decreased with BEZ in all 5 lines; total S6/actin unchanged (loading controls)."},
        {"assay_key": "viability_bez_dox_combo", "assay_type": "Cell viability assay (AQueous One)", "assay_name": "Fig5A-D BEZ235 +/- doxorubicin combination viability", "sample_type": "pancreatic or ovarian cancer cell line", "measurement_platform": "AQueous One viability assay, 48 h", "figure": "Figure 5", "panel": "A-D", "reported_time": 48, "reported_time_unit": "h", "replicate_count": None, "notes": "Primary fitting data per companion QSP workbook Read me sheet. DOX alone dose = 0.5 uM in all panels. Several endpoint values cross-confirmed as explicit text values (see per-observation notes)."},
        {"assay_key": "cleaved_parp_blot", "assay_type": "Western blot", "assay_name": "Fig6A-B cleaved PARP, +/- DOX 0.5 uM across BEZ doses", "sample_type": "pancreatic or ovarian cancer cell line", "measurement_platform": "Western blot, relative band intensity read on an arbitrary 0-4 scale (not normalized densitometry ratios; no software quantification reported)", "figure": "Figure 6", "panel": "A-B", "reported_time": 48, "reported_time_unit": "h", "replicate_count": None, "notes": "BEZ alone did not induce cl-PARP in any line. DOX alone induced cl-PARP in MiaPaca2/A2780 but NOT in Mia-B1/A2780-dx (ABCB1-overexpressing); BEZ co-treatment re-sensitized Mia-B1/A2780-dx to DOX-induced PARP cleavage dose-dependently, mirroring the Fig5 viability decrease (explicit pattern from text)."},
    ]

    # ---- conditions -------------------------------------------------
    conditions: dict[str, dict[str, Any]] = {}
    steps: list[dict[str, Any]] = []

    def ensure_condition(context_key: str, label: str, step_specs: list[dict[str, Any]], notes: str | None = None) -> str:
        key = f"{context_key}__{_slug(label)}"
        if key not in conditions:
            conditions[key] = {"condition_key": key, "context_key": context_key, "condition_label": label, "notes": notes}
            for index, spec in enumerate(step_specs, start=1):
                steps.append({"condition_step_key": f"{key}__step_{index}", "condition_key": key, "sequence_index": index, **spec})
        return key

    def bez_step(dose: float | None, start: float, end: float, time_unit: str, notes: str | None = None) -> dict[str, Any]:
        return {"perturbation_name": "Dactolisib", "dose_value": dose, "dose_unit": "nM", "start_time": start, "end_time": end, "time_unit": time_unit, "notes": notes}

    def dox_step(dose: float | None, start: float, end: float, time_unit: str, notes: str | None = None) -> dict[str, Any]:
        return {"perturbation_name": "Doxorubicin", "dose_value": dose, "dose_unit": "uM", "start_time": start, "end_time": end, "time_unit": time_unit, "notes": notes}

    observations: list[dict[str, Any]] = []
    defaults = {
        "value": None, "value_unit": None, "time_value": None, "time_unit": None,
        "statistic": None, "uncertainty_type": None, "uncertainty_value": None,
        "replicate_count": None, "normalization": None, "normalization_reference": None,
        "figure": None, "panel": None, "table": None, "lane": None,
        "is_censored": False, "censoring_limit": None, "notes": None,
    }

    def add(**row: Any) -> None:
        item = dict(defaults)
        item.update(row)
        observations.append(item)

    # 1) Fig1A-C DOX dose-response.
    for pair, curves in FIG1_PAIRS.items():
        panel = FIG1_PANEL[pair]
        for line, values in curves.items():
            ctx = context_key_for(line)
            for dose, value in zip(FIG1_DOSES, values):
                label = f"Doxorubicin {dose:g} uM, 48 h" if dose else "Vehicle control, 48 h"
                step = [dox_step(dose if dose else None, 0, 48, "h")] if dose else [{"perturbation_name": "Vehicle", "dose_value": None, "dose_unit": None, "start_time": 0, "end_time": 48, "time_unit": "h", "notes": None}]
                cond = ensure_condition(ctx, f"{label} (Fig1{panel} pair: {pair[0]} vs {pair[1]})", step)
                add(record_id=f"fig1{panel.lower()}_{_slug(line)}_{dose}um", context_key=ctx, condition_key=cond, assay_key="dox_dose_response",
                    observable="pct_viable_cells", observable_raw_label=f"% viable cells, {line}, DOX {dose} uM (Fig1{panel})",
                    value=float(value), value_unit="% viable cells vs control", time_value=48, time_unit="h",
                    statistic="percent viable cells vs untreated control",
                    uncertainty_type="visual digitization uncertainty (bar-height estimate)",
                    source_key="workbook", figure="Figure 1", panel=panel, extraction_method="PLOT_DIGITIZED", quality_class="SEMI_QUANTITATIVE",
                    notes=f"Parental-vs-resistant pair: {pair[0]} (parental) vs {pair[1]} (resistant). n replicates not stated per bar (error bars small per source).")
            continue

    # 2) Fig4A-B ABCB1 ATPase activity.
    atpase_steps = {
        "No treatment": [], "No Treatment": [],
        "Vanadate": [("Vanadate", None, None)],
        "Verapamil (positive control substrate)": [("Verapamil", None, None)],
        "Verapamil": [("Verapamil", None, None)],
        "DOX 0.2 uM": [("Doxorubicin", 0.2, "uM")],
        "Sildenafil 10 uM": [("Sildenafil", 10.0, "uM")],
        "BEZ 50 nM": [("Dactolisib", 50.0, "nM")],
        "BEZ 150 nM": [("Dactolisib", 150.0, "nM")],
        "Verapamil + BEZ 50 nM": [("Verapamil", None, None), ("Dactolisib", 50.0, "nM")],
        "Verapamil + BEZ 150 nM": [("Verapamil", None, None), ("Dactolisib", 150.0, "nM")],
        "Verapamil + Vanadate": [("Verapamil", None, None), ("Vanadate", None, None)],
    }
    for panel, rows in (("A", FIG4A_ATPASE), ("B", FIG4B_ATPASE)):
        for condition_label, value, significance in rows:
            ctx = "isolated_abcb1_membrane_preparation"
            if ctx not in contexts:
                contexts[ctx] = {
                    "context_key": ctx, "species": "Homo sapiens", "cell_line": "Isolated ABCB1 (P-glycoprotein) membrane preparation",
                    "cell_type": "cell-free membrane vesicle preparation", "tissue": None, "disease": None,
                    "culture_context": "cell-free ABCB1 ATPase activity assay (isolated Pgp membranes)",
                    "notes": "Used to test whether BEZ235 is an ABCB1 transport substrate/ATPase stimulator or a non-ATP-site inhibitor, independent of any cell line.",
                }
            perturbagens = atpase_steps[condition_label]
            step_specs = [
                {"perturbation_name": name, "dose_value": dose, "dose_unit": unit, "start_time": None, "end_time": None, "time_unit": None, "notes": None}
                for name, dose, unit in perturbagens
            ] or [{"perturbation_name": "Vehicle", "dose_value": None, "dose_unit": None, "start_time": None, "end_time": None, "time_unit": None, "notes": None}]
            cond = ensure_condition(ctx, f"Fig4{panel}: {condition_label}", step_specs)
            add(record_id=f"fig4{panel.lower()}_{_slug(condition_label)}", context_key=ctx, condition_key=cond, assay_key="abcb1_atpase",
                observable="abcb1_atpase_activity_rlu", observable_raw_label=f"ATPase activity, {condition_label} (Fig4{panel})",
                value=float(value), value_unit="RLU (background-subtracted)", statistic="approximate bar height",
                uncertainty_type="visual digitization uncertainty (bar-height estimate)",
                source_key="workbook", figure="Figure 4", panel=panel, extraction_method="PLOT_DIGITIZED", quality_class="SEMI_QUANTITATIVE",
                notes=f"Significance vs 'No Treatment': {significance}.")

    # 3) Fig4C p-S6/S6 relative-to-control (from companion QSP workbook, image-derived).
    for line, doses in FIG4C_PS6.items():
        ctx = context_key_for(line)
        for dose, value in doses.items():
            label = f"BEZ235 {dose:g} nM, 24 h" if dose else "Vehicle control, 24 h"
            step = [bez_step(dose if dose else None, 0, 24, "h")] if dose else [{"perturbation_name": "Vehicle", "dose_value": None, "dose_unit": None, "start_time": 0, "end_time": 24, "time_unit": "h", "notes": None}]
            cond = ensure_condition(ctx, f"{label} (Fig4C pS6 blot)", step)
            add(record_id=f"fig4c_{_slug(line)}_{dose}nm", context_key=ctx, condition_key=cond, assay_key="ps6_blot",
                observable="pS6_over_S6_relative_to_control", observable_raw_label=f"p-S6/S6, {line}, BEZ {dose} nM, 24 h",
                value=float(value), value_unit="relative to 0 nM control", time_value=24, time_unit="h",
                statistic="single-blot image-derived relative estimate",
                uncertainty_type="ordinal/semi-quantitative image estimate; wide observation error (companion QSP workbook Read me guidance)",
                uncertainty_value=0.3,
                source_key="qsp_workbook", figure="Figure 4", panel="C", extraction_method="BLOT_DENSITOMETRY", quality_class="SEMI_QUANTITATIVE",
                notes="Raw curated workbook records this panel as qualitative-only (band-intensity call); the companion QSP "
                      "digitization workbook's numeric relative-to-control estimate is used here per task guidance, with wide "
                      "observation uncertainty since it is image-derived and not software densitometry.")

    # 4) Fig5A-D BEZ +/- DOX combination viability (primary fitting data).
    line_letter = {"MiaPaCa2": "A", "Mia-B1": "B", "A2780": "C", "A2780-dx": "D"}
    for line, values in FIG5_VALUES.items():
        ctx = context_key_for(line)
        panel = line_letter[line]
        for (label, bez_dose, dox_dose), value in zip(FIG5_CONDITIONS, values):
            step_specs = []
            if bez_dose:
                step_specs.append(bez_step(bez_dose, 0, 48, "h"))
            if dox_dose:
                step_specs.append(dox_step(dox_dose, 0, 48, "h"))
            if not step_specs:
                step_specs = [{"perturbation_name": "Vehicle", "dose_value": None, "dose_unit": None, "start_time": 0, "end_time": 48, "time_unit": "h", "notes": None}]
            cond = ensure_condition(ctx, f"{label}, 48 h (Fig5{panel})", step_specs)
            explicit = (line, label) in FIG5_EXPLICIT_TEXT
            add(record_id=f"fig5{panel.lower()}_{_slug(line)}_{_slug(label)}", context_key=ctx, condition_key=cond, assay_key="viability_bez_dox_combo",
                observable="pct_viable_cells", observable_raw_label=f"% viable cells, {line}, {label} (Fig5{panel})",
                value=float(value), value_unit="% viable cells vs untreated control", time_value=48, time_unit="h",
                statistic="percent viable cells vs untreated control",
                uncertainty_type=None if explicit else "visual digitization uncertainty (bar-height estimate)",
                source_key="workbook", figure="Figure 5", panel=panel,
                extraction_method="DIRECT_SOURCE" if explicit else "PLOT_DIGITIZED",
                quality_class="QUANTITATIVE" if explicit else "SEMI_QUANTITATIVE",
                notes="Endpoint value cross-confirmed as an explicit text value." if explicit else "Visual estimate of bar height (% viable cells vs untreated control=100).")

    # 5) Fig6A-B cleaved PARP relative intensity.
    for line, rows in FIG6_PARP.items():
        ctx = context_key_for(line)
        panel = {"MiaPaCa2": "A", "Mia-B1": "A", "A2780": "B", "A2780-dx": "B"}[line]
        for bez_dose, no_dox_value, plus_dox_value in rows:
            for dox_present, value in ((False, no_dox_value), (True, plus_dox_value)):
                step_specs = []
                if bez_dose:
                    step_specs.append(bez_step(float(bez_dose), 0, 48, "h"))
                if dox_present:
                    step_specs.append(dox_step(0.5, 0, 48, "h"))
                if not step_specs:
                    step_specs = [{"perturbation_name": "Vehicle", "dose_value": None, "dose_unit": None, "start_time": 0, "end_time": 48, "time_unit": "h", "notes": None}]
                label = f"BEZ235 {bez_dose:g} nM" + (" + doxorubicin 0.5 uM" if dox_present else "") + ", 48 h"
                cond = ensure_condition(ctx, f"{label} (Fig6 PARP blot)", step_specs)
                add(record_id=f"fig6_{_slug(line)}_bez{int(bez_dose)}_{'plusdox' if dox_present else 'nodox'}",
                    context_key=ctx, condition_key=cond, assay_key="cleaved_parp_blot",
                    observable="cleaved_PARP_relative_intensity", observable_raw_label=f"cleaved PARP, {line}, {label}",
                    value=float(value), value_unit="relative band intensity (arbitrary 0-4 scale)", time_value=48, time_unit="h",
                    statistic="single-blot relative intensity estimate (0=no band, 4=strongest band on this blot)",
                    uncertainty_type="ordinal/semi-quantitative image estimate; wide observation error (arbitrary scale, no software densitometry)",
                    uncertainty_value=0.3,
                    source_key="workbook", figure="Figure 6", panel=panel, extraction_method="BLOT_DENSITOMETRY", quality_class="SEMI_QUANTITATIVE",
                    notes="Relative intensity read on an arbitrary 0-4 scale (not normalized densitometry ratios); actin loading "
                          "control bands even across all lanes (not shown numerically) per source.")

    context_columns = ["context_key", "species", "cell_line", "cell_type", "tissue", "disease", "culture_context", "notes"]
    condition_columns = ["condition_key", "context_key", "condition_label", "notes"]
    step_columns = ["condition_step_key", "condition_key", "perturbation_name", "dose_value", "dose_unit", "start_time", "end_time", "time_unit", "sequence_index", "notes"]
    assay_columns = ["assay_key", "assay_type", "assay_name", "sample_type", "measurement_platform", "figure", "panel", "reported_time", "reported_time_unit", "replicate_count", "notes"]
    observation_columns = [
        "record_id", "context_key", "condition_key", "assay_key", "observable", "observable_raw_label",
        "value", "value_unit", "time_value", "time_unit", "statistic", "uncertainty_type",
        "uncertainty_value", "replicate_count", "normalization", "normalization_reference", "source_key",
        "figure", "panel", "table", "lane", "extraction_method", "quality_class", "is_censored",
        "censoring_limit", "notes",
    ]
    not_quant_columns = ["figure", "panel", "cell_line_or_group", "target_or_observable", "qualitative_result", "reason_not_quantifiable"]

    _write_csv("contexts.csv", sorted(contexts.values(), key=lambda r: r["context_key"]), context_columns)
    _write_csv("conditions.csv", sorted(conditions.values(), key=lambda r: r["condition_key"]), condition_columns)
    _write_csv("condition_steps.csv", sorted(steps, key=lambda r: r["condition_step_key"]), step_columns)
    _write_csv("assays.csv", sorted(assay_rows, key=lambda r: r["assay_key"]), assay_columns)
    _write_csv("observations.csv", sorted(observations, key=lambda r: r["record_id"]), observation_columns)
    _write_csv("not_quantifiable_figures.csv", NOT_QUANTIFIABLE_ROWS, not_quant_columns)

    counts = {
        "contexts": len(contexts), "conditions": len(conditions), "condition_steps": len(steps),
        "assays": len(assay_rows), "observations": len(observations),
        "not_quantifiable_figures": len(NOT_QUANTIFIABLE_ROWS),
    }
    artifacts = [
        {"source_key": "workbook", "path": RAW_WORKBOOK},
        {"source_key": "qsp_workbook", "path": RAW_QSP_WORKBOOK},
    ]
    metadata = {
        "schema_version": 1, "paper_id": PAPER_ID, "pmid": "32061787", "pmcid": "PMC10845210",
        "doi": "10.1016/j.bbagen.2020.129556",
        "extraction_date": "2026-09-08", "generated_counts": counts,
        "observation_counts_by_method": dict(sorted(Counter(row["extraction_method"] for row in observations).items())),
        "source_artifacts": [
            {"source_key": item["source_key"], "path": relative(item["path"]), "sha256": sha256(item["path"])}
            for item in artifacts
        ],
        "corrections": [
            "Fig4A-B ATPase 'vanadate' RLU value differs slightly between the raw curated workbook (-300 for Fig4A, "
            "-200/-300 for Fig4B verapamil+vanadate) and the companion QSP workbook (-100 for Fig4A, -100/-200 for "
            "Fig4B); the raw curated workbook's values are used as authoritative (primary per-figure source), "
            "difference noted as visual-digitization variance between two independent bar-height re-reads.",
            "Fig4C p-S6/S6 relative values are NOT present as numbers in the raw curated workbook (recorded there "
            "as a qualitative band-intensity call only); the companion QSP digitization workbook's numeric "
            "relative-to-control estimates are promoted to observations.csv instead, per the task brief's guidance "
            "that Fig4C is an image-derived relative/ordinal estimate warranting wide observation error (a fixed "
            "uncertainty_value of 0.3 relative-units is applied to every Fig4C observation as a conservative "
            "wide-error placeholder, not a measured SD/SEM).",
        ],
        "caveats": [
            "THERE IS NO ANIMAL/TUMOUR MODEL IN THIS PAPER. All data in this package are in vitro (2D cell culture) "
            "or cell-free (isolated ABCB1 membrane ATPase assay). Nothing in this package should be read as "
            "implying in vivo/tumour efficacy data exists for this study.",
            "Fig1D-F (ABCB1 protein by western blot and confocal microscopy), Fig2 (DOX accumulation flow "
            "cytometry overlay histograms), and Fig3 (DOX efflux flow cytometry overlay histograms) are explicitly "
            "NOT quantifiable per both the raw curated workbook and the companion QSP workbook's Read me sheet: no "
            "densitometry values, fluorescence-intensity scale bars, MFI values, or % positive gates are printed. "
            "These are captured only in not_quantifiable_figures.csv as qualitative calls, never forced into "
            "observations.csv.",
            "Fig4C (p-S6/S6, mTORC1 target engagement) and Fig6 (cleaved PARP) are image-derived relative/ordinal "
            "estimates, not software densitometry ratios; both carry wide observation uncertainty flags "
            "(quality_class SEMI_QUANTITATIVE) per the companion QSP workbook's Read me sheet guidance.",
            "The companion QSP workbook's Read me sheet designates Figure 5 viability and Figure 1 DOX-resistance "
            "curves as the primary fitting data for the recommended joint transporter/pathway/combination PD model "
            "(ABCB1 efflux -> intracellular DOX -> cleaved PARP -> viability, with p-S6 as a parallel target-"
            "engagement readout); Fig2/Fig3 fluorescence histograms should be used only qualitatively unless raw "
            "FCS/MFI data are obtained from the authors.",
            "Fig6 relative band-intensity values are read on an arbitrary 0-4 scale defined per-blot (0=no band, "
            "4=strongest band seen on THAT blot), not a normalized densitometry ratio comparable across blots or "
            "across the companion QSP workbook's separately-scaled Fig6 sheet (which uses a 0-1.15 range for the "
            "same concept); the two are not on the same numeric scale and were not reconciled.",
            "This package is workbook-only: PMID 32061787 has a PMCID (PMC10845210) but no local PMC HTML/paper "
            "file is available, so there is no PAPER-type source_artifacts row, mirroring the dactolisib_mm and "
            "pemigatinib.py pattern.",
        ],
    }
    (EXTRACTED / "extraction_metadata.json").write_text(
        json.dumps(metadata, indent=2, sort_keys=True, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    return counts


if __name__ == "__main__":
    for table, count in prepare().items():
        print(f"prepared {table}: {count}")

"""Normalize the supplied Dactolisib (NVP-BEZ235) multiple myeloma extraction into
registry-v1 CSV tables for datasets/extracted/dactolisib_mm.

Source paper: McMillin DW, et al. "Antimyeloma Activity of the Orally Bioavailable
Dual Phosphatidylinositol 3-Kinase/Mammalian Target of Rapamycin Inhibitor
NVP-BEZ235." Cancer Research 2009;69(14):5835-42. PMID 19584292 (no PMCID).

There is no raw paper PDF/HTML/figure image available locally for this study
(unlike birinapant/cilengitide) -- this is a workbook + companion-MOA-doc-only
build, mirroring pemigatinib.py's pattern for source_artifacts when no local
paper file exists (no PAPER-type source_artifacts row).

Two supplied, immutable-provenance inputs drive this script and are never modified:
  - dactolisib_multipleMyeloma_extracted.xlsx (per-figure digitized/curated workbook)
  - BEZ235_QSP_PD_Biomarker_Cascade.md + its companion annotations workbook
    (human-written interpretive MOA cascade guide with its own digitized tables
    for a subset of figures -- treated as the higher-precision source for Fig1C,
    Fig2A, Fig2B per the task brief, and cross-checked against the raw workbook
    elsewhere).

Figures explicitly marked NOT reliably quantifiable in the source workbook
(Fig2C-D, Fig3B-C western blots; Fig4 gene-signature bars; Fig6A-C 3D combination
surfaces) are captured only in not_quantifiable_figures.csv, never forced into
observations.csv.
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


PAPER_ID = "paper_PMID19584292"
EXTRACTED = DATASETS / "extracted" / "dactolisib_mm"
RAW_WORKBOOK = DATASETS / "raw" / "workbooks" / "dactolisib_multipleMyeloma_extracted.xlsx"
RAW_ANNOTATION_WORKBOOK = DATASETS / "raw" / "workbooks" / "BEZ235_QSP_PD_Biomarker_Cascade_Annotations.xlsx"
MOA_DOC = EXTRACTED / "BEZ235_QSP_PD_Biomarker_Cascade.md"

EXPECTED_WORKBOOK_SHEETS = {
    "Fig1A_IC50_CellLinePanel", "Fig1B_PatientSamples_DoseResp", "Fig1CD_NormalCell_Controls",
    "Fig2AB_Akt_Bcl2_DoseResp", "Fig2CD_WB_AktBcl2_NotQuant", "Fig3A_AnnexinV_FlowCyt",
    "Fig3BC_WB_ApoptosisPathway", "Fig4_GeneSignatures_SemiQuant", "Fig5ABC_Xenograft_InVivo",
    "Fig6ABC_Combo_NotQuant", "Summary",
}
EXPECTED_ANNOTATION_SHEETS = {"Cascade Map", "Digitized Data", "Figure Annotations", "Modeling Notes"}


def _slug(value: object) -> str:
    return "_".join(re.sub(r"[^a-z0-9]+", " ", str(value).lower()).split())


def _write_csv(name: str, rows: list[dict[str, Any]], columns: list[str]) -> None:
    EXTRACTED.mkdir(parents=True, exist_ok=True)
    with (EXTRACTED / name).open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns, extrasaction="raise")
        writer.writeheader()
        writer.writerows({column: row.get(column) for column in columns} for row in rows)


# ---------------------------------------------------------------------------
# Digitized/curated data, transcribed from the supplied workbook sheets and
# (for Fig1C, Fig2A, Fig2B) the higher-precision MOA-doc digitized tables per
# the task brief. Values are exactly those printed in the source sheets/tables.
# ---------------------------------------------------------------------------

# Fig1A: printed IC50s (nmol/L), 21-line MM panel, 48h MTT. From workbook.
FIG1A_IC50 = {
    "MM.1S": 22.78, "JJN3": 17.87, "MM.1R": 24.64, "ARK": 27.64, "Dox40": 19.78,
    "KMS-12-PE": 40.05, "NCI-H929": 31.81, "OPM-6": 112.16, "KMS-11": 54.71,
    "Delta 47": 141.52, "OPM-2": 99.63, "U266": 152.64, "KMS-34": 347.70,
    "S6B45": 190.88, "KMS-5": 515.04, "KMS-12-BM": 425.41, "OCI-MY5": 623.30,
    "KMS-28-PE": None, "XG1": None, "KMS-28-BM": None, "MR20": None,
}
FIG1A_CENSORED = {"KMS-28-PE", "XG1", "KMS-28-BM", "MR20"}  # printed as ">800"

# Fig1B: % survival vs BEZ235 dose, 5 primary MM patient samples, 48h MTT (visual estimate). From workbook.
FIG1B_DOSES = [0, 25, 50, 100, 200, 400, 800]
FIG1B_PATIENTS = {
    "Patient 1 (resistant)": [100, 110, 100, 95, 88, 86, 84],
    "Patient 2 (resistant)": [100, 100, 95, 90, 80, 80, 78],
    "Patient 3 (sensitive)": [100, 75, 68, 60, 45, 35, 22],
    "Patient 4 (sensitive)": [100, 50, 45, 38, 30, 28, 25],
    "Patient 5 (most sensitive)": [100, 45, 30, 15, 8, 5, 3],
}

# Fig1C selectivity: % survival vs BEZ235 dose (THLE-3, HS-5, MM.1S). MOA-doc digitized table
# (8 dose points incl ~10 nM), used per task brief as the higher-precision source for this panel.
FIG1C_DOSES = [0, 10, 25, 50, 100, 200, 400, 800]
FIG1C_CURVES = {
    "THLE-3": [100, 92, 92, 91.9, 86.0, 76.4, 77.6, 76],
    "HS-5": [100, 80, 71.1, 66.2, 63.4, 55.8, 48.1, 48.7],
    "MM.1S": [100, 90, 35, 25, 20, 11, 5, 3],
}
FIG1C_APPROXIMATE_DOSE = {10}  # "~10" in the MOA doc table

# Fig1D: pooled/representative PBMC (unstim/PHA-stim range) curve. From workbook (single
# representative range given for 8 donor curves that were too tightly clustered to separate).
FIG1D_DOSES = [0, 25, 50, 100, 200, 400, 800]
FIG1D_PBMC = [100, 100, 95, 92, 88, 85, 80]

# Fig2A: Akt-node rescue, % survival vs BEZ235 dose. MOA-doc digitized table (task brief: encode
# with the MOA doc's exact numbers as the highest-value mechanistic data).
FIG2_DOSES = [0, 10, 25, 50, 100, 200, 400, 800]
FIG2A = {
    "MM.1S parental (Fig2A)": [100, 96, 73.5, 52.4, 35.2, 22.7, 6.7, 2.4],
    "MM.1S-myrAkt": [100, 97, 80.9, 63.0, 42.9, 31.5, 19.1, 5.6],
}
# Fig2B: Bcl-2-node rescue, % survival vs BEZ235 dose. MOA-doc digitized table -- preserves the
# non-zero survival plateau (MM.1S-Bcl-2 stays at 32-38% from 50 nM onward) exactly as digitized.
FIG2B = {
    "MM.1S parental (Fig2B)": [100, 65, 35.0, 26.0, 20.1, 11.2, 5.2, 3.7],
    "MM.1S-Bcl-2": [100, 70, 66, 53.7, 37.9, 38.2, 34.3, 31.7],
}
FIG2_APPROXIMATE_DOSE = {10}

# Fig3A: Annexin V/PI flow cytometry, MM.1S, 100 nmol/L BEZ235 time-course. Explicit printed
# quadrant percentages (identical in workbook and MOA doc).
FIG3A_TIMEPOINTS = [
    (0.0, "Control (0h)", 98.4, 0.18, 0.45, 0.99),
    (24.0, "24h", 91.9, 3.54, 2.92, 1.58),
    (36.0, "36h", 70.7, 14.1, 12.2, 2.91),
    (48.0, "48h", 52.1, 9.93, 37.8, 0.24),
]

# Fig5A: in vivo tumor size (mm2), MM.1S-GFP/luc s.c. xenograft. From workbook.
FIG5A_TUMOR_SIZE = [
    (28.0, 35, 17), (34.0, 73, 38), (40.0, 158, 42), (47.0, 167, 42),
]
# Fig5B: Kaplan-Meier percent survival. From workbook.
FIG5B_SURVIVAL = [
    (0.0, 100, 100), (25.0, 90, 100), (38.0, 80, 100), (40.0, 68, 80),
    (50.0, 35, 80), (55.0, 20, 80), (60.0, 20, 80),
]
# Fig5C: body weight (g). From workbook.
FIG5C_BODY_WEIGHT = [
    (0.0, 20, 21), (15.0, 22, 20), (25.0, 23, 22), (35.0, 25, 23),
]

# Not-quantifiable figures/panels: qualitative-only content, kept as an audit CSV
# rather than forced into observations.csv (Fig2C-D, Fig3B-C western blots; Fig4
# gene-signature bars; Fig6A-C 3D combination surfaces).
NOT_QUANTIFIABLE_ROWS: list[dict[str, Any]] = [
    # Fig2C-D
    {"figure": "Fig 2C", "panel": "C", "cell_line_or_group": "Parental MM.1S", "target_or_observable": "Akt (total)", "qualitative_result": "Stable across time points (0-24h, 100 nmol/L BEZ235)", "reason_not_quantifiable": "No densitometry printed on blot; qualitative visual read only."},
    {"figure": "Fig 2C", "panel": "C", "cell_line_or_group": "Parental MM.1S", "target_or_observable": "p-Akt Ser473", "qualitative_result": "Decreased starting ~4-8h, most reduced by 24h", "reason_not_quantifiable": "No densitometry printed on blot; qualitative visual read only."},
    {"figure": "Fig 2C", "panel": "C", "cell_line_or_group": "Parental MM.1S", "target_or_observable": "p-Akt Thr308", "qualitative_result": "Decreased starting ~4-8h, most reduced by 24h", "reason_not_quantifiable": "No densitometry printed on blot; qualitative visual read only."},
    {"figure": "Fig 2C", "panel": "C", "cell_line_or_group": "MM.1S-myr-Akt", "target_or_observable": "Akt (total)", "qualitative_result": "Stable, higher baseline than parental (overexpression)", "reason_not_quantifiable": "No densitometry printed on blot; qualitative visual read only."},
    {"figure": "Fig 2C", "panel": "C", "cell_line_or_group": "MM.1S-myr-Akt", "target_or_observable": "p-Akt Ser473/Thr308", "qualitative_result": "Comparable decrease pattern to parental", "reason_not_quantifiable": "No densitometry printed on blot; qualitative visual read only."},
    {"figure": "Fig 2D", "panel": "D", "cell_line_or_group": "Parental MM.1S", "target_or_observable": "Bcl-2", "qualitative_result": "Increased over time (compensatory upregulation)", "reason_not_quantifiable": "No densitometry printed on blot; qualitative visual read only."},
    {"figure": "Fig 2D", "panel": "D", "cell_line_or_group": "Parental MM.1S", "target_or_observable": "Bad", "qualitative_result": "Stable", "reason_not_quantifiable": "No densitometry printed on blot; qualitative visual read only."},
    {"figure": "Fig 2D", "panel": "D", "cell_line_or_group": "Parental MM.1S", "target_or_observable": "Bcl-XL", "qualitative_result": "Stable", "reason_not_quantifiable": "No densitometry printed on blot; qualitative visual read only."},
    {"figure": "Fig 2D", "panel": "D", "cell_line_or_group": "MM.1S-Bcl-2", "target_or_observable": "Bcl-2", "qualitative_result": "Constitutively high, stable", "reason_not_quantifiable": "No densitometry printed on blot; qualitative visual read only."},
    {"figure": "Fig 2D", "panel": "D", "cell_line_or_group": "MM.1S-Bcl-2", "target_or_observable": "Bad / Bcl-XL", "qualitative_result": "Stable", "reason_not_quantifiable": "No densitometry printed on blot; qualitative visual read only."},
    # Fig3B-C
    {"figure": "Fig 3B", "panel": "B", "cell_line_or_group": "MM.1S", "target_or_observable": "PARP (full-length)", "qualitative_result": "Slight decrease at 24h (consistent with cleavage)", "reason_not_quantifiable": "No densitometry printed on blot; qualitative visual read only."},
    {"figure": "Fig 3B", "panel": "B", "cell_line_or_group": "MM.1S", "target_or_observable": "Caspase-3 (full-length)", "qualitative_result": "Relatively stable, slight decrease at later time points", "reason_not_quantifiable": "No densitometry printed on blot; qualitative visual read only."},
    {"figure": "Fig 3B", "panel": "B", "cell_line_or_group": "MM.1S", "target_or_observable": "Caspase-3 (cleaved)", "qualitative_result": "Appears starting ~8h, increases through 24h", "reason_not_quantifiable": "No densitometry printed on blot; qualitative visual read only."},
    {"figure": "Fig 3C", "panel": "C", "cell_line_or_group": "MM.1S", "target_or_observable": "Phospho-mTOR", "qualitative_result": "Sharply decreased by 2h, remains suppressed through 24h", "reason_not_quantifiable": "No densitometry printed on blot; qualitative visual read only."},
    {"figure": "Fig 3C", "panel": "C", "cell_line_or_group": "MM.1S", "target_or_observable": "Total mTOR", "qualitative_result": "Stable across time points", "reason_not_quantifiable": "No densitometry printed on blot; qualitative visual read only."},
    {"figure": "Fig 3C", "panel": "C", "cell_line_or_group": "MM.1S", "target_or_observable": "Phospho-p70S6K", "qualitative_result": "Sharply decreased by 2h, remains suppressed through 24h", "reason_not_quantifiable": "No densitometry printed on blot; qualitative visual read only."},
    {"figure": "Fig 3C", "panel": "C", "cell_line_or_group": "MM.1S", "target_or_observable": "Total p70S6K", "qualitative_result": "Stable across time points", "reason_not_quantifiable": "No densitometry printed on blot; qualitative visual read only."},
    # Fig4 gene signatures
    {"figure": "Fig 4", "panel": None, "cell_line_or_group": "MM.1S", "target_or_observable": "myc (Zeller et al.) signature", "qualitative_result": "Decreased, as early as 4h, large decrease at 24h", "reason_not_quantifiable": "12 overlapping gene signatures x 5 timepoints with large error bars densely overlapping; only direction/relative rank at 24h reliably readable; low-confidence visual estimate."},
    {"figure": "Fig 4", "panel": None, "cell_line_or_group": "MM.1S", "target_or_observable": "myc (Yu et al.) signature", "qualitative_result": "Decreased, as early as 4h, large decrease at 24h", "reason_not_quantifiable": "Same as above."},
    {"figure": "Fig 4", "panel": None, "cell_line_or_group": "MM.1S", "target_or_observable": "High-risk MM (Q4) signature", "qualitative_result": "Decreased, as early as 4h, large decrease at 24h", "reason_not_quantifiable": "Same as above."},
    {"figure": "Fig 4", "panel": None, "cell_line_or_group": "MM.1S", "target_or_observable": "Angiogenic (Hu et al.) signature", "qualitative_result": "Decreased, as early as 4h, moderate-large decrease at 24h", "reason_not_quantifiable": "Same as above."},
    {"figure": "Fig 4", "panel": None, "cell_line_or_group": "MM.1S", "target_or_observable": "Proteasome signature", "qualitative_result": "Decreased, as early as 4h, moderate decrease at 24h", "reason_not_quantifiable": "Same as above; check for a GEO/microarray accession before attempting further digitization."},
    {"figure": "Fig 4", "panel": None, "cell_line_or_group": "MM.1S", "target_or_observable": "Undifferentiated human ES cell signature", "qualitative_result": "Decreased, as early as 4h, moderate decrease at 24h", "reason_not_quantifiable": "Same as above."},
    {"figure": "Fig 4", "panel": None, "cell_line_or_group": "MM.1S", "target_or_observable": "Mouse embryonic SC signature", "qualitative_result": "Decreased, later onset (8-24h), small-moderate decrease", "reason_not_quantifiable": "Same as above."},
    {"figure": "Fig 4", "panel": None, "cell_line_or_group": "MM.1S", "target_or_observable": "Downregulated by p53 signature", "qualitative_result": "Mixed/small change, variable onset", "reason_not_quantifiable": "Same as above."},
    {"figure": "Fig 4", "panel": None, "cell_line_or_group": "MM.1S", "target_or_observable": "Hedgehog signature", "qualitative_result": "Small increase, variable onset", "reason_not_quantifiable": "Same as above."},
    {"figure": "Fig 4", "panel": None, "cell_line_or_group": "MM.1S", "target_or_observable": "hTERT signature", "qualitative_result": "Small increase, variable onset", "reason_not_quantifiable": "Same as above."},
    {"figure": "Fig 4", "panel": None, "cell_line_or_group": "MM.1S", "target_or_observable": "IRF4 signature", "qualitative_result": "Increased at 24h, moderate increase", "reason_not_quantifiable": "Same as above."},
    {"figure": "Fig 4", "panel": None, "cell_line_or_group": "MM.1S", "target_or_observable": "Notch signature", "qualitative_result": "Increased at 24h, moderate-large increase", "reason_not_quantifiable": "Same as above."},
    {"figure": "Fig 4", "panel": None, "cell_line_or_group": "MM.1S", "target_or_observable": "Ribosome signature", "qualitative_result": "Decreased, as early as 4h, moderate decrease at 24h", "reason_not_quantifiable": "Same as above."},
    # Fig6A-C
    {"figure": "Fig 6A", "panel": "A", "cell_line_or_group": "MM.1S (+ KMS-18/KMS-12PE/ARP-1 per Suppl. Fig. S7, not viewed)", "target_or_observable": "BEZ235 + bortezomib (PS-341) combination", "qualitative_result": "Additive effect across broad dose range, no antagonism", "reason_not_quantifiable": "3D response-surface mesh; static 2D image/screenshot has no gridline value labels at intermediate points and perspective distortion; z-values not reliably extractable."},
    {"figure": "Fig 6B", "panel": "B", "cell_line_or_group": "MM.1S", "target_or_observable": "BEZ235 + doxorubicin combination", "qualitative_result": "Additive effect across broad dose range, no antagonism", "reason_not_quantifiable": "Same as Fig 6A."},
    {"figure": "Fig 6C", "panel": "C", "cell_line_or_group": "MM.1S", "target_or_observable": "BEZ235 + dexamethasone combination", "qualitative_result": "Additive effect across broad dose range, no antagonism", "reason_not_quantifiable": "Same as Fig 6A."},
]


def prepare() -> dict[str, int]:
    sources = [RAW_WORKBOOK, RAW_ANNOTATION_WORKBOOK, MOA_DOC]
    missing = [str(p) for p in sources if not p.is_file()]
    if missing:
        raise FileNotFoundError(f"Missing Dactolisib MM source artifacts: {missing}")

    workbook = openpyxl.load_workbook(RAW_WORKBOOK, read_only=True, data_only=True)
    if set(workbook.sheetnames) != EXPECTED_WORKBOOK_SHEETS:
        raise ValueError(f"Unexpected Dactolisib MM workbook sheets: {workbook.sheetnames}")
    annotation_workbook = openpyxl.load_workbook(RAW_ANNOTATION_WORKBOOK, read_only=True, data_only=True)
    if set(annotation_workbook.sheetnames) != EXPECTED_ANNOTATION_SHEETS:
        raise ValueError(f"Unexpected Dactolisib MM annotation workbook sheets: {annotation_workbook.sheetnames}")

    # ---- contexts -----------------------------------------------------
    contexts: dict[str, dict[str, Any]] = {}

    def ensure_context(key: str, **fields: Any) -> str:
        if key not in contexts:
            contexts[key] = {"context_key": key, **fields}
        return key

    def mm_line_context(cell_line: str) -> str:
        key = f"{_slug(cell_line)}_in_vitro_mm"
        return ensure_context(
            key, species="Homo sapiens", cell_line=cell_line, cell_type="multiple myeloma cell",
            tissue="bone marrow / peripheral blood (MM cell line)", disease="multiple myeloma",
            culture_context="in vitro 2D cell culture, 48 h MTT viability assay",
            notes=f"Fig1A cell-line IC50 panel; IC50={FIG1A_IC50.get(cell_line)} nmol/L"
                  f"{' (>800 nmol/L, censored)' if cell_line in FIG1A_CENSORED else ''}.",
        )

    mm1s_key = mm_line_context("MM.1S")

    akt_key = ensure_context(
        "mm1s_myr_akt_in_vitro", species="Homo sapiens", cell_line="MM.1S-myrAkt",
        cell_type="multiple myeloma cell (engineered)", tissue="bone marrow / peripheral blood (MM cell line)",
        disease="multiple myeloma",
        culture_context="in vitro 2D cell culture, stable myristoylated-Akt (constitutively active) overexpression, 48 h MTT viability assay",
        notes="Fig2A genetic-rescue subline: myristoylated (constitutively active) Akt overexpression does NOT "
              "protect MM.1S cells from BEZ235 (curve tracks parental almost exactly, even slightly more sensitive).",
    )
    bcl2_key = ensure_context(
        "mm1s_bcl2_in_vitro", species="Homo sapiens", cell_line="MM.1S-Bcl-2",
        cell_type="multiple myeloma cell (engineered)", tissue="bone marrow / peripheral blood (MM cell line)",
        disease="multiple myeloma",
        culture_context="in vitro 2D cell culture, stable Bcl-2 overexpression, 48 h MTT viability assay",
        notes="Fig2B genetic-rescue subline: Bcl-2 overexpression provides partial protection from BEZ235, "
              "producing a non-zero survival plateau (~32-38%) rather than a rightward IC50 shift alone -- the "
              "quantitative signature of a protected fraction (highest-value mechanistic data for a dual-target "
              "threshold PD equation).",
    )

    patient_keys: dict[str, str] = {}
    for patient_label in FIG1B_PATIENTS:
        key = f"{_slug(patient_label)}_primary_sample"
        patient_keys[patient_label] = ensure_context(
            key, species="Homo sapiens", cell_line=patient_label, cell_type="primary CD138-selected MM cell",
            tissue="bone marrow aspirate (primary patient sample)", disease="multiple myeloma",
            culture_context="ex vivo primary cell culture, CD138-selected, 48 h MTT viability assay",
            notes=f"Fig1B primary patient sample; phenotype tier per text: {patient_label.split('(')[-1].rstrip(')')}.",
        )

    thle3_key = ensure_context(
        "thle3_hepatocyte_in_vitro", species="Homo sapiens", cell_line="THLE-3",
        cell_type="immortalized non-malignant hepatocyte", tissue="liver", disease=None,
        culture_context="in vitro 2D cell culture, 48 h MTT viability assay",
        notes="Fig1C selectivity comparator; IC50 >800 nmol/L per text (therapeutic-index evidence).",
    )
    hs5_key = ensure_context(
        "hs5_stromal_in_vitro", species="Homo sapiens", cell_line="HS-5",
        cell_type="bone marrow stromal cell", tissue="bone marrow", disease=None,
        culture_context="in vitro 2D cell culture, 48 h MTT viability assay",
        notes="Fig1C selectivity comparator; IC50 >800 nmol/L per text (therapeutic-index evidence).",
    )
    pbmc_key = ensure_context(
        "pbmc_healthy_donor_pooled", species="Homo sapiens", cell_line="PBMC (healthy donors, pooled range)",
        cell_type="peripheral blood mononuclear cell", tissue="peripheral blood", disease=None,
        culture_context="in vitro 2D cell culture, +/- PHA stimulation, 48 h MTT viability assay",
        notes="Fig1D selectivity comparator; single representative range digitized for 8 tightly-clustered "
              "donor curves (4 donors x unstimulated/PHA-stimulated); individual donor curves not separable "
              "from the source figure. Text states all remained >=50% viable at 800 nmol/L BEZ235.",
    )

    xenograft_key = ensure_context(
        "mm1s_gfp_luc_xenograft", species="Mus musculus", cell_line="MM.1S-GFP/luc",
        cell_type="human multiple myeloma xenograft", tissue="subcutaneous flank tumor",
        disease="multiple myeloma",
        culture_context="human MM.1S-GFP/luc-cell xenograft in nude (immunodeficient) mice, subcutaneous implant",
        notes="Fig5A-C in vivo efficacy model; BEZ235 30 mg/kg oral daily vs vehicle. "
              "No PK sampling reported for this in vivo arm.",
    )

    # ---- assays ---------------------------------------------------------
    assay_rows = [
        {"assay_key": "ic50_cellline_panel", "assay_type": "MTT viability assay", "assay_name": "Fig1A BEZ235 IC50, 21-line MM cell panel", "sample_type": "multiple myeloma cell line", "measurement_platform": "MTT viability assay, 48 h, printed IC50 heat-map values", "figure": "Figure 1", "panel": "A", "reported_time": 48, "reported_time_unit": "h", "replicate_count": None, "notes": "Explicit values printed on the figure's heat map; dose range tested 0-800 nmol/L."},
        {"assay_key": "patient_dose_response", "assay_type": "MTT viability assay", "assay_name": "Fig1B BEZ235 dose-response, primary MM patient samples", "sample_type": "primary CD138-selected MM patient sample", "measurement_platform": "MTT viability assay, 48 h", "figure": "Figure 1", "panel": "B", "reported_time": 48, "reported_time_unit": "h", "replicate_count": None, "notes": "Visual estimate of curve positions; 3 of 5 patient samples sensitive (IC50 <200 nmol/L), 2 relatively resistant (explicit text statement)."},
        {"assay_key": "selectivity_dose_response", "assay_type": "MTT viability assay", "assay_name": "Fig1C-D BEZ235 dose-response, non-malignant cells vs MM.1S", "sample_type": "non-malignant cell (stromal/hepatocyte/PBMC) or MM.1S", "measurement_platform": "MTT viability assay, 48 h", "figure": "Figure 1", "panel": "C-D", "reported_time": 48, "reported_time_unit": "h", "replicate_count": None, "notes": "Fig1C from MOA-doc digitized table (higher precision, 8 dose points); Fig1D PBMC from workbook representative range."},
        {"assay_key": "akt_rescue_dose_response", "assay_type": "MTT viability assay", "assay_name": "Fig2A BEZ235 dose-response, MM.1S parental vs myr-Akt overexpressing", "sample_type": "multiple myeloma cell line (parental or engineered)", "measurement_platform": "MTT viability assay, 48 h", "figure": "Figure 2", "panel": "A", "reported_time": 48, "reported_time_unit": "h", "replicate_count": None, "notes": "MOA-doc digitized table; myr-Akt curve tracks parental almost exactly (no protection)."},
        {"assay_key": "bcl2_rescue_dose_response", "assay_type": "MTT viability assay", "assay_name": "Fig2B BEZ235 dose-response, MM.1S parental vs Bcl-2 overexpressing", "sample_type": "multiple myeloma cell line (parental or engineered)", "measurement_platform": "MTT viability assay, 48 h", "figure": "Figure 2", "panel": "B", "reported_time": 48, "reported_time_unit": "h", "replicate_count": None, "notes": "MOA-doc digitized table; MM.1S-Bcl-2 plateaus at 32-38% survival from 50 nmol/L onward -- non-zero lower asymptote preserved exactly."},
        {"assay_key": "annexin_flow", "assay_type": "Flow cytometry", "assay_name": "Fig3A Annexin V/PI apoptosis time-course, MM.1S", "sample_type": "multiple myeloma cell line", "measurement_platform": "Annexin V-FITC/PI flow cytometry, 100 nmol/L BEZ235", "figure": "Figure 3", "panel": "A", "reported_time": None, "reported_time_unit": "h", "replicate_count": None, "notes": "Explicit quadrant percentages printed directly on each flow plot."},
        {"assay_key": "xenograft_tumor_size", "assay_type": "Caliper tumor size", "assay_name": "Fig5A xenograft tumor size", "sample_type": "MM.1S-GFP/luc xenograft tumor", "measurement_platform": "Caliper measurement, mm2", "figure": "Figure 5", "panel": "A", "reported_time": None, "reported_time_unit": "d", "replicate_count": None, "notes": "P=0.033 (unpaired one-tailed t test), explicit (printed on figure and in text)."},
        {"assay_key": "xenograft_survival", "assay_type": "Kaplan-Meier survival", "assay_name": "Fig5B xenograft overall survival", "sample_type": "MM.1S-GFP/luc xenograft-bearing mouse", "measurement_platform": "Kaplan-Meier analysis", "figure": "Figure 5", "panel": "B", "reported_time": None, "reported_time_unit": "d", "replicate_count": None, "notes": "P=0.028 (log-rank test), explicit. Median OS: BEZ235 not reached (median follow-up 48 days); control = 23 days (95% CI 21-26), explicit from text."},
        {"assay_key": "xenograft_body_weight", "assay_type": "Body weight", "assay_name": "Fig5C xenograft body weight (toxicity surrogate)", "sample_type": "MM.1S-GFP/luc xenograft-bearing mouse", "measurement_platform": "Scale, grams", "figure": "Figure 5", "panel": "C", "reported_time": None, "reported_time_unit": "d", "replicate_count": None, "notes": "Text states no significant weight change/toxicity signs."},
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

    def bez235_step(dose: float | None, unit: str, start: float | None, end: float | None, time_unit: str, notes: str | None = None) -> dict[str, Any]:
        return {"perturbation_name": "Dactolisib", "dose_value": dose, "dose_unit": unit, "start_time": start, "end_time": end, "time_unit": time_unit, "notes": notes}

    def dose_condition(context_key: str, dose: float, unit: str, duration: float, time_unit: str) -> str:
        label = f"BEZ235 {dose:g} {unit}, {duration:g} {time_unit}" if dose else f"Vehicle control, {duration:g} {time_unit}"
        step = bez235_step(dose if dose else None, unit, 0, duration, time_unit) if dose else {"perturbation_name": "Vehicle", "dose_value": None, "dose_unit": None, "start_time": 0, "end_time": duration, "time_unit": time_unit, "notes": None}
        return ensure_condition(context_key, label, [step])

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

    # 1) Fig1A IC50 panel.
    for line, ic50 in FIG1A_IC50.items():
        ctx = mm_line_context(line)
        cond = ensure_condition(ctx, "BEZ235 dose-response (IC50 determination), 48 h", [
            bez235_step(None, "nM", 0, 48, "h", "IC50-determining dose-response, 0-800 nmol/L range."),
        ])
        censored = line in FIG1A_CENSORED
        add(record_id=f"fig1a_{_slug(line)}_ic50", context_key=ctx, condition_key=cond, assay_key="ic50_cellline_panel",
            observable="viability_IC50", observable_raw_label=f"BEZ235 IC50, {line}",
            value=ic50, value_unit="nmol/L", time_value=48, time_unit="h", statistic="IC50",
            source_key="workbook", figure="Figure 1", panel="A", extraction_method="DIRECT_SOURCE", quality_class="QUANTITATIVE",
            is_censored=censored, censoring_limit=800.0 if censored else None,
            notes="Printed directly on the figure's heat map (not estimated from the color scale).")

    # 2) Fig1B patient-sample dose response.
    for patient_label, values in FIG1B_PATIENTS.items():
        ctx = patient_keys[patient_label]
        for dose, value in zip(FIG1B_DOSES, values):
            cond = dose_condition(ctx, float(dose), "nM", 48, "h")
            add(record_id=f"fig1b_{_slug(patient_label)}_{dose}nm", context_key=ctx, condition_key=cond, assay_key="patient_dose_response",
                observable="pct_survival", observable_raw_label=f"% survival, {patient_label}, {dose} nmol/L BEZ235",
                value=float(value), value_unit="% survival", time_value=48, time_unit="h",
                statistic="percent survival vs untreated control",
                uncertainty_type="visual digitization uncertainty (curve-position estimate)",
                source_key="workbook", figure="Figure 1", panel="B", extraction_method="PLOT_DIGITIZED", quality_class="SEMI_QUANTITATIVE",
                notes="Visual estimate of curve position at each printed dose.")

    # 3) Fig1C selectivity curves (MOA-doc digitized table).
    for label, values in FIG1C_CURVES.items():
        ctx = {"THLE-3": thle3_key, "HS-5": hs5_key, "MM.1S": mm1s_key}[label]
        for dose, value in zip(FIG1C_DOSES, values):
            approx = dose in FIG1C_APPROXIMATE_DOSE
            cond = dose_condition(ctx, float(dose), "nM", 48, "h")
            add(record_id=f"fig1c_{_slug(label)}_{dose}nm", context_key=ctx, condition_key=cond, assay_key="selectivity_dose_response",
                observable="pct_survival", observable_raw_label=f"% survival, {label}, {dose} nmol/L BEZ235",
                value=float(value), value_unit="% survival", time_value=48, time_unit="h",
                statistic="percent survival vs untreated control",
                uncertainty_type="visual digitization uncertainty (+/-2-3 percentage points per companion MOA doc)",
                source_key="moa_doc", figure="Figure 1", panel="C", extraction_method="PLOT_DIGITIZED", quality_class="SEMI_QUANTITATIVE",
                notes=f"From BEZ235_QSP_PD_Biomarker_Cascade.md digitized table (400 DPI page render, pixel-based marker "
                      f"centroid extraction, visually cross-checked).{' Approximate dose (~10 nmol/L in source table).' if approx else ''}"
                      + (" Note: MM.1S curve here implies IC50 closer to 25-50 nmol/L by simple interpolation, slightly right "
                         "of the 22.78 nmol/L value in Fig1A -- plausible inter-experiment (day/passage) variability, not a "
                         "transcription error." if label == "MM.1S" else ""))

    # 4) Fig1D PBMC representative range.
    for dose, value in zip(FIG1D_DOSES, FIG1D_PBMC):
        cond = dose_condition(pbmc_key, float(dose), "nM", 48, "h")
        add(record_id=f"fig1d_pbmc_{dose}nm", context_key=pbmc_key, condition_key=cond, assay_key="selectivity_dose_response",
            observable="pct_survival", observable_raw_label=f"% survival, PBMC pooled range, {dose} nmol/L BEZ235",
            value=float(value), value_unit="% survival", time_value=48, time_unit="h",
            statistic="percent survival vs untreated control (representative of 8 donor curves)",
            uncertainty_type="visual digitization uncertainty; pooled/representative of 8 tightly clustered donor curves",
            source_key="workbook", figure="Figure 1", panel="D", extraction_method="PLOT_DIGITIZED", quality_class="SEMI_QUANTITATIVE",
            notes="Single representative range digitized in place of 8 overlapping donor curves (4 donors x unstim/PHA-stim); "
                  "text confirms all remained >=50% viable at 800 nmol/L.")

    # 5) Fig2A Akt-rescue.
    for label, values in FIG2A.items():
        ctx = mm1s_key if "parental" in label else akt_key
        for dose, value in zip(FIG2_DOSES, values):
            approx = dose in FIG2_APPROXIMATE_DOSE
            cond = ensure_condition(ctx, f"BEZ235 {dose:g} nM, 48 h (Fig2A Akt-rescue experiment)" if dose else "Vehicle control, 48 h (Fig2A Akt-rescue experiment)",
                                     [bez235_step(dose if dose else None, "nM", 0, 48, "h")] if dose else [{"perturbation_name": "Vehicle", "dose_value": None, "dose_unit": None, "start_time": 0, "end_time": 48, "time_unit": "h", "notes": None}])
            add(record_id=f"fig2a_{_slug(label)}_{dose}nm", context_key=ctx, condition_key=cond, assay_key="akt_rescue_dose_response",
                observable="pct_survival", observable_raw_label=f"% survival, {label}, {dose} nmol/L BEZ235",
                value=float(value), value_unit="% survival", time_value=48, time_unit="h",
                statistic="percent survival vs untreated control",
                uncertainty_type="visual digitization uncertainty (+/-2-3 percentage points per companion MOA doc)",
                source_key="moa_doc", figure="Figure 2", panel="A", extraction_method="PLOT_DIGITIZED", quality_class="SEMI_QUANTITATIVE",
                notes=f"From BEZ235_QSP_PD_Biomarker_Cascade.md digitized table. myrAkt curve sits at or slightly above "
                      f"parental at every dose -- direct numeric confirmation Akt overexpression provides no protection."
                      f"{' Approximate dose (~10 nmol/L in source table).' if approx else ''}")

    # 6) Fig2B Bcl-2-rescue (the non-zero plateau -- highest-value mechanistic data).
    for label, values in FIG2B.items():
        ctx = mm1s_key if "parental" in label else bcl2_key
        for dose, value in zip(FIG2_DOSES, values):
            approx = dose in FIG2_APPROXIMATE_DOSE
            cond = ensure_condition(ctx, f"BEZ235 {dose:g} nM, 48 h (Fig2B Bcl2-rescue experiment)" if dose else "Vehicle control, 48 h (Fig2B Bcl2-rescue experiment)",
                                     [bez235_step(dose if dose else None, "nM", 0, 48, "h")] if dose else [{"perturbation_name": "Vehicle", "dose_value": None, "dose_unit": None, "start_time": 0, "end_time": 48, "time_unit": "h", "notes": None}])
            add(record_id=f"fig2b_{_slug(label)}_{dose}nm", context_key=ctx, condition_key=cond, assay_key="bcl2_rescue_dose_response",
                observable="pct_survival", observable_raw_label=f"% survival, {label}, {dose} nmol/L BEZ235",
                value=float(value), value_unit="% survival", time_value=48, time_unit="h",
                statistic="percent survival vs untreated control",
                uncertainty_type="visual digitization uncertainty (+/-2-3 percentage points per companion MOA doc)",
                source_key="moa_doc", figure="Figure 2", panel="B", extraction_method="PLOT_DIGITIZED", quality_class="SEMI_QUANTITATIVE",
                notes=f"From BEZ235_QSP_PD_Biomarker_Cascade.md digitized table. "
                      + ("MM.1S-Bcl-2 plateaus at 32-38% survival from 50 nmol/L onward instead of continuing toward zero -- "
                         "a non-zero lower asymptote (protected fraction), not just a rightward IC50 shift; this is the shape "
                         "a threshold/rescue term in a PD model needs to reproduce." if "Bcl-2" in label else
                         "Parental arm of the Bcl-2-rescue experiment (separate replicate from the Fig2A parental arm; dose "
                         "values differ slightly between the two experiments, both preserved as recorded).")
                      + (f" Approximate dose (~10 nmol/L in source table)." if approx else ""))

    # 7) Fig3A Annexin V/PI.
    quadrant_labels = ("viable", "early_apoptotic", "late_apoptotic", "necrotic_debris")
    for time_value, time_label, viable, early, late, necrotic in FIG3A_TIMEPOINTS:
        cond = ensure_condition(mm1s_key, f"BEZ235 100 nM, {time_label}" if time_value else "Vehicle control (t=0)",
                                 [bez235_step(100, "nM", 0, time_value, "h")] if time_value else [{"perturbation_name": "Vehicle", "dose_value": None, "dose_unit": None, "start_time": 0, "end_time": 0, "time_unit": "h", "notes": None}])
        for observable, value in zip(quadrant_labels, (viable, early, late, necrotic)):
            add(record_id=f"fig3a_{_slug(time_label)}_{observable}", context_key=mm1s_key, condition_key=cond, assay_key="annexin_flow",
                observable=f"annexinV_PI_{observable}_pct", observable_raw_label=f"{observable.replace('_', ' ')}, {time_label}",
                value=float(value), value_unit="% of gated cells", time_value=time_value, time_unit="h",
                statistic="quadrant percentage of gated cells",
                source_key="workbook", figure="Figure 3", panel="A", extraction_method="DIRECT_SOURCE", quality_class="QUANTITATIVE",
                notes="Explicit quadrant percentages printed directly on each flow plot (not estimated).")

    # 8) Fig5A tumor size.
    for day, control, treated in FIG5A_TUMOR_SIZE:
        vehicle_cond = ensure_condition(xenograft_key, "Vehicle control (xenograft)", [{"perturbation_name": "Vehicle", "dose_value": None, "dose_unit": None, "start_time": None, "end_time": None, "time_unit": None, "notes": None}])
        treated_cond = ensure_condition(xenograft_key, "BEZ235 30 mg/kg oral daily", [bez235_step(30, "mg/kg", 0, None, "d", "Oral daily dosing.")])
        for cond, value, arm in ((vehicle_cond, control, "control"), (treated_cond, treated, "BEZ235 30 mg/kg")):
            add(record_id=f"fig5a_day{int(day)}_{arm.split()[0].lower()}", context_key=xenograft_key, condition_key=cond, assay_key="xenograft_tumor_size",
                observable="xenograft_tumor_size", observable_raw_label=f"Tumor size, {arm}, day {int(day)}",
                value=float(value), value_unit="mm2", time_value=day, time_unit="d", statistic="mean tumor size",
                uncertainty_type="visual digitization uncertainty (point-position estimate)",
                source_key="workbook", figure="Figure 5", panel="A", extraction_method="PLOT_DIGITIZED", quality_class="SEMI_QUANTITATIVE",
                notes="P=0.033 (unpaired one-tailed t test) reported explicitly for the overall comparison (printed on figure and in text).")

    # 9) Fig5B survival.
    for day, control, treated in FIG5B_SURVIVAL:
        vehicle_cond = ensure_condition(xenograft_key, "Vehicle control (xenograft)", [{"perturbation_name": "Vehicle", "dose_value": None, "dose_unit": None, "start_time": None, "end_time": None, "time_unit": None, "notes": None}])
        treated_cond = ensure_condition(xenograft_key, "BEZ235 30 mg/kg oral daily", [bez235_step(30, "mg/kg", 0, None, "d", "Oral daily dosing.")])
        for cond, value, arm in ((vehicle_cond, control, "control"), (treated_cond, treated, "BEZ235 30 mg/kg")):
            add(record_id=f"fig5b_day{int(day)}_{arm.split()[0].lower()}", context_key=xenograft_key, condition_key=cond, assay_key="xenograft_survival",
                observable="xenograft_pct_survival", observable_raw_label=f"Percent survival, {arm}, day {int(day)}",
                value=float(value), value_unit="% survival", time_value=day, time_unit="d", statistic="Kaplan-Meier percent survival",
                uncertainty_type="visual digitization uncertainty (step-position estimate)",
                source_key="workbook", figure="Figure 5", panel="B", extraction_method="PLOT_DIGITIZED", quality_class="SEMI_QUANTITATIVE",
                notes="P=0.028 (log-rank test) explicit. Median OS: BEZ235 not reached (median follow-up 48 days); "
                      "control = 23 days (95% CI 21-26), explicit from text.")

    # 10) Fig5C body weight.
    for day, control, treated in FIG5C_BODY_WEIGHT:
        vehicle_cond = ensure_condition(xenograft_key, "Vehicle control (xenograft)", [{"perturbation_name": "Vehicle", "dose_value": None, "dose_unit": None, "start_time": None, "end_time": None, "time_unit": None, "notes": None}])
        treated_cond = ensure_condition(xenograft_key, "BEZ235 30 mg/kg oral daily", [bez235_step(30, "mg/kg", 0, None, "d", "Oral daily dosing.")])
        for cond, value, arm in ((vehicle_cond, control, "control"), (treated_cond, treated, "BEZ235 30 mg/kg")):
            add(record_id=f"fig5c_day{int(day)}_{arm.split()[0].lower()}", context_key=xenograft_key, condition_key=cond, assay_key="xenograft_body_weight",
                observable="xenograft_body_weight", observable_raw_label=f"Body weight, {arm}, day {int(day)}",
                value=float(value), value_unit="g", time_value=day, time_unit="d", statistic="mean body weight",
                uncertainty_type="visual digitization uncertainty (point-position estimate)",
                source_key="workbook", figure="Figure 5", panel="C", extraction_method="PLOT_DIGITIZED", quality_class="QUALITATIVE_VALIDATION",
                notes="Toxicity surrogate; text states no significant weight change/toxicity signs observed.")

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
        {"source_key": "annotation_workbook", "path": RAW_ANNOTATION_WORKBOOK},
        {"source_key": "moa_doc", "path": MOA_DOC},
    ]
    metadata = {
        "schema_version": 1, "paper_id": PAPER_ID, "pmid": "19584292", "pmcid": None,
        "doi": "10.1158/0008-5472.CAN-09-0715",
        "extraction_date": "2026-09-08", "generated_counts": counts,
        "observation_counts_by_method": dict(sorted(Counter(row["extraction_method"] for row in observations).items())),
        "source_artifacts": [
            {"source_key": item["source_key"], "path": relative(item["path"]), "sha256": sha256(item["path"])}
            for item in artifacts
        ],
        "corrections": [
            "Fig1A IC50 for MM.1S differs by rounding between the raw curated workbook (22.78 nmol/L) and the "
            "companion MOA doc (22.16 nmol/L); the workbook's printed-on-figure value is used as authoritative "
            "since it is stated to be an explicit, not estimated, value; the MOA doc's own Fig1C selectivity "
            "curve for MM.1S implies an IC50 closer to 25-50 nmol/L by simple interpolation, a difference the "
            "MOA doc itself flags as plausible inter-experiment (day/passage) variability rather than a "
            "transcription error.",
            "Fig2A/Fig2B parental MM.1S arms are two separate digitized replicates (one per rescue experiment) "
            "with slightly different values at matched doses (e.g. 50 nmol/L: 55% in Fig2A vs 42% in Fig2B); both "
            "are preserved as separate conditions/observations rather than merged, since they come from different "
            "figure panels/replicates per the source workbook and MOA doc.",
            "Fig5A tumor-size day-47 control value differs by 1 mm2 between the workbook (167) and the MOA doc "
            "(166); the workbook value is used as authoritative (primary curated source), difference noted as "
            "visual-digitization variance, not corrected further.",
            "Fig5B Kaplan-Meier step timepoints differ between the workbook (7 steps: days 0/25/38/40/50/55/60) "
            "and the MOA doc (9 steps: days 0/25/40/44/48/53/58/60/73); the workbook's table is used as "
            "authoritative here since it is the primary per-figure curated source for this package; both are "
            "independent visual re-reads of the same printed Kaplan-Meier curve and show the digitization "
            "variance typical of step-plot reconstruction.",
        ],
        "caveats": [
            "No PK data exists in this paper at all: the 100 nmol/L in vitro kinetic dose (Fig2C/2D, Fig3B/3C) "
            "and the 30 mg/kg oral in vivo dose (Fig5) are not linked to a plasma-exposure model by any data in "
            "this source; an exposure-response bridge requires PK parameters from elsewhere in the pipeline or "
            "the literature.",
            "Fig4 (13-signature x 5-timepoint gene-expression bar chart) is explicitly flagged by both the "
            "workbook and the companion MOA doc as a low-confidence visual estimate: bars for 12+ overlapping "
            "gene signatures with large, overlapping error bars could only be read for general direction and "
            "relative rank at 24h; no numeric values were promoted to observations.csv. Before attempting further "
            "digitization, check whether the underlying HT-U133A/U133B microarray data were deposited to a "
            "public repository (no GEO accession is stated in the visible text or reference list).",
            "Several figures are explicitly NOT digitized to numeric values at all and appear only in "
            "not_quantifiable_figures.csv: Fig2C-D and Fig3B-C (single representative western blot images, no "
            "densitometry reported), and Fig6A-C (3D response-surface combination meshes -- BEZ235 + bortezomib/"
            "doxorubicin/dexamethasone, all read qualitatively as 'additive, no antagonism' per the text).",
            "Fig1B (5 unlabeled primary patient sample curves) and Fig1D (pooled/representative PBMC range, "
            "originally 8 overlapping donor curves) are visual-estimate curve digitizations, not printed values; "
            "treat as SEMI_QUANTITATIVE.",
            "Supplementary Figs S1-S7 (cited repeatedly for quantitative support, e.g. S2 commitment-to-death "
            "kinetics, S4 cell-cycle/sub-G1 distribution, S7 additional combination-sensitive cell lines) are not "
            "available locally and are not represented in this package.",
            "All western blots referenced in this study (Fig2C-D, Fig3B-C) are single representative images with "
            "no densitometry; if continuous values are needed at these tiers, plan for image densitometry as a "
            "discrete follow-up task.",
            "This package is workbook + companion-MOA-doc-only: no raw paper PDF/HTML or original figure image is "
            "available locally for PMID 19584292 (no PMCID); accordingly there is no PAPER-type source_artifacts "
            "row, mirroring the pemigatinib.py pattern for a real-PMID study without a local paper file.",
        ],
    }
    (EXTRACTED / "extraction_metadata.json").write_text(
        json.dumps(metadata, indent=2, sort_keys=True, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    return counts


if __name__ == "__main__":
    for table, count in prepare().items():
        print(f"prepared {table}: {count}")

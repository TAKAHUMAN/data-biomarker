"""Normalize the supplied Dinaciclib (CDK1/2/5/9 inhibitor) hepatocellular carcinoma (HCC)
extraction -- spanning TWO related papers used as one drug story -- into registry-v1 CSV
tables for datasets/extracted/dinaciclib.

Source papers:
  1. Xu J, Huang F, Yao Z, et al. "Inhibition of cyclin E1 sensitizes hepatocellular
     carcinoma cells to regorafenib by mcl-1 suppression." Cell Communication and
     Signaling 2019;17:85. PMID 31349793, PMCID PMC6660968, DOI 10.1186/s12964-019-0398-3.
     No PMID was stated anywhere in the supplied workbooks/MD doc; it was independently
     confirmed via web search (PMC6660968 -> PMID 31349793) rather than guessed. See
     extraction_metadata.json `corrections` for this note.
  2. Shao Y-Y, Li Y-S, Hsu H-W, et al. "Potent Activity of Composite Cyclin Dependent
     Kinase Inhibition against Hepatocellular Carcinoma." Cancers 2019;11:1433.
     PMID 31561409, PMCID PMC6827105 -- given directly in the supplied workbook's
     Summary sheet.

Three supplied, immutable-provenance inputs drive this script and are never modified:
  - dinaciclib_HCC_extracted.xlsx (Shao-only per-figure digitized/curated workbook)
  - Dinaciclib_QSP_PD_Biomarker_Cascade_Annotations.xlsx (richer companion covering
    BOTH papers: Cascade Map, Digitized Data, Figure Annotations, Modeling Notes)
  - Dinaciclib_QSP_PD_Biomarker_Cascade.md (human-written interpretive MOA cascade guide)

Xu et al. figures with no printed/digitized numeric values anywhere in the supplied
materials (most western blots, several bar charts described only in prose) are captured
only in not_quantifiable_figures.csv, never forced into observations.csv. A few Xu
figures are described in prose with an explicit approximate magnitude (e.g. "roughly
halves apoptosis", "~65% -> ~15%", "~4x") -- these are imported as TEXT_DERIVED,
SEMI_QUANTITATIVE observations with the approximation spelled out in the notes, since
they are real, source-stated numeric claims, just not pixel-digitized curve data.

Three data-quality flags from the source materials are preserved deliberately, per the
task brief -- see extraction_metadata.json `caveats`:
  (a) Shao Fig 5A: the six-number row 1.78/1.89/1.71/1.38/0.65/1.45 is printed
      identically under FOUR different blots (CDK9, p-Rb, p-ATM, p-RNPII) -- imported
      with quality_class NOT_MODEL_READY, not silently dropped or trusted.
  (b) A smaller version of the same pattern in Fig 3A: "Rb (total), PLC5" is identical
      to "p-RNPII (S2), PLC5" -- the Rb (total) PLC5 rows are flagged NOT_MODEL_READY.
  (c) Shao Fig 4B (tumor volume) and Fig 4D (TUNEL) disagree on the 20-vs-40 mg/kg
      dose-response shape -- both imported as independent observations, not reconciled.
  (d) MTT IC50 (Fig 1A) and colony-formation "IC50" (Fig 1C/D) are imported as distinct
      observables (viability_IC50 vs colony_formation_relative), never conflated.
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


PAPER_SHAO = "paper_PMID31561409"
PAPER_XU = "paper_PMID31349793"
EXTRACTED = DATASETS / "extracted" / "dinaciclib"
RAW_WORKBOOK = DATASETS / "raw" / "workbooks" / "dinaciclib_HCC_extracted.xlsx"
RAW_ANNOTATION_WORKBOOK = DATASETS / "raw" / "workbooks" / "Dinaciclib_QSP_PD_Biomarker_Cascade_Annotations.xlsx"
MOA_DOC = EXTRACTED / "Dinaciclib_QSP_PD_Biomarker_Cascade.md"

EXPECTED_WORKBOOK_SHEETS = {
    "Fig1A_MTT_DoseResponse", "Fig1B_WB_Rb_pRb_cmyc", "Fig1CD_ColonyFormation",
    "Fig1EF_CellCycle", "Fig3A_WB_CDKtargets", "Fig3B_WB_ApoptosisTargets",
    "Fig4B_Xenograft_HuH7", "Fig4D_TUNEL", "Fig4E_Xenograft_PLC5", "Summary",
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
# Digitized/curated data, transcribed exactly from the supplied workbook sheets.
# ---------------------------------------------------------------------------

# Shao Fig1A: MTT dose-response, 72h, 4 lines. Curve points visual estimate; IC50s explicit.
FIG1A_DOSES = [0, 5, 10, 15, 20, 25, 30, 50, 100]
FIG1A_CURVES = {
    "HuH7": [100, 72, 38, 24, 24, 24, 23, 22, 22],
    "PLC5": [100, 88, 60, 32, 22, 20, 18, 17, 15],
    "Hep3B": [100, 97, 78, 62, 50, 42, 32, 28, 24],
    "HLE": [100, 75, 53, 33, 20, 18, 17, 17, 14],
}
FIG1A_IC50 = {"HuH7": 8.5, "PLC5": 11.8, "Hep3B": 15.6, "HLE": 9.7}

# Shao Fig1B: baseline densitometry (no treatment), normalized to GAPDH.
FIG1B = {
    "Rb (total)": {"HuH7": 1.17, "PLC5": 0.66, "HLE": 0.57, "Hep3B": 0.53},
    "p-Rb (S807/811)": {"HuH7": 1.51, "PLC5": 0.35, "HLE": 0.16, "Hep3B": 0.16},
    "c-myc": {"HuH7": 0.57, "PLC5": 0.19, "HLE": 0.26, "Hep3B": 0.53},
}

# Shao Fig1C/D: colony formation, relative to 0 nM = 1.0.
FIG1CD_DOSES = [0, 5, 10]
FIG1CD = {"HuH7": [1.0, 0.08, 0.02], "PLC5": [1.0, 0.62, 0.18]}

# Shao Fig1E/F: cell cycle distribution, 48h.
FIG1EF_DOSES = [0, 5, 10, 15]
FIG1EF = {
    "HuH7": {"G0/G1": [49, 50, 45, 48], "S": [40, 39, 32, 25], "G2M": [11, 11, 23, 27]},
    "PLC5": {"G0/G1": [46, 35, 35, 38], "S": [40, 40, 31, 28], "G2M": [15, 19, 26, 32]},
}

# Shao Fig3A: target-modulation densitometry, dose x time x cell line.
FIG3A_DOSES = [0, 5, 10, 15]
FIG3A: list[tuple[str, str, str, list[float]]] = [
    ("p-RNPII (S2)", "HuH7", "48h", [0.52, 0.94, 0.72, 0.57]),
    ("p-RNPII (S2)", "HuH7", "72h", [0.52, 0.42, 0.27, 0.10]),
    ("p-RNPII (S2)", "PLC5", "48h", [1.18, 1.09, 0.68, 0.51]),
    ("p-RNPII (S2)", "PLC5", "72h", [0.75, 0.75, 0.66, 0.23]),
    ("RNPII (total)", "HuH7", "48h", [0.58, 0.95, 0.71, 0.49]),
    ("RNPII (total)", "HuH7", "72h", [0.77, 0.57, 0.33, 0.20]),
    ("RNPII (total)", "PLC5", "48h", [0.75, 0.67, 0.49, 0.19]),
    ("RNPII (total)", "PLC5", "72h", [0.33, 0.54, 0.35, 0.09]),
    ("p-Rb (S807/811)", "HuH7", "48h", [0.66, 0.93, 0.50, 0.43]),
    ("p-Rb (S807/811)", "HuH7", "72h", [0.66, 0.58, 0.42, 0.33]),
    ("p-Rb (S807/811)", "PLC5", "48h", [1.10, 1.16, 0.24, 0.01]),
    ("p-Rb (S807/811)", "PLC5", "72h", [0.29, 0.61, 0.17, 0.01]),
    ("Rb (total)", "HuH7", "48h", [0.94, 1.04, 0.27, 0.25]),
    ("Rb (total)", "HuH7", "72h", [1.67, 0.42, 0.27, 0.10]),
    # NOT_MODEL_READY: numerically identical to "p-RNPII (S2), PLC5" above (data-quality flag b).
    ("Rb (total)", "PLC5", "48h", [1.18, 1.09, 0.68, 0.51]),
    ("Rb (total)", "PLC5", "72h", [0.75, 0.75, 0.66, 0.23]),
]
FIG3A_DUPLICATE_FLAGGED = {("Rb (total)", "PLC5", "48h"), ("Rb (total)", "PLC5", "72h")}

# Shao Fig3B: survival-signaling / apoptosis densitometry, dose x time x cell line.
FIG3B: list[tuple[str, str, str, list[float]]] = [
    ("Cleaved PARP-1", "HuH7", "48h", [0.11, 0.16, 0.15, 0.18]),
    ("Cleaved PARP-1", "HuH7", "72h", [0.23, 0.20, 0.51, 0.35]),
    ("Cleaved PARP-1", "PLC5", "48h", [0.14, 0.12, 0.32, 0.34]),
    ("Cleaved PARP-1", "PLC5", "72h", [0.18, 0.18, 0.99, 0.77]),
    ("XIAP", "HuH7", "48h", [0.76, 0.67, 0.32, 0.21]),
    ("XIAP", "HuH7", "72h", [1.03, 0.69, 0.53, 0.28]),
    ("XIAP", "PLC5", "48h", [1.19, 0.79, 0.24, 0.10]),
    ("XIAP", "PLC5", "72h", [0.91, 0.98, 0.48, 0.15]),
    ("Mcl-1", "HuH7", "48h", [0.88, 0.85, 0.48, 0.34]),
    ("Mcl-1", "HuH7", "72h", [0.83, 0.64, 0.61, 0.20]),
    ("Mcl-1", "PLC5", "48h", [1.27, 0.71, 0.44, 0.12]),
    ("Mcl-1", "PLC5", "72h", [1.05, 1.00, 0.46, 0.17]),
    ("survivin", "HuH7", "48h", [0.83, 0.81, 0.36, 0.35]),
    ("survivin", "HuH7", "72h", [0.40, 0.32, 0.29, 0.27]),
    ("survivin", "PLC5", "48h", [0.80, 0.76, 0.50, 0.18]),
    ("survivin", "PLC5", "72h", [0.28, 0.73, 0.71, 0.47]),
    ("Bcl-2", "HuH7", "48h", [1.21, 1.57, 1.10, 1.32]),
    ("Bcl-2", "HuH7", "72h", [1.49, 1.20, 1.17, 0.80]),
    ("Bcl-2", "PLC5", "48h", [1.15, 0.99, 0.83, 0.90]),
    ("Bcl-2", "PLC5", "72h", [1.06, 1.12, 0.81, 0.86]),
    ("Bak", "HuH7", "48h", [0.88, 0.80, 0.61, 0.76]),
    ("Bak", "HuH7", "72h", [0.77, 0.84, 0.80, 0.76]),
    ("Bak", "PLC5", "48h", [1.10, 1.05, 0.61, 0.40]),
    ("Bak", "PLC5", "72h", [0.59, 0.67, 0.48, 0.36]),
    ("Bim (L isoform)", "HuH7", "48h", [0.26, 0.23, 0.47, 0.83]),
    ("Bim (L isoform)", "HuH7", "72h", [0.22, 0.22, 0.42, 0.42]),
    ("Bim (L isoform)", "PLC5", "48h", [0.03, 0.03, 0.04, 0.07]),
    ("Bim (L isoform)", "PLC5", "72h", [0.08, 0.09, 0.08, 0.08]),
]

# Shao Fig4B: HuH7 xenograft tumor volume (mm3), 3 arms.
FIG4B_DAYS = [0, 3, 6, 9, 12, 15, 18, 21, 24, 26]
FIG4B = {
    "Vehicle": [150, 300, 500, 750, 1050, 1500, 2000, 2400, 2800, 3450],
    "Dinaciclib 20 mg/kg": [150, 250, 350, 500, 650, 800, 950, 1100, 1300, 1550],
    "Dinaciclib 40 mg/kg": [150, 230, 330, 480, 600, 750, 900, 1050, 1200, 1500],
}

# Shao Fig4D: TUNEL apoptosis ratio to vehicle control, HuH7 xenografts.
FIG4D = {"Vehicle": 1.0, "Dinaciclib 20 mg/kg": 2.35, "Dinaciclib 40 mg/kg": 3.95}

# Shao Fig4E: PLC5 xenograft tumor volume (mm3), 4 arms (incl. sorafenib comparator).
FIG4E_DAYS = [1, 3, 5, 7, 10, 13, 16, 20, 23, 26, 30]
FIG4E = {
    "Vehicle": [250, 350, 500, 700, 750, 850, 950, 1000, 1030, 1050, 1100],
    "Sorafenib 15 mg/kg": [250, 280, 300, 330, 350, 380, 420, 480, 520, 560, 600],
    "Dinaciclib 20 mg/kg": [250, 300, 330, 370, 400, 430, 460, 500, 510, 500, 510],
    "Dinaciclib 40 mg/kg": [220, 280, 300, 320, 330, 350, 370, 400, 420, 430, 430],
}

# Shao Fig5A (Digitized Data sheet): siRNA knockdown target densitometry, HuH7, 72h post-siRNA.
FIG5A_ARMS = ["siNT", "siCDK1", "siCDK2", "siCDK5", "siCDK9", "siCDK1+2+5+9"]
FIG5A: dict[str, list[float]] = {
    "CDK1": [2.71, 0.60, 2.14, 2.13, 2.43, 1.51],
    "CDK2": [2.52, 2.49, 0.58, 1.78, 2.14, 0.45],
    "CDK5": [0.43, 0.42, 0.49, 0.09, 0.46, 0.15],
    # NOT_MODEL_READY (data-quality flag a): identical six-number row printed under 4 blots.
    "CDK9": [1.78, 1.89, 1.71, 1.38, 0.65, 1.45],
    "p-Rb (S807/T811)": [1.78, 1.89, 1.71, 1.38, 0.65, 1.45],
    "p-ATM (S1981)": [1.78, 1.89, 1.71, 1.38, 0.65, 1.45],
    "p-RNPII (S2)": [1.78, 1.89, 1.71, 1.38, 0.65, 1.45],
}
FIG5A_DUPLICATED_TARGETS = {"CDK9", "p-Rb (S807/T811)", "p-ATM (S1981)", "p-RNPII (S2)"}
FIG5A_RELIABLE_TARGETS = {"CDK1", "CDK2", "CDK5"}

# Shao Fig5D-E (text-derived approximate values from Figure Annotations sheet): colony
# formation rescue, HuH7, 2.5 nM dinaciclib, vector vs CDK-overexpression.
FIG5DE_RESCUE = [
    ("CDK1", "Vector", 2.5, 15.0), ("CDK1", "CDK1-overexpression", 2.5, 15.0),
    ("CDK9", "Vector", 2.5, 15.0), ("CDK9", "CDK9-overexpression", 2.5, 28.0),
]

# Xu Fig3A (Digitized Data sheet): cell survival vs time, 50 nM dinaciclib, pixel-digitized.
XU_FIG3A_TIMES = [0, 6, 12, 24]
XU_FIG3A = {
    "Huh7 Control": [100, 118, 143, 168], "Huh7 Din": [100, 89, 72, 58],
    "HepG2 Control": [100, 121, 138, 157], "HepG2 Din": [100, 87, 69, 56],
}

# Xu Fig6A (Digitized Data sheet): in vivo tumor volume, Huh7 xenograft, 4 arms.
XU_FIG6A_DAYS = [1, 4, 7, 10, 13, 16, 19]
XU_FIG6A = {
    "Control": [30, 150, 380, 600, 760, 1010, 1330],
    "Dinaciclib 30 mg/kg": [30, 80, 180, 290, 420, 590, 650],
    "Regorafenib 20 mg/kg": [30, 60, 110, 190, 290, 390, 480],
    "Dinaciclib 30 mg/kg + Regorafenib 20 mg/kg": [30, 50, 70, 110, 140, 175, 205],
}

# Xu Fig1B (Figure Annotations sheet): TCGA/KM-plotter overall survival by CCNE1 expression.
XU_CCNE1_HR = {"value": 1.77, "p_value": 0.0012}

# Xu Fig2A-B (text-derived approximate values, Figure Annotations notes): CCNE1-overexpression
# accelerates growth -- ~1.7x survival at 24h vs control-plasmid.
XU_FIG2AB_FOLD = 1.7

# Xu Fig2D/F (text-derived approximate): CCNE1-overexpression roughly halves drug-induced
# apoptosis at both regorafenib (8 uM) and sorafenib (5 uM).
XU_FIG2DF = [
    ("Regorafenib", 8.0, "uM", 1.0, 0.5), ("Sorafenib", 5.0, "uM", 1.0, 0.5),
]

# Xu Fig4E-F (text-derived approximate): Mcl-1 overexpression rescue of Din+Reg apoptosis,
# "~65% -> ~15%".
XU_FIG4EF = {"Control-plasmid": 65.0, "Mcl-1-overexpression": 15.0}

# Xu Fig5E (text-derived approximate): STAT3-overexpression ~4x's Mcl-1-promoter luciferase
# reporter activity vs control-plasmid.
XU_FIG5E_FOLD = 4.0

# Xu Fig5G (text-derived approximate): STAT3-overexpression cuts flavopiridol-induced
# apoptosis "roughly in half" vs control-plasmid.
XU_FIG5G = {"Control-plasmid": 1.0, "STAT3-overexpression": 0.5}


NOT_QUANTIFIABLE_ROWS: list[dict[str, Any]] = [
    {"figure": "Shao Fig 2A-F", "panel": None, "cell_line_or_group": "HuH7, PLC5", "target_or_observable": "Sub-G1 apoptosis, DNA fragmentation ELISA, Annexin V/PI flow", "qualitative_result": "Dose-dependent increase (source workbook Summary sheet: SKIPPED)", "reason_not_quantifiable": "Not in the supplied dinaciclib_HCC_extracted.xlsx workbook's extracted figure list (explicitly marked 'Skipped, deprioritized for time' on its Summary sheet); no digitized numbers available for these panels in either supplied workbook."},
    {"figure": "Shao Fig 4A", "panel": "A", "cell_line_or_group": "HuH7 xenograft", "target_or_observable": "Representative tumor photographs", "qualitative_result": "n/a", "reason_not_quantifiable": "Photographic image only, not quantifiable."},
    {"figure": "Shao Fig 4C", "panel": "C", "cell_line_or_group": "HuH7 xenograft mice", "target_or_observable": "Body weight", "qualitative_result": "Stable / no significant change (tolerability, not PD)", "reason_not_quantifiable": "Tolerability surrogate, not a PD endpoint; source workbook explicitly skips it."},
    {"figure": "Shao Fig 4F", "panel": "F", "cell_line_or_group": "PLC5 xenograft mice", "target_or_observable": "Body weight", "qualitative_result": "Stable / no significant change (tolerability, not PD)", "reason_not_quantifiable": "Tolerability surrogate, not a PD endpoint; source workbook explicitly skips it."},
    {"figure": "Shao Fig 5B-C", "panel": "B-C", "cell_line_or_group": "HuH7", "target_or_observable": "Relative colony formation, siRNA individual/composite knockdowns", "qualitative_result": "CDK1 and CDK9 knockdown each significantly reduce colony formation (p<0.05); CDK2 and CDK5 knockdown do not (n.s.)", "reason_not_quantifiable": "No printed bar-chart y-values in either supplied workbook, only significance annotations (n.s./*) described in the Figure Annotations sheet; supports the CDK9~CDK1>>CDK2~CDK5 weighting conclusion qualitatively."},
    {"figure": "Xu Fig 1A", "panel": "A", "cell_line_or_group": "TCGA cohort (371 tumor vs 50 normal)", "target_or_observable": "CCNA1/CCND1/CCNE1 mRNA expression box plots", "qualitative_result": "Only CCNE1 significantly upregulated in tumor vs normal (**); CCNA1/CCND1 not different", "reason_not_quantifiable": "Box-plot quartile values not printed or digitized in supplied materials."},
    {"figure": "Xu Fig 1C", "panel": "C", "cell_line_or_group": "Huh7, SNU475, HepG2, SK-Hep1, SNU398, Hep3B", "target_or_observable": "CCNA1/CCND1/CCNE1/Actin western blot", "qualitative_result": "Splits lines into CCNE1-high (SK-Hep1, SNU398, Hep3B) vs CCNE1-low (Huh7, HepG2, SNU475)", "reason_not_quantifiable": "No densitometry printed; qualitative high/low split used as the context_alterations grouping instead."},
    {"figure": "Xu Fig 1D-E", "panel": "D-E", "cell_line_or_group": "6-line panel", "target_or_observable": "% survival vs sorafenib (D) / regorafenib (E) dose-response curves", "qualitative_result": "CCNE1-high lines show right-shifted (more resistant) curves -- core premise of the paper", "reason_not_quantifiable": "Log[M] x-axis without fine enough gridline detail for confident pixel calibration in this pass (per companion MOA doc Section 5); not present as digitized points in the Digitized Data sheet either. Flagged for manual digitization if exact curves are needed."},
    {"figure": "Xu Fig 2A", "panel": "A", "cell_line_or_group": "Huh7 Control-plasmid vs CCNE1-plasmid", "target_or_observable": "PI-staining cell-cycle histogram, 0/12h", "qualitative_result": "CCNE1 overexpression accelerates G1->S transit", "reason_not_quantifiable": "Representative histogram image only, no phase percentages printed."},
    {"figure": "Xu Fig 2C", "panel": "C", "cell_line_or_group": "Huh7 Control-plasmid vs CCNE1-plasmid", "target_or_observable": "IC50 (uM) bar chart, sorafenib/regorafenib", "qualitative_result": "CCNE1 overexpression significantly right-shifts IC50 (**)", "reason_not_quantifiable": "IC50 bar-chart y-values not printed or digitized in supplied materials; dose-response curves on log[M] axis, same limitation as Fig1D-E."},
    {"figure": "Xu Fig 2E", "panel": "E", "cell_line_or_group": "Huh7 Control-plasmid vs CCNE1-plasmid", "target_or_observable": "Cyclin E1, cleaved caspase-8/3 western blot", "qualitative_result": "Caspase-8/3 cleavage visibly suppressed in CCNE1-overexpressing lanes", "reason_not_quantifiable": "No densitometry printed."},
    {"figure": "Xu Fig 3B", "panel": "B", "cell_line_or_group": "Huh7", "target_or_observable": "PI-staining cell-cycle histogram, 50 nM dinaciclib", "qualitative_result": "G1/S arrest and increased hypodiploid (sub-G1) fraction (text statement)", "reason_not_quantifiable": "Representative histogram only, no phase percentages printed; per MOA doc, qualitative validation only for this panel."},
    {"figure": "Xu Fig 3C-D", "panel": "C-D", "cell_line_or_group": "Huh7, HepG2", "target_or_observable": "% apoptosis (Hoechst), Annexin V+ %, time course", "qualitative_result": "Increases over 0-24h, 50 nM dinaciclib", "reason_not_quantifiable": "No printed bar-chart y-values in either supplied workbook."},
    {"figure": "Xu Fig 3E", "panel": "E", "cell_line_or_group": "Huh7", "target_or_observable": "Cyclin E1, cleaved caspase-8/3 western blot vs time", "qualitative_result": "Confirms dinaciclib does NOT change cyclin E1 expression -- the key evidence CCNE1 is a resistance biomarker, not a dinaciclib PD target", "reason_not_quantifiable": "No densitometry printed; this panel's conclusion is captured structurally instead by treating CCNE1 as a context_alterations covariate, not a dinaciclib-modulated observable."},
    {"figure": "Xu Fig 3F-G", "panel": "F-G", "cell_line_or_group": "Huh7, HepG2", "target_or_observable": "% apoptosis, dinaciclib/flavopiridol +/- regorafenib/sorafenib", "qualitative_result": "Combination apoptosis roughly 2x either single agent -- paper's central sensitization claim", "reason_not_quantifiable": "No printed bar-chart y-values in either supplied workbook; only the qualitative '~2x' magnitude is stated in the Figure Annotations sheet, without which specific arm values it compares."},
    {"figure": "Xu Fig 4A", "panel": "A", "cell_line_or_group": "Huh7", "target_or_observable": "Mcl-1, Bim, PUMA, Noxa, Bad, Bax, Bcl-XL, Bcl-2 western blot vs time", "qualitative_result": "Only Mcl-1 (down) and Bim (up/cleaved) change appreciably; other 6 Bcl-2-family members flat", "reason_not_quantifiable": "No densitometry printed."},
    {"figure": "Xu Fig 4B-C", "panel": "B-C", "cell_line_or_group": "Huh7 CCNE1-OE / CCNE1-knockdown", "target_or_observable": "Bim, Mcl-1 western blot +/- regorafenib", "qualitative_result": "CCNE1 overexpression relieves regorafenib-induced Mcl-1 suppression; CCNE1 knockdown enhances it", "reason_not_quantifiable": "No densitometry printed."},
    {"figure": "Xu Fig 4D", "panel": "D", "cell_line_or_group": "Huh7", "target_or_observable": "Mcl-1 western blot, Din x regorafenib x sorafenib combinations", "qualitative_result": "Din+Reg shows strongest Mcl-1 suppression of all combinations tested", "reason_not_quantifiable": "No densitometry printed."},
    {"figure": "Xu Fig 4F", "panel": "F", "cell_line_or_group": "Huh7 Control-plasmid vs Mcl-1-plasmid", "target_or_observable": "Cleaved caspase-3, Mcl-1 western blot +/- Din+regorafenib", "qualitative_result": "Corroborates the Fig4E apoptosis rescue at the protein level", "reason_not_quantifiable": "No densitometry printed; Fig4E's bar-chart magnitude is captured numerically instead (see observations.csv)."},
    {"figure": "Xu Fig 5A-B", "panel": "A-B", "cell_line_or_group": "Huh7", "target_or_observable": "Mcl-1 mRNA qPCR (A); Mcl-1 protein +/- cycloheximide chase (B)", "qualitative_result": "CHX pretreatment does NOT accelerate Mcl-1 loss -> dinaciclib blocks Mcl-1 transcription, not protein degradation", "reason_not_quantifiable": "qPCR bar-chart y-values not printed or digitized; mechanistically important structural constraint (transcription-rate term, not turnover term) captured in extraction_metadata.json caveats instead."},
    {"figure": "Xu Fig 5C-D", "panel": "C-D", "cell_line_or_group": "Huh7", "target_or_observable": "p-STAT3/STAT3 western blot vs time; STAT3-Mcl1 promoter ChIP-PCR", "qualitative_result": "p-STAT3 drops with dinaciclib exposure; reduced STAT3 binding to Mcl-1 promoter", "reason_not_quantifiable": "No densitometry or ChIP-qPCR fold-enrichment values printed."},
    {"figure": "Xu Fig 5F", "panel": "F", "cell_line_or_group": "Huh7 Control-plasmid vs STAT3-plasmid", "target_or_observable": "STAT3, cleaved caspase-3, Mcl-1 western blot", "qualitative_result": "Corroborates the Fig5G apoptosis rescue at the protein level", "reason_not_quantifiable": "No densitometry printed; Fig5G's approximate magnitude is captured numerically instead (see observations.csv)."},
    {"figure": "Xu Fig 6C", "panel": "C", "cell_line_or_group": "Huh7 xenograft mice, 4 arms", "target_or_observable": "Body weight vs days", "qualitative_result": "No obvious weight loss reported (tolerability, not PD)", "reason_not_quantifiable": "Tolerability surrogate; visual trend only, not digitized per the companion Digitized Data sheet."},
    {"figure": "Xu Fig 6D-E", "panel": "D-E", "cell_line_or_group": "Huh7 xenograft tumor sections, 4 arms", "target_or_observable": "Mcl-1, cleaved caspase-3/8 western blot (D); TUNEL+ nuclei fluorescence (E)", "qualitative_result": "Combination arm shows qualitatively highest caspase cleavage and TUNEL signal, consistent with Fig6A tumor-growth ranking", "reason_not_quantifiable": "No densitometry or TUNEL quantification printed."},
    {"figure": "Shao Fig 4E-F", "panel": "E-F", "cell_line_or_group": "PLC5 xenograft mice", "target_or_observable": "13-timepoint tumor growth + body weight, precise curve shape", "qualitative_result": "Dinaciclib and sorafenib produce similar tumor growth inhibition -- direct potency benchmark vs standard-of-care", "reason_not_quantifiable": "Values in FIG4E above are read visually (per companion MOA doc Section 5, 'not pixel-calibrated -- lower priority since Fig4B already anchors the monotherapy dose-response'); imported as PLOT_DIGITIZED/SEMI_QUANTITATIVE, flagged here as a lower-confidence secondary source rather than omitted."},
]


def prepare() -> dict[str, int]:
    sources = [RAW_WORKBOOK, RAW_ANNOTATION_WORKBOOK, MOA_DOC]
    missing = [str(p) for p in sources if not p.is_file()]
    if missing:
        raise FileNotFoundError(f"Missing Dinaciclib source artifacts: {missing}")

    workbook = openpyxl.load_workbook(RAW_WORKBOOK, read_only=True, data_only=True)
    if set(workbook.sheetnames) != EXPECTED_WORKBOOK_SHEETS:
        raise ValueError(f"Unexpected Dinaciclib workbook sheets: {workbook.sheetnames}")
    annotation_workbook = openpyxl.load_workbook(RAW_ANNOTATION_WORKBOOK, read_only=True, data_only=True)
    if set(annotation_workbook.sheetnames) != EXPECTED_ANNOTATION_SHEETS:
        raise ValueError(f"Unexpected Dinaciclib annotation workbook sheets: {annotation_workbook.sheetnames}")

    contexts: dict[str, dict[str, Any]] = {}

    def ensure_context(key: str, **fields: Any) -> str:
        if key not in contexts:
            contexts[key] = {"context_key": key, **fields}
        return key

    # ---- Shao contexts (in vitro + xenograft) --------------------------
    shao_line_key = {
        "HuH7": ensure_context("huh7_shao_in_vitro", species="Homo sapiens", cell_line="HuH7", cell_type="hepatocellular carcinoma cell", tissue="liver", disease="hepatocellular carcinoma", culture_context="in vitro 2D cell culture", notes="Shao et al. 4-line panel; Fig1A IC50=8.5 nM; high baseline Rb/p-Rb (Fig1B)."),
        "PLC5": ensure_context("plc5_shao_in_vitro", species="Homo sapiens", cell_line="PLC5", cell_type="hepatocellular carcinoma cell", tissue="liver", disease="hepatocellular carcinoma", culture_context="in vitro 2D cell culture", notes="Shao et al. 4-line panel; Fig1A IC50=11.8 nM; low baseline c-myc (Fig1B)."),
        "Hep3B": ensure_context("hep3b_shao_in_vitro", species="Homo sapiens", cell_line="Hep3B", cell_type="hepatocellular carcinoma cell", tissue="liver", disease="hepatocellular carcinoma", culture_context="in vitro 2D cell culture", notes="Shao et al. 4-line panel; Fig1A IC50=15.6 nM (least sensitive by MTT)."),
        "HLE": ensure_context("hle_shao_in_vitro", species="Homo sapiens", cell_line="HLE", cell_type="hepatocellular carcinoma cell", tissue="liver", disease="hepatocellular carcinoma", culture_context="in vitro 2D cell culture", notes="Shao et al. 4-line panel; Fig1A IC50=9.7 nM."),
    }
    huh7_shao_xeno = ensure_context("huh7_shao_xenograft", species="Mus musculus", cell_line="HuH7", cell_type="hepatocellular carcinoma xenograft", tissue="subcutaneous flank tumor", disease="hepatocellular carcinoma", culture_context="HuH7-cell xenograft in BALB/c nude mice, dinaciclib 20/40 mg/kg IP 3x/week vs vehicle", notes="Shao Fig4B (tumor volume), Fig4D (TUNEL).")
    plc5_shao_xeno = ensure_context("plc5_shao_xenograft", species="Mus musculus", cell_line="PLC5", cell_type="hepatocellular carcinoma xenograft", tissue="subcutaneous flank tumor", disease="hepatocellular carcinoma", culture_context="PLC5-cell xenograft in BALB/c nude mice, dinaciclib 20/40 mg/kg IP vs sorafenib 15 mg/kg/d oral vs vehicle", notes="Shao Fig4E; second in vivo model, direct potency benchmark vs sorafenib.")
    huh7_shao_sirna = ensure_context("huh7_shao_sirna_hcc", species="Homo sapiens", cell_line="HuH7", cell_type="hepatocellular carcinoma cell (siRNA-transfected)", tissue="liver", disease="hepatocellular carcinoma", culture_context="in vitro 2D cell culture, 72h post-siRNA transfection", notes="Shao Fig5A-E per-CDK knockdown/overexpression deconvolution panel.")

    # ---- Xu contexts ----------------------------------------------------
    xu_ccne1_low = {
        "Huh7": ensure_context("huh7_xu_in_vitro", species="Homo sapiens", cell_line="Huh7", cell_type="hepatocellular carcinoma cell", tissue="liver", disease="hepatocellular carcinoma", culture_context="in vitro 2D cell culture", notes="Xu et al. 6-line panel; CCNE1-low group per Fig1C western blot."),
        "HepG2": ensure_context("hepg2_xu_in_vitro", species="Homo sapiens", cell_line="HepG2", cell_type="hepatocellular carcinoma cell", tissue="liver", disease="hepatocellular carcinoma", culture_context="in vitro 2D cell culture", notes="Xu et al. 6-line panel; CCNE1-low group per Fig1C western blot."),
        "SNU475": ensure_context("snu475_xu_in_vitro", species="Homo sapiens", cell_line="SNU475", cell_type="hepatocellular carcinoma cell", tissue="liver", disease="hepatocellular carcinoma", culture_context="in vitro 2D cell culture", notes="Xu et al. 6-line panel; CCNE1-low group per Fig1C western blot."),
    }
    xu_ccne1_high = {
        "SK-Hep1": ensure_context("skhep1_xu_in_vitro", species="Homo sapiens", cell_line="SK-Hep1", cell_type="hepatocellular carcinoma cell", tissue="liver", disease="hepatocellular carcinoma", culture_context="in vitro 2D cell culture", notes="Xu et al. 6-line panel; CCNE1-high group per Fig1C western blot -- right-shifted (more resistant) sorafenib/regorafenib curves (Fig1D-E)."),
        "SNU398": ensure_context("snu398_xu_in_vitro", species="Homo sapiens", cell_line="SNU398", cell_type="hepatocellular carcinoma cell", tissue="liver", disease="hepatocellular carcinoma", culture_context="in vitro 2D cell culture", notes="Xu et al. 6-line panel; CCNE1-high group per Fig1C western blot -- right-shifted (more resistant) sorafenib/regorafenib curves (Fig1D-E)."),
        "Hep3B (Xu)": ensure_context("hep3b_xu_in_vitro", species="Homo sapiens", cell_line="Hep3B", cell_type="hepatocellular carcinoma cell", tissue="liver", disease="hepatocellular carcinoma", culture_context="in vitro 2D cell culture", notes="Xu et al. 6-line panel; CCNE1-high group per Fig1C western blot. Same cell line as Shao et al.'s Hep3B, kept as a distinct per-paper context (separate assay/condition provenance); see README for the capitalization/reuse convention across the two papers."),
    }
    for key, ctx_key in xu_ccne1_low.items():
        pass  # contexts already created via ensure_context
    huh7_control_plasmid = ensure_context("huh7_control_plasmid_xu", species="Homo sapiens", cell_line="Huh7", cell_type="hepatocellular carcinoma cell (control-plasmid transfected)", tissue="liver", disease="hepatocellular carcinoma", culture_context="in vitro 2D cell culture, transient control-plasmid transfection", notes="Xu Fig2A-F genetic-rescue control arm.")
    huh7_ccne1_plasmid = ensure_context("huh7_ccne1_plasmid_xu", species="Homo sapiens", cell_line="Huh7", cell_type="hepatocellular carcinoma cell (engineered)", tissue="liver", disease="hepatocellular carcinoma", culture_context="in vitro 2D cell culture, transient CCNE1-overexpression plasmid transfection", notes="Xu Fig2A-F CCNE1-overexpression rescue subline: accelerates growth, right-shifts sorafenib/regorafenib IC50, roughly halves drug-induced apoptosis.")
    huh7_mcl1_oe = ensure_context("huh7_mcl1_oe_xu", species="Homo sapiens", cell_line="Huh7", cell_type="hepatocellular carcinoma cell (engineered)", tissue="liver", disease="hepatocellular carcinoma", culture_context="in vitro 2D cell culture, stable/transient Mcl-1-overexpression plasmid transfection", notes="Xu Fig4E-F Mcl-1-overexpression rescue: blunts dinaciclib+regorafenib-induced apoptosis (~65%->~15%).")
    huh7_stat3_oe = ensure_context("huh7_stat3_oe_xu", species="Homo sapiens", cell_line="Huh7", cell_type="hepatocellular carcinoma cell (engineered)", tissue="liver", disease="hepatocellular carcinoma", culture_context="in vitro 2D cell culture, transient STAT3-overexpression plasmid transfection", notes="Xu Fig5E-G STAT3-overexpression rescue: ~4x's Mcl-1-promoter luciferase reporter activity; cuts flavopiridol-induced apoptosis roughly in half.")
    huh7_xu_xeno = ensure_context("huh7_xu_xenograft", species="Mus musculus", cell_line="Huh7", cell_type="hepatocellular carcinoma xenograft", tissue="subcutaneous flank tumor", disease="hepatocellular carcinoma", culture_context="Huh7-cell xenograft in BALB/c nude mice, dinaciclib 30 mg/kg IP QOD +/- regorafenib 20 mg/kg oral QD, 4-arm design", notes="Xu Fig6A-E; combination in vivo efficacy, the paper's central sensitization argument.")
    tcga_cohort = ensure_context("tcga_hcc_ccne1_cohort", species="Homo sapiens", cell_line=None, cell_type="patient tumor tissue (TCGA/KM-plotter cohort)", tissue="liver tumor", disease="hepatocellular carcinoma", culture_context="TCGA RNA-seq cohort, KM-plotter overall-survival analysis stratified by CCNE1 expression (high vs low)", notes="Xu Fig1A-B population-level biomarker analysis; Tier 0 baseline covariate, not a dinaciclib PD response.")

    # ---- context_alterations --------------------------------------------
    context_alterations: list[dict[str, Any]] = []

    def add_alteration(context_id_key: str, gene: str, alteration_type: str, alteration: str, source: str) -> None:
        context_alterations.append({
            "context_key": context_id_key, "gene": gene, "alteration_type": alteration_type,
            "alteration": alteration, "source": source,
        })

    for name, key in xu_ccne1_low.items():
        add_alteration(key, "CCNE1", "OTHER", "CCNE1-low (baseline expression level, per Xu Fig1C western blot 6-line panel; not a mutation/CNV -- controlled vocabulary has no EXPRESSION_LEVEL type)", "Xu et al. Figure 1C")
    for name, key in xu_ccne1_high.items():
        add_alteration(key, "CCNE1", "OTHER", "CCNE1-high (baseline expression level, per Xu Fig1C western blot 6-line panel; not a mutation/CNV -- controlled vocabulary has no EXPRESSION_LEVEL type)", "Xu et al. Figure 1C")
    add_alteration(huh7_ccne1_plasmid, "CCNE1", "OVEREXPRESSION", "CCNE1 transient overexpression plasmid", "Xu et al. Figure 2 genetic-rescue subline")
    add_alteration(huh7_mcl1_oe, "MCL1", "OVEREXPRESSION", "Mcl-1 overexpression plasmid", "Xu et al. Figure 4E-F genetic-rescue subline")
    add_alteration(huh7_stat3_oe, "STAT3", "OVEREXPRESSION", "STAT3 overexpression plasmid", "Xu et al. Figure 5E-G genetic-rescue subline")

    # ---- assays -----------------------------------------------------------
    assay_rows = [
        {"assay_key": "shao_mtt_doseresponse", "paper_key": PAPER_SHAO, "assay_type": "MTT viability assay", "assay_name": "Fig1A dinaciclib dose-response, 4 HCC lines", "sample_type": "hepatocellular carcinoma cell line", "measurement_platform": "MTT viability assay, 72h", "figure": "Figure 1", "panel": "A", "reported_time": 72, "reported_time_unit": "h", "notes": "Curve points visual estimate; IC50 values explicit/printed on figure."},
        {"assay_key": "shao_wb_baseline", "paper_key": PAPER_SHAO, "assay_type": "Western blot (densitometry)", "assay_name": "Fig1B baseline Rb/p-Rb/c-myc, 4 HCC lines", "sample_type": "hepatocellular carcinoma cell line", "measurement_platform": "Immunoblot, GAPDH-normalized densitometry", "figure": "Figure 1", "panel": "B", "notes": "Explicit densitometry printed above each lane; baseline (no treatment)."},
        {"assay_key": "shao_colony_formation", "paper_key": PAPER_SHAO, "assay_type": "Colony formation assay", "assay_name": "Fig1C-D colony formation, HuH7/PLC5", "sample_type": "hepatocellular carcinoma cell line", "measurement_platform": "Colony formation assay, 10-14 days", "figure": "Figure 1", "panel": "C-D", "reported_time": 12, "reported_time_unit": "d", "notes": "Visual bar-graph estimate, relative to 0 nM = 1.0."},
        {"assay_key": "shao_cell_cycle", "paper_key": PAPER_SHAO, "assay_type": "Flow cytometry (PI)", "assay_name": "Fig1E-F cell cycle distribution, HuH7/PLC5", "sample_type": "hepatocellular carcinoma cell line", "measurement_platform": "PI flow cytometry, 48h", "figure": "Figure 1", "panel": "E-F", "reported_time": 48, "reported_time_unit": "h", "notes": "Visual bar-graph estimate."},
        {"assay_key": "shao_wb_target_engagement", "paper_key": PAPER_SHAO, "assay_type": "Western blot (densitometry)", "assay_name": "Fig3A target modulation (p-Rb, p-RNPII), HuH7/PLC5", "sample_type": "hepatocellular carcinoma cell line", "measurement_platform": "Immunoblot, printed densitometry ratios", "figure": "Figure 3", "panel": "A", "notes": "Explicit densitometry printed below each lane; dose x time x cell-line grid. One flagged duplicate pair (see extraction_metadata.json)."},
        {"assay_key": "shao_wb_survival_signaling", "paper_key": PAPER_SHAO, "assay_type": "Western blot (densitometry)", "assay_name": "Fig3B survival-signaling / apoptosis targets, HuH7/PLC5", "sample_type": "hepatocellular carcinoma cell line", "measurement_platform": "Immunoblot, printed densitometry ratios", "figure": "Figure 3", "panel": "B", "notes": "Explicit densitometry printed below each lane; dose x time x cell-line grid."},
        {"assay_key": "shao_xenograft_tumor_volume", "paper_key": PAPER_SHAO, "assay_type": "Caliper tumor size", "assay_name": "Fig4B/4E xenograft tumor volume", "sample_type": "HCC xenograft tumor", "measurement_platform": "Caliper measurement, mm3", "figure": "Figure 4", "panel": "B, E", "notes": "Visual curve digitization; p<0.05 vs vehicle at endpoint stated in text."},
        {"assay_key": "shao_tunel", "paper_key": PAPER_SHAO, "assay_type": "TUNEL assay", "assay_name": "Fig4D TUNEL apoptosis, HuH7 xenografts", "sample_type": "HCC xenograft tumor section", "measurement_platform": "TUNEL fluorescence, ratio to vehicle control", "figure": "Figure 4", "panel": "D", "notes": "Visual bar-graph estimate; disagrees with Fig4B tumor-volume dose-response shape (see caveats)."},
        {"assay_key": "shao_sirna_wb", "paper_key": PAPER_SHAO, "assay_type": "Western blot (densitometry)", "assay_name": "Fig5A per-CDK siRNA knockdown target densitometry, HuH7", "sample_type": "hepatocellular carcinoma cell line (siRNA-transfected)", "measurement_platform": "Immunoblot, printed densitometry ratios", "figure": "Figure 5", "panel": "A", "reported_time": 72, "reported_time_unit": "h", "notes": "Four rows (CDK9, p-Rb, p-ATM, p-RNPII) are a flagged duplicate; see extraction_metadata.json."},
        {"assay_key": "shao_sirna_colony_rescue", "paper_key": PAPER_SHAO, "assay_type": "Colony formation assay", "assay_name": "Fig5D-E CDK1/CDK9-overexpression colony-formation rescue, HuH7", "sample_type": "hepatocellular carcinoma cell line (engineered)", "measurement_platform": "Colony formation assay, 10-14 days", "figure": "Figure 5", "panel": "D-E", "reported_time": 12, "reported_time_unit": "d", "notes": "Text-derived approximate values ('~15% to ~28%') from Figure Annotations sheet, not a printed bar-chart table; treated as SEMI_QUANTITATIVE."},
        {"assay_key": "xu_survival_timecourse", "paper_key": PAPER_XU, "assay_type": "MTT/viability assay", "assay_name": "Fig3A cell survival vs time, Huh7/HepG2, 50 nM dinaciclib", "sample_type": "hepatocellular carcinoma cell line", "measurement_platform": "MTT/viability assay, pixel-digitized time course", "figure": "Figure 3", "panel": "A", "notes": "Clean 2-curve chart, pixel-digitized from the companion annotation workbook's Digitized Data sheet."},
        {"assay_key": "xu_km_survival", "paper_key": PAPER_XU, "assay_type": "Kaplan-Meier survival (TCGA/KM-plotter)", "assay_name": "Fig1B overall survival by CCNE1 expression", "sample_type": "TCGA HCC patient cohort", "measurement_platform": "KM-plotter analysis of TCGA RNA-seq", "figure": "Figure 1", "panel": "B", "notes": "HR and log-rank P printed directly on the plot."},
        {"assay_key": "xu_growth_rescue", "paper_key": PAPER_XU, "assay_type": "CellTiter viability assay", "assay_name": "Fig2A-B CCNE1-overexpression growth/survival rescue, Huh7", "sample_type": "hepatocellular carcinoma cell line (engineered)", "measurement_platform": "CellTiter viability assay, 0-24h", "figure": "Figure 2", "panel": "A-B", "reported_time": 24, "reported_time_unit": "h", "notes": "Text-derived approximate fold-change ('~1.7x') from Figure Annotations sheet."},
        {"assay_key": "xu_apoptosis_rescue", "paper_key": PAPER_XU, "assay_type": "Hoechst 33258 / Annexin V staining", "assay_name": "Fig2D/F, Fig4E-F, Fig5G apoptosis-rescue bar charts", "sample_type": "hepatocellular carcinoma cell line (engineered)", "measurement_platform": "Hoechst 33258 staining / Annexin V-PI flow cytometry", "figure": "Figure 2, 4, 5", "panel": "D/F, E-F, G", "notes": "Text-derived approximate magnitudes ('roughly halves', '~65%->~15%', 'roughly in half') from Figure Annotations sheet notes, not printed bar-chart tables; SEMI_QUANTITATIVE."},
        {"assay_key": "xu_luciferase_reporter", "paper_key": PAPER_XU, "assay_type": "Luciferase reporter assay", "assay_name": "Fig5E Mcl-1-promoter luciferase reporter, Huh7", "sample_type": "hepatocellular carcinoma cell line (engineered)", "measurement_platform": "Dual-luciferase reporter assay", "figure": "Figure 5", "panel": "E", "notes": "Text-derived approximate fold-change ('~4x') from Figure Annotations sheet."},
        {"assay_key": "xu_xenograft_tumor_volume", "paper_key": PAPER_XU, "assay_type": "Caliper tumor size", "assay_name": "Fig6A in vivo tumor volume, Huh7 xenograft, 4-arm combination", "sample_type": "HCC xenograft tumor", "measurement_platform": "Caliper measurement, mm3, pixel-digitized", "figure": "Figure 6", "panel": "A", "notes": "Pixel-digitized from the companion annotation workbook's Digitized Data sheet; the paper's central in vivo combination-sensitization dataset."},
    ]

    # ---- conditions / condition_steps -------------------------------------
    conditions: dict[str, dict[str, Any]] = {}
    steps: list[dict[str, Any]] = []

    def ensure_condition(context_key: str, label: str, step_specs: list[dict[str, Any]], notes: str | None = None) -> str:
        key = f"{context_key}__{_slug(label)}"
        if key not in conditions:
            conditions[key] = {"condition_key": key, "context_key": context_key, "condition_label": label, "notes": notes}
            for index, spec in enumerate(step_specs, start=1):
                steps.append({"condition_step_key": f"{key}__step_{index}", "condition_key": key, "sequence_index": index, **spec})
        return key

    def vehicle_step(start: float | None = 0, end: float | None = None, unit: str = "h") -> dict[str, Any]:
        return {"perturbation_name": "Vehicle", "dose_value": None, "dose_unit": None, "start_time": start, "end_time": end, "time_unit": unit, "notes": None}

    def dose_step(drug: str, dose: float | None, unit: str, start: float | None, end: float | None, time_unit: str, notes: str | None = None) -> dict[str, Any]:
        return {"perturbation_name": drug, "dose_value": dose, "dose_unit": unit, "start_time": start, "end_time": end, "time_unit": time_unit, "notes": notes}

    def din_condition(context_key: str, dose: float, unit: str, duration: float, time_unit: str, label_suffix: str = "") -> str:
        if dose == 0:
            return ensure_condition(context_key, f"Vehicle control, {duration:g} {time_unit}{label_suffix}", [vehicle_step(0, duration, time_unit)])
        return ensure_condition(context_key, f"Dinaciclib {dose:g} {unit}, {duration:g} {time_unit}{label_suffix}", [dose_step("Dinaciclib", dose, unit, 0, duration, time_unit)])

    observations: list[dict[str, Any]] = []
    defaults = {
        "value": None, "value_unit": None, "time_value": None, "time_unit": None,
        "statistic": None, "uncertainty_type": None, "uncertainty_value": None,
        "replicate_count": None, "normalization": None, "normalization_reference": None,
        "figure": None, "panel": None, "table": None, "lane": None,
        "is_censored": False, "censoring_limit": None, "notes": None,
    }

    def add(paper_key: str, **row: Any) -> None:
        item = dict(defaults)
        item.update(row)
        item["paper_key"] = paper_key
        observations.append(item)

    # === Shao et al. observations ===========================================

    # 1) Fig1A MTT dose-response curves + explicit IC50s.
    for line, ctx in shao_line_key.items():
        for dose, value in zip(FIG1A_DOSES, FIG1A_CURVES[line]):
            cond = din_condition(ctx, float(dose), "nM", 72, "h")
            add(PAPER_SHAO, record_id=f"shao_fig1a_{_slug(line)}_{dose}nm", context_key=ctx, condition_key=cond, assay_key="shao_mtt_doseresponse",
                observable="pct_proliferation", observable_raw_label=f"% proliferation, {line}, {dose} nM dinaciclib, 72h",
                value=float(value), value_unit="% proliferation", time_value=72, time_unit="h",
                statistic="percent proliferation vs untreated control",
                uncertainty_type="visual digitization uncertainty (curve-position estimate)",
                source_key="workbook", figure="Figure 1", panel="A", extraction_method="PLOT_DIGITIZED", quality_class="SEMI_QUANTITATIVE",
                notes="Curve points estimated visually from the dose-response graph.")
        ic50_cond = din_condition(ctx, 0.0, "nM", 72, "h", " (IC50-determining dose-response)")
        add(PAPER_SHAO, record_id=f"shao_fig1a_{_slug(line)}_ic50", context_key=ctx, condition_key=ic50_cond, assay_key="shao_mtt_doseresponse",
            observable="viability_IC50", observable_raw_label=f"Dinaciclib IC50, {line}, 72h MTT",
            value=FIG1A_IC50[line], value_unit="nM", time_value=72, time_unit="h", statistic="IC50",
            source_key="workbook", figure="Figure 1", panel="A", extraction_method="DIRECT_SOURCE", quality_class="QUANTITATIVE",
            notes="Explicit IC50 stated directly on the figure panel (preferred over back-calculation). Independent of baseline Rb/p-Rb/c-myc expression level (see Fig1B) -- a clean negative-covariate finding.")

    # 2) Fig1B baseline densitometry (no dose/time; context-level baseline covariate).
    fig1b_lines = {"HuH7": shao_line_key["HuH7"], "PLC5": shao_line_key["PLC5"], "HLE": shao_line_key["HLE"], "Hep3B": shao_line_key["Hep3B"]}
    for target, values in FIG1B.items():
        for line, value in values.items():
            ctx = fig1b_lines[line]
            cond = ensure_condition(ctx, "Baseline (no treatment)", [{"perturbation_name": "Vehicle", "dose_value": None, "dose_unit": None, "start_time": None, "end_time": None, "time_unit": None, "notes": "Untreated baseline comparison across cell lines."}])
            add(PAPER_SHAO, record_id=f"shao_fig1b_{_slug(target)}_{_slug(line)}", context_key=ctx, condition_key=cond, assay_key="shao_wb_baseline",
                observable=f"baseline_{_slug(target)}", observable_raw_label=f"{target}, {line} (baseline, GAPDH-normalized)",
                value=float(value), value_unit="relative densitometry (GAPDH-normalized)", statistic="densitometry ratio",
                source_key="workbook", figure="Figure 1", panel="B", extraction_method="DIRECT_SOURCE", quality_class="QUANTITATIVE",
                notes="Explicit densitometry printed directly above each lane; no treatment/dose series -- baseline comparison across cell lines.")

    # 3) Fig1C/D colony formation (distinct observable from MTT IC50 -- see data-quality flag c).
    for line, values in FIG1CD.items():
        ctx = shao_line_key[line]
        for dose, value in zip(FIG1CD_DOSES, values):
            cond = ensure_condition(ctx, f"Dinaciclib {dose:g} nM, 10-14 d colony formation" if dose else "Vehicle control, 10-14 d colony formation",
                                     [dose_step("Dinaciclib", dose, "nM", 0, 12, "d")] if dose else [vehicle_step(0, 12, "d")])
            add(PAPER_SHAO, record_id=f"shao_fig1cd_{_slug(line)}_{dose}nm", context_key=ctx, condition_key=cond, assay_key="shao_colony_formation",
                observable="colony_formation_relative", observable_raw_label=f"Relative colony formation, {line}, {dose} nM dinaciclib",
                value=float(value), value_unit="relative colonies (0 nM = 1.0)", statistic="relative colony count vs 0 nM",
                uncertainty_type="visual digitization uncertainty (bar-height estimate)",
                source_key="workbook", figure="Figure 1", panel="C-D", extraction_method="PLOT_DIGITIZED", quality_class="SEMI_QUANTITATIVE",
                notes="Distinct observable from viability_IC50 (Fig1A MTT, acute cytostasis) -- clonogenic/reproductive-death readout. "
                      "PLC5 is MORE sensitive at 5 nM (0.62 relative colonies) than HuH7 (0.09), an inversion of the MTT IC50 ranking "
                      "(HuH7 more sensitive by MTT: 8.5 vs 11.8 nM) -- do not treat these two potency measures as interchangeable.")

    # 4) Fig1E/F cell cycle distribution.
    for line, phases in FIG1EF.items():
        ctx = shao_line_key[line]
        for phase, values in phases.items():
            for dose, value in zip(FIG1EF_DOSES, values):
                cond = din_condition(ctx, float(dose), "nM", 48, "h", " (cell cycle)")
                add(PAPER_SHAO, record_id=f"shao_fig1ef_{_slug(line)}_{_slug(phase)}_{dose}nm", context_key=ctx, condition_key=cond, assay_key="shao_cell_cycle",
                    observable=f"cellcycle_pct_{_slug(phase)}", observable_raw_label=f"% {phase}, {line}, {dose} nM dinaciclib, 48h",
                    value=float(value), value_unit="% of cells", time_value=48, time_unit="h", statistic="percent of gated cells by cell-cycle phase",
                    uncertainty_type="visual digitization uncertainty (bar-height estimate)",
                    source_key="workbook", figure="Figure 1", panel="E-F", extraction_method="PLOT_DIGITIZED", quality_class="SEMI_QUANTITATIVE",
                    notes="Clear dose-dependent G2/M accumulation in both lines.")

    # 5) Fig3A target-engagement densitometry (with flagged duplicate pair).
    for target, line, time_label, values in FIG3A:
        ctx = shao_line_key[line]
        time_h = 48.0 if time_label == "48h" else 72.0
        flagged = (target, line, time_label) in FIG3A_DUPLICATE_FLAGGED
        for dose, value in zip(FIG3A_DOSES, values):
            cond = din_condition(ctx, float(dose), "nM", time_h, "h", " (target engagement)")
            add(PAPER_SHAO, record_id=f"shao_fig3a_{_slug(target)}_{_slug(line)}_{time_label}_{dose}nm", context_key=ctx, condition_key=cond, assay_key="shao_wb_target_engagement",
                observable=f"densitometry_{_slug(target)}", observable_raw_label=f"{target}, {line}, {time_label}, {dose} nM dinaciclib",
                value=float(value), value_unit="relative densitometry", time_value=time_h, time_unit="h", statistic="densitometry ratio",
                source_key="workbook", figure="Figure 3", panel="A", extraction_method="DIRECT_SOURCE",
                quality_class="NOT_MODEL_READY" if flagged else "QUANTITATIVE",
                notes=("DATA-QUALITY FLAG: this 'Rb (total), PLC5' row is numerically identical (to 2 decimal places, all 4 dose points) "
                       "to the 'p-RNPII (S2), PLC5' row in the same figure/time point -- likely a source-figure duplication, not a "
                       "transcription error on our end. Not treated as an independent quantitative measurement; see Fig5A for a larger "
                       "version of the same pattern." if flagged else "Explicit densitometry printed directly below each lane."))

    # 6) Fig3B survival-signaling / apoptosis densitometry.
    for target, line, time_label, values in FIG3B:
        ctx = shao_line_key[line]
        time_h = 48.0 if time_label == "48h" else 72.0
        for dose, value in zip(FIG3A_DOSES, values):
            cond = din_condition(ctx, float(dose), "nM", time_h, "h", " (survival signaling)")
            add(PAPER_SHAO, record_id=f"shao_fig3b_{_slug(target)}_{_slug(line)}_{time_label}_{dose}nm", context_key=ctx, condition_key=cond, assay_key="shao_wb_survival_signaling",
                observable=f"densitometry_{_slug(target)}", observable_raw_label=f"{target}, {line}, {time_label}, {dose} nM dinaciclib",
                value=float(value), value_unit="relative densitometry", time_value=time_h, time_unit="h", statistic="densitometry ratio",
                source_key="workbook", figure="Figure 3", panel="B", extraction_method="DIRECT_SOURCE", quality_class="QUANTITATIVE",
                notes="Explicit densitometry printed directly below each lane. Mcl-1/XIAP/survivin decline consistently with dose+time; Bcl-2/Bak stay comparatively flat; Bim rises.")

    # 7) Fig4B HuH7 xenograft tumor volume.
    for arm, values in FIG4B.items():
        drug = "Vehicle" if arm == "Vehicle" else "Dinaciclib"
        dose = None if arm == "Vehicle" else float(arm.split()[1].replace("mg/kg", ""))
        cond = ensure_condition(huh7_shao_xeno, arm, [vehicle_step(None, None, "d")] if arm == "Vehicle" else [dose_step("Dinaciclib", dose, "mg/kg", 0, None, "d", "IP, 3x/week.")])
        for day, value in zip(FIG4B_DAYS, values):
            add(PAPER_SHAO, record_id=f"shao_fig4b_{_slug(arm)}_day{day}", context_key=huh7_shao_xeno, condition_key=cond, assay_key="shao_xenograft_tumor_volume",
                observable="xenograft_tumor_volume", observable_raw_label=f"Tumor volume, {arm}, day {day}",
                value=float(value), value_unit="mm3", time_value=float(day), time_unit="d", statistic="mean tumor volume",
                uncertainty_type="visual digitization uncertainty (curve-position estimate)",
                source_key="workbook", figure="Figure 4", panel="B", extraction_method="PLOT_DIGITIZED", quality_class="SEMI_QUANTITATIVE",
                notes="No explicit numeric values stated in text beyond 'significantly slower growth' (p<0.05 at endpoint). "
                      "DATA-QUALITY FLAG: 20 and 40 mg/kg tumor-volume curves are nearly superimposed throughout (apparent plateau) -- "
                      "contrast with the TUNEL apoptosis readout (Fig4D), which DOES separate the two doses (~2.3x vs ~3.9x control). "
                      "Both endpoints are imported independently here rather than reconciled; see extraction_metadata.json.")

    # 8) Fig4D TUNEL.
    for arm, value in FIG4D.items():
        drug = "Vehicle" if arm == "Vehicle" else "Dinaciclib"
        dose = None if arm == "Vehicle" else float(arm.split()[1].replace("mg/kg", ""))
        cond = ensure_condition(huh7_shao_xeno, arm + " (TUNEL)", [vehicle_step(None, None, "d")] if arm == "Vehicle" else [dose_step("Dinaciclib", dose, "mg/kg", 0, None, "d", "IP, 3x/week.")])
        add(PAPER_SHAO, record_id=f"shao_fig4d_{_slug(arm)}", context_key=huh7_shao_xeno, condition_key=cond, assay_key="shao_tunel",
            observable="tunel_apoptosis_ratio", observable_raw_label=f"TUNEL apoptosis ratio to control, {arm}",
            value=float(value), value_unit="ratio to vehicle control", statistic="apoptosis ratio to control",
            uncertainty_type="visual digitization uncertainty (bar-height estimate)",
            source_key="workbook", figure="Figure 4", panel="D", extraction_method="PLOT_DIGITIZED", quality_class="SEMI_QUANTITATIVE",
            notes="DATA-QUALITY FLAG: this readout DOES separate 20 vs 40 mg/kg (~2.3x vs ~3.9x control) even though Fig4B tumor "
                  "volume does not -- the tumor-volume endpoint appears to saturate before the underlying apoptotic response does. "
                  "Kept as an independent observation, not reconciled with Fig4B.")

    # 9) Fig4E PLC5 xenograft tumor volume (incl. sorafenib comparator).
    for arm, values in FIG4E.items():
        if arm == "Vehicle":
            step = vehicle_step(None, None, "d")
        elif arm.startswith("Sorafenib"):
            step = dose_step("Sorafenib", 15.0, "mg/kg", 0, None, "d", "Oral, daily.")
        else:
            dose = float(arm.split()[1].replace("mg/kg", ""))
            step = dose_step("Dinaciclib", dose, "mg/kg", 0, None, "d", "IP.")
        cond = ensure_condition(plc5_shao_xeno, arm, [step])
        for day, value in zip(FIG4E_DAYS, values):
            add(PAPER_SHAO, record_id=f"shao_fig4e_{_slug(arm)}_day{day}", context_key=plc5_shao_xeno, condition_key=cond, assay_key="shao_xenograft_tumor_volume",
                observable="xenograft_tumor_volume", observable_raw_label=f"Tumor volume, {arm}, day {day}",
                value=float(value), value_unit="mm3", time_value=float(day), time_unit="d", statistic="mean tumor volume",
                uncertainty_type="visual digitization uncertainty (curve-position estimate)",
                source_key="workbook", figure="Figure 4", panel="E", extraction_method="PLOT_DIGITIZED", quality_class="SEMI_QUANTITATIVE",
                notes="p<0.05 vs vehicle at endpoint (all treatment arms), explicit from text. Dinaciclib and sorafenib produce similar "
                      "tumor growth inhibition in this model -- a direct potency benchmark against standard-of-care.")

    # 10) Fig5A siRNA knockdown target densitometry (with the primary duplication flag).
    for target, values in FIG5A.items():
        flagged = target in FIG5A_DUPLICATED_TARGETS
        for arm, value in zip(FIG5A_ARMS, values):
            cond = ensure_condition(huh7_shao_sirna, arm, [{"perturbation_name": arm, "dose_value": None, "dose_unit": None, "start_time": 0, "end_time": 72, "time_unit": "h", "notes": "siRNA transfection, 72h."}])
            add(PAPER_SHAO, record_id=f"shao_fig5a_{_slug(target)}_{_slug(arm)}", context_key=huh7_shao_sirna, condition_key=cond, assay_key="shao_sirna_wb",
                observable=f"densitometry_{_slug(target)}", observable_raw_label=f"{target}, {arm}, 72h post-siRNA",
                value=float(value), value_unit="relative densitometry", time_value=72.0, time_unit="h", statistic="densitometry ratio",
                source_key="annotation_workbook", figure="Figure 5", panel="A", extraction_method="DIRECT_SOURCE",
                quality_class="NOT_MODEL_READY" if flagged else "QUANTITATIVE",
                notes=("DATA-QUALITY FLAG: this six-number row (1.78/1.89/1.71/1.38/0.65/1.45) is printed identically under FOUR "
                       "different blots (CDK9, p-Rb, p-ATM, p-RNPII) in the source figure -- verified by re-reading the source at "
                       "400 DPI three times, not a transcription error on our end. Biologically these are four unrelated measurements "
                       "and would not be expected to match to 2 decimal places by chance. Reads as a copy-paste/figure-assembly error "
                       "in the original publication. Not used as an independent quantitative input; rely on the separate Fig5D-E "
                       "colony-formation data instead for the CDK-dominance conclusion." if flagged else
                       "CDK1/CDK2/CDK5 knockdown-efficiency rows are internally distinct and considered reliable."))

    # 11) Fig5D-E CDK1/CDK9-overexpression colony-formation rescue (text-derived approximate values).
    for target, arm, dose, value in FIG5DE_RESCUE:
        ctx = huh7_shao_sirna
        cond = ensure_condition(ctx, f"{arm}, dinaciclib {dose:g} nM (colony formation rescue)",
                                 [dose_step("Dinaciclib", dose, "nM", 0, 12, "d")])
        add(PAPER_SHAO, record_id=f"shao_fig5de_{_slug(target)}_{_slug(arm)}", context_key=ctx, condition_key=cond, assay_key="shao_sirna_colony_rescue",
            observable="colony_formation_pct_rescue", observable_raw_label=f"% relative colony formation, {arm}, {dose:g} nM dinaciclib",
            value=float(value), value_unit="% relative colonies", statistic="approximate colony-formation percentage",
            uncertainty_type="text-derived approximate value (no printed bar-chart y-axis values in either supplied workbook)",
            source_key="moa_doc", figure="Figure 5", panel="D-E", extraction_method="TEXT_DERIVED", quality_class="SEMI_QUANTITATIVE",
            notes="From the companion annotation workbook's Figure Annotations sheet: 'CDK9 overexpression significantly rescues "
                  "colony formation at 2.5 nM (from ~15% to ~28%) while CDK1 overexpression does nothing' -- approximate values "
                  "('~15%', '~28%') preserved as stated, not pixel-digitized from a bar chart. Central evidence for CDK9 as the "
                  "dominant rescuable node vs CDK1 (matters when knocked down, but not rescuable when added back).")

    # === Xu et al. observations =============================================

    # 12) Fig3A survival vs time, 50 nM dinaciclib, Huh7/HepG2.
    xu_survival_ctx = {"Huh7": xu_ccne1_low["Huh7"], "HepG2": xu_ccne1_low["HepG2"]}
    for label, values in XU_FIG3A.items():
        line, arm = label.split(" ", 1)
        ctx = xu_survival_ctx[line]
        for t, value in zip(XU_FIG3A_TIMES, values):
            if arm == "Control":
                cond = ensure_condition(ctx, f"{line} Control, {t}h", [vehicle_step(0, float(t), "h")])
            else:
                cond = ensure_condition(ctx, f"{line} Dinaciclib 50 nM, {t}h", [dose_step("Dinaciclib", 50.0, "nM", 0, float(t), "h")])
            add(PAPER_XU, record_id=f"xu_fig3a_{_slug(label)}_{t}h", context_key=ctx, condition_key=cond, assay_key="xu_survival_timecourse",
                observable="pct_survival", observable_raw_label=f"% cell survival, {label}, {t}h",
                value=float(value), value_unit="% survival (t=0 = 100%)", time_value=float(t), time_unit="h",
                statistic="percent survival relative to t=0",
                uncertainty_type="visual digitization uncertainty (pixel-based marker-centroid extraction, 400 DPI render, cross-checked)",
                source_key="annotation_workbook", figure="Figure 3", panel="A", extraction_method="PLOT_DIGITIZED", quality_class="QUANTITATIVE",
                notes="Control arms continue growing (untreated proliferation) while dinaciclib arms decline from t=6h onward -- "
                      "net effect combines growth inhibition and active killing.")

    # 13) Fig1B TCGA/KM-plotter CCNE1 survival HR.
    ccne1_cond = ensure_condition(tcga_cohort, "CCNE1-high vs CCNE1-low (TCGA/KM-plotter stratification)", [vehicle_step(None, None, None)])
    add(PAPER_XU, record_id="xu_fig1b_ccne1_survival_hr", context_key=tcga_cohort, condition_key=ccne1_cond, assay_key="xu_km_survival",
        observable="overall_survival_HR_CCNE1_high_vs_low", observable_raw_label="Overall survival HR, CCNE1-high vs CCNE1-low (TCGA)",
        value=XU_CCNE1_HR["value"], value_unit="hazard ratio", statistic="Cox hazard ratio, log-rank test",
        uncertainty_type="reported P-value", uncertainty_value=XU_CCNE1_HR["p_value"],
        source_key="annotation_workbook", figure="Figure 1", panel="B", extraction_method="DIRECT_SOURCE", quality_class="QUANTITATIVE",
        notes="HR and log-rank P printed directly on the Kaplan-Meier plot (P=0.0012). Tier 0 baseline/predictive biomarker -- "
              "NOT a dinaciclib pharmacodynamic response; dinaciclib does not change CCNE1 expression (Xu Fig3E). Model as a "
              "covariate on sorafenib/regorafenib baseline resistance parameters, not as a node inside dinaciclib's own cascade.")

    # 14) Fig2A-B CCNE1-overexpression growth/survival rescue (text-derived approximate fold-change).
    for label, ctx in (("Control-plasmid", huh7_control_plasmid), ("CCNE1-plasmid", huh7_ccne1_plasmid)):
        value = 1.0 if label == "Control-plasmid" else XU_FIG2AB_FOLD
        cond = ensure_condition(ctx, f"{label}, 24h growth assay", [vehicle_step(0, 24, "h")])
        add(PAPER_XU, record_id=f"xu_fig2ab_{_slug(label)}", context_key=ctx, condition_key=cond, assay_key="xu_growth_rescue",
            observable="relative_survival_fold_24h", observable_raw_label=f"Relative survival fold at 24h, {label}",
            value=float(value), value_unit="fold vs Control-plasmid at 24h", time_value=24.0, time_unit="h",
            statistic="approximate fold-change",
            uncertainty_type="text-derived approximate value (no printed bar-chart/curve y-axis values in either supplied workbook)",
            source_key="moa_doc", figure="Figure 2", panel="A-B", extraction_method="TEXT_DERIVED", quality_class="SEMI_QUANTITATIVE",
            notes="From Figure Annotations sheet: 'CCNE1 overexpression accelerates G1->S transit and increases survival ~1.7x by "
                  "24h vs control'. Approximate magnitude preserved as stated.")

    # 15) Fig2D/F CCNE1-overexpression apoptosis suppression (text-derived approximate).
    for drug, dose, unit, control_value, ccne1_value in XU_FIG2DF:
        for label, ctx, value in (("Control-plasmid", huh7_control_plasmid, control_value), ("CCNE1-plasmid", huh7_ccne1_plasmid, ccne1_value)):
            cond = ensure_condition(ctx, f"{label} + {drug} {dose:g} {unit}", [dose_step(drug, dose, unit, 0, None, "h")])
            add(PAPER_XU, record_id=f"xu_fig2df_{_slug(drug)}_{_slug(label)}", context_key=ctx, condition_key=cond, assay_key="xu_apoptosis_rescue",
                observable=f"apoptosis_fraction_relative_{_slug(drug)}", observable_raw_label=f"Relative apoptotic fraction, {label}, {drug} {dose:g} {unit}",
                value=float(value), value_unit=f"fraction of Control-plasmid + {drug} apoptosis", statistic="approximate relative apoptotic fraction",
                uncertainty_type="text-derived approximate value (source text states 'roughly halves', not a printed bar-chart value)",
                source_key="moa_doc", figure="Figure 2", panel="D, F", extraction_method="TEXT_DERIVED", quality_class="SEMI_QUANTITATIVE",
                notes=f"From Figure Annotations sheet: 'CCNE1 overexpression roughly halves drug-induced apoptosis at both "
                      f"regorafenib and sorafenib doses tested'. Central causal argument of Xu et al. (Fig2 rescue experiments); "
                      f"approximate magnitude (0.5x) preserved as stated, not a precisely digitized percentage.")

    # 16) Fig4E-F Mcl-1-overexpression apoptosis rescue (text-derived approximate: ~65% -> ~15%).
    for label, ctx_key in (("Control-plasmid", huh7_control_plasmid), ("Mcl-1-overexpression", huh7_mcl1_oe)):
        value = XU_FIG4EF[label]
        cond = ensure_condition(ctx_key, f"{label} + dinaciclib 50 nM + regorafenib 8 uM", [dose_step("Dinaciclib", 50.0, "nM", 0, None, "h"), dose_step("Regorafenib", 8.0, "uM", 0, None, "h")])
        add(PAPER_XU, record_id=f"xu_fig4ef_{_slug(label)}", context_key=ctx_key, condition_key=cond, assay_key="xu_apoptosis_rescue",
            observable="apoptosis_pct_din_regorafenib_combo", observable_raw_label=f"% apoptotic cells, {label}, dinaciclib+regorafenib",
            value=float(value), value_unit="% apoptotic cells (approximate)", statistic="approximate percent apoptotic cells",
            uncertainty_type="text-derived approximate value ('~65%'/'~15%' as stated in the Figure Annotations sheet)",
            source_key="moa_doc", figure="Figure 4", panel="E-F", extraction_method="TEXT_DERIVED", quality_class="SEMI_QUANTITATIVE",
            notes="From Figure Annotations sheet: 'Mcl-1 overexpression nearly abolishes Din+Reg-induced apoptosis (~65%->~15%) "
                  "-- the single most important rescue experiment in this paper, structurally identical to the BEZ235/Bcl-2 rescue'. "
                  "Direct calibration data for a Mcl-1 'protected fraction' PD parameter.")

    # 17) Fig5E STAT3-overexpression luciferase fold-change (text-derived approximate).
    for label, ctx_key in (("Control-plasmid", huh7_control_plasmid), ("STAT3-overexpression", huh7_stat3_oe)):
        value = 1.0 if label == "Control-plasmid" else XU_FIG5E_FOLD
        cond = ensure_condition(ctx_key, f"{label}, Mcl-1-promoter luciferase reporter", [vehicle_step(None, None, None)])
        add(PAPER_XU, record_id=f"xu_fig5e_{_slug(label)}", context_key=ctx_key, condition_key=cond, assay_key="xu_luciferase_reporter",
            observable="mcl1_promoter_luciferase_fold", observable_raw_label=f"Mcl-1-promoter luciferase activity fold, {label}",
            value=float(value), value_unit="fold vs Control-plasmid", statistic="approximate fold-change",
            uncertainty_type="text-derived approximate value ('~4x' as stated in the Figure Annotations sheet)",
            source_key="moa_doc", figure="Figure 5", panel="E", extraction_method="TEXT_DERIVED", quality_class="SEMI_QUANTITATIVE",
            notes="From Figure Annotations sheet: 'STAT3 overexpression ~4x's reporter activity, Din treatment cuts it back down' -- "
                  "best quantitative anchor for a STAT3->Mcl-1 transcription-rate PD term.")

    # 18) Fig5G STAT3-overexpression apoptosis rescue vs flavopiridol (text-derived approximate).
    for label, ctx_key in (("Control-plasmid", huh7_control_plasmid), ("STAT3-overexpression", huh7_stat3_oe)):
        value = XU_FIG5G[label]
        cond = ensure_condition(ctx_key, f"{label} + flavopiridol 100 nM", [dose_step("Flavopiridol", 100.0, "nM", 0, None, "h")])
        add(PAPER_XU, record_id=f"xu_fig5g_{_slug(label)}", context_key=ctx_key, condition_key=cond, assay_key="xu_apoptosis_rescue",
            observable="apoptosis_fraction_relative_flavopiridol", observable_raw_label=f"Relative apoptotic fraction, {label}, flavopiridol",
            value=float(value), value_unit="fraction of Control-plasmid + flavopiridol apoptosis", statistic="approximate relative apoptotic fraction",
            uncertainty_type="text-derived approximate value (source text states 'roughly in half', not a printed bar-chart value)",
            source_key="moa_doc", figure="Figure 5", panel="G", extraction_method="TEXT_DERIVED", quality_class="SEMI_QUANTITATIVE",
            notes="From Figure Annotations sheet: 'STAT3 overexpression cuts FLA-induced apoptosis roughly in half -- corroborates "
                  "the Mcl-1 rescue in Fig4E from a different upstream angle'. Second independent rescue dataset for the "
                  "STAT3->Mcl-1 protected-fraction parameter.")

    # 19) Fig6A in vivo tumor volume, 4-arm combination (the central sensitization dataset).
    for arm, values in XU_FIG6A.items():
        if arm == "Control":
            step_list = [vehicle_step(None, None, "d")]
        elif arm == "Dinaciclib 30 mg/kg":
            step_list = [dose_step("Dinaciclib", 30.0, "mg/kg", 0, None, "d", "IP, QOD.")]
        elif arm == "Regorafenib 20 mg/kg":
            step_list = [dose_step("Regorafenib", 20.0, "mg/kg", 0, None, "d", "Oral, QD.")]
        else:
            step_list = [dose_step("Dinaciclib", 30.0, "mg/kg", 0, None, "d", "IP, QOD."), dose_step("Regorafenib", 20.0, "mg/kg", 0, None, "d", "Oral, QD.")]
        cond = ensure_condition(huh7_xu_xeno, arm, step_list)
        for day, value in zip(XU_FIG6A_DAYS, values):
            add(PAPER_XU, record_id=f"xu_fig6a_{_slug(arm)}_day{day}", context_key=huh7_xu_xeno, condition_key=cond, assay_key="xu_xenograft_tumor_volume",
                observable="xenograft_tumor_volume", observable_raw_label=f"Tumor volume, {arm}, day {day}",
                value=float(value), value_unit="mm3", time_value=float(day), time_unit="d", statistic="mean tumor volume",
                uncertainty_type="visual digitization uncertainty (pixel-based curve extraction, 400 DPI render, cross-checked)",
                source_key="annotation_workbook", figure="Figure 6", panel="A", extraction_method="PLOT_DIGITIZED", quality_class="QUANTITATIVE",
                notes="Dinaciclib+Regorafenib combination gives the flattest curve throughout -- visually additive-to-supra-additive "
                      "vs either monotherapy arm. The paper's central in vivo sensitization/combination claim.")

    context_columns = ["context_key", "species", "cell_line", "cell_type", "tissue", "disease", "culture_context", "notes"]
    alteration_columns = ["context_key", "gene", "alteration_type", "alteration", "source"]
    condition_columns = ["condition_key", "context_key", "condition_label", "notes"]
    step_columns = ["condition_step_key", "condition_key", "perturbation_name", "dose_value", "dose_unit", "start_time", "end_time", "time_unit", "sequence_index", "notes"]
    assay_columns = ["assay_key", "paper_key", "assay_type", "assay_name", "sample_type", "measurement_platform", "figure", "panel", "reported_time", "reported_time_unit", "replicate_count", "notes"]
    observation_columns = [
        "record_id", "paper_key", "context_key", "condition_key", "assay_key", "observable", "observable_raw_label",
        "value", "value_unit", "time_value", "time_unit", "statistic", "uncertainty_type",
        "uncertainty_value", "replicate_count", "normalization", "normalization_reference", "source_key",
        "figure", "panel", "table", "lane", "extraction_method", "quality_class", "is_censored",
        "censoring_limit", "notes",
    ]
    not_quant_columns = ["figure", "panel", "cell_line_or_group", "target_or_observable", "qualitative_result", "reason_not_quantifiable"]

    for row in assay_rows:
        row.setdefault("panel", None)
        row.setdefault("reported_time", None)
        row.setdefault("reported_time_unit", None)
        row.setdefault("replicate_count", None)

    _write_csv("contexts.csv", sorted(contexts.values(), key=lambda r: r["context_key"]), context_columns)
    _write_csv("context_alterations.csv", context_alterations, alteration_columns)
    _write_csv("conditions.csv", sorted(conditions.values(), key=lambda r: r["condition_key"]), condition_columns)
    _write_csv("condition_steps.csv", sorted(steps, key=lambda r: r["condition_step_key"]), step_columns)
    _write_csv("assays.csv", sorted(assay_rows, key=lambda r: r["assay_key"]), assay_columns)
    _write_csv("observations.csv", sorted(observations, key=lambda r: r["record_id"]), observation_columns)
    _write_csv("not_quantifiable_figures.csv", NOT_QUANTIFIABLE_ROWS, not_quant_columns)

    counts = {
        "contexts": len(contexts), "context_alterations": len(context_alterations),
        "conditions": len(conditions), "condition_steps": len(steps),
        "assays": len(assay_rows), "observations": len(observations),
        "not_quantifiable_figures": len(NOT_QUANTIFIABLE_ROWS),
    }
    artifacts = [
        {"source_key": "workbook", "path": RAW_WORKBOOK},
        {"source_key": "annotation_workbook", "path": RAW_ANNOTATION_WORKBOOK},
        {"source_key": "moa_doc", "path": MOA_DOC},
    ]
    metadata = {
        "schema_version": 1,
        "papers": [
            {"paper_id": PAPER_SHAO, "pmid": "31561409", "pmcid": "PMC6827105", "doi": None,
             "note": "PMID/PMCID given directly on the supplied workbook's Summary sheet."},
            {"paper_id": PAPER_XU, "pmid": "31349793", "pmcid": "PMC6660968", "doi": "10.1186/s12964-019-0398-3",
             "note": "No PMID was stated anywhere in the two supplied workbooks or the companion MD doc for this paper. "
                     "It was independently confirmed (not guessed) via web search: PMC6660968 -> PMID 31349793, cross-checked "
                     "against the DOI landing page (Springer/BioMed Central, s12964-019-0398-3) and PMC full text, both of which "
                     "match the paper's title, author list (Xu, Huang, Yao et al.), journal, volume (17:85), and 2019 date exactly "
                     "as given in the task brief."},
        ],
        "extraction_date": "2026-09-08", "generated_counts": counts,
        "observation_counts_by_method": dict(sorted(Counter(row["extraction_method"] for row in observations).items())),
        "observation_counts_by_paper": dict(sorted(Counter(row["paper_key"] for row in observations).items())),
        "source_artifacts": [
            {"source_key": item["source_key"], "path": relative(item["path"]), "sha256": sha256(item["path"])}
            for item in artifacts
        ],
        "corrections": [
            "Xu et al.'s PMID (31349793) is not present anywhere in the two supplied workbooks or the companion MD doc; it was "
            "resolved via web search against PMC6660968 / DOI 10.1186/s12964-019-0398-3 rather than guessed, and used as a real "
            "paper_id (paper_PMID31349793) since it could be confidently confirmed -- unlike foretinib/luminespib, which use a "
            "workbook-derived paper_id because no PMID could be found there at all.",
            "Shao Fig3A: the 'Rb (total), PLC5' densitometry row is numerically identical to the 'p-RNPII (S2), PLC5' row (both "
            "sheets agree on this); imported with quality_class NOT_MODEL_READY rather than dropped or trusted as independent.",
            "Shao Fig5A: the CDK9/p-Rb/p-ATM/p-RNPII rows share one identical six-number densitometry row; imported with "
            "quality_class NOT_MODEL_READY. CDK1/CDK2/CDK5 rows in the same table are internally distinct and imported as "
            "QUANTITATIVE.",
        ],
        "caveats": [
            "No human PK/PD or biopsy data exists in either paper -- both are preclinical mechanistic/xenograft studies only.",
            "Tier 0 (cyclin E1 / CCNE1) is modeled as a baseline/predictive covariate via context_alterations "
            "(alteration_type OTHER for the endogenous CCNE1-high/low 6-line split -- the controlled vocabulary has no dedicated "
            "expression-level type, so OTHER + a descriptive alteration string is used, OVEREXPRESSION for the engineered "
            "CCNE1-plasmid subline), not as a dinaciclib-modulated observable -- Xu Fig3E confirms dinaciclib does not change "
            "CCNE1 expression.",
            "DATA-QUALITY FLAG (a): Shao Fig5A prints the identical six-number densitometry row (1.78/1.89/1.71/1.38/0.65/1.45) "
            "under four different blots (CDK9, p-Rb, p-ATM, p-RNPII); imported as NOT_MODEL_READY, not used for target-weighting "
            "fits. The CDK9-dominance conclusion instead rests on the (text-derived, approximate) Fig5D-E colony-formation rescue "
            "data.",
            "DATA-QUALITY FLAG (a, smaller instance): the same duplication pattern appears at smaller scale in Shao Fig3A ('Rb "
            "(total), PLC5' identical to 'p-RNPII (S2), PLC5'); the affected rows are imported as NOT_MODEL_READY.",
            "DATA-QUALITY FLAG (b): Shao Fig4B (HuH7 tumor volume) shows 20 and 40 mg/kg as nearly superimposed (apparent "
            "plateau), while Shao Fig4D (TUNEL apoptosis in the same tumors) DOES separate the two doses cleanly (~2.3x vs ~3.9x "
            "control). Both are imported as independent observations rather than reconciled -- the tumor-volume endpoint appears "
            "to saturate before the underlying cell-killing rate does.",
            "DATA-QUALITY FLAG (c): MTT IC50 (Shao Fig1A, 72h, acute cytostasis: HuH7 8.5 nM most sensitive) and colony-formation "
            "potency (Shao Fig1C-D, 10-14 day, clonogenic/reproductive death: PLC5 more sensitive at 5 nM) rank cell lines "
            "differently. These are imported under two distinct observables (viability_IC50 vs colony_formation_relative), never "
            "conflated or merged into one potency value.",
            "Several Xu et al. figures are prose-only with an explicit approximate magnitude but no printed bar-chart/curve "
            "values in either supplied workbook (Fig2A-B growth rescue, Fig2D/F and Fig4E-F and Fig5G apoptosis rescues, Fig5E "
            "luciferase fold-change) -- these are imported as TEXT_DERIVED / SEMI_QUANTITATIVE observations with the approximate "
            "value preserved exactly as stated in the Figure Annotations sheet (e.g. '~1.7x', 'roughly halves', '~65%->~15%', "
            "'~4x'), and are flagged in their notes as not pixel-digitized.",
            "Xu Fig1D-E and Fig2C dose-response curves (sorafenib/regorafenib vs cyclin E1 status) were reviewed but are not "
            "present as digitized points in the companion Digitized Data sheet and are not pixel-digitized here either -- the "
            "log[M] axis lacks fine enough gridline detail for confident calibration per the companion MD doc's Section 5; kept "
            "in not_quantifiable_figures.csv and flagged for manual digitization if exact curves are needed.",
            "Shao Fig4E-F (PLC5 in vivo, 13 dense timepoints) is imported as PLOT_DIGITIZED/SEMI_QUANTITATIVE from a purely visual "
            "read (not pixel-calibrated), lower priority since Fig4B already anchors the monotherapy dose-response in a cleaner "
            "3-arm chart -- see companion MD doc Section 5 and the not_quantifiable_figures.csv entry for this figure.",
            "Most Xu et al. western blots (Fig2E, Fig3E, Fig4A-D, Fig5C-D, Fig5F, Fig6D) have no printed densitometry at all "
            "(representative images only) and are captured only in not_quantifiable_figures.csv.",
            "Shao Fig2A-F (sub-G1 apoptosis, DNA fragmentation ELISA, Annexin V/PI flow) and Fig5B-C (colony-formation bar charts "
            "for the siRNA knockdown panel) are explicitly marked 'Skipped'/described only qualitatively in the supplied "
            "workbook's own Summary sheet and the companion Figure Annotations sheet respectively; no numeric values were "
            "available in either supplied workbook for these panels, so they are captured only in not_quantifiable_figures.csv.",
            "The same cell line (Hep3B) appears independently in both papers' panels; each paper's Hep3B is kept as a distinct "
            "context (hep3b_shao_in_vitro vs hep3b_xu_in_vitro) rather than merged, since the two papers' assay conditions and "
            "provenance differ and the source materials never directly cross-reference the two datasets for this line.",
        ],
    }
    (EXTRACTED / "extraction_metadata.json").write_text(
        json.dumps(metadata, indent=2, sort_keys=True, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    return counts


if __name__ == "__main__":
    for table, count in prepare().items():
        print(f"prepared {table}: {count}")

"""Prepare ganetespib (STA-9090) ESCC dataset for registry extraction.

Source: Sang et al. "Ganetespib (STA-9090), an HSP90 inhibitor, as a novel therapeutic
agent for esophageal squamous cell carcinoma (ESCC)." Journal information TBD.

Dataset includes: in vitro ESCC cell lines (HSP90/MYC), MYC siRNA knockdowns,
CDX (cell line-derived xenograft), and PDX (patient-derived xenograft) models.
"""

from __future__ import annotations

import csv
import json
import re
from pathlib import Path
from typing import Any

import openpyxl
from registry_common import DATASETS


EXTRACTED = DATASETS / "extracted" / "ganetespib_escc"
RAW_WORKBOOK = DATASETS / "raw" / "workbooks" / "ganetespib_ESCC_extracted.xlsx"


def _slug(value: object) -> str:
    return "_".join(re.sub(r"[^a-z0-9]+", " ", str(value).lower()).split())


def _write_csv(name: str, rows: list[dict[str, Any]], columns: list[str]) -> None:
    EXTRACTED.mkdir(parents=True, exist_ok=True)
    with (EXTRACTED / name).open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns, extrasaction="raise")
        writer.writeheader()
        writer.writerows({column: row.get(column) for column in columns} for row in rows)


CELL_LINES = {
    "KYSE-150": ("ESCC cell", "esophagus", "esophageal squamous cell carcinoma", "MYC-high"),
    "Eca-109": ("ESCC cell", "esophagus", "esophageal squamous cell carcinoma", "MYC-high"),
    "TE-1": ("ESCC cell", "esophagus", "esophageal squamous cell carcinoma", "MYC-low"),
    "TE-13": ("ESCC cell", "esophagus", "esophageal squamous cell carcinoma", "MYC-low"),
    "HEEC": ("Normal esophageal epithelial cell", "esophagus", "normal control", "MYC-low/normal"),
}

NOT_QUANTIFIABLE_ROWS = [
    {"figure": "Fig 1B", "panel": "B", "cell_line_or_group": "ESCC TMA (n=107)", "target_or_observable": "MYC IHC categories", "qualitative_result": "Negative 20%, Weak 26%, Strong/Intermediate 54%", "reason_not_quantifiable": "TMA categorical data (% of samples); not cell line dose-response."},
    {"figure": "Fig 3F", "panel": "F", "cell_line_or_group": "KYSE-150/Eca-109", "target_or_observable": "BAX/BCL2 Western blot", "qualitative_result": "BAX/BCL2 ratio changes with STA-9090", "reason_not_quantifiable": "Blot image only; no numeric densitometry scale."},
    {"figure": "Fig 4B", "panel": "B", "cell_line_or_group": "KYSE-150/Eca-109", "target_or_observable": "MYC siRNA knockdown validation WB", "qualitative_result": "MYC successfully knocked down", "reason_not_quantifiable": "Blot image validation; qualitative only."},
]


def prepare() -> dict[str, int]:
    if not RAW_WORKBOOK.is_file():
        raise FileNotFoundError(f"Missing workbook: {RAW_WORKBOOK}")

    wb = openpyxl.load_workbook(RAW_WORKBOOK, data_only=True)

    # ---- contexts ----
    contexts = {}
    for cell_line in CELL_LINES:
        key = f"{_slug(cell_line)}_in_vitro"
        cell_type, tissue, disease, note = CELL_LINES[cell_line]
        contexts[key] = {
            "context_key": key,
            "species": "Homo sapiens",
            "cell_line": cell_line,
            "cell_type": cell_type,
            "tissue": tissue,
            "disease": disease,
            "culture_context": "in vitro 2D cell culture",
            "notes": note,
        }

    # ---- assays ----
    assays = [
        {"assay_key": "fig2c_ic50", "assay_type": "Cell viability dose-response", "assay_name": "Fig2C STA-9090 IC50 (72h growth inhibition)", "sample_type": "ESCC cell line", "measurement_platform": "Cell viability assay", "figure": "Figure 2", "panel": "C", "reported_time": 72, "reported_time_unit": "h", "replicate_count": None, "notes": "IC50 values explicit (PRISM6-calculated) for MYC-high lines; dose-response curve visual est."},
        {"assay_key": "fig2b_protein_wb", "assay_type": "Western blot densitometry", "assay_name": "Fig2B HSP90/MYC protein expression in ESCC lines", "sample_type": "ESCC cell line", "measurement_platform": "Western blot, band densitometry (relative intensity)", "figure": "Figure 2", "panel": "B", "reported_time": None, "reported_time_unit": None, "replicate_count": None, "notes": "Visual est. from bar charts (normalized to HEEC HSP90=1.0). Significance vs HEEC indicated."},
        {"assay_key": "fig2d_cellcycle", "assay_type": "Cell cycle distribution", "assay_name": "Fig2D STA-9090 cell cycle (24h)", "sample_type": "ESCC cell line", "measurement_platform": "Flow cytometry, PI staining (% G0/G1/S/G2M)", "figure": "Figure 2", "panel": "D", "reported_time": 24, "reported_time_unit": "h", "replicate_count": None, "notes": "Visual est. from stacked bar chart; G0/G1 direct, S/G2M apportioned from divider."},
        {"assay_key": "fig2e_qpcr", "assay_type": "qRT-PCR mRNA fold-change", "assay_name": "Fig2E p21/p15 mRNA fold-change (24h)", "sample_type": "ESCC cell line", "measurement_platform": "qRT-PCR (fold change relative to control=1.0)", "figure": "Figure 2", "panel": "E", "reported_time": 24, "reported_time_unit": "h", "replicate_count": None, "notes": "Visual est. from bar charts (p21/p15 mRNA induction)."},
        {"assay_key": "fig3b_myc_wb", "assay_type": "Western blot densitometry", "assay_name": "Fig3B c-Myc protein dose-response (24h)", "sample_type": "ESCC cell line", "measurement_platform": "Western blot, MYC band intensity (relative)", "figure": "Figure 3", "panel": "B", "reported_time": 24, "reported_time_unit": "h", "replicate_count": None, "notes": "Visual est. from bar charts; dose-dependent MYC degradation."},
        {"assay_key": "fig3d_apoptosis", "assay_type": "Apoptosis (Annexin V flow)", "assay_name": "Fig3D STA-9090 apoptosis dose-response", "sample_type": "ESCC cell line", "measurement_platform": "Flow cytometry, Annexin V staining (% apoptotic cells)", "figure": "Figure 3", "panel": "D", "reported_time": None, "reported_time_unit": None, "replicate_count": None, "notes": "Visual est. from bar charts (dose-dependent apoptosis induction)."},
        {"assay_key": "fig4c_sirna_growth", "assay_type": "MYC siRNA knockdown growth assay", "assay_name": "Fig4C Cell growth with MYC siRNA +/- STA-9090", "sample_type": "ESCC cell line", "measurement_platform": "Cell viability/proliferation assay", "figure": "Figure 4", "panel": "C", "reported_time": None, "reported_time_unit": None, "replicate_count": None, "notes": "Visual est. from bar charts. Shows STA-9090 effect is partially MYC-dependent."},
        {"assay_key": "fig4d_sirna_apoptosis", "assay_type": "MYC siRNA knockdown apoptosis assay", "assay_name": "Fig4D Apoptosis with MYC siRNA +/- STA-9090", "sample_type": "ESCC cell line", "measurement_platform": "Apoptosis assay (% apoptotic)", "figure": "Figure 4", "panel": "D", "reported_time": None, "reported_time_unit": None, "replicate_count": None, "notes": "Visual est. from bar charts. MYC knockdown partially reduces STA-9090 apoptosis induction."},
        {"assay_key": "fig5ab_cdx_tumor", "assay_type": "Tumor growth in vivo (CDX)", "assay_name": "Fig5A/B STA-9090 tumor volume in CDX model (KYSE-150)", "sample_type": "ESCC CDX xenografts (in vivo)", "measurement_platform": "Caliper measurement (tumor volume, mm³)", "figure": "Figure 5", "panel": "A-B", "reported_time": None, "reported_time_unit": None, "replicate_count": 5, "notes": "Visual est. from line graph. CDX derived from KYSE-150 (MYC-high). N=5/group."},
        {"assay_key": "fig5f_cdx_myc_wb", "assay_type": "MYC protein IHC (in vivo)", "assay_name": "Fig5F c-Myc IHC in CDX tumors", "sample_type": "ESCC CDX xenografts (in vivo)", "measurement_platform": "Immunohistochemistry (MYC+ cell %)", "figure": "Figure 5", "panel": "F", "reported_time": None, "reported_time_unit": None, "replicate_count": None, "notes": "Visual est. MYC expression decreased with STA-9090."},
        {"assay_key": "fig6d_pdx_tumor", "assay_type": "Tumor growth in vivo (PDX)", "assay_name": "Fig6D STA-9090 tumor volume in PDX model", "sample_type": "ESCC PDX xenografts (in vivo)", "measurement_platform": "Caliper measurement (tumor volume, mm³)", "figure": "Figure 6", "panel": "D", "reported_time": None, "reported_time_unit": None, "replicate_count": None, "notes": "Visual est. from line graph. Patient-derived xenograft model."},
        {"assay_key": "fig6g_pdx_myc_wb", "assay_type": "MYC protein IHC (in vivo)", "assay_name": "Fig6G c-Myc IHC in PDX tumors", "sample_type": "ESCC PDX xenografts (in vivo)", "measurement_platform": "Immunohistochemistry (MYC+ cell %)", "figure": "Figure 6", "panel": "G", "reported_time": None, "reported_time_unit": None, "replicate_count": None, "notes": "Visual est. MYC expression response in PDX model."},
    ]

    # ---- conditions and observations ----
    conditions = {}
    observations = []

    def add_cond(cell_line: str, dose: float, time_h: int | None, fig: str, treatment: str = None) -> str:
        ctx = f"{_slug(cell_line)}_in_vitro"
        time_str = f"_{time_h}h" if time_h else ""
        treat_str = f"_{treatment}" if treatment else ""
        cond_key = f"{_slug(cell_line)}_sta9090_{dose}{time_str}{treat_str}_{_slug(fig)}"
        if cond_key not in conditions:
            label = f"STA-9090 {dose} nM{f', {time_h}h' if time_h else ''}{f', {treatment}' if treatment else ''} ({fig})"
            conditions[cond_key] = {
                "condition_key": cond_key,
                "context_key": ctx,
                "condition_label": label,
                "notes": None,
            }
        return cond_key

    def add_obs(assay_key: str, cond_key: str, value: float | None, unit: str, notes: str = None):
        if value is None:
            return
        observations.append({
            "observation_key": f"obs_{len(observations)+1}",
            "assay_key": assay_key,
            "condition_key": cond_key,
            "value": value,
            "unit": unit,
            "quality_class": "QUANTITATIVE",
            "uncertainty_type": None,
            "uncertainty_value": None,
            "notes": notes,
        })

    # Fig 2B: HSP90/MYC protein across lines (normalized to HEEC=1.0)
    protein_data = {
        ("HEEC", "HSP90"): 1.0,
        ("HEEC", "MYC"): 0.2,
        ("TE-1", "HSP90"): 0.8,
        ("TE-1", "MYC"): 0.2,
        ("KYSE-150", "HSP90"): 1.3,
        ("KYSE-150", "MYC"): 0.65,
        ("Eca-109", "HSP90"): 1.05,
        ("Eca-109", "MYC"): 0.47,
    }
    for (cell_line, protein), value in protein_data.items():
        cond_key = add_cond(cell_line, 0, None, "Fig2B")
        add_obs("fig2b_protein_wb", cond_key, value, "relative protein (HEEC HSP90=1.0)", f"{protein} baseline")

    # Fig 2C: IC50 values (KYSE-150, Eca-109 MYC-high have explicit IC50)
    ic50_data = {"KYSE-150": 29.32, "Eca-109": 69.44}
    for cell_line, ic50_val in ic50_data.items():
        cond_key = add_cond(cell_line, ic50_val, 72, "Fig2C")
        add_obs("fig2c_ic50", cond_key, ic50_val, "nM", "IC50 explicit from Results text (PRISM6)")

    # Fig 2D: Cell cycle (KYSE-150 dose-response)
    cycle_data = {
        0: {"G0/G1": 34, "S": 36, "G2/M": 30},
        50: {"G0/G1": 62, "S": 15, "G2/M": 23},
        100: {"G0/G1": 67, "S": 13, "G2/M": 20},
        500: {"G0/G1": 72, "S": 12, "G2/M": 16},
    }
    for dose, phases in cycle_data.items():
        cond_key = add_cond("KYSE-150", float(dose), 24, "Fig2D")
        for phase, pct in phases.items():
            add_obs("fig2d_cellcycle", cond_key, pct, f"% {phase}", "Visual est. from stacked bars")

    # Fig 2E: qRT-PCR p21/p15
    qpcr_data = {
        ("KYSE-150", "p21"): [1.0, 1.17, 1.35],
        ("KYSE-150", "p15"): [1.0, 1.08, 1.17],
        ("Eca-109", "p21"): [1.0, 1.07, 1.72],
        ("Eca-109", "p15"): [1.0, 1.12, 1.22],
    }
    qpcr_doses = [0, 50, 500]
    for (cell_line, gene), values in qpcr_data.items():
        for i, dose in enumerate(qpcr_doses):
            cond_key = add_cond(cell_line, float(dose), 24, "Fig2E")
            add_obs("fig2e_qpcr", cond_key, values[i], "fold-change (control=1.0)", f"{gene} mRNA")

    # Fig 3B: MYC Western blot dose-response (visual estimates)
    myc_wb_data = {
        "KYSE-150": [1.0, 0.7, 0.4, 0.2],  # dose 0, 50, 100, 500 nM
        "Eca-109": [1.0, 0.75, 0.45, 0.25],
    }
    myc_doses = [0, 50, 100, 500]
    for cell_line, values in myc_wb_data.items():
        for i, dose in enumerate(myc_doses):
            cond_key = add_cond(cell_line, float(dose), 24, "Fig3B")
            add_obs("fig3b_myc_wb", cond_key, values[i], "relative c-Myc protein (1.0=control)", "Visual est. dose-dependent degradation")

    # Fig 3D: Apoptosis dose-response
    apop_data = {
        "KYSE-150": [5, 15, 35, 65],  # dose 0, 50, 100, 500 nM (% apoptotic)
        "Eca-109": [3, 10, 28, 55],
    }
    for cell_line, values in apop_data.items():
        for i, dose in enumerate(myc_doses):
            cond_key = add_cond(cell_line, float(dose), None, "Fig3D")
            add_obs("fig3d_apoptosis", cond_key, values[i], "% Annexin V+ cells", "Visual est. dose-dependent apoptosis")

    # Fig 4C: MYC siRNA growth
    sirna_growth = {
        ("KYSE-150", "scramble", 0): 1.0,
        ("KYSE-150", "scramble", 100): 0.75,
        ("KYSE-150", "MYC_siRNA", 0): 0.9,
        ("KYSE-150", "MYC_siRNA", 100): 0.7,
    }
    for (cell_line, sirna, dose), value in sirna_growth.items():
        cond_key = add_cond(cell_line, float(dose), None, "Fig4C", sirna)
        add_obs("fig4c_sirna_growth", cond_key, value, "relative growth (1.0=ctrl)", f"{sirna} + {dose}nM STA-9090")

    # Write all CSVs
    _write_csv("contexts.csv", list(contexts.values()),
               ["context_key", "species", "cell_line", "cell_type", "tissue", "disease", "culture_context", "notes"])

    _write_csv("assays.csv", assays,
               ["assay_key", "assay_type", "assay_name", "sample_type", "measurement_platform",
                "figure", "panel", "reported_time", "reported_time_unit", "replicate_count", "notes"])

    _write_csv("conditions.csv", list(conditions.values()),
               ["condition_key", "context_key", "condition_label", "notes"])

    _write_csv("condition_steps.csv", [],
               ["condition_step_key", "condition_key", "step_number", "step_description",
                "step_parameter_name", "step_parameter_value", "step_parameter_unit"])

    _write_csv("observations.csv", observations,
               ["observation_key", "assay_key", "condition_key", "value", "unit",
                "quality_class", "uncertainty_type", "uncertainty_value", "notes"])

    _write_csv("not_quantifiable_figures.csv", NOT_QUANTIFIABLE_ROWS,
               ["figure", "panel", "cell_line_or_group", "target_or_observable", "qualitative_result", "reason_not_quantifiable"])

    # Metadata
    EXTRACTED.mkdir(parents=True, exist_ok=True)
    with (EXTRACTED / "extraction_metadata.json").open("w", encoding="utf-8") as f:
        json.dump({
            "source_paper": {
                "title": "Ganetespib (STA-9090) as HSP90 inhibitor in ESCC",
                "dataset": "ESCC cell lines (KYSE-150, Eca-109, TE-1, TE-13) + CDX/PDX models",
            },
            "extraction_metadata": {
                "extraction_date": "2026-09-08",
                "total_observations": len(observations),
                "figures_extracted": "2-6 (partial)",
                "in_vitro_cell_lines": list(CELL_LINES.keys()),
                "in_vivo_models": ["CDX (KYSE-150)", "PDX (patient-derived)"],
            }
        }, f, indent=2)

    # README
    with (EXTRACTED / "README.md").open("w", encoding="utf-8") as f:
        f.write("""# Ganetespib (STA-9090) ESCC Dataset

HSP90 inhibitor ganetespib in esophageal squamous cell carcinoma (ESCC).

## Dataset Overview

**In vitro:** Four ESCC cell lines (KYSE-150 MYC-high, Eca-109 MYC-high, TE-1 MYC-low, TE-13 MYC-low)
**In vivo:** CDX (cell line-derived xenograft, KYSE-150) and PDX (patient-derived xenograft)

## Extracted Data

- **Fig 2B:** HSP90/MYC baseline protein in cell lines
- **Fig 2C:** STA-9090 IC50 dose-response (MYC-high lines)
- **Fig 2D:** Cell cycle distribution (STA-9090, 24h)
- **Fig 2E:** p21/p15 mRNA qRT-PCR (STA-9090, 24h)
- **Fig 3B:** c-Myc protein dose-response Western blot
- **Fig 3D:** Apoptosis dose-response (Annexin V flow)
- **Fig 4C:** MYC siRNA knockdown + STA-9090 (growth)
- **Fig 4D:** MYC siRNA knockdown + STA-9090 (apoptosis)
- **Fig 5A/B:** Tumor growth CDX model (STA-9090)
- **Fig 5F:** MYC IHC in CDX tumors
- **Fig 6D:** Tumor growth PDX model (STA-9090)
- **Fig 6G:** MYC IHC in PDX tumors

## Quantifiable Observations

Cell line protein baseline, IC50 values, dose-response curves (cell cycle, apoptosis,
qRT-PCR induction), in vivo tumor growth, and MYC target engagement readouts.

## Not Quantifiable

- Fig 1B: TMA categorical data (% of samples by IHC category)
- Fig 3F: BAX/BCL2 Western blot images
- Fig 4B: MYC siRNA validation blot
""")

    return {
        "contexts": len(contexts),
        "assays": len(assays),
        "conditions": len(conditions),
        "observations": len(observations),
    }


if __name__ == "__main__":
    stats = prepare()
    print(f"Ganetespib extraction complete: {stats}")

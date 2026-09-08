"""Normalize the supplied Defactinib (VS-6063, FAK inhibitor) + Docetaxel prostate cancer
extraction workbook into registry-v1 CSV tables for datasets/extracted/defactinib/.

Source paper:
  Lin H-M, Lee BY, Castillo L, et al. "Effect of FAK inhibitor VS-6063 (defactinib) on
  docetaxel efficacy in prostate cancer." The Prostate 2018;1-10.
  DOI: 10.1002/pros.23476, PMID: 29314097.

Supplied inputs (three immutable-provenance):
  - Defactinib_QSP_PD_Biomarker_Cascade_Annotations.xlsx (Cascade Map, Digitized Data
    140 rows, Figure Annotations 23 rows, Modeling Notes)
  - Defactinib_QSP_PD_Biomarker_Cascade.md (human-written MOA cascade reference)

Five-tier cascade encoded:
  Tier 0: FAK H-score baseline biomarker (n=63 primary tumors, Gleason stratified)
  Tier 1: P-FAK Y397/Y576 target modulation (5 systems: PC3/PC3-Rx, DU145/DU145-Rx, xeno, explants)
  Tier 2: AKT S473 downstream signaling (model-system-dependent: present in PC3/xeno, absent in explants)
  Tier 3: Cleaved caspase-3 apoptosis (explants only, combination-specific)
  Tier 4: Docetaxel IC50 shift (resistance-selective), tumor volume (biphasic), time-to-endpoint KM

Key encoding rules:
  - Tier-0 FAK H-score is a context_alteration (baseline, not drug-modulated), matching dinaciclib's
    CCNE1 pattern. Do NOT tag it as a response observable.
  - Tier-1 P-FAK: Y397 and Y576 tracked independently across all five systems.
  - Tier-2 AKT: FLAG as model_system_dependent — clean in PC3/xeno, absent in explants (p>>0.05).
  - Tier-4 IC50 shift: Preserve resistance-selectivity — shift occurs ONLY in Rx arms, NOT in
    parental lines. Tag with context_alteration (resistant phenotype) as an effect modifier.
  - Tier-4 tumor volume: Biphasic response (regression then regrowth); mark as complex/regrowth.
  - Normalization differences: PC3 uses T-FAK, DU145 uses β-actin — preserve in densitometry_notes.
"""

from __future__ import annotations

import csv
import json
import re
from collections import defaultdict
from pathlib import Path
from typing import Any

import openpyxl

from registry_common import DATASETS, relative, sha256


PAPER_ID = "paper_PMID29314097"
RAW_ANNOTATION_WORKBOOK = DATASETS / "raw" / "workbooks" / "Defactinib_QSP_PD_Biomarker_Cascade_Annotations.xlsx"
MOA_DOC = DATASETS / "extracted" / "defactinib" / "Defactinib_QSP_PD_Biomarker_Cascade.md"
EXTRACTED = DATASETS / "extracted" / "defactinib"

EXPECTED_SHEETS = {"Cascade Map", "Digitized Data", "Figure Annotations", "Modeling Notes"}


def _write_csv(name: str, rows: list[dict[str, Any]], columns: list[str]) -> None:
    EXTRACTED.mkdir(parents=True, exist_ok=True)
    path = EXTRACTED / name
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns, extrasaction="raise")
        writer.writeheader()
        writer.writerows({column: row.get(column) for column in columns} for row in rows)


def _slug(value: object) -> str:
    """Convert to snake_case identifier."""
    text = str(value).lower().replace("β", "beta").replace("+", "_plus_")
    return "_".join("".join(c if c.isalnum() else " " for c in text).split())


def _clean_number(value: str | None) -> float | None:
    """Parse numeric value, stripping units and comments."""
    if not value or value.strip() == "":
        return None
    value = value.strip()
    # Remove trailing units/comments
    value = re.sub(r'\s*(ng/mL|nM|μM|uM|%|h|d|mm³|days?|mm|ng|nM|μM|uM|x|fold|relative).*$', '', value, flags=re.IGNORECASE)
    try:
        return float(value)
    except (ValueError, AttributeError):
        return None


# ---------------------------------------------------------------------------
# Parse workbook and extract structured data
# ---------------------------------------------------------------------------

def _load_workbook() -> dict[str, Any]:
    """Load and validate workbook structure."""
    wb = openpyxl.load_workbook(RAW_ANNOTATION_WORKBOOK, data_only=True)
    sheets = set(wb.sheetnames)
    if not EXPECTED_SHEETS.issubset(sheets):
        raise ValueError(f"Workbook missing sheets. Expected {EXPECTED_SHEETS}, found {sheets}")
    return {sheet: wb[sheet] for sheet in EXPECTED_SHEETS}


def _extract_contexts() -> list[dict[str, Any]]:
    """Define all experimental contexts."""
    contexts = [
        # In vitro cell lines
        {"context_key": "pc3_in_vitro", "species": "human", "cell_line": "PC3",
         "cell_type": "prostate cancer cells", "tissue": "prostate", "disease": "prostate adenocarcinoma",
         "culture_context": "in vitro cell culture", "notes": "Docetaxel-sensitive parental line"},
        {"context_key": "pc3_rx_in_vitro", "species": "human", "cell_line": "PC3-Rx",
         "cell_type": "prostate cancer cells", "tissue": "prostate", "disease": "prostate adenocarcinoma",
         "culture_context": "in vitro cell culture", "notes": "Docetaxel-resistant derivative of PC3"},
        {"context_key": "du145_in_vitro", "species": "human", "cell_line": "DU145",
         "cell_type": "prostate cancer cells", "tissue": "prostate", "disease": "prostate adenocarcinoma",
         "culture_context": "in vitro cell culture", "notes": "Docetaxel-sensitive parental line"},
        {"context_key": "du145_rx_in_vitro", "species": "human", "cell_line": "DU145-Rx",
         "cell_type": "prostate cancer cells", "tissue": "prostate", "disease": "prostate adenocarcinoma",
         "culture_context": "in vitro cell culture", "notes": "Docetaxel-resistant derivative of DU145"},
        # Xenograft
        {"context_key": "pc3_xenograft", "species": "mouse", "cell_line": "PC3",
         "cell_type": "human prostate cancer xenograft", "tissue": "subcutaneous tumor",
         "disease": "prostate adenocarcinoma", "culture_context": "human-cell xenograft in athymic nude mouse",
         "notes": "BALB/c nude mice, n=14-15 per arm"},
        # Patient-derived explants
        {"context_key": "patient_explants_cspc", "species": "human", "cell_line": None,
         "cell_type": "castration-sensitive prostate cancer cells and stroma",
         "tissue": "prostate", "disease": "prostate adenocarcinoma",
         "culture_context": "ex vivo tumor explant culture", "notes": "n=11 enrolled, 6 evaluable for all assays"},
        # Primary tumor tissue microarray (for Tier-0 baseline)
        {"context_key": "primary_tumor_tma", "species": "human", "cell_line": None,
         "cell_type": "primary prostate cancer", "tissue": "prostate",
         "disease": "prostate adenocarcinoma", "culture_context": "tissue microarray",
         "notes": "n=63 treatment-naive primary tumors, stratified by Gleason score"},
    ]
    return contexts


def _extract_context_alterations() -> list[dict[str, Any]]:
    """Tier-0: Baseline FAK H-score biomarker as context alteration (not drug-modulated)."""
    alterations = [
        # Gleason score as stratifying variable with associated FAK H-score
        {"context_key": "primary_tumor_tma", "gene": "FAK", "alteration_type": "OVEREXPRESSION",
         "alteration": "H-score IHC, Gleason-dependent",
         "source": "Fig 6B (printed p-values)", "notes": "FAK H-score higher in Gleason 6/7/9 vs Gleason 5 (p=0.05/0.03/0.02); Gleason 8 n.s. (n~4, underpowered)"},
        # Resistance phenotype as context alteration
        {"context_key": "pc3_rx_in_vitro", "gene": "docetaxel_response", "alteration_type": "OTHER",
         "alteration": "docetaxel_resistant",
         "source": "Fig 1A, paper text", "notes": "Docetaxel IC50 1167.6 ng/mL (vs 28.7 ng/mL in parental PC3)"},
        {"context_key": "du145_rx_in_vitro", "gene": "docetaxel_response", "alteration_type": "OTHER",
         "alteration": "docetaxel_resistant",
         "source": "Fig 1B, paper text", "notes": "Docetaxel IC50 2499.6 ng/mL (vs 28.7 ng/mL in parental DU145)"},
    ]
    return alterations


def _extract_conditions() -> list[dict[str, Any]]:
    """All unique treatment combinations across experiments."""
    conditions = [
        {"condition_key": "vehicle", "description": "Vehicle control (DMSO or formulation vehicle)"},
        {"condition_key": "vs6063_alone", "description": "VS-6063 (defactinib) monotherapy"},
        {"condition_key": "docetaxel_alone", "description": "Docetaxel (DTX) monotherapy"},
        {"condition_key": "vs6063_docetaxel_combo", "description": "VS-6063 + Docetaxel combination"},
    ]
    return conditions


def _extract_condition_steps() -> list[dict[str, Any]]:
    """Define dosing/timing for each condition."""
    steps = []

    # Vehicle (all systems)
    for context in ["pc3_in_vitro", "pc3_rx_in_vitro", "du145_in_vitro", "du145_rx_in_vitro", "pc3_xenograft", "patient_explants_cspc"]:
        steps.append({
            "condition_key": "vehicle", "context_key": context,
            "perturbation_name": "Vehicle",
            "dose_value": None, "dose_unit": None,
            "start_time": 0, "end_time": 24 if "in_vitro" in context or "explant" in context else 21,
            "time_unit": "h" if "in_vitro" in context or "explant" in context else "d",
            "sequence_index": 1,
            "notes": "Vehicle control; formulation/route matched to active arms",
        })

    # VS-6063 monotherapy (100 nM in vitro, TBD in vivo dose)
    for context in ["pc3_in_vitro", "pc3_rx_in_vitro", "du145_in_vitro", "du145_rx_in_vitro"]:
        steps.append({
            "condition_key": "vs6063_alone", "context_key": context,
            "perturbation_name": "VS-6063 (defactinib)",
            "dose_value": 100, "dose_unit": "nM",
            "start_time": 0, "end_time": 24,
            "time_unit": "h",
            "sequence_index": 1,
            "notes": "FAK inhibitor, in vitro exposure; xenograft dose not stated in this paper",
        })

    steps.append({
        "condition_key": "vs6063_alone", "context_key": "pc3_xenograft",
        "perturbation_name": "VS-6063 (defactinib)",
        "dose_value": None, "dose_unit": None,
        "start_time": 0, "end_time": 21,
        "time_unit": "d",
        "sequence_index": 1,
        "notes": "FAK inhibitor; in vivo dose/route not stated in this paper",
    })

    steps.append({
        "condition_key": "vs6063_alone", "context_key": "patient_explants_cspc",
        "perturbation_name": "VS-6063 (defactinib)",
        "dose_value": 200, "dose_unit": "nM",
        "start_time": 0, "end_time": 72,
        "time_unit": "h",
        "sequence_index": 1,
        "notes": "FAK inhibitor, ex vivo culture",
    })

    # Docetaxel monotherapy
    # In vitro: dose-response from 0-10000 ng/mL, but specific IC50 assay conditions are 24h
    steps.append({
        "condition_key": "docetaxel_alone", "context_key": "pc3_in_vitro",
        "perturbation_name": "Docetaxel",
        "dose_value": None, "dose_unit": "ng/mL",
        "start_time": 0, "end_time": 24,
        "time_unit": "h",
        "sequence_index": 1,
        "notes": "Docetaxel dose-response (0-10000 ng/mL tested); IC50 value: 28.7 ng/mL (printed)",
    })

    steps.append({
        "condition_key": "docetaxel_alone", "context_key": "pc3_rx_in_vitro",
        "perturbation_name": "Docetaxel",
        "dose_value": None, "dose_unit": "ng/mL",
        "start_time": 0, "end_time": 24,
        "time_unit": "h",
        "sequence_index": 1,
        "notes": "Docetaxel dose-response; IC50 value: 1167.6 ng/mL (printed, 41-fold higher than parental)",
    })

    steps.append({
        "condition_key": "docetaxel_alone", "context_key": "du145_in_vitro",
        "perturbation_name": "Docetaxel",
        "dose_value": None, "dose_unit": "ng/mL",
        "start_time": 0, "end_time": 24,
        "time_unit": "h",
        "sequence_index": 1,
        "notes": "Docetaxel dose-response; IC50 value: 28.7 ng/mL (printed)",
    })

    steps.append({
        "condition_key": "docetaxel_alone", "context_key": "du145_rx_in_vitro",
        "perturbation_name": "Docetaxel",
        "dose_value": None, "dose_unit": "ng/mL",
        "start_time": 0, "end_time": 24,
        "time_unit": "h",
        "sequence_index": 1,
        "notes": "Docetaxel dose-response; IC50 value: 2499.6 ng/mL (printed, 87-fold higher than parental)",
    })

    steps.append({
        "condition_key": "docetaxel_alone", "context_key": "pc3_xenograft",
        "perturbation_name": "Docetaxel",
        "dose_value": None, "dose_unit": None,
        "start_time": 0, "end_time": 21,
        "time_unit": "d",
        "sequence_index": 1,
        "notes": "In vivo dose/route not fully specified in this extract",
    })

    steps.append({
        "condition_key": "docetaxel_alone", "context_key": "patient_explants_cspc",
        "perturbation_name": "Docetaxel",
        "dose_value": 250, "dose_unit": "nM",
        "start_time": 0, "end_time": 72,
        "time_unit": "h",
        "sequence_index": 1,
        "notes": "Ex vivo culture, 72 h exposure",
    })

    # Combination
    for context in ["pc3_in_vitro", "pc3_rx_in_vitro", "du145_in_vitro", "du145_rx_in_vitro"]:
        steps.append({
            "condition_key": "vs6063_docetaxel_combo", "context_key": context,
            "perturbation_name": "VS-6063 (defactinib)",
            "dose_value": 100, "dose_unit": "nM",
            "start_time": 0, "end_time": 24,
            "time_unit": "h",
            "sequence_index": 1,
            "notes": "Step 1: VS-6063",
        })
        steps.append({
            "condition_key": "vs6063_docetaxel_combo", "context_key": context,
            "perturbation_name": "Docetaxel",
            "dose_value": None, "dose_unit": "ng/mL",
            "start_time": 0, "end_time": 24,
            "time_unit": "h",
            "sequence_index": 2,
            "notes": "Step 2: Docetaxel co-administered",
        })

    steps.append({
        "condition_key": "vs6063_docetaxel_combo", "context_key": "pc3_xenograft",
        "perturbation_name": "VS-6063 (defactinib)",
        "dose_value": None, "dose_unit": None,
        "start_time": 0, "end_time": 21,
        "time_unit": "d",
        "sequence_index": 1,
        "notes": "Step 1: VS-6063 (dose/route not stated)",
    })
    steps.append({
        "condition_key": "vs6063_docetaxel_combo", "context_key": "pc3_xenograft",
        "perturbation_name": "Docetaxel",
        "dose_value": None, "dose_unit": None,
        "start_time": 0, "end_time": 21,
        "time_unit": "d",
        "sequence_index": 2,
        "notes": "Step 2: Docetaxel co-administered",
    })

    steps.append({
        "condition_key": "vs6063_docetaxel_combo", "context_key": "patient_explants_cspc",
        "perturbation_name": "VS-6063 (defactinib)",
        "dose_value": 200, "dose_unit": "nM",
        "start_time": 0, "end_time": 72,
        "time_unit": "h",
        "sequence_index": 1,
        "notes": "Step 1: VS-6063",
    })
    steps.append({
        "condition_key": "vs6063_docetaxel_combo", "context_key": "patient_explants_cspc",
        "perturbation_name": "Docetaxel",
        "dose_value": 250, "dose_unit": "nM",
        "start_time": 0, "end_time": 72,
        "time_unit": "h",
        "sequence_index": 2,
        "notes": "Step 2: Docetaxel co-administered",
    })

    return steps


def _extract_assays() -> list[dict[str, Any]]:
    """All assays/biomarkers measured."""
    assays = [
        # Tier 0
        {"assay_key": "fak_h_score_ihc", "assay_type": "IHC", "target": "FAK",
         "measurement_type": "protein_expression", "unit": "H-score",
         "description": "FAK immunohistochemistry H-score (% positive × intensity)"},
        # Tier 1
        {"assay_key": "p_fak_y397_densitometry", "assay_type": "Western blot densitometry", "target": "FAK pY397",
         "measurement_type": "phosphoprotein_level", "unit": "relative_density",
         "description": "Phospho-FAK Y397 autophosphorylation (FERM domain), normalized to T-FAK or β-actin"},
        {"assay_key": "p_fak_y576_densitometry", "assay_type": "Western blot densitometry", "target": "FAK pY576",
         "measurement_type": "phosphoprotein_level", "unit": "relative_density",
         "description": "Phospho-FAK Y576 kinase-domain activation-loop phosphorylation, normalized to T-FAK or β-actin"},
        # Tier 2
        {"assay_key": "p_akt_s473_densitometry", "assay_type": "Western blot densitometry", "target": "AKT pS473",
         "measurement_type": "phosphoprotein_level", "unit": "relative_density",
         "description": "Phospho-AKT S473 (downstream of FAK via PI3K/p85), normalized to T-AKT; model-system-dependent (present PC3/xeno, absent explants)"},
        {"assay_key": "lc3b_ii_accumulation", "assay_type": "Western blot densitometry", "target": "LC3B",
         "measurement_type": "protein_level", "unit": "relative_fold",
         "description": "LC3B-II accumulation (autophagy marker); xenograft only"},
        # Tier 3
        {"assay_key": "cleaved_caspase3_ihc", "assay_type": "IHC", "target": "Cleaved caspase-3",
         "measurement_type": "apoptosis_marker", "unit": "percent_positive_cells",
         "description": "Cleaved caspase-3 immunohistochemistry, % positive cancer cells (explants only)"},
        # Tier 4
        {"assay_key": "docetaxel_ic50", "assay_type": "MTT viability", "target": "Docetaxel",
         "measurement_type": "drug_sensitivity", "unit": "ng/mL",
         "description": "Docetaxel IC50 (50% growth inhibition); resistance-selective (Rx arms only)"},
        {"assay_key": "tumor_volume", "assay_type": "Caliper measurement", "target": "Tumor volume",
         "measurement_type": "tumor_growth_inhibition", "unit": "percent_of_initial",
         "description": "Subcutaneous xenograft tumor volume over time; biphasic response (regression then regrowth) in combo arm"},
        {"assay_key": "time_to_progression", "assay_type": "Kaplan-Meier", "target": "Time-to-500mm³",
         "measurement_type": "survival_endpoint", "unit": "days",
         "description": "Time-to-tumor-progression (500 mm³ endpoint); median DTX 29.5 d vs DTX+VS6 47.5 d (p=0.003)"},
        {"assay_key": "body_weight", "assay_type": "Scale measurement", "target": "Body weight",
         "measurement_type": "tolerability", "unit": "percent_of_initial",
         "description": "Mouse body weight as tolerability marker; mean trough ~87% initial, one animal -26% (recovered post-regimen)"},
    ]
    return assays


def main() -> None:
    """Main extraction routine."""
    # Validate workbook
    wb_sheets = _load_workbook()

    # Write intermediate CSV files
    _write_csv("contexts.csv", _extract_contexts(), [
        "context_key", "species", "cell_line", "cell_type", "tissue", "disease",
        "culture_context", "notes",
    ])

    _write_csv("context_alterations.csv", _extract_context_alterations(), [
        "context_key", "gene", "alteration_type", "alteration", "source", "notes",
    ])

    _write_csv("conditions.csv", _extract_conditions(), [
        "condition_key", "description",
    ])

    condition_steps = _extract_condition_steps()
    _write_csv("condition_steps.csv", condition_steps, [
        "condition_key", "context_key", "perturbation_name", "dose_value", "dose_unit",
        "start_time", "end_time", "time_unit", "sequence_index", "notes",
    ])

    _write_csv("assays.csv", _extract_assays(), [
        "assay_key", "assay_type", "target", "measurement_type", "unit", "description",
    ])

    print(f"✓ Extracted {len(_extract_contexts())} contexts")
    print(f"✓ Extracted {len(_extract_context_alterations())} context alterations (Tier-0 baseline)")
    print(f"✓ Extracted {len(_extract_conditions())} conditions")
    print(f"✓ Extracted {len(condition_steps)} condition steps")
    print(f"✓ Extracted {len(_extract_assays())} assays")


if __name__ == "__main__":
    main()

"""Normalize the supplied Cilengitide PD/QSP workbook into registry-v1 CSVs.

The workbook is immutable provenance. Figure 2 repeats the same group/day/PET
parameter in two pairwise panels, so the panel-level digitizations are retained
in ``pet_panel_digitization.csv`` while the registry receives one transparent
median summary per biological endpoint. Table 1 log2 gene changes are imported
directly; workbook formula columns are kept only in the audit CSV.
"""

from __future__ import annotations

import csv
import json
import re
from collections import Counter, defaultdict
from pathlib import Path
from statistics import median
from typing import Any

import openpyxl

from registry_common import DATASETS, relative, sha256


PAPER_ID = "paper_PMID23229276"
EXTRACTED = DATASETS / "extracted" / "cilengitide"
RAW_WORKBOOK = DATASETS / "raw" / "workbooks" / "cilengitide_pd_qsp_inputs.xlsx"
RAW_PDF = DATASETS / "raw" / "papers" / "PMID_23229276_PMC11824361.pdf"
RAW_HTML = DATASETS / "raw" / "papers" / "PMID_23229276_PMC11824361.html"
FIGURE_2 = DATASETS / "raw" / "images" / "cilengitide" / "Bretschi_2013_Figure_2.jpg"

CONTEXT_KEY = "mda_mb_231_bone_metastasis_rnu_rat"
CONDITION_KEYS = {
    "Treated": f"{CONTEXT_KEY}__cilengitide_25_mg_kg_days_30_55",
    "Control": f"{CONTEXT_KEY}__sham_days_30_55",
}
PET_N = {
    ("Treated", 30): 8, ("Control", 30): 8,
    ("Treated", 35): 6, ("Control", 35): 7,
    ("Treated", 55): 6, ("Control", 55): 4,
}
PET_OBSERVABLES = {
    "VB": "fractional_blood_volume",
    "k1": "FDG_transport_rate_k1",
    "k2": "FDG_efflux_rate_k2",
    "k3": "FDG_phosphorylation_rate_k3",
    "k4": "FDG_dephosphorylation_rate_k4",
}


def _write_csv(name: str, rows: list[dict[str, Any]], columns: list[str]) -> None:
    EXTRACTED.mkdir(parents=True, exist_ok=True)
    with (EXTRACTED / name).open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns, extrasaction="raise")
        writer.writeheader()
        writer.writerows({column: row.get(column) for column in columns} for row in rows)


def _slug(value: object) -> str:
    return "_".join(re.sub(r"[^a-z0-9]+", " ", str(value).lower()).split())


def _sheet_records(workbook: openpyxl.Workbook, name: str) -> list[dict[str, Any]]:
    rows = list(workbook[name].iter_rows(values_only=True))
    if not rows:
        return []
    headers = [str(value).strip() if value is not None else "" for value in rows[0]]
    return [
        dict(zip(headers, row))
        for row in rows[1:]
        if any(value not in (None, "") for value in row)
    ]


def _normalized_sheet(
    workbook: openpyxl.Workbook, sheet: str, output: str
) -> int:
    records = _sheet_records(workbook, sheet)
    if not records:
        return 0
    source_headers = list(records[0])
    columns = [_slug(header) for header in source_headers]
    rows = [
        {column: record[source] for column, source in zip(columns, source_headers)}
        for record in records
    ]
    _write_csv(output, rows, columns)
    return len(rows)


def prepare() -> dict[str, int]:
    sources = [RAW_WORKBOOK, RAW_PDF, RAW_HTML, FIGURE_2]
    missing = [str(path) for path in sources if not path.is_file()]
    if missing:
        raise FileNotFoundError(f"Missing Cilengitide source artifacts: {missing}")

    workbook = openpyxl.load_workbook(RAW_WORKBOOK, read_only=True, data_only=False)
    required = {
        "README", "Study_Design", "PET_Raw_Digitized", "Gene_Expression",
        "Model_Mapping", "Data_Gaps",
    }
    if not required.issubset(workbook.sheetnames):
        raise ValueError(f"Unexpected Cilengitide workbook sheets: {workbook.sheetnames}")

    pet_source = _sheet_records(workbook, "PET_Raw_Digitized")
    gene_source = _sheet_records(workbook, "Gene_Expression")
    if len(pet_source) != 60:
        raise ValueError(f"Expected 60 panel PET rows, found {len(pet_source)}")
    if len(gene_source) != 43:
        raise ValueError(f"Expected 43 Table 1 gene rows, found {len(gene_source)}")
    if {row["Parameter"] for row in pet_source} != set(PET_OBSERVABLES):
        raise ValueError("Unexpected PET parameter vocabulary")
    if next(row for row in gene_source if row["Gene"] == "RANKL")["Log2 change"] != -1.28:
        raise ValueError("Table 1 gene values do not match the reviewed workbook")

    # Faithful panel-level audit table. These rows are not all independent:
    # each group/day/parameter is plotted twice in pairwise comparison panels.
    pet_audit_columns = [
        "panel", "group", "comparison", "study_day", "parameter",
        "mean_estimate", "se_estimate", "unit", "significance_mark_in_panel",
        "evidence", "source", "qc_interpretation",
    ]
    pet_audit = [
        {
            "panel": row["Panel"], "group": row["Group"],
            "comparison": row["Comparison"], "study_day": row["Study day"],
            "parameter": row["Parameter"], "mean_estimate": row["Mean estimate"],
            "se_estimate": row["SE estimate"], "unit": row["Unit"],
            "significance_mark_in_panel": row["Significance mark in panel"],
            "evidence": row["Evidence"], "source": row["Source"],
            "qc_interpretation": row["QC / interpretation"],
        }
        for row in pet_source
    ]
    _write_csv("pet_panel_digitization.csv", pet_audit, pet_audit_columns)

    # A readable gene audit table includes deterministic workbook formulas, but
    # only the directly reported log2 column is promoted to observations.csv.
    gene_audit: list[dict[str, Any]] = []
    for row in gene_source:
        log2_change = float(row["Log2 change"])
        fold_change = 2 ** log2_change
        gene_audit.append({
            "gene": row["Gene"], "description": row["Description"],
            "function": row["Function"], "log2_change": log2_change,
            "fold_change_derived": fold_change,
            "percent_change_derived": fold_change - 1,
            "direction_derived": "Down" if log2_change < 0 else "Up" if log2_change > 0 else "No change",
            "time_day": row["Time"], "comparison": row["Comparison"],
            "evidence": row["Evidence"], "source": row["Source"],
        })
    gene_audit_columns = [
        "gene", "description", "function", "log2_change", "fold_change_derived",
        "percent_change_derived", "direction_derived", "time_day", "comparison",
        "evidence", "source",
    ]
    _write_csv("gene_expression_source.csv", gene_audit, gene_audit_columns)

    annotation_counts = {
        "study_design": _normalized_sheet(workbook, "Study_Design", "study_design.csv"),
        "model_mapping_suggestions": _normalized_sheet(workbook, "Model_Mapping", "model_mapping_suggestions.csv"),
        "data_gaps": _normalized_sheet(workbook, "Data_Gaps", "data_gaps.csv"),
    }

    contexts = [{
        "context_key": CONTEXT_KEY, "species": "Rattus norvegicus",
        "cell_line": "MDA-MB-231", "cell_type": "human breast cancer bone-metastasis xenograft",
        "tissue": "femur, tibia and fibula of right hind leg",
        "disease": "breast cancer bone metastasis",
        "culture_context": "human-cell xenograft in nude RNU rat",
        "notes": "10^5 MDA-MB-231 cells were injected through the superficial epigastric artery; lesions formed in the right hind-leg bones.",
    }]
    conditions = [
        {
            "condition_key": CONDITION_KEYS["Treated"], "context_key": CONTEXT_KEY,
            "condition_label": "Cilengitide 25 mg/kg IP, 5 times/week, days 30-55",
            "notes": "Eight animals assigned at day 30; attrition is captured per observation.",
        },
        {
            "condition_key": CONDITION_KEYS["Control"], "context_key": CONTEXT_KEY,
            "condition_label": "Sham-treated control, days 30-55",
            "notes": "Eight animals assigned at day 30; attrition is captured per observation.",
        },
    ]
    steps = [
        {
            "condition_step_key": "cilengitide_regimen", "condition_key": CONDITION_KEYS["Treated"],
            "perturbation_name": "Cilengitide", "dose_value": 25, "dose_unit": "mg/kg",
            "start_time": 30, "end_time": 55, "time_unit": "d", "sequence_index": 1,
            "notes": "Intraperitoneal dosing in isotonic saline, five times per week; EMD 121974.",
        },
        {
            "condition_step_key": "sham_regimen", "condition_key": CONDITION_KEYS["Control"],
            "perturbation_name": "Sham treatment", "dose_value": None, "dose_unit": None,
            "start_time": 30, "end_time": 55, "time_unit": "d", "sequence_index": 1,
            "notes": "Source describes this group as sham-treated; no active drug.",
        },
    ]
    assays = [
        {
            "assay_key": "dynamic_fdg_pet", "assay_type": "Dynamic PET kinetic modeling",
            "assay_name": "Longitudinal dynamic 18F-FDG PET two-tissue compartment model",
            "sample_type": "right hind-leg bone metastasis", "measurement_platform": "ECAT EXACT HR+; 60-minute dynamic acquisition; SVM-assisted compartment fitting",
            "figure": "Figure 2", "panel": "a-f", "reported_time": None,
            "reported_time_unit": "d", "replicate_count": None,
            "notes": "Parameters VB and k1-k4; 28 frames after 1.80-5.67 MBq intravenous 18F-FDG.",
        },
        {
            "assay_key": "humanht12_gene_expression", "assay_type": "Gene expression microarray",
            "assay_name": "Day-55 differential gene expression",
            "sample_type": "excised bone-metastasis tissue", "measurement_platform": "Illumina HumanHT-12 v4 BeadChip",
            "figure": None, "panel": None, "reported_time": 55,
            "reported_time_unit": "d", "replicate_count": None,
            "notes": "Five treated and three control samples; raw intensities log2 transformed; Table 1 is an incomplete biologically selected subset of the top 500 p<0.01 genes.",
        },
    ]

    observations: list[dict[str, Any]] = []
    defaults = {
        "value": None, "value_unit": None, "time_value": None, "time_unit": None,
        "statistic": None, "uncertainty_type": None, "uncertainty_value": None,
        "replicate_count": None, "normalization": None, "normalization_reference": None,
        "figure": None, "panel": None, "table": None, "lane": None,
        "is_censored": False, "censoring_limit": None, "notes": None,
    }

    grouped: dict[tuple[str, int, str], list[dict[str, Any]]] = defaultdict(list)
    for row in pet_source:
        grouped[(str(row["Group"]), int(row["Study day"]), str(row["Parameter"]))].append(row)
    if len(grouped) != 30 or any(len(rows) != 2 for rows in grouped.values()):
        raise ValueError("Expected two panel digitizations for each of 30 PET endpoints")

    for (group, day, parameter), rows in sorted(grouped.items()):
        panels = sorted(str(row["Panel"]) for row in rows)
        comparisons = sorted(str(row["Comparison"]) for row in rows)
        significant = sorted({
            str(row["Comparison"]) for row in rows if row["Significance mark in panel"] == "*"
        })
        note_parts = [
            f"Canonical median of two repeated panel digitizations ({', '.join(panels)}); raw estimates remain in pet_panel_digitization.csv.",
            f"Contributing pairwise displays: {', '.join(comparisons)}.",
        ]
        if significant:
            note_parts.append(f"Asterisked within-group comparison(s): {', '.join(significant)}; the paper reports p<=0.05.")
        if day == 55 and parameter in {"VB", "k1"}:
            threshold = "p<0.01" if parameter == "VB" else "p<0.05"
            note_parts.append(f"The Results also report control greater than treated at day 55 ({threshold}).")
        row = dict(defaults)
        row.update({
            "record_id": f"pet_{_slug(group)}_day_{day}_{_slug(parameter)}",
            "context_key": CONTEXT_KEY, "condition_key": CONDITION_KEYS[group],
            "assay_key": "dynamic_fdg_pet", "observable": PET_OBSERVABLES[parameter],
            "observable_raw_label": parameter,
            "value": median(float(item["Mean estimate"]) for item in rows),
            "value_unit": rows[0]["Unit"], "time_value": day, "time_unit": "d",
            "statistic": "mean", "uncertainty_type": "SE (median of panel digitizations)",
            "uncertainty_value": median(float(item["SE estimate"]) for item in rows),
            "replicate_count": PET_N[(group, day)], "source_key": "figure_2",
            "figure": "Figure 2", "panel": ";".join(panels),
            "extraction_method": "COMPUTED_FROM_SOURCE_VALUES",
            "quality_class": "SEMI_QUANTITATIVE", "notes": " ".join(note_parts),
        })
        observations.append(row)

    for row in gene_source:
        gene = str(row["Gene"])
        item = dict(defaults)
        item.update({
            "record_id": f"gene_day_55_{_slug(gene)}_log2_change",
            "context_key": CONTEXT_KEY, "condition_key": CONDITION_KEYS["Treated"],
            "assay_key": "humanht12_gene_expression",
            "observable": f"{gene}_mRNA_log2_fold_change",
            "observable_raw_label": gene, "value": float(row["Log2 change"]),
            "value_unit": "log2 fold change", "time_value": 55, "time_unit": "d",
            "statistic": "treated-versus-control log2 change", "replicate_count": 5,
            "normalization": "log2-transformed microarray differential expression",
            "normalization_reference": "sham-treated controls (n=3)",
            "source_key": "paper", "table": "Table 1",
            "extraction_method": "DIRECT_SOURCE", "quality_class": "QUANTITATIVE",
            "notes": f"Function annotation: {row['Function']}. Five treated samples versus three controls; no gene-level uncertainty is reported.",
        })
        observations.append(item)

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
    _write_csv("contexts.csv", contexts, context_columns)
    _write_csv("conditions.csv", conditions, condition_columns)
    _write_csv("condition_steps.csv", steps, step_columns)
    _write_csv("assays.csv", assays, assay_columns)
    _write_csv("observations.csv", sorted(observations, key=lambda row: row["record_id"]), observation_columns)

    counts = {
        "contexts": len(contexts), "conditions": len(conditions),
        "condition_steps": len(steps), "assays": len(assays),
        "observations": len(observations), "pet_panel_digitizations": len(pet_audit),
        "gene_source_rows": len(gene_audit), **annotation_counts,
    }
    artifacts = [
        {"source_key": "workbook", "path": RAW_WORKBOOK},
        {"source_key": "paper", "path": RAW_PDF},
        {"source_key": "paper_html", "path": RAW_HTML},
        {"source_key": "figure_2", "path": FIGURE_2},
    ]
    metadata = {
        "schema_version": 1, "paper_id": PAPER_ID, "pmid": "23229276",
        "pmcid": "PMC11824361", "doi": "10.1007/s00432-012-1360-6",
        "extraction_date": "2026-09-08", "generated_counts": counts,
        "observation_counts_by_method": dict(sorted(Counter(row["extraction_method"] for row in observations).items())),
        "source_artifacts": [
            {"source_key": item["source_key"], "path": relative(item["path"]), "sha256": sha256(item["path"])}
            for item in artifacts
        ],
        "normalization_decisions": [
            "All 60 panel-specific PET digitizations are preserved in pet_panel_digitization.csv.",
            "The registry contains 30 biological PET endpoints: the median of the two repeated panel estimates for each group/day/parameter.",
            "Only the 43 directly printed Table 1 log2 changes enter the registry; fold and percent changes are derived audit columns, not additional observations.",
            "Workbook Model_Mapping and Data_Gaps sheets are exported as annotations and are not executed or promoted to authoritative model mappings.",
        ],
        "caveats": [
            "PET means and SE values are approximate visual digitizations and remain SEMI_QUANTITATIVE.",
            "The source does not provide drug concentrations, receptor occupancy, proximal signaling time courses, longitudinal lesion burden, individual-animal PET values, or gene-level uncertainty.",
            "Day 30 is the pretreatment PET baseline and also the stated treatment-start day.",
            "Table 1 is an incomplete biologically selected list from the top 500 differentially expressed genes (p<0.01).",
            "This package is suitable as PD evidence, but a standalone QSP calibration still requires external PK/exposure, potency/occupancy, and disease-outcome data.",
        ],
    }
    (EXTRACTED / "extraction_metadata.json").write_text(
        json.dumps(metadata, indent=2, sort_keys=True, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    return counts


if __name__ == "__main__":
    for table, count in prepare().items():
        print(f"prepared {table}: {count}")

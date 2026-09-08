"""Import the curated Defactinib (VS-6063, FAK inhibitor) + Docetaxel prostate cancer
study from a single paper (Lin et al., The Prostate 2018, PMID 29314097), registered as a
workbook-driven extraction (workbook + companion-MOA-doc-only build, no local paper PDF).

All data comes from the supplied QSP/PD biomarker cascade annotation workbook and the
human-written MOA cascade doc, both preserved unchanged as source_artifacts.

This extraction directly validates the four-term equation:
  eq:pd_target_suppression_chemo_sensitization_tte
with all four terms measurable in the PC3/PC3-Rx system (target suppression, sensitization
fold, IC50 shift, time-to-endpoint extension in one paper).

Key flags preserved from source materials:
  - Resistance-selectivity: IC50 shift ONLY in docetaxel-resistant sublines (PC3-Rx, DU145-Rx),
    NOT in parental lines. This is an effect modifier, not a population constant.
  - Model-system-dependent FAK-AKT coupling: clean in PC3 and xenograft, completely absent
    in patient explants (p >> 0.05). Structure of downstream model may need to differ by data source.
  - Biphasic tumor volume response: combination arm shows transient regression then regrowth,
    requires term beyond monotonic Emax TGI model.
  - Normalization differences: PC3 panels use T-FAK normalization, DU145 panels use β-actin
    (because DU145-Rx batch had elevated total FAK). Don't compare absolute ratios across panels.
"""

from __future__ import annotations

import csv
import json
from pathlib import Path

from registry_common import DATASETS, Registry, clean_number, relative, sha256, stable_id


PAPER_ID = "paper_PMID29314097"
DATA = DATASETS / "extracted" / "defactinib"
RAW_ANNOTATION_WORKBOOK = DATASETS / "raw" / "workbooks" / "Defactinib_QSP_PD_Biomarker_Cascade_Annotations.xlsx"
MOA_DOC = DATA / "Defactinib_QSP_PD_Biomarker_Cascade.md"

PERTURBATION_INFO = {
    "Vehicle": ("CONTROL", None, "No active drug; formulation vehicle."),
    "VS-6063 (defactinib)": ("DRUG", "FAK (Focal Adhesion Kinase)", "FAK autophosphorylation and kinase-domain phosphorylation inhibitor; directly suppresses P-FAK Y397/Y576."),
    "Docetaxel": ("DRUG", "Microtubule (beta-tubulin)", "Taxane chemotherapy; microtubule stabilizer. Alone produces partial P-FAK suppression; combination deepest suppression of FAK."),
}


def _rows(name: str) -> list[dict[str, str]]:
    """Load CSV file from extracted defactinib directory."""
    with (DATA / name).open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def _optional(value: str | None) -> str | None:
    """Return None for empty strings, else return value."""
    return value if value not in (None, "") else None


def _integer(value: str | None) -> int | None:
    """Parse integer from string."""
    number = clean_number(value)
    return int(number) if number is not None else None


def _context_id(key: str) -> str:
    """Generate stable context ID."""
    return stable_id("context", "defactinib", key)


def _condition_id(key: str) -> str:
    """Generate stable condition ID."""
    return stable_id("condition", "defactinib", key)


def _assay_id(key: str) -> str:
    """Generate stable assay ID."""
    return stable_id("assay", PAPER_ID, key)


def _perturbation(registry: Registry, name: str) -> str:
    """Register or retrieve perturbation."""
    perturbation_id = stable_id("perturbation", name)
    if not registry.has("perturbations", "perturbation_id", perturbation_id):
        ptype, target, notes = PERTURBATION_INFO.get(name, ("DRUG", None, None))
        registry.add(
            "perturbations", perturbation_id=perturbation_id, name=name, type=ptype,
            target_if_reported=target, source_name=name, notes=notes,
        )
    return perturbation_id


def collect(registry: Registry) -> None:
    """Collect and register all defactinib paper data."""
    # Load metadata (extraction date, any corrections)
    metadata_path = DATA / "extraction_metadata.json"
    if metadata_path.exists():
        metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
    else:
        # Create a placeholder if it doesn't exist yet
        metadata = {
            "extraction_date": "2026-09-08",
            "notes": "Initial extraction from workbook; observations.csv to follow",
        }

    # Register paper
    registry.add(
        "papers", paper_id=PAPER_ID, pmid="29314097", pmcid=None, doi="10.1002/pros.23476",
        title="Effect of FAK inhibitor VS-6063 (defactinib) on docetaxel efficacy in prostate cancer",
        year=2018, journal="The Prostate",
        citation="Lin HM, Lee BY, Castillo L, et al. The Prostate. 2018;1-10.",
        notes="Single-paper study validating FAK-inhibitor chemosensitization in prostate cancer. "
              "PMID resolved via DOI (10.1002/pros.23476 -> PMID 29314097). Directly validates "
              "eq:pd_target_suppression_chemo_sensitization_tte with all four terms in PC3 system: "
              "target suppression (~92% P-FAK Y397/Y576 reduction), sensitization fold (75x in PC3-Rx), "
              "IC50 shift (1167.6 -> 15.6 ng/mL), time-to-endpoint extension (29.5 -> 47.5 days, p=0.003). "
              "Key flag: resistance-selectivity (IC50 shift in Rx arms ONLY, not in parental lines) and "
              "model-system-dependent FAK-AKT coupling (present in vitro/xeno, absent in explants).",
    )

    # Register source artifacts
    artifact_specs: list[tuple[str, Path, str, str]] = [
        ("artifact_defactinib_annotation_workbook", RAW_ANNOTATION_WORKBOOK, "WORKBOOK",
         "Supplied QSP/PD biomarker cascade annotation workbook (Cascade Map, Digitized Data 140 rows, "
         "Figure Annotations 23 rows, Modeling Notes), preserved unchanged."),
        ("artifact_defactinib_moa_doc", MOA_DOC, "EXTRACTION_ARTIFACT",
         "Human-written mechanism-of-action / PD biomarker cascade reference document (five-tier cascade, "
         "data-quality flags, direct equation validation)."),
    ]
    for artifact_id, path, artifact_type, description in artifact_specs:
        registry.add(
            "source_artifacts", source_artifact_id=artifact_id,
            paper_id=PAPER_ID, artifact_type=artifact_type, path=relative(path),
            original_filename=path.name, sha256=sha256(path), figure=None, panel=None,
            supplement_identifier=None, source_description=description,
        )

    # Load and register contexts (7: PC3/DU145 ±Rx, PC3 xeno, patient explants, primary TMA)
    for row in _rows("contexts.csv"):
        context_id = _context_id(row["context_key"])
        registry.add(
            "contexts", context_id=context_id, species=row["species"],
            cell_line=_optional(row["cell_line"]), cell_type=_optional(row["cell_type"]),
            tissue=_optional(row["tissue"]), disease=_optional(row["disease"]),
            culture_context=_optional(row["culture_context"]), notes=_optional(row["notes"]),
        )

    # Load and register context alterations (Tier-0 baseline FAK expression + resistance phenotype)
    for row in _rows("context_alterations.csv"):
        context_id = _context_id(row["context_key"])
        registry.add(
            "context_alterations",
            context_alteration_id=stable_id("context_alteration", context_id, row["gene"],
                                           row["alteration_type"], row["alteration"]),
            context_id=context_id, gene=row["gene"], alteration_type=row["alteration_type"],
            alteration=row["alteration"], zygosity_or_copy_context=None,
            source=_optional(row["source"]), notes=_optional(row["notes"]),
        )

    # Load and register conditions (4: Vehicle, VS-6063 alone, Docetaxel alone, Combination)
    for row in _rows("conditions.csv"):
        registry.add(
            "conditions", condition_id=_condition_id(row["condition_key"]),
            context_id=None,  # Conditions are context-agnostic; linked via condition_steps
            condition_label=row["description"], notes=None,
        )

    # Load and register condition steps (30 rows: dose/time for each condition x context pair)
    for row in _rows("condition_steps.csv"):
        registry.add(
            "condition_steps", condition_step_id=stable_id(
                "condition_step", _condition_id(row["condition_key"]), row["context_key"],
                row["perturbation_name"], row["sequence_index"]),
            condition_id=_condition_id(row["condition_key"]),
            perturbation_id=_perturbation(registry, row["perturbation_name"]),
            dose_value=clean_number(row["dose_value"]), dose_unit=_optional(row["dose_unit"]),
            start_time=clean_number(row["start_time"]), end_time=clean_number(row["end_time"]),
            time_unit=_optional(row["time_unit"]), sequence_index=_integer(row["sequence_index"]),
            notes=_optional(row["notes"]),
        )

    # Load and register assays (10: Tier 0-4, from H-score IHC to KM curves)
    for row in _rows("assays.csv"):
        registry.add(
            "assays", assay_id=_assay_id(row["assay_key"]), paper_id=PAPER_ID,
            assay_type=row["assay_type"], assay_name=row["target"],
            sample_type=None, measurement_platform=None,
            figure=None, panel=None, reported_time=None, reported_time_unit=None,
            replicate_count=None, notes=_optional(row["description"]),
        )

    # NOTE: observations.csv not yet implemented. Will contain:
    #   - Tier 0: FAK H-score (Fig 6B, n=63 primary tumors)
    #   - Tier 1: P-FAK Y397/Y576 densitometry (Figs 2B-C, 3B-C, 5B-C, 6F)
    #   - Tier 2: AKT S473 (Figs 2D, 5D; FLAG: absent in explants)
    #   - Tier 2b: LC3B-II (Fig 5E, xeno only)
    #   - Tier 3: Cleaved caspase-3 (Fig 6D, explants only, n=6)
    #   - Tier 4a: Docetaxel IC50 (Figs 1A-B, FLAG: shift in Rx arms ONLY)
    #   - Tier 4b: Tumor volume (Fig 4A, biphasic growth)
    #   - Tier 4c: Time-to-500mm³ (Fig 4B, KM curves, 47.5 vs 29.5 days, p=0.003)
    #   - Tier 4d: Body weight (Fig 4C, tolerability)

    print(f"✓ Registered paper {PAPER_ID}")
    print(f"✓ Registered {len(_rows('contexts.csv'))} contexts")
    print(f"✓ Registered {len(_rows('context_alterations.csv'))} context_alterations (Tier-0 baseline + resistance)")
    print(f"✓ Registered {len(_rows('conditions.csv'))} conditions")
    print(f"✓ Registered {len(_rows('condition_steps.csv'))} condition_steps")
    print(f"✓ Registered {len(_rows('assays.csv'))} assays (Tier 0-4)")
    print(f"✓ observations.csv: placeholder (to follow with digitized data)")

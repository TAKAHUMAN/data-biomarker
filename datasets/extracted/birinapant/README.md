# Birinapant extraction package

This package normalizes Krepler et al. 2013 (PMID 23403634, PMCID PMC3618495,
*The novel SMAC mimetic birinapant exhibits potent activity against human
melanoma cells*, Clin Cancer Res 19(7):1784-1794) into the same registry
structure as the other drug datasets. The supplied observations workbook,
the QSP/biomarker digitization workbook, the supplied draft JSON, the
supplied draft importer, and the mechanism-of-action reference document are
all preserved unchanged under `datasets/raw/workbooks/` and
`datasets/extracted/birinapant/`.

Registry-ready tables:

- `contexts.csv`
- `conditions.csv`
- `condition_steps.csv`
- `assays.csv`
- `observations.csv`
- `extraction_metadata.json`

Audit and annotation exports (from `birinapant_qsp_biomarker_digitization.xlsx`):

- `recommended_qsp_inputs.csv` — Figure 5B author-bar cIAP1 percent-of-vehicle
  digitization with approximate SEM, by xenograft model and timepoint
- `raw_densitometry_digitization.csv` — image-derived Figure 3A band
  intensities (cIAP1/XIAP, normalized to GAPDH and to vehicle)
- `method_and_caveats.csv` — the workbook author's own digitization method
  notes and caveats

## What the source contains

Seventeen melanoma cell lines were tested with birinapant alone and in
combination with TNF-alpha, revealing a three-tiered phenotype (confirmed by
spot-checking the open full text): one single-agent-sensitive line (WM9),
nine combination-sensitive lines, and seven resistant lines. cIAP1
degradation occurs in essentially all lines regardless of phenotype, so
resistance sits downstream of target engagement. The package covers viability
IC50s, apoptosis markers (sub-G1, Annexin V, PARP cleavage), NF-kB/RIP1
signaling, cIAP1/XIAP target-engagement kinetics (in vitro and in xenograft
tumor tissue), 3D spheroid validation, mechanistic reversal experiments
(Z-VAD-FMK, Necrostatin-1, TNF-alpha blocking mAb), dosing-schedule
dependency, BRAF-inhibitor-resistant subline cross-resistance, cisplatin
combination sensitization, and in vivo xenograft tumor growth/target
engagement/caspase-3 IHC.

## Normalization notes

- Each of the 170 `Observations` sheet rows was classified by its
  `Measurement` text into one of 16 experiment categories, each mapped
  programmatically to a context (2D/spheroid/xenograft/pooled-group), a
  condition with explicit dose/time `condition_steps` (not `dose=None`
  placeholders, unlike the supplied draft importer), an assay, and an
  observable. One row (`Activated caspase-3 positive cells (IHC)`, Figure
  5C) explicitly covers both 451Lu and 1205Lu xenografts and was split into
  two observations, giving 171 registry rows from 170 source rows.
- Two additional t=0 vehicle-baseline observations for the Figure 5B cIAP1
  kinetic curve were added from the QSP workbook's `Recommended input`
  sheet (not present in `BIRINAPANT_OBSERVATIONS.xlsx`), and its approximate
  SEM values were joined onto the eight matching Figure 5B post-dose
  cIAP1-remaining observations. See `extraction_metadata.json`
  `corrections` for the full list.
- Figure 3A cIAP1/XIAP kinetics are recorded as qualitative blot calls
  (`cIAP1_protein_level_status`); the underlying image-derived band
  intensities remain available for inspection in
  `raw_densitometry_digitization.csv` but are not promoted to numeric
  observations, because the QSP workbook's own method notes flag the
  reconstruction as unreliable for precise EC50 fitting.
- The Figure 6D cisplatin-combination cell line label ("451Lu (or panel
  line)") is ambiguous in the source workbook; it is mapped to the 451Lu in
  vitro context as the best-supported reading and flagged in the caveats.
- Figure 3D RIPK1 mRNA values are pooled sensitive/resistant group means
  (not per-cell-line) and are attached to two pooled-cohort contexts rather
  than individual cell-line contexts.
- The supplied draft importer (`supplied_birinapant_importer.py`) used an
  incompatible old dataclass API and carried an incorrect paper title; it is
  preserved as provenance but was not executed. `importers/birinapant.py` is
  a fresh importer using the current generic `Registry.add(table, **row)`
  API, matching the barasertib/cilengitide pattern.

Regenerate and validate with:

```powershell
py -3 datasets/tools/prepare_birinapant.py
py -3 datasets/tools/build_registry.py
py -3 datasets/tools/validate_registry.py
```

Tests: `py -3 -m pytest datasets/tools/tests/test_birinapant_importer.py -q`

## What's still needed for full QSP calibration

This is a rich PD, target-engagement, and apoptosis-mechanism evidence
package, but it is not a standalone QSP dataset. No plasma pharmacokinetic
or exposure data, receptor occupancy assay, or dose-to-plasma-concentration
mapping is reported in the source, so the 30 mg/kg IP xenograft dose and the
0.1-1000 nM/uM in vitro concentrations are not linked to a PK model without
external data. A modeller wanting exposure-response calibration will need
to supply PK data separately.

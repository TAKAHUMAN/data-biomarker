# Cilengitide extraction package

This package normalizes Bretschi et al. 2013 (PMID 23229276, PMCID
PMC11824361) into the same registry structure as the other drug datasets.
The supplied workbook is preserved unchanged under `datasets/raw/workbooks/`.

Registry-ready tables:

- `contexts.csv`
- `conditions.csv`
- `condition_steps.csv`
- `assays.csv`
- `observations.csv`
- `extraction_metadata.json`

Audit and annotation exports:

- `pet_panel_digitization.csv` — all 60 approximate Figure 2 bar/SE rows
- `gene_expression_source.csv` — 43 direct log2 values plus clearly labelled derived formulas
- `study_design.csv`
- `model_mapping_suggestions.csv`
- `data_gaps.csv`

Figure 2 displays each group/day/PET parameter twice in pairwise panels. To
avoid double-weighting the same animals, the registry contains 30 canonical
PET observations formed as the median of each pair of panel digitizations.
The 43 Table 1 log2 expression changes enter the registry directly. Suggested
model mappings and gap-handling notes remain annotations; they are not treated
as experimental observations or executable instructions.

Regenerate and validate with:

```powershell
py -3 datasets/tools/prepare_cilengitide.py
py -3 datasets/tools/build_registry.py
py -3 datasets/tools/validate_registry.py
```

This is a useful PD evidence package, not a complete standalone QSP dataset.
External PK/exposure, target potency or occupancy, and longitudinal disease
outcome data are still needed for full QSP calibration.

# AMG 900 / Aurora-inhibitor extraction package

This package normalizes the Noronha et al. study of AMG 900,
AZD1152-HQPA, and MK-5108 in SW-872, 93T449, and HCT-116 cells.

The study is indexed under AMG 900 while retaining the two comparator
inhibitors. The supplied workbook, JSON, narrative, and draft importer are
preserved unchanged. The draft importer is provenance only and is not executed.

Generated registry-ready tables:

- `contexts.csv`
- `conditions.csv`
- `condition_steps.csv`
- `assays.csv`
- `observations.csv`
- `extraction_metadata.json`

Regenerate, build, and validate with:

```powershell
py -3 datasets/tools/prepare_amg900.py
py -3 datasets/tools/build_registry.py
py -3 datasets/tools/validate_registry.py
```

Important corrections are recorded in `extraction_metadata.json`. In
particular, the authoritative paper identifier is PMID 29197031, and the
AZD1152-HQPA EC50 for 93T449 is 74.5 nM. Plot-derived points are explicitly
semi-quantitative, and Western-blot calls are qualitative image observations.

The full paper PDF is not present. The publicly accessible article figures are
preserved under `datasets/raw/images/amg900` for extraction provenance.

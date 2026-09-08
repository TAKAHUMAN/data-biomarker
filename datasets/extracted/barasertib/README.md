# Barasertib extraction package

This package normalizes Helfrich et al. 2016 (PMID 27496133, PMCID
PMC5050114). In-vitro experiments used the active metabolite
barasertib-HQPA; the H841 xenograft experiment used parent barasertib.

The supplied workbook, JSON, and draft importer are preserved unchanged. The
draft importer is provenance only and is not executed.

Generated registry-ready tables:

- `contexts.csv`
- `conditions.csv`
- `condition_steps.csv`
- `assays.csv`
- `observations.csv`
- `extraction_metadata.json`

Regenerate and validate with:

```powershell
py -3 datasets/tools/prepare_barasertib.py
py -3 datasets/tools/build_registry.py
py -3 datasets/tools/validate_registry.py
```

Important source corrections are listed in `extraction_metadata.json`.
Unsupported exact IC50 guesses are not treated as reported measurements; the
source-supported `IC50 < 50 nM` result is encoded using registry censoring.
Exact Table 2 ploidy values and numeric xenograft volumes reported in the
Results are retained. DMS114, omitted from the supplied observation rows, is
restored as the 23rd screened line using its source-defined response class.

# Alisertib extraction package

This directory contains the normalized extraction intermediates for Sehdev et
al. 2012 (PMID 22302096, PMCID PMC3297687).

The immutable curator workbook is stored at
`datasets/raw/workbooks/Alisertib_MLN8237_Registry_Ready.xlsx`. The originally
supplied tumor-endpoint JSON is preserved here as `REGISTRY_IMPORT_DATA.json`.

Generated tables:

- `contexts.csv`: biological contexts used by the observations;
- `conditions.csv`: reusable treatment conditions;
- `condition_steps.csv`: one row per drug in a regimen, retaining both doses in
  combination treatments;
- `assays.csv`: assay definitions and source locations;
- `observations.csv`: one quantitative observation per row;
- `extraction_metadata.json`: counts, source hashes, and extraction caveats;
- `figure_4_provenance.json`: provenance for the supplied Day-21 xenograft
  observations.

Regenerate these files with:

```powershell
py -3 datasets/tools/prepare_alisertib.py
```

Then rebuild and validate the registry:

```powershell
py -3 datasets/tools/build_registry.py
py -3 datasets/tools/validate_registry.py
```

The package deliberately does not invent intermediate Figure 4 curve points.
Paper-reported endpoint values, plot-derived measurements, and subjective image
annotations retain distinct extraction methods and quality classes.

The original paper PDF is still required at
`datasets/raw/papers/PMID_22302096_PMC3297687.pdf` for complete source
preservation.

# Biomarker dataset workspace

This workspace contains an independent copy of the `datasets/` subtree from
[JosephKangas/cell_signal_transduction_prototyping](https://github.com/JosephKangas/cell_signal_transduction_prototyping),
copied from commit `b944aeda4c2f715a7eadb6cd6a721b4838b59d2e` on 2026-09-07.

Only the dataset layer was copied. The source repository's unrelated BioModels,
experiments, fitted results, visualizations, and working models were intentionally
left out.

## Included drug datasets

| Drug | Extracted folder | Parsed observations | Main raw source |
|---|---|---:|---|
| Foretinib | `datasets/extracted/foretinib/` | 120 | Excel workbook |
| Luminespib | `datasets/extracted/luminespib/` | 62 | Excel workbook |
| Pemigatinib | `datasets/extracted/pemigatinib/` | 72 | Paper and supplements |
| Tepotinib | `datasets/extracted/tepotinib/` | 122 | Paper and source figure |
| Alisertib (MLN8237) | `datasets/extracted/alisertib/` | 93 | Excel workbook and JSON |
| AMG 900 (with AZD1152-HQPA and MK-5108 comparators) | `datasets/extracted/amg900/` | 66 | Excel, JSON, and source figures |
| Barasertib (AZD1152) | `datasets/extracted/barasertib/` | 45 | Excel, JSON, PMC full text, and source figures |
| Cilengitide (EMD 121974) | `datasets/extracted/cilengitide/` | 73 | Excel, paper, and Figure 2 source image |

The correct spellings used by the copied data are **luminespib** and
**tepotinib**.

## Where to upload new data

Keep original files unchanged and place them by artifact type:

- Workbooks: `datasets/raw/workbooks/`
- Papers: `datasets/raw/papers/`
- Supplementary files: `datasets/raw/supplementary/`
- Source images: `datasets/raw/images/`

For each new drug or study, create `datasets/extracted/<study_name>/` for
digitized tables, cleaned CSV files, extraction metadata, provenance, and a
`registry_import_manifest.json`.

The intended data flow is:

```text
RAW -> EXTRACTED -> REGISTRY -> QUERY/COHORT -> EXPERIMENT
```

Do not edit the Parquet registry tables by hand. A new source also needs an
importer under `datasets/tools/importers/` and registration in
`datasets/tools/build_registry.py`. Then install the single dependency and
rebuild and validate the registry:

```powershell
py -3 -m pip install -r datasets/tools/requirements.txt
py -3 datasets/tools/build_registry.py
py -3 datasets/tools/validate_registry.py
```

See `datasets/README.md` and
`datasets/paper_data_extraction_storage_standard.md` for the canonical rules.

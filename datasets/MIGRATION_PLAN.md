# Dataset-registry migration plan

## Inventory recorded before migration

| Study | Immutable source | Existing extraction/reader | Consumer dependency |
|---|---|---|---|
| Foretinib/FLT3-ITD | `lab_data/foretinib/foretinib_experimental_data.xlsx` (SHA-256 `754413029a5319293f1e5879ce9ef4800bca1032b5331f04d062397c128c740d`) | direct OOXML reader in `experiments/foretinib_flt3_itd/fitting/workbook_data.py` | fitting scripts and its experiment test |
| Luminespib/HSP90 | `lab_data/luminespib_pd_drug_only.xlsx` (SHA-256 `FD7063B2864418B432E934112B192A9266056D1CA7A29044100A1BA96F1F0638`) | direct OOXML reader in `experiments/luminespib_hsp90/fitting/workbook_data.py` | fitting scripts and its experiment test |
| Pemigatinib/FGFR | PMID 32315352 paper and supplements under `tmp/pdfs/` | experiment-local CSV, JSON, and blot-densitometry files | `calibrate_proximal_target.py` read `data/observations.csv` |

`lab_data/foretinib/foretinib_data.py` is an unreferenced legacy digitization script with a separate Wang et al. AML data scope. It is preserved as an extracted legacy artifact and is not silently mixed with the FLT3-ITD workbook study.

Existing result reports contain historical raw paths.  They are retained unchanged because they are derived fit/report artifacts.  Only live readers and manifests are updated.

## Migration sequence

1. Move native workbooks/paper/supplements to `datasets/raw/`, and extraction artifacts to `datasets/extracted/`.
2. Build all standardized records deterministically into Parquet tables.
3. Replace live experiment-local data readers with registry compatibility readers while preserving their return values.
4. Add explicit registry observation selection to experiment manifests.
5. Validate table schemas, keys, controlled vocabularies, source hashes, deterministic record content, reader equivalence, and the unchanged canonical-model hash.

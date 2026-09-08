# Experimental dataset registry

This directory is the canonical data layer for the cell-signaling project.

`raw/` contains immutable, native source artifacts (workbooks, papers, supplements, and source images).  `extracted/` contains parsing, digitization, densitometry, and other extraction intermediates.  `registry/` contains the authoritative, standardized Parquet tables built from those inputs. `query_registry.py` provides the sole generic read-only selection layer; experiments consume registry observation IDs. `exports/` is reserved for derived analysis and future training exports.

The distinctions are mandatory:

- source data != extracted data
- extracted data != standardized observation
- observation != model coordinate
- model fit != source data

Model-specific interpretations are stored only in `registry/model_mappings.parquet`; the experimental observation records remain model-independent.  Unknown values are null rather than inferred.

Install `datasets/tools/requirements.txt`, then run `py -3 datasets/tools/build_registry.py` after source or extraction changes and `py -3 datasets/tools/validate_registry.py` afterward. The build sorts stable semantic IDs and is deterministic at the record level.

The intended flow is `RAW -> EXTRACTED -> REGISTRY -> QUERY/COHORT -> EXPERIMENT`.

A dynamic query is for discovery: it can legitimately return more observations after a future registry addition. A frozen cohort manifest records the registry semantic digest, query provenance, and—authoritatively—the selected `observation_ids`; use it for reproducible calibration or validation. A CSV or Parquet export is a disposable derived representation of that frozen cohort, never a second source of truth.

Examples:

```powershell
py -3 datasets/tools/query_registry.py --drug pemigatinib --observable pERK
py -3 datasets/tools/query_registry.py --cell-line KG1a --time-h 2 --format csv
py -3 datasets/tools/create_cohort_manifest.py --cohort-id kg1a_2h_perk --description "KG1a 2 h pERK" --pmid 32315352 --cell-line KG1a --time-h 2 --observable pERK --export parquet
```

Future ML train/validation/test partitions should normally be split at the paper or study level—not randomly by observation—to prevent leakage among nearby doses and conditions from the same source figure.

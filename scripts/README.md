# QSP/PD Biomarker Data Utilities

Python tools for loading, validating, and preparing biomarker datasets for quantitative systems pharmacology (QSP) and pharmacodynamic (PD) modeling.

## Scripts

### `validate_datasets.py`
Validate all biomarker datasets for data integrity.

**Run:**
```bash
python scripts/validate_datasets.py
```

**Checks:**
- CSV files present and readable
- CSV format validity (headers, rows)
- Observation counts per drug
- Flags incomplete/missing datasets

**Example output:**
```
📊 VALIDATING extracted
================================================================================
✅ dordaprivone_ovarian      | 222 observations
✅ ganetespib_escc           | 54 observations
✅ evofosfamide_breast       | 51 observations
...
================================================================================
✅ Complete: 16/16 drugs
📈 Total observations: 1,700+
📚 Average obs/drug: 106
✅ Validation complete!
```

---

### `biomarker_loader.py`
Load and combine biomarker datasets programmatically.

**Classes:**
- `BiomarkerDataset`: Load a single drug
- `MultiDrugDataset`: Manage multiple drug datasets

**Basic Usage:**

```python
from biomarker_loader import BiomarkerDataset

# Load single drug
data = BiomarkerDataset('dordaprivone_ovarian')
print(data.observations.head())  # DataFrame

# Load multiple drugs
multi = BiomarkerDataset.load_multiple([
    'dordaprivone_ovarian',
    'ganetespib_escc',
    'niraparib_hcc'
])
all_obs = multi.combined_observations()

# Load all available drugs
all_drugs = BiomarkerDataset.load_all()
print(all_drugs.summary())  # Summary table
```

**API Reference:**

#### BiomarkerDataset

```python
data = BiomarkerDataset(drug_name, extracted_dir=None)

# Attributes:
data.observations   # pd.DataFrame
data.assays         # pd.DataFrame
data.conditions     # pd.DataFrame
data.contexts       # pd.DataFrame
data.metadata       # dict (from JSON)
data.readme         # str (README.md content)

# Methods:
data.summary()      # Dict with obs/assay/condition/context counts
str(data)          # Print friendly representation
```

#### MultiDrugDataset

```python
multi = BiomarkerDataset.load_multiple(['drug1', 'drug2'])
# OR
multi = BiomarkerDataset.load_all()

# Attributes:
multi.datasets      # Dict[drug_name -> BiomarkerDataset]

# Methods:
multi.combined_observations()   # Concatenate all obs (adds 'drug' column)
multi.get_drug(name)            # Get single BiomarkerDataset
multi.drug_names()              # List all loaded drugs
multi.summary()                 # pd.DataFrame with obs/assay counts per drug
str(multi)                      # Print friendly representation
```

---

### `example_usage.py`
Complete examples for loading and preparing biomarker data for modeling.

**Run:**
```bash
python examples/example_usage.py
```

**Demonstrates:**
1. Load single drug dataset
2. Filter by quality class and data source
3. Load multiple drugs for comparison
4. Prepare dose-response curves
5. Extract mechanistic cascade data (Tier 1→2→3→4)
6. Identify synergy/combination effects
7. Read drug-specific mechanistic notes
8. Export combined data for R/Stan/NONMEM

---

## Data Structure

Each drug folder (`datasets/extracted/<drug_name>/`) contains:

| File | Purpose |
|------|---------|
| `observations.csv` | All quantitative measurements (rows = data points) |
| `assays.csv` | Assay definitions & measurement types |
| `conditions.csv` | Experimental conditions (doses, timepoints) |
| `contexts.csv` | Cell lines, tissues, disease models |
| `README.md` | Mechanism of action, data quality notes, modeling guidance |
| `extraction_metadata.json` | Paper info, extraction summary |

### observations.csv Columns

| Column | Type | Example |
|--------|------|---------|
| `observation_key` | str | `"obs_1"` |
| `assay_key` | str | `"viability_assay_1"` |
| `condition_key` | str | `"dose_0_time_24h"` |
| `value` | float | `45.3` |
| `unit` | str | `"% viability"` or `"nM (IC50)"` |
| `quality_class` | str | `"QUANTITATIVE"` or `"SEMI_QUANTITATIVE"` |
| `uncertainty_type` | str | `"stdev"` (optional) |
| `uncertainty_value` | float | `2.1` (optional) |
| `notes` | str | `"pixel-digitized from Fig 1C"` |

### Quality Flags in `notes`

| Flag | Confidence | Use for |
|------|------------|---------|
| `explicit from text` | ✅✅✅ | Parameter fitting |
| `printed in legend` | ✅✅✅ | IC50 constants (highest quality) |
| `visual est. from bar chart` | ✅✅ | Constraints, priors |
| `pixel-digitized` | ✅✅ | Curves, secondary confirmation |
| `SEMI_QUANTITATIVE` | ✅ | Relative comparisons, not absolute fits |

---

## Workflow Examples

### 1. Extract IC50 Values for Dose-Response Fitting

```python
from biomarker_loader import BiomarkerDataset

data = BiomarkerDataset('evofosfamide_breast')

# Get IC50 data only
ic50 = data.observations[data.observations['unit'].str.contains('IC50')]
print(ic50[['condition_key', 'value', 'unit', 'notes']])

# Value is ready to use as constant in your model
```

### 2. Build Mechanistic Cascade Model

```python
# Example: Dordaprivone (ONC201) - death pathway cascade
data = BiomarkerDataset('dordaprivone_ovarian')

# Extract each tier of cascade
tier1 = data.observations[data.observations['assay_key'].str.contains('target')]
tier2 = data.observations[data.observations['assay_key'].str.contains('pathway')]
tier3 = data.observations[data.observations['assay_key'].str.contains('apoptosis')]
tier4 = data.observations[data.observations['context_key'].str.contains('xenograft')]

# Fit tier 1→2→3→4 cascade equations using your modeling tool
print(f"Tier 1 targets: {len(tier1)} obs")
print(f"Tier 2 pathways: {len(tier2)} obs")
print(f"Tier 3 cell phenotype: {len(tier3)} obs")
print(f"Tier 4 in vivo growth: {len(tier4)} obs")
```

### 3. Multi-Drug Comparative Analysis

```python
multi = BiomarkerDataset.load_all()

# Get all apoptosis data across drugs
all_obs = multi.combined_observations()
apoptosis = all_obs[
    all_obs['assay_key'].str.contains('apoptosis|caspase')
]

# Compare IC50s by drug
print(apoptosis.groupby('drug')['value'].agg(['count', 'min', 'max', 'mean']))
```

### 4. Export for External QSP Tools

```python
all_drugs = BiomarkerDataset.load_all()
all_obs = all_drugs.combined_observations()

# Clean export
export = all_obs[[
    'drug', 'observation_key', 'assay_key', 'value', 'unit'
]].copy()

export.to_csv('qsp_data.csv', index=False)
# Use in R/Stan/NONMEM with drug stratification
```

---

## Dependencies

- `pandas` (data manipulation)
- `openpyxl` (if reading raw Excel — not needed for CSV utilities)

Install:
```bash
pip install pandas openpyxl
```

---

## File Locations

Assuming standard folder structure:

```
data-biomarker/
├── scripts/
│   ├── validate_datasets.py
│   ├── biomarker_loader.py
│   └── README.md (this file)
├── examples/
│   └── example_usage.py
└── datasets/
    └── extracted/
        ├── dordaprivone_ovarian/
        │   ├── observations.csv
        │   ├── assays.csv
        │   ├── conditions.csv
        │   ├── contexts.csv
        │   └── README.md
        └── [15 more drugs...]
```

If folders are in different locations, pass `extracted_dir` parameter:

```python
data = BiomarkerDataset(
    'dordaprivone_ovarian',
    extracted_dir=Path('/path/to/datasets/extracted')
)
```

---

## Troubleshooting

### `FileNotFoundError: Drug folder not found`
- Check folder name matches exactly (case-sensitive on Linux/Mac)
- Verify `datasets/extracted/<drug_name>/` folder exists
- Run `python scripts/validate_datasets.py` to list all available drugs

### `Empty DataFrame` warning
- Some drugs may not have specific CSVs (e.g., no uncertainty data)
- Check drug README.md to understand what data was extracted

### Unicode/encoding errors
- Ensure files are UTF-8 encoded
- Windows PowerShell: may need `chcp 65001` to enable UTF-8
- Python 3.7+: UTF-8 is default

---

## Questions?

See [USAGE.md](../USAGE.md) for overview and quick-start guide.

---

Last updated: 2026-09-08

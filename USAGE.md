# QSP/PD Biomarker Data - Usage Guide

Welcome! This repository contains digitized and annotated biomarker data from 16 published cancer studies, ready for quantitative systems pharmacology (QSP) and pharmacodynamic (PD) modeling.

## 🚀 Quick Start

### 1. Validate Your Data
```bash
python scripts/validate_datasets.py
```
Checks all 16 drugs for data integrity and completeness.

### 2. Load Data for Modeling
```python
from scripts.biomarker_loader import BiomarkerDataset

# Load a single drug
data = BiomarkerDataset('dordaprivone_ovarian')
print(data.observations.head())
print(data.assays)

# Load multiple drugs
multi = BiomarkerDataset.load_multiple([
    'dordaprivone_ovarian',
    'ganetespib_escc',
    'niraparib_hcc'
])

# Get combined data
all_observations = multi.combined_observations()
summary = multi.summary()
```

### 3. Load All Available Drugs
```python
from scripts.biomarker_loader import BiomarkerDataset

# Load all 16 complete datasets at once
all_drugs = BiomarkerDataset.load_all()
print(all_drugs.summary())  # Summary table
print(all_drugs.combined_observations())  # All observations
```

---

## 📊 Available Datasets (16 drugs, 1700+ observations)

| Drug | Cancer Type | Obs | Key Data |
|------|------------|-----|----------|
| **Dordaprivone (ONC201)** | Ovarian | 222 | Apoptosis cascade, ROS, in vivo tumor growth |
| **Ganetespib (STA-9090)** | ESCC | 54 | HSP90 inhibitor, MYC pathway, CDX+PDX |
| **Evofosfamide (TH-302)** | Breast | 51 | **Hypoxia-activated prodrug**, selectivity |
| **Motesanib (AMG 706)** | GIST | 11 | **Genotype-stratified KIT inhibition** |
| **Niraparib (PARP inhibitor)** | HCC | 25 | **PARP + autophagy synergy** |
| **Dactolisib (BEZ235)** | Multiple | 318 | Dual PI3K/mTOR inhibition |
| **Dinaciclib** | Multiple | 438 | CDK inhibitor (largest dataset!) |
| **Defactinib** | Prostate | 45 | FAK inhibitor + docetaxel synergy |
| **+ 8 more** | Various | 500+ | Alisertib, AMG900, Barasertib, etc. |

---

## 📁 Data Structure

Each drug folder contains:

```
dordaprivone_ovarian/
├── observations.csv          # All digitized data points
├── assays.csv               # Assay definitions & platforms
├── conditions.csv           # Experimental conditions (doses, timepoints)
├── contexts.csv             # Cell lines, tissues, disease models
├── README.md                # Mechanistic insights & modeling notes
└── extraction_metadata.json # Paper info & extraction summary
```

### observations.csv columns:
- `observation_key`: Unique identifier
- `assay_key`: Links to assays.csv
- `condition_key`: Links to conditions.csv
- `value`: The measured value
- `unit`: Measurement unit (nM, %, relative fold-change, etc.)
- `quality_class`: QUANTITATIVE or SEMI_QUANTITATIVE
- `notes`: Data source (explicit, visual estimate, pixel-digitized, etc.)

---

## 🎯 Usage Examples

### Example 1: Extract IC50 Values
```python
from scripts.biomarker_loader import BiomarkerDataset

data = BiomarkerDataset('dordaprivone_ovarian')

# Get all IC50 observations
ic50_data = data.observations[data.observations['unit'].str.contains('IC50|uM')]
print(ic50_data[['condition_key', 'value', 'unit', 'notes']])
```

### Example 2: Filter by Assay Type
```python
# Get all viability/apoptosis data across drugs
multi = BiomarkerDataset.load_all()
all_obs = multi.combined_observations()

apoptosis = all_obs[all_obs['assay_key'].str.contains('apoptosis|caspase')]
print(apoptosis.groupby('drug')['observation_key'].count())
```

### Example 3: Build a Dose-Response Curve
```python
import matplotlib.pyplot as plt

data = BiomarkerDataset('evofosfamide_breast')

# Filter for a specific condition
dose_response = data.observations[
    data.observations['condition_key'].str.contains('dose')
].sort_values('value')

plt.plot(dose_response['value'], 'o-')
plt.xlabel('Dose (µM)')
plt.ylabel('Viability (%)')
plt.title('Evofosfamide Dose-Response')
plt.show()
```

---

## 📚 Mechanistic Insights

Each drug's README.md contains:

- **Source paper**: PMID, DOI, full citation
- **Mechanism of action**: How the drug works
- **PD cascade**: Tier 1 (target) → Tier 2 (pathway) → Tier 3 (cell-level) → Tier 4 (in vivo)
- **Cell lines/models**: What was tested
- **Data quality notes**: Explicit vs. visual estimates, pixel-digitization methods
- **Modeling recommendations**: Suggested QSP equation structures

**Example:** Motesanib is a **genotype-stratified KIT inhibitor** where IC50 varies by mutation type (primary activating, secondary imatinib-resistant). The README explains why a single IC50 constant would misrepresent the data.

---

## 🔍 Data Quality Flags

Look for in the `notes` column:

| Flag | Meaning |
|------|---------|
| `explicit from text` | Printed in paper results |
| `printed in legend` | Highest confidence (IC50 values) |
| `visual est. from bar chart` | Visually read from figure |
| `pixel-digitized` | Programmatically extracted from axis |
| `SEMI_QUANTITATIVE` | Western blot densitometry (carry uncertainty) |

---

## ⚙️ For Modelers: Recommended Workflow

1. **Start with the README** for each drug to understand the mechanism
2. **Check `quality_class`** before fitting — QUANTITATIVE vs SEMI_QUANTITATIVE
3. **Read the `notes`** to see if values are explicit (text/legend) or visual estimates
4. **Use `contexts.csv`** to identify cell lines and stratify by cancer type
5. **Cascade tiers** in README suggest how to structure your PD model (which assays feed into which downstream effects)

---

## 📞 Questions?

- **Data gaps?** Check the README's "Not Quantifiable" section — qualitative-only figures are documented
- **Uncertainty?** Quality flags and notes tell you the extraction method and confidence
- **Missing a drug?** 2 legacy format drugs (foretinib, luminespib) can be converted if needed

---

## 🔗 Repository

**GitHub:** https://github.com/TAKAHUMAN/data-biomarker

---

Happy modeling! 🚀

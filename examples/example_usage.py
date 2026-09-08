#!/usr/bin/env python3
"""
Example: Loading and Using QSP/PD Biomarker Data for Model Building

This notebook demonstrates how to load biomarker data and prepare it for
quantitative systems pharmacology (QSP) and pharmacodynamic (PD) modeling.
"""

import pandas as pd
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / 'scripts'))
from biomarker_loader import BiomarkerDataset


# ============================================================================
# EXAMPLE 1: Load a Single Drug Dataset
# ============================================================================
print("=" * 80)
print("EXAMPLE 1: Load a Single Drug")
print("=" * 80)

data = BiomarkerDataset('dordaprivone_ovarian')
print(f"\nLoaded: {data}")
print(f"\nObservations shape: {data.observations.shape}")
print(f"Columns: {list(data.observations.columns)}")
print("\nFirst 5 observations:")
print(data.observations.head())

print(f"\n\nAvailable assays ({len(data.assays)}):")
print(data.assays[['assay_key', 'assay_name', 'measurement_type']].head(10))

print(f"\n\nExperimental conditions ({len(data.conditions)}):")
print(data.conditions[['condition_key', 'dose_value', 'timepoint_hours']].head(10))


# ============================================================================
# EXAMPLE 2: Filter Data by Quality and Type
# ============================================================================
print("\n" + "=" * 80)
print("EXAMPLE 2: Filter High-Quality Data for Fitting")
print("=" * 80)

# Get only quantitative data (exclude semi-quantitative Western blots if you prefer)
quantitative = data.observations[data.observations['quality_class'] == 'QUANTITATIVE']
print(f"\nQuantitative observations: {len(quantitative)} / {len(data.observations)}")

# Get observations from specific sources (highest confidence)
explicit_data = quantitative[quantitative['notes'].str.contains('explicit|printed')]
print(f"Explicit (printed in paper): {len(explicit_data)} observations")

# Example: Extract IC50 values
ic50_data = data.observations[data.observations['unit'].str.contains('IC50', na=False)]
print(f"\nIC50 values: {len(ic50_data)}")
if len(ic50_data) > 0:
    print(ic50_data[['assay_key', 'condition_key', 'value', 'unit']].head())


# ============================================================================
# EXAMPLE 3: Load Multiple Drugs for Comparative Analysis
# ============================================================================
print("\n" + "=" * 80)
print("EXAMPLE 3: Load Multiple Drugs")
print("=" * 80)

multi = BiomarkerDataset.load_multiple([
    'dordaprivone_ovarian',
    'ganetespib_escc',
    'niraparib_hcc',
    'evofosfamide_breast'
])

print(f"\nLoaded {len(multi.datasets)} drugs")
print("\nDataset Summary:")
summary = multi.summary()
print(summary.to_string(index=False))

# Combine observations
all_obs = multi.combined_observations()
print(f"\n\nCombined observations: {len(all_obs)} total rows")
print(f"Observations per drug:")
print(all_obs.groupby('drug')['observation_key'].count())


# ============================================================================
# EXAMPLE 4: Prepare Data for Dose-Response Fitting
# ============================================================================
print("\n" + "=" * 80)
print("EXAMPLE 4: Dose-Response Curve Preparation")
print("=" * 80)

# Filter for viability/apoptosis dose-response data
data = BiomarkerDataset('evofosfamide_breast')
viability_assays = data.observations[
    data.observations['assay_key'].str.contains('viability|apoptosis', na=False)
]

print(f"Viability/apoptosis observations: {len(viability_assays)}")
print("\nExample observations for curve fitting:")

# Show data organized by context/cell line
for context_key in viability_assays['context_key'].unique()[:3]:
    context_data = viability_assays[viability_assays['context_key'] == context_key]
    print(f"\n  {context_key}: {len(context_data)} points")
    print(f"    Values: {sorted(context_data['value'].dropna().values)}")
    print(f"    Units: {context_data['unit'].unique()[0]}")


# ============================================================================
# EXAMPLE 5: Extract Mechanistic Cascade Data
# ============================================================================
print("\n" + "=" * 80)
print("EXAMPLE 5: Mechanistic Cascade (Multi-Tier PD)")
print("=" * 80)

# Dordaprivone has rich cascade data: target -> pathway -> cell-level -> in vivo
data = BiomarkerDataset('dordaprivone_ovarian')

# Tier 1: Direct target engagement
tier1 = data.observations[
    data.observations['assay_key'].str.contains('target|engagement', na=False, case=False)
]
print(f"Tier 1 (Direct target): {len(tier1)} obs")

# Tier 2: Pathway/signaling effects
tier2 = data.observations[
    data.observations['assay_key'].str.contains('protein|pathway|phosph', na=False, case=False)
]
print(f"Tier 2 (Pathway proteins): {len(tier2)} obs")

# Tier 3: Cell-level phenotypes
tier3 = data.observations[
    data.observations['assay_key'].str.contains('viability|apoptosis|cycle|ros', na=False, case=False)
]
print(f"Tier 3 (Cell-level): {len(tier3)} obs")

# Tier 4: In vivo effects
tier4 = data.observations[
    data.observations['context_key'].str.contains('xenograft|tumor|vivo', na=False, case=False)
]
print(f"Tier 4 (In vivo): {len(tier4)} obs")

print("\nRecommended PD model structure:")
print("  Target engagement -> MAPK/Akt pathway -> Apoptosis cascade -> Tumor growth")


# ============================================================================
# EXAMPLE 6: Identify Synergy/Combination Effects
# ============================================================================
print("\n" + "=" * 80)
print("EXAMPLE 6: Combination/Synergy Data")
print("=" * 80)

# Defactinib has FAK inhibitor + docetaxel combinations
data = BiomarkerDataset('defactinib')

# Look for combination conditions
combo_obs = data.observations[
    data.observations['condition_key'].str.contains('combo|combination', na=False, case=False)
]

if len(combo_obs) > 0:
    print(f"\nCombination observations: {len(combo_obs)}")
    print("\nIC50 values (monotherapy vs combination):")
    ic50 = combo_obs[combo_obs['unit'].str.contains('IC50', na=False)]
    if len(ic50) > 0:
        print(ic50[['condition_key', 'value', 'unit', 'notes']])


# ============================================================================
# EXAMPLE 7: Extract Drug-Specific Modeling Insights
# ============================================================================
print("\n" + "=" * 80)
print("EXAMPLE 7: Read Mechanistic Notes from README")
print("=" * 80)

# Motesanib has important genotype stratification
data = BiomarkerDataset('motesanib_gist')
print("\n--- Motesanib (Genotype-Stratified KIT Inhibitor) ---")
print(data.readme[:500])

# Check assays defined
print("\n\nAssays in dataset:")
print(data.assays[['assay_key', 'assay_name', 'measurement_type']].to_string(index=False))


# ============================================================================
# EXAMPLE 8: Export Data for External Analysis
# ============================================================================
print("\n" + "=" * 80)
print("EXAMPLE 8: Export Combined Data for R/Stan/NONMEM")
print("=" * 80)

# Load all drugs
all_drugs = BiomarkerDataset.load_all()
all_obs = all_drugs.combined_observations()

# Create export-friendly format
export_data = all_obs[[
    'drug', 'observation_key', 'assay_key', 'value', 'unit', 'quality_class'
]].copy()

print(f"\nExported {len(export_data)} observations across {all_drugs.datasets.__len__()} drugs")
print("\nSample export data:")
print(export_data.head(10))

# Save to CSV for downstream modeling tools
# export_data.to_csv('qsp_biomarker_export.csv', index=False)
# print("\n✓ Saved to 'qsp_biomarker_export.csv'")


# ============================================================================
# SUMMARY
# ============================================================================
print("\n" + "=" * 80)
print("SUMMARY: Next Steps for QSP Modeling")
print("=" * 80)
print("""
1. ✓ Load drug dataset(s) using BiomarkerDataset
2. ✓ Filter by quality_class and notes (quantitative/explicit data preferred)
3. ✓ Organize by assay_key and context_key for your PD cascade model
4. ✓ Read README.md for mechanistic insights and modeling recommendations
5. ✓ Fit dose-response curves (IC50 extraction already done)
6. ✓ Build Tier 1→2→3→4 cascade equations based on data structure
7. ✓ Export clean data for R/Stan/NONMEM with 'drug' column for multi-drug analysis

Questions?
- Check USAGE.md in repo root for API documentation
- Check drug-specific README.md for mechanistic guidance
- Run validate_datasets.py to check data integrity
""")

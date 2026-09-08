# Motesanib (AMG 706) KIT-Mutant GIST Dataset

Genotype-stratified kinase inhibition: direct ATP-competitive KIT inhibition across 7 clinically relevant genotypes.

## Data

- **7 KIT genotypes:** WT + 3 primary activating (Delta552-559, V560G, W557_K558del) + 3 imatinib-resistant (V654A, Y823D, D816V)
- **IC50 values:** Motesanib vs imatinib across all genotypes (Table 2/3, printed ground truth)
- **Assays:** Biochemical (CHO KIT autophosphorylation) + Functional (Ba/F3 viability)
- **Key finding:** Motesanib shows genotype-dependent potency variation (most potent vs primary mutants, less vs WT). Retains Y823D activity where imatinib fails.

## Mechanistic Innovation

This is a **genotype-stratified kinase inhibition** archetype: IC50 varies primarily by KIT mutation class, not by a single population parameter. Resistance mutations (D816V) are structurally incompatible with both drugs' binding mode (DFG-out inactive conformation).

## Model Recommendation

Genotype-indexed Emax/Hill occupancy model with categorical 'DFG-compatible' flag for resistance classification.

# Aurora Kinase Inhibitors in Liposarcoma — Mechanism of Action

**Paper:** Noronha et al. 2017  
**Journal:** In Vitro Cell Dev Biol—Animal  
**Published:** December 1, 2017  
**DOI:** 10.1007/s11626-017-0208-4

---

## PRIMARY MECHANISM OF ACTION

### Aurora Kinase Function
- **AURKA (Aurora Kinase A)**
  - Localizes near the centrosome
  - Recruits substrate proteins to promote bipolar spindle formation
  - Required for centrosome maturation and proper kinetochore assembly
  - Essential for accurate chromosome segregation during mitosis

- **AURKB (Aurora Kinase B)**
  - Associates with kinetochores and centromeres
  - Regulates chromosome segregation and cytokinesis
  - Phosphorylates histone H3 and other chromosomal passenger complex (CPC) substrates
  - Prevents aberrant mitotic progression

- **AURKC (Aurora Kinase C)**
  - Most abundantly expressed in reproductive tissue
  - Targeted by pan-Aurora inhibitors like AMG 900

### Inhibition Consequences
Blocking Aurora kinases → **Mitotic catastrophe** → Polyploidy → G2/M arrest → Apoptosis

---

## THREE INHIBITORS WITH DISTINCT SELECTIVITY PROFILES

### 1. AMG 900 — Pan-Aurora Kinase Inhibitor
- **Selectivity:** Inhibits AURKA, AURKB, and AURKC equally
- **Mechanism:** Binds ATP-binding pocket (non-selective)
- **Effect:** 
  - Most potent cell viability inhibition (EC50 3.7 nM SW-872; 1.4 nM HCT-116)
  - Strong dose-dependent polyploidy induction starting at 25 nM (SW-872)
  - Largest fold-increase in polyploidy (~8-9 fold in SW-872; ~2.4-3 fold in 93T449)
  - Causes large polyploid cells visible by microscopy (Figs. 2E-F, 3E-F)

### 2. AZD1152-HQPA — AURKB-Selective Inhibitor
- **Selectivity:** Primarily targets AURKB; lesser activity against AURKA
- **Mechanism:** Selective ATP-competitive inhibitor
- **Effect:**
  - Intermediate potency (EC50 43.4 nM both liposarcoma lines; 27.3 nM HCT-116)
  - Significant polyploidy induction but delayed compared to AMG 900 (starts ~100 nM in SW-872)
  - Consistent with AURKB role in cytokinesis: blocks cell division → binucleate/polyploid cells
  - Less effective in 93T449 (well-differentiated) vs SW-872 (undifferentiated)

### 3. MK-5108 — AURKA-Selective Inhibitor
- **Selectivity:** Primarily targets AURKA; lesser activity against AURKB (becomes AURKB-inhibitory at >500 nM)
- **Mechanism:** AURKA-selective ATP-competitive inhibitor
- **Effect:**
  - Least potent on viability (EC50 309 nM SW-872; 135.1 nM HCT-116)
  - **Minimal polyploidy induction** even at 500–1000 nM
  - Suggests AURKA inhibition alone insufficient for polyploidy in these cell lines
  - AURKB appears more critical for cytokinesis defects in liposarcoma

---

## DIFFERENTIAL SENSITIVITY BETWEEN LIPOSARCOMA SUBTYPES

### SW-872 (Undifferentiated) — HIGHLY RESPONSIVE
- **AURKA mRNA:** ~32–40 fold upregulation vs adipocytes
- **AURKB mRNA:** ~100–200 fold upregulation vs adipocytes
- **AURKA Protein:** Clearly detectable ~48 kDa band (Fig. 5A)
- **AURKB Protein:** Strong band + smaller splice variant detected (Fig. 5D)
- **Polyploidy response:**
  - AMG 900: 8–9 fold increase (baseline ~20% → ~90% at 1000 nM)
  - AZD1152-HQPA: 3.1 fold increase (starts ~100 nM)
  - MK-5108: No significant effect

**Interpretation:** Undifferentiated liposarcoma cells are addicted to Aurora kinase activity. Loss of both AURKA and AURKB (via pan-inhibitor) or AURKB alone (via selective inhibitor) causes catastrophic polyploidy.

### 93T449 (Well-Differentiated) — MODERATELY RESPONSIVE
- **AURKA mRNA:** ~31 fold upregulation vs adipocytes (similar to SW-872)
- **AURKB mRNA:** ~50–100 fold upregulation (lower than SW-872)
- **AURKA Protein:** Faint/minimal band (Fig. 5C)
- **AURKB Protein:** Strong band detectable (Fig. 5D)
- **Polyploidy response:**
  - AMG 900: 2.4–3 fold increase (baseline ~25% → ~60% at 1000 nM)
  - AZD1152-HQPA: Minimal response
  - MK-5108: No significant effect

**Interpretation:** Well-differentiated liposarcoma cells retain some Aurora kinase expression but are more resistant to inhibition. May reflect increased p53 dysfunction (wild-type in 93T449 vs proficient in SW-872) or differential splicing of AURKB.

### HCT-116 (Colorectal Cancer) — POSITIVE CONTROL
- **AURKA mRNA:** ~40 fold increase
- **AURKB mRNA:** ~202 fold increase (highest of all)
- **Most sensitive to AMG 900:** EC50 1.4 nM
- Confirms Aurora kinase inhibitors are active; validates assay

---

## BIOMARKERS OF AURORA KINASE INHIBITION

### Primary Readout: Polyploidy (% >4N DNA)
- **Method:** Propidium iodide staining + FACS analysis
- **Sensitivity:** Dose-dependent and kinase-selective
- **Interpretation:** 
  - Pan-inhibitor (AMG 900) > AURKB-selective (AZD1152) > AURKA-selective (MK-5108)
  - Suggests cytokinesis (AURKB) more critical than spindle assembly (AURKA) for preventing polyploidy in these cells

### Secondary Readouts:
1. **Aurora Kinase mRNA expression** (RT-PCR)
   - AURKA and AURKB highly expressed in SW-872, intermediate in 93T449
   - Correlates with inhibitor sensitivity

2. **Aurora Kinase protein levels** (Western blot)
   - AURKA present in undifferentiated liposarcoma; absent in well-differentiated
   - AURKB splice variants: AURKB-Sv2 detected in some cancer cells but not normal tissue
   - Isoform profile may dictate inhibitor response

3. **Cell viability** (MTT assay; EC50 values)
   - Direct measure of inhibitor potency
   - 100–200 fold difference in EC50 between inhibitors (MK-5108 vs AMG 900 in SW-872)

---

## DIFFERENTIATION STATUS DETERMINES SENSITIVITY

**Key Finding:** Undifferentiated liposarcoma (SW-872) is dramatically more sensitive to Aurora kinase inhibitors than well-differentiated liposarcoma (93T449).

- **Undifferentiated:** High AURKA + High AURKB → dependent on Aurora kinases for cell division
- **Well-differentiated:** Similar/Higher AURKA mRNA but lower/absent AURKA protein; High AURKB → may have alternative survival pathways

**Implication for QSP modeling:** The differentially regulated AURKA/AURKB ratio and the presence of splice variants (AURKB-Sv2) could be incorporated as phenotypic switches in a tumor heterogeneity model.

---

## SUMMARY TABLE

| Parameter | SW-872 | 93T449 | HCT-116 |
|-----------|--------|--------|---------|
| **AURKA mRNA (fold vs adipocytes)** | 32–40 | 31 | 40 |
| **AURKB mRNA (fold vs adipocytes)** | 100–200 | 50–100 | 202 |
| **AURKA Protein** | Present (48 kDa) | Minimal/Faint | Faint |
| **AURKB Protein** | Strong + variant | Strong + variant | Strong |
| **AMG 900 EC50** | 3.7 nM | 6.5 nM | 1.4 nM |
| **AZD1152 EC50** | 43.4 nM | 43.4 nM | 27.3 nM |
| **MK-5108 EC50** | 309 nM | 283.6 nM | 135.1 nM |
| **Polyploidy fold-change (AMG 900)** | 8–9× | 2.4–3× | High |
| **Differentiation status** | Undifferentiated | Well-differentiated | N/A |
| **p53 status** | Proficient | Wild-type | Mutant |

---

## CLINICAL RELEVANCE

Aurora kinase inhibitors show selective activity against **undifferentiated liposarcoma**, which is the more aggressive form. The pan-inhibitor (AMG 900) shows >80-fold selectivity between undifferentiated and well-differentiated liposarcoma, suggesting potential therapeutic window in patients with high-grade tumors.

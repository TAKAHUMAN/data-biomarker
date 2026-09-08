# Defactinib (VS-6063, FAK Inhibitor) + Docetaxel in Prostate Cancer

**Single-paper extraction and validation study**

**Paper:** Lin H-M, Lee BY, Castillo L, *et al.* "Effect of FAK inhibitor VS-6063 (defactinib) on docetaxel efficacy in prostate cancer." *The Prostate* 2018;1-10. DOI: [10.1002/pros.23476](https://doi.org/10.1002/pros.23476), PMID: [29314097](https://pubmed.ncbi.nlm.nih.gov/29314097/).

**Extraction status:** Contexts, conditions, assays registered. Observations (digitized data) placeholder.

---

## Overview

This dataset directly validates the four-term quantitative equation in your pipeline:
```
eq:pd_target_suppression_chemo_sensitization_tte
  (target_suppression → sensitization_fold → IC50_shift → time_to_endpoint_extension)
```

All four terms are measurable from a single, internally consistent experimental system (**PC3/PC3-Rx**):

| Equation term | Value | Source |
|---|---|---|
| **target_suppression** | 91–92% reduction (P-FAK Y397/Y576, 1.00-1.10 → 0.09-0.10) | Fig 2B-C |
| **sensitization_fold** | 75-fold (IC50: 1167.6 → 15.6 ng/mL) | Fig 1A |
| **IC50_shift** | −1152 ng/mL absolute | Fig 1A |
| **time_to_endpoint_extension** | 1.6-fold (median 29.5 → 47.5 days to 500 mm³, p=0.003) | Fig 4B |

An independent replicate validation is available in the **DU145/DU145-Rx** pair (target suppression ≈88–90%, sensitization 43-fold, IC50 shift from 2499.6 to 58.0 ng/mL), though without an in vivo time-to-endpoint arm.

---

## Five-Tier Cascade

### **Tier 0 — Baseline Biomarker: FAK Expression vs. Disease Grade**

- **Context:** Primary prostate cancer, treatment-naive (n=63 tissue microarray)
- **Biomarker:** FAK H-score IHC (%positive × intensity)
- **Finding:** Higher in Gleason 6, 7, 9 vs Gleason 5 (p=0.05, 0.03, 0.02); Gleason 8 n.s. (n≈4, underpowered)
- **Model role:** Context covariate (stratification variable), NOT a drug-response endpoint. Structurally analogous to cyclin E1 (CCNE1) in the dinaciclib extraction.
- **Figure:** Fig 6A-B

### **Tier 1 — Target Modulation: P-FAK Y397 and Y576 Autophosphorylation**

**Consistent pattern across all five model systems:**
> Docetaxel alone → partial suppression  
> VS-6063 alone → larger suppression  
> Combination → deepest suppression

- **PC3/PC3-Rx (Fig 2B-C):** Y397 and Y576 move together (single lumped FAK-activation state); PC3-Rx shows 91–92% reduction in combination.
- **DU145/DU145-Rx (Fig 3B-C):** Y397 and Y576 **partially separable** here (VS-6063 alone: Y397 1.00→0.12 vs Y576 1.00→0.53). Normalized to β-actin (not T-FAK); don't compare absolute ratios to PC3 panels.
- **PC3 xenograft (Fig 5B-C):** Same pattern as PC3 in vitro; in vivo target engagement is deep.
- **Patient explants (Fig 6F):** Y397 could not be reliably detected; Y576 only, but shows significant suppression with VS-6063 alone (p=0.01).

**Key encoding rule:** Treat docetaxel as having a measurable on-target FAK-suppression contribution. Do not model combination as "VS-6063 + inert chemotherapy"; use an interaction term.

### **Tier 2 — Downstream Signaling: AKT(S473), mTOR, LC3B (Autophagy)**

**⚠ FLAG: Model-System-Dependent Coupling**

- **PC3 in vitro (Fig 2D):** AKT S473 tracks FAK suppression cleanly. DTX alone suppresses AKT more than VS-6063 alone (ratio 0.16 vs 0.43 in PC3-Rx).
- **PC3 xenograft (Fig 5D):** AKT phosphorylation responds similarly to FAK suppression in vivo.
- **Patient explants (Fig 6G):** **No significant AKT change** with any treatment (p=0.71, 0.27, 0.22 for DTX/VS6/combo vs control). **This is a genuine negative result, not a technical failure.** Possible explanations: stromal dilution of signal, differential AKT regulation in cancer cells *vs.* stroma, or greater stroma-cancer crosstalk in explant architecture — but the paper does not confirm which.

**Implication:** The FAK → p85/PI3K → AKT edge may be context-dependent. If building a mechanistic model, consider gating AKT as downstream of FAK in PC3/xenograft systems but as independent (or weakly coupled) in patient-derived contexts. This is a model-structure decision, not a parameter-fitting problem.

**Autophagy marker (Fig 5E, xenograft only):**
- LC3B-II accumulation: 1.95 → 3.40 relative fold with combination treatment, interpreted as autophagic cell death.
- p-mTOR(S2448) and p62 are image-only (not densitometry-quantified), so LC3B-II is the only numerically fittable autophagy node from this paper alone.

### **Tier 3 — Cell-Death Execution: Cleaved Caspase-3 (Apoptosis)**

- **Context:** Ex vivo patient-derived CSPC explants (n=6 evaluable of 11 enrolled)
- **Biomarker:** Cleaved caspase-3 IHC, % positive cancer cells
- **Finding:**
  - DTX alone (p=0.21): n.s. vs control
  - VS-6063 alone (p=0.88): n.s. vs control
  - **Combination (p=0.04):** 6.5% → 16.0% positive cells ✓ **Significant synergy signature**

- **Model role:** Synergy checkpoint for validating mechanistic models built from other tiers. **NOT suitable for curve-fitting:** only four discrete conditions (no dose-ranging within explants), so this tier is qualitative-validation class rather than quantitative.
- **Figure:** Fig 6C-D

### **Tier 4 — Tumor / Efficacy Endpoint**

#### **In Vitro Chemosensitization (IC50, Figs 1A-B)**

**⚠ FLAG: Resistance-Selectivity is the Central Finding**

Docetaxel IC50 shifts **ONLY in docetaxel-resistant sublines**, NOT in parental lines:

| Context | Parental IC50 | Resistant IC50 | Fold Shift | +VS-6063 Shift | P-value |
|---|---|---|---|---|---|
| **PC3** | 28.7 ng/mL | — | — | Not significant | — |
| **PC3-Rx** | — | 1167.6 ng/mL | **41-fold resistant** | **75-fold sensitization** (→15.6 ng/mL) | p<0.0005 |
| **DU145** | 28.7 ng/mL | — | — | Not significant | — |
| **DU145-Rx** | — | 2499.6 ng/mL | **87-fold resistant** | **43-fold sensitization** (→58.0 ng/mL) | p<0.0001 |

**Model implication:** If this equation is meant to generalize across a tumor population with mixed sensitivity/resistance profiles, sensitization_fold **must be gated by (or made a function of) baseline resistance status**. Using a single population constant (75x or 43x) would misapply the resistant-subline value to naturally-sensitive disease. Consider:
- Baseline docetaxel IC50 (or some proxy for resistance) as an effect modifier.
- Sensitization fold as a logistic or piecewise function of baseline IC50 or baseline P-FAK level.

#### **In Vivo Tumor Growth (Fig 4A)**

**⚠ FLAG: Biphasic Response (Regression + Regrowth)**

The combination arm does **not** follow a monotonic sigmoid saturation curve:
- **Day 0–21:** Transient tumor regression to ~85% of peak (~day 19–21).
- **Day 21–35:** Slow regrowth despite continued dosing.

**Model implication:** A simple Emax TGI model will not capture this without additional terms:
- **Simeoni-type TGI model** with resistance-emergence (rate of resistance development over time).
- **Or:** effective-drug-exposure-decay term (pharmacokinetic loss or efflux/metabolism increase).
- **Or:** tumor-growth-heterogeneity (subpopulation with intrinsic resistance emerges during treatment).

The biphasic growth curve is the **underlying mechanism** for the time-to-progression Kaplan-Meier result (Section below).

#### **Time-to-Tumor-Progression (500 mm³ Endpoint, Fig 4B)**

- **Method:** Kaplan-Meier log-rank test, n=14–15 mice per arm.
- **Primary comparison:** DTX + Vehicle vs **DTX + VS-6063** (not all four arms pooled).
  - **DTX alone:** median 29.5 days
  - **DTX + VS-6063:** median 47.5 days
  - **Extension:** 1.6-fold, p=0.003
  
- **Validation:** Our pixel-digitized step curves independently reproduce these medians (47.3 and 28.2 days at 50%-crossing points), providing internal validation of the digitization pipeline.

- **Model role:** This is the `time_to_endpoint_extension` output of your equation. It is the **integrated consequence** of the underlying biphasic tumor-growth curve (Fig 4A), not an independent mechanism — both are now available if a mechanistic (rather than purely descriptive) TTE model is desired.

#### **Tolerability (Fig 4C)**

- **Body weight:** Mean trough ~87% of initial (day 14–17).
- **Individual variability:** 5/15 mice (33%) had weight loss up to 26%, fully recovered post-regimen.
- **Toxicity grade:** No mortality or treatment discontinuation attributable to toxicity.

---

## Data-Quality Flags and Digitization Confidence

| Figure | Data Quality | Notes |
|---|---|---|
| **Fig 1A/1B (IC50 curves)** | Mixed | Top series (Rx + DTX, filled circles) is pixel-exact (dose ladder cross-validated to ±5%). Other series overlap above 40 ng/mL; visual estimates ±2–3 pp. |
| **Fig 4A (tumor volume)** | High (with exception) | Red and blue arms pixel-exact. Black arm (saline+vehicle) had black arrow glyphs contaminating RGB detection; corrected by visual reading. |
| **Fig 4B (Kaplan-Meier)** | High (DTX arms) | DTX-containing arms pixel-digitized end-to-end; cross-validate tightly against printed medians. Saline arms: visual estimates only (contaminated by overlapping elements). |
| **Fig 6B (Gleason-7 scatter, n≈32)** | Semi-quantitative | Point overlap too dense for individual recovery; reported as distribution range + mean (not 32 single points). Mean/SEM error bar read exactly. |
| **Overall duplication check** | Passed | No outright duplication errors detected (unlike dinaciclib Fig 5A). Printed values internally consistent with pixel-digitized independent reads. |

---

## Recommended Before Handoff

1. **Observations CSV:** Digitize Figures 1–6 (all 10 assays, ≈80–100 observation rows expected).
2. **PK data:** Not reported in this paper. A PK-PD link requires external input or PK modeling assumptions.
3. **Individual patient-level explant data (Fig 6D/F/G):** Could remove residual point-reading uncertainty; author data request recommended.
4. **Dose-ranging in explants:** Only four discrete conditions tested for caspase-3; cannot support continuous dose-response fit as-is.
5. **Model structure choice for FAK→AKT coupling:** Decide whether to:
   - Use conditional nodes (presence/absence of AKT response by context).
   - Use a switching function gated by stromal fraction or culture format.
   - Fit separate model coefficients per context (PC3 vs. explants).

---

## Source Artifacts

- `Defactinib_QSP_PD_Biomarker_Cascade_Annotations.xlsx` — Cascade Map, Digitized Data (140 rows), Figure Annotations (23 rows), Modeling Notes. Preserved unchanged.
- `Defactinib_QSP_PD_Biomarker_Cascade.md` — Companion human-written MOA cascade reference (read first).

---

## Registry Structure

| Table | Rows | Notes |
|---|---|---|
| **Contexts** | 7 | PC3/DU145 ±Rx (in vitro), PC3 xenograft, patient explants, primary TMA |
| **Context_alterations** | 3 | Tier-0 FAK H-score baseline (primary TMA); docetaxel resistance phenotype (PC3-Rx, DU145-Rx) |
| **Conditions** | 4 | Vehicle, VS-6063 alone, Docetaxel alone, Combination |
| **Condition_steps** | 30 | Dose/time/schedule for each condition × context pair |
| **Assays** | 10 | H-score IHC, P-FAK densitometry (×2), AKT/LC3B, caspase-3, IC50, tumor volume, time-to-progression, body weight |
| **Observations** | 0 (pending) | To include all digitized bar charts, curves, scatter plots, and KM step curves |

---

## Key References

- See `extraction_metadata.json` for PMID resolution details, data-quality caveats, and four-term equation validation summary.
- See companion MOA doc (`Defactinib_QSP_PD_Biomarker_Cascade.md`) for detailed pathway interpretation and model recommendations.

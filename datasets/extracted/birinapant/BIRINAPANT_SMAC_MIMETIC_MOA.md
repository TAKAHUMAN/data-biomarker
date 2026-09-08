# Birinapant (TL32711), SMAC Mimetic in Melanoma — Mechanism of Action

**Paper:** Krepler et al. 2013  
**Journal:** Clinical Cancer Research  
**Published:** February 12, 2013  
**DOI:** 10.1158/1078-0432.CCR-12-2518  
**PMID:** 23403634

---

## PRIMARY MECHANISM OF ACTION

### SMAC Mimetic Class: cIAP1/cIAP2 Antagonism

#### Birinapant Selectivity Profile
- **Drug class:** Bivalent, selective small molecule peptidomimetic of Smac tetrapeptide
- **Design basis:** Based on N-terminal amino acids of Smac/DIABLO (Ala-Val-Pro-Ile) and caspase-9 (Ala-Thr-Pro-Phe)
- **Binding affinity (Kd):**
  - XIAP: 45 nM
  - cIAP-1: <1 nM
- **Target selectivity:** Specifically targets cIAP1 and cIAP2 for degradation; XIAP not affected by birinapant at therapeutic doses

#### Inhibitor of Apoptosis (IAP) Family
- **IAP function:** Family of proteins defined by baculoviral IAP repeats (BIR)
- **IAP members:** XIAP, cIAP1, cIAP2, ML-IAP, survivin
- **Role in cancer:** Up-regulated in melanoma; confer chemoresistance and poor prognosis
- **Control mechanism:** IAPs are controlled by SMAC (Second Mitochondria-Derived Activator of Caspases)
  - SMAC released from mitochondria upon apoptosis onset
  - SMAC binds directly to IAPs → IAP degradation

### TNF Receptor (TNFR) Signaling Switch

#### Mechanism Without Birinapant (cIAP1/cIAP2 present)
1. TNF-α binds to TNFR
2. TNFR complex-I assembly (membrane-localized):
   - TNFRSF1A associated via death domain (TRADD)
   - Ubiquitin ligases TRAF2, TRAF5, **cIAP1, cIAP2**
   - Protein kinase RIPK1
3. Result: Ubiquitination cascade → NF-κB pathway activation → **cell proliferation**

#### Mechanism With Birinapant (cIAP1/cIAP2 degraded)
1. Birinapant binding → cIAP1/cIAP2 degradation (sustained ≥24h at 30-100 nM doses)
2. TNF-α binds to TNFR
3. Without cIAP1/cIAP2: Death complex formation → RIPK1-dependent pathway
4. Result: **Caspase-8 activation → apoptosis** (reversal from proliferation to cell death)

#### NF-κB Signaling Perturbation
- SMAC mimetics perturb NF-κB signaling downstream of TNFR
- In sensitive cells: cIAP1/cIAP2 degradation → decrease in NF-κB p65 protein levels (WM9 only)
- NF-κB2 p100 levels increase with TNF-α; return to baseline with birinapant + TNF-α combination

### Apoptosis Dependency
- **Caspase-dependent:** Z-VAD-FMK (pan-caspase inhibitor) completely blocks birinapant + TNF-α cell death
- **RIP1 kinase-dependent:** Necrostatin-1 (RIP1 inhibitor) completely reverses birinapant + TNF-α effect
- **RIP1 depletion:** RIP1 protein depleted in 3/4 combination-sensitive cell lines during combination treatment

---

## MELANOMA BIOLOGY AND SMAC MIMETIC VULNERABILITY

### Melanoma Genetic Heterogeneity
- **Five major genetic subgroups tested:**
  - BRAF V600E mutations (~50% of cutaneous melanoma)
  - NRAS mutations (~25%)
  - KIT mutations
  - CTNNB1/β-catenin mutations
  - Triple wild-type (no major pathway mutation)

### Anti-Apoptotic Mechanisms in Melanoma
- **Chronic inflammation:** Tumor-infiltrating immune cells (macrophages, lymphocytes) generate elevated TNF-α
  - TNF-α normally promotes proliferation (pro-tumor)
  - TNF-α as single agent: no anti-tumor effect; minimal clinical benefit with significant toxicity
- **IAP up-regulation:** Conserved inhibitor of apoptosis proteins (XIAP, cIAP1, cIAP2, ML-IAP, survivin) highly expressed
  - Mechanism of therapy resistance
  - Attractive therapeutic target

### Why Birinapant Sensitivity Varies
1. **cIAP1 target engagement occurs in ALL cell lines tested** (confirmed by Western blot degradation)
   - Resistance is NOT due to lack of target engagement
2. **Apoptosis downstream of cIAP1 degradation depends on additional factors:**
   - TNF-α signaling competence (endogenous or exogenous)
   - RIP1 kinase availability
   - Caspase-8 activation capacity
   - Possible alternative survival pathway activation in resistant lines

---

## THREE-TIERED SENSITIVITY PHENOTYPE IN 17 MELANOMA LINES

### Pattern A: Single Agent Sensitive (1/17 lines, 6%)
**Cell line: WM9 (BRAFV600E)**

Phenotype:
- IC50 with birinapant alone: **2.7 nM** (digitized from Figure 1); IC50 with birinapant + TNF-α: **2.4 nM** — WM9 is the only line of 17 with a sub-1000nM single-agent IC50
- Robust apoptosis induction with birinapant alone (no TNF-α required)
- PARP cleavage: **Yes** (24h birinapant alone)
- Sub-G1 fraction (apoptosis): **Significant increase** with birinapant alone
- Annexin V positive: **Yes** with birinapant alone
- NF-κB p65: **Decreased** with birinapant ± TNF-α
- Mechanism: Dependent on endogenous TNF-α; blocking TNF-α with mAb dose-dependently abrogates birinapant effect

Clinical relevance:
- Highest sensitivity phenotype
- Effective monotherapy
- Maintains response in 3D spheroid models

### Pattern B: Combination Sensitive (9/17 lines, 53%)
**Cell lines: 451Lu (BRAFV600E), WM1366 (NRASQ61L), WTH202, WM793B, WM164, WM1341D, WM3130, WM1985, WM3854**

*[CORRECTED per Figure 1 digitization: the paper's Figure 1 groups 10 lines under the "sensitive" bracket — WM9 (single-agent) plus these 9 combination-only lines — and 7 under "resistant" (1205Lu plus 6 others), i.e. 1+9+7=17. The abstract's "twelve out of eighteen" figure refers to a different count (18 lines including the 451Lu-BR subline) and a looser "strong combination activity" criterion than the bracket grouping in Figure 1; both are noted here rather than reconciled by assumption.]*

Phenotype:
- Resistant to birinapant alone: IC50 >1000 nM (not reached, assay ceiling; grey bars capped in Figure 1)
- Resistant to TNF-α alone: No effect on cell viability
- **Strong combination activity** with birinapant + TNF-α (1 ng/ml):
  - IC50 (digitized, Figure 1, 10 combination-sensitive lines): range 1.8-226 nM — WTH202 1.8, WM793B 2.5, WM1366 2.7, WM164 7.9, 451Lu 9.0, WM1341D 57.6, WM3130 64.3, WM1985 97, WM3854 226 nM
  - >75% growth inhibition at 10 nM+ with combination
  - Neither compound effective individually but combination is "highly effective" (satisfies "coalism" definition)
- PARP cleavage: **Only with combination**, not alone
- Sub-G1 fraction: **Significant increase only with combination**
- Annexin V positive: **Only with combination**
- NF-κB2 p100: Increases with TNF-α; returns to baseline with combination
- RIP1 depletion: **Yes** in 2/2 lines with combination
- Caspase-dependent: Z-VAD-FMK completely blocks combination effect
- RIP1 kinase-dependent: Necrostatin-1 completely reverses combination effect
- **Schedule-dependent:** Birinapant followed by TNF-α (36h → 36h) effective; reverse order (TNF-α → birinapant) significantly less effective
  - Hypothesis: cIAP1/cIAP2 degradation MUST precede TNF-α-mediated TNFR activation

Subsets:
- BRAF V600E (451Lu): Responds to combination; shows identical response regardless of BRAF inhibitor resistance status
- NRAS Q61L (WM1366): Responds to combination
- Multiple genetic backgrounds (BRAF, NRAS, KIT, wild-type): Combination sensitivity independent of genetic driver

### Pattern C: Resistant (7/17 lines, 41%)
**Cell lines: 1205Lu, WM1799, UACC-62, WM3670, WM3918, C8161, WM8**

Phenotype:
- Birinapant alone: IC50 >1000 nM (not reached)
- Birinapant + TNF-α: IC50 >1000 nM (not reached; resistant to combination) — applies to all 7 resistant lines: 1205Lu, WM1799, UACC-62, WM3670, WM3918, C8161, WM8
- **cIAP1 target engagement confirmed:** cIAP1 protein degraded to similar levels as in sensitive lines (Western blot)
  - Resistance is NOT due to inability to degrade target
- PARP cleavage: **No**, even with combination
- Sub-G1 fraction: **No increase** with combination
- Annexin V positive: **No** with combination
- Apoptotic pathway blocked downstream of cIAP1 degradation

Resistance mechanism (unknown):
- NOT due to loss of RIP1 expression (Figure 3D shows no difference vs sensitive lines)
- NOT due to increased ERK1/2 phosphorylation (no differential in resistant cohort)
- NOT due to increased RAC1 levels (no differential in resistant cohort)
- Hypothesis: Alternative survival pathway activation or defective apoptotic machinery downstream of RIP1/caspase-8

---

## THREE-DIMENSIONAL SPHEROID AND IN VIVO VALIDATION

### 3D Spheroid Models (Collagen Matrix, 72h)
Response patterns conserved:
- **WM9 (single agent sensitive):** Extensive reduction in live cells with birinapant alone
- **451Lu & WM1366 (combination sensitive):** Marked decrease in live cells only with combination
- **1205Lu (resistant):** Slight growth retardation even with combination
- Alamar Blue metabolic assay confirms Live/Dead staining results
- **Conclusion:** Collagen-embedded spheroids closely mirror monolayer culture responses

### In Vivo Xenograft Studies (NUDE mice)

#### Study Design
- Two cell lines tested: 451Lu and 1205Lu
- Birinapant: 30 mg/kg, intraperitoneal (IP), 3× per week, 21 days
- Tumor volume: Measured by caliper twice weekly (V = length × width² / 2)
- Tumor sampling: 3h, 6h, 12h, 24h post-dose for pharmacodynamics

#### 451Lu Results (In vitro: combination sensitive)
- **In vivo response:** Dramatic antitumor effect as single agent
  - Significant tumor growth delay during treatment
  - Tumor growth abrogation: 2/5 animals had unmeasurable tumors at end of study
  - Sustained growth inhibition through 21 days
  - **p<0.05 vs vehicle control**
- **Mechanism:** cIAP1 degradation sustained 3-24h post-dose
  - cIAP1 levels depressed to low levels at 3h; sustained through 24h
- **Apoptosis:** Modest increase in activated caspase-3 positive cells at 24h (IHC staining)
- **Difference from in vitro:** Single agent effective in vivo despite requiring TNF-α combination in vitro

#### 1205Lu Results (In vitro: resistant)
- **In vivo response:** Marked slowing of tumor growth (partial efficacy)
  - Less sustained than 451Lu
  - Tumor growth continues despite treatment (not abrogated)
- **Mechanism:** cIAP1 degradation sustained 3-24h post-dose (same as 451Lu)
- **Apoptosis:** Similar modest increase in activated caspase-3 as 451Lu
- **Difference from in vitro:** In vitro resistant line shows growth delay in vivo

#### Interpretation
- **In vivo complexity:** Tissue microenvironment provides additional pro-apoptotic stimuli (immune infiltrates, endogenous TNF-α, microenvironment-derived factors)
- **Exogenous TNF-α not required in vivo:** Endogenous TNF-α from tumor-infiltrating immune cells likely sufficient
- **Bioavailability:** Intermittent dosing (3×/week) achieves adequate pharmacokinetics; intermittent pulsatile schedule appears preferred over continuous dosing (continuous associated with myelosuppression)

---

## SPECIAL CASES AND MECHANISM STUDIES

### BRAF Inhibitor Cross-Resistance
- **451Lu (BRAFV600E, BRAF inhibitor sensitive):** Responds to birinapant + TNF-α
- **451Lu-BR (acquired BRAF inhibitor resistance via RAF isoform switching + IGF-1R/PI3K upregulation):** Shows **identical birinapant response** to parental line
  - Conclusion: Birinapant overcomes BRAF inhibitor resistance (potential second-line therapy)

### Birinapant + Cisplatin Combination
- Two birinapant-resistant cell lines (451Lu, WM1366): Treated with cisplatin ± birinapant (100 nM)
- Result: Birinapant-mediated cIAP1 degradation **significantly enhances cisplatin sensitivity** (P<0.05)
- Suggestion: Potential combination with cytotoxic chemotherapy for resistant cases

### TNF-α Dependency and Schedule
- **WM9 (single agent sensitive):** Birinapant effect completely blocked by TNF-α neutralizing mAb (dose-dependent blocking)
  - No exogenous TNF-α added; endogenous TNF-α required
- **451Lu (combination sensitive):** Sequence matters
  - Birinapant 36h → TNF-α 36h: Significant growth inhibition
  - TNF-α 36h → Birinapant 36h: Significantly less effective
  - Mechanism: cIAP1/cIAP2 degradation must precede TNFR activation

### TNF-α Endogenous Levels
- **All four representative cell lines tested:** Comparable levels of TNF-α in 72h supernatants (Supplementary Fig S4)
- Exogenous TNF-α alone (1 ng/ml) has no effect on cell viability (Supplementary Fig S5)
- **Conclusion:** Sensitivity cannot be predicted from TNF-α production levels

---

## BIOMARKER ANALYSIS

### Genetic Background (Poor Predictor)
- **Tested:** BRAF V600E, NRAS mutations, KIT, CTNNB1, wild-type
- **Finding:** Sensitivity independent of genetic background
  - BRAF V600E: WM9 (single agent sensitive), 451Lu (combination sensitive), others intermediate
  - NRAS: Mixed responses
  - Wild-type: Mixed responses
- **Conclusion:** Genetic driver alone does not predict birinapant sensitivity

### Target Engagement (Not Predictive of Response)
- **cIAP1 degradation:** Occurs in ALL cell lines tested (sensitive and resistant)
  - Confirmed by Western blot in resistant cell line cohort (Supplementary Fig S3)
- **XIAP levels:** Not affected by birinapant (no XIAP target engagement at therapeutic doses)
- **Conclusion:** Resistance is DOWNSTREAM of cIAP1 degradation, not due to target engagement failure

### RIP1 Expression (Not Predictive)
- **Tested:** RIPK1 mRNA expression in all 17 cell lines
- **Finding:** No difference in RIPK1 expression between sensitive and resistant cohorts
  - Measured in untreated cells and TNF-α-stimulated (1 ng/ml, 24h)
- **Conclusion:** RIP1 expression alone cannot predict birinapant sensitivity despite being mechanistically required

### ERK1/2 Phosphorylation & RAC1 (Not Predictive)
- **ERK1/2:** Marked decrease in p-ERK at 24h in BOTH sensitive and resistant cohorts
  - Not differential; not predictive
- **RAC1:** Protein levels similar in sensitive vs resistant cohorts; no change upon birinapant treatment
- **Conclusion:** These signaling molecules not predictive of birinapant response

### Functional Phenotype (Predictive but Empirical)
- **Response category:** Single agent sensitive, combination sensitive, or resistant (determined empirically)
- **Apoptosis markers:** PARP cleavage, sub-G1 fraction, Annexin V positivity
- **Limitation:** Requires cell line testing; no a priori biomarker to predict response before testing

---

## CLINICAL IMPLICATIONS & BIOMARKER STRATEGY

### Key Findings Summary
- Birinapant induces apoptosis in melanoma by antagonizing cIAP1/cIAP2
- Single agent activity observed in limited subset (1/17 = 6%)
- Combination with TNF-α highly effective in a further 53% (9/17) independent of genetic background (41%, 7/17, resistant to both alone and combination)
- In vitro TNF-α addition requirement does not correlate with in vivo response (endogenous TNF-α from immune infiltrates sufficient)
- Single agent shows modest but meaningful antitumor activity in vivo, even in cells resistant in vitro

### Resistance Mechanisms (Unresolved)
- NOT due to: Genetic driver, cIAP1 target engagement failure, RIP1 loss, ERK1/2 pathway, RAC1 pathway
- Likely due to: Defective apoptotic machinery downstream of RIP1/caspase-8 (alternative pathway activation, survival signal upregulation)
- Further investigation needed to define predictive biomarker for resistant subgroup

### Recommended Biomarker Panel for Clinical Trials
1. **Functional assay:** Ex vivo cell viability testing (MTS) with birinapant ± TNF-α on patient tumor samples
   - Categorize: Single agent sensitive vs combination sensitive vs resistant
   - Compare to clinical response
2. **Exploratory mechanistic markers:**
   - cIAP1/cIAP2 protein levels (Western blot or IHC)
   - RIPK1 mRNA expression (RT-qPCR)
   - Phospho-ERK1/2, RAC1 (baseline to rule out known resistance mechanisms)
3. **Genetic characterization:**
   - BRAF, NRAS, KIT, CTNNB1 mutation status (establish genetic background)
   - Correlation with birinapant response (if any emerges)
4. **Pharmacodynamic markers (on-treatment biopsies):**
   - cIAP1 degradation (Western blot of tumor lysate)
   - Activated caspase-3 (IHC)
   - Apoptosis rate (TUNEL assay)

### Proposed Trial Design
- **Population:** Patients with cutaneous or advanced melanoma (unresectable or metastatic)
- **Phase:** Phase II (single arm with biomarker stratification, or randomized vs standard care)
- **Dosing:** Birinapant 30 mg/kg IV or IP, 3× per week (mimics preclinical efficacy schedule)
- **Combination considerations:**
  - Birinapant + TNF-α (recombinant): If combination strategy pursued (requires TNF-α toxicity mitigation)
  - Birinapant monotherapy: If leveraging endogenous TNF-α from tumor microenvironment
  - Birinapant + chemotherapy: Explore cisplatin or other DNA-damaging agents (shows synergy in vitro)
  - Birinapant + BRAF inhibitor: Test in BRAF inhibitor-resistant patients
- **Stratification:** Genetic background (BRAF/NRAS/WT); ex vivo birinapant sensitivity if feasible
- **Primary endpoint:** Overall response rate (ORR) or progression-free survival (PFS)
- **Secondary endpoints:** 
  - Overall survival (OS)
  - Biomarker correlation (ex vivo sensitivity vs on-treatment response)
  - Toxicity and tolerability

### Translational Relevance
- SMAC mimetics represent novel apoptosis-inducing strategy orthogonal to kinase inhibition
- Potential use in:
  1. BRAF/NRAS wild-type melanomas (no targeted kinase therapy)
  2. BRAF inhibitor-resistant disease (evidence: identical response to parental)
  3. Immunotherapy-resistant or -progressing patients (leverages endogenous immune TNF-α)
  4. Combination with checkpoint inhibitors (exploratory)

---

## SUMMARY TABLE

| Parameter | Single Agent Sensitive (WM9) | Combination Sensitive (451Lu, WM1366, 7 others) | Resistant (1205Lu, 6 others) |
|-----------|------------------------------|-----------------------------------------------|-----------------------------|
| **N (% of 17)** | 1 (6%) | 9 (53%) | 7 (41%) |
| **Birinapant IC50 alone** | 2.7 nM | >1000 nM (not reached) | >1000 nM (not reached) |
| **Birinapant + TNF-α IC50** | 2.4 nM | 1.8-226 nM (digitized range) | >1000 nM (not reached) |
| **Growth inhibition @ 1 µM birinapant** | >75% | <20% | <20% |
| **Growth inhibition @ 1 µM + 1 ng/ml TNF-α** | >75% | >75% | <20% |
| **PARP cleavage (birinapant alone)** | Yes | No | No |
| **PARP cleavage (combination)** | Yes | Yes | No |
| **Sub-G1 apoptosis (birinapant alone)** | Yes | No | No |
| **Sub-G1 apoptosis (combination)** | Yes | Yes | No |
| **Annexin V positive (birinapant alone)** | Yes | No | No |
| **Annexin V positive (combination)** | Yes | Yes | No |
| **cIAP1 degradation** | Yes | Yes | Yes* |
| **NF-κB p65 decrease** | Yes | No | No |
| **NF-κB2 p100 modulation** | N/A | Yes (↓ with combo) | N/A |
| **RIP1 depletion (combination)** | N/A | Yes (2/2) | No |
| **Caspase-dependent** | Yes | Yes | N/A |
| **RIP1 kinase-dependent** | Presumed | Yes | N/A |
| **TNF-α dependency** | Endogenous required | Exogenous or endogenous | N/A |
| **Schedule-dependent** | N/A | Yes (birinapant → TNF-α) | N/A |
| **3D spheroid response** | Yes | Yes | Slight only |
| **In vivo xenograft response (451Lu/1205Lu)** | N/A | Yes (451Lu: tumor abrogation) | Partial (1205Lu: growth delay) |
| **BRAF inhibitor cross-resistance** | N/A | No (451Lu-BR same response) | N/A |

*cIAP1 degraded to similar levels as sensitive lines (target engagement occurs); resistance is downstream

---

## REFERENCES

Krepler C, et al. The novel SMAC mimetic birinapant exhibits potent activity against human melanoma cells. Clin Cancer Res. 2013 Feb 12;19(7):1784–1794. doi:10.1158/1078-0432.CCR-12-2518

Key related studies:
- Li L, et al. A small molecule Smac mimic potentiates TRAIL- and TNFalpha-mediated cell death. Science. 2004;305:1471–4. (SMAC mimetic discovery)
- Varfolomeev E, et al. IAP Antagonists Induce Autoubiquitination of c-IAPs, NF-κB Activation, and TNFα-Dependent Apoptosis. Cell. 2007;131:669–81. (IAP antagonist mechanism)
- Gyrd-Hansen M, Meier P. IAPs: from caspase inhibitors to modulators of NF-kappaB, inflammation and cancer. Nat Rev Cancer. 2010;10:561–74. (IAP biology review)
- Villanueva J, et al. Acquired resistance to BRAF inhibitors mediated by a RAF kinase switch in melanoma can be overcome by cotargeting MEK and IGF-1R/PI3K. Cancer Cell. 2010;18:683–95. (BRAF inhibitor resistance context)


# Dinaciclib (CDK1/2/5/9 inhibitor) hepatocellular carcinoma (HCC) extraction package

This package normalizes **two related papers**, used together as one drug story, into
the same registry structure as the other drug datasets:

1. Xu J, Huang F, Yao Z, et al. "Inhibition of cyclin E1 sensitizes hepatocellular
   carcinoma cells to regorafenib by mcl-1 suppression." *Cell Communication and
   Signaling* 2019;17:85. **PMID 31349793, PMCID PMC6660968, DOI
   10.1186/s12964-019-0398-3.**
2. Shao Y-Y, Li Y-S, Hsu H-W, et al. "Potent Activity of Composite Cyclin Dependent
   Kinase Inhibition against Hepatocellular Carcinoma." *Cancers* 2019;11:1433.
   **PMID 31561409, PMCID PMC6827105.**

Unlike the dactolisib packages (`dactolisib_mm`, `dactolisib_ovarian`), which cover two
*unrelated* indications, these two papers are both HCC and are tied together by a
companion cascade document: dinaciclib's own four-target CDK mechanism (Shao et al.) and
cyclin E1 as a baseline biomarker for sorafenib/regorafenib resistance that dinaciclib
overcomes via STAT3->Mcl-1 suppression (Xu et al.).

There is no local paper PDF/HTML file for either study; this is a workbook +
companion-MOA-doc-only build, mirroring `importers/pemigatinib.py`'s pattern for a
real-PMID study without a local paper file (no PAPER-type `source_artifacts` row).

The three supplied, immutable-provenance inputs are preserved unchanged:

- `datasets/raw/workbooks/dinaciclib_HCC_extracted.xlsx` (Shao-et-al.-only digitized workbook)
- `datasets/raw/workbooks/Dinaciclib_QSP_PD_Biomarker_Cascade_Annotations.xlsx` (richer companion covering BOTH papers: Cascade Map, Digitized Data, Figure Annotations, Modeling Notes)
- `datasets/extracted/dinaciclib/Dinaciclib_QSP_PD_Biomarker_Cascade.md` (human-written interpretive MOA cascade guide)

Registry-ready tables:

- `contexts.csv`, `context_alterations.csv`, `conditions.csv`, `condition_steps.csv`,
  `assays.csv`, `observations.csv`, `extraction_metadata.json`

Audit and annotation export:

- `not_quantifiable_figures.csv` -- 25 rows covering Xu et al. western blots with no
  printed densitometry, cell-cycle/tumor-photo/body-weight panels, dose-response curves
  on a log[M] axis without fine enough gridline detail to digitize, and Shao et al.
  figures the source workbook's own Summary sheet marks "Skipped".

## PMID resolution for Xu et al.

No PMID was stated anywhere in either supplied workbook or the companion MD doc for the
Xu paper. Per the task brief, it was **not guessed**: it was independently confirmed via
web search (PMC6660968 -> PMID 31349793), cross-checked against the DOI landing page
(10.1186/s12964-019-0398-3) and PMC full text, both matching the paper's title, author
list, journal, volume (17:85), and 2019 date exactly. Because it could be confidently
confirmed, a real `paper_PMID31349793` id is used rather than a workbook-derived id
(contrast with `foretinib`/`luminespib`, which use workbook-derived ids because no PMID
could be found there at all).

## Tier 0 vs. dinaciclib's own mechanism

Cyclin E1 (CCNE1) is modeled as a **baseline/predictive covariate**, not a dinaciclib
pharmacodynamic response: Xu Fig3E confirms dinaciclib does not change CCNE1 expression.
High CCNE1 predicts poor HCC survival (HR=1.77, P=0.0012, TCGA/KM-plotter) and
right-shifted (more resistant) sorafenib/regorafenib dose-response curves. This is
captured via `context_alterations` rows: `alteration_type` `OTHER` for the endogenous
CCNE1-high (SK-Hep1, SNU398, Hep3B) vs CCNE1-low (Huh7, HepG2, SNU475) 6-line split (the
controlled vocabulary in `controlled_vocabularies.json` has no dedicated
expression-level type, so `OTHER` + a descriptive `alteration` string is used), and
`OVEREXPRESSION` for the engineered CCNE1-, Mcl-1-, and STAT3-plasmid rescue sublines --
the same pattern `dactolisib_mm` uses for its AKT1/BCL2-overexpression rescue sublines.

## What the source contains

**Shao et al.** (the richer quantitative source, printing exact densitometry ratios
under nearly every blot): a 4-line MTT dose-response panel with explicit IC50s (HuH7 8.5
nM, PLC5 11.8 nM, Hep3B 15.6 nM, HLE 9.7 nM), baseline Rb/p-Rb/c-myc densitometry, colony
formation, dose-dependent cell-cycle (G2/M) distribution, a full dose x time x cell-line
target-engagement densitometry grid (p-Rb/p-RNPII, Fig3A) and a matching
survival-signaling/apoptosis grid (Mcl-1/XIAP/survivin/Bcl-2/Bak/Bim/cleaved PARP-1,
Fig3B), HuH7 and PLC5 xenograft tumor-growth curves with a TUNEL apoptosis readout, and a
per-CDK siRNA-knockdown/overexpression deconvolution panel (Fig5) supporting a
CDK9~CDK1>>CDK2~CDK5 weighting for a multi-target PD structure.

**Xu et al.**: TCGA/KM-plotter CCNE1 survival analysis, a 6-line CCNE1-high/low western
blot split, CCNE1-overexpression rescue experiments (growth, IC50, apoptosis), a
Huh7/HepG2 survival time-course under 50 nM dinaciclib (pixel-digitized), the
STAT3->Mcl-1 transcriptional-suppression mechanism (ChIP, luciferase reporter,
cycloheximide-chase ruling out accelerated degradation) with two independent rescue
experiments (Mcl-1-overexpression, STAT3-overexpression), and a 4-arm in vivo Huh7
xenograft combination study (control / dinaciclib / regorafenib / dinaciclib+regorafenib)
that is the paper's central sensitization argument and the most clinically relevant
dataset in either paper.

## Normalization notes

- Xu et al. figures with no printed bar-chart/curve values in either supplied workbook,
  but an explicit approximate magnitude stated in prose in the companion Figure
  Annotations sheet (e.g. "~1.7x", "roughly halves", "~65%->~15%", "~4x"), are imported
  as `TEXT_DERIVED` / `SEMI_QUANTITATIVE` observations with the approximate value
  preserved exactly as stated and flagged as not pixel-digitized. Figures with **no**
  numeric claim at all (most Xu western blots) are captured only in
  `not_quantifiable_figures.csv`.
- The same cell line (Hep3B) appears independently in both papers' panels; each paper's
  Hep3B is kept as a distinct context (`hep3b_shao_in_vitro` vs `hep3b_xu_in_vitro`)
  rather than merged, since the two papers' assay conditions and provenance differ and
  the source materials never cross-reference the two datasets for this line.
- siRNA knockdowns (siCDK1/2/5/9, individual and composite) are modeled as
  `condition_steps` perturbations of type `GENETIC_PERTURBATION` (a new but minimal
  addition to the perturbation-type vocabulary; `perturbations.type` is a free-text
  column, not schema-constrained), the same structural role a dosed drug perturbation
  plays elsewhere in this repo.

## Data-quality flags -- preserved, not smoothed over

1. **Shao Fig5A duplicated densitometry.** The exact six-number row
   `1.78, 1.89, 1.71, 1.38, 0.65, 1.45` is printed identically under FOUR different blots
   (CDK9, p-Rb, p-ATM, p-RNPII) in the source figure -- verified by the companion
   annotation workbook's authors at 400 DPI, three re-reads. These four rows are imported
   with `quality_class = NOT_MODEL_READY` and an explicit note, **not** silently dropped
   or trusted as four independent measurements. CDK1/CDK2/CDK5 rows in the same table are
   internally distinct and imported as `QUANTITATIVE`. A smaller version of the same
   pattern appears in Shao Fig3A ("Rb (total), PLC5" identical to "p-RNPII (S2), PLC5"),
   flagged the same way. The CDK9-dominance conclusion instead rests on the separate
   (text-derived, approximate) Fig5D-E colony-formation rescue data.
2. **Tumor-volume vs. TUNEL divergence.** Shao Fig4B (HuH7 tumor volume) shows 20 and 40
   mg/kg dinaciclib as nearly superimposed (apparent plateau), while Fig4D (TUNEL
   apoptosis in the same tumors) DOES separate the two doses cleanly (~2.3x vs ~3.9x
   control). Both are imported as independent observations, never reconciled or dropped.
3. **MTT vs. colony-formation IC50 non-interchangeability.** By 72h MTT (Fig1A), HuH7 is
   the most sensitive line (8.5 nM); by 10-14 day colony formation (Fig1C-D), PLC5 is
   more sensitive at 5 nM (0.62 relative colonies vs HuH7's 0.09) -- an inversion of the
   MTT ranking. These are imported under two distinct observables
   (`viability_IC50` vs `colony_formation_relative`), never conflated into one potency
   value.

Regenerate and validate with:

```powershell
py -3 datasets/tools/prepare_dinaciclib.py
py -3 datasets/tools/build_registry.py
py -3 datasets/tools/validate_registry.py
```

Tests: `py -3 -m pytest datasets/tools/tests/test_dinaciclib_importer.py -q`

## What's still needed for full QSP calibration

**No human PK/PD or biopsy data exists in either paper** -- both are preclinical
mechanistic/xenograft studies only, same caveat as the BEZ235 cascade. Xu Fig1D-E and
Fig2C dose-response curves (sorafenib/regorafenib vs cyclin E1 status) are on a log[M]
axis without fine enough gridline detail for confident pixel calibration and are not
present as digitized points in the companion Digitized Data sheet either -- flagged for
manual digitization if exact curves (rather than the approximate magnitudes captured
here) are needed. Shao Fig4E-F (PLC5 in vivo, 13 dense timepoints) is a purely visual
read, not pixel-calibrated -- lower priority since Fig4B already anchors the monotherapy
dose-response in a cleaner 3-arm chart. Shao Fig2A-F (sub-G1/DNA-fragmentation/Annexin V)
and Fig5B-C (siRNA colony-formation bar charts) are marked "Skipped"/qualitative-only in
the source materials and have no numeric values available in either supplied workbook.
Cross-checking the flagged Fig5A densitometry against Shao et al.'s supplementary
materials (a Figure S1 is cited but not supplied) or contacting the authors would be
needed if precise per-CDK knockdown efficiencies matter for weight-fitting.

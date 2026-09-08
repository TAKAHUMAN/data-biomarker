# Dactolisib (NVP-BEZ235) multiple myeloma extraction package

This package normalizes McMillin DW, Ooi M, Delmore J, et al. "Antimyeloma
Activity of the Orally Bioavailable Dual Phosphatidylinositol 3-Kinase/
Mammalian Target of Rapamycin Inhibitor NVP-BEZ235." *Cancer Research*
2009;69(14):5835-42 (PMID 19584292, no PMCID) into the same registry
structure as the other drug datasets. There is no local paper PDF/HTML file
for this study; this is a workbook + companion-MOA-doc-only build, mirroring
`importers/pemigatinib.py`'s pattern for a real-PMID study without a local
paper file (no PAPER-type `source_artifacts` row).

The supplied curated workbook
(`dactolisib_multipleMyeloma_extracted.xlsx`), its companion QSP/PD
biomarker-cascade annotation workbook
(`BEZ235_QSP_PD_Biomarker_Cascade_Annotations.xlsx`), and the human-written
MOA cascade document (`BEZ235_QSP_PD_Biomarker_Cascade.md`) are all
preserved unchanged under `datasets/raw/workbooks/` and
`datasets/extracted/dactolisib_mm/`.

Registry-ready tables:

- `contexts.csv`
- `conditions.csv`
- `condition_steps.csv`
- `assays.csv`
- `observations.csv`
- `extraction_metadata.json`

Audit and annotation export:

- `not_quantifiable_figures.csv` — qualitative-only content from Fig2C-D and
  Fig3B-C (single representative western blots, no densitometry), Fig4
  (13-signature x 5-timepoint gene-expression bar chart, low-confidence
  visual estimate), and Fig6A-C (3D response-surface combination meshes),
  kept out of `observations.csv` entirely.

## What the source contains

BEZ235 was tested across a 21-line multiple myeloma cell panel (printed
IC50s, Fig1A), five primary CD138-selected patient samples (Fig1B), and a
therapeutic-index selectivity comparison against bone marrow stromal cells
(HS-5), immortalized hepatocytes (THLE-3), and healthy-donor PBMCs
(Fig1C-D). Two engineered MM.1S sublines -- constitutively-active
(myristoylated) Akt overexpression and Bcl-2 overexpression -- probe the
survival-signaling tier of the mechanism: Akt overexpression confers no
protection, while Bcl-2 overexpression produces a non-zero survival plateau
(Fig2A-B). Annexin V/PI flow cytometry gives a clean apoptosis time course
(Fig3A). A gene-signature time course (Fig4), apoptosis/mTOR-pathway western
blots (Fig2C-D, Fig3B-C), an MM.1S-GFP/luc xenograft efficacy study (tumor
size, Kaplan-Meier survival, body weight; Fig5A-C), and 3D combination
dose-response surfaces with bortezomib/doxorubicin/dexamethasone (Fig6A-C,
all additive, no antagonism per the text) round out the dataset.

## Normalization notes

- The companion MOA doc (`BEZ235_QSP_PD_Biomarker_Cascade.md`) organizes the
  paper into a five-tier PD cascade (target modulation -> survival-signaling
  balance -> transcriptional output -> cell-death execution -> tumor/
  efficacy endpoint) and supplies its own higher-precision digitized tables
  for Fig1C (selectivity), Fig2A (Akt-rescue), and Fig2B (Bcl-2-rescue); per
  the task brief those three tables are used as the numeric source for those
  panels instead of the raw workbook's own visual-estimate table, and the
  MOA doc's exact Fig2B numbers are preserved to keep the non-zero survival
  plateau shape faithful (highest-value mechanistic data for a dual-target
  threshold PD equation).
- The two engineered MM.1S sublines (myr-Akt, Bcl-2 overexpression) are
  modeled as distinct `contexts` from parental MM.1S, each carrying a
  `context_alterations` row (gene `AKT1` or `BCL2`, `alteration_type`
  `OVEREXPRESSION`, the controlled-vocabulary value) rather than as dosed `perturbations` --
  stable cell engineering is captured the same way birinapant captures
  genotype context (BRAF/NRAS mutation rows), just with an overexpression
  alteration type instead of a point mutation.
- Fig2A and Fig2B each contain their own separate MM.1S-parental digitized
  replicate; the two parental arms have slightly different values at
  matched doses (e.g. 50 nmol/L: 55% survival in the Fig2A replicate vs 42%
  in the Fig2B replicate) and are preserved as separate conditions rather
  than merged, since they come from different figure panels/replicates.
- Fig2C-D, Fig3B-C (western blots with no densitometry), Fig4 (dense,
  overlapping-error-bar gene-signature bar chart), and Fig6A-C (3D
  combination-surface meshes) are captured only in
  `not_quantifiable_figures.csv`, never forced into numeric
  `observations.csv` rows, per both the source workbook's own quality
  annotations and the MOA doc's explicit "what's still not digitized"
  section.
- Fig1A's printed MM.1S IC50 (22.78 nmol/L, workbook) differs slightly from
  the MOA doc's version (22.16 nmol/L); the workbook's explicit
  printed-on-figure value is used as authoritative. See
  `extraction_metadata.json` `corrections` for this and other
  cross-check discrepancies (Fig5A/Fig5B digitization variance between the
  workbook and the MOA doc).

Regenerate and validate with:

```powershell
py -3 datasets/tools/prepare_dactolisib_mm.py
py -3 datasets/tools/build_registry.py
py -3 datasets/tools/validate_registry.py
```

Tests: `py -3 -m pytest datasets/tools/tests/test_dactolisib_mm_importer.py -q`

## What's still needed for full QSP calibration

**No BEZ235 pharmacokinetic data exists in this paper at all.** Neither the
100 nmol/L in vitro kinetic dose (Fig2C-D, Fig3B-C) nor the 30 mg/kg oral in
vivo dose (Fig5) is linked to a plasma-exposure model by any data in this
source; an exposure-response bridge requires PK parameters from elsewhere in
the pipeline or the literature. The Fig4 gene-signature bars are a
low-confidence visual estimate (12+ overlapping signatures with large,
overlapping error bars; only 24h direction/relative rank could be read
reliably) and are not represented numerically anywhere in this package --
before attempting further digitization, check whether the underlying
HT-U133A/U133B microarray data were deposited to a public repository (no GEO
accession is stated in the visible text or reference list). Several figures
(Fig2C-D, Fig3B-C western blots; Fig6A-C 3D meshes) are qualitative-only by
design and Supplementary Figs S1-S7 (cited repeatedly for quantitative
support) are not available locally at all.

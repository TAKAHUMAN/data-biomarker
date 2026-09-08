# Dactolisib (BEZ235) ABCB1-overexpressing ovarian/pancreatic cancer extraction package

This package normalizes Durrant DE, et al. "A Dual PI3 Kinase/mTOR Inhibitor
BEZ235 reverses doxorubicin resistance in ABCB1 overexpressing ovarian and
pancreatic cancer cell lines." *Biochimica et Biophysica Acta - General
Subjects*, 2020 (DOI 10.1016/j.bbagen.2020.129556; PMID 32061787, PMCID
PMC10845210) into the same registry structure as the other drug datasets.
PMC HTML is not present locally for this study; this is a workbook-only
build, mirroring `importers/dactolisib_mm.py` and `importers/pemigatinib.py`
(no PAPER-type `source_artifacts` row).

The supplied curated workbook (`dactolisib_ABCB1ovarian_extracted.xlsx`) and
its companion QSP-recommendation workbook
(`bez235_dox_qsp_pd_digitization.xlsx`) are preserved unchanged under
`datasets/raw/workbooks/`.

Registry-ready tables:

- `contexts.csv`
- `conditions.csv`
- `condition_steps.csv`
- `assays.csv`
- `observations.csv`
- `extraction_metadata.json`

Audit and annotation export:

- `not_quantifiable_figures.csv` — qualitative-only content from Fig1D-F
  (ABCB1 western blot and confocal microscopy, no densitometry/intensity
  scale), Fig2 (DOX accumulation flow-cytometry overlay histograms, no
  printed MFI/gate values), and Fig3 (DOX efflux flow-cytometry overlay
  histograms), kept out of `observations.csv` entirely.

## What the source contains

Two parental-vs-resistant cell-line pairs anchor the study: MiaPaCa2
(pancreatic, parental) vs Mia-B1 (engineered ABCB1-overexpressing resistant
subline), and A2780 (ovarian, parental) vs A2780-dx (doxorubicin-selected,
ABCB1-overexpressing resistant subline). A third pancreatic subline, Mia-dx
(doxorubicin-resistant but ABCB1-undetectable), serves as an
ABCB1-independent specificity control throughout. The paper shows BEZ235
reverses doxorubicin resistance in the ABCB1-overexpressing lines (Fig1A-C
dose-response), that BEZ235 is a poor/non-substrate, non-ATP-site inhibitor
of ABCB1 by a cell-free ATPase assay (Fig4A-B), that it suppresses p-S6
(mTORC1 target engagement, Fig4C), that BEZ235 + doxorubicin combination
re-sensitizes the resistant lines in a viability assay (Fig5A-D, the
paper's primary combination-PD dataset), and that BEZ235 co-treatment
restores DOX-induced cleaved-PARP apoptotic signaling in the resistant lines
(Fig6A-B). ABCB1 protein levels (Fig1D-F) and DOX accumulation/efflux flow
cytometry (Fig2-3) are shown but not quantified numerically in the source.

## Normalization notes

- Parental-vs-ABCB1-overexpressing (doxorubicin-resistant) pairs are
  modeled as distinct `contexts` per cell line (5 cell-line contexts total,
  plus one cell-free "isolated ABCB1 membrane preparation" context for the
  Fig4A-B ATPase assay, which has no cell line at all).
- Conditions distinguish BEZ235 alone, doxorubicin alone, and BEZ235 +
  doxorubicin combination as separate `condition_steps` sequences, matching
  Fig5's four-panel structure (one condition per cell line x
  BEZ-dose x DOX-present/absent combination).
- Per the companion QSP workbook's `Read me` sheet (authoritative for
  classifying each figure's data quality): Fig1D-F, Fig2, and Fig3 are
  qualitative-only (no MFI/densitometry/scale-bar values printed) and are
  captured only in `not_quantifiable_figures.csv`. Fig4C (p-S6/S6 blot) and
  Fig6 (cleaved PARP blot) ARE image-derived relative/ordinal numeric
  estimates and are promoted to `observations.csv` with wide observation
  uncertainty flags (`quality_class` `SEMI_QUANTITATIVE`, an explicit
  `uncertainty_type` note, and a conservative `uncertainty_value` of 0.3
  relative-units) rather than treated as precise densitometry ratios.
- Fig4C's numeric values come from the companion QSP workbook (the raw
  curated workbook records this panel as a qualitative band-intensity call
  only); Fig6's numeric values come from the raw curated workbook's own
  0-4 arbitrary relative-intensity scale, which is NOT on the same numeric
  scale as the companion QSP workbook's separately-digitized Fig6 sheet
  (0-1.15 range) -- the two were not reconciled; see
  `extraction_metadata.json` `corrections`/`caveats`.

Regenerate and validate with:

```powershell
py -3 datasets/tools/prepare_dactolisib_ovarian.py
py -3 datasets/tools/build_registry.py
py -3 datasets/tools/validate_registry.py
```

Tests: `py -3 -m pytest datasets/tools/tests/test_dactolisib_ovarian_importer.py -q`

## What's still needed for full QSP calibration

**There is no animal/tumour model in this paper.** All data in this package
are in vitro (2D cell culture) or cell-free (isolated ABCB1 membrane ATPase
assay); nothing here should be read as implying in vivo/tumour efficacy
data exists for this study. Per the companion QSP workbook, the recommended
model is a joint in-vitro transporter/pathway/combination PD model (ABCB1
efflux -> intracellular DOX -> cleaved PARP -> viability, with p-S6 as a
parallel PI3K/mTOR target-engagement readout), with Figure 5 viability and
Figure 1 DOX-resistance curves as the primary fitting data. Fig2/Fig3
fluorescence histograms should be used only qualitatively unless raw
FCS/MFI data are obtained from the authors, and both Fig4C and Fig6 should
be treated as ordinal/semi-quantitative with wide observation error rather
than precise densitometry.

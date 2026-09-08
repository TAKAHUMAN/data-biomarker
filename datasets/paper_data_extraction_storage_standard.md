# Paper Data Extraction Storage Standard

## Purpose

This document defines how quantitative data extracted from papers should be stored in the `cell_signal_transduction_prototyping` dataset system so that all papers use the same structure, provenance rules, identifiers, and semantics.

The goal is to make extracted literature data:

- reproducible;
- queryable across papers;
- traceable back to the exact source location;
- distinguishable as direct, digitized, derived, or model-generated;
- compatible with later model calibration and validation;
- independent of any one experiment or drug-fit implementation.

The dataset layer is the authoritative record of literature data. Experiment folders should reference dataset records rather than maintain independent copies of the same observations.

---

## 1. Core principles

### 1.1 Preserve raw sources

Original papers, supplements, spreadsheets, images, and downloaded source files are immutable.

Never overwrite, crop, rescale, rename internally, or otherwise modify the only copy of a source artifact.

### 1.2 Separate source data from standardized data

Keep three distinct layers:

1. **Raw source** — original downloaded file.
2. **Extracted representation** — paper-specific transcription/digitization with source coordinates and extraction metadata.
3. **Registry representation** — normalized cross-paper records used for queries, fitting, and validation.

### 1.3 Do not erase provenance during normalization

Every quantitative value must remain traceable to:

- paper;
- source artifact;
- figure/table/supplement location;
- experimental context;
- condition;
- extraction method;
- original reported units;
- any transformation performed.

### 1.4 Do not mix experimental observations with simulations

Paper-generated model curves, fitted curves, predicted values, interpolations, and simulations must not be labeled as experimental measurements.

### 1.5 Do not invent missing information

Do not infer error bars, replicate counts, assay units, dose units, time points, cell-line alterations, or other metadata unless the paper supports the inference.

Use explicit missing values and notes when information is unavailable.

### 1.6 Preserve reported values before converting them

Always retain the value and unit as reported by the paper. Unit-normalized values may be stored separately.

### 1.7 Stable IDs are permanent

Once a paper, condition, observation, or measurement ID has been assigned and entered into the registry, do not silently reuse that ID for a different record.

---

## 2. Recommended directory structure

```text
datasets/
├── README.md
├── schema/
│   ├── paper.schema.json
│   ├── source_artifact.schema.json
│   ├── context.schema.json
│   ├── alteration.schema.json
│   ├── condition.schema.json
│   ├── condition_step.schema.json
│   ├── observation.schema.json
│   ├── measurement.schema.json
│   ├── extraction_run.schema.json
│   ├── model_mapping.schema.json
│   └── observation_usage.schema.json
│
├── raw/
│   └── <paper_id>/
│       ├── article.pdf
│       ├── supplement_01.pdf
│       ├── supplementary_data.xlsx
│       └── ...
│
├── extracted/
│   └── <paper_id>/
│       ├── extraction_manifest.json
│       ├── observations.csv
│       ├── measurements.csv
│       ├── conditions.csv
│       ├── condition_steps.csv
│       ├── contexts.csv
│       ├── alterations.csv
│       └── digitization/
│           ├── figure_2b.csv
│           ├── figure_2b_metadata.json
│           └── ...
│
├── registry/
│   ├── papers.parquet
│   ├── source_artifacts.parquet
│   ├── contexts.parquet
│   ├── alterations.parquet
│   ├── conditions.parquet
│   ├── condition_steps.parquet
│   ├── observations.parquet
│   ├── measurements.parquet
│   ├── extraction_runs.parquet
│   ├── model_mappings.parquet
│   └── observation_usage.parquet
│
├── tools/
│   └── ...
│
└── exports/
    └── ...
```

The `registry/*.parquet` files are the authoritative standardized dataset layer.

Files under `extracted/<paper_id>/` are paper-specific extraction records and should remain readable enough to audit manually.

---

## 3. Paper identifiers

Use a stable machine-readable `paper_id`.

Preferred order:

1. `pmid_<PMID>`
2. `doi_<normalized_doi>` if no PMID exists
3. `firstauthor_year_shorttitle` if neither exists

Examples:

```text
pmid_33818908
pmid_29018036
doi_10_1002_psp4_12602
```

Do not use filenames as paper IDs.

---

# 4. Standard registry tables

## 4.1 `papers`

One row per paper.

Required fields:

| Field | Meaning |
|---|---|
| `paper_id` | Stable dataset paper identifier |
| `title` | Full article title |
| `first_author` | First author surname |
| `publication_year` | Publication year |
| `journal` | Journal name |
| `doi` | DOI if available |
| `pmid` | PubMed ID if available |
| `pmcid` | PMC ID if available |
| `citation` | Human-readable citation |
| `notes` | Paper-level extraction notes |

Optional fields may include URL, publication date, corresponding author, or project-specific tags.

---

## 4.2 `source_artifacts`

One row for every source file used during extraction.

Required fields:

| Field | Meaning |
|---|---|
| `source_artifact_id` | Stable artifact ID |
| `paper_id` | Parent paper |
| `artifact_type` | `article`, `supplement`, `spreadsheet`, `author_data`, `image`, etc. |
| `relative_path` | Path under `datasets/raw/<paper_id>/` |
| `original_filename` | Original downloaded filename |
| `description` | Human-readable description |
| `immutable` | Normally `true` |

Recommended fields:

- `sha256`
- `download_date`
- `source_url`
- `supplement_number`

---

## 4.3 `contexts`

A context describes the biological system in which measurements were made.

One row per distinct biological context.

Required fields:

| Field | Meaning |
|---|---|
| `context_id` | Stable context ID |
| `paper_id` | Parent paper |
| `species` | Species |
| `system_type` | `cell_line`, `xenograft`, `patient`, `primary_cell`, `in_vitro`, etc. |
| `system_name` | Cell line, xenograft, patient cohort, tissue, etc. |
| `tissue` | Tissue of origin if known |
| `disease` | Disease context if known |
| `notes` | Additional biological context |

Examples of distinct contexts:

```text
KP-4 xenograft
Hs746T xenograft
MV4-11 cells
MOLM-13 cells
human FIH tumor biopsy cohort
```

Do not encode treatment dose or time in `context_id`; those belong in conditions.

---

## 4.4 `alterations`

One row per relevant molecular alteration associated with a context.

Required fields:

| Field | Meaning |
|---|---|
| `alteration_id` | Stable alteration ID |
| `context_id` | Biological context |
| `gene_or_target` | Gene/protein |
| `alteration_type` | `mutation`, `fusion`, `amplification`, `deletion`, `overexpression`, `deficiency`, etc. |
| `alteration` | Specific alteration |
| `status` | `present`, `absent`, `unknown`, or quantitative if explicitly supported |
| `source_location` | Where the paper establishes the alteration |
| `notes` | Clarification |

Examples:

```text
MET | amplification | high-level amplification
MET | mutation | exon 14 skipping
FLT3 | mutation | ITD
FGFR1 | fusion | FGFR1OP2-FGFR1
BRCA1 | deficiency | HR-deficient
```

Only include alterations actually supported by the paper or another explicitly cited source.

---

## 4.5 `conditions`

A condition represents one experimentally distinct state under which one or more observations were collected.

Examples:

- vehicle at 2 h;
- 3 nM drug at 2 h;
- 50 mg/kg once daily on day 10;
- baseline biopsy;
- post-treatment biopsy.

Required fields:

| Field | Meaning |
|---|---|
| `condition_id` | Stable condition ID |
| `paper_id` | Parent paper |
| `context_id` | Biological context |
| `condition_label` | Human-readable description |
| `time_value` | Observation time if a single time is meaningful |
| `time_unit` | `s`, `min`, `h`, `day`, etc. |
| `notes` | Condition-specific notes |

Do not force complex regimens into a single text string. Use `condition_steps`.

---

## 4.6 `condition_steps`

Use this table to encode treatments, perturbations, doses, media changes, ligand additions, washouts, radiation, or other interventions associated with a condition.

One row per intervention step.

Required fields:

| Field | Meaning |
|---|---|
| `condition_step_id` | Stable step ID |
| `condition_id` | Parent condition |
| `step_order` | Ordered integer |
| `intervention_type` | `drug`, `ligand`, `genetic`, `radiation`, `media`, etc. |
| `agent` | Drug/ligand/perturbation name |
| `amount_value` | Dose/concentration if reported |
| `amount_unit` | Original unit |
| `start_time_value` | Start time relative to experiment |
| `start_time_unit` | Time unit |
| `duration_value` | Duration if known |
| `duration_unit` | Duration unit |
| `route` | Oral, IV, in vitro exposure, etc., when applicable |
| `frequency` | QD, BID, single dose, etc., when applicable |
| `notes` | Additional regimen details |

This table allows multi-step protocols to be represented without creating custom schemas for each paper.

---

# 5. Quantitative data

## 5.1 `observations`

An observation is the standardized quantitative datum used for analysis.

Typical observations include:

- plotted mean at one dose/time;
- table value;
- normalized Western blot intensity;
- tumor volume mean;
- phosphoprotein concentration;
- response fraction;
- PK exposure metric;
- IC50 explicitly reported by the authors.

One row per condition/readout/statistical value.

### Required fields

| Field | Meaning |
|---|---|
| `observation_id` | Stable observation ID |
| `paper_id` | Parent paper |
| `source_artifact_id` | Source file |
| `context_id` | Biological context |
| `condition_id` | Experimental condition |
| `readout` | What was measured |
| `value` | Extracted numeric value |
| `unit` | Unit exactly as interpreted for the stored value |
| `statistic` | `mean`, `median`, `individual`, `fold_change`, `IC50`, etc. |
| `source_location` | Figure/table/supplement location |
| `data_origin` | Controlled category described below |
| `extraction_method` | `transcribed`, `digitized`, `author_data`, etc. |
| `extraction_run_id` | Extraction operation that generated the record |

### Strongly recommended fields

| Field | Meaning |
|---|---|
| `error_value` | Error magnitude if explicitly available |
| `error_type` | `SD`, `SEM`, `CI95`, range, etc. |
| `n` | Replicate/sample count if explicitly reported |
| `normalization` | e.g. vehicle=1, baseline=100%, loading-control normalized |
| `assay` | Western blot, Luminex, ELISA, tumor caliper, etc. |
| `analyte` | Molecular species measured |
| `compartment` | plasma, tumor, whole-cell lysate, nuclear, etc. |
| `qualifier` | `<`, `>`, `~`, censored, below detection, etc. |
| `value_original` | Original reported/digitized value before conversion |
| `unit_original` | Original unit |
| `value_normalized` | Optional normalized value used by the registry |
| `unit_normalized` | Unit for normalized value |
| `notes` | Observation-specific details |

---

## 5.2 Controlled `data_origin`

Every observation must have one of the following origins:

### `DIRECT_REPORTED`

Number explicitly printed in the paper, supplement, or author data.

Examples:

- table entry;
- reported IC50;
- value in supplementary spreadsheet.

### `DIGITIZED_EXPERIMENTAL`

Experimental point reconstructed from a plot.

The original figure location and digitization metadata are required.

### `DERIVED_FROM_REPORTED`

Calculated from experimental quantities reported by the authors.

The derivation must be recorded.

Examples:

- percent inhibition calculated from reported treated/control values;
- fold change calculated from two table entries.

### `PAPER_MODEL_PREDICTION`

Value generated by a model, fit, interpolation, or simulation in the paper.

This category must never be treated as experimental data by default.

### `QUALITATIVE_ONLY`

Paper supports directionality or categorical behavior but not a defensible numeric value.

Do not fabricate a numeric value for these records.

---

## 5.3 `measurements`

Use `measurements` only when individual replicate-level values are available.

Do not manufacture replicate records from means and error bars.

Required fields:

| Field | Meaning |
|---|---|
| `measurement_id` | Stable measurement ID |
| `observation_id` | Summary observation that the replicate belongs to |
| `replicate_index` | Replicate/sample identifier |
| `value` | Individual value |
| `unit` | Unit |
| `subject_id` | Optional animal/patient/sample identifier |
| `notes` | Replicate-specific notes |

If the paper reports only mean ± SEM, store one observation and leave `measurements` empty.

---

# 6. Source-location standard

Every quantitative datum must have a precise `source_location`.

Preferred formats:

```text
Figure 2B
Figure 2B, pERK panel
Figure 4A, 300 mg QD point
Table 1, Hs746T row
Supplementary Table S3, row 12
Supplementary Data 1, sheet PK, row 44
Main text, Results, paragraph 3
```

For digitized figures also record:

- panel;
- series/legend label;
- axis identity;
- axis scale (`linear`, `log10`, etc.);
- digitization software or method;
- digitization file path.

---

# 7. Digitized figure data

Each digitized panel should have both a data file and metadata file.

Example:

```text
extracted/<paper_id>/digitization/
├── figure_2b.csv
└── figure_2b_metadata.json
```

Recommended metadata:

```json
{
  "paper_id": "pmid_33818908",
  "source_artifact_id": "...",
  "source_location": "Figure 2B",
  "panel": "B",
  "x_axis": "time",
  "x_unit": "day",
  "y_axis": "tumor_volume",
  "y_unit": "mm3",
  "x_scale": "linear",
  "y_scale": "linear",
  "digitization_method": "WebPlotDigitizer",
  "digitized_by": "...",
  "digitization_date": "YYYY-MM-DD",
  "notes": "..."
}
```

Do not round digitized data more aggressively than necessary. Preserve the extraction precision, while recognizing that digitized values are estimates.

---

# 8. Extraction runs

Every extraction/import pass should receive an `extraction_run_id`.

This prevents later edits from becoming indistinguishable from the original extraction.

Recommended fields:

| Field | Meaning |
|---|---|
| `extraction_run_id` | Stable run ID |
| `paper_id` | Paper |
| `timestamp` | Run time |
| `extractor` | Human, script, Codex, etc. |
| `method` | transcription, digitization, scripted import, etc. |
| `source_artifacts` | Artifacts examined |
| `output_files` | Files generated |
| `notes` | Important decisions/limitations |

If values are corrected later, create a new extraction run or maintain a documented revision history rather than silently changing provenance.

---

# 9. Model mappings

Literature readouts and model states are separate concepts.

Do not encode model-state assumptions directly into `observations`.

Use `model_mappings` for mappings such as:

```text
paper readout: pERK / total ERK
model readout: ERK_double_phosphorylated
```

Recommended fields:

| Field | Meaning |
|---|---|
| `mapping_id` | Stable mapping ID |
| `observation_id` or `readout` | Literature quantity |
| `model_id` | Model version |
| `model_symbol` | State/observable used |
| `mapping_transform` | Identity, normalization, baseline subtraction, etc. |
| `mapping_status` | direct, approximate, constructed, unresolved |
| `notes` | Interpretation |

This allows the same paper data to be reused with future model versions.

---

# 10. Fit and validation usage

Whether an observation is used for fitting is not an intrinsic property of the literature datum.

Store usage separately in `observation_usage`.

Recommended fields:

| Field | Meaning |
|---|---|
| `observation_id` | Registry observation |
| `experiment_id` | Modeling experiment |
| `usage_role` | Controlled role |
| `fit_stage` | Optional stage identifier |
| `parameter_set_id` | Parameter set if relevant |
| `used_in_objective` | Boolean |
| `used_for_validation` | Boolean |
| `held_out` | Boolean |
| `exclusion_reason` | Reason if excluded |
| `notes` | Additional explanation |

Controlled `usage_role` values:

```text
FIT
HELD_OUT_DIAGNOSTIC
HELD_OUT_QUANTITATIVE_VALIDATION
QUALITATIVE_VALIDATION
EXCLUDED
UNUSED
```

Do not alter the underlying observation when its fitting role changes.

---

# 11. Units and normalization

## Always store original units

Examples:

```text
nM
ng/mL
mg/kg
ng*h/mL
mm3
% control
fold over vehicle
arbitrary Western-blot intensity
```

If unit conversion is useful, preserve both:

```text
value_original
unit_original
value_normalized
unit_normalized
```

Record the transformation explicitly.

### Western blots and other relative assays

Do not imply absolute concentration when the paper reports relative intensity.

Examples:

```text
unit = relative_intensity
normalization = vehicle_at_2h_equals_1
```

or

```text
unit = percent_of_control
normalization = vehicle_equals_100_percent
```

---

# 12. Missing, zero, and censored values

These must remain distinguishable.

### True reported zero

```text
value = 0
qualifier = exact_or_reported_zero
```

### Below detection

```text
value = null
qualifier = below_detection_limit
```

or retain the reported bound if given.

### Not measured

```text
value = null
qualifier = not_measured
```

### Not extractable

```text
value = null
qualifier = not_quantitatively_extractable
```

Do not replace censored or missing observations with arbitrary small positive numbers in the registry. Any fitting-specific numerical floor belongs in the experiment/modeling layer.

---

# 13. Derived quantities

Derived observations are allowed but must never masquerade as direct measurements.

Required metadata:

```text
data_origin = DERIVED_FROM_REPORTED
derivation = <formula or procedure>
parent_observation_ids = [...]
```

Example:

```text
pMET inhibition = 1 - treated_pMET / vehicle_pMET
```

Keep the parent observations whenever possible.

---

# 14. Paper-generated model results

If a paper contains both measurements and model predictions, store them separately.

For example:

```text
Figure 3A experimental symbols -> DIGITIZED_EXPERIMENTAL
Figure 3A fitted/simulated curve -> PAPER_MODEL_PREDICTION
```

A model-predicted curve must not be used as though it were an independent experimental observation unless an experiment explicitly chooses to use that model-derived quantity and records that decision.

---

# 15. Recommended IDs

IDs should be stable, readable, and globally unique within the dataset registry.

Examples:

```text
paper_id:
pmid_33818908

context_id:
pmid_33818908__kp4_xenograft

condition_id:
pmid_33818908__kp4__tepotinib_50mgkg_qd__day10

observation_id:
pmid_33818908__fig2a__kp4__50mgkg__day10__tumor_volume

measurement_id:
pmid_33818908__fig2a__kp4__50mgkg__day10__tumor_volume__rep01
```

IDs should encode identity, not every piece of metadata. Do not make IDs so elaborate that changing a unit or note requires changing the ID.

---

# 16. Minimum extraction checklist for every paper

Before marking a paper extraction complete, confirm that:

- the original article/supplement files are preserved under `raw/`;
- the paper has a stable `paper_id`;
- all source artifacts used are registered;
- biological contexts are explicitly defined;
- relevant molecular alterations are captured;
- treatment conditions are represented consistently;
- multi-step treatment regimens use `condition_steps`;
- every numeric observation has a source location;
- every observation is labeled direct, digitized, derived, or model-generated;
- original units and normalization are preserved;
- reported error bars and `n` values are stored when available;
- individual measurements are stored only when actual replicate data exist;
- digitized values retain digitization metadata;
- no paper-generated simulation is mislabeled as experimental data;
- no missing values or error estimates have been invented;
- extraction decisions are tied to an `extraction_run_id`;
- model-state mappings are stored separately from observations;
- fitting/validation usage is stored separately from observations.

---

# 17. Example observation records

## Direct table value

```text
observation_id: pmid_xxx__table1__kp4__tumor_static_concentration
paper_id: pmid_xxx
context_id: pmid_xxx__kp4_xenograft
condition_id: pmid_xxx__kp4__tumor_static
readout: tumor_static_concentration
value: 80
unit: ng/mL
statistic: model_derived_summary
source_location: Table 1, KP-4 row
data_origin: PAPER_MODEL_PREDICTION
extraction_method: transcribed
```

The value may be numerically explicit in a table but still be model-derived. `data_origin` describes what the number represents, not merely how it was extracted.

## Digitized experimental point

```text
observation_id: pmid_xxx__fig2b__hs746t__6mgkg__day10__tumor_volume
paper_id: pmid_xxx
context_id: pmid_xxx__hs746t_xenograft
condition_id: pmid_xxx__hs746t__6mgkg_qd__day10
readout: tumor_volume
value: 142.6
unit: mm3
statistic: mean
source_location: Figure 2B, 6 mg/kg series, day 10
data_origin: DIGITIZED_EXPERIMENTAL
extraction_method: digitized
```

## Western blot

```text
observation_id: pmid_xxx__fig4__mv411__3nm__2h__pstat5
context_id: pmid_xxx__mv411
condition_id: pmid_xxx__mv411__drug_3nm__2h
readout: pSTAT5
value: 0.42
unit: relative_intensity
statistic: normalized_signal
normalization: vehicle_2h_equals_1
source_location: Figure 4, MV4-11 pSTAT5 panel
data_origin: DIGITIZED_EXPERIMENTAL
extraction_method: digitized
```

---

# 18. What should NOT be stored in the paper dataset layer

Do not store these as literature observations:

- fitted model parameters generated by our model;
- drug IC50 values inferred solely by our fit;
- target-interface gains from the signaling model;
- experiment-specific normalization constants;
- arbitrary numerical floors for log fitting;
- model predictions generated by our code;
- hypothetical missing data;
- guessed error bars;
- inferred replicates;
- states created solely for the working signaling model.

These belong in experiment/model result directories with links back to the dataset observations used.

---

# 19. Summary rule

For every number extracted from a paper, it should always be possible to answer:

1. **Which paper did it come from?**
2. **Where exactly in that paper did it come from?**
3. **What biological system was measured?**
4. **What treatment/condition produced it?**
5. **What quantity was measured?**
6. **What value and units were reported?**
7. **Was it directly reported, digitized, derived, or model-generated?**
8. **How was it extracted or transformed?**
9. **What model state, if any, is it later mapped to?**
10. **Was it used for fitting, held out, or excluded?**

If these ten questions can be answered without returning to the original extraction session, the paper has been stored correctly.

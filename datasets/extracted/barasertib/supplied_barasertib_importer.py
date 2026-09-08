"""
Barasertib (AZD1152), Aurora Kinase B Inhibitor in SCLC
Helfrich et al. 2016 — Molecular Cancer Therapeutics

Registry importer for preclinical biomarker and pharmacodynamic data.
"""

from registry_common import stable_id, Registry, Paper, Context, Assay, Condition, ConditionStep, Observation


def collect(registry: Registry) -> Registry:
    """
    Add Helfrich et al. 2016 Barasertib (AURKB-selective) SCLC data to registry.

    Dimensions:
    - 23 SCLC cell lines (characterized by Rb/p53 loss and MYC family amplification)
    - 1 drug (Barasertib-HQPA, AURKB-selective)
    - 6 assay modalities:
      * Cell viability (MTS, IC50 values)
      * Polyploidy (FACS, % 4N and ≥8N DNA content)
      * cMYC gene expression (CCLE database)
      * Phosphorylated histone H3 Ser10 (FACS, marker of AURKB activity)
      * MYC amplification status (Genomic)
      * In vivo efficacy (H841 xenograft tumor volume)

    Total: 46 observations across viability, polyploidy, gene expression, and in vivo data
    Key finding: cMYC amplification (P=0.018, 16× odds ratio) and expression (P=0.026, 11× odds ratio)
                 strongly predict barasertib sensitivity
    """

    # ============================================================================
    # PAPER METADATA
    # ============================================================================
    paper = Paper(
        paper_id=stable_id("paper_PMID27496133", "Helfrich_2016_Barasertib_SCLC"),
        title="Barasertib (AZD1152), a small molecule Aurora B inhibitor, inhibits the growth of SCLC cell lines in vitro and in vivo",
        authors="Helfrich BA, et al.",
        journal="Molecular Cancer Therapeutics",
        year=2016,
        volume=15,
        issue=10,
        pages="2314-2322",
        doi="10.1158/1535-7163.MCT-16-0298",
        pmid=27496133,
    )
    registry.add_paper(paper)

    # ============================================================================
    # CONTEXTS (Cell culture conditions & xenograft model)
    # ============================================================================
    context_sclc_vitro = Context(
        context_id=stable_id("context_SCLC_vitro", "sclc_undifferentiated_culture"),
        paper_id=paper.paper_id,
        cell_line="Multiple SCLC lines (23 total)",
        tissue="Small cell lung cancer",
        species="Homo sapiens",
        differentiation_status="Undifferentiated neuroendocrine",
        rb_status="Loss (universal in SCLC)",
        p53_status="Loss (universal in SCLC)",
        culture_medium="RPMI-1640 with 10% FBS",
        assay_type="in_vitro_cell_culture",
        notes="Universal Rb and p53 inactivation in SCLC; MYC family member amplification in ~30%; stratified into cMYC-amplified (56% sensitive), MYCL1-amplified (33% sensitive), MYCN-amplified (0% sensitive), and non-amplified (50% sensitive) subgroups",
    )
    registry.add_context(context_sclc_vitro)

    context_h841_xenograft = Context(
        context_id=stable_id("context_H841_xenograft", "sclc_h841_mouse_xenograft"),
        paper_id=paper.paper_id,
        cell_line="H841",
        tissue="Small cell lung cancer",
        species="Mus musculus (host)",
        tumor_origin_species="Homo sapiens",
        differentiation_status="Undifferentiated",
        rb_status="Loss",
        p53_status="Loss",
        tumor_stage="Limited stage (L)",
        assay_type="in_vivo_xenograft",
        host="Nude mice (immunodeficient)",
        implantation="Subcutaneous",
        notes="H841 line (no cMYC amplification, high expression CCLE 10.6, MYC signature positive); predictive of barasertib sensitivity despite lack of amplification; demonstrates in vivo efficacy",
    )
    registry.add_context(context_h841_xenograft)

    # ============================================================================
    # ASSAYS
    # ============================================================================
    assay_mts_viability = Assay(
        assay_id=stable_id("assay_MTS_viability", "cell_viability_mts"),
        paper_id=paper.paper_id,
        assay_name="Cell Viability (MTS)",
        measurement_type="Viability",
        unit="nM",
        method="MTS proliferation assay (3-(4,5-dimethylthiazol-2-yl)-5-(3-carboxymethoxyphenyl)-2-(4-sulfophenyl)-2H-tetrazolium)",
        readout="IC50 (concentration causing 50% reduction in viable cell count)",
        incubation_time=72,
    )
    registry.add_assay(assay_mts_viability)

    assay_facs_polyploidy = Assay(
        assay_id=stable_id("assay_FACS_polyploidy", "cell_cycle_polyploidy_facs"),
        paper_id=paper.paper_id,
        assay_name="Polyploidy (FACS)",
        measurement_type="Cell cycle",
        unit="%",
        method="Propidium iodide staining + flow cytometry (FACS)",
        readout="Percentage of cells with 4N or ≥8N DNA content",
        incubation_time=48,
    )
    registry.add_assay(assay_facs_polyploidy)

    assay_ccle_gene_expression = Assay(
        assay_id=stable_id("assay_CCLE_gene_expression", "gene_expression_cmyc_ccle"),
        paper_id=paper.paper_id,
        assay_name="cMYC Gene Expression (CCLE)",
        measurement_type="Gene expression",
        unit="Expression score",
        method="Cancer Cell Line Encyclopedia (CCLE) RNA-seq expression data",
        readout="cMYC mRNA expression (log2 scale normalized)",
    )
    registry.add_assay(assay_ccle_gene_expression)

    assay_facs_phospho_h3 = Assay(
        assay_id=stable_id("assay_FACS_phospho_H3", "protein_phosphorylation_h3"),
        paper_id=paper.paper_id,
        assay_name="Phosphorylated Histone H3 (FACS)",
        measurement_type="Protein phosphorylation",
        unit="%",
        method="Flow cytometry with phospho-histone H3 (Ser10) antibody; co-incubation with paclitaxel (100 nM, 24h) to arrest in G2/M",
        readout="Percentage of phospho-H3 (Ser10) positive cells",
        incubation_time=24,
    )
    registry.add_assay(assay_facs_phospho_h3)

    assay_myc_amplification = Assay(
        assay_id=stable_id("assay_mycn_amplification_status", "genomic_myc_amplification"),
        paper_id=paper.paper_id,
        assay_name="cMYC/MYCL1/MYCN Amplification Status",
        measurement_type="Genomic",
        unit="Amplified / Not amplified",
        method="FISH or NGS (based on literature or cell line databases)",
        readout="Binary: cMYC amplified (yes/no), MYCL1 amplified (yes/no), MYCN amplified (yes/no)",
    )
    registry.add_assay(assay_myc_amplification)

    assay_xenograft = Assay(
        assay_id=stable_id("assay_xenograft_tumor_volume", "in_vivo_efficacy_xenograft"),
        paper_id=paper.paper_id,
        assay_name="Xenograft Tumor Volume",
        measurement_type="In vivo efficacy",
        unit="mm³",
        method="Subcutaneous H841 xenograft; tumor volume measured by caliper (V = length × width² / 2)",
        readout="Tumor volume over time; dosing schedule Monday-Friday (5 days on, 2 days off)",
        incubation_time=61,
    )
    registry.add_assay(assay_xenograft)

    # ============================================================================
    # CONDITIONS (Drug treatments)
    # ============================================================================

    # VEHICLE CONTROL
    condition_dmso = Condition(
        condition_id=stable_id("condition_vehicle_control", "dmso_control_72h"),
        paper_id=paper.paper_id,
        context_id=context_sclc_vitro.context_id,
        condition_name="DMSO vehicle control",
        incubation_time=72,
        steps=None,  # Vehicle has no drug steps
    )
    registry.add_condition(condition_dmso)

    # BARASERTIB IN VITRO
    condition_barasertib_vitro = Condition(
        condition_id=stable_id("condition_barasertib_vitro", "sclc_barasertib_dose_response_72h"),
        paper_id=paper.paper_id,
        context_id=context_sclc_vitro.context_id,
        condition_name="Barasertib-HQPA (in vitro, dose-response)",
        incubation_time=72,
        steps=[
            ConditionStep(
                drug_name="Barasertib-HQPA",
                dose=None,
                dose_unit="nM",
                duration=72,
                route="in_vitro",
                notes="Active metabolite of barasertib (AZD1152); AURKB-selective Aurora kinase inhibitor (IC50 AURKB 0.37 nM, 100-fold selective over AURKA 1369 nM)",
            )
        ],
    )
    registry.add_condition(condition_barasertib_vitro)

    condition_barasertib_polyploidy = Condition(
        condition_id=stable_id("condition_barasertib_polyploidy", "sclc_barasertib_polyploidy_dose_response"),
        paper_id=paper.paper_id,
        context_id=context_sclc_vitro.context_id,
        condition_name="Barasertib-HQPA (polyploidy induction)",
        incubation_time=48,
        steps=[
            ConditionStep(
                drug_name="Barasertib-HQPA",
                dose=None,
                dose_unit="nM",
                duration=48,
                route="in_vitro",
                notes="Doses 30 nM or 50 nM; timepoints 24h and 48h; propidium iodide staining for FACS analysis",
            )
        ],
    )
    registry.add_condition(condition_barasertib_polyploidy)

    condition_barasertib_phospho_h3 = Condition(
        condition_id=stable_id("condition_barasertib_phospho_h3", "sclc_barasertib_paclitaxel_phospho_h3"),
        paper_id=paper.paper_id,
        context_id=context_sclc_vitro.context_id,
        condition_name="Barasertib-HQPA + paclitaxel (phospho-H3 assay)",
        incubation_time=24,
        steps=[
            ConditionStep(
                drug_name="Barasertib-HQPA",
                dose=None,
                dose_unit="nM",
                duration=24,
                route="in_vitro",
                notes="Co-incubated with paclitaxel (100 nM, 24h) to arrest cells in G2/M phase for AURKB activity assessment",
            ),
            ConditionStep(
                drug_name="Paclitaxel",
                dose=100,
                dose_unit="nM",
                duration=24,
                route="in_vitro",
                notes="Cell cycle arrest agent; blocks mitotic progression to allow G2/M-stage histone H3 phosphorylation",
            ),
        ],
    )
    registry.add_condition(condition_barasertib_phospho_h3)

    # BARASERTIB IN VIVO (H841 xenograft)
    condition_barasertib_xenograft_50mg = Condition(
        condition_id=stable_id("condition_barasertib_xenograft_50mg", "h841_barasertib_50mg_kg_intermittent"),
        paper_id=paper.paper_id,
        context_id=context_h841_xenograft.context_id,
        condition_name="Barasertib (50 mg/kg, intermittent dosing)",
        incubation_time=61,
        steps=[
            ConditionStep(
                drug_name="Barasertib",
                dose=50,
                dose_unit="mg/kg",
                duration=61,
                route="intravenous",
                notes="Intermittent pulsatile dosing: Monday-Friday (5 days on, 2 days off) for 2 weeks; doses provided trough barasertib-HQPA serum concentrations exceeding in vitro IC50 range",
            )
        ],
    )
    registry.add_condition(condition_barasertib_xenograft_50mg)

    condition_barasertib_xenograft_100mg = Condition(
        condition_id=stable_id("condition_barasertib_xenograft_100mg", "h841_barasertib_100mg_kg_intermittent"),
        paper_id=paper.paper_id,
        context_id=context_h841_xenograft.context_id,
        condition_name="Barasertib (100 mg/kg, intermittent dosing)",
        incubation_time=61,
        steps=[
            ConditionStep(
                drug_name="Barasertib",
                dose=100,
                dose_unit="mg/kg",
                duration=61,
                route="intravenous",
                notes="Intermittent pulsatile dosing: Monday-Friday (5 days on, 2 days off) for 2 weeks; higher dose for sustained regression",
            )
        ],
    )
    registry.add_condition(condition_barasertib_xenograft_100mg)

    # ============================================================================
    # OBSERVATIONS (46 total)
    # ============================================================================
    # Load observations from JSON data with stable_id() conversions applied
    import json
    import os

    json_path = os.path.join(os.path.dirname(__file__), "REGISTRY_IMPORT_DATA_BARASERTIB.json")

    try:
        with open(json_path, 'r') as f:
            data = json.load(f)

        # Map stubs to stable_ids for reference lookups
        context_stub_to_id = {
            "context_SCLC_vitro": context_sclc_vitro.context_id,
            "context_H841_xenograft": context_h841_xenograft.context_id,
        }

        assay_stub_to_id = {
            "assay_MTS_viability": assay_mts_viability.assay_id,
            "assay_FACS_polyploidy": assay_facs_polyploidy.assay_id,
            "assay_CCLE_gene_expression": assay_ccle_gene_expression.assay_id,
            "assay_FACS_phospho_H3": assay_facs_phospho_h3.assay_id,
            "assay_mycn_amplification_status": assay_myc_amplification.assay_id,
            "assay_xenograft_tumor_volume": assay_xenograft.assay_id,
        }

        # Process observations from JSON
        for obs_data in data["observations"]:
            # Generate semantic stable_id for observation
            obs_id_stub = obs_data.get("observation_id_stub", "")

            # Create descriptive slug based on cell line, measurement type, and dose (if applicable)
            cell_line = obs_data.get("cell_line", "").replace("-", "").replace(" ", "").lower()
            measurement = obs_data.get("measurement_name", "").replace(" ", "_").replace("%", "pct").replace("≥", "").lower()[:25]
            dose = obs_data.get("dose", "")
            phenotype = obs_data.get("phenotype", "").replace(" ", "_").lower().split("_")[0]  # Extract first word (sensitive/intermediate/resistant)

            if dose:
                obs_semantic_slug = f"{cell_line}_{measurement}_{dose}nm"
            elif phenotype:
                obs_semantic_slug = f"{cell_line}_{measurement}_{phenotype}"
            else:
                obs_semantic_slug = f"{cell_line}_{measurement}"

            # Create Observation with stable_id
            observation = Observation(
                observation_id=stable_id(obs_id_stub, obs_semantic_slug),
                paper_id=paper.paper_id,
                context_id=context_stub_to_id.get(obs_data.get("context_id_stub", "")),
                assay_id=assay_stub_to_id.get(obs_data.get("assay_id_stub", "")),
                figure_panel=obs_data.get("figure_panel", ""),
                measurement_name=obs_data.get("measurement_name", ""),
                dose=obs_data.get("dose"),
                dose_unit=obs_data.get("dose_unit", ""),
                value=obs_data.get("value"),
                value_unit=obs_data.get("value_unit", ""),
                value_qualitative=obs_data.get("value_qualitative"),
                extraction_method=obs_data.get("extraction_method", ""),
                quality_class=obs_data.get("quality_class", ""),
                uncertainty=obs_data.get("uncertainty"),
                uncertainty_type=obs_data.get("uncertainty_type"),
                pvalue=obs_data.get("pvalue"),
                notes=obs_data.get("notes", ""),
            )
            registry.add_observation(observation)

    except FileNotFoundError:
        # If JSON file not found, continue without observation data
        # (observations can be populated separately)
        pass
    except Exception as e:
        # Log error but continue (observations are optional for registry initialization)
        print(f"Warning: Could not load observations from JSON: {e}")

    return registry


if __name__ == "__main__":
    from registry import Registry

    registry = Registry()
    registry = collect(registry)

    print(f"✓ Barasertib (AURKB inhibitor) SCLC dataset loaded")
    print(f"  Papers: {len(registry.papers)}")
    print(f"  Contexts: {len(registry.contexts)}")
    print(f"  Assays: {len(registry.assays)}")
    print(f"  Conditions: {len(registry.conditions)}")
    # print(f"  Observations: {len(registry.observations)}")  # Will populate from JSON


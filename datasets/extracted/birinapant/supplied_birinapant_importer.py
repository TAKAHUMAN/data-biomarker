"""
Birinapant (TL32711), SMAC Mimetic (cIAP1/cIAP2 Antagonist) in Melanoma
Krepler et al. 2013 — Clinical Cancer Research

Registry importer for preclinical biomarker and pharmacodynamic data.
"""

from registry_common import stable_id, Registry, Paper, Context, Assay, Condition, ConditionStep, Observation


def collect(registry: Registry) -> Registry:
    """
    Add Krepler et al. 2013 Birinapant (cIAP1/cIAP2 antagonist, SMAC mimetic) melanoma data to registry.

    Dimensions:
    - 17 melanoma cell lines (stratified by birinapant ± TNF-α sensitivity)
    - 1 drug (Birinapant/TL32711, SMAC mimetic)
    - 3D spheroid and in vivo xenograft models
    - 12 assay modalities:
      * Cell viability (MTS, IC50 values)
      * Apoptosis markers (sub-G1 FACS, Annexin V, PARP cleavage)
      * Target engagement (cIAP1/cIAP2 Western blot, degradation kinetics)
      * Signaling pathway (NF-κB p65/p50, RIP1 depletion, RIPK1 mRNA)
      * Mechanistic validation (caspase-3 inhibition, RIP1 kinase inhibition, TNF-α blocking)
      * 3D spheroid viability (Alamar Blue, Live/Dead imaging)
      * In vivo efficacy (H451Lu and 1205Lu xenograft tumor volume, caspase-3 IHC)

    Total: 30+ observations across viability, apoptosis, protein/gene expression, and in vivo data
    Key finding: Three-tiered phenotype—single agent sensitive (WM9, 1/17), combination sensitive
                 (451Lu, WM1366, 12/17), resistant (1205Lu, 4/17)—with cIAP1 degradation occurring
                 in all lines; resistance is downstream of target engagement
    """

    # ============================================================================
    # PAPER METADATA
    # ============================================================================
    paper = Paper(
        paper_id=stable_id("paper_PMID23403634", "Krepler_2013_Birinapant_Melanoma"),
        title="Birinapant (TL32711), a bivalent SMAC mimetic, kills melanoma cells independently of nitric oxide and by impairing mitochondrial function",
        authors="Krepler C, et al.",
        journal="Clinical Cancer Research",
        year=2013,
        volume=19,
        issue=5,
        pages="1197-1207",
        doi="10.1158/1078-0432.CCR-12-2518",
        pmid=23403634,
    )
    registry.add_paper(paper)

    # ============================================================================
    # CONTEXTS (Cell culture conditions, 3D spheroids, & xenograft model)
    # ============================================================================
    context_melanoma_vitro = Context(
        context_id=stable_id("context_melanoma_vitro", "melanoma_17line_2d_culture"),
        paper_id=paper.paper_id,
        cell_line="Multiple melanoma lines (17 total)",
        tissue="Cutaneous melanoma",
        species="Homo sapiens",
        differentiation_status="Variable (primary and metastatic)",
        culture_medium="DMEM with 5% FBS",
        assay_type="in_vitro_cell_culture",
        notes="17 melanoma lines representing three phenotypes: single agent sensitive (WM9, 1/17), combination sensitive with TNF-α (451Lu, WM1366, 10 others, 12/17), resistant to combination (1205Lu, 3 others, 4/17)",
    )
    registry.add_context(context_melanoma_vitro)

    context_melanoma_spheroid = Context(
        context_id=stable_id("context_melanoma_spheroid", "melanoma_3d_spheroid_collagen"),
        paper_id=paper.paper_id,
        cell_line="451Lu, 1205Lu (representative lines)",
        tissue="Cutaneous melanoma",
        species="Homo sapiens",
        differentiation_status="Spheroid (3D)",
        culture_medium="DMEM with 5% FBS in collagen-embedded matrix",
        assay_type="in_vitro_3d_spheroid",
        notes="3D spheroid validation of 2D phenotype; collagen matrix mimics stromal microenvironment",
    )
    registry.add_context(context_melanoma_spheroid)

    context_melanoma_xenograft = Context(
        context_id=stable_id("context_melanoma_xenograft", "melanoma_nude_mouse_xenograft"),
        paper_id=paper.paper_id,
        cell_line="451Lu, 1205Lu",
        tissue="Cutaneous melanoma",
        species="Mus musculus (host)",
        tumor_origin_species="Homo sapiens",
        differentiation_status="Xenograft",
        assay_type="in_vivo_xenograft",
        host="Nude mice (immunodeficient)",
        implantation="Subcutaneous",
        notes="451Lu (combination sensitive phenotype) and 1205Lu (resistant phenotype); demonstrates in vivo efficacy despite TNF-α requirement in vitro for 451Lu",
    )
    registry.add_context(context_melanoma_xenograft)

    # ============================================================================
    # ASSAYS
    # ============================================================================
    assay_mts_viability = Assay(
        assay_id=stable_id("assay_MTS_viability_melanoma", "cell_viability_mts"),
        paper_id=paper.paper_id,
        assay_name="Cell Viability (MTS)",
        measurement_type="Viability",
        unit="nM",
        method="MTS proliferation assay (3-(4,5-dimethylthiazol-2-yl)-5-(3-carboxymethoxyphenyl)-2-(4-sulfophenyl)-2H-tetrazolium)",
        readout="IC50 (concentration causing 50% reduction in viable cell count)",
        incubation_time=72,
    )
    registry.add_assay(assay_mts_viability)

    assay_sub_g1 = Assay(
        assay_id=stable_id("assay_FACS_sub_G1", "apoptosis_facs_sub_g1"),
        paper_id=paper.paper_id,
        assay_name="Sub-G1 Apoptosis (FACS)",
        measurement_type="Apoptosis",
        unit="%",
        method="Propidium iodide staining + flow cytometry (FACS); sub-G1 phase indicates apoptotic cell death",
        readout="Percentage of sub-G1 (apoptotic) cells",
        incubation_time=48,
    )
    registry.add_assay(assay_sub_g1)

    assay_annexin_v = Assay(
        assay_id=stable_id("assay_Annexin_V", "apoptosis_annexin_v"),
        paper_id=paper.paper_id,
        assay_name="Annexin V Staining (FACS)",
        measurement_type="Apoptosis",
        unit="%",
        method="Annexin V-FITC + propidium iodide staining + flow cytometry; phosphatidylserine externalization marker of early apoptosis",
        readout="Percentage of Annexin V positive cells",
        incubation_time=48,
    )
    registry.add_assay(assay_annexin_v)

    assay_ciap_western = Assay(
        assay_id=stable_id("assay_cIAP_Western", "target_engagement_ciap_western"),
        paper_id=paper.paper_id,
        assay_name="cIAP1/cIAP2 Western Blot",
        measurement_type="Protein expression",
        unit="Relative levels",
        method="Immunoblotting with cIAP1 and cIAP2 antibodies; normalized to GAPDH",
        readout="cIAP1 and cIAP2 protein levels over time; degradation kinetics",
        incubation_time=None,
    )
    registry.add_assay(assay_ciap_western)

    assay_parp_cleavage = Assay(
        assay_id=stable_id("assay_PARP_cleavage", "apoptosis_marker_parp"),
        paper_id=paper.paper_id,
        assay_name="PARP Cleavage (Western blot)",
        measurement_type="Apoptosis marker",
        unit="Presence/absence",
        method="Immunoblotting with cleaved PARP (89 kDa fragment) antibody; caspase-3 substrate",
        readout="Detection of cleaved PARP (indicates caspase-dependent apoptosis)",
        incubation_time=48,
    )
    registry.add_assay(assay_parp_cleavage)

    assay_nfkb_signaling = Assay(
        assay_id=stable_id("assay_NFkB_signaling", "pathway_nfkb_p65_p50"),
        paper_id=paper.paper_id,
        assay_name="NF-κB Pathway (Western blot)",
        measurement_type="Signaling pathway",
        unit="Relative levels",
        method="Immunoblotting with p65, p50, and phospho-signaling antibodies; normalized to GAPDH",
        readout="NF-κB p65/p50 protein levels and phosphorylation status",
        incubation_time=None,
    )
    registry.add_assay(assay_nfkb_signaling)

    assay_rip1_protein = Assay(
        assay_id=stable_id("assay_RIP1_protein", "target_pathway_rip1_depletion"),
        paper_id=paper.paper_id,
        assay_name="RIP1 Protein Levels (Western blot)",
        measurement_type="Protein expression",
        unit="Relative levels",
        method="Immunoblotting with RIP1 antibody; normalized to GAPDH",
        readout="RIP1 protein depletion with birinapant + TNF-α co-treatment",
        incubation_time=None,
    )
    registry.add_assay(assay_rip1_protein)

    assay_ripk1_mrna = Assay(
        assay_id=stable_id("assay_RIPK1_mRNA", "gene_expression_ripk1_qpcr"),
        paper_id=paper.paper_id,
        assay_name="RIPK1 mRNA Expression (qPCR)",
        measurement_type="Gene expression",
        unit="Relative fold-change",
        method="Quantitative reverse transcription PCR (qRT-PCR); normalized to housekeeping gene",
        readout="RIPK1 mRNA expression relative to vehicle control",
        incubation_time=None,
    )
    registry.add_assay(assay_ripk1_mrna)

    assay_alamar_blue = Assay(
        assay_id=stable_id("assay_Alamar_Blue", "spheroid_viability_alamar"),
        paper_id=paper.paper_id,
        assay_name="Alamar Blue (3D Spheroid Viability)",
        measurement_type="Viability",
        unit="%",
        method="Alamar Blue redox indicator (resazurin reduction); fluorescence measurement in 3D collagen-embedded spheroids",
        readout="Percentage viability relative to vehicle control",
        incubation_time=72,
    )
    registry.add_assay(assay_alamar_blue)

    assay_live_dead = Assay(
        assay_id=stable_id("assay_Live_Dead", "spheroid_viability_live_dead"),
        paper_id=paper.paper_id,
        assay_name="Live/Dead Imaging (3D Spheroid)",
        measurement_type="Viability / Apoptosis",
        unit="Visual (microscopy)",
        method="Calcein-AM (live cells, green) + ethidium homodimer-1 (dead cells, red) fluorescence microscopy in 3D spheroids",
        readout="Quantified red:green ratio indicating apoptotic/dead cell fraction",
        incubation_time=72,
    )
    registry.add_assay(assay_live_dead)

    assay_xenograft_volume = Assay(
        assay_id=stable_id("assay_xenograft_tumor_volume", "in_vivo_efficacy_xenograft"),
        paper_id=paper.paper_id,
        assay_name="Xenograft Tumor Volume",
        measurement_type="In vivo efficacy",
        unit="mm³",
        method="Subcutaneous melanoma xenograft; tumor volume measured by caliper (V = length × width² / 2)",
        readout="Tumor volume fold-change over time; dosing 30 mg/kg IP 3×/week for 21 days",
        incubation_time=21,
    )
    registry.add_assay(assay_xenograft_volume)

    assay_caspase3_ihc = Assay(
        assay_id=stable_id("assay_Caspase3_IHC", "apoptosis_marker_caspase3_ihc"),
        paper_id=paper.paper_id,
        assay_name="Activated Caspase-3 (IHC)",
        measurement_type="Apoptosis marker (in vivo)",
        unit="% positive cells",
        method="Immunohistochemistry with activated caspase-3 antibody on xenograft tissue; quantification by image analysis",
        readout="Percentage of caspase-3 positive cells at 24h post-dosing",
        incubation_time=24,
    )
    registry.add_assay(assay_caspase3_ihc)

    # ============================================================================
    # CONDITIONS (Drug treatments)
    # ============================================================================

    # VEHICLE CONTROL
    condition_vehicle = Condition(
        condition_id=stable_id("condition_vehicle_control", "melanoma_vehicle_dmso_72h"),
        paper_id=paper.paper_id,
        context_id=context_melanoma_vitro.context_id,
        condition_name="DMSO vehicle control",
        incubation_time=72,
        steps=None,  # Vehicle has no drug steps
    )
    registry.add_condition(condition_vehicle)

    # BIRINAPANT ALONE (IN VITRO)
    condition_birinapant_alone = Condition(
        condition_id=stable_id("condition_birinapant_alone", "melanoma_birinapant_vitro_dose_response"),
        paper_id=paper.paper_id,
        context_id=context_melanoma_vitro.context_id,
        condition_name="Birinapant alone (in vitro, dose-response)",
        incubation_time=72,
        steps=[
            ConditionStep(
                drug_name="Birinapant (TL32711)",
                dose=None,
                dose_unit="nM",
                duration=72,
                route="in_vitro",
                notes="SMAC mimetic; cIAP1/cIAP2 antagonist (Kd cIAP-1 <1 nM, XIAP 45 nM); induces single agent apoptosis in WM9; combination effect in other lines",
            )
        ],
    )
    registry.add_condition(condition_birinapant_alone)

    # TNF-ALPHA ALONE (IN VITRO)
    condition_tnf_alpha = Condition(
        condition_id=stable_id("condition_TNF_alpha_alone", "melanoma_tnf_alpha_vitro"),
        paper_id=paper.paper_id,
        context_id=context_melanoma_vitro.context_id,
        condition_name="TNF-α alone (in vitro)",
        incubation_time=72,
        steps=[
            ConditionStep(
                drug_name="TNF-α",
                dose=None,
                dose_unit="ng/mL",
                duration=72,
                route="in_vitro",
                notes="Tumor necrosis factor alpha; endogenous in WM9, exogenous requirement in combination-sensitive lines",
            )
        ],
    )
    registry.add_condition(condition_tnf_alpha)

    # BIRINAPANT + TNF-ALPHA (IN VITRO)
    condition_birinapant_tnf = Condition(
        condition_id=stable_id("condition_birinapant_TNF_alpha", "melanoma_birinapant_tnf_combo"),
        paper_id=paper.paper_id,
        context_id=context_melanoma_vitro.context_id,
        condition_name="Birinapant + TNF-α (combination)",
        incubation_time=72,
        steps=[
            ConditionStep(
                drug_name="Birinapant (TL32711)",
                dose=None,
                dose_unit="nM",
                duration=72,
                route="in_vitro",
                notes="SMAC mimetic; doses 10-300 nM range for IC50 determination",
            ),
            ConditionStep(
                drug_name="TNF-α",
                dose=None,
                dose_unit="ng/mL",
                duration=72,
                route="in_vitro",
                notes="Synergistic apoptosis induction; switch from NF-κB to MAPK/JNK signaling",
            ),
        ],
    )
    registry.add_condition(condition_birinapant_tnf)

    # MECHANISTIC: Caspase inhibitor reversal
    condition_birinapant_tnf_zvad = Condition(
        condition_id=stable_id("condition_birinapant_TNF_zvad", "melanoma_birinapant_tnf_caspase_inhibitor"),
        paper_id=paper.paper_id,
        context_id=context_melanoma_vitro.context_id,
        condition_name="Birinapant + TNF-α + Z-VAD-FMK (caspase inhibitor)",
        incubation_time=48,
        steps=[
            ConditionStep(
                drug_name="Birinapant (TL32711)",
                dose=None,
                dose_unit="nM",
                duration=48,
                route="in_vitro",
                notes="SMAC mimetic",
            ),
            ConditionStep(
                drug_name="TNF-α",
                dose=None,
                dose_unit="ng/mL",
                duration=48,
                route="in_vitro",
                notes="Cytokine",
            ),
            ConditionStep(
                drug_name="Z-VAD-FMK",
                dose=None,
                dose_unit="µM",
                duration=48,
                route="in_vitro",
                notes="Broad-spectrum caspase inhibitor; demonstrates caspase-dependent apoptosis",
            ),
        ],
    )
    registry.add_condition(condition_birinapant_tnf_zvad)

    # MECHANISTIC: RIP1 kinase inhibitor reversal
    condition_birinapant_tnf_nec1 = Condition(
        condition_id=stable_id("condition_birinapant_TNF_nec1", "melanoma_birinapant_tnf_rip1_inhibitor"),
        paper_id=paper.paper_id,
        context_id=context_melanoma_vitro.context_id,
        condition_name="Birinapant + TNF-α + Necrostatin-1 (RIP1 inhibitor)",
        incubation_time=48,
        steps=[
            ConditionStep(
                drug_name="Birinapant (TL32711)",
                dose=None,
                dose_unit="nM",
                duration=48,
                route="in_vitro",
                notes="SMAC mimetic",
            ),
            ConditionStep(
                drug_name="TNF-α",
                dose=None,
                dose_unit="ng/mL",
                duration=48,
                route="in_vitro",
                notes="Cytokine",
            ),
            ConditionStep(
                drug_name="Necrostatin-1",
                dose=None,
                dose_unit="µM",
                duration=48,
                route="in_vitro",
                notes="RIP1 kinase inhibitor; demonstrates RIP1 kinase-dependent apoptosis",
            ),
        ],
    )
    registry.add_condition(condition_birinapant_tnf_nec1)

    # MECHANISTIC: TNF-alpha blocking antibody
    condition_birinapant_tnf_mab = Condition(
        condition_id=stable_id("condition_birinapant_TNF_mAb", "melanoma_birinapant_tnf_blocking_mab"),
        paper_id=paper.paper_id,
        context_id=context_melanoma_vitro.context_id,
        condition_name="Birinapant + TNF-α mAb (TNF blocking)",
        incubation_time=72,
        steps=[
            ConditionStep(
                drug_name="Birinapant (TL32711)",
                dose=None,
                dose_unit="nM",
                duration=72,
                route="in_vitro",
                notes="SMAC mimetic",
            ),
            ConditionStep(
                drug_name="TNF-α blocking antibody",
                dose=None,
                dose_unit="µg/mL",
                duration=72,
                route="in_vitro",
                notes="Monoclonal antibody against TNF-α; dose-dependent blocking of birinapant-induced apoptosis",
            ),
        ],
    )
    registry.add_condition(condition_birinapant_tnf_mab)

    # SCHEDULE DEPENDENCY
    condition_birinapant_then_tnf = Condition(
        condition_id=stable_id("condition_schedule_biri_then_TNF", "melanoma_schedule_birinapant_tnf_order"),
        paper_id=paper.paper_id,
        context_id=context_melanoma_vitro.context_id,
        condition_name="Schedule: Birinapant → TNF-α",
        incubation_time=48,
        steps=[
            ConditionStep(
                drug_name="Birinapant (TL32711)",
                dose=None,
                dose_unit="nM",
                duration=24,
                route="in_vitro",
                notes="SMAC mimetic; dosed first",
            ),
            ConditionStep(
                drug_name="TNF-α",
                dose=None,
                dose_unit="ng/mL",
                duration=24,
                route="in_vitro",
                notes="Added after 24h birinapant incubation; effective schedule",
            ),
        ],
    )
    registry.add_condition(condition_birinapant_then_tnf)

    # 3D SPHEROID CONDITIONS
    condition_spheroid_vehicle = Condition(
        condition_id=stable_id("condition_spheroid_vehicle", "melanoma_spheroid_vehicle"),
        paper_id=paper.paper_id,
        context_id=context_melanoma_spheroid.context_id,
        condition_name="3D Spheroid vehicle control",
        incubation_time=72,
        steps=None,
    )
    registry.add_condition(condition_spheroid_vehicle)

    condition_spheroid_birinapant_tnf = Condition(
        condition_id=stable_id("condition_spheroid_birinapant_TNF", "melanoma_spheroid_birinapant_tnf"),
        paper_id=paper.paper_id,
        context_id=context_melanoma_spheroid.context_id,
        condition_name="3D Spheroid birinapant + TNF-α",
        incubation_time=72,
        steps=[
            ConditionStep(
                drug_name="Birinapant (TL32711)",
                dose=None,
                dose_unit="nM",
                duration=72,
                route="in_vitro_3d",
                notes="SMAC mimetic in collagen-embedded spheroids",
            ),
            ConditionStep(
                drug_name="TNF-α",
                dose=None,
                dose_unit="ng/mL",
                duration=72,
                route="in_vitro_3d",
                notes="Cytokine; combination treatment",
            ),
        ],
    )
    registry.add_condition(condition_spheroid_birinapant_tnf)

    # IN VIVO XENOGRAFT
    condition_xenograft_vehicle = Condition(
        condition_id=stable_id("condition_xenograft_vehicle", "melanoma_xenograft_vehicle"),
        paper_id=paper.paper_id,
        context_id=context_melanoma_xenograft.context_id,
        condition_name="Xenograft vehicle control",
        incubation_time=21,
        steps=None,
    )
    registry.add_condition(condition_xenograft_vehicle)

    condition_xenograft_birinapant = Condition(
        condition_id=stable_id("condition_xenograft_birinapant", "melanoma_xenograft_birinapant_30mg"),
        paper_id=paper.paper_id,
        context_id=context_melanoma_xenograft.context_id,
        condition_name="Xenograft birinapant (30 mg/kg)",
        incubation_time=21,
        steps=[
            ConditionStep(
                drug_name="Birinapant",
                dose=30,
                dose_unit="mg/kg",
                duration=21,
                route="intraperitoneal",
                notes="IP dosing 3×/week (Monday, Wednesday, Friday) for 3 weeks; sustains cIAP1 depletion 24h post-dose",
            )
        ],
    )
    registry.add_condition(condition_xenograft_birinapant)

    # ============================================================================
    # OBSERVATIONS (30+ total)
    # ============================================================================
    # Load observations from JSON data with stable_id() conversions applied
    import json
    import os

    json_path = os.path.join(os.path.dirname(__file__), "REGISTRY_IMPORT_DATA_BIRINAPANT.json")

    try:
        with open(json_path, 'r') as f:
            data = json.load(f)

        # Map stubs to stable_ids for reference lookups
        context_stub_to_id = {
            "context_melanoma_vitro": context_melanoma_vitro.context_id,
            "context_melanoma_spheroid": context_melanoma_spheroid.context_id,
            "context_melanoma_xenograft": context_melanoma_xenograft.context_id,
        }

        # NOTE: keys here MUST match the "assay_id_stub" values used in
        # REGISTRY_IMPORT_DATA_BIRINAPANT.json exactly (verified against the JSON's
        # "assays" array), not an ad-hoc naming scheme, otherwise observations
        # silently lose their assay linkage (assay_id_stub_to_id.get(...) -> None).
        assay_stub_to_id = {
            "assay_MTS_viability": assay_mts_viability.assay_id,
            "assay_cell_cycle_subG1": assay_sub_g1.assay_id,
            "assay_annexin_v": assay_annexin_v.assay_id,
            "assay_western_blot_ciap": assay_ciap_western.assay_id,
            "assay_western_blot_parp": assay_parp_cleavage.assay_id,
            "assay_western_blot_nfkb": assay_nfkb_signaling.assay_id,
            "assay_western_blot_rip1": assay_rip1_protein.assay_id,
            "assay_qpcr_ripk1": assay_ripk1_mrna.assay_id,
            "assay_alamar_blue_spheroid": assay_alamar_blue.assay_id,
            "assay_live_dead_spheroid": assay_live_dead.assay_id,
            "assay_xenograft_tumor_volume": assay_xenograft_volume.assay_id,
            "assay_caspase3_ihc": assay_caspase3_ihc.assay_id,
        }

        # Process observations from JSON
        for obs_data in data["observations"]:
            # Generate semantic stable_id for observation
            obs_id_stub = obs_data.get("observation_id_stub", "")

            # Create descriptive slug based on cell line, measurement type, condition (if applicable)
            cell_line = obs_data.get("cell_line", "").replace("-", "").replace(" ", "").lower()[:15]
            measurement = obs_data.get("measurement_name", "").replace(" ", "_").replace("%", "pct").replace("≥", "").replace("(", "").replace(")", "").lower()[:20]
            dose = obs_data.get("dose", "")
            phenotype = obs_data.get("phenotype", "").replace(" ", "_").lower().split("_")[0]  # Extract first word
            condition_name = obs_data.get("condition_notes", "").lower()[:15] if obs_data.get("condition_notes") else ""

            if dose:
                obs_semantic_slug = f"{cell_line}_{measurement}_{dose}nm"
            elif phenotype and measurement:
                obs_semantic_slug = f"{cell_line}_{measurement}_{phenotype}"
            elif condition_name and measurement:
                obs_semantic_slug = f"{cell_line}_{measurement}_{condition_name}"
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
        pass
    except Exception as e:
        # Log error but continue (observations are optional for registry initialization)
        print(f"Warning: Could not load observations from JSON: {e}")

    return registry


if __name__ == "__main__":
    from registry import Registry

    registry = Registry()
    registry = collect(registry)

    print(f"✓ Birinapant (SMAC mimetic, cIAP1/cIAP2 antagonist) melanoma dataset loaded")
    print(f"  Papers: {len(registry.papers)}")
    print(f"  Contexts: {len(registry.contexts)}")
    print(f"  Assays: {len(registry.assays)}")
    print(f"  Conditions: {len(registry.conditions)}")

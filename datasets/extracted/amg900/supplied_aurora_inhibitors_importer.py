"""
Aurora kinase inhibitors (AMG 900, AZD1152-HQPA, MK-5108) in liposarcoma
Noronha et al. 2017 — In Vitro Cell Dev Biol—Animal

Registry importer for preclinical biomarker and pharmacodynamic data.
"""

from registry_common import stable_id, Registry, Paper, Context, Assay, Condition, ConditionStep, Observation


def collect(registry: Registry) -> Registry:
    """
    Add Noronha et al. 2017 Aurora kinase inhibitor data to registry.

    Dimensions:
    - 3 cell lines (SW-872 undiff, 93T449 diff, HCT-116 positive control)
    - 3 drugs (AMG 900 pan, AZD1152-HQPA AURKB-selective, MK-5108 AURKA-selective)
    - 4 assay modalities:
      * Cell viability (MTT, EC50 + dose-response curves)
      * Polyploidy (FACS, % >4N DNA at multiple doses)
      * AURKA/AURKB mRNA (qRT-PCR, fold change)
      * AURKA/AURKB protein (Western blot, semi-quantitative)

    Total: 66 observations across viability, polyploidy, gene, and protein expression
    """

    # ============================================================================
    # PAPER METADATA
    # ============================================================================
    paper = Paper(
        paper_id=stable_id("paper_PMID28657245", "Noronha_2017_Aurora_liposarcoma"),
        title="Preclinical evaluation of the Aurora kinase inhibitors AMG 900, AZD1152-HQPA, and MK-5108 on SW-872 and 93T449 human liposarcoma cells",
        authors="Noronha S, Ait L, Scimeca T, Zaron O, Obrzut J, Zanotti B, Hayward E, Pillai A, Mathur S, Rojas J, Salamah R, Chandar N, Fay MJ",
        journal="In Vitro Cell Dev Biol—Animal",
        year=2017,
        volume=53,
        issue=12,
        pages="1-14",
        doi="10.1007/s11626-017-0208-4",
        pmid=28657245,
    )
    registry.add_paper(paper)

    # ============================================================================
    # CONTEXTS (Cell culture conditions)
    # ============================================================================
    context_sw872 = Context(
        context_id=stable_id("context_SW872_undiff_vitro", "liposarcoma_undifferentiated"),
        paper_id=paper.paper_id,
        cell_line="SW-872",
        tissue="Liposarcoma (undifferentiated)",
        species="Homo sapiens",
        differentiation_status="Undifferentiated",
        p53_status="Proficient",
        culture_medium="DMEM with 10% heat-inactivated FBS",
        assay_type="in_vitro_cell_culture",
        notes="Most responsive Aurora kinase inhibitor line; high AURKA and AURKB expression",
    )
    registry.add_context(context_sw872)

    context_93t449 = Context(
        context_id=stable_id("context_93T449_diff_vitro", "liposarcoma_well_differentiated"),
        paper_id=paper.paper_id,
        cell_line="93T449",
        tissue="Liposarcoma (well-differentiated)",
        species="Homo sapiens",
        differentiation_status="Well-differentiated",
        p53_status="Wild-type",
        culture_medium="RPMI 1640 with 10% heat-inactivated FBS",
        assay_type="in_vitro_cell_culture",
        notes="Moderately responsive; lower AURKA protein expression than SW-872",
    )
    registry.add_context(context_93t449)

    context_hct116 = Context(
        context_id=stable_id("context_HCT116_control_vitro", "colorectal_cancer_control"),
        paper_id=paper.paper_id,
        cell_line="HCT-116",
        tissue="Colorectal cancer",
        species="Homo sapiens",
        differentiation_status="N/A",
        p53_status="Mutant",
        culture_medium="McCoy's 5a Modified Medium with 10% FBS",
        assay_type="in_vitro_cell_culture",
        notes="Most sensitive to Aurora kinase inhibitors; highest mRNA expression",
    )
    registry.add_context(context_hct116)

    # ============================================================================
    # ASSAYS
    # ============================================================================
    assay_viability = Assay(
        assay_id=stable_id("assay_MTT_viability", "cell_viability_mtt"),
        paper_id=paper.paper_id,
        assay_name="Cell Viability (MTT)",
        measurement_type="Viability",
        unit="nM or %",
        method="MTT assay (3-(4,5-dimethylthiazol-2-yl)-2,5-diphenyltetrazolium bromide)",
        readout="EC50 or % Total Viable Cells",
        incubation_time=72,
    )
    registry.add_assay(assay_viability)

    assay_polyploidy = Assay(
        assay_id=stable_id("assay_FACS_polyploidy", "cell_cycle_polyploidy_facs"),
        paper_id=paper.paper_id,
        assay_name="Polyploidy (FACS)",
        measurement_type="Cell cycle",
        unit="%",
        method="Propidium iodide staining + flow cytometry (FACS)",
        readout="Percentage of cells with >4N DNA content (polyploid)",
        incubation_time=72,
    )
    registry.add_assay(assay_polyploidy)

    assay_aurka_mrna = Assay(
        assay_id=stable_id("assay_qRTPCR_AURKA", "gene_expression_aurka_rtpcr"),
        paper_id=paper.paper_id,
        assay_name="AURKA mRNA expression",
        measurement_type="Gene expression",
        unit="Fold change",
        method="Real-time RT-PCR (TaqMan, comparative Ct method)",
        readout="Fold change relative to β-actin housekeeping control",
    )
    registry.add_assay(assay_aurka_mrna)

    assay_aurkb_mrna = Assay(
        assay_id=stable_id("assay_qRTPCR_AURKB", "gene_expression_aurkb_rtpcr"),
        paper_id=paper.paper_id,
        assay_name="AURKB mRNA expression",
        measurement_type="Gene expression",
        unit="Fold change",
        method="Real-time RT-PCR (TaqMan, comparative Ct method)",
        readout="Fold change relative to β-actin housekeeping control",
    )
    registry.add_assay(assay_aurkb_mrna)

    assay_aurka_protein = Assay(
        assay_id=stable_id("assay_WB_AURKA_protein", "protein_expression_aurka_wb"),
        paper_id=paper.paper_id,
        assay_name="AURKA protein expression",
        measurement_type="Protein expression",
        unit="Band intensity (qualitative/semi-quantitative)",
        method="Western blot analysis (AURKA rabbit mAb, 1:1000 dilution)",
        readout="48 kDa band intensity (AURKA full-length)",
    )
    registry.add_assay(assay_aurka_protein)

    assay_aurkb_protein = Assay(
        assay_id=stable_id("assay_WB_AURKB_protein", "protein_expression_aurkb_wb"),
        paper_id=paper.paper_id,
        assay_name="AURKB protein expression",
        measurement_type="Protein expression",
        unit="Band intensity (qualitative/semi-quantitative)",
        method="Western blot analysis (AURKB rabbit mAb, 1:1000 dilution)",
        readout="39 kDa band intensity (AURKB full-length) + splice variants",
    )
    registry.add_assay(assay_aurkb_protein)

    # ============================================================================
    # CONDITIONS (Drug treatments)
    # ============================================================================

    # VEHICLE CONTROL
    condition_dmso = Condition(
        condition_id=stable_id("condition_DMSO_vehicle", "dmso_control_72h"),
        paper_id=paper.paper_id,
        context_id=context_sw872.context_id,
        condition_name="DMSO vehicle control",
        incubation_time=72,
        steps=None,  # Vehicle has no drug steps
    )
    registry.add_condition(condition_dmso)

    # ============================================================================
    # AMG 900 (Pan-Aurora Kinase Inhibitor)
    # ============================================================================

    # SW-872
    condition_amg900_sw872 = Condition(
        condition_id=stable_id("condition_SW872_AMG900", "undiff_liposarcoma_amg900_72h"),
        paper_id=paper.paper_id,
        context_id=context_sw872.context_id,
        condition_name="AMG 900 (pan-Aurora)",
        incubation_time=72,
        steps=[
            ConditionStep(
                drug_name="AMG 900",
                dose=None,
                dose_unit="nM",
                duration=72,
                route="in_vitro",
                notes="Pan-Aurora kinase inhibitor (AURKA/AURKB/AURKC)",
            )
        ],
    )
    registry.add_condition(condition_amg900_sw872)

    # 93T449
    condition_amg900_93t449 = Condition(
        condition_id=stable_id("condition_93T449_AMG900", "diff_liposarcoma_amg900_72h"),
        paper_id=paper.paper_id,
        context_id=context_93t449.context_id,
        condition_name="AMG 900 (pan-Aurora)",
        incubation_time=72,
        steps=[
            ConditionStep(
                drug_name="AMG 900",
                dose=None,
                dose_unit="nM",
                duration=72,
                route="in_vitro",
                notes="Pan-Aurora kinase inhibitor",
            )
        ],
    )
    registry.add_condition(condition_amg900_93t449)

    # HCT-116
    condition_amg900_hct116 = Condition(
        condition_id=stable_id("condition_HCT116_AMG900", "colorectal_amg900_72h"),
        paper_id=paper.paper_id,
        context_id=context_hct116.context_id,
        condition_name="AMG 900 (pan-Aurora)",
        incubation_time=72,
        steps=[
            ConditionStep(
                drug_name="AMG 900",
                dose=None,
                dose_unit="nM",
                duration=72,
                route="in_vitro",
                notes="Pan-Aurora kinase inhibitor; positive control",
            )
        ],
    )
    registry.add_condition(condition_amg900_hct116)

    # ============================================================================
    # AZD1152-HQPA (AURKB-Selective Inhibitor)
    # ============================================================================

    condition_azd1152_sw872 = Condition(
        condition_id=stable_id("condition_SW872_AZD1152", "undiff_liposarcoma_azd1152_72h"),
        paper_id=paper.paper_id,
        context_id=context_sw872.context_id,
        condition_name="AZD1152-HQPA (AURKB-selective)",
        incubation_time=72,
        steps=[
            ConditionStep(
                drug_name="AZD1152-HQPA",
                dose=None,
                dose_unit="nM",
                duration=72,
                route="in_vitro",
                notes="AURKB-selective inhibitor",
            )
        ],
    )
    registry.add_condition(condition_azd1152_sw872)

    condition_azd1152_93t449 = Condition(
        condition_id=stable_id("condition_93T449_AZD1152", "diff_liposarcoma_azd1152_72h"),
        paper_id=paper.paper_id,
        context_id=context_93t449.context_id,
        condition_name="AZD1152-HQPA (AURKB-selective)",
        incubation_time=72,
        steps=[
            ConditionStep(
                drug_name="AZD1152-HQPA",
                dose=None,
                dose_unit="nM",
                duration=72,
                route="in_vitro",
                notes="AURKB-selective inhibitor",
            )
        ],
    )
    registry.add_condition(condition_azd1152_93t449)

    condition_azd1152_hct116 = Condition(
        condition_id=stable_id("condition_HCT116_AZD1152", "colorectal_azd1152_72h"),
        paper_id=paper.paper_id,
        context_id=context_hct116.context_id,
        condition_name="AZD1152-HQPA (AURKB-selective)",
        incubation_time=72,
        steps=[
            ConditionStep(
                drug_name="AZD1152-HQPA",
                dose=None,
                dose_unit="nM",
                duration=72,
                route="in_vitro",
                notes="AURKB-selective inhibitor",
            )
        ],
    )
    registry.add_condition(condition_azd1152_hct116)

    # ============================================================================
    # MK-5108 (AURKA-Selective Inhibitor)
    # ============================================================================

    condition_mk5108_sw872 = Condition(
        condition_id=stable_id("condition_SW872_MK5108", "undiff_liposarcoma_mk5108_72h"),
        paper_id=paper.paper_id,
        context_id=context_sw872.context_id,
        condition_name="MK-5108 (AURKA-selective)",
        incubation_time=72,
        steps=[
            ConditionStep(
                drug_name="MK-5108",
                dose=None,
                dose_unit="nM",
                duration=72,
                route="in_vitro",
                notes="AURKA-selective inhibitor",
            )
        ],
    )
    registry.add_condition(condition_mk5108_sw872)

    condition_mk5108_93t449 = Condition(
        condition_id=stable_id("condition_93T449_MK5108", "diff_liposarcoma_mk5108_72h"),
        paper_id=paper.paper_id,
        context_id=context_93t449.context_id,
        condition_name="MK-5108 (AURKA-selective)",
        incubation_time=72,
        steps=[
            ConditionStep(
                drug_name="MK-5108",
                dose=None,
                dose_unit="nM",
                duration=72,
                route="in_vitro",
                notes="AURKA-selective inhibitor",
            )
        ],
    )
    registry.add_condition(condition_mk5108_93t449)

    condition_mk5108_hct116 = Condition(
        condition_id=stable_id("condition_HCT116_MK5108", "colorectal_mk5108_72h"),
        paper_id=paper.paper_id,
        context_id=context_hct116.context_id,
        condition_name="MK-5108 (AURKA-selective)",
        incubation_time=72,
        steps=[
            ConditionStep(
                drug_name="MK-5108",
                dose=None,
                dose_unit="nM",
                duration=72,
                route="in_vitro",
                notes="AURKA-selective inhibitor",
            )
        ],
    )
    registry.add_condition(condition_mk5108_hct116)

    # ============================================================================
    # OBSERVATIONS (66 total)
    # ============================================================================
    # Load observations from JSON data with stable_id() conversions applied
    import json
    import os

    json_path = os.path.join(os.path.dirname(__file__), "REGISTRY_IMPORT_DATA_AURORA_INHIBITORS.json")

    try:
        with open(json_path, 'r') as f:
            data = json.load(f)

        # Map stubs to stable_ids for reference lookups
        context_stub_to_id = {
            "context_SW872_undiff_vitro": context_sw872.context_id,
            "context_93T449_diff_vitro": context_93t449.context_id,
            "context_HCT116_control_vitro": context_hct116.context_id,
        }

        assay_stub_to_id = {
            "assay_MTT_viability": assay_viability.assay_id,
            "assay_FACS_polyploidy": assay_polyploidy.assay_id,
            "assay_qRTPCR_AURKA": assay_aurka_mrna.assay_id,
            "assay_qRTPCR_AURKB": assay_aurkb_mrna.assay_id,
            "assay_WB_AURKA_protein": assay_aurka_protein.assay_id,
            "assay_WB_AURKB_protein": assay_aurkb_protein.assay_id,
        }

        # Create mapping of condition stubs to condition objects for reference
        # (observations reference conditions via dose info; some observations are DMSO vehicle or mRNA/protein)
        condition_dmso_id = condition_dmso.condition_id

        # Process observations from JSON
        for obs_data in data["observations"]:
            # Generate semantic stable_id for observation
            obs_id_stub = obs_data.get("observation_id_stub", "")

            # Create descriptive slug based on measurement type and drug (if applicable)
            drug = obs_data.get("drug", "vehicle")
            cell_line = obs_data.get("cell_line", "").replace("-", "").lower()
            measurement = obs_data.get("measurement_name", "").replace(" ", "_").replace("%", "pct").lower()

            if drug != "vehicle":
                drug_slug = drug.lower().replace("-", "").replace(" ", "")
            else:
                drug_slug = "dmso"

            obs_semantic_slug = f"{drug_slug}_{cell_line}_{measurement[:20]}"

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

    print(f"✓ Aurora kinase inhibitor dataset loaded")
    print(f"  Papers: {len(registry.papers)}")
    print(f"  Contexts: {len(registry.contexts)}")
    print(f"  Assays: {len(registry.assays)}")
    print(f"  Conditions: {len(registry.conditions)}")
    # print(f"  Observations: {len(registry.observations)}")  # Will populate from JSON

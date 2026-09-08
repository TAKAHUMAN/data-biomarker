from __future__ import annotations

import sys
import unittest
from pathlib import Path


TOOLS = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(TOOLS))

from importers import dinaciclib
from registry_common import Registry


PAPER_SHAO = "paper_PMID31561409"
PAPER_XU = "paper_PMID31349793"


class DinaciclibImporterTests(unittest.TestCase):
    def setUp(self) -> None:
        self.registry = Registry()
        dinaciclib.collect(self.registry)

    def test_two_papers_registered(self) -> None:
        paper_ids = {row["paper_id"] for row in self.registry.tables["papers"]}
        self.assertEqual(paper_ids, {PAPER_SHAO, PAPER_XU})

    def test_no_paper_artifact_row(self) -> None:
        # No local paper PDF/HTML file exists for either study; only WORKBOOK/
        # EXTRACTION_ARTIFACT source_artifacts should be registered.
        types = {row["artifact_type"] for row in self.registry.tables["source_artifacts"]}
        self.assertNotIn("PAPER", types)

    def test_referential_integrity(self) -> None:
        context_ids = {row["context_id"] for row in self.registry.tables["contexts"]}
        condition_ids = {row["condition_id"] for row in self.registry.tables["conditions"]}
        assay_ids = {row["assay_id"] for row in self.registry.tables["assays"]}
        for row in self.registry.tables["observations"]:
            self.assertIn(row["context_id"], context_ids)
            self.assertIn(row["condition_id"], condition_ids)
            self.assertIn(row["assay_id"], assay_ids)
            self.assertIn(row["paper_id"], {PAPER_SHAO, PAPER_XU})

    def test_fig5a_duplicated_rows_not_quantitative(self) -> None:
        # Data-quality flag (a): the CDK9/p-Rb/p-ATM/p-RNPII rows in Shao Fig5A share
        # one identical six-number densitometry row and must never be imported as
        # independent QUANTITATIVE observations.
        duplicated_targets = {"cdk9", "p_rb_s807_t811", "p_atm_s1981", "p_rnpii_s2"}
        fig5a_rows = [
            row for row in self.registry.tables["observations"]
            if row["figure"] == "Figure 5" and row["panel"] == "A"
        ]
        self.assertGreater(len(fig5a_rows), 0)
        for row in fig5a_rows:
            observable = row["observable"]
            if any(observable == f"densitometry_{target}" for target in duplicated_targets):
                self.assertEqual(row["quality_class"], "NOT_MODEL_READY", observable)
            elif observable.startswith("densitometry_cdk"):
                self.assertEqual(row["quality_class"], "QUANTITATIVE", observable)

    def test_fig3a_duplicate_pair_flagged(self) -> None:
        # Data-quality flag (a, smaller instance): Fig3A "Rb (total), PLC5" duplicates
        # "p-RNPII (S2), PLC5" and must be NOT_MODEL_READY.
        rows = [
            row for row in self.registry.tables["observations"]
            if row["figure"] == "Figure 3" and row["panel"] == "A"
            and row["observable"] == "densitometry_rb_total"
            and "PLC5" in row["observable_raw_label"]
        ]
        self.assertEqual(len(rows), 8)
        self.assertTrue(all(row["quality_class"] == "NOT_MODEL_READY" for row in rows))

    def test_tumor_volume_and_tunel_both_present(self) -> None:
        # Data-quality flag (b): tumor-volume/TUNEL divergence -- both endpoints kept.
        tumor = [row for row in self.registry.tables["observations"] if row["observable"] == "xenograft_tumor_volume" and row["paper_id"] == PAPER_SHAO]
        tunel = [row for row in self.registry.tables["observations"] if row["observable"] == "tunel_apoptosis_ratio"]
        self.assertGreater(len(tumor), 0)
        self.assertEqual(len(tunel), 3)

    def test_mtt_and_colony_ic50_distinct_observables(self) -> None:
        # Data-quality flag (c): MTT IC50 and colony-formation potency must never share
        # an observable name.
        observables = {row["observable"] for row in self.registry.tables["observations"]}
        self.assertIn("viability_IC50", observables)
        self.assertIn("colony_formation_relative", observables)

    def test_ccne1_context_alterations(self) -> None:
        alterations = {(row["gene"], row["alteration_type"]) for row in self.registry.tables["context_alterations"]}
        self.assertIn(("CCNE1", "OTHER"), alterations)
        self.assertIn(("CCNE1", "OVEREXPRESSION"), alterations)
        self.assertIn(("MCL1", "OVEREXPRESSION"), alterations)
        self.assertIn(("STAT3", "OVEREXPRESSION"), alterations)

    def test_ccne1_not_a_dinaciclib_observable(self) -> None:
        # Tier 0: dinaciclib does not modulate CCNE1 -- no observation with a
        # CCNE1-labeled observable should be attached to a Dinaciclib condition_step.
        din_id = next(row["perturbation_id"] for row in self.registry.tables["perturbations"] if row["name"] == "Dinaciclib")
        din_condition_ids = {row["condition_id"] for row in self.registry.tables["condition_steps"] if row["perturbation_id"] == din_id}
        for row in self.registry.tables["observations"]:
            if "ccne1" in (row["observable"] or "").lower():
                self.assertNotIn(row["condition_id"], din_condition_ids)


if __name__ == "__main__":
    unittest.main()

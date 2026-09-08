from __future__ import annotations

import sys
import unittest
from pathlib import Path


TOOLS = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(TOOLS))

from importers import dactolisib_mm
from registry_common import Registry


class DactolisibMMImporterTests(unittest.TestCase):
    def setUp(self) -> None:
        self.registry = Registry()
        dactolisib_mm.collect(self.registry)

    def test_counts_and_references(self) -> None:
        self.assertEqual(len(self.registry.tables["papers"]), 1)
        self.assertEqual(len(self.registry.tables["contexts"]), 32)
        self.assertEqual(len(self.registry.tables["assays"]), 9)
        self.assertEqual(len(self.registry.tables["observations"]), 165)
        self.assertEqual(len(self.registry.tables["extraction_runs"]), 165)
        condition_ids = {row["condition_id"] for row in self.registry.tables["conditions"]}
        self.assertTrue(all(row["condition_id"] in condition_ids for row in self.registry.tables["observations"]))
        context_ids = {row["context_id"] for row in self.registry.tables["contexts"]}
        self.assertTrue(all(row["context_id"] in context_ids for row in self.registry.tables["observations"]))

    def test_no_paper_artifact_row(self) -> None:
        # No local paper PDF/HTML file exists for PMID 19584292; only WORKBOOK/
        # EXTRACTION_ARTIFACT source_artifacts should be registered.
        types = {row["artifact_type"] for row in self.registry.tables["source_artifacts"]}
        self.assertNotIn("PAPER", types)

    def test_ic50_censoring_for_high_ic50_lines(self) -> None:
        rows = [row for row in self.registry.tables["observations"] if row["observable"] == "viability_IC50"]
        self.assertEqual(len(rows), 21)
        censored = [row for row in rows if row["is_censored"]]
        self.assertEqual(len(censored), 4)
        self.assertTrue(all(row["value"] is None and row["censoring_limit"] == 800.0 for row in censored))

    def test_bcl2_rescue_nonzero_plateau(self) -> None:
        contexts = {row["context_id"]: row["cell_line"] for row in self.registry.tables["contexts"]}
        rows = [
            row for row in self.registry.tables["observations"]
            if row["observable"] == "pct_survival" and contexts.get(row["context_id"]) == "MM.1S-Bcl-2"
        ]
        self.assertEqual(len(rows), 8)
        high_dose_values = sorted(row["value"] for row in rows if row["time_value"] == 48.0)[:1]
        # The highest-dose points should sit well above zero (non-zero plateau), unlike parental.
        self.assertTrue(all(value >= 30.0 for row in rows for value in [row["value"]] if row["observable_raw_label"].endswith("800 nmol/L BEZ235")))

    def test_akt_overexpression_context_alteration(self) -> None:
        alterations = {(row["gene"], row["alteration_type"]) for row in self.registry.tables["context_alterations"]}
        self.assertIn(("AKT1", "OVEREXPRESSION"), alterations)
        self.assertIn(("BCL2", "OVEREXPRESSION"), alterations)

    def test_not_quantifiable_figures_excluded_from_observations(self) -> None:
        # Fig4 gene-signature bars must never appear as numeric observations.
        fig4_rows = [row for row in self.registry.tables["observations"] if row["figure"] == "Figure 4"]
        self.assertEqual(len(fig4_rows), 0)


if __name__ == "__main__":
    unittest.main()

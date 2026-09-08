from __future__ import annotations

import sys
import unittest
from pathlib import Path


TOOLS = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(TOOLS))

from importers import amg900
from registry_common import Registry


class AMG900ImporterTests(unittest.TestCase):
    def setUp(self) -> None:
        self.registry = Registry()
        amg900.collect(self.registry)

    def test_counts_and_references(self) -> None:
        self.assertEqual(len(self.registry.tables["papers"]), 1)
        self.assertEqual(len(self.registry.tables["contexts"]), 3)
        self.assertEqual(len(self.registry.tables["assays"]), 6)
        self.assertEqual(len(self.registry.tables["observations"]), 66)
        self.assertEqual(len(self.registry.tables["extraction_runs"]), 66)
        condition_ids = {row["condition_id"] for row in self.registry.tables["conditions"]}
        assay_ids = {row["assay_id"] for row in self.registry.tables["assays"]}
        self.assertTrue(all(row["condition_id"] in condition_ids for row in self.registry.tables["observations"]))
        self.assertTrue(all(row["assay_id"] in assay_ids for row in self.registry.tables["observations"]))

    def test_exact_ec50_values_and_metadata(self) -> None:
        paper = self.registry.tables["papers"][0]
        self.assertEqual(paper["pmid"], "29197031")
        self.assertEqual(paper["year"], 2018)
        ec50 = sorted(
            row["value"] for row in self.registry.tables["observations"]
            if row["observable"] == "viability_EC50"
        )
        self.assertEqual(ec50, [1.4, 3.7, 6.5, 27.3, 43.4, 74.5, 135.1, 283.6, 309.0])

    def test_plot_and_blot_quality_are_not_overstated(self) -> None:
        rows = self.registry.tables["observations"]
        plotted = [row for row in rows if row["extraction_method"] == "PLOT_DIGITIZED"]
        blots = [row for row in rows if row["observable"] in {"AURKA_protein", "AURKB_protein"}]
        self.assertTrue(plotted)
        self.assertTrue(all(row["quality_class"] == "SEMI_QUANTITATIVE" for row in plotted))
        self.assertEqual(len(blots), 4)
        self.assertTrue(all(row["extraction_method"] == "IMAGE_DERIVED" for row in blots))
        self.assertTrue(all(row["quality_class"] == "QUALITATIVE_VALIDATION" for row in blots))


if __name__ == "__main__":
    unittest.main()

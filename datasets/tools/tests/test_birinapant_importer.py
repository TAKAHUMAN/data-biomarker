from __future__ import annotations

import sys
import unittest
from pathlib import Path


TOOLS = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(TOOLS))

from importers import birinapant
from registry_common import Registry


class BirinapantImporterTests(unittest.TestCase):
    def setUp(self) -> None:
        self.registry = Registry()
        birinapant.collect(self.registry)

    def test_counts_and_references(self) -> None:
        self.assertEqual(len(self.registry.tables["papers"]), 1)
        self.assertEqual(len(self.registry.tables["contexts"]), 26)
        self.assertEqual(len(self.registry.tables["assays"]), 13)
        self.assertEqual(len(self.registry.tables["observations"]), 173)
        self.assertEqual(len(self.registry.tables["extraction_runs"]), 173)
        condition_ids = {row["condition_id"] for row in self.registry.tables["conditions"]}
        self.assertTrue(all(row["condition_id"] in condition_ids for row in self.registry.tables["observations"]))
        context_ids = {row["context_id"] for row in self.registry.tables["contexts"]}
        self.assertTrue(all(row["context_id"] in context_ids for row in self.registry.tables["observations"]))

    def test_ic50_censoring_for_resistant_lines(self) -> None:
        rows = [row for row in self.registry.tables["observations"] if row["observable"] == "viability_IC50"]
        self.assertEqual(len(rows), 25)
        censored = [row for row in rows if row["is_censored"]]
        self.assertEqual(len(censored), 14)
        self.assertTrue(all(row["value"] is None and row["censoring_limit"] == 1000.0 for row in censored))
        uncensored = [row for row in rows if not row["is_censored"]]
        self.assertEqual(len(uncensored), 11)
        contexts = {row["context_id"]: row["cell_line"] for row in self.registry.tables["contexts"]}
        wm9_values = sorted(
            row["value"] for row in uncensored if contexts[row["context_id"]] == "WM9"
        )
        self.assertEqual(wm9_values, [2.4, 2.7])

    def test_xenograft_ciap1_kinetics_includes_qsp_baseline(self) -> None:
        contexts = {row["context_id"]: row["cell_line"] for row in self.registry.tables["contexts"]}
        rows = [
            row for row in self.registry.tables["observations"]
            if row["observable"] == "cIAP1_protein_remaining_pct" and contexts[row["context_id"]] == "451Lu"
        ]
        times = sorted(row["time_value"] for row in rows)
        self.assertEqual(times, [0.0, 3.0, 6.0, 12.0, 24.0])
        baseline = next(row for row in rows if row["time_value"] == 0.0)
        self.assertEqual(baseline["value"], 100.0)
        self.assertIsNotNone(baseline["uncertainty_value"])

    def test_genotype_context_alterations(self) -> None:
        alterations = {
            (row["gene"], row["alteration"]) for row in self.registry.tables["context_alterations"]
        }
        self.assertIn(("BRAF", "BRAFV600E"), alterations)
        self.assertIn(("NRAS", "NRASQ61L"), alterations)


if __name__ == "__main__":
    unittest.main()

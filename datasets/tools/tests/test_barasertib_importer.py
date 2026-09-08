from __future__ import annotations

import sys
import unittest
from pathlib import Path


TOOLS = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(TOOLS))

from importers import barasertib
from registry_common import Registry


class BarasertibImporterTests(unittest.TestCase):
    def setUp(self) -> None:
        self.registry = Registry()
        barasertib.collect(self.registry)

    def test_counts_and_references(self) -> None:
        self.assertEqual(len(self.registry.tables["papers"]), 1)
        self.assertEqual(len(self.registry.tables["contexts"]), 27)
        self.assertEqual(len(self.registry.tables["assays"]), 6)
        self.assertEqual(len(self.registry.tables["observations"]), 45)
        self.assertEqual(len(self.registry.tables["extraction_runs"]), 45)
        condition_ids = {row["condition_id"] for row in self.registry.tables["conditions"]}
        self.assertTrue(all(row["condition_id"] in condition_ids for row in self.registry.tables["observations"]))

    def test_ic50_is_source_censored_not_invented(self) -> None:
        rows = [row for row in self.registry.tables["observations"] if row["observable"] == "viability_IC50"]
        self.assertEqual(len(rows), 9)
        self.assertTrue(all(row["value"] is None for row in rows))
        self.assertTrue(all(row["is_censored"] and row["censoring_limit"] == 50.0 for row in rows))
        self.assertTrue(all(row["time_value"] == 120.0 and row["time_unit"] == "h" for row in rows))

    def test_table2_and_xenograft_values(self) -> None:
        rows = self.registry.tables["observations"]
        h446_24 = sorted(
            row["value"] for row in rows
            if row["time_value"] == 24.0 and row["observable"] in {"cell_cycle_4N_fraction", "cell_cycle_ge8N_fraction"}
        )
        self.assertEqual(h446_24, [10.0, 75.0])
        tumor = {(row["time_value"], row["value"]): row for row in rows if row["observable"] == "tumor_volume"}
        self.assertIn((34.0, 2774.0), tumor)
        self.assertIn((34.0, 232.0), tumor)
        self.assertIn((61.0, 2828.0), tumor)

    def test_ph3_conditions_have_equal_two_drug_doses(self) -> None:
        ph3 = [row for row in self.registry.tables["observations"] if row["observable"] == "phospho_H3_Ser10_status"]
        self.assertEqual(len(ph3), 2)
        steps_by_condition: dict[str, list[dict]] = {}
        for step in self.registry.tables["condition_steps"]:
            steps_by_condition.setdefault(step["condition_id"], []).append(step)
        for row in ph3:
            steps = steps_by_condition[row["condition_id"]]
            self.assertEqual(len(steps), 2)
            self.assertEqual({step["dose_value"] for step in steps}, {25.0} if row["panel"] == "A" else {50.0})

    def test_source_response_classes_are_corrected(self) -> None:
        contexts = {row["context_id"]: row["cell_line"] for row in self.registry.tables["contexts"]}
        classes = {
            contexts[row["context_id"]]: row["observable_raw_label"]
            for row in self.registry.tables["observations"]
            if row["observable"] == "growth_inhibition_class"
        }
        self.assertTrue(classes["H524"].startswith("intermediate"))
        self.assertTrue(classes["H748"].startswith("resistant"))
        self.assertTrue(classes["DMS114"].startswith("intermediate"))


if __name__ == "__main__":
    unittest.main()

from __future__ import annotations

import sys
import unittest
from pathlib import Path


TOOLS = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(TOOLS))

from importers import alisertib
from registry_common import Registry


class AlisertibImporterTests(unittest.TestCase):
    def setUp(self) -> None:
        self.registry = Registry()
        alisertib.collect(self.registry)

    def test_counts_and_references(self) -> None:
        self.assertEqual(len(self.registry.tables["papers"]), 1)
        self.assertEqual(len(self.registry.tables["contexts"]), 5)
        self.assertEqual(len(self.registry.tables["conditions"]), 19)
        self.assertEqual(len(self.registry.tables["assays"]), 12)
        self.assertEqual(len(self.registry.tables["observations"]), 93)
        self.assertEqual(len(self.registry.tables["extraction_runs"]), 93)
        condition_ids = {row["condition_id"] for row in self.registry.tables["conditions"]}
        assay_ids = {row["assay_id"] for row in self.registry.tables["assays"]}
        self.assertTrue(all(row["condition_id"] in condition_ids for row in self.registry.tables["observations"]))
        self.assertTrue(all(row["assay_id"] in assay_ids for row in self.registry.tables["observations"]))

    def test_combination_conditions_retain_both_doses(self) -> None:
        perturbations = {row["perturbation_id"]: row["name"] for row in self.registry.tables["perturbations"]}
        conditions = {row["condition_id"]: row for row in self.registry.tables["conditions"]}
        steps_by_condition: dict[str, list[dict]] = {}
        for step in self.registry.tables["condition_steps"]:
            steps_by_condition.setdefault(step["condition_id"], []).append(step)
        combinations = [row for row in conditions.values() if "+" in row["condition_label"]]
        self.assertEqual(len(combinations), 5)
        for condition in combinations:
            steps = steps_by_condition[condition["condition_id"]]
            self.assertEqual({perturbations[step["perturbation_id"]] for step in steps}, {"MLN8237", "Cisplatin"})
            self.assertTrue(all(step["dose_value"] is not None and step["dose_unit"] for step in steps))

    def test_day21_tumor_endpoints(self) -> None:
        rows = [row for row in self.registry.tables["observations"] if row["observable"] == "tumor_volume"]
        self.assertEqual(len(rows), 8)
        direct = sorted(row["value"] for row in rows if row["extraction_method"] == "DIRECT_SOURCE")
        self.assertEqual(direct, [10.07, 51.47, 76.66, 90.99, 178.84, 264.53])
        self.assertTrue(all(row["time_value"] == 21.0 and row["time_unit"] == "d" for row in rows))
        self.assertTrue(all(row["uncertainty_type"] == "SEM" for row in rows if row["extraction_method"] == "DIRECT_SOURCE"))


if __name__ == "__main__":
    unittest.main()

from __future__ import annotations

import csv
import sys
import unittest
from pathlib import Path


TOOLS = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(TOOLS))

from importers import cilengitide
from registry_common import Registry


class CilengitideImporterTests(unittest.TestCase):
    def setUp(self) -> None:
        self.registry = Registry()
        cilengitide.collect(self.registry)

    def test_counts_and_references(self) -> None:
        self.assertEqual(len(self.registry.tables["papers"]), 1)
        self.assertEqual(len(self.registry.tables["contexts"]), 1)
        self.assertEqual(len(self.registry.tables["conditions"]), 2)
        self.assertEqual(len(self.registry.tables["assays"]), 2)
        self.assertEqual(len(self.registry.tables["observations"]), 73)
        self.assertEqual(len(self.registry.tables["extraction_runs"]), 73)
        condition_ids = {row["condition_id"] for row in self.registry.tables["conditions"]}
        self.assertTrue(all(row["condition_id"] in condition_ids for row in self.registry.tables["observations"]))

    def test_pet_panel_rows_are_preserved_but_not_double_weighted(self) -> None:
        with (cilengitide.DATA / "pet_panel_digitization.csv").open(newline="", encoding="utf-8") as handle:
            self.assertEqual(len(list(csv.DictReader(handle))), 60)
        pet = [row for row in self.registry.tables["observations"] if row["assay_id"] == cilengitide._assay_id("dynamic_fdg_pet")]
        self.assertEqual(len(pet), 30)
        self.assertTrue(all(row["quality_class"] == "SEMI_QUANTITATIVE" for row in pet))
        self.assertTrue(all(row["extraction_method"] == "COMPUTED_FROM_SOURCE_VALUES" for row in pet))

    def test_pet_sample_sizes_and_baseline_median(self) -> None:
        rows = self.registry.tables["observations"]
        treated_id = next(
            row["condition_id"] for row in self.registry.tables["conditions"]
            if row["condition_label"].startswith("Cilengitide")
        )
        vb = next(row for row in rows if row["observable"] == "fractional_blood_volume" and row["time_value"] == 30 and row["condition_id"] == treated_id)
        self.assertAlmostEqual(vb["value"], 0.1025)
        self.assertEqual(vb["replicate_count"], 8)
        day55 = [row for row in rows if row["time_value"] == 55 and row["observable"].startswith("FDG_")]
        self.assertEqual({row["replicate_count"] for row in day55}, {4, 6})

    def test_gene_values_are_direct_table_values(self) -> None:
        rows = self.registry.tables["observations"]
        genes = [row for row in rows if row["table"] == "Table 1"]
        self.assertEqual(len(genes), 43)
        self.assertTrue(all(row["extraction_method"] == "DIRECT_SOURCE" for row in genes))
        rankl = next(row for row in genes if row["observable_raw_label"] == "RANKL")
        self.assertEqual(rankl["value"], -1.28)
        self.assertEqual(rankl["value_unit"], "log2 fold change")


if __name__ == "__main__":
    unittest.main()

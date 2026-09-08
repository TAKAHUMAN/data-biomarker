from __future__ import annotations

import sys
import unittest
from pathlib import Path


TOOLS = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(TOOLS))

from importers import dactolisib_ovarian
from registry_common import Registry


class DactolisibOvarianImporterTests(unittest.TestCase):
    def setUp(self) -> None:
        self.registry = Registry()
        dactolisib_ovarian.collect(self.registry)

    def test_counts_and_references(self) -> None:
        self.assertEqual(len(self.registry.tables["papers"]), 1)
        self.assertEqual(len(self.registry.tables["contexts"]), 6)
        self.assertEqual(len(self.registry.tables["assays"]), 5)
        self.assertEqual(len(self.registry.tables["observations"]), 153)
        self.assertEqual(len(self.registry.tables["extraction_runs"]), 153)
        condition_ids = {row["condition_id"] for row in self.registry.tables["conditions"]}
        self.assertTrue(all(row["condition_id"] in condition_ids for row in self.registry.tables["observations"]))
        context_ids = {row["context_id"] for row in self.registry.tables["contexts"]}
        self.assertTrue(all(row["context_id"] in context_ids for row in self.registry.tables["observations"]))

    def test_no_paper_artifact_row(self) -> None:
        types = {row["artifact_type"] for row in self.registry.tables["source_artifacts"]}
        self.assertNotIn("PAPER", types)

    def test_no_in_vivo_assay_types(self) -> None:
        # This paper has NO animal/tumour model -- guard against any xenograft/tumor
        # assay type ever being introduced for this drug/paper.
        in_vivo_terms = ("xenograft", "tumor", "tumour", "in vivo")
        for row in self.registry.tables["assays"]:
            if row["paper_id"] != "paper_PMID32061787":
                continue
            haystack = " ".join(str(row.get(field) or "") for field in ("assay_type", "assay_name", "sample_type", "measurement_platform", "notes")).lower()
            self.assertFalse(any(term in haystack for term in in_vivo_terms), haystack)

    def test_not_quantifiable_flow_cytometry_excluded(self) -> None:
        # Fig2/Fig3 DOX accumulation/efflux flow-cytometry histograms must never
        # appear as numeric observations.
        for row in self.registry.tables["observations"]:
            self.assertNotIn(row["figure"], ("Figure 2", "Figure 3"))

    def test_ps6_and_parp_have_wide_uncertainty(self) -> None:
        rows = [
            row for row in self.registry.tables["observations"]
            if row["observable"] in ("pS6_over_S6_relative_to_control", "cleaved_PARP_relative_intensity")
        ]
        self.assertGreater(len(rows), 0)
        self.assertTrue(all(row["uncertainty_type"] is not None for row in rows))


if __name__ == "__main__":
    unittest.main()

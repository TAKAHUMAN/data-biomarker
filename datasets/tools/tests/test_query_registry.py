from __future__ import annotations

import hashlib
import json
import sys
import tempfile
import unittest
from pathlib import Path

import pyarrow.parquet as pq

TOOLS = Path(__file__).resolve().parents[1]
ROOT = TOOLS.parents[1]
sys.path.insert(0, str(TOOLS))

from create_cohort_manifest import create_cohort_manifest, export_cohort, registry_semantic_digest, resolve_cohort_manifest, write_cohort_manifest
from query_registry import query_observations


def _registry_hashes() -> dict[str, str]:
    return {path.name: hashlib.sha256(path.read_bytes()).hexdigest() for path in sorted((ROOT / "datasets" / "registry").glob("*.parquet"))}


class QueryRegistryTests(unittest.TestCase):
    def setUp(self) -> None:
        self.registry_before = _registry_hashes()
        self.digest_before = registry_semantic_digest()
        self.canonical_before = hashlib.sha256((ROOT / "working_model" / "generated" / "working_signal_model.json").read_bytes()).hexdigest()

    def tearDown(self) -> None:
        self.assertEqual(_registry_hashes(), self.registry_before)
        self.assertEqual(registry_semantic_digest(), self.digest_before)
        self.assertEqual(hashlib.sha256((ROOT / "working_model" / "generated" / "working_signal_model.json").read_bytes()).hexdigest(), self.canonical_before)

    def test_foretinib_mv4_11_two_hour_phosphosignals(self) -> None:
        rows = query_observations(paper_id="paper_foretinib_flt3_itd_workbook", cell_line="MV4-11", time=2.0, time_unit="h", observable=("pFLT3", "pSTAT5", "pAKT", "pERK"), has_numeric_value=True)
        self.assertEqual(len(rows), 20)
        self.assertEqual(len({row["observation"]["observation_id"] for row in rows}), 20)
        def dose(row: dict) -> float:
            return row["condition"]["steps"][0]["dose_value"]
        values = {name: [row["observation"]["value"] for row in sorted((row for row in rows if row["observation"]["observable"] == name), key=dose)] for name in ("pFLT3", "pSTAT5", "pAKT", "pERK")}
        self.assertEqual(values["pFLT3"], [1.0, 0.25, 0.1, 0.02, 0.0])
        self.assertEqual(values["pSTAT5"], [1.0, 0.05, 0.0, 0.0, 0.0])
        self.assertEqual(values["pAKT"], [1.0, 0.3, 0.1, 0.02, 0.0])
        self.assertEqual(values["pERK"], [1.0, 0.7, 0.35, 0.1, 0.02])

    def test_luminespib_existing_hela_pakt_cohort(self) -> None:
        rows = query_observations(paper_id="paper_luminespib_hsp90_workbook", cell_line="HeLa", time=24.0, time_unit="h", observable="pAKT", has_numeric_value=True)
        rows = sorted(rows, key=lambda row: row["condition"]["steps"][0]["dose_value"])
        self.assertEqual([row["observation"]["value"] for row in rows], [1.0, 0.85, 0.2, 0.05])
        self.assertTrue(all(row["assay"]["assay_type"] == "Western blot" for row in rows))

    def test_pemigatinib_kg1a_perk_series_and_mapping_opt_in(self) -> None:
        rows = query_observations(pmid="32315352", cell_line="KG1a", time=2.0, time_unit="h", observable="pERK", extraction_method="BLOT_DENSITOMETRY", has_numeric_value=True)
        self.assertEqual([row["observation"]["observation_id"] for row in rows], [f"obs_PMID32315352_P32315352_KG1A_PERK_{index:02d}" for index in range(1, 9)])
        self.assertEqual(len(rows), 8)
        mapped = query_observations(observation_ids=rows[0]["observation"]["observation_id"], include_model_mappings=True)
        self.assertIn("model_mappings", mapped[0])
        self.assertTrue(mapped[0]["model_mappings"])

    def test_kato_ic50_and_rt4_qualitative_are_explicit(self) -> None:
        kato = query_observations(pmid="32315352", cell_line="KATO III", observable="pFGFR2 inhibition IC50", assay_type="phospho-FGFR2 ELISA", has_numeric_value=True)
        self.assertEqual([row["observation"]["observation_id"] for row in kato], ["obs_PMID32315352_P32315352_005", "obs_PMID32315352_P32315352_006"])
        self.assertEqual([row["observation"]["value"] for row in kato], [3.0, 10.9])
        rt4 = query_observations(pmid="32315352", cell_line="RT-4", observable="pFRS2", quality_class="QUALITATIVE_VALIDATION")
        self.assertEqual(len(rt4), 7)
        self.assertTrue(all(row["observation"]["value"] is None for row in rt4))
        self.assertTrue(all(row["observation"]["quality_class"] == "QUALITATIVE_VALIDATION" for row in rt4))

    def test_itd_shorthand_and_frozen_cohort_export(self) -> None:
        itd = query_observations(gene="FLT3", alteration_type="ITD", observable="pFLT3", time=2.0, time_unit="h")
        self.assertEqual(len(itd), 15)
        an3ca = query_observations(pmid="32315352", cell_line="AN3CA")
        self.assertEqual(len(an3ca), 1)
        self.assertEqual(len(an3ca[0]["context"]["alterations"]), 2)
        self.assertEqual(len({row["observation"]["observation_id"] for row in query_observations()}), len(query_observations()))
        manifest = create_cohort_manifest("test_kg1a_perk", "Focused KG1a 2 h pERK cohort", {"pmid": "32315352", "cell_line": "KG1a", "time": 2.0, "time_unit": "h", "observable": "pERK", "extraction_method": "BLOT_DENSITOMETRY", "has_numeric_value": True})
        self.assertEqual(manifest["observation_count"], 8)
        self.assertEqual(manifest["observation_ids"], sorted(manifest["observation_ids"]))
        self.assertEqual([row["observation"]["observation_id"] for row in resolve_cohort_manifest(manifest)], manifest["observation_ids"])
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory)
            manifest_path = write_cohort_manifest(manifest, target / "cohort.json")
            self.assertEqual(json.loads(manifest_path.read_text(encoding="utf-8"))["observation_ids"], manifest["observation_ids"])
            for format_name in ("csv", "parquet"):
                data, sidecar = export_cohort(manifest, format_name, target)
                self.assertTrue(data.is_file() and sidecar.is_file())
                self.assertEqual(json.loads(sidecar.read_text(encoding="utf-8"))["observation_ids"], manifest["observation_ids"])
                if format_name == "parquet":
                    self.assertEqual(pq.read_table(data).num_rows, 8)


if __name__ == "__main__":
    unittest.main()

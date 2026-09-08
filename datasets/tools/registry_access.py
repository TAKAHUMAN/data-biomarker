"""Read-only access helpers for experiment consumers of registry observations."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pyarrow.parquet as pq

ROOT = Path(__file__).resolve().parents[2]
REGISTRY = ROOT / "datasets" / "registry"


def table(name: str) -> list[dict[str, Any]]:
    path = REGISTRY / f"{name}.parquet"
    if not path.exists():
        raise FileNotFoundError(f"Registry table missing: {path}. Run datasets/tools/build_registry.py first.")
    return pq.read_table(path).to_pylist()


def observations(*, paper_id: str | None = None, observation_ids: set[str] | None = None) -> list[dict[str, Any]]:
    rows = table("observations")
    if paper_id is not None:
        rows = [row for row in rows if row["paper_id"] == paper_id]
    if observation_ids is not None:
        rows = [row for row in rows if row["observation_id"] in observation_ids]
    return rows


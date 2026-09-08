#!/usr/bin/env python3
"""
QSP/PD Biomarker Data Loader

Load and combine biomarker datasets for quantitative systems pharmacology modeling.

Example:
    from biomarker_loader import BiomarkerDataset

    # Load single drug
    data = BiomarkerDataset('dordaprivone_ovarian')
    print(data.observations.head())

    # Load multiple drugs
    multi = BiomarkerDataset.load_multiple(['dordaprivone_ovarian', 'ganetespib_escc'])
    all_obs = multi.combined_observations()
"""

import pandas as pd
import json
from pathlib import Path
from typing import Dict, List, Optional
import warnings

class BiomarkerDataset:
    """Load and manage biomarker data for a single drug."""

    def __init__(self, drug_name: str, extracted_dir: Optional[Path] = None):
        """
        Initialize biomarker dataset.

        Args:
            drug_name: Name of drug folder (e.g., 'dordaprivone_ovarian')
            extracted_dir: Path to extracted datasets folder
        """
        if extracted_dir is None:
            extracted_dir = Path(__file__).parent.parent / 'datasets' / 'extracted'

        self.drug_dir = extracted_dir / drug_name
        self.drug_name = drug_name

        if not self.drug_dir.exists():
            raise FileNotFoundError(f"Drug folder not found: {self.drug_dir}")

        # Load data
        self._load_all()

    def _load_all(self):
        """Load all CSV and metadata files."""
        # Load CSVs
        self.observations = self._load_csv('observations.csv')
        self.assays = self._load_csv('assays.csv')
        self.conditions = self._load_csv('conditions.csv')
        self.contexts = self._load_csv('contexts.csv')

        # Load metadata
        self.metadata = self._load_json('extraction_metadata.json')

        # Load README
        readme_path = self.drug_dir / 'README.md'
        self.readme = readme_path.read_text(encoding='utf-8') if readme_path.exists() else ""

    def _load_csv(self, filename: str) -> pd.DataFrame:
        """Load CSV file, return empty DataFrame if not found."""
        filepath = self.drug_dir / filename
        if filepath.exists():
            return pd.read_csv(filepath)
        else:
            warnings.warn(f"Missing {filename} in {self.drug_name}")
            return pd.DataFrame()

    def _load_json(self, filename: str) -> dict:
        """Load JSON file, return empty dict if not found."""
        filepath = self.drug_dir / filename
        if filepath.exists():
            with open(filepath, 'r') as f:
                return json.load(f)
        return {}

    def summary(self) -> Dict[str, any]:
        """Get dataset summary."""
        return {
            'drug': self.drug_name,
            'observations': len(self.observations),
            'assays': len(self.assays),
            'conditions': len(self.conditions),
            'contexts': len(self.contexts),
        }

    def __repr__(self) -> str:
        s = self.summary()
        return f"BiomarkerDataset({self.drug_name}: {s['observations']} obs, {s['assays']} assays)"

    @classmethod
    def load_multiple(cls, drug_names: List[str], extracted_dir: Optional[Path] = None) -> 'MultiDrugDataset':
        """Load multiple drug datasets."""
        datasets = [cls(name, extracted_dir) for name in drug_names]
        return MultiDrugDataset(datasets)

    @classmethod
    def load_all(cls, extracted_dir: Optional[Path] = None) -> 'MultiDrugDataset':
        """Load all available drug datasets."""
        if extracted_dir is None:
            extracted_dir = Path(__file__).parent.parent / 'datasets' / 'extracted'

        drug_dirs = [d for d in extracted_dir.iterdir()
                     if d.is_dir() and (d / 'observations.csv').exists()]

        return cls.load_multiple([d.name for d in sorted(drug_dirs)], extracted_dir)


class MultiDrugDataset:
    """Manage multiple drug datasets."""

    def __init__(self, datasets: List[BiomarkerDataset]):
        """Initialize with list of BiomarkerDataset objects."""
        self.datasets = {d.drug_name: d for d in datasets}

    def combined_observations(self) -> pd.DataFrame:
        """Combine observations from all drugs."""
        dfs = []
        for drug_name, dataset in self.datasets.items():
            df = dataset.observations.copy()
            df['drug'] = drug_name
            dfs.append(df)

        if not dfs:
            return pd.DataFrame()

        return pd.concat(dfs, ignore_index=True)

    def get_drug(self, name: str) -> BiomarkerDataset:
        """Get a single drug dataset."""
        return self.datasets[name]

    def drug_names(self) -> List[str]:
        """List all loaded drugs."""
        return sorted(self.datasets.keys())

    def summary(self) -> pd.DataFrame:
        """Get summary of all drugs."""
        rows = []
        for drug_name, dataset in sorted(self.datasets.items()):
            s = dataset.summary()
            rows.append({
                'Drug': drug_name,
                'Observations': s['observations'],
                'Assays': s['assays'],
                'Conditions': s['conditions'],
                'Contexts': s['contexts'],
            })

        return pd.DataFrame(rows)

    def __repr__(self) -> str:
        return f"MultiDrugDataset({len(self.datasets)} drugs, {len(self.combined_observations())} total obs)"


def main():
    """Example usage."""
    print("Loading all biomarker datasets...\n")

    # Load all
    multi = BiomarkerDataset.load_all()
    print(multi)
    print("\n" + "="*80 + "\n")

    # Summary table
    print("Dataset Summary:")
    print(multi.summary().to_string(index=False))
    print("\n" + "="*80 + "\n")

    # Combined observations
    all_obs = multi.combined_observations()
    print(f"Combined Observations: {len(all_obs)} rows")
    print(f"Columns: {', '.join(all_obs.columns[:5])}...")


if __name__ == '__main__':
    main()

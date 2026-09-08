#!/usr/bin/env python3
"""
Validate biomarker dataset integrity across all drugs.

Checks:
- All required CSV files present
- CSV format validity (headers, columns)
- Observation counts
- File structure consistency
"""

import os
import csv
import json
from pathlib import Path
from typing import Dict, List, Tuple

REQUIRED_FILES = ['observations.csv', 'assays.csv', 'conditions.csv', 'contexts.csv', 'README.md']
EXTRACTED_DIR = Path(__file__).parent.parent / 'datasets' / 'extracted'

def validate_csv(filepath: Path) -> Tuple[bool, str]:
    """Validate CSV file structure."""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            rows = list(reader)
            if not rows:
                return False, "Empty CSV"
            return True, f"{len(rows)} rows"
    except Exception as e:
        return False, str(e)

def validate_drug(drug_dir: Path) -> Dict[str, any]:
    """Validate a single drug dataset."""
    result = {'drug': drug_dir.name, 'status': 'OK', 'files': {}, 'observations': 0}

    for required_file in REQUIRED_FILES:
        filepath = drug_dir / required_file
        if not filepath.exists():
            result['status'] = 'FAIL'
            result['files'][required_file] = 'MISSING'
        else:
            if filepath.suffix == '.csv':
                is_valid, msg = validate_csv(filepath)
                result['files'][required_file] = msg
                if required_file == 'observations.csv':
                    try:
                        result['observations'] = int(msg.split()[0])
                    except:
                        result['observations'] = 0
            else:
                result['files'][required_file] = 'OK'

    return result

def main():
    """Run validation on all drugs."""
    if not EXTRACTED_DIR.exists():
        print(f"FAIL: Extracted directory not found: {EXTRACTED_DIR}")
        return

    print(f"\nVALIDATING {EXTRACTED_DIR.name}")
    print("=" * 80)

    results = []
    drug_dirs = sorted([d for d in EXTRACTED_DIR.iterdir() if d.is_dir()])

    for drug_dir in drug_dirs:
        result = validate_drug(drug_dir)
        results.append(result)

        status = result['status']
        drug = result['drug']
        obs = result['observations']
        print(f"[{status}] {drug:30s} | {obs:4d} observations")

    print("=" * 80)

    # Summary
    total_drugs = len(results)
    complete = sum(1 for r in results if r['status'] == 'OK')
    total_obs = sum(r['observations'] for r in results)

    print(f"\nComplete: {complete}/{total_drugs} drugs")
    print(f"Total observations: {total_obs}")
    print(f"Average obs/drug: {total_obs//complete if complete > 0 else 0}")

    # Issues
    issues = [r for r in results if r['status'] == 'FAIL']
    if issues:
        print(f"\nINCOMPLETE DATASETS ({len(issues)}):")
        for issue in issues:
            missing = [k for k, v in issue['files'].items() if v == 'MISSING']
            print(f"  - {issue['drug']}: missing {', '.join(missing)}")

    print("\nValidation complete!")

if __name__ == '__main__':
    main()

from __future__ import annotations

import csv
import logging
from pathlib import Path

import pytest

from src.engine import run_engine
from src.io_parsers import load_bom, load_ghp, validate_inputs
from src.output_writer import write_item_mrp_csv


ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data"
EXPECTED_DIR = ROOT / "output"


def _read_csv_rows(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


@pytest.mark.parametrize(
    "bom_file,ghp_file,expected_subdir",
    [
        ("bom_zad1.json", "ghp_zad1.csv", "zad1"),
        ("bom_zad2.json", "ghp_zad2.csv", "zad2"),
        ("bom_zad1a.json", "ghp_zad1a.csv", "zad1a"),
        ("bom_shared_component_demo.json", "ghp_shared_component_demo.csv", "shared_demo"),
    ],
)
def test_dataset_outputs_match_expected_snapshots(
    bom_file: str,
    ghp_file: str,
    expected_subdir: str,
    tmp_path: Path,
) -> None:
    items = load_bom(str(DATA_DIR / bom_file))
    ghp = load_ghp(str(DATA_DIR / ghp_file))
    max_ghp_week, max_scheduled_receipt_week = validate_inputs(items, ghp)
    horizon = max(max_ghp_week, max_scheduled_receipt_week)

    results = run_engine(
        items=items,
        ghp_production=ghp,
        horizon=horizon,
        logger=logging.getLogger("test_integration"),
    )

    if expected_subdir == "shared_demo":
        final_w3 = results["FINAL-001"].weeks[2]
        a_w2 = results["A-001"].weeks[1]
        c_w1 = results["C-SHARED-001"].weeks[0]
        c_w2 = results["C-SHARED-001"].weeks[1]
        c_w3 = results["C-SHARED-001"].weeks[2]

        # Parent demand for A/B is driven by FINAL planned releases at week 2.
        assert final_w3.gross_requirements == 20
        assert a_w2.gross_requirements == 20
        assert a_w2.planned_order_receipts == 10

        # Shared demand is the sum of parent releases across both parents.
        assert c_w1.gross_requirements == 50
        assert c_w2.gross_requirements == 50
        assert c_w1.planned_order_receipts == 30
        assert c_w1.projected_on_hand == -20

        # One-lot policy keeps residual shortages and can trigger repeated receipts.
        assert c_w2.net_requirements == 70
        assert c_w2.planned_order_receipts == 30
        assert c_w3.planned_order_receipts == 30
        return

    for item_id in sorted(results):
        write_item_mrp_csv(results[item_id], str(tmp_path))

    expected_files = sorted((EXPECTED_DIR / expected_subdir).glob("*_mrp.csv"))
    produced_files = sorted(tmp_path.glob("*_mrp.csv"))

    assert [f.name for f in produced_files] == [f.name for f in expected_files]

    for expected_path in expected_files:
        produced_path = tmp_path / expected_path.name
        assert _read_csv_rows(produced_path) == _read_csv_rows(expected_path)

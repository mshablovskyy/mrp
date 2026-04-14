from __future__ import annotations

import csv
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ENGINE_SCRIPT = ROOT / "mrp_engine.py"
DATA_DIR = ROOT / "data"


def _run_cli(*args: str, cwd: Path = ROOT) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(ENGINE_SCRIPT), *args],
        cwd=str(cwd),
        text=True,
        capture_output=True,
        check=False,
    )


def test_cli_runs_successfully_and_creates_outputs(tmp_path: Path) -> None:
    result = _run_cli(
        "--bom",
        str(DATA_DIR / "bom_zad1.json"),
        "--ghp",
        str(DATA_DIR / "ghp_zad1.csv"),
        "--out",
        str(tmp_path),
    )

    assert result.returncode == 0, result.stdout + result.stderr
    assert any(tmp_path.glob("*_mrp.csv"))


def test_cli_requires_all_arguments() -> None:
    result = _run_cli()
    assert result.returncode != 0


def test_cli_returns_nonzero_on_invalid_ghp_header(tmp_path: Path) -> None:
    bad_ghp = tmp_path / "bad_ghp.csv"
    bad_ghp.write_text("w,d,p\n1,0,1\n", encoding="utf-8")

    result = _run_cli(
        "--bom",
        str(DATA_DIR / "bom_zad1.json"),
        "--ghp",
        str(bad_ghp),
        "--out",
        str(tmp_path / "out"),
    )

    assert result.returncode == 1
    assert "Fatal error" in (result.stdout + result.stderr)


def test_cli_overwrites_existing_output_files(tmp_path: Path) -> None:
    first_run = _run_cli(
        "--bom",
        str(DATA_DIR / "bom_zad1.json"),
        "--ghp",
        str(DATA_DIR / "ghp_zad1.csv"),
        "--out",
        str(tmp_path),
    )
    assert first_run.returncode == 0

    one_output = next(tmp_path.glob("*_mrp.csv"))
    one_output.write_text("corrupted\n", encoding="utf-8")

    second_run = _run_cli(
        "--bom",
        str(DATA_DIR / "bom_zad1.json"),
        "--ghp",
        str(DATA_DIR / "ghp_zad1.csv"),
        "--out",
        str(tmp_path),
    )
    assert second_run.returncode == 0

    with one_output.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.reader(handle)
        header = next(reader)

    assert header == [
        "week",
        "gross_requirements",
        "scheduled_receipts",
        "projected_on_hand",
        "net_requirements",
        "planned_order_receipts",
        "planned_order_releases",
    ]

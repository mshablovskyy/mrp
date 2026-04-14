from __future__ import annotations

import csv
from pathlib import Path

from .models import ItemMRPResult


OUTPUT_HEADERS = [
    "week",
    "gross_requirements",
    "scheduled_receipts",
    "projected_on_hand",
    "net_requirements",
    "planned_order_receipts",
    "planned_order_releases",
]


def write_item_mrp_csv(result: ItemMRPResult, out_dir: str) -> Path:
    out_path = Path(out_dir)
    out_path.mkdir(parents=True, exist_ok=True)

    file_path = out_path / f"{result.item_id}_mrp.csv"
    with file_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=OUTPUT_HEADERS)
        writer.writeheader()

        for week in result.weeks:
            writer.writerow(
                {
                    "week": week.week,
                    "gross_requirements": week.gross_requirements,
                    "scheduled_receipts": week.scheduled_receipts,
                    "projected_on_hand": week.projected_on_hand,
                    "net_requirements": week.net_requirements,
                    "planned_order_receipts": week.planned_order_receipts,
                    "planned_order_releases": week.planned_order_releases,
                }
            )

    return file_path

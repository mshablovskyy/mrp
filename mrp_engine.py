from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

from src.engine import run_engine
from src.io_parsers import load_bom, load_ghp, validate_inputs
from src.output_writer import write_item_mrp_csv


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Core MRP Engine CLI")
    parser.add_argument("--bom", required=True, help="Path to bom_items.json")
    parser.add_argument("--ghp", required=True, help="Path to ghp.csv")
    parser.add_argument("--out", required=True, help="Path to output directory")
    return parser


def main() -> int:
    logging.basicConfig(
        level=logging.INFO,
        format="%(levelname)s:%(name)s:%(message)s",
    )
    logger = logging.getLogger("mrp_engine")

    parser = build_parser()
    args = parser.parse_args()

    try:
        items = load_bom(args.bom)
        ghp_production = load_ghp(args.ghp)
        max_ghp_week, max_scheduled_receipt_week = validate_inputs(items, ghp_production)

        horizon = max(max_ghp_week, max_scheduled_receipt_week)

        for item in items:
            for week in item.scheduled_receipts:
                if week > max_ghp_week:
                    logger.warning(
                        "Scheduled receipt outside GHP range: item_id=%s week=%s quantity=%s",
                        item.id,
                        week,
                        item.scheduled_receipts[week],
                    )

        results = run_engine(
            items=items,
            ghp_production=ghp_production,
            horizon=horizon,
            logger=logger,
        )

        out_path = Path(args.out)
        if out_path.exists():
            for f in out_path.glob("*_mrp.csv"):
                f.unlink()

        for item_id in sorted(results):
            output_file = write_item_mrp_csv(results[item_id], args.out)
            logger.info("Wrote output: %s", output_file)

        return 0
    except (FileNotFoundError, ValueError) as exc:
        logger.error("Fatal error: %s", exc)
        return 1
    except Exception:
        logger.exception("Fatal unexpected error")
        return 1


if __name__ == "__main__":
    sys.exit(main())

from __future__ import annotations

import logging
from collections import defaultdict
from typing import Dict, List

from .calculator import calculate_item_mrp
from .models import Item, ItemMRPResult


def run_engine(
    items: List[Item],
    ghp_production: Dict[int, int],
    horizon: int,
    logger: logging.Logger,
) -> Dict[str, ItemMRPResult]:
    items_by_level = defaultdict(list)
    for item in items:
        items_by_level[item.bom_level].append(item)

    max_level = max(items_by_level)
    results: Dict[str, ItemMRPResult] = {}
    release_lookup: Dict[str, Dict[int, int]] = {}

    for level in range(0, max_level + 1):
        for item in items_by_level.get(level, []):
            if level > 0:
                for parent in item.parents:
                    if parent.parent_id not in results:
                        raise ValueError(
                            f"Parent '{parent.parent_id}' for item '{item.id}' is not calculated yet. "
                            "Check BOM levels and parent relationships."
                        )

            item_result = calculate_item_mrp(
                item=item,
                parent_release_lookup=release_lookup,
                ghp_production=ghp_production,
                horizon=horizon,
                logger=logger,
            )

            results[item.id] = item_result
            release_lookup[item.id] = {
                week.week: week.planned_order_releases for week in item_result.weeks
            }

    return results

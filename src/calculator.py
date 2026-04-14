from __future__ import annotations

import logging
from collections import defaultdict
from typing import Dict

from .models import Item, ItemMRPResult, MRPWeek


def calculate_item_mrp(
    item: Item,
    parent_release_lookup: Dict[str, Dict[int, int]],
    ghp_production: Dict[int, int],
    horizon: int,
    logger: logging.Logger,
) -> ItemMRPResult:
    """Calculate a full per-week MRP table for a single item.

    Level 0 is intentionally treated as MPS-driven: GHP production is taken as
    planned order receipts and shifted by lead time into planned order releases.
    Lower BOM levels are shortage-driven and follow the one-lot-per-shortage rule.
    """
    gross_requirements: Dict[int, int] = {}
    scheduled_receipts: Dict[int, int] = {}
    projected_on_hand: Dict[int, int] = {0: item.on_hand}
    net_requirements: Dict[int, int] = {}
    planned_order_receipts: Dict[int, int] = {}
    planned_order_releases_all = defaultdict(int)

    for week in range(1, horizon + 1):
        if item.bom_level == 0:
            gross = ghp_production.get(week, 0)
            scheduled = item.scheduled_receipts.get(week, 0)

            # Final product follows MPS directly: planned receipts come from GHP production.
            receipt = ghp_production.get(week, 0)
            net = 0
            projected = projected_on_hand[week - 1] + scheduled + receipt - gross

            release_week = week - item.lead_time
            if receipt > 0:
                planned_order_releases_all[release_week] += receipt
                if release_week < 1:
                    logger.warning(
                        "Negative release week: item_id=%s receipt_week=%s release_week=%s quantity=%s",
                        item.id,
                        week,
                        release_week,
                        receipt,
                    )

            gross_requirements[week] = gross
            scheduled_receipts[week] = scheduled
            projected_on_hand[week] = projected
            net_requirements[week] = net
            planned_order_receipts[week] = receipt
            continue
        else:
            gross = 0
            for parent in item.parents:
                parent_release = parent_release_lookup.get(parent.parent_id, {}).get(week, 0)
                gross += parent_release * parent.quantity_required

        scheduled = item.scheduled_receipts.get(week, 0)
        preliminary_on_hand = projected_on_hand[week - 1] + scheduled - gross

        if preliminary_on_hand < 0:
            net = abs(preliminary_on_hand)
            receipt = item.lot_size
            projected = preliminary_on_hand + receipt
        else:
            net = 0
            receipt = 0
            projected = preliminary_on_hand

        release_week = week - item.lead_time
        if receipt > 0:
            planned_order_releases_all[release_week] += receipt
            if release_week < 1:
                logger.warning(
                    "Negative release week: item_id=%s receipt_week=%s release_week=%s quantity=%s",
                    item.id,
                    week,
                    release_week,
                    receipt,
                )

        gross_requirements[week] = gross
        scheduled_receipts[week] = scheduled
        projected_on_hand[week] = projected
        net_requirements[week] = net
        planned_order_receipts[week] = receipt

    result_weeks = []
    for week in range(1, horizon + 1):
        result_weeks.append(
            MRPWeek(
                week=week,
                gross_requirements=gross_requirements[week],
                scheduled_receipts=scheduled_receipts[week],
                projected_on_hand=projected_on_hand[week],
                net_requirements=net_requirements[week],
                planned_order_receipts=planned_order_receipts[week],
                planned_order_releases=max(planned_order_releases_all.get(week, 0), 0),
            )
        )

    return ItemMRPResult(item_id=item.id, weeks=result_weeks)

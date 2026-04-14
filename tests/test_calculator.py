from __future__ import annotations

import logging

from src.calculator import calculate_item_mrp
from src.models import Item, ParentLink


def _make_item(
    *,
    item_id: str = "CHILD",
    bom_level: int = 1,
    lead_time: int = 0,
    lot_size: int = 10,
    on_hand: int = 0,
) -> Item:
    return Item(
        id=item_id,
        name=item_id,
        bom_level=bom_level,
        lead_time=lead_time,
        lot_size=lot_size,
        on_hand=on_hand,
        scheduled_receipts={},
        parents=[ParentLink(parent_id="PARENT", quantity_required=1)] if bom_level > 0 else [],
    )


def test_one_item_no_shortage() -> None:
    item = _make_item(on_hand=10, lot_size=40, lead_time=0)

    result = calculate_item_mrp(
        item=item,
        parent_release_lookup={"PARENT": {1: 5}},
        ghp_production={},
        horizon=1,
        logger=logging.getLogger("test_calculator"),
    )

    week = result.weeks[0]
    assert week.gross_requirements == 5
    assert week.net_requirements == 0
    assert week.planned_order_receipts == 0
    assert week.projected_on_hand == 5
    assert week.planned_order_releases == 0


def test_one_item_shortage_creates_single_lot_receipt() -> None:
    item = _make_item(on_hand=2, lot_size=7, lead_time=0)

    result = calculate_item_mrp(
        item=item,
        parent_release_lookup={"PARENT": {1: 10}},
        ghp_production={},
        horizon=1,
        logger=logging.getLogger("test_calculator"),
    )

    week = result.weeks[0]
    assert week.gross_requirements == 10
    assert week.net_requirements == 8
    assert week.planned_order_receipts == 7
    assert week.projected_on_hand == -1
    assert week.planned_order_releases == 7


def test_shortage_larger_than_lot_size_keeps_negative_projected_on_hand() -> None:
    item = _make_item(on_hand=1, lot_size=5, lead_time=0)

    result = calculate_item_mrp(
        item=item,
        parent_release_lookup={"PARENT": {1: 20}},
        ghp_production={},
        horizon=1,
        logger=logging.getLogger("test_calculator"),
    )

    week = result.weeks[0]
    assert week.net_requirements == 19
    assert week.planned_order_receipts == 5
    assert week.projected_on_hand == -14


def test_lead_time_pushes_release_before_week_one_logs_warning(caplog) -> None:
    item = _make_item(on_hand=0, lot_size=10, lead_time=2)
    logger_name = "test_calculator_warning"

    with caplog.at_level(logging.WARNING, logger=logger_name):
        result = calculate_item_mrp(
            item=item,
            parent_release_lookup={"PARENT": {1: 9}},
            ghp_production={},
            horizon=1,
            logger=logging.getLogger(logger_name),
        )

    week = result.weeks[0]
    assert week.planned_order_receipts == 10
    assert week.planned_order_releases == 0
    assert "Negative release week" in caplog.text

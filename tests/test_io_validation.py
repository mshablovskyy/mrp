from __future__ import annotations

import pytest

from src.io_parsers import validate_inputs
from src.models import Item, ParentLink


def _item(
    *,
    item_id: str,
    level: int,
    parents: list[ParentLink] | None = None,
) -> Item:
    return Item(
        id=item_id,
        name=item_id,
        bom_level=level,
        lead_time=1,
        lot_size=1,
        on_hand=0,
        scheduled_receipts={},
        parents=parents or [],
    )


def test_validate_requires_exactly_one_level_zero_item() -> None:
    items = [_item(item_id="A", level=0), _item(item_id="B", level=0)]
    with pytest.raises(ValueError, match="Exactly one item with bom_level == 0"):
        validate_inputs(items, {1: 1})


def test_validate_rejects_non_root_without_parent() -> None:
    items = [_item(item_id="ROOT", level=0), _item(item_id="C1", level=1)]
    with pytest.raises(ValueError, match="must define at least one parent"):
        validate_inputs(items, {1: 1})


def test_validate_rejects_missing_parent_reference() -> None:
    items = [
        _item(item_id="ROOT", level=0),
        _item(
            item_id="C1",
            level=1,
            parents=[ParentLink(parent_id="MISSING", quantity_required=1)],
        ),
    ]
    with pytest.raises(ValueError, match="non-existing parent_id"):
        validate_inputs(items, {1: 1})


def test_validate_rejects_invalid_parent_level_relationship() -> None:
    items = [
        _item(item_id="ROOT", level=0),
        _item(
            item_id="C1",
            level=1,
            parents=[ParentLink(parent_id="C2", quantity_required=1)],
        ),
        _item(
            item_id="C2",
            level=2,
            parents=[ParentLink(parent_id="ROOT", quantity_required=1)],
        ),
    ]

    with pytest.raises(ValueError, match="Invalid BOM levels"):
        validate_inputs(items, {1: 1})

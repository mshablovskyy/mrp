from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Dict, List, Tuple

from .models import Item, ParentLink


def _require_int(value: object, field_name: str, *, min_value: int | None = None) -> int:
    if not isinstance(value, int):
        raise ValueError(f"Field '{field_name}' must be an integer.")
    if min_value is not None and value < min_value:
        raise ValueError(f"Field '{field_name}' must be >= {min_value}.")
    return value


def load_bom(path: str) -> List[Item]:
    bom_path = Path(path)
    if not bom_path.exists():
        raise FileNotFoundError(f"BOM file not found: {path}")

    with bom_path.open("r", encoding="utf-8") as handle:
        payload = json.load(handle)

    if not isinstance(payload, dict) or "items" not in payload:
        raise ValueError("BOM JSON must be an object with an 'items' array.")
    if not isinstance(payload["items"], list):
        raise ValueError("BOM field 'items' must be a list.")

    items: List[Item] = []
    for idx, raw_item in enumerate(payload["items"], start=1):
        if not isinstance(raw_item, dict):
            raise ValueError(f"BOM item #{idx} must be an object.")

        item_id = raw_item.get("id")
        name = raw_item.get("name")
        bom_level = _require_int(raw_item.get("bom_level"), f"bom_level for item #{idx}", min_value=0)
        lead_time = _require_int(raw_item.get("lead_time"), f"lead_time for item #{idx}", min_value=0)
        lot_size = _require_int(raw_item.get("lot_size"), f"lot_size for item #{idx}", min_value=1)
        on_hand = _require_int(raw_item.get("on_hand"), f"on_hand for item #{idx}", min_value=0)

        if not isinstance(item_id, str) or not item_id.strip():
            raise ValueError("Field 'id' must be a non-empty string.")
        if not isinstance(name, str) or not name.strip():
            raise ValueError(f"Item '{item_id}': field 'name' must be a non-empty string.")

        scheduled_raw = raw_item.get("scheduled_receipts", {})
        if not isinstance(scheduled_raw, dict):
            raise ValueError(f"Item '{item_id}': 'scheduled_receipts' must be an object.")

        scheduled_receipts: Dict[int, int] = {}
        for week_str, qty in scheduled_raw.items():
            try:
                week = int(week_str)
            except (TypeError, ValueError) as exc:
                raise ValueError(
                    f"Item '{item_id}': scheduled receipt week key '{week_str}' is not a valid integer."
                ) from exc
            if week < 1:
                raise ValueError(f"Item '{item_id}': scheduled receipt week must be >= 1.")
            scheduled_receipts[week] = _require_int(
                qty,
                f"scheduled_receipts[{week}]",
                min_value=0,
            )

        parent_links_raw = raw_item.get("parents", [])
        if not isinstance(parent_links_raw, list):
            raise ValueError(f"Item '{item_id}': 'parents' must be a list.")

        parent_links: List[ParentLink] = []
        for parent in parent_links_raw:
            if not isinstance(parent, dict):
                raise ValueError(f"Item '{item_id}': each parent link must be an object.")
            parent_id = parent.get("parent_id")
            quantity_required = _require_int(
                parent.get("quantity_required"),
                f"quantity_required for item '{item_id}'",
                min_value=1,
            )
            if not isinstance(parent_id, str) or not parent_id.strip():
                raise ValueError(f"Item '{item_id}': parent_id must be a non-empty string.")
            parent_links.append(ParentLink(parent_id=parent_id, quantity_required=quantity_required))

        items.append(
            Item(
                id=item_id,
                name=name,
                bom_level=bom_level,
                lead_time=lead_time,
                lot_size=lot_size,
                on_hand=on_hand,
                scheduled_receipts=scheduled_receipts,
                parents=parent_links,
            )
        )

    return items


def load_ghp(path: str) -> Dict[int, int]:
    ghp_path = Path(path)
    if not ghp_path.exists():
        raise FileNotFoundError(f"GHP CSV file not found: {path}")

    with ghp_path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        expected_headers = ["week", "demand", "production"]
        if reader.fieldnames != expected_headers:
            raise ValueError(
                "GHP CSV must have header exactly: week,demand,production"
            )

        ghp_production: Dict[int, int] = {}
        for row_number, row in enumerate(reader, start=2):
            try:
                week = int(row["week"])
            except (TypeError, ValueError) as exc:
                raise ValueError(
                    f"GHP row {row_number}: column 'week' must contain integers."
                ) from exc

            try:
                production = int(row["production"])
            except (TypeError, ValueError) as exc:
                raise ValueError(
                    f"GHP row {row_number}: column 'production' must contain integers."
                ) from exc

            if week < 1:
                raise ValueError(f"GHP row {row_number}: week must be >= 1.")
            if production < 0:
                raise ValueError(f"GHP row {row_number}: production must be >= 0.")
            if week in ghp_production:
                raise ValueError(
                    f"GHP week values must be unique. Duplicate week {week} at row {row_number}."
                )

            ghp_production[week] = production

    if not ghp_production:
        raise ValueError("GHP CSV must contain at least one data row.")

    return ghp_production


def validate_inputs(items: List[Item], ghp_production: Dict[int, int]) -> Tuple[int, int]:
    if not items:
        raise ValueError("BOM must contain at least one item.")
    if not ghp_production:
        raise ValueError("GHP must not be empty.")

    seen_ids = set()
    for item in items:
        if item.id in seen_ids:
            raise ValueError(f"Duplicate item id found: {item.id}")
        seen_ids.add(item.id)

    level_zero_items = [item for item in items if item.bom_level == 0]
    if len(level_zero_items) != 1:
        raise ValueError("Exactly one item with bom_level == 0 is required.")

    for item in level_zero_items:
        if item.parents:
            raise ValueError(f"Level 0 item '{item.id}' must not have parents.")

    for item in items:
        if item.bom_level > 0 and not item.parents:
            raise ValueError(f"Non-root item '{item.id}' must define at least one parent.")

    all_ids = {item.id for item in items}
    item_by_id = {item.id: item for item in items}
    for item in items:
        for parent in item.parents:
            if parent.parent_id not in all_ids:
                raise ValueError(
                    f"Item '{item.id}' references non-existing parent_id '{parent.parent_id}'."
                )
            if parent.parent_id == item.id:
                raise ValueError(f"Item '{item.id}' cannot reference itself as parent.")

    for item in items:
        for parent in item.parents:
            parent_item = item_by_id[parent.parent_id]
            if parent_item.bom_level >= item.bom_level:
                raise ValueError(
                    f"Invalid BOM levels: item '{item.id}' (level {item.bom_level}) must have "
                    f"a parent on a lower level than '{parent.parent_id}' (level {parent_item.bom_level})."
                )

    visiting: set[str] = set()
    visited: set[str] = set()

    def _detect_cycle(item_id: str, path_stack: List[str]) -> None:
        if item_id in visiting:
            cycle_start = path_stack.index(item_id)
            cycle_path = " -> ".join(path_stack[cycle_start:] + [item_id])
            raise ValueError(f"BOM contains a cycle: {cycle_path}")
        if item_id in visited:
            return

        visiting.add(item_id)
        path_stack.append(item_id)
        current = item_by_id[item_id]
        for parent in current.parents:
            _detect_cycle(parent.parent_id, path_stack)
        path_stack.pop()
        visiting.remove(item_id)
        visited.add(item_id)

    for item in items:
        if item.id not in visited:
            _detect_cycle(item.id, [])

    max_ghp_week = max(ghp_production)
    max_scheduled_receipt_week = 0
    for item in items:
        if item.scheduled_receipts:
            max_scheduled_receipt_week = max(max_scheduled_receipt_week, max(item.scheduled_receipts))

    return max_ghp_week, max_scheduled_receipt_week

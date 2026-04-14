from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List


@dataclass(frozen=True)
class ParentLink:
    parent_id: str
    quantity_required: int


@dataclass(frozen=True)
class Item:
    id: str
    name: str
    bom_level: int
    lead_time: int
    lot_size: int
    on_hand: int
    scheduled_receipts: Dict[int, int]
    parents: List[ParentLink]


@dataclass(frozen=True)
class MRPWeek:
    week: int
    gross_requirements: int
    scheduled_receipts: int
    projected_on_hand: int
    net_requirements: int
    planned_order_receipts: int
    planned_order_releases: int


@dataclass(frozen=True)
class ItemMRPResult:
    item_id: str
    weeks: List[MRPWeek]

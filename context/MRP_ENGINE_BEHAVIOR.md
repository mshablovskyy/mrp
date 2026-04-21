# MRP Engine Behavior & Core Logic

> **Note for the Frontend Team:**
> While you do not need to modify the Python backend, understanding the mathematical rules and edge cases it uses will help you debug UI behavior, handle warnings correctly, and understand how the output CSVs are generated.

---

## 1. Terminology & Row Mapping
The engine maps standard MRP concepts to the following columns in the output CSVs (`[item_id]_mrp.csv`):

*   **Całkowite zapotrzebowanie** -> `gross_requirements`
*   **Planowane przyjęcia** -> `scheduled_receipts` (In-transit supply pre-defined in the JSON)
*   **Przewidywane na stanie** -> `projected_on_hand` (Inventory at the end of the week)
*   **Zapotrzebowanie netto** -> `net_requirements` (Shortage that must be fulfilled)
*   **Planowane przyjęcie zamówień** -> `planned_order_receipts` (Incoming orders planned by the engine)
*   **Planowane zamówienia** -> `planned_order_releases` (When the order must be placed, shifted by lead time)

---

## 2. The Core Mathematical Loop
The engine processes items completely deterministically, level by level (Level 0 first, then Level 1, etc.). This ensures that all parental demand is strictly established before a child component is calculated.

For each item, for each week, the logic executes in this exact order:

1.  **Gross Requirements Check:**
    *   *For Level 0 (Final Product):* Driven entirely by the `production` column in `ghp.csv`.
    *   *For Sub-items:* Sum of all parents' `planned_order_releases` multiplied by the respective `quantity_required` for that parent. (Note: If a component is shared across multiple parents, the demand is perfectly summed here).
2.  **Preliminary On-Hand Calculation:**
    `[Previous Week's projected_on_hand] + [scheduled_receipts] - [gross_requirements]`
3.  **Net Requirements:**
    If the Preliminary On-Hand is `< 0`, then `net_requirements = Absolute Value of Preliminary On-Hand`. Otherwise, it is `0`.
4.  **Planned Order Receipts (Ordering Logic):**
    If there is a Net Requirement, the engine orders **exactly one lot** (`lot_size` from JSON) to cover the shortage.
    *Note:* The engine does not round to multiple lots. If the shortage is `60` and the lot size is `40`, it orders `40`. The `projected_on_hand` can remain negative in this step depending strictly on the `lot_size` values.
5.  **Projected On-Hand Update:**
    The final `projected_on_hand` for the week becomes `[Preliminary On-Hand] + [planned_order_receipts]`.
6.  **Planned Order Releases (Time Shifting):**
    The `planned_order_receipts` are shifted backwards in time by the `lead_time`. For example, receiving an order in Week 4 with a lead time of 2 requires a planned release in Week 2.

---

## 3. Planning Horizon & Edge Cases

### The Planning Horizon
The total number of weeks calculated by the engine is dynamic. It is determined by the `max()` of:
*   The highest week defined in the `ghp.csv` schedule.
*   The highest week referenced in any item's `scheduled_receipts` mapping in the JSON.
All output CSVs will run from Week 1 up to this Max Week.

### Edge Case: Negative Release Weeks (Lead Time Push)
If an item has a short delivery time but requires a long `lead_time`, the mathematical formula might attempt to place a `planned_order_releases` into a zero or negative week (e.g., Week `-1`).
*   **Behavior:** The engine **does not** output negative week columns or rows to the CSV.
*   Instead, it logs a system warning detailing the Item ID, Receipt Week, and Required Release Week. The standard week values (Week 1 and onward) remain unchanged.

### Edge Case: Missing Weeks in GHP
If the `ghp.csv` skips weeks (e.g., jumps from Week 4 to Week 6), the engine treats the missing Week 5 as having `production = 0`.

---

## 4. Error Logging & Warning Policy

The backend acts as a strict validator for your inputs. It will exit immediately with an error (Fatal) or continue and log a warning depending on the severity.

**The command will exit with an error (Fatal) if:**
*   `bom_items.json` or `ghp.csv` are missing or improperly formatted.
*   There are duplicate Item IDs in the JSON.
*   A parent reference points to a non-existent `parent_id`.
*   Invalid constraints are detected (e.g., negative lot sizes).

**The command will continue but log a warning if:**
*   A lead time shift results in a negative week order.
*   A scheduled receipt week occurs completely outside the standard GHP timeline.

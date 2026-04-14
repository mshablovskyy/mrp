# Core MRP Engine (Python)

A stateless CLI backend that calculates Material Requirements Planning (MRP) tables from:

- BOM registry JSON
- GHP/MPS CSV

The engine processes items level-by-level (`bom_level` ascending) and generates one output CSV per item.

## Project Structure

- `mrp_engine.py` - CLI entrypoint
- `src/models.py` - dataclasses used by the engine
- `src/io_parsers.py` - input parsing and validation
- `src/calculator.py` - per-item weekly MRP calculations
- `src/engine.py` - level-by-level execution across all items
- `src/output_writer.py` - output CSV writer
- `data/` - ready-to-use sample BOM/GHP datasets
- `output/` - example output target directory

## Requirements

- Python 3.10+
- Runtime engine uses Python standard library only
- `pytest` is used for automated tests

`requirements.txt` is included so startup is the same on all machines.

## Quick Start

1. Create and activate virtual environment:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

1. Install dependencies:

```bash
pip install -r requirements.txt
```

1. Run the engine:

```bash
python mrp_engine.py --bom data/bom_zad1.json --ghp data/ghp_zad1.csv --out output
```

## CLI Contract

```bash
python mrp_engine.py --bom path/to/bom_items.json --ghp path/to/ghp.csv --out path/to/output_folder
```

Arguments:

- `--bom` required
- `--ghp` required
- `--out` required

Behavior:

- Creates output directory if missing
- Overwrites existing `[item_id]_mrp.csv`
- Exit code `0` on success
- Non-zero exit code on fatal validation/parsing errors

## Input Format

### BOM JSON

Top-level:

```json
{
  "items": []
}
```

Required item fields:

- `id` unique string
- `name` string
- `bom_level` integer >= 0
- `lead_time` integer >= 0
- `lot_size` integer > 0
- `on_hand` integer >= 0
- `scheduled_receipts` object with week keys as strings and integer quantities >= 0.

     `{"1": 20, "5": 5}` means 20 items come on week 1, 5 items on week 5.
- `parents` array of `{ "parent_id": "...", "quantity_required": int > 0 }`

### GHP CSV

Header must be exactly:

```csv
week,demand,production
```

Rules:

- `week` integer >= 1
- `production` integer >= 0
- `demand` is allowed but ignored by calculations
- week values must be unique

## Output Format

For each item `X`, output file:

- `X_mrp.csv`

Header and order:

```csv
week,gross_requirements,scheduled_receipts,projected_on_hand,net_requirements,planned_order_receipts,planned_order_releases
```

## How The Algorithm Works

For each item and each week in planning horizon:

- Compute gross requirements:
  - level 0: from GHP production
  - lower levels: from parent planned order releases * BOM quantities
- Compute preliminary projected on-hand:
  - previous projected + scheduled receipts - gross requirements
- If preliminary on-hand is negative:
  - net requirement = absolute shortage
  - planned order receipt = exactly one lot (`lot_size`)
  - projected on-hand is updated by adding this one lot
- Shift planned receipt by lead time to planned order release week

Important implemented behavior (as specified):

- One lot only per shortage event (no multi-lot rounding)
- `projected_on_hand` may remain negative after receipt if shortage > lot size
- negative release week is logged as warning and not written as CSV row

## Sample Datasets

Task-like datasets:

- `data/bom_zad1.json` + `data/ghp_zad1.csv`
- `data/bom_zad2.json` + `data/ghp_zad2.csv`
- `data/bom_zad1a.json` + `data/ghp_zad1a.csv`

Additional multi-parent demo:

- `data/bom_shared_component_demo.json` + `data/ghp_shared_component_demo.csv`

## Development Notes

- Engine is stateless between runs
- Input files are never modified
- Logging reports warnings (negative release week, scheduled receipts beyond original GHP range)
- Fatal input errors stop execution with non-zero exit code

## Teammate Integration Contract

This section defines the backend integration start/end points for GUI teammates.

### Start Point (What Backend Requires)

The backend starts when both files exist and are fully saved:

1. BOM JSON file (for example `data/bom_zad1.json`)
2. GHP CSV file (for example `data/ghp_zad1.csv`)

Input requirements that frontend must satisfy before calling CLI:

- BOM: top-level object with `items` list
- Exactly one item must have `bom_level == 0`
- Level 0 item must have no parents
- Every non-root item must have at least one parent
- Parent IDs must reference existing items
- Parent level must be lower than child level
- `week,demand,production` CSV header must be exact
- GHP week values must be unique and `>= 1`
- Numeric fields must satisfy contract bounds from spec

If frontend changes any scenario parameter (lot size, lead time, on-hand, scheduled receipts, GHP values), it must rewrite source files and rerun backend. Backend keeps no hidden state.

### End Point (What Backend Produces)

Backend ends by writing one CSV per item into output folder:

- `<item_id>_mrp.csv`

Each output file uses this exact schema:

```csv
week,gross_requirements,scheduled_receipts,projected_on_hand,net_requirements,planned_order_receipts,planned_order_releases
```

Week rows are written only for weeks `1..N` where:

- `N = max(max_ghp_week, max_scheduled_receipt_week)`

Negative release weeks are never written as CSV rows; they are reported as warnings.

### Runtime Flow For Frontend Team

1. Persist full BOM JSON file.
2. Persist full GHP CSV file.
3. Run backend command:

```bash
python mrp_engine.py --bom <bom_path> --ghp <ghp_path> --out <output_dir>
```

1. Read generated `*_mrp.csv` files from output directory.
2. Render rows in UI without changing backend semantics.

### Logging And Failure Semantics

Warnings (run continues):

- Scheduled receipt week outside original GHP range
- Lead time shift produces release week `< 1`

Fatal errors (run stops, non-zero exit):

- Missing files
- Invalid JSON or CSV format
- Invalid numeric constraints
- Duplicate item IDs
- Missing parent references
- Invalid parent/child BOM level relationships
- BOM cycle detection failure

### Troubleshooting Map

- Error about CSV header: ensure header is exactly `week,demand,production`
- Error about duplicate week: ensure each week appears only once in GHP
- Error about non-existing parent: frontend saved parent id typo or stale item id
- Error about invalid BOM levels: child references parent at same/deeper level
- Error about non-root item without parent: item is disconnected from product tree
- Warning about negative release week: lead time too long for early demand, output remains valid for weeks `>= 1`

## Testing

Run the full suite:

```bash
pytest
```

Test scope:

- Unit tests for weekly shortage logic
- Validation tests for contract enforcement
- Integration tests for zad1, zad2, zad1a, and shared-component datasets
- CLI tests for argument contract and fatal-error exit behavior

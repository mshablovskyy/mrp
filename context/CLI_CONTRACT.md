# CLI Contract & Error Handling

## Execution Command

```bash
python mrp_engine.py --bom path/to/bom_items.json --ghp path/to/ghp.csv --out path/to/output_folder
```

## Arguments

| Argument | Required | Description |
|----------|----------|-------------|
| `--bom` | Yes | Path to BOM JSON file |
| `--ghp` | Yes | Path to GHP CSV file |
| `--out` | Yes | Path to output folder (created if missing) |

## Exit Codes

| Exit Code | Meaning |
|-----------|---------|
| `0` | Success - output CSVs generated |
| `non-zero` | Fatal error - see below |

## Behavior

- Creates output directory if it doesn't exist
- Overwrites existing `*_mrp.csv` files in output folder safely

---

## Fatal Errors (non-zero exit)

The command will exit immediately with an error if:

- `bom_items.json` or `ghp.csv` are missing
- Invalid JSON or CSV format (parse errors)
- Duplicate item IDs in BOM
- Invalid numeric constraints (negative lot_size, negative lead_time, etc.)
- A parent reference points to a non-existent `parent_id`

---

## Warnings (logged, execution continues)

The command will continue but log a warning if:

- Lead time shift results in a negative week order (e.g., need to order in Week -1 to fulfill Week 1 demand)
- A scheduled receipt week occurs completely outside the standard GHP planning timeline

These warnings are informational and do not indicate failure.

---

## GUI Integration Notes

- Use `subprocess.run()` and check `returncode` to detect success/failure
- You do NOT need to pre-create the output directory - the engine handles it
- It is safe to re-run the engine multiple times - previous output files will be overwritten
- Display warning messages to users if the engine logs warnings (helpful for debugging their input data)
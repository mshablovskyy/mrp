# MRP Simulator - Material Requirements Planning Application

A web-based MRP calculator with GUI for managing BOM (Bill of Materials), GHP schedules, and visualizing results.

## How to Run

```bash
# 1. Create and activate virtual environment
python3 -m venv .venv
source .venv/bin/activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. Run the app
streamlit run app.py
```

Then open http://localhost:8501 in your browser.

## Features

- **Dashboard** - Run MRP simulations and view results
- **Schedule (GHP)** - Create and manage master production schedule
- **BOM Tree** - Visualize and manage product structure
- **Parameters** - Adjust lot sizes, lead times, and inventory levels

## Project Structure

- `app.py` - Main Streamlit application
- `mrp_engine.py` - CLI backend entrypoint
- `src/` - Backend engine modules
- `pages/` - GUI page components
- `data/` - Sample BOM and GHP datasets
- `output/` - Generated MRP results
- `.venv/` - Virtual environment (create with `python3 -m venv .venv`)

## Sample Datasets

Ready to use examples in `data/`:

- `bom_zad1.json` + `ghp_zad1.csv`
- `bom_zad2.json` + `ghp_zad2.csv`
- `bom_zad1a.json` + `ghp_zad1a.csv`
- `bom_shared_component_demo.json` + `ghp_shared_component_demo.csv`

## Running Tests

```bash
pytest
```

## CLI Mode (Advanced)

The underlying engine can also be run via command line:

```bash
python mrp_engine.py --bom data/bom_zad1.json --ghp data/ghp_zad1.csv --out output
```

Arguments:
- `--bom` - Path to BOM JSON file
- `--ghp` - Path to GHP CSV file  
- `--out` - Output directory for MRP results
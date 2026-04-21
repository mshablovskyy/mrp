# GUI Architecture & API Specification

> **Note for AI Coding Assistants:** 
> This is your root system context. Read this fully to understand the headless backend you are connecting to, your data contracts, and your specific GUI development tasks.

## 1. Project Overview & MVC Architecture
This project is an **MRP (Material Requirements Planning) Simulator**. 
The backend has already been built and is located in this repository (e.g., `mrp_engine.py` and `src/`). It acts as a headless, purely mathematical Model. 

**Backend Characteristics:**
- **Stateless:** It maintains no memory between runs. 
- **Black-box:** You do NOT need to modify the Python backend. You simply write specific input files, trigger a CLI command in a subprocess, and read the generic output files.

Your job is to build the View/Controller GUI that collects data, passes it to this backend, and visualizes the results.

---

## 2. Global GUI Layout & Integration Strategy
To ensure that both engineers can build their features independently and merge them seamlessly into a "Single App", the GUI should be designed as a **Multi-Page Application with a Sidebar**.

- **Navigation:** Use a persistent left or top sidebar to navigate between 4 distinct views.
- **Home Page:** The execution dashboard **must** be the Home Page (Page 1).
- **Framework Recommendation:** Python's **Streamlit** is highly recommended for building this specific architecture easily, but any stack is allowed.

---

## 3. Team Responsibilities & App Pages

The work is split into two strict domains to prevent git/code conflicts.

### Teammate 2: "The Engine & Schedule Controller"
**Page 1: Home Dashboard (Execution & Visuals)**
- This is the main landing page of the app.
- **File Validation Pre-Check:** Before attempting to run the engine, the UI *must* verify that `bom_items.json` and `ghp.csv` exist.
- **Warning States:** If files are missing, the "Run Simulation" button must be disabled, and a clear warning must be displayed specifying exactly which files are missing (e.g., "⚠️ Missing: ghp.csv. Please define the schedule first.").
- **Execution:** Upon clicking "Run Simulation", execute the python terminal subprocess.
- **Visualization:** Read the resulting `[item_id]_mrp.csv` files and display them in clean, readable UI tables.

**Page 2: Master Production Schedule (GHP)**
- A data-editor table or CSV uploader to create the GHP schedule.
- Outputs/Updates the `ghp.csv` file.

### Teammate 1: "The BOM & Product Engineer"
**Page 3: BOM Architecture & Tree**
- GUI form to create and outline the base BOM template.
- Generates the permanent structural data (Item IDs, names, BOM levels, and Parent-Child relationships).
- Must include a visual tree (graph) representation to verify the product hierarchy.
- Outputs/Updates the `bom_items.json` file.

**Page 4: Parameter Tweaker (What-If Scenarios)**
- GUI to load the existing JSON map and modify "non-permanent" variables rapidly without touching the structure.
- Editable parameters: `lot_size` (wielkość partii), `lead_time` (czas realizacji), `on_hand` (na stanie), and `scheduled_receipts` (planowane przyjęcia).
- Updates the `bom_items.json` file securely.

---

## 4. State & Memory (Rolling History Buffer)
To allow users to prototype safely, the GUI must implement a **3-Step Rolling History** for both `bom_items.json` and `ghp.csv`. Do not blindly overwrite the main file. 

1. **Version Buffer:** Keep up to 3 historical saves natively in the directory. Upon a 4th write, rotate out the oldest.
2. **Undo/Restore:** Provide a "Restore Previous Version" button on the editing pages to fall back a step if a mistake is made.
3. **Write Optimization:** Before initiating a file save/version-bump, specifically check if the user actually modified any data. If identical, skip the disk write.

---

## 5. Formal Data Contracts

### 1. Execution Contract
Trigger the backend via a terminal subprocess (e.g., `subprocess.run()`, `exec()`, etc). 
```bash
python mrp_engine.py --bom path/to/bom_items.json --ghp path/to/ghp.csv --out path/to/output_folder
```

### 2. Output MRP CSV Contract (`*_mrp.csv`)
The engine generates one file per item. Expect exactly this header format:
```csv
week,gross_requirements,scheduled_receipts,projected_on_hand,net_requirements,planned_order_receipts,planned_order_releases
```

### 3. BOM JSON Contract (`bom_items.json`)
The hierarchy is flat. Sub-items point *upward* to their parents using the `parents` array. Exactly one item must possess `bom_level: 0` (the root product).
```json
{
  "items": [
    {
      "id": "STOL-001",
      "name": "Stół",
      "bom_level": 0,
      "lead_time": 1,
      "lot_size": 1,
      "on_hand": 2,
      "scheduled_receipts": {},
      "parents": [] 
    },
    {
      "id": "NOGI-001",
      "name": "Nogi",
      "bom_level": 1,
      "lead_time": 2,
      "lot_size": 120,
      "on_hand": 40,
      "scheduled_receipts": {"2": 50}, 
      "parents": [
        { "parent_id": "STOL-001", "quantity_required": 4 }
      ]
    }
  ]
}
```
*(Note: scheduled_receipt keys are string-typed week numbers. Quantities are integers.)*

### 4. GHP CSV Contract (`ghp.csv`)
Requires exact headers. The engine processes `week` and `production`, but `demand` must be maintained in the file.
```csv
week,demand,production
1,0,0
2,0,0
3,20,28
4,0,0
```

---

## 6. Reference Behavior Patterns

The engine follows these key MRP logic patterns. Understanding them helps debug UI behavior and interpret results:

1. **One Lot Per Shortage**: When there's a net requirement, the engine orders exactly one lot (the `lot_size` value). It does NOT round to multiple lots. If shortage is 60 and lot_size is 40, it orders 40 - leaving projected_on_hand potentially negative.

2. **Component Demand = Parent Planned Releases**: For sub-items (Level > 0), gross requirements are driven by parents' `planned_order_receipts`, NOT their gross requirements. This is critical for shared components.

3. **Scheduled Receipts Offset Shortage**: External scheduled receipts (incoming inventory already in transit) offset the shortage first. If you have 30 units arriving in Week 1 and need 30, no new order is created.

4. **Level-by-Level Processing**: The engine processes all Level 0 items first, then Level 1, then Level 2, etc. This ensures parent planned releases are calculated before child demand is derived.

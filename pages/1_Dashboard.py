import streamlit as st
import subprocess
import os
import glob
import pandas as pd
import json

HEADERS = {
    "week": "Tydzień",
    "gross_requirements": "Całkowite zapotrzebowanie",
    "scheduled_receipts": "Planowane przyjęcia",
    "projected_on_hand": "Przewidywane na stanie",
    "net_requirements": "Zapotrzebowanie netto",
    "planned_order_receipts": "Planowane przyjęcie",
    "planned_order_releases": "Planowane zamówienia"
}

st.set_page_config(page_title="Panel sterowania MRP", layout="wide")
st.title("⚙️ Panel sterowania MRP")

OUTPUT_DIR = "output/current_run"

os.makedirs("data", exist_ok=True)

col1, col2 = st.columns(2)

BOM_FILE = st.session_state.get("bom_path", "data/bom_zad1.json")
GHP_FILE = st.session_state.get("ghp_path", "data/ghp_zad1.csv")

with col1:
    uploaded_bom = st.file_uploader("Wybierz strukturę BOM (.json)", type=["json"])
    if uploaded_bom is not None:
        BOM_FILE = os.path.join("data", uploaded_bom.name)
        with open(BOM_FILE, "wb") as f:
            f.write(uploaded_bom.getbuffer())
        st.session_state["bom_path"] = BOM_FILE
    st.info(f"📁 Plik BOM: `{BOM_FILE}`")

with col2:
    uploaded_ghp = st.file_uploader("Wybierz harmonogram GHP (.csv)", type=["csv"])
    if uploaded_ghp is not None:
        GHP_FILE = os.path.join("data", uploaded_ghp.name)
        with open(GHP_FILE, "wb") as f:
            f.write(uploaded_ghp.getbuffer())
        st.session_state["ghp_path"] = GHP_FILE
    st.info(f"📁 Plik GHP: `{GHP_FILE}`")

bom_exists = os.path.exists(BOM_FILE)
ghp_exists = os.path.exists(GHP_FILE)
files_ready = bom_exists and ghp_exists

with col1:
    if not bom_exists: 
        st.error(f"⚠️ Brak pliku BOM")
with col2:
    if not ghp_exists: 
        st.error(f"⚠️ Brak pliku: GHP")

if st.button("🚀 Uruchom Symulację MRP", type="primary"):
    with st.spinner("Przetwarzanie..."):
        result = subprocess.run(
            ["python", "mrp_engine.py", "--bom", BOM_FILE, "--ghp", GHP_FILE, "--out", OUTPUT_DIR],
            capture_output=True, text=True
        )
        
        if result.stderr:
            for line in result.stderr.splitlines():
                if "WARNING" in line:
                    st.warning(f"Ostrzeżenie: {line.split('WARNING:mrp_engine:')[-1].strip()}")
                elif "ERROR" in line or "Fatal" in line:
                    st.error(f"Błąd krytyczny: {line.split(':')[-1].strip()}")

        if result.returncode == 0:
            st.session_state["run_successful"] = True
        else:
            st.error("Wystąpił błąd krytyczny.")
            st.session_state["run_successful"] = False

st.divider()

if st.session_state.get("run_successful", False):
    st.subheader("📊 Wyniki MRP")
    item_names = {}
    if os.path.exists(BOM_FILE):
        with open(BOM_FILE, "r", encoding="utf-8") as f:
            try:
                bom_data = json.load(f)
                item_names = {item["id"]: item["name"] for item in bom_data.get("items", [])}
            except json.JSONDecodeError:
                pass

    output_files = sorted(glob.glob(os.path.join(OUTPUT_DIR, "*_mrp.csv")))
    
    if output_files:
        item_ids = [os.path.basename(f).replace("_mrp.csv", "") for f in output_files]
        
        tab_labels = [f"{item_names.get(item_id, item_id)}" for item_id in item_ids]
        
        tabs = st.tabs(tab_labels)
        
        for tab, item_id, tab_label, file_path in zip(tabs, item_ids, tab_labels, output_files):
            with tab:
                st.markdown(f"### **{tab_label}**") 
                
                df = pd.read_csv(file_path)
                df = df.rename(columns=HEADERS).set_index("Tydzień")
                df_transposed = df.T
                df_transposed.columns = [f"Tydzień {col}" for col in df_transposed.columns]
                df_transposed = df_transposed.fillna(0).astype(int)
                
                st.dataframe(df_transposed, use_container_width=True)

                st.download_button(
                    label=f"⬇️ Pobierz CSV ({tab_label})",
                    data=df_transposed.to_csv(index=True).encode('utf-8'),
                    file_name=f"{item_names.get(item_id, item_id).replace(' ', '_')}_{item_id}_mrp.csv",
                    mime="text/csv",
                    key=f"dl_{item_id}"
                )
                
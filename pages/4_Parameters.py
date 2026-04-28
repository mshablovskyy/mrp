import streamlit as st
import json
import os
import sys

# Podpinamy nasz plik narzędziowy z historią
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from utils import save_bom_with_history, restore_bom_history

st.set_page_config(page_title="Parameter Tweaker", layout="wide")

st.title("🎛️ Symulator Parametrów (What-If)")
st.write("Szybko modyfikuj zmienne bez obaw o uszkodzenie hierarchii BOM.")

BOM_FILE = st.session_state.get("bom_path", "data/bom_zad1.json")

st.info(f"📁 Plik BOM: `{BOM_FILE}`")

def load_bom_data():
    if os.path.exists(BOM_FILE):
        with open(BOM_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"items": []}

bom_data = load_bom_data()

if not bom_data.get("items"):
    st.warning("Plik BOM jest pusty lub nie istnieje. Skonfiguruj go najpierw na Stronie 3.")
else:
    # Używamy st.form, żeby zmiany zapisały się dopiero po kliknięciu głównego przycisku
    with st.form("parameters_form"):
        st.subheader("Parametry produkcyjne przedmiotów")
        
        updated_items = []
        
        # Generujemy pola edycji dla każdego przedmiotu w BOM
        for item in bom_data["items"]:
            st.markdown(f"### 📦 {item['name']} (ID: `{item['id']}` | Poziom: {item['bom_level']})")
            
            # Układamy pola w 4 kolumnach
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                new_lot_size = st.number_input(
                    "Wielkość partii (lot_size)", 
                    min_value=1, 
                    value=item.get("lot_size", 1), 
                    key=f"lot_{item['id']}"
                )
            with col2:
                new_lead_time = st.number_input(
                    "Czas realizacji (lead_time)", 
                    min_value=0, 
                    value=item.get("lead_time", 0), 
                    key=f"lead_{item['id']}"
                )
            with col3:
                new_on_hand = st.number_input(
                    "Na stanie (on_hand)", 
                    min_value=0, 
                    value=item.get("on_hand", 0), 
                    key=f"hand_{item['id']}"
                )
            with col4:
                # Planowane przyjęcia w formacie tekstowym JSON, np. {"2": 50}
                sched_str = json.dumps(item.get("scheduled_receipts", {}))
                new_sched_str = st.text_input(
                    "Planowane przyjęcia (JSON)", 
                    value=sched_str, 
                    key=f"sched_{item['id']}"
                )
            
            # Bezpieczne wczytywanie planowanych przyjęć
            try:
                new_sched = json.loads(new_sched_str)
                if not isinstance(new_sched, dict):
                    new_sched = item.get("scheduled_receipts", {})
            except:
                new_sched = item.get("scheduled_receipts", {})

            # Tworzymy zaktualizowany słownik dla przedmiotu (blokując edycję struktury)
            updated_item = {
                "id": item["id"],
                "name": item["name"],
                "bom_level": item["bom_level"],
                "lead_time": new_lead_time,
                "lot_size": new_lot_size,
                "on_hand": new_on_hand,
                "scheduled_receipts": new_sched,
                "parents": item["parents"] # Zostawiamy oryginalne powiązania!
            }
            updated_items.append(updated_item)
            
            st.divider()

        # Przycisk zapisujący cały formularz
        submit = st.form_submit_button("💾 Zapisz parametry do pliku", type="primary")
        
        if submit:
            new_bom_data = {"items": updated_items}
            # Zapis z użyciem historii, którą zrobiliśmy wcześniej
            success = save_bom_with_history(BOM_FILE, new_bom_data)
            if success:
                st.success("Parametry zaktualizowane i zapisane pomyślnie!")
            else:
                st.info("Brak zmian do zapisania (dane były identyczne).")

    # Przycisk Undo
    st.subheader("Opcje historii")
    if st.button("↩️ Cofnij zmiany"):
        if restore_bom_history(BOM_FILE):
            st.success("Cofnięto zmiany.")
            st.rerun() # Automatyczne odświeżenie strony po cofnięciu
        else:
            st.warning("Brak kopii zapasowej dla tego pliku.")
import streamlit as st
import json
import os
import sys

# Podpinamy nasz plik narzędziowy z historią
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from utils import save_bom_with_history, restore_bom_history

st.set_page_config(page_title="BOM Architecture", layout="wide")

st.title("🌳 Architektura BOM i Drzewo Produktu")
st.write("Wizualizacja hierarchii produktu oraz edytor struktury materiałowej.")

BOM_FILE = st.session_state.get("bom_path", "data/bom_zad1.json")

st.info(f"📁 Plik BOM: `{BOM_FILE}`")

def load_bom_data():
    if os.path.exists(BOM_FILE):
        with open(BOM_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"items": []}


if "last_loaded_bom_path" not in st.session_state or st.session_state.last_loaded_bom_path != BOM_FILE:
    st.session_state.bom_text = json.dumps(load_bom_data(), indent=2)
    st.session_state.last_loaded_bom_path = BOM_FILE


bom_data = load_bom_data()

# Funkcja generująca kod grafu (język DOT)
def generate_dot_graph(items):
    dot = "digraph BOM {\n"
    # Ustawienia stylu węzłów i strzałek
    dot += "  node [shape=box, style=filled, fillcolor=\"#E1F5FE\", fontname=\"Arial\", rounded=true];\n"
    dot += "  edge [fontname=\"Arial\", fontsize=10, color=\"#555555\"];\n"
    dot += "  rankdir=TB;\n" # TB = Top to Bottom (z góry na dół)

    # Najpierw tworzymy wszystkie węzły (przedmioty)
    for item in items:
        item_id = item["id"]
        name = item["name"]
        level = item["bom_level"]
        
        # Wyróżniamy produkt główny (Level 0) innym kolorem
        if level == 0:
            dot += f'  "{item_id}" [label="{name}\\n({item_id})\\nPoziom: {level}", fillcolor=\"#C8E6C9\", style=\"filled,bold\"];\n'
        else:
            dot += f'  "{item_id}" [label="{name}\\n({item_id})\\nPoziom: {level}"];\n'

        # Następnie rysujemy strzałki (relacje rodzic -> dziecko)
        for parent in item.get("parents", []):
            parent_id = parent["parent_id"]
            qty = parent["quantity_required"]
            dot += f'  "{parent_id}" -> "{item_id}" [label="{qty} szt."];\n'

    dot += "}\n"
    return dot

# Dzielimy ekran na dwie zakładki!
tab1, tab2 = st.tabs(["Drzewo Wizualne", "Edytor Struktury (JSON)"])

# --- ZAKŁADKA 1: GRAF ---
with tab1:
    st.subheader("Wizualizacja powiązań")
    if bom_data and "items" in bom_data and len(bom_data["items"]) > 0:
        try:
            dot_code = generate_dot_graph(bom_data["items"])
            st.graphviz_chart(dot_code, use_container_width=True)
        except Exception as e:
            st.error(f"Nie udało się wygenerować grafu. Upewnij się, że struktura JSON jest poprawna. Szczegóły: {e}")
    else:
        st.info("Brak danych do wyświetlenia drzewa.")

# --- ZAKŁADKA 2: EDYTOR ---
with tab2:
    col1, col2 = st.columns([2, 1])
    
    with col1:
        new_bom_text = st.text_area("Edytuj BOM (format JSON):", value=st.session_state.bom_text, height=400)
        
        if st.button("💾 Zapisz zmiany w strukturze", type="primary"):
            try:
                new_data = json.loads(new_bom_text)
                success = save_bom_with_history(BOM_FILE, new_data)
                
                if success:
                    st.success("Zapisano zmiany!")
                    st.session_state.bom_text = json.dumps(new_data, indent=2)
                    st.rerun() # Odświeżamy, żeby graf w pierwszej zakładce też się zaktualizował!
                else:
                    st.info("Brak zmian do zapisania.")
            except json.JSONDecodeError as e:
                st.error(f"Błąd formatu JSON! Szczegóły: {e}")

    with col2:
        st.info("💡 **Wskazówka:** Produkt główny (zaznaczony na zielono na grafie) musi mieć `bom_level: 0`.")
        st.subheader("Opcje historii")
        if st.button("↩️ Cofnij zmiany"):
            if restore_bom_history(BOM_FILE):
                st.success("Cofnięto zmiany")
                st.session_state.bom_text = json.dumps(load_bom_data(), indent=2)
                st.rerun()
            else:
                st.warning("Brak kopii zapasowej dla tego pliku.")
import streamlit as st

# Definiujemy strony i nadajemy im własne nazwy/ikony
page_1 = st.Page("pages/1_Dashboard.py", title="Panel sterowania MRP", icon="⚙️")
page_2 = st.Page("pages/2_Schedule.py", title="Harmonogram GHP", icon="📅")
page_3 = st.Page("pages/3_BOM_Tree.py", title="Struktura BOM", icon="🌳")
page_4 = st.Page("pages/4_Parameters.py", title="Parametry MRP", icon="🎛️")

# Inicjalizujemy nawigację
pg = st.navigation([page_1, page_2, page_3, page_4])
st.set_page_config(page_title="Symulator MRP", layout="wide")
pg.run()
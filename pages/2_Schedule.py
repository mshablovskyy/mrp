import streamlit as st
import pandas as pd
import os
import shutil
from pathlib import Path

GHP_FILE = st.session_state.get("ghp_path", "data/ghp_zad1.csv")

MAX_HISTORY = 3

st.set_page_config(page_title="Harmonogram GHP", layout="wide")
st.title("📅 Główny Harmonogram Produkcji (GHP)")
st.info(f"📁 Plik GHP: `{GHP_FILE}`")

def save_ghp_with_history(new_df: pd.DataFrame) -> bool:
    path = Path(GHP_FILE)
    
    if path.exists():
        current_df = pd.read_csv(path)
        if current_df.equals(new_df):
            return False 
        
    if path.exists():
        oldest_backup = Path(f"{GHP_FILE}.bak_{MAX_HISTORY}")
        if oldest_backup.exists(): oldest_backup.unlink()
        for i in range(MAX_HISTORY - 1, 0, -1):
            src, dst = Path(f"{GHP_FILE}.bak_{i}"), Path(f"{GHP_FILE}.bak_{i+1}")
            if src.exists(): src.rename(dst)
        shutil.copy2(path, f"{GHP_FILE}.bak_1")

    new_df.to_csv(path, index=False, columns=["week", "demand", "production"])
    return True

if os.path.exists(GHP_FILE):
    df = pd.read_csv(GHP_FILE)
else:
    df = pd.DataFrame({"week": [1], "demand": [0], "production": [0]})

df = df.sort_values("week")
df["week"] = range(1, len(df) + 1)
df_to_edit = df.set_index(pd.Index(range(1, len(df) + 1), name="Tydzień"))
df_to_edit = df_to_edit.drop(columns=["week"])

edited_df = st.data_editor(
    df_to_edit,
    num_rows="dynamic",
    use_container_width=True,
    hide_index=False,
    column_config={
        "demand": st.column_config.NumberColumn("Popyt", min_value=0, step=1, required=True),
        "production": st.column_config.NumberColumn("Produkcja", min_value=0, step=1, required=True)
    }
)


if st.button("💾 Zapisz zmiany", type="primary"):
        final_df = edited_df.reset_index(drop=True)
        final_df["week"] = range(1, len(final_df) + 1)
        final_df["demand"] = final_df["demand"].fillna(0).astype(int)
        final_df["production"] = final_df["production"].fillna(0).astype(int)
        
        if save_ghp_with_history(final_df[["week", "demand", "production"]]):
            st.success("Zaktualizowano plik.")
            st.rerun()
        else:
            st.info("Brak zmian do zapisania.")
if st.button("↩️ Cofnij zmiany"):
        backup_path = Path(f"{GHP_FILE}.bak_1")
        if backup_path.exists():
            shutil.copy2(backup_path, GHP_FILE)
            st.success("Cofnięto zmiany.")
            st.rerun()
        else:
            st.warning("Brak kopii zapasowej dla tego pliku.")
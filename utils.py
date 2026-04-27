import os
import json
import shutil
from pathlib import Path

def save_bom_with_history(file_path: str, new_data: dict, max_history: int = 3) -> bool:
    """
    Zapisuje plik JSON zachowując historię (rolling buffer) 
    i optymalizuje zapis sprawdzając, czy zaszły zmiany.
    """
    path = Path(file_path)
    
    if path.exists():
        with open(path, "r", encoding="utf-8") as f:
            try:
                current_data = json.load(f)
                if current_data == new_data:
                    return False  
            except json.JSONDecodeError:
                pass 

    if path.exists():
        oldest_backup = Path(f"{file_path}.bak_{max_history}")
        if oldest_backup.exists():
            oldest_backup.unlink()

        for i in range(max_history - 1, 0, -1):
            src = Path(f"{file_path}.bak_{i}")
            dst = Path(f"{file_path}.bak_{i+1}")
            if src.exists():
                src.rename(dst)

        shutil.copy2(path, f"{file_path}.bak_1")

    with open(path, "w", encoding="utf-8") as f:
        json.dump(new_data, f, indent=2)
        
    return True 

def restore_bom_history(file_path: str) -> bool:
    """
    Przywraca plik BOM z pierwszej dostępnej kopii zapasowej (.bak_1).
    Wymagany do funkcji Undo/Restore.
    """
    backup_path = Path(f"{file_path}.bak_1")
    if not backup_path.exists():
        return False
        
    shutil.copy2(backup_path, file_path)
    return True
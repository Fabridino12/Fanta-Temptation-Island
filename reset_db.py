"""
Reset del database: cancella gioco.db e lo ricrea pulito con i dati iniziali.

USO:
    .\\venv\\Scripts\\python.exe reset_db.py

ATTENZIONE: cancella TUTTO (utenti, squadre, schieramenti, leghe, eventi
assegnati, impostazioni...). Resta solo il seed di partenza:
admin/admin123, 6 coppie, eventi di esempio, Puntata 1 aperta.
Le foto in images/ e il regolamento.txt NON vengono toccati.
"""
import os
import runpy

DB = "gioco.db"

if os.path.exists(DB):
    try:
        os.remove(DB)
        print(f"{DB} eliminato.")
    except PermissionError:
        print(f"ERRORE: {DB} risulta in uso. Chiudi l'app Streamlit e riprova.")
        raise SystemExit(1)
else:
    print(f"{DB} non trovato: lo creo da zero.")

# riesegue database.py per ricreare schema + seed
runpy.run_path("database.py", run_name="__main__")

print("Reset completato: tutto pulito con i dati iniziali.")

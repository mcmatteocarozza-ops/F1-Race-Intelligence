
import json
from pathlib import Path

import requests

# Identificativo della gara di Monza 2024
SESSION_KEY = 9590

# Endpoint OpenF1 per i tempi sul giro
url = "https://api.openf1.org/v1/laps"

params = {
    "session_key": SESSION_KEY
}

print("Connessione a OpenF1...")
print("Download dei tempi sul giro di Monza 2024...")

# Richiesta HTTP
response = requests.get(
    url,
    params=params,
    timeout=120
)

# Controlla eventuali errori HTTP
response.raise_for_status()

# Converte la risposta JSON in oggetti Python
laps = response.json()

if not isinstance(laps, list) or not laps:
    raise RuntimeError("Nessun dato valido ricevuto.")

print(f"Giri acquisiti: {len(laps)}")

# Crea la cartella di destinazione
output_dir = Path("data/raw")
output_dir.mkdir(parents=True, exist_ok=True)

# Salva i dati originali
output_file = output_dir / "monza_2024_laps.json"

with output_file.open("w", encoding="utf-8") as file:
    json.dump(laps, file, indent=2, ensure_ascii=False)

print(f"File salvato: {output_file.resolve()}")

# Mostra un esempio dei dati
print("\nEsempio di record:")
print(json.dumps(laps[0], indent=2))

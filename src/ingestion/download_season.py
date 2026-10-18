import json
import time
from pathlib import Path

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# Percorsi del progetto
CATALOG_PATH = Path("data/bronze/races_2024.json")
OUTPUT_DIR = Path("data/bronze/laps")

API_URL = "https://api.openf1.org/v1/laps"

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# Configurazione retry HTTP
retry_strategy = Retry(
    total=3,
    backoff_factor=2,
    status_forcelist=[429, 500, 502, 503, 504],
    allowed_methods=["GET"]
)

http = requests.Session()
adapter = HTTPAdapter(max_retries=retry_strategy)
http.mount("https://", adapter)

# Caricamento catalogo gare
with CATALOG_PATH.open("r", encoding="utf-8") as f:
    races = json.load(f)

print("=== F1 RACE INTELLIGENCE ===")
print(f"Gare da elaborare: {len(races)}\n")

total_records = 0
successful = 0
failed = []

for index, race in enumerate(races, start=1):

    session_key = race["session_key"]
    circuit = race["circuit"]

    filename = f"{session_key}_{circuit}.json"
    output_file = OUTPUT_DIR / filename

    print(f"[{index}/{len(races)}] {circuit}")

    # Evita download duplicati
    if output_file.exists():
        print("  Già scaricato, salto.")
        continue

    try:
        response = http.get(
            API_URL,
            params={"session_key": session_key},
            timeout=120
        )

        response.raise_for_status()
        laps = response.json()

        if not isinstance(laps, list) or not laps:
            raise ValueError("Risposta vuota o non valida")

        # Scrittura temporanea per evitare file parziali
        temp_file = output_file.with_suffix(".tmp")

        with temp_file.open("w", encoding="utf-8") as f:
            json.dump(laps, f, ensure_ascii=False)

        temp_file.replace(output_file)

        print(f"  OK - {len(laps)} record")

        total_records += len(laps)
        successful += 1

        # Pausa per non sovraccaricare l'API
        time.sleep(1)

    except (requests.RequestException, ValueError) as e:
        print(f"  ERRORE: {e}")
        failed.append({
            "session_key": session_key,
            "circuit": circuit,
            "error": str(e)
        })

http.close()

print("\n=== REPORT ACQUISIZIONE ===")
print(f"Nuove gare scaricate: {successful}")
print(f"Nuovi record acquisiti: {total_records}")
print(f"Errori: {len(failed)}")

if failed:
    print("\nGare da riprovare:")
    for item in failed:
        print(f"- {item['circuit']}: {item['error']}")

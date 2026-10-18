import json
from pathlib import Path

import requests

API_URL = "https://api.openf1.org/v1/sessions"

print("F1 Race Intelligence")
print("Ricerca delle gare della stagione 2024...\n")

response = requests.get(
    API_URL,
    params={
        "year": 2024,
        "session_name": "Race"
    },
    timeout=60
)

response.raise_for_status()
sessions = response.json()

if not isinstance(sessions, list):
    raise RuntimeError("Risposta API non valida")

races = [
    session
    for session in sessions
    if session.get("session_name") == "Race"
    and session.get("year") == 2024
]

races.sort(key=lambda x: x.get("date_start") or "")

catalog = []

for race in races:
    catalog.append({
        "session_key": race["session_key"],
        "meeting_key": race["meeting_key"],
        "circuit": race["circuit_short_name"],
        "country": race["country_name"],
        "date": race["date_start"]
    })

output_dir = Path("data/bronze")
output_dir.mkdir(parents=True, exist_ok=True)

output_file = output_dir / "races_2024.json"

with output_file.open("w", encoding="utf-8") as f:
    json.dump(catalog, f, indent=2, ensure_ascii=False)

print(f"Gare trovate: {len(catalog)}\n")

for i, race in enumerate(catalog, start=1):
    print(
        f"{i:02d}. {race['country']:<20} "
        f"{race['circuit']:<18} "
        f"Session Key: {race['session_key']}"
    )

print(f"\nCatalogo salvato in: {output_file.resolve()}")
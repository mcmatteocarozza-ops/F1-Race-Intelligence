import json
from pathlib import Path
from collections import Counter

file_path = Path("data/raw/monza_2024_laps.json")

with file_path.open("r", encoding="utf-8") as file:
    laps = json.load(file)

print("=== F1 RACE INTELLIGENCE ===")
print("Dataset: Monza 2024\n")

print("Numero totale di record:", len(laps))

# piloti presenti
drivers = set(
    lap["driver_number"]
    for lap in laps
    if lap.get("driver_number") is not None
)

print("Numero piloti:", len(drivers))
print("Numeri piloti:", sorted(drivers))

# campi disponibili
print("\nCampi disponibili:")
for field in laps[0].keys():
    print("-", field)

# tempi sul giro
valid_laps = [
    lap for lap in laps
    if isinstance(lap.get("lap_duration"), (int, float))
    and lap["lap_duration"] > 0
]

print("\nGiri con durata valida:", len(valid_laps))
print("Giri senza durata valida:", len(laps) - len(valid_laps))

# Conta i giri per pilota
counts = Counter(
    lap["driver_number"]
    for lap in laps
    if lap.get("driver_number") is not None
)

print("\nNumero di record per pilota:")
for driver, count in sorted(counts.items()):
    print(f"Pilota #{driver}: {count}")

import json
from pathlib import Path

DATA_DIR = Path("data/bronze/laps")
files = sorted(DATA_DIR.glob("*.json"))

total_records = 0
valid_records = 0
missing_duration = 0
duplicates = 0
errors = []

print("=== F1 RACE INTELLIGENCE ===")
print("DATA QUALITY REPORT - STAGIONE 2024\n")

print(f"File JSON trovati: {len(files)}\n")

for file_path in files:
    try:
        with file_path.open("r", encoding="utf-8") as f:
            laps = json.load(f)

        if not isinstance(laps, list):
            raise ValueError("Il JSON non contiene una lista")

        seen = set()
        file_valid = 0
        file_duplicates = 0

        for lap in laps:
            if not isinstance(lap, dict):
                continue

            duration = lap.get("lap_duration")

            if isinstance(duration, (int, float)) and duration > 0:
                valid_records += 1
                file_valid += 1
            else:
                missing_duration += 1

            key = (
                lap.get("session_key"),
                lap.get("driver_number"),
                lap.get("lap_number")
            )

            if key in seen:
                duplicates += 1
                file_duplicates += 1
            else:
                seen.add(key)

        total_records += len(laps)

        print(
            f"{file_path.stem:<25} "
            f"Record: {len(laps):>5} | "
            f"Durate valide: {file_valid:>5} | "
            f"Duplicati: {file_duplicates}"
        )

    except (OSError, ValueError, TypeError) as e:
        errors.append((file_path.name, str(e)))
        print(f"ERRORE - {file_path.name}: {e}")

print("\n=== RIEPILOGO ===")
print(f"File trovati: {len(files)}")
print(f"Record totali: {total_records}")
print(f"Durate valide: {valid_records}")
print(f"Durate mancanti/non valide: {missing_duration}")
print(f"Duplicati: {duplicates}")
print(f"File con errori: {len(errors)}")

if total_records:
    percentage = valid_records / total_records * 100
    print(f"Percentuale durate valide: {percentage:.2f}%")

if len(files) != 24:
    print("\nATTENZIONE: attesi 24 file JSON")
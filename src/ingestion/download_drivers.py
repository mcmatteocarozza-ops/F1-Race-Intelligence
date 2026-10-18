import json
import time
from pathlib import Path

import requests

BASE_URL = "https://api.openf1.org/v1/drivers"

RACES_PATH = Path("data/bronze/races_2024.json")
OUTPUT_PATH = Path("data/bronze/drivers_2024.json")


def main():
    with RACES_PATH.open("r", encoding="utf-8") as f:
        races = json.load(f)

    print("\n=== F1 RACE INTELLIGENCE ===")
    print("DOWNLOAD DRIVERS - SEASON 2024\n")

    all_drivers = []
    seen = set()

    with requests.Session() as session:
        for index, race in enumerate(races, start=1):
            session_key = race["session_key"]
            circuit = race["circuit"]

            print(
                f"[{index}/{len(races)}] "
                f"{circuit} - session {session_key}"
            )

            response = session.get(
                BASE_URL,
                params={"session_key": session_key},
                timeout=60
            )

            response.raise_for_status()
            drivers = response.json()

            for driver in drivers:
                # Manteniamo una riga per pilota e sessione.
                key = (
                    driver["session_key"],
                    driver["driver_number"]
                )

                if key not in seen:
                    seen.add(key)
                    all_drivers.append(driver)

            print(f"  Piloti trovati: {len(drivers)}")

            # Pausa per non inviare richieste troppo ravvicinate
            time.sleep(1)

    OUTPUT_PATH.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    with OUTPUT_PATH.open("w", encoding="utf-8") as f:
        json.dump(
            all_drivers,
            f,
            indent=2,
            ensure_ascii=False
        )

    unique_drivers = {
        d["driver_number"] for d in all_drivers
    }

    print("\n=== DOWNLOAD COMPLETATO ===")
    print("Record pilota-sessione:", len(all_drivers))
    print("Piloti distinti:", len(unique_drivers))
    print("File salvato:", OUTPUT_PATH)

    print("\n=== PILOTI ===")
    for driver in sorted(
        all_drivers,
        key=lambda d: d["driver_number"]
    ):
        number = driver["driver_number"]

        if number in unique_drivers:
            print(
                number,
                "-",
                driver.get("full_name"),
                "-",
                driver.get("team_name")
            )
            unique_drivers.remove(number)


if __name__ == "__main__":
    main()
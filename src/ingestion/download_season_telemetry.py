import json
import time
from pathlib import Path

import requests

BASE_DIR = Path(__file__).resolve().parents[2]

DRIVERS_PATH = BASE_DIR / "data/bronze/drivers_2024.json"
OUTPUT_DIR = BASE_DIR / "data/bronze/car_data"

API_URL = "https://api.openf1.org/v1/car_data"

# Prima prova: solo 3 combinazioni pilota-gara.
# Successivamente useremo None per tutta la stagione.
MAX_DOWNLOADS = None

REQUEST_TIMEOUT = 120
MAX_RETRIES = 4
DELAY_SECONDS = 2

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


def download_telemetry(session_key, driver_number):
    output_path = (
        OUTPUT_DIR
        / f"{session_key}_driver_{driver_number}.json"
    )

    # Non riscaricare file già presenti e validi.
    if output_path.exists():
        try:
            with output_path.open(
                "r", encoding="utf-8"
            ) as file:
                existing = json.load(file)

            if isinstance(existing, list) and existing:
                print(f"[SKIP] {output_path.name}")
                return "skipped"

        except (json.JSONDecodeError, OSError):
            pass

    params = {
        "session_key": session_key,
        "driver_number": driver_number,
    }

    for attempt in range(1, MAX_RETRIES + 1):
        try:
            response = requests.get(
                API_URL,
                params=params,
                timeout=REQUEST_TIMEOUT,
            )

            if response.status_code == 429:
                wait = DELAY_SECONDS * attempt * 5
                print(f"[RATE LIMIT] Attendo {wait}s")
                time.sleep(wait)
                continue

            response.raise_for_status()
            data = response.json()

            if not isinstance(data, list):
                raise ValueError(
                    "Risposta API non valida: attesa lista JSON"
                )

            if not data:
                print(
                    f"[EMPTY] Sessione {session_key}, "
                    f"pilota {driver_number}"
                )
                return "empty"

            # Scrittura temporanea per evitare file incompleti.
            temporary_path = output_path.with_suffix(".json.tmp")

            with temporary_path.open(
                "w", encoding="utf-8"
            ) as file:
                json.dump(data, file)

            temporary_path.replace(output_path)

            print(
                f"[OK] {output_path.name}: "
                f"{len(data):,} eventi"
            )

            return "downloaded"

        except (
            requests.RequestException,
            ValueError,
            json.JSONDecodeError,
        ) as exc:
            print(
                f"[ERROR] Tentativo {attempt}/{MAX_RETRIES}: "
                f"{exc}"
            )

            if attempt < MAX_RETRIES:
                time.sleep(DELAY_SECONDS * attempt)

    return "failed"


def main():
    with DRIVERS_PATH.open(
        "r", encoding="utf-8"
    ) as file:
        drivers = json.load(file)

    combinations = sorted({
        (
            int(driver["session_key"]),
            int(driver["driver_number"]),
        )
        for driver in drivers
        if driver.get("session_key") is not None
        and driver.get("driver_number") is not None
    })

    if MAX_DOWNLOADS is not None:
        combinations = combinations[:MAX_DOWNLOADS]

    print("\n=== F1 RACE INTELLIGENCE ===")
    print("2024 TELEMETRY DOWNLOADER\n")
    print(f"Combinazioni da elaborare: {len(combinations)}\n")

    results = {
        "downloaded": 0,
        "skipped": 0,
        "empty": 0,
        "failed": 0,
    }

    for index, (session_key, driver_number) in enumerate(
        combinations, start=1
    ):
        print(
            f"\n[{index}/{len(combinations)}] "
            f"Sessione {session_key} - "
            f"Pilota {driver_number}"
        )

        status = download_telemetry(
            session_key,
            driver_number,
        )

        results[status] += 1

        time.sleep(DELAY_SECONDS)

    print("\n=== RIEPILOGO ===")

    for status, count in results.items():
        print(f"{status}: {count}")


if __name__ == "__main__":
    main()
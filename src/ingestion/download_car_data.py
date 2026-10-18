import json
from pathlib import Path

import requests

BASE_URL = "https://api.openf1.org/v1/car_data"

SESSION_KEY = 9590
DRIVER_NUMBER = 4

OUTPUT_DIR = Path("data/bronze/car_data")
OUTPUT_FILE = OUTPUT_DIR / (
    f"{SESSION_KEY}_driver_{DRIVER_NUMBER}.json"
)


def main():
    print("\n=== F1 RACE INTELLIGENCE ===")
    print("DOWNLOAD CAR DATA\n")

    print("Sessione:", SESSION_KEY)
    print("Pilota:", DRIVER_NUMBER)

    if OUTPUT_FILE.exists():
        print("\nFile già presente:", OUTPUT_FILE)
        print("Download non necessario.")
        return

    params = {
        "session_key": SESSION_KEY,
        "driver_number": DRIVER_NUMBER
    }

    response = requests.get(
        BASE_URL,
        params=params,
        timeout=180
    )

    print("HTTP status:", response.status_code)
    response.raise_for_status()

    data = response.json()

    if not isinstance(data, list) or not data:
        raise ValueError(
            "La risposta API non contiene rilevazioni"
        )

    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    with OUTPUT_FILE.open("w", encoding="utf-8") as f:
        json.dump(
            data,
            f,
            ensure_ascii=False
        )

    print("\n=== DOWNLOAD COMPLETATO ===")
    print("Rilevazioni:", len(data))
    print("File salvato:", OUTPUT_FILE)

    print("\n=== PRIMA RILEVAZIONE ===")
    print(data[0])

    print("\n=== ULTIMA RILEVAZIONE ===")
    print(data[-1])


if __name__ == "__main__":
    main()
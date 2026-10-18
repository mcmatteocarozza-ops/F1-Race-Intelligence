import requests

URL = "https://api.openf1.org/v1/car_data"

params = {
    "session_key": 9590,
    "driver_number": 4,
    "speed>": 300
}

print("\n=== F1 RACE INTELLIGENCE ===")
print("TEST OPENF1 - CAR DATA\n")

response = requests.get(
    URL,
    params=params,
    timeout=60
)

print("HTTP status:", response.status_code)
response.raise_for_status()

data = response.json()

print("Record ricevuti:", len(data))

if data:
    print("\n=== CAMPI DISPONIBILI ===")
    for key, value in data[0].items():
        print(f"{key}: {value}")

    print("\n=== PRIME 3 RILEVAZIONI ===")
    for record in data[:3]:
        print(record)

print("\nTEST COMPLETATO")
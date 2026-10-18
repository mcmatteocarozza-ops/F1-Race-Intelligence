import requests

url = "https://api.openf1.org/v1/sessions"

params = {
    "year": 2024,
    "country_name": "Italy",
    "session_name": "Race"
}

response = requests.get(url, params=params, timeout=30)
response.raise_for_status()

sessions = response.json()

for session in sessions:
    print(
        session["circuit_short_name"],
        "- Session Key:",
        session["session_key"]
    )

import requests
from config.settings import LATITUDE, LONGITUDE


def get_weather():
    url = "https://api.open-meteo.com/v1/forecast"
    params = {
        "latitude": LATITUDE,
        "longitude": LONGITUDE,
        "current": "temperature_2m,relative_humidity_2m,wind_speed_10m,weather_code",
        "timezone": "auto",
    }
    try:
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        current = response.json()["current"]
        code = current["weather_code"]
        descriptions = {
            0: "Sonnig", 1: "Überwiegend sonnig", 2: "Teilweise bewölkt",
            3: "Bewölkt", 45: "Nebelig", 48: "Nebel",
            51: "Leichter Nieselregen", 53: "Nieselregen", 55: "Starker Nieselregen",
            61: "Leichter Regen", 63: "Regen", 65: "Starker Regen",
            71: "Leichter Schnee", 73: "Schnee", 75: "Starker Schnee",
            80: "Regenschauer", 81: "Regenschauer", 82: "Starke Regenschauer",
            95: "Gewitter", 96: "Gewitter mit Hagel", 99: "Starkes Gewitter",
        }
        condition = descriptions.get(code, "Wechselhaft")
        return (
            f"Las Palmas: {condition}\n"
            f"Temperatur: {current['temperature_2m']} °C   "
            f"Luftfeuchtigkeit: {current['relative_humidity_2m']} %\n"
            f"Wind: {current['wind_speed_10m']} km/h"
        )
    except Exception as exc:
        print("Wetterfehler:", exc)
        return "Wetter konnte nicht geladen werden. Internetverbindung prüfen."

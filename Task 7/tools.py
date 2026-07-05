import httpx
from langchain_core.tools import tool

GEOCODE_URL = "https://geocoding-api.open-meteo.com/v1/search"
WEATHER_URL = "https://api.open-meteo.com/v1/forecast"
FX_URL = "https://open.er-api.com/v6/latest/{base}"

WEATHER_CODES = {
    0: "clear sky",
    1: "mainly clear",
    2: "partly cloudy",
    3: "overcast",
    45: "fog",
    48: "freezing fog",
    51: "light drizzle",
    53: "drizzle",
    55: "heavy drizzle",
    61: "light rain",
    63: "rain",
    65: "heavy rain",
    71: "light snow",
    73: "snow",
    75: "heavy snow",
    80: "rain showers",
    81: "rain showers",
    82: "violent rain showers",
    85: "snow showers",
    86: "snow showers",
    95: "thunderstorm",
    96: "thunderstorm with hail",
    99: "thunderstorm with hail",
}


@tool
async def get_weather(city: str) -> str:
    """Get the current weather for a city or place. Use this for any question about
    temperature, conditions, humidity, or wind happening right now."""
    async with httpx.AsyncClient(timeout=10) as client:
        geo = (await client.get(GEOCODE_URL, params={"name": city, "count": 1})).json()
        results = geo.get("results")
        if not results:
            return f"Could not find a place called '{city}'."

        place = results[0]
        label = ", ".join(p for p in [place["name"], place.get("country")] if p)
        wx = (
            await client.get(
                WEATHER_URL,
                params={
                    "latitude": place["latitude"],
                    "longitude": place["longitude"],
                    "current": "temperature_2m,apparent_temperature,relative_humidity_2m,wind_speed_10m,weather_code",
                },
            )
        ).json()

    cur = wx["current"]
    desc = WEATHER_CODES.get(cur["weather_code"], "unknown conditions")
    return (
        f"{label}: {cur['temperature_2m']}°C (feels like {cur['apparent_temperature']}°C), "
        f"{desc}, humidity {cur['relative_humidity_2m']}%, wind {cur['wind_speed_10m']} km/h."
    )


@tool
async def convert_currency(amount: float, base: str, target: str) -> str:
    """Convert an amount from one currency to another using live exchange rates.
    base and target are 3-letter ISO codes such as USD, EUR, GBP, or NGN."""
    base, target = base.upper(), target.upper()
    async with httpx.AsyncClient(timeout=10) as client:
        data = (await client.get(FX_URL.format(base=base))).json()

    if data.get("result") != "success":
        return f"Could not look up rates for '{base}'. Check the currency code."

    rates = data.get("rates", {})
    if target not in rates:
        return f"Could not convert {base} to {target}. Check the currency codes."

    converted = amount * rates[target]
    updated = data.get("time_last_update_utc", "unknown time")
    return f"{amount:.2f} {base} = {converted:.2f} {target} (rate updated {updated})."


TOOLS = [get_weather, convert_currency]
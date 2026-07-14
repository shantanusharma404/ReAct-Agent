"""
weather.py

OpenWeatherMap Weather Tool
Used by the ReAct agent.
"""

import os
import requests

BASE_URL = "https://api.openweathermap.org/data/2.5/weather"


def weather(city: str) -> str:
    """
    Gets the current weather for a given city using the OpenWeatherMap API.

    Example:
        weather("Mumbai")
        weather("London,GB")   # city name + ISO country code disambiguates
                                # cities that share a name across countries
    """

    print("\n[Weather Tool Called]")

    api_key = os.getenv("OPENWEATHER_API_KEY")

    if not api_key:
        return (
            "Weather Error: OPENWEATHER_API_KEY not set. "
            "Add it to your .env file."
        )

    try:

        response = requests.get(
            BASE_URL,
            params={
                "q": city,
                "appid": api_key,
                "units": "metric",
            },
            timeout=10,
        )

        data = response.json()

        if response.status_code != 200:
            message = data.get("message", "Unknown error")
            return f"Weather Error: {message} (city: '{city}')"

        weather_desc = data["weather"][0]["description"]
        temp = data["main"]["temp"]
        feels_like = data["main"]["feels_like"]
        humidity = data["main"]["humidity"]
        wind_speed = data["wind"]["speed"]
        resolved_name = data.get("name", city)

        return (
            f"Weather in {resolved_name}\n"
            f"Condition   : {weather_desc}\n"
            f"Temperature : {temp}\u00b0C (feels like {feels_like}\u00b0C)\n"
            f"Humidity    : {humidity}%\n"
            f"Wind Speed  : {wind_speed} m/s"
        )

    except requests.exceptions.RequestException as e:
        return f"Weather Error: Could not reach OpenWeatherMap ({e})"

    except (KeyError, IndexError) as e:
        return f"Weather Error: Unexpected response format ({e})"

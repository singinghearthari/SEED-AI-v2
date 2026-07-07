import os
import logging
from utils.api_gateway import APIGateway

logger = logging.getLogger("WeatherService")


class WeatherService:
    """
    Production weather service using OpenWeatherMap API.
    Returns live weather data or a structured error if unavailable.
    """

    def __init__(self):
        self.api_key = os.getenv("OPENWEATHER_API_KEY")
        self.base_url = "https://api.openweathermap.org/data/2.5/weather"

    def get_weather(self, location: str) -> dict:
        if not self.api_key:
            logger.warning("OpenWeatherMap API Key not configured.")
            return {"error": "OPENWEATHER_API_KEY not set", "source": "none"}

        try:
            params = {"q": location, "appid": self.api_key, "units": "metric"}
            data = APIGateway.fetch_json(self.base_url, params=params, timeout=5)

            return {
                "rain_1h": data.get("rain", {}).get("1h", 0),
                "humidity": data["main"]["humidity"],
                "temperature": data["main"]["temp"],
                "feels_like": data["main"]["feels_like"],
                "wind_speed": data["wind"]["speed"],
                "description": data["weather"][0]["description"] if data.get("weather") else "Unknown",
                "source": "openweathermap",
            }
        except Exception as e:
            logger.error(f"Weather API call failed: {e}")
            return {"error": f"Weather service unavailable: {str(e)}", "source": "none"}

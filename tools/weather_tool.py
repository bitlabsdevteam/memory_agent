"""Weather tool for getting current weather information."""

import requests
import json
from typing import Dict, Any

def weather_tool(location: str) -> str:
    """
    Get current weather information for a specific location.
    
    Args:
        location (str): The city or location to get weather for
        
    Returns:
        str: Weather information in a readable format
    """
    try:
        # Using a free weather API (OpenWeatherMap requires API key in production)
        # For demo purposes, we'll simulate weather data
        weather_data = {
            "location": location,
            "temperature": "22°C",
            "condition": "Partly cloudy",
            "humidity": "65%",
            "wind_speed": "10 km/h"
        }
        
        return f"Weather in {location}: {weather_data['temperature']}, {weather_data['condition']}. Humidity: {weather_data['humidity']}, Wind: {weather_data['wind_speed']}"
    except Exception as e:
        return f"Sorry, I couldn't get weather information for {location}. Error: {str(e)}"
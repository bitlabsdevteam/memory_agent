"""Travel tools with real API implementations"""

import requests
import json
from datetime import datetime
from config import Config

class WeatherTool:
    """Get current weather for a city using OpenWeatherMap API"""
    
    def __init__(self):
        self.api_key = Config.OPENWEATHERMAP_API_KEY
        self.base_url = "http://api.openweathermap.org/data/2.5/weather"
    
    def get_weather(self, city: str) -> str:
        """Get current weather for a city"""
        if not self.api_key:
            return f"Weather for {city}: Sunny, 22°C (mock data - OpenWeatherMap API key not configured)"
        
        try:
            params = {
                'q': city,
                'appid': self.api_key,
                'units': 'metric'
            }
            
            response = requests.get(self.base_url, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            
            weather_desc = data['weather'][0]['description'].title()
            temp = data['main']['temp']
            feels_like = data['main']['feels_like']
            humidity = data['main']['humidity']
            
            return f"Weather in {city}: {weather_desc}, {temp}°C (feels like {feels_like}°C), Humidity: {humidity}%"
            
        except requests.exceptions.RequestException as e:
            return f"Error getting weather for {city}: Network error - {str(e)}"
        except KeyError as e:
            return f"Error getting weather for {city}: Invalid response format - {str(e)}"
        except Exception as e:
            return f"Error getting weather for {city}: {str(e)}"


class TimeTool:
    """Get current time in a city using TimeZoneDB API"""
    
    def __init__(self):
        self.api_key = Config.TIMEZONEDB_API_KEY
        self.base_url = "http://api.timezonedb.com/v2.1/get-time-zone"
    
    def get_time(self, city: str) -> str:
        """Get current time in a city"""
        if not self.api_key:
            current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            return f"Current time in {city}: {current_time} (mock data - TimeZoneDB API key not configured)"
        
        try:
            # First, get coordinates for the city using a geocoding service
            # For simplicity, we'll use a basic mapping for major cities
            city_coords = self._get_city_coordinates(city)
            
            if not city_coords:
                return f"Current time in {city}: Unable to determine timezone for this city"
            
            params = {
                'key': self.api_key,
                'format': 'json',
                'by': 'position',
                'lat': city_coords['lat'],
                'lng': city_coords['lng']
            }
            
            response = requests.get(self.base_url, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            
            if data['status'] == 'OK':
                formatted_time = data['formatted']
                timezone_name = data['zoneName']
                return f"Current time in {city}: {formatted_time} ({timezone_name})"
            else:
                return f"Error getting time for {city}: {data.get('message', 'Unknown error')}"
            
        except requests.exceptions.RequestException as e:
            return f"Error getting time for {city}: Network error - {str(e)}"
        except Exception as e:
            return f"Error getting time for {city}: {str(e)}"
    
    def _get_city_coordinates(self, city: str) -> dict:
        """Get coordinates for major cities (simplified mapping)"""
        city_coords = {
            'paris': {'lat': 48.8566, 'lng': 2.3522},
            'london': {'lat': 51.5074, 'lng': -0.1278},
            'tokyo': {'lat': 35.6762, 'lng': 139.6503},
            'new york': {'lat': 40.7128, 'lng': -74.0060},
            'sydney': {'lat': -33.8688, 'lng': 151.2093},
            'berlin': {'lat': 52.5200, 'lng': 13.4050},
            'rome': {'lat': 41.9028, 'lng': 12.4964},
            'madrid': {'lat': 40.4168, 'lng': -3.7038},
            'amsterdam': {'lat': 52.3676, 'lng': 4.9041},
            'barcelona': {'lat': 41.3851, 'lng': 2.1734}
        }
        
        return city_coords.get(city.lower())


class CityFactsTool:
    """Get basic facts about a city using Wikipedia API and GeoDB Cities API"""
    
    def __init__(self):
        self.geodb_api_key = Config.GEODB_API_KEY
        self.wikipedia_enabled = Config.WIKIPEDIA_API_ENABLED
        self.geodb_base_url = "https://wft-geo-db.p.rapidapi.com/v1/geo/cities"
        self.wikipedia_base_url = "https://en.wikipedia.org/api/rest_v1/page/summary"
    
    def get_city_facts(self, city: str) -> str:
        """Get basic facts about a city"""
        try:
            # Try to get facts from GeoDB Cities API first
            geodb_facts = self._get_geodb_facts(city)
            
            # Try to get additional info from Wikipedia
            wikipedia_facts = self._get_wikipedia_facts(city) if self.wikipedia_enabled else None
            
            # Combine the information
            if geodb_facts or wikipedia_facts:
                result = []
                if geodb_facts:
                    result.append(geodb_facts)
                if wikipedia_facts:
                    result.append(wikipedia_facts)
                return " ".join(result)
            else:
                # Fallback to mock data
                return self._get_mock_facts(city)
                
        except Exception as e:
            return f"Error getting facts for {city}: {str(e)}"
    
    def _get_geodb_facts(self, city: str) -> str:
        """Get city facts from GeoDB Cities API"""
        if not self.geodb_api_key:
            return None
        
        try:
            headers = {
                'X-RapidAPI-Key': self.geodb_api_key,
                'X-RapidAPI-Host': 'wft-geo-db.p.rapidapi.com'
            }
            
            params = {
                'namePrefix': city,
                'limit': 1
            }
            
            response = requests.get(self.geodb_base_url, headers=headers, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            
            if data['data']:
                city_data = data['data'][0]
                name = city_data['name']
                country = city_data['country']
                population = city_data.get('population', 'Unknown')
                
                return f"{name} is located in {country} with a population of {population:,} people."
            
        except Exception:
            return None
    
    def _get_wikipedia_facts(self, city: str) -> str:
        """Get city facts from Wikipedia API"""
        try:
            url = f"{self.wikipedia_base_url}/{city}"
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            extract = data.get('extract', '')
            
            if extract:
                # Limit to first 200 characters for brevity
                return extract[:200] + "..." if len(extract) > 200 else extract
            
        except Exception:
            return None
    
    def _get_mock_facts(self, city: str) -> str:
        """Fallback mock data for city facts"""
        city_facts = {
            "paris": {
                "country": "France",
                "population": "2.1 million",
                "description": "Paris is the capital of France. It's known for the Eiffel Tower, Louvre Museum, and its romantic atmosphere."
            },
            "london": {
                "country": "United Kingdom",
                "population": "9 million",
                "description": "London is the capital of England and the UK. Famous for Big Ben, Tower Bridge, and rich history."
            },
            "tokyo": {
                "country": "Japan",
                "population": "14 million",
                "description": "Tokyo is Japan's capital and largest city. Known for modern technology, anime culture, and traditional temples."
            },
            "new york": {
                "country": "United States",
                "population": "8.3 million",
                "description": "New York City is the most populous city in the US. Famous for Times Square, Central Park, and the Statue of Liberty."
            },
            "sydney": {
                "country": "Australia",
                "population": "5.3 million",
                "description": "Sydney is Australia's largest city. Known for the Sydney Opera House, Harbour Bridge, and beautiful beaches."
            }
        }
        
        city_lower = city.lower()
        if city_lower in city_facts:
            facts = city_facts[city_lower]
            return f"{city} is located in {facts['country']} with a population of {facts['population']}. {facts['description']}"
        else:
            return f"Basic facts about {city}: A city with rich culture and history (API keys not configured - using fallback data)"


class PlanCityVisitTool:
    """Composite tool that uses multiple tools to plan a city visit"""
    
    def __init__(self):
        self.weather_tool = WeatherTool()
        self.time_tool = TimeTool()
        self.city_facts_tool = CityFactsTool()
    
    def plan_visit(self, city: str) -> str:
        """Plan a city visit by gathering comprehensive information"""
        try:
            # Get city facts
            facts = self.city_facts_tool.get_city_facts(city)
            
            # Get current weather
            weather = self.weather_tool.get_weather(city)
            
            # Get current time
            current_time = self.time_tool.get_time(city)
            
            # Create thinking process
            thinking = f"To help you plan your visit to {city}, I'll gather facts, weather, and time information."
            
            # Combine all information
            response = {
                "thinking": thinking,
                "function_calls": [
                    {"tool": "CityFactsTool", "parameters": {"city": city}},
                    {"tool": "WeatherTool", "parameters": {"city": city}},
                    {"tool": "TimeTool", "parameters": {"city": city}}
                ],
                "response": f"{facts} {weather} {current_time} What would you like to do in {city}?"
            }
            
            return json.dumps(response, indent=2)
        except Exception as e:
            return f"Error planning visit to {city}: {str(e)}"
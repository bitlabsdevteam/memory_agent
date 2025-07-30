"""City visit planning tool for creating travel itineraries."""

from typing import Dict, Any, Optional

def plan_city_visit_tool(city: str, days: int = 3, interests: Optional[str] = None) -> str:
    """
    Create a travel plan for visiting a city.
    
    Args:
        city (str): The city to plan a visit for
        days (int): Number of days for the visit (default: 3)
        interests (str, optional): Specific interests or preferences
        
    Returns:
        str: A detailed travel plan for the city
    """
    try:
        # Simulated travel plans database
        city_plans = {
            "paris": {
                "day1": "Visit Eiffel Tower, Seine River cruise, Champs-Élysées",
                "day2": "Louvre Museum, Notre-Dame Cathedral, Latin Quarter",
                "day3": "Montmartre, Sacré-Cœur, local cafés and bistros",
                "food": "Try croissants, escargot, and French wine",
                "transport": "Use Metro system, very efficient"
            },
            "tokyo": {
                "day1": "Shibuya Crossing, Harajuku, Meiji Shrine",
                "day2": "Tsukiji Fish Market, Imperial Palace, Ginza",
                "day3": "Asakusa Temple, Tokyo Skytree, traditional neighborhoods",
                "food": "Try sushi, ramen, and street food",
                "transport": "JR Pass for trains, very punctual"
            },
            "new york": {
                "day1": "Central Park, Times Square, Broadway show",
                "day2": "Statue of Liberty, 9/11 Memorial, Wall Street",
                "day3": "Brooklyn Bridge, High Line, local neighborhoods",
                "food": "Try pizza, bagels, and diverse cuisine",
                "transport": "Subway system, walking, yellow cabs"
            },
            "london": {
                "day1": "Big Ben, Westminster Abbey, Thames River",
                "day2": "Tower of London, Tower Bridge, Borough Market",
                "day3": "British Museum, Covent Garden, Hyde Park",
                "food": "Try fish and chips, afternoon tea, pub food",
                "transport": "Underground (Tube), buses, walking"
            }
        }
        
        city_lower = city.lower()
        if city_lower in city_plans:
            plan = city_plans[city_lower]
            
            itinerary = f"Here's a {days}-day plan for {city}:\n\n"
            
            # Add day-by-day itinerary based on requested days
            for day in range(1, min(days + 1, 4)):  # Max 3 days in our template
                day_key = f"day{day}"
                if day_key in plan:
                    itinerary += f"Day {day}: {plan[day_key]}\n"
            
            # Add additional days if requested
            if days > 3:
                itinerary += f"\nFor days 4-{days}, consider exploring local neighborhoods, museums, and cultural sites.\n"
            
            # Add food and transport recommendations
            itinerary += f"\nFood recommendations: {plan['food']}\n"
            itinerary += f"Transportation: {plan['transport']}\n"
            
            # Add interests-based recommendations if provided
            if interests:
                itinerary += f"\nBased on your interest in {interests}, I recommend researching specific venues and activities related to this theme.\n"
            
            return itinerary
        else:
            return f"I don't have a specific plan for {city}, but I can help you research popular attractions, local cuisine, and transportation options for your {days}-day visit!"
    except Exception as e:
        return f"Sorry, I couldn't create a plan for {city}. Error: {str(e)}"
"""City facts tool for getting interesting information about cities."""

from typing import Dict, Any

def city_facts_tool(city: str) -> str:
    """
    Get interesting facts and information about a city.
    
    Args:
        city (str): The city to get facts about
        
    Returns:
        str: Interesting facts about the city
    """
    try:
        # Simulated city facts database
        city_facts = {
            "paris": {
                "population": "2.1 million",
                "famous_for": "Eiffel Tower, Louvre Museum, fashion",
                "fun_fact": "Paris has more dogs than children!",
                "best_time_to_visit": "April to June, September to October"
            },
            "tokyo": {
                "population": "13.9 million",
                "famous_for": "Technology, anime, sushi",
                "fun_fact": "Tokyo has the world's busiest train station (Shinjuku)",
                "best_time_to_visit": "March to May, September to November"
            },
            "new york": {
                "population": "8.3 million",
                "famous_for": "Statue of Liberty, Broadway, Central Park",
                "fun_fact": "New York City has over 800 languages spoken!",
                "best_time_to_visit": "April to June, September to November"
            },
            "london": {
                "population": "8.9 million",
                "famous_for": "Big Ben, Tower Bridge, British Museum",
                "fun_fact": "London has over 170 museums!",
                "best_time_to_visit": "May to September"
            }
        }
        
        city_lower = city.lower()
        if city_lower in city_facts:
            facts = city_facts[city_lower]
            return f"Facts about {city}: Population: {facts['population']}, Famous for: {facts['famous_for']}, Fun fact: {facts['fun_fact']}, Best time to visit: {facts['best_time_to_visit']}"
        else:
            return f"I don't have specific facts about {city} in my database, but I'd be happy to help you plan a visit there!"
    except Exception as e:
        return f"Sorry, I couldn't get facts about {city}. Error: {str(e)}"
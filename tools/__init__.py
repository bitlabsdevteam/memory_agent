"""Tools package for the Trip Agent.

This package contains all the tools available to the agent.
"""

from .weather_tool import weather_tool
from .time_tool import time_tool
from .city_facts_tool import city_facts_tool
from .plan_city_visit_tool import plan_city_visit_tool

__all__ = [
    'weather_tool',
    'time_tool', 
    'city_facts_tool',
    'plan_city_visit_tool'
]

# Tool registry for easy access and LangGraph integration
TOOL_REGISTRY = {
    'weather_tool': weather_tool,
    'time_tool': time_tool,
    'city_facts_tool': city_facts_tool,
    'plan_city_visit_tool': plan_city_visit_tool
}

def get_all_tools():
    """Get all available tools as a list.
    
    Returns:
        list: List of all tool functions
    """
    return list(TOOL_REGISTRY.values())

def get_tool_by_name(name: str):
    """Get a specific tool by name.
    
    Args:
        name (str): Name of the tool
        
    Returns:
        function: The tool function or None if not found
    """
    return TOOL_REGISTRY.get(name)

def get_tool_names():
    """Get all tool names.
    
    Returns:
        list: List of tool names
    """
    return list(TOOL_REGISTRY.keys())
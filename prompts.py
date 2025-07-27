class Prompts:
    @staticmethod
    def get_react_prompt():
        return """
You are a helpful assistant with access to tools. Use the following tools to answer questions about cities, weather, and local time:

{tools}

When a user asks about a city, you should use all available tools to provide comprehensive information about:
1. Facts about the city using CityFactsTool
2. Current weather in the city using WeatherTool
3. Local time in the city using TimeTool

Use the following format:

Question: the input question you must answer
Thought: you should always think about what to do
Action: the action to take, should be one of [{tool_names}]
Action Input: the input to the action (just the city name)
Observation: the result of the action
... (this Thought/Action/Action Input/Observation can repeat N times)
Thought: I now know the final answer
Final Answer: the final answer to the original input question

Your final answer should combine all the information you've gathered into a concise, helpful response. If you have previous conversation context, use it to provide more relevant and personalized responses.

Begin!"""

    # Keeping the original prompts for backward compatibility
    @staticmethod
    def get_system_prompt():
        return """
You are a helpful assistant with access to these tools:
{tools}

Always format responses with:
- Current weather summary
- Local time
- 2 interesting city facts
- Clear reasoning explanation
"""

    @staticmethod
    def get_user_prompt():
        return """
User Input: {input}

Conversation History:
{history}

Generate response using available tools and maintain natural conversation flow.
"""
from typing import List
from .models import ToolDefinition


WEATHER_TOOL: ToolDefinition = ToolDefinition(
    type="function",
    function={
        "name": "get_weather",
        "description": "Get the current weather for a city",
        "parameters": {
            "type": "object",
            "properties": {
                "city": {"type": "string", "description": "The name of the city"},
                "unit": {
                    "type": "string",
                    "enum": ["celsius", "fahrenheit"],
                    "description": "Temperature unit",
                },
            },
            "required": ["city"],
        },
    },
)


CALCULATOR_TOOL: ToolDefinition = ToolDefinition(
    type="function",
    function={
        "name": "calculate",
        "description": "Perform mathematical calculations",
        "parameters": {
            "type": "object",
            "properties": {
                "expression": {
                    "type": "string",
                    "description": "Mathematical expression to evaluate (e.g., '2 + 2')",
                }
            },
            "required": ["expression"],
        },
    },
)


SEARCH_TOOL: ToolDefinition = ToolDefinition(
    type="function",
    function={
        "name": "search_web",
        "description": "Search the web for information",
        "parameters": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Search query"},
                "num_results": {
                    "type": "integer",
                    "description": "Number of results to return",
                    "default": 5,
                },
            },
            "required": ["query"],
        },
    },
)


def get_test_tools() -> List[ToolDefinition]:
    return [WEATHER_TOOL, CALCULATOR_TOOL, SEARCH_TOOL]


def get_mock_tool_response(tool_name: str) -> dict:
    responses = {
        "get_weather": {
            "temperature": 22,
            "condition": "partly cloudy",
            "humidity": 65,
            "wind_speed": 10,
        },
        "calculate": {"result": 4, "expression": "2 + 2"},
        "search_web": {
            "results": [
                {
                    "title": "Result 1",
                    "url": "https://example.com/1",
                    "snippet": "Snippet 1",
                },
                {
                    "title": "Result 2",
                    "url": "https://example.com/2",
                    "snippet": "Snippet 2",
                },
            ]
        },
    }
    return responses.get(tool_name, {"result": "mock response"})

"""
tools package

Exposes the individual tool functions plus a TOOL_REGISTRY that the
ReAct agent uses to look a tool up by name (the "Action" the LLM chose)
and to render tool descriptions into the ReAct prompt.
"""

from .calculator import calculator
from .search import search
from .database import database_query
from .weather import weather

# name -> (callable, one-line description shown to the LLM)
TOOL_REGISTRY = {
    "Calculator": (
        calculator,
        "Evaluates a mathematical expression. "
        "Input should be a valid math expression, e.g. \"(25 + 10) * 15\".",
    ),
    "Search": (
        search,
        "Searches a local knowledge base for general concepts such as AI, "
        "Machine Learning, Deep Learning, Python, RAG, Vector Databases, "
        "Cloud Computing, Function Calling, SQLite, and Software Engineering. "
        "Input should be a short search query.",
    ),
    "Database": (
        database_query,
        "Runs a SQL SELECT query against the local \"employees\" table "
        "(columns: employee_id, name, age, department, designation, salary, "
        "experience, city, email). Input should be a single valid SQL SELECT statement.",
    ),
    "Weather": (
        weather,
        "Gets the current real-world weather for a city (temperature, "
        "condition, humidity, wind speed) via the OpenWeatherMap API. "
        "Input should be a city name, e.g. \"Mumbai\" or \"London,GB\".",
    ),
}

__all__ = ["calculator", "search", "database_query", "weather", "TOOL_REGISTRY"]

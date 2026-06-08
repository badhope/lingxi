"""CrewAI crew definitions.

Each crew wraps a set of agents and tasks. The two crews that are actually
invoked by `routers/api.py` are `data_analysis` and `knowledge_team`.
"""

from .data_analysis import create_data_analysis_crew, run_data_analysis
from .knowledge_team import create_knowledge_team, run_knowledge_query

__version__ = "0.1.0"

__all__ = [
    "create_data_analysis_crew",
    "run_data_analysis",
    "create_knowledge_team",
    "run_knowledge_query",
]

"""CrewAI agent factories.

The factory functions live in `agents.base_agent`. Concrete agent
constructors (researcher / analyst / writer / knowledge manager) are also
exported from `base_agent`.
"""

from .base_agent import (
    create_analyst_agent,
    create_base_agent,
    create_knowledge_manager_agent,
    create_researcher_agent,
    create_writer_agent,
    get_llm,
)

__version__ = "0.1.0"

__all__ = [
    "get_llm",
    "create_base_agent",
    "create_researcher_agent",
    "create_analyst_agent",
    "create_writer_agent",
    "create_knowledge_manager_agent",
]

"""Base CrewAI agent factory.

Wraps `crewai.Agent` and pulls LLM config from `config.settings`.
"""
from crewai import Agent
from langchain_openai import ChatOpenAI
from typing import List, Optional
from config import settings


def get_llm() -> ChatOpenAI:
    """Get the default LLM instance."""
    return ChatOpenAI(
        model=settings.default_model,
        temperature=settings.default_temperature,
        api_key=settings.openai_api_key or "dummy-key",
        base_url=settings.openai_base_url
    )


def create_base_agent(
    role: str,
    goal: str,
    backstory: str,
    tools: Optional[List] = None,
    llm: Optional[ChatOpenAI] = None,
    allow_delegation: bool = False
) -> Agent:
    """Create a base CrewAI Agent.

    Args:
        role: Agent role name.
        goal: What the agent is trying to achieve.
        backstory: Free-form backstory for the agent prompt.
        tools: Optional list of tools the agent can call.
        llm: Optional ChatOpenAI override. Defaults to `get_llm()`.
        allow_delegation: Whether this agent may hand off to others.

    Returns:
        A configured `crewai.Agent`.
    """
    if tools is None:
        tools = []
    
    if llm is None:
        llm = get_llm()
    
    return Agent(
        role=role,
        goal=goal,
        backstory=backstory,
        llm=llm,
        tools=tools,
        verbose=True,
        allow_delegation=allow_delegation
    )


def create_researcher_agent(llm: Optional[ChatOpenAI] = None) -> Agent:
    """Researcher: gathers background information for a user question."""
    if llm is None:
        llm = get_llm()

    return create_base_agent(
        role="Researcher",
        goal="Gather the background information needed to answer the user's question.",
        backstory=(
            "You are a researcher. Find relevant facts, summarize sources, and "
            "hand off a clean brief to the analyst."
        ),
        llm=llm,
        tools=[]
    )


def create_analyst_agent(llm: Optional[ChatOpenAI] = None) -> Agent:
    """Analyst: turns the research brief into structured findings."""
    if llm is None:
        llm = get_llm()

    return create_base_agent(
        role="Analyst",
        goal="Turn the research brief into a structured analysis with key findings.",
        backstory=(
            "You are an analyst. Look for patterns, compare options, and call out "
            "trade-offs. Output structured findings the writer can use."
        ),
        llm=llm,
        tools=[]
    )


def create_writer_agent(llm: Optional[ChatOpenAI] = None) -> Agent:
    """Writer: produces the final readable report."""
    if llm is None:
        llm = get_llm()

    return create_base_agent(
        role="Writer",
        goal="Turn the analyst's findings into a clear, well-structured report.",
        backstory=(
            "You are a writer. Take structured findings and produce a short, "
            "readable report. Lead with the conclusion."
        ),
        llm=llm,
        tools=[]
    )


def create_knowledge_manager_agent(llm: Optional[ChatOpenAI] = None) -> Agent:
    """Knowledge manager: retrieves from the KB and answers a user question."""
    if llm is None:
        llm = get_llm()

    return create_base_agent(
        role="Knowledge Manager",
        goal="Find the most relevant chunks in the knowledge base and answer the user.",
        backstory=(
            "You are a knowledge-base manager. Pick the chunks that match the "
            "question, quote them when useful, and admit when the KB does not "
            "contain the answer."
        ),
        llm=llm,
        tools=[]
    )

"""Knowledge team crew (1 agent: knowledge manager)."""
from crewai import Task, Crew, Process
from langchain_openai import ChatOpenAI
from agents.base_agent import create_knowledge_manager_agent, get_llm


def create_knowledge_team(llm: ChatOpenAI | None = None) -> Crew:
    """Build a 1-agent crew that retrieves from the KB and answers."""
    if llm is None:
        llm = get_llm()

    knowledge_manager = create_knowledge_manager_agent(llm)

    search_task = Task(
        description=(
            "Answer the question below using the knowledge base.\n"
            "Question: {question}\n\n"
            "Include:\n"
            "1. The direct answer\n"
            "2. The relevant chunks you used\n"
            "3. The source for each chunk"
        ),
        expected_output="Answer with sources.",
        agent=knowledge_manager,
    )

    return Crew(
        name="Knowledge Team",
        agents=[knowledge_manager],
        tasks=[search_task],
        process=Process.sequential,
        verbose=True,
    )


def run_knowledge_query(question: str, llm: ChatOpenAI | None = None) -> str:
    """Kick off the knowledge crew and return the answer text."""
    crew = create_knowledge_team(llm)
    result = crew.kickoff(inputs={"question": question})
    return str(result) if result else ""


__all__ = ["create_knowledge_team", "run_knowledge_query"]

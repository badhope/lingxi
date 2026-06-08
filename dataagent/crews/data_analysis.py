"""Data analysis crew (3 agents: researcher -> analyst -> writer)."""
from crewai import Task, Crew, Process
from langchain_openai import ChatOpenAI
from agents.base_agent import (
    create_analyst_agent,
    create_researcher_agent,
    create_writer_agent,
    get_llm,
)


def create_data_analysis_crew(llm: ChatOpenAI | None = None) -> Crew:
    """Build a 3-agent crew that researches, analyses, and writes a report."""
    if llm is None:
        llm = get_llm()

    researcher = create_researcher_agent(llm)
    analyst = create_analyst_agent(llm)
    writer = create_writer_agent(llm)

    research_task = Task(
        description=(
            "Research the following question.\n"
            "Question: {query}\n\n"
            "Collect background information, key data points, and any relevant "
            "examples. Hand off a structured brief."
        ),
        expected_output="Structured research brief with key findings.",
        agent=researcher,
    )

    analysis_task = Task(
        description=(
            "Take the research brief and produce an analysis:\n"
            "- Key trends and patterns\n"
            "- Data-driven insights\n"
            "- Risks or open questions\n"
            "- Actionable recommendations"
        ),
        expected_output="Structured analysis with insights and recommendations.",
        agent=analyst,
    )

    report_task = Task(
        description=(
            "Take the analysis and write the final report.\n"
            "Include: executive summary, detailed analysis, conclusions, and "
            "recommendations. Lead with the conclusion."
        ),
        expected_output="Final report suitable for a general audience.",
        agent=writer,
    )

    return Crew(
        name="Data Analysis Team",
        agents=[researcher, analyst, writer],
        tasks=[research_task, analysis_task, report_task],
        process=Process.sequential,
        verbose=True,
    )


def run_data_analysis(query: str, llm: ChatOpenAI | None = None) -> str:
    """Kick off the analysis crew and return the result text."""
    crew = create_data_analysis_crew(llm)
    result = crew.kickoff(inputs={"query": query})
    return str(result) if result else ""


__all__ = ["create_data_analysis_crew", "run_data_analysis"]

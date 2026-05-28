"""
知识库团队 - Knowledge Team Crew
基于 CrewAI 框架的知识管理团队
"""
from crewai import Task, Crew, Process
from langchain_openai import ChatOpenAI
from agents.base_agent import (
    create_knowledge_agent,
    get_llm
)


def create_knowledge_crew(llm: ChatOpenAI | None = None) -> Crew:
    """
    创建知识库管理团队
    
    Args:
        llm: LLM实例，可选
    
    Returns:
        配置好的 Crew 实例
    """
    if llm is None:
        llm = get_llm()
    
    # 创建Agent
    knowledge_manager = create_knowledge_agent(llm)
    
    # 定义任务
    search_task = Task(
        description="""回答以下问题：{question}
请从知识库中检索相关信息，提供准确的答案。
包括：
1. 核心答案
2. 相关文档
3. 参考来源""",
        expected_output="准确的答案，包含参考来源",
        agent=knowledge_manager
    )
    
    # 组建团队
    crew = Crew(
        name="知识库管理团队",
        agents=[knowledge_manager],
        tasks=[search_task],
        process=Process.sequential,
        verbose=True
    )
    
    return crew


def run_knowledge_query(question: str, llm: ChatOpenAI | None = None) -> str:
    """
    运行知识库查询
    
    Args:
        question: 查询问题
        llm: LLM实例，可选
    
    Returns:
        查询结果
    """
    crew = create_knowledge_crew(llm)
    result = crew.kickoff(inputs={"question": question})
    return str(result) if result else ""

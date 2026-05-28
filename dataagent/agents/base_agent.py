"""
基础Agent定义 - 角色驱动的AI智能体
基于 CrewAI 框架
"""
from crewai import Agent
from langchain_openai import ChatOpenAI
from typing import List, Optional
from config import settings


def get_llm() -> ChatOpenAI:
    """获取默认LLM实例"""
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
    """
    创建基础Agent
    
    Args:
        role: 角色名称
        goal: 目标
        backstory: 背景故事
        tools: 工具列表
        llm: LLM实例
        allow_delegation: 是否允许委托任务
    
    Returns:
        Agent 实例
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
    """创建研究员Agent"""
    if llm is None:
        llm = get_llm()
    
    return create_base_agent(
        role="高级数据研究员",
        goal="深入研究用户问题，收集和整理相关数据资料",
        backstory="""你是一位资深数据研究员，有10年数据分析经验。
你擅长从各种数据源中提取有价值的信息，能够快速定位关键信息。
你熟悉多种搜索和数据收集工具，能够高效完成研究任务。""",
        llm=llm,
        tools=[]
    )


def create_analyst_agent(llm: Optional[ChatOpenAI] = None) -> Agent:
    """创建分析师Agent"""
    if llm is None:
        llm = get_llm()
    
    return create_base_agent(
        role="数据分析师",
        goal="分析研究数据，生成深度洞察和可视化建议",
        backstory="""你是一位专业数据分析师，精通统计学和数据可视化。
你能够将复杂数据转化为简单易懂的结论。
你擅长发现数据中的模式和趋势，并提供可操作的建议。""",
        llm=llm,
        tools=[]
    )


def create_writer_agent(llm: Optional[ChatOpenAI] = None) -> Agent:
    """创建报告撰写Agent"""
    if llm is None:
        llm = get_llm()
    
    return create_base_agent(
        role="报告专家",
        goal="将分析结果转化为专业、清晰的报告",
        backstory="""你是一位出色的技术作家，擅长将复杂的技术分析转化为可读性强的报告。
你擅长用图表、表格和文字结合的方式展示数据洞见。
你的报告结构清晰，重点突出，适合不同层次的读者。""",
        llm=llm,
        tools=[]
    )


def create_knowledge_agent(llm: Optional[ChatOpenAI] = None) -> Agent:
    """创建知识库管理Agent"""
    if llm is None:
        llm = get_llm()
    
    return create_base_agent(
        role="知识库管理员",
        goal="管理和检索知识库内容，提供相关知识支持",
        backstory="""你负责组织和维护知识库系统。
你擅长快速定位相关文档和知识，能够将新知识有效整合到现有知识体系中。
你对知识的分类和检索有丰富的经验。""",
        llm=llm,
        tools=[]
    )

"""
数据分析团队 - Data Analysis Crew
基于 CrewAI 框架的协作研究团队
"""
from crewai import Task, Crew, Process
from langchain_openai import ChatOpenAI
from agents.base_agent import (
    create_researcher_agent,
    create_analyst_agent,
    create_writer_agent,
    get_llm
)


def create_data_analysis_crew(llm: ChatOpenAI | None = None) -> Crew:
    """
    创建数据分析团队
    
    Args:
        llm: LLM实例，可选
    
    Returns:
        配置好的 Crew 实例
    """
    if llm is None:
        llm = get_llm()
    
    # 创建Agent
    researcher = create_researcher_agent(llm)
    analyst = create_analyst_agent(llm)
    writer = create_writer_agent(llm)
    
    # 定义任务
    research_task = Task(
        description="""研究以下问题：{query}
请收集相关信息、数据和案例，整理成结构化的研究报告。
包括：
1. 问题背景
2. 关键数据点
3. 相关案例
4. 参考资料来源""",
        expected_output="详细的研究报告，包含关键数据和发现",
        agent=researcher
    )
    
    analysis_task = Task(
        description="""基于研究报告进行深入分析：
1. 识别关键趋势和模式
2. 提供数据洞察
3. 发现潜在问题
4. 建议可视化方式
5. 提出改进建议""",
        expected_output="完整的分析报告，包含洞见和建议",
        agent=analyst
    )
    
    report_task = Task(
        description="""将研究和分析结果整合成最终报告：
1. 执行摘要
2. 详细分析
3. 结论和建议
4. 可视化图表描述（如果需要）
5. 附录和参考资料""",
        expected_output="专业的最终报告，格式清晰，适合管理层阅读",
        agent=writer
    )
    
    # 组建团队
    crew = Crew(
        name="数据分析团队",
        agents=[researcher, analyst, writer],
        tasks=[research_task, analysis_task, report_task],
        process=Process.sequential,
        verbose=True
    )
    
    return crew


def run_data_analysis(query: str, llm: ChatOpenAI | None = None) -> str:
    """
    运行数据分析流程
    
    Args:
        query: 分析问题
        llm: LLM实例，可选
    
    Returns:
        分析结果
    """
    crew = create_data_analysis_crew(llm)
    result = crew.kickoff(inputs={"query": query})
    return str(result) if result else ""

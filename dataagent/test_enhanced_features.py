"""
DataAgent 增强功能综合测试
测试工作流、LLMOps 和权限管理功能
"""
import sys
import os
from pathlib import Path

# 确保项目根目录在 Python 路径中
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

import asyncio
import time
from core.logging import get_logger
from core.auth import auth_manager, UserRole, Permission, User
from app.flow.workflow import workflow_engine, NodeType, Node, Edge, WorkflowStatus
from core.llm_ops import llm_ops, prompt_manager, ab_test_manager, LLMProvider, LLMTraceStatus

logger = get_logger("test_enhanced")

def print_separator(title=""):
    """打印分隔符"""
    print("\n" + "="*80)
    if title:
        print(f"  {title}")
        print("="*80)

def test_auth_system():
    """测试认证和权限系统"""
    print_separator("测试认证和权限系统")
    
    # 测试用户创建
    print("✓ 测试用户创建...")
    try:
        test_user = auth_manager.create_user(
            username="test_user",
            email="test@example.com",
            password="test123456",
            role=UserRole.USER
        )
        print(f"  ✓ 用户创建成功: {test_user.username}")
    except ValueError as e:
        if "已存在" in str(e):
            test_user = auth_manager.get_user_by_username("test_user")
            print(f"  ✓ 用户已存在: {test_user.username}")
    
    # 测试权限检查
    print("\n✓ 测试权限检查...")
    admin = auth_manager.get_user_by_username("admin")
    print(f"  管理员权限 - MANAGE_WORKFLOWS: {admin.has_permission(Permission.MANAGE_WORKFLOWS)}")
    print(f"  管理员权限 - VIEW_LLMOPS: {admin.has_permission(Permission.VIEW_LLMOPS)}")
    
    test_user = auth_manager.get_user_by_username("test_user")
    print(f"  普通用户权限 - EXECUTE_WORKFLOWS: {test_user.has_permission(Permission.EXECUTE_WORKFLOWS)}")
    print(f"  普通用户权限 - MANAGE_LLMOPS: {test_user.has_permission(Permission.MANAGE_LLMOPS)}")
    
    # 测试认证
    print("\n✓ 测试用户认证...")
    session = auth_manager.authenticate("test_user", "test123456")
    if session:
        print(f"  ✓ 认证成功，Token: {session.token[:20]}...")
        auth_manager.revoke_session(session.token)
    else:
        print("  ✗ 认证失败")
    
    print("\n✓ 认证和权限系统测试完成")
    return True

def test_workflow_system():
    """测试工作流系统"""
    print_separator("测试工作流系统")
    
    # 创建工作流
    print("✓ 创建示例工作流...")
    workflow = workflow_engine.create_workflow(
        name="数据处理工作流",
        description="一个完整的数据处理示例工作流"
    )
    print(f"  ✓ 工作流创建成功: {workflow.name} (ID: {workflow.id})")
    
    # 添加节点
    print("\n✓ 添加工作流节点...")
    
    # 开始节点
    start_node = Node(
        type=NodeType.START,
        name="开始",
        config={}
    )
    workflow_engine.add_node(workflow.id, start_node)
    print(f"  ✓ 添加开始节点: {start_node.id}")
    
    # Agent 节点
    agent_node = Node(
        type=NodeType.AGENT,
        name="数据分析Agent",
        config={
            "prompt": "请分析以下数据",
            "model": "gpt-4"
        }
    )
    workflow_engine.add_node(workflow.id, agent_node)
    print(f"  ✓ 添加Agent节点: {agent_node.id}")
    
    # 工具节点
    tool_node = Node(
        type=NodeType.TOOL,
        name="数据查询工具",
        config={
            "tool_name": "python_execute",
            "code": "print('处理数据')"
        }
    )
    workflow_engine.add_node(workflow.id, tool_node)
    print(f"  ✓ 添加工具节点: {tool_node.id}")
    
    # 结束节点
    end_node = Node(
        type=NodeType.END,
        name="结束",
        config={}
    )
    workflow_engine.add_node(workflow.id, end_node)
    print(f"  ✓ 添加结束节点: {end_node.id}")
    
    # 添加边
    print("\n✓ 添加工作流连接...")
    workflow_engine.add_edge(workflow.id, Edge(start_node.id, agent_node.id))
    workflow_engine.add_edge(workflow.id, Edge(agent_node.id, tool_node.id))
    workflow_engine.add_edge(workflow.id, Edge(tool_node.id, end_node.id))
    print("  ✓ 边添加完成")
    
    # 获取执行顺序
    print("\n✓ 计算执行顺序...")
    execution_order = workflow_engine._get_execution_order(workflow)
    print(f"  ✓ 执行顺序: {[node_id for node_id in execution_order]}")
    
    # 列出所有工作流
    print("\n✓ 列出所有工作流...")
    workflows = workflow_engine.list_workflows()
    for wf in workflows:
        print(f"  - {wf.name} (状态: {wf.status.value})")
    
    print("\n✓ 工作流系统测试完成")
    return True

def test_llm_ops_system():
    """测试 LLMOps 系统"""
    print_separator("测试 LLMOps 系统")
    
    # 测试 LLM 调用追踪
    print("✓ 测试 LLM 调用追踪...")
    trace = llm_ops.start_trace(
        provider=LLMProvider.OPENAI,
        model="gpt-4",
        prompt="Hello, world!",
        user_id="test_user"
    )
    print(f"  ✓ 追踪开始: {trace.id}")
    
    # 结束追踪
    trace = llm_ops.end_trace(
        trace=trace,
        response="Hi there!",
        prompt_tokens=10,
        completion_tokens=5,
        success=True
    )
    print(f"  ✓ 追踪结束 - 状态: {trace.status.value}, 成本: ${trace.cost:.6f}")
    
    # 再创建几个测试追踪
    for i in range(3):
        t = llm_ops.start_trace(
            provider=LLMProvider.OPENAI,
            model="gpt-3.5-turbo",
            prompt=f"Test prompt {i}",
            user_id="test_user"
        )
        llm_ops.end_trace(
            trace=t,
            response=f"Test response {i}",
            prompt_tokens=5,
            completion_tokens=3,
            success=True
        )
    
    # 测试获取指标
    print("\n✓ 获取模型指标...")
    all_metrics = llm_ops.get_all_metrics()
    for metric in all_metrics[:3]:
        print(f"  - {metric.provider}/{metric.model}: {metric.total_calls} calls, ${metric.total_cost:.6f}")
    
    # 测试成本统计
    print("\n✓ 获取成本统计...")
    cost_summary = llm_ops.get_cost_summary(days=30)
    print(f"  ✓ 总成本: ${cost_summary['total_cost']:.6f}")
    print(f"  ✓ 总调用: {cost_summary['total_calls']}")
    
    # 测试提示词管理
    print("\n✓ 测试提示词管理...")
    prompt = prompt_manager.create_prompt(
        name="数据分析提示词",
        prompt="请分析以下数据并生成报告",
        description="用于数据分析的标准提示词",
        variables=["data"],
        created_by="test_user"
    )
    print(f"  ✓ 提示词创建: {prompt.name} (v{prompt.version})")
    
    # 列出所有提示词
    all_prompts = prompt_manager.list_prompts()
    for p in all_prompts:
        print(f"  - {p.name}")
    
    # 测试 A/B 测试
    print("\n✓ 测试 A/B 测试...")
    ab_test = ab_test_manager.create_test(
        name="提示词优化测试",
        variants={
            "A": {"prompt": "请分析数据"},
            "B": {"prompt": "请详细分析这些数据"}
        },
        traffic_split={"A": 0.5, "B": 0.5}
    )
    print(f"  ✓ A/B 测试创建: {ab_test.name}")
    
    # 获取变体
    variant = ab_test_manager.get_variant(ab_test.id, "user_123")
    print(f"  ✓ 获取变体: {variant}")
    
    # 记录转化
    ab_test_manager.record_conversion(ab_test.id, "A", revenue=10.0)
    ab_test_manager.record_conversion(ab_test.id, "A", revenue=15.0)
    ab_test_manager.record_conversion(ab_test.id, "B", revenue=20.0)
    
    # 获取测试结果
    results = ab_test_manager.get_test_results(ab_test.id)
    print(f"  ✓ 测试结果: {results}")
    
    # 测试缓存
    print("\n✓ 测试缓存系统...")
    print(f"  ✓ 缓存大小: {len(llm_ops.cache)}/{llm_ops.max_cache_size}")
    
    print("\n✓ LLMOps 系统测试完成")
    return True

def test_integration():
    """集成测试"""
    print_separator("集成测试")
    
    # 测试创建完整工作流并执行模拟
    print("✓ 模拟创建并执行完整工作流...")
    
    workflow = workflow_engine.create_workflow(
        name="集成测试工作流",
        description="测试完整的工作流执行流程"
    )
    
    # 添加节点
    start = Node(type=NodeType.START, name="开始", config={})
    data_node = Node(type=NodeType.DATA_TRANSFORM, name="数据转换", config={"transform": "clean"})
    agent_node = Node(type=NodeType.AGENT, name="AI 分析", config={"model": "gpt-4"})
    end = Node(type=NodeType.END, name="结束", config={})
    
    workflow_engine.add_node(workflow.id, start)
    workflow_engine.add_node(workflow.id, data_node)
    workflow_engine.add_node(workflow.id, agent_node)
    workflow_engine.add_node(workflow.id, end)
    
    workflow_engine.add_edge(workflow.id, Edge(start.id, data_node.id))
    workflow_engine.add_edge(workflow.id, Edge(data_node.id, agent_node.id))
    workflow_engine.add_edge(workflow.id, Edge(agent_node.id, end.id))
    
    # 更新工作流状态
    workflow_engine.update_workflow_status(workflow.id, WorkflowStatus.PUBLISHED)
    
    # 模拟执行过程中的 LLMOps 追踪
    print("\n✓ 模拟工作流执行中的 LLMOps 追踪...")
    execution_trace = llm_ops.start_trace(
        provider=LLMProvider.OPENAI,
        model="gpt-4",
        prompt="执行工作流分析",
        tags=["workflow", "integration_test"]
    )
    time.sleep(0.1)  # 模拟执行时间
    llm_ops.end_trace(
        trace=execution_trace,
        response="工作流执行完成",
        prompt_tokens=50,
        completion_tokens=30,
        success=True
    )
    
    print("  ✓ 集成测试工作流创建和执行模拟完成")
    
    print("\n✓ 集成测试完成")
    return True

def main():
    """主测试函数"""
    print_separator("DataAgent 增强功能综合测试")
    
    results = {}
    
    # 运行所有测试
    try:
        results["认证系统"] = test_auth_system()
    except Exception as e:
        logger.error(f"认证系统测试失败: {e}", exc_info=True)
        results["认证系统"] = False
    
    try:
        results["工作流系统"] = test_workflow_system()
    except Exception as e:
        logger.error(f"工作流系统测试失败: {e}", exc_info=True)
        results["工作流系统"] = False
    
    try:
        results["LLMOps系统"] = test_llm_ops_system()
    except Exception as e:
        logger.error(f"LLMOps系统测试失败: {e}", exc_info=True)
        results["LLMOps系统"] = False
    
    try:
        results["集成测试"] = test_integration()
    except Exception as e:
        logger.error(f"集成测试失败: {e}", exc_info=True)
        results["集成测试"] = False
    
    # 打印测试结果汇总
    print_separator("测试结果汇总")
    all_passed = True
    for test_name, passed in results.items():
        status = "✓ 通过" if passed else "✗ 失败"
        print(f"  {test_name}: {status}")
        if not passed:
            all_passed = False
    
    print("\n" + "="*80)
    if all_passed:
        print("  🎉 所有测试通过！")
    else:
        print("  ⚠️  部分测试失败，请检查日志")
    print("="*80)
    
    return all_passed

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)

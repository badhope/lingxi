"""
DataAgent - CLI 命令行界面
完整的命令行工具，支持交互式操作和批量处理
"""
import sys
import os
import json
import asyncio
import argparse
from pathlib import Path
from typing import Optional, List, Dict, Any
from datetime import datetime

# 添加项目路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from core.logging import get_logger
from core.workspace import get_workspace_manager, WorkspaceFileType
from core.skills import get_skills_engine
from core.skill_hub import get_skill_hub_manager
from core.memory import get_memory_engine
from core.heartbeat import get_heartbeat_engine
from core.orchestrator import get_llm_router, get_agent_orchestrator
from core.gateway import get_gateway

logger = get_logger("cli")


class Colors:
    """ANSI 颜色码"""
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'


def color_print(text: str, color: str = Colors.ENDC):
    """带颜色的打印"""
    print(f"{color}{text}{Colors.ENDC}")


class DataAgentCLI:
    """
    DataAgent 命令行界面
    """
    
    def __init__(self):
        self.workspace = None
        self.skills_engine = None
        self.skill_hub = None
        self.memory_engine = None
        self.heartbeat = None
        self.llm_router = None
        self.orchestrator = None
        self.gateway = None
        
        self._init_components()
    
    def _init_components(self):
        """初始化组件"""
        color_print("初始化 DataAgent...", Colors.OKBLUE)
        
        try:
            self.workspace = get_workspace_manager()
            color_print("✓ 工作区", Colors.OKGREEN)
        except Exception as e:
            color_print(f"✗ 工作区: {e}", Colors.FAIL)
        
        try:
            self.skills_engine = get_skills_engine()
            color_print("✓ 技能引擎", Colors.OKGREEN)
        except Exception as e:
            color_print(f"✗ 技能引擎: {e}", Colors.FAIL)
        
        try:
            self.skill_hub = get_skill_hub_manager()
            color_print("✓ 技能仓库", Colors.OKGREEN)
        except Exception as e:
            color_print(f"✗ 技能仓库: {e}", Colors.FAIL)
        
        try:
            self.memory_engine = get_memory_engine()
            color_print("✓ 记忆引擎", Colors.OKGREEN)
        except Exception as e:
            color_print(f"✗ 记忆引擎: {e}", Colors.FAIL)
        
        try:
            self.heartbeat = get_heartbeat_engine()
            color_print("✓ 心跳引擎", Colors.OKGREEN)
        except Exception as e:
            color_print(f"✗ 心跳引擎: {e}", Colors.FAIL)
        
        try:
            self.llm_router = get_llm_router()
            color_print("✓ LLM 路由", Colors.OKGREEN)
        except Exception as e:
            color_print(f"✗ LLM 路由: {e}", Colors.FAIL)
        
        try:
            self.orchestrator = get_agent_orchestrator()
            color_print("✓ Agent 编排", Colors.OKGREEN)
        except Exception as e:
            color_print(f"✗ Agent 编排: {e}", Colors.FAIL)
        
        try:
            self.gateway = get_gateway()
            color_print("✓ Gateway", Colors.OKGREEN)
        except Exception as e:
            color_print(f"✗ Gateway: {e}", Colors.FAIL)
        
        print()
    
    def show_banner(self):
        """显示横幅"""
        print()
        color_print("=" * 60, Colors.HEADER)
        color_print("  DataAgent CLI - 智能助手命令行工具", Colors.BOLD)
        color_print("  OpenClaw 功能完整集成版", Colors.OKCYAN)
        color_print("=" * 60, Colors.HEADER)
        print()
    
    def show_help(self):
        """显示帮助信息"""
        print()
        color_print("可用命令:", Colors.BOLD)
        print()
        print("  工作区管理:")
        print("    workspace list      - 列出工作区文件")
        print("    workspace show     - 显示当前配置")
        print("    workspace update   - 更新工作区配置")
        print()
        print("  技能管理:")
        print("    skills list        - 列出所有技能")
        print("    skills search      - 搜索技能仓库")
        print("    skills install     - 安装技能")
        print("    skills uninstall   - 卸载技能")
        print()
        print("  记忆管理:")
        print("    memory add         - 添加记忆")
        print("    memory list        - 列出记忆")
        print("    memory search      - 搜索记忆")
        print("    memory clear       - 清除记忆")
        print()
        print("  心跳任务:")
        print("    heartbeat list     - 列出心跳任务")
        print("    heartbeat add      - 添加心跳任务")
        print("    heartbeat remove   - 移除心跳任务")
        print()
        print("  LLM 路由:")
        print("    llm status         - 查看 LLM 状态")
        print("    llm add-provider   - 添加 LLM 提供方")
        print("    llm test           - 测试 LLM 调用")
        print()
        print("  Agent 编排:")
        print("    agent list         - 列出 Agent")
        print("    agent create-task  - 创建任务")
        print("    agent status       - 查看编排状态")
        print()
        print("  数据管理:")
        print("    data export        - 导出数据")
        print("    data import        - 导入数据")
        print("    data backup        - 备份所有数据")
        print("    data restore       - 恢复数据")
        print()
        print("  工具:")
        print("    dashboard          - 启动监控仪表板")
        print("    web                - 启动 Web 服务")
        print("    help               - 显示此帮助")
        print("    exit               - 退出")
        print()
    
    # ========== 工作区命令 ==========
    
    async def cmd_workspace_list(self, args):
        """列出工作区文件"""
        if not self.workspace:
            color_print("工作区未初始化", Colors.FAIL)
            return
        
        files = self.workspace.list_workspace_files()
        
        print()
        color_print(f"工作区: {self.workspace.workspace_path}", Colors.BOLD)
        print()
        
        for file in files:
            size = file['size'] / 1024
            print(f"  📄 {file['name']:<20} {size:.1f} KB")
        print()
    
    async def cmd_workspace_show(self, args):
        """显示工作区配置"""
        if not self.workspace:
            color_print("工作区未初始化", Colors.FAIL)
            return
        
        print()
        color_print("当前配置:", Colors.BOLD)
        print()
        
        # 显示 Agents
        agents = self.workspace.parse_agents_md()
        print(f"Agents ({len(agents)}):")
        for agent in agents:
            status = "✓" if agent.enabled else "✗"
            print(f"  {status} {agent.name}")
            print(f"      - Model: {agent.model}")
            print(f"      - Personality: {agent.personality}")
            print(f"      - Skills: {', '.join(agent.skills) if agent.skills else 'None'}")
        print()
        
        # 显示 Heartbeat
        tasks = self.workspace.parse_heartbeat_md()
        print(f"心跳任务 ({len(tasks)}):")
        for task in tasks:
            status = "✓" if task.enabled else "✗"
            print(f"  {status} {task.name}")
            print(f"      - Schedule: {task.schedule} @ {task.time}")
        print()
    
    # ========== 技能命令 ==========
    
    async def cmd_skills_list(self, args):
        """列出所有技能"""
        if not self.skills_engine:
            color_print("技能引擎未初始化", Colors.FAIL)
            return
        
        skills = self.skills_engine.list_skills()
        
        print()
        color_print(f"技能列表 ({len(skills)}):", Colors.BOLD)
        print()
        
        for skill in skills:
            status = "✓" if skill.enabled else "✗"
            print(f"  {status} {skill.name}")
            print(f"      - ID: {skill.id}")
            print(f"      - Category: {skill.category}")
            print(f"      - Tags: {', '.join(skill.tags) if skill.tags else 'None'}")
            print()
    
    async def cmd_skills_search(self, args):
        """搜索技能仓库"""
        if not self.skill_hub:
            color_print("技能仓库未初始化", Colors.FAIL)
            return
        
        query = args.query if args.query else ""
        result = self.skill_hub.search_skills(query=query)
        
        print()
        color_print(f"搜索结果: {result['total']}", Colors.BOLD)
        print()
        
        for skill in result['skills'][:10]:
            print(f"  📦 {skill['name']}")
            print(f"      - {skill['description']}")
            print(f"      - ⭐ {skill['rating']} | 📥 {skill['downloads']}")
            print(f"      - Status: {skill['status']}")
            print()
    
    async def cmd_skills_install(self, args):
        """安装技能"""
        if not self.skill_hub or not args.skill_id:
            color_print("缺少参数: skill_id", Colors.FAIL)
            return
        
        color_print(f"正在安装技能: {args.skill_id}", Colors.OKCYAN)
        
        result = await self.skill_hub.install_skill(args.skill_id)
        
        if result['success']:
            color_print("✓ 安装成功!", Colors.OKGREEN)
        else:
            color_print(f"✗ 安装失败: {result.get('error')}", Colors.FAIL)
    
    # ========== 记忆命令 ==========
    
    async def cmd_memory_add(self, args):
        """添加记忆"""
        if not self.memory_engine:
            color_print("记忆引擎未初始化", Colors.FAIL)
            return
        
        content = args.content if args.content else input("记忆内容: ")
        memory_type = args.type if args.type else "note"
        
        result = await self.memory_engine.add_memory(
            content=content,
            memory_type=memory_type
        )
        
        color_print(f"✓ 记忆已添加: {result['id']}", Colors.OKGREEN)
    
    async def cmd_memory_list(self, args):
        """列出记忆"""
        if not self.memory_engine:
            color_print("记忆引擎未初始化", Colors.FAIL)
            return
        
        memories = await self.memory_engine.get_recent_memories(limit=10)
        
        print()
        color_print(f"最近记忆 ({len(memories)}):", Colors.BOLD)
        print()
        
        for memory in memories:
            print(f"  📝 [{memory['type']}] {memory['content'][:50]}...")
            print()
    
    async def cmd_memory_search(self, args):
        """搜索记忆"""
        if not self.memory_engine or not args.query:
            color_print("缺少参数: query", Colors.FAIL)
            return
        
        results = await self.memory_engine.search_memory(args.query)
        
        print()
        color_print(f"搜索结果: {len(results)}", Colors.BOLD)
        print()
        
        for memory in results[:10]:
            print(f"  📝 [{memory['type']}] {memory['content'][:60]}...")
            print(f"      Score: {memory.get('relevance', 0):.2f}")
            print()
    
    # ========== 心跳命令 ==========
    
    async def cmd_heartbeat_list(self, args):
        """列出心跳任务"""
        if not self.heartbeat:
            color_print("心跳引擎未初始化", Colors.FAIL)
            return
        
        status = self.heartbeat.get_status()
        
        print()
        color_print(f"心跳任务 ({status['active_tasks']} 活跃):", Colors.BOLD)
        print()
        
        for task_id, task in status.get('scheduled_tasks', {}).items():
            status_icon = "✓" if task.get('enabled') else "✗"
            print(f"  {status_icon} {task['name']}")
            print(f"      - Schedule: {task['schedule']}")
            print(f"      - Last: {task.get('last_run', 'Never')}")
            print()
    
    # ========== LLM 命令 ==========
    
    async def cmd_llm_status(self, args):
        """查看 LLM 状态"""
        if not self.llm_router:
            color_print("LLM 路由未初始化", Colors.FAIL)
            return
        
        status = self.llm_router.get_status()
        
        print()
        color_print("LLM 路由状态:", Colors.BOLD)
        print()
        print(f"  策略: {status['strategy']}")
        print(f"  总提供方: {status['total_providers']}")
        print(f"  启用提供方: {status['enabled_providers']}")
        print()
        
        for provider in status['providers']:
            print(f"  📦 {provider['provider']} / {provider['model']}")
            print(f"      - 启用: {'✓' if provider['enabled'] else '✗'}")
            print(f"      - 请求: {provider['metrics']['requests']}")
            print(f"      - 成功率: {provider['metrics']['success_rate']:.1f}%")
            print()
    
    # ========== Agent 编排命令 ==========
    
    async def cmd_agent_status(self, args):
        """查看 Agent 编排状态"""
        if not self.orchestrator:
            color_print("Agent 编排未初始化", Colors.FAIL)
            return
        
        status = self.orchestrator.get_status()
        
        print()
        color_print("Agent 编排状态:", Colors.BOLD)
        print()
        print(f"  运行中: {'✓' if status['running'] else '✗'}")
        print(f"  Agents: {len(status['agents'])}")
        print()
        print(f"  任务统计:")
        print(f"    总数: {status['tasks']['total']}")
        print(f"    等待: {status['tasks']['pending']}")
        print(f"    进行中: {status['tasks']['in_progress']}")
        print(f"    已完成: {status['tasks']['completed']}")
        print(f"    失败: {status['tasks']['failed']}")
        print()
    
    async def cmd_agent_create_task(self, args):
        """创建任务"""
        if not self.orchestrator:
            color_print("Agent 编排未初始化", Colors.FAIL)
            return
        
        description = args.description if args.description else input("任务描述: ")
        priority = args.priority if args.priority else 5
        
        task_id = self.orchestrator.create_task(
            description=description,
            priority=priority
        )
        
        color_print(f"✓ 任务已创建: {task_id}", Colors.OKGREEN)
    
    # ========== 数据管理命令 ==========
    
    async def cmd_data_export(self, args):
        """导出数据"""
        if not self.workspace:
            color_print("工作区未初始化", Colors.FAIL)
            return
        
        export_path = args.path if args.path else "./dataagent_export.json"
        
        data = {
            "version": "1.0",
            "exported_at": datetime.now().isoformat(),
            "workspace": {
                "soul": self.workspace.read_file(WorkspaceFileType.SOUL),
                "agents": self.workspace.read_file(WorkspaceFileType.AGENTS),
                "memory": self.workspace.read_file(WorkspaceFileType.MEMORY),
                "heartbeat": self.workspace.read_file(WorkspaceFileType.HEARTBEAT)
            }
        }
        
        if self.memory_engine:
            data["memories"] = await self.memory_engine.get_all_memories()
        
        with open(export_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        color_print(f"✓ 数据已导出到: {export_path}", Colors.OKGREEN)
    
    async def cmd_data_import(self, args):
        """导入数据"""
        if not self.workspace:
            color_print("工作区未初始化", Colors.FAIL)
            return
        
        import_path = args.path if args.path else "./dataagent_export.json"
        
        if not Path(import_path).exists():
            color_print(f"文件不存在: {import_path}", Colors.FAIL)
            return
        
        with open(import_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        if "workspace" in data:
            ws = data["workspace"]
            
            if "soul" in ws:
                self.workspace.write_file(WorkspaceFileType.SOUL, ws["soul"])
            if "agents" in ws:
                self.workspace.write_file(WorkspaceFileType.AGENTS, ws["agents"])
            if "memory" in ws:
                self.workspace.write_file(WorkspaceFileType.MEMORY, ws["memory"])
            if "heartbeat" in ws:
                self.workspace.write_file(WorkspaceFileType.HEARTBEAT, ws["heartbeat"])
            
            color_print("✓ 工作区数据已导入", Colors.OKGREEN)
        else:
            color_print("无效的数据格式", Colors.FAIL)
    
    async def cmd_data_backup(self, args):
        """备份所有数据"""
        if not self.workspace:
            color_print("工作区未初始化", Colors.FAIL)
            return
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = Path.home() / ".dataagent" / "backups" / f"backup_{timestamp}"
        backup_path.mkdir(parents=True, exist_ok=True)
        
        # 备份工作区
        ws_path = self.workspace.workspace_path
        for file in ws_path.glob("*.md"):
            import shutil
            shutil.copy(file, backup_path / file.name)
        
        # 备份配置
        config_path = Path.home() / ".dataagent"
        if config_path.exists():
            import shutil
            for file in config_path.glob("*.json"):
                shutil.copy(file, backup_path / file.name)
        
        color_print(f"✓ 备份已保存到: {backup_path}", Colors.OKGREEN)
    
    async def cmd_dashboard(self, args):
        """显示监控仪表板"""
        print()
        color_print("=" * 80, Colors.HEADER)
        color_print("  DataAgent 监控仪表板", Colors.BOLD)
        color_print("=" * 80, Colors.HEADER)
        print()
        
        # 系统信息
        color_print("📊 系统概览", Colors.OKCYAN)
        print()
        
        if self.workspace:
            files = self.workspace.list_workspace_files()
            print(f"  工作区文件: {len(files)}")
        
        if self.skills_engine:
            skills = self.skills_engine.list_skills()
            print(f"  已注册技能: {len(skills)}")
        
        if self.skill_hub:
            hub_status = self.skill_hub.get_status()
            print(f"  仓库技能: {hub_status['registry_count']}")
            print(f"  已安装技能: {hub_status['installed_count']}")
        
        if self.memory_engine:
            memories = await self.memory_engine.get_recent_memories(limit=100)
            print(f"  记忆条目: {len(memories)}")
        
        if self.heartbeat:
            hb_status = self.heartbeat.get_status()
            print(f"  心跳任务: {hb_status['active_tasks']}")
        
        if self.llm_router:
            llm_status = self.llm_router.get_status()
            print(f"  LLM 提供方: {llm_status['enabled_providers']}/{llm_status['total_providers']}")
        
        if self.orchestrator:
            orch_status = self.orchestrator.get_status()
            print(f"  活跃任务: {orch_status['tasks']['in_progress']}")
        
        print()
        color_print("🎯 快速操作", Colors.OKCYAN)
        print()
        print("  1. 启动 Web 服务")
        print("  2. 添加记忆")
        print("  3. 搜索技能")
        print("  4. 查看 LLM 状态")
        print("  5. 创建任务")
        print("  6. 导出数据")
        print()
    
    # ========== 主命令处理器 ==========
    
    async def run_command(self, cmd: str, args):
        """运行命令"""
        cmd_map = {
            'workspace': {
                'list': self.cmd_workspace_list,
                'show': self.cmd_workspace_show,
            },
            'skills': {
                'list': self.cmd_skills_list,
                'search': self.cmd_skills_search,
                'install': self.cmd_skills_install,
            },
            'memory': {
                'add': self.cmd_memory_add,
                'list': self.cmd_memory_list,
                'search': self.cmd_memory_search,
            },
            'heartbeat': {
                'list': self.cmd_heartbeat_list,
            },
            'llm': {
                'status': self.cmd_llm_status,
            },
            'agent': {
                'status': self.cmd_agent_status,
                'create-task': self.cmd_agent_create_task,
            },
            'data': {
                'export': self.cmd_data_export,
                'import': self.cmd_data_import,
                'backup': self.cmd_data_backup,
            },
            'dashboard': self.cmd_dashboard,
        }
        
        parts = cmd.split()
        if not parts:
            return
        
        main_cmd = parts[0]
        sub_cmd = parts[1] if len(parts) > 1 else None
        
        if main_cmd == 'help':
            self.show_help()
        elif main_cmd == 'exit':
            color_print("再见!", Colors.OKCYAN)
            sys.exit(0)
        elif main_cmd == 'web':
            color_print("启动 Web 服务...", Colors.OKCYAN)
            os.system("python -m uvicorn web_app:app --reload --host 0.0.0.0 --port 8000")
        elif main_cmd in cmd_map:
            if sub_cmd and main_cmd in cmd_map and isinstance(cmd_map[main_cmd], dict):
                if sub_cmd in cmd_map[main_cmd]:
                    await cmd_map[main_cmd][sub_cmd](args)
                else:
                    color_print(f"未知子命令: {sub_cmd}", Colors.FAIL)
            elif callable(cmd_map[main_cmd]):
                await cmd_map[main_cmd](args)
            else:
                color_print(f"未知命令: {cmd}", Colors.FAIL)
        else:
            color_print(f"未知命令: {main_cmd}", Colors.FAIL)
            print("输入 'help' 查看可用命令")


async def main_async():
    """异步主函数"""
    cli = DataAgentCLI()
    cli.show_banner()
    cli.show_help()
    
    while True:
        try:
            cmd = input(f"{Colors.OKGREEN}dataagent> {Colors.ENDC}").strip()
            
            if not cmd:
                continue
            
            # 解析参数
            parser = argparse.ArgumentParser(description="DataAgent CLI", exit_on_error=False)
            parser.add_argument('command', nargs='*')
            parser.add_argument('--query', '-q')
            parser.add_argument('--skill-id', '-s')
            parser.add_argument('--content', '-c')
            parser.add_argument('--type', '-t')
            parser.add_argument('--path', '-p')
            parser.add_argument('--description', '-d')
            parser.add_argument('--priority', type=int, default=5)
            
            try:
                parsed, unknown = parser.parse_known_args(cmd.split())
            except SystemExit:
                continue
            
            command = ' '.join(parsed.command) if parsed.command else cmd
            
            await cli.run_command(command, parsed)
            
        except KeyboardInterrupt:
            print()
            color_print("\n再见!", Colors.OKCYAN)
            break
        except Exception as e:
            color_print(f"错误: {e}", Colors.FAIL)


def main():
    """主函数"""
    try:
        asyncio.run(main_async())
    except KeyboardInterrupt:
        print()
        color_print("再见!", Colors.OKCYAN)


if __name__ == "__main__":
    main()

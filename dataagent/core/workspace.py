
"""Workspace file manager.

Reads and writes the four workspace files: SOUL.md, AGENTS.md,
HEARTBEAT.md, MEMORY.md. Used by `/api/workspace/*` routes.
"""
import re
import json
import yaml
import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from enum import Enum

from core.logging import get_logger

logger = get_logger("workspace")


class WorkspaceFileType(str, Enum):
    """Workspace file type."""

    SOUL = "SOUL.md"
    AGENTS = "AGENTS.md"
    HEARTBEAT = "HEARTBEAT.md"
    MEMORY = "MEMORY.md"
    CONFIG = "config.yaml"


@dataclass
class AgentConfig:
    """Agent entry parsed from AGENTS.md."""
    name: str
    description: str = ""
    model: str = ""
    personality: str = ""
    skills: List[str] = field(default_factory=list)
    channels: List[str] = field(default_factory=list)
    enabled: bool = True
    config: Dict[str, Any] = field(default_factory=dict)


@dataclass
class HeartbeatTask:
    """心跳任务（来自 HEARTBEAT.md）"""
    name: str
    description: str = ""
    schedule: str = "daily"
    time: str = "08:00"
    enabled: bool = True
    task_type: str = "reminder"
    target: str = ""
    message: str = ""


@dataclass
class MemoryEntry:
    """记忆条目（来自 MEMORY.md）"""
    id: str
    date: str
    type: str
    content: str
    tags: List[str] = field(default_factory=list)
    importance: int = 5


class WorkspaceManager:
    """Manages the four workspace files (SOUL/AGENTS/HEARTBEAT/MEMORY)."""
    
    def __init__(self, workspace_path: Optional[Path] = None):
        if workspace_path is None:
            workspace_path = Path.home() / ".dataagent" / "workspace"
        
        self.workspace_path = workspace_path
        self.workspace_path.mkdir(parents=True, exist_ok=True)
        
        # 初始化所有必需的文件
        self._init_files()
        
        logger.info(f"工作区初始化完成: {self.workspace_path}")
    
    def _init_files(self):
        """初始化工作区文件"""
        files = {
            WorkspaceFileType.SOUL: self._get_default_soul,
            WorkspaceFileType.AGENTS: self._get_default_agents,
            WorkspaceFileType.HEARTBEAT: self._get_default_heartbeat,
            WorkspaceFileType.MEMORY: self._get_default_memory,
            WorkspaceFileType.CONFIG: self._get_default_config
        }
        
        for file_type, default_fn in files.items():
            file_path = self.workspace_path / file_type.value
            if not file_path.exists():
                content = default_fn()
                file_path.write_text(content, encoding="utf-8")
                logger.info(f"创建默认文件: {file_path}")
    
    def _get_default_soul(self) -> str:
        """获取默认 SOUL.md 内容"""
        return """# SOUL.md

You are a helpful data assistant. Be concise, prefer code or numbers over
prose, and always cite the source when you quote a fact.

## Personality
- Tone: direct, slightly informal
- Default length: 3-5 sentences for chat, longer for reports
- Language: match the user
"""

    def _get_default_agents(self) -> str:
        """获取默认 AGENTS.md 内容"""
        return """# AGENTS.md

## Agents

### main
- Description: Default assistant
- Model: gpt-4
- Skills: *
- Channels: *
- Enabled: true

### research
- Description: Research assistant
- Model: gpt-4
- Skills: web_search, file_ops
- Channels: *
- Enabled: true

### creative
- Description: Creative assistant
- Model: gpt-4
- Skills: image_gen, brainstorm
- Channels: *
- Enabled: true
"""
    
    def _get_default_heartbeat(self) -> str:
        """Default HEARTBEAT.md content."""
        return """# HEARTBEAT.md

- every 30m: refresh index of recent files in workspace/data
- every 2h: summarize today's MEMORY.md entries
"""
    
    def _get_default_memory(self) -> str:
        """获取默认 MEMORY.md 内容"""
        return """# MEMORY.md

(empty)
"""
    
    def _get_default_config(self) -> str:
        """Default config.yaml content."""
        return """# config.yaml
model: gpt-4
temperature: 0.7
log_level: INFO
"""
    
    def get_file_path(self, file_type: WorkspaceFileType) -> Path:
        """获取文件路径"""
        return self.workspace_path / file_type.value
    
    def read_file(self, file_type: WorkspaceFileType) -> str:
        """读取文件内容"""
        file_path = self.get_file_path(file_type)
        if file_path.exists():
            return file_path.read_text(encoding="utf-8")
        return ""
    
    def write_file(self, file_type: WorkspaceFileType, content: str):
        """写入文件内容"""
        file_path = self.get_file_path(file_type)
        file_path.write_text(content, encoding="utf-8")
        logger.info(f"文件已更新: {file_path}")
    
    # ========== AGENTS.md 管理 ==========
    
    def parse_agents_md(self) -> List[AgentConfig]:
        """解析 AGENTS.md 文件"""
        content = self.read_file(WorkspaceFileType.AGENTS)
        agents = []
        
        # 解析 Agent 配置
        agent_blocks = re.split(r'###\s+(\w+)', content)
        
        for i in range(1, len(agent_blocks), 2):
            name = agent_blocks[i].strip()
            block = agent_blocks[i + 1] if (i + 1) < len(agent_blocks) else ""
            
            agent = AgentConfig(name=name)
            
            # 提取各项配置
            if match := re.search(r'Description:\s*(.+)', block):
                agent.description = match.group(1).strip()
            if match := re.search(r'Model:\s*(\w+)', block):
                agent.model = match.group(1).strip()
            if match := re.search(r'Personality:\s*(\w+)', block):
                agent.personality = match.group(1).strip()
            if match := re.search(r'Skills:\s*(.+)', block):
                skills_str = match.group(1).strip()
                agent.skills = [s.strip() for s in skills_str.split(',') if s.strip()]
            if match := re.search(r'Channels:\s*(.+)', block):
                channels_str = match.group(1).strip()
                agent.channels = [c.strip() for c in channels_str.split(',') if c.strip()]
            if match := re.search(r'Enabled:\s*(true|false)', block, re.I):
                agent.enabled = match.group(1).lower() == 'true'
            
            agents.append(agent)
        
        return agents
    
    def get_agent_config(self, name: str) -> Optional[AgentConfig]:
        """获取指定 Agent 的配置"""
        agents = self.parse_agents_md()
        for agent in agents:
            if agent.name == name:
                return agent
        return None
    
    # ========== HEARTBEAT.md 管理 ==========
    
    def parse_heartbeat_md(self) -> List[HeartbeatTask]:
        """解析 HEARTBEAT.md 文件"""
        content = self.read_file(WorkspaceFileType.HEARTBEAT)
        tasks = []
        
        task_blocks = re.split(r'###\s+(\w+)', content)
        
        for i in range(1, len(task_blocks), 2):
            name = task_blocks[i].strip()
            block = task_blocks[i + 1] if (i + 1) < len(task_blocks) else ""
            
            task = HeartbeatTask(name=name)
            
            if match := re.search(r'Description:\s*(.+)', block):
                task.description = match.group(1).strip()
            if match := re.search(r'Schedule:\s*(\w+)', block):
                task.schedule = match.group(1).strip()
            if match := re.search(r'Time:\s*(\d{1,2}:\d{2})', block):
                task.time = match.group(1).strip()
            if match := re.search(r'Type:\s*(\w+)', block):
                task.task_type = match.group(1).strip()
            if match := re.search(r'Message:\s*(.+)', block):
                task.message = match.group(1).strip()
            if match := re.search(r'Enabled:\s*(true|false)', block, re.I):
                task.enabled = match.group(1).lower() == 'true'
            
            tasks.append(task)
        
        return tasks
    
    # ========== MEMORY.md 管理 ==========
    
    def add_memory(self, content: str, memory_type: str = "note", tags: Optional[List[str]] = None, importance: int = 5) -> MemoryEntry:
        """添加记忆条目"""
        now = datetime.datetime.now()
        memory_id = f"{now.strftime('%Y-%m-%d')}-{len(content[:20]).to_bytes(4, 'big').hex()}"
        
        entry = MemoryEntry(
            id=memory_id,
            date=now.strftime('%Y-%m-%d'),
            type=memory_type,
            content=content,
            tags=tags or [],
            importance=importance
        )
        
        # 追加到 MEMORY.md
        memory_path = self.get_file_path(WorkspaceFileType.MEMORY)
        with open(memory_path, 'a', encoding='utf-8') as f:
            f.write(f"\n\n### {entry.id}\n")
            f.write(f"- Date: {entry.date}\n")
            f.write(f"- Type: {entry.type}\n")
            f.write(f"- Content: {entry.content}\n")
            if entry.tags:
                f.write(f"- Tags: {', '.join(entry.tags)}\n")
            f.write(f"- Importance: {entry.importance}\n")
        
        logger.info(f"添加记忆: {entry.id}")
        return entry
    
    def list_workspace_files(self) -> List[Dict[str, Any]]:
        """列出所有工作区文件"""
        files = []
        for file_type in WorkspaceFileType:
            file_path = self.get_file_path(file_type)
            if file_path.exists():
                stat = file_path.stat()
                files.append({
                    "name": file_type.value,
                    "path": str(file_path),
                    "size": stat.st_size,
                    "modified": stat.st_mtime
                })
        return files


# 全局工作区管理器
_workspace_manager: Optional[WorkspaceManager] = None


def get_workspace_manager(workspace_path: Optional[Path] = None) -> WorkspaceManager:
    """获取工作区管理器实例"""
    global _workspace_manager
    if _workspace_manager is None:
        _workspace_manager = WorkspaceManager(workspace_path)
    return _workspace_manager


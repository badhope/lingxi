"""
DataAgent - 模板系统增强
支持预制工作流模板、Agent 模板库、SOUL 模板市场
"""
import json
import yaml
from typing import Dict, List, Optional, Any
from pathlib import Path
from dataclasses import dataclass, field
from datetime import datetime

from core.logging import get_logger

logger = get_logger("templates")


@dataclass
class WorkflowTemplate:
    """工作流模板"""
    id: str
    name: str
    description: str
    category: str
    tags: List[str] = field(default_factory=list)
    version: str = "1.0.0"
    author: str = "DataAgent"
    nodes: List[Dict] = field(default_factory=list)
    edges: List[Dict] = field(default_factory=list)
    variables: Dict[str, Any] = field(default_factory=dict)
    created_at: float = field(default_factory=lambda: datetime.now().timestamp())


@dataclass
class AgentTemplate:
    """Agent 模板"""
    id: str
    name: str
    description: str
    personality: str
    skills: List[str] = field(default_factory=list)
    channels: List[str] = field(default_factory=list)
    model: str = "gpt-4"
    system_prompt: str = ""


@dataclass
class SoulTemplate:
    """SOUL 模板"""
    id: str
    name: str
    description: str
    personality_type: str
    communication_style: str
    humor_level: int
    prohibited_phrases: List[str] = field(default_factory=list)
    preferred_openers: List[str] = field(default_factory=list)
    rules: List[str] = field(default_factory=list)


class TemplateManager:
    """
    模板管理器
    提供工作流、Agent、SOUL 模板的创建和管理
    """
    
    def __init__(self, template_dir: Optional[Path] = None):
        if template_dir is None:
            template_dir = Path.home() / ".dataagent" / "templates"
        
        self.template_dir = template_dir
        self.template_dir.mkdir(parents=True, exist_ok=True)
        
        (self.template_dir / "workflows").mkdir(exist_ok=True)
        (self.template_dir / "agents").mkdir(exist_ok=True)
        (self.template_dir / "souls").mkdir(exist_ok=True)
        
        self._init_default_templates()
        
        logger.info("模板管理器初始化完成")
    
    def _init_default_templates(self):
        """初始化默认模板"""
        # 工作流模板
        workflow_templates = [
            {
                "id": "tpl_data_analysis",
                "name": "数据分析工作流",
                "description": "完整的数据分析流程：数据导入、清洗、分析、可视化",
                "category": "data",
                "tags": ["data", "analysis", "visualization"],
                "nodes": [
                    {"id": "1", "type": "data_input", "name": "数据导入"},
                    {"id": "2", "type": "data_clean", "name": "数据清洗"},
                    {"id": "3", "type": "data_analysis", "name": "数据分析"},
                    {"id": "4", "type": "visualization", "name": "可视化"}
                ],
                "edges": [
                    {"from": "1", "to": "2"},
                    {"from": "2", "to": "3"},
                    {"from": "3", "to": "4"}
                ]
            },
            {
                "id": "tpl_content_generation",
                "name": "内容生成工作流",
                "description": "AI 辅助内容创作：选题、撰写、润色、发布",
                "category": "content",
                "tags": ["content", "writing", "ai"],
                "nodes": [
                    {"id": "1", "type": "topic_select", "name": "选题"},
                    {"id": "2", "type": "content_write", "name": "撰写"},
                    {"id": "3", "type": "content_polish", "name": "润色"},
                    {"id": "4", "type": "content_review", "name": "审核"}
                ],
                "edges": [
                    {"from": "1", "to": "2"},
                    {"from": "2", "to": "3"},
                    {"from": "3", "to": "4"}
                ]
            },
            {
                "id": "tpl_customer_service",
                "name": "客服工作流",
                "description": "智能客服：问题分类、回复生成、满意度跟踪",
                "category": "service",
                "tags": ["customer", "service", "chatbot"],
                "nodes": [
                    {"id": "1", "type": "intent_classify", "name": "意图分类"},
                    {"id": "2", "type": "knowledge_retrieve", "name": "知识检索"},
                    {"id": "3", "type": "response_generate", "name": "回复生成"},
                    {"id": "4", "type": "satisfaction_track", "name": "满意度跟踪"}
                ],
                "edges": [
                    {"from": "1", "to": "2"},
                    {"from": "2", "to": "3"},
                    {"from": "3", "to": "4"}
                ]
            }
        ]
        
        workflow_file = self.template_dir / "workflows" / "default_templates.json"
        if not workflow_file.exists():
            with open(workflow_file, 'w', encoding='utf-8') as f:
                json.dump(workflow_templates, f, ensure_ascii=False, indent=2)
        
        # Agent 模板
        agent_templates = [
            {
                "id": "tpl_researcher",
                "name": "研究员",
                "description": "专注于信息检索、分析和报告撰写",
                "personality": "professional",
                "skills": ["web_search", "data_analysis", "writing"],
                "channels": ["web", "console"],
                "model": "gpt-4",
                "system_prompt": "你是一个专业的研究员，擅长信息检索和分析。"
            },
            {
                "id": "tpl_creative",
                "name": "创意助手",
                "description": "专注于创意生成和内容创作",
                "personality": "creative",
                "skills": ["brainstorm", "writing", "image_gen"],
                "channels": ["web", "console"],
                "model": "gpt-4",
                "system_prompt": "你是一个充满创意的助手，擅长头脑风暴和创意生成。"
            },
            {
                "id": "tpl_coder",
                "name": "编程助手",
                "description": "专注于代码编写、调试和技术支持",
                "personality": "technical",
                "skills": ["code_gen", "code_review", "debug"],
                "channels": ["web", "console"],
                "model": "gpt-4",
                "system_prompt": "你是一个经验丰富的程序员，精通多种编程语言。"
            }
        ]
        
        agent_file = self.template_dir / "agents" / "default_templates.json"
        if not agent_file.exists():
            with open(agent_file, 'w', encoding='utf-8') as f:
                json.dump(agent_templates, f, ensure_ascii=False, indent=2)
        
        # SOUL 模板
        soul_templates = [
            {
                "id": "tpl_professional",
                "name": "专业助手",
                "description": "正式、严谨、注重准确性",
                "personality_type": "professional",
                "communication_style": "formal",
                "humor_level": 2,
                "prohibited_phrases": ["哈哈", "这个嘛", "应该是吧"],
                "preferred_openers": ["根据分析", "经过研究", "建议"],
                "rules": [
                    "使用正式的语言风格",
                    "提供准确的数据和引用",
                    "避免模糊的表达"
                ]
            },
            {
                "id": "tpl_friendly",
                "name": "友好助手",
                "description": "亲切、耐心、善于鼓励",
                "personality_type": "friendly",
                "communication_style": "casual",
                "humor_level": 7,
                "prohibited_phrases": [],
                "preferred_openers": ["好的！", "没问题！", "很高兴帮你！"],
                "rules": [
                    "使用友好的语气",
                    "适当使用表情",
                    "鼓励用户尝试"
                ]
            },
            {
                "id": "tpl_minimal",
                "name": "简洁助手",
                "description": "高效、直接、少废话",
                "personality_type": "minimal",
                "communication_style": "terse",
                "humor_level": 3,
                "prohibited_phrases": ["好的", "让我想想", "这个问题的答案是"],
                "preferred_openers": ["答:", "结论:", "方案:"],
                "rules": [
                    "直接给出答案",
                    "省略不必要的解释",
                    "保持简洁"
                ]
            }
        ]
        
        soul_file = self.template_dir / "souls" / "default_templates.json"
        if not soul_file.exists():
            with open(soul_file, 'w', encoding='utf-8') as f:
                json.dump(soul_templates, f, ensure_ascii=False, indent=2)
    
    def list_workflow_templates(self, category: Optional[str] = None) -> List[Dict]:
        """列出工作流模板"""
        workflow_file = self.template_dir / "workflows" / "default_templates.json"
        
        if not workflow_file.exists():
            return []
        
        with open(workflow_file, 'r', encoding='utf-8') as f:
            templates = json.load(f)
        
        if category:
            templates = [t for t in templates if t.get('category') == category]
        
        return templates
    
    def list_agent_templates(self) -> List[Dict]:
        """列出 Agent 模板"""
        agent_file = self.template_dir / "agents" / "default_templates.json"
        
        if not agent_file.exists():
            return []
        
        with open(agent_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def list_soul_templates(self) -> List[Dict]:
        """列出 SOUL 模板"""
        soul_file = self.template_dir / "souls" / "default_templates.json"
        
        if not soul_file.exists():
            return []
        
        with open(soul_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def apply_workflow_template(self, template_id: str) -> Optional[Dict]:
        """应用工作流模板"""
        templates = self.list_workflow_templates()
        
        for tpl in templates:
            if tpl['id'] == template_id:
                return {
                    'name': tpl['name'],
                    'nodes': tpl['nodes'],
                    'edges': tpl['edges'],
                    'variables': tpl.get('variables', {})
                }
        
        return None
    
    def apply_agent_template(self, template_id: str) -> Optional[Dict]:
        """应用 Agent 模板"""
        templates = self.list_agent_templates()
        
        for tpl in templates:
            if tpl['id'] == template_id:
                return tpl
        
        return None
    
    def apply_soul_template(self, template_id: str) -> Optional[Dict]:
        """应用 SOUL 模板"""
        templates = self.list_soul_templates()
        
        for tpl in templates:
            if tpl['id'] == template_id:
                return tpl
        
        return None
    
    def create_workflow_template(
        self,
        name: str,
        description: str,
        category: str,
        nodes: List[Dict],
        edges: List[Dict],
        tags: Optional[List[str]] = None
    ) -> str:
        """创建工作流模板"""
        template_id = f"custom_{name.lower().replace(' ', '_')}_{datetime.now().timestamp()}"
        
        template = {
            "id": template_id,
            "name": name,
            "description": description,
            "category": category,
            "tags": tags or [],
            "version": "1.0.0",
            "author": "custom",
            "nodes": nodes,
            "edges": edges
        }
        
        workflow_file = self.template_dir / "workflows" / "custom_templates.json"
        
        custom_templates = []
        if workflow_file.exists():
            with open(workflow_file, 'r', encoding='utf-8') as f:
                custom_templates = json.load(f)
        
        custom_templates.append(template)
        
        with open(workflow_file, 'w', encoding='utf-8') as f:
            json.dump(custom_templates, f, ensure_ascii=False, indent=2)
        
        logger.info(f"创建工作流模板: {name}")
        return template_id
    
    def get_status(self) -> Dict[str, Any]:
        """获取模板状态"""
        return {
            "workflows": len(self.list_workflow_templates()),
            "agents": len(self.list_agent_templates()),
            "souls": len(self.list_soul_templates())
        }


_template_manager: Optional[TemplateManager] = None


def get_template_manager() -> TemplateManager:
    """获取模板管理器"""
    global _template_manager
    if _template_manager is None:
        _template_manager = TemplateManager()
    return _template_manager

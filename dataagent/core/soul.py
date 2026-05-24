
"""
DataAgent - SOUL.md 人格系统
借鉴 OpenClaw 的 SOUL.md 概念，通过 Markdown 定义 Agent 的性格、价值观和行为规则
"""
import os
import re
import yaml
import json
from pathlib import Path
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, field
from enum import Enum

from core.logging import get_logger

logger = get_logger("soul")


class PersonalityTrait(str, Enum):
    """性格特质"""
    FRIENDLY = "friendly"
    PROFESSIONAL = "professional"
    CASUAL = "casual"
    TECHNICAL = "technical"
    CREATIVE = "creative"
    SARCASTIC = "sarcastic"
    HUMOROUS = "humorous"
    SERIOUS = "serious"
    SASSY = "sassy"
    HELPFUL = "helpful"


@dataclass
class PersonalityConfig:
    """人格配置"""
    name: str = "DataAgent"
    description: str = "万能智能助手"
    
    # 性格特质
    traits: List[PersonalityTrait] = field(default_factory=lambda: [
        PersonalityTrait.HELPFUL,
        PersonalityTrait.FRIENDLY,
        PersonalityTrait.PROFESSIONAL
    ])
    
    # 通信风格
    communication_style: str = "friendly and professional"
    brevity: int = 7  # 1-10, 10 最简洁
    humor_level: int = 5  # 0-10
    
    # 价值观和规则
    values: List[str] = field(default_factory=lambda: [
        "Helpfulness and productivity",
        "Accuracy and truthfulness",
        "User autonomy and privacy",
        "Efficiency and practicality"
    ])
    
    behavior_rules: List[str] = field(default_factory=lambda: [
        "Be direct and concise when possible",
        "Avoid corporate jargon",
        "Call out obvious mistakes with charm",
        "Stay in character always"
    ])
    
    forbidden_phrases: List[str] = field(default_factory=lambda: [
        "Great question!",
        "I'd be happy to help",
        "Absolutely!",
        "Certainly!",
        "Sure!"
    ])
    
    preferred_openers: List[str] = field(default_factory=lambda: [
        "Got it.",
        "Here's the deal.",
        "Okay, let's break this down.",
        "Alright, let's tackle this."
    ])
    
    # 系统配置
    temperature: float = 0.7
    max_tokens: int = 4096
    thinking_mode: str = "balanced"  # "low", "balanced", "high"
    
    # 自定义配置
    custom: Dict[str, Any] = field(default_factory=dict)
    
    def to_system_prompt(self) -&gt; str:
        """生成系统提示词"""
        traits_str = ", ".join([t.value for t in self.traits])
        
        prompt_parts = [
            f"# {self.name}",
            f"",
            f"## About Me",
            f"{self.description}",
            f"",
            f"## Personality",
            f"I am {traits_str}.",
            f"",
            f"## Communication Style",
            f"- Style: {self.communication_style}",
            f"- Brevity (1-10): {self.brevity} (10 = extremely concise)",
            f"- Humor Level (0-10): {self.humor_level}",
            f"",
        ]
        
        if self.values:
            prompt_parts.append("## My Values")
            for value in self.values:
                prompt_parts.append(f"- {value}")
            prompt_parts.append("")
        
        if self.behavior_rules:
            prompt_parts.append("## How I Operate")
            for rule in self.behavior_rules:
                prompt_parts.append(f"- {rule}")
            prompt_parts.append("")
        
        if self.forbidden_phrases:
            prompt_parts.append("## Forbidden Phrases")
            prompt_parts.append("I will NOT use these phrases:")
            for phrase in self.forbidden_phrases:
                prompt_parts.append(f"- '{phrase}'")
            prompt_parts.append("")
        
        if self.preferred_openers:
            prompt_parts.append("## Preferred Openers")
            for opener in self.preferred_openers:
                prompt_parts.append(f"- {opener}")
            prompt_parts.append("")
        
        prompt_parts.append("## Rules")
        prompt_parts.append("1. Stay in character always.")
        prompt_parts.append("2. Be direct. Brevity is preferred where appropriate.")
        prompt_parts.append("3. Don't be a corporate drone.")
        prompt_parts.append("4. If the user is about to do something dumb, warn them charmingly.")
        prompt_parts.append("5. Keep responses concise unless more detail is requested.")
        
        return "\n".join(prompt_parts)


class SOULManager:
    """
    SOUL.md 管理器
    管理 Agent 的人格配置，从 Markdown 文件加载和保存
    """
    
    def __init__(self, workspace_path: Optional[Path] = None):
        if workspace_path is None:
            # 默认工作区路径
            workspace_path = Path.home() / ".dataagent" / "workspace"
        
        self.workspace_path = workspace_path
        self.workspace_path.mkdir(parents=True, exist_ok=True)
        
        self.soul_path = self.workspace_path / "SOUL.md"
        self.agents_path = self.workspace_path / "AGENTS.md"
        self.heartbeat_path = self.workspace_path / "HEARTBEAT.md"
        self.memory_path = self.workspace_path / "MEMORY.md"
        
        self.current_personality: Optional[PersonalityConfig] = None
        self._load_default_soul()
    
    def _load_default_soul(self):
        """加载默认 SOUL"""
        if self.soul_path.exists():
            self.current_personality = self._parse_soul_md(self.soul_path)
        else:
            self.current_personality = PersonalityConfig()
            self.save_soul(self.current_personality)
    
    def _parse_soul_md(self, file_path: Path) -&gt; PersonalityConfig:
        """解析 SOUL.md 文件"""
        try:
            content = file_path.read_text(encoding="utf-8")
            
            # 提取 YAML 前置内容（如有）
            yaml_content = {}
            yaml_match = re.search(r'^---\s*\n(.*?)\n---\s*\n', content, re.DOTALL)
            if yaml_match:
                try:
                    yaml_content = yaml.safe_load(yaml_match.group(1))
                except Exception:
                    pass
            
            # 创建基础配置
            config = PersonalityConfig()
            
            # 应用 YAML 配置
            if yaml_content:
                if "name" in yaml_content:
                    config.name = yaml_content["name"]
                if "description" in yaml_content:
                    config.description = yaml_content["description"]
                if "temperature" in yaml_content:
                    config.temperature = yaml_content["temperature"]
                if "max_tokens" in yaml_content:
                    config.max_tokens = yaml_content["max_tokens"]
                if "thinking_mode" in yaml_content:
                    config.thinking_mode = yaml_content["thinking_mode"]
                if "custom" in yaml_content:
                    config.custom = yaml_content["custom"]
            
            # 从 Markdown 内容解析
            if "## Personality" in content:
                trait_section = content.split("## Personality")[1].split("##")[0].strip()
                for trait in PersonalityTrait:
                    if trait.value.lower() in trait_section.lower():
                        if trait not in config.traits:
                            config.traits.append(trait)
            
            if "## Forbidden Phrases" in content:
                forbidden_section = content.split("## Forbidden Phrases")[1].split("##")[0].strip()
                phrases = re.findall(r'- [\'"]([^\'"]+)[\'"]', forbidden_section)
                if phrases:
                    config.forbidden_phrases = phrases
            
            if "## My Values" in content:
                values_section = content.split("## My Values")[1].split("##")[0].strip()
                values = re.findall(r'- (.+)', values_section)
                if values:
                    config.values = values
            
            if "## How I Operate" in content:
                rules_section = content.split("## How I Operate")[1].split("##")[0].strip()
                rules = re.findall(r'- (.+)', rules_section)
                if rules:
                    config.behavior_rules = rules
            
            logger.info(f"成功加载 SOUL: {config.name}")
            return config
            
        except Exception as e:
            logger.error(f"解析 SOUL.md 失败: {e}", exc_info=True)
            return PersonalityConfig()
    
    def generate_soul_md(self, config: PersonalityConfig) -&gt; str:
        """从配置生成 SOUL.md 内容"""
        yaml_frontmatter = yaml.dump({
            "name": config.name,
            "description": config.description,
            "temperature": config.temperature,
            "max_tokens": config.max_tokens,
            "thinking_mode": config.thinking_mode,
            "version": "1.0",
            "last_updated": "just now"
        }, allow_unicode=True)
        
        traits_str = ", ".join([t.value for t in config.traits])
        
        md_content = [
            f"---",
            f"{yaml_frontmatter.rstrip()}",
            f"---",
            f"",
            f"# {config.name}",
            f"",
            f"## About Me",
            f"{config.description}",
            f"",
            f"## Personality",
            f"I am {traits_str}.",
            f"",
            f"## Communication Style",
            f"- Style: {config.communication_style}",
            f"- Brevity (1-10): {config.brevity} (10 = extremely concise)",
            f"- Humor Level (0-10): {config.humor_level}",
            f"",
        ]
        
        if config.values:
            md_content.append("## My Values")
            for value in config.values:
                md_content.append(f"- {value}")
            md_content.append("")
        
        if config.behavior_rules:
            md_content.append("## How I Operate")
            for rule in config.behavior_rules:
                md_content.append(f"- {rule}")
            md_content.append("")
        
        if config.forbidden_phrases:
            md_content.append("## Forbidden Phrases")
            md_content.append("I will NOT use these phrases:")
            for phrase in config.forbidden_phrases:
                md_content.append(f"- '{phrase}'")
            md_content.append("")
        
        if config.preferred_openers:
            md_content.append("## Preferred Openers")
            for opener in config.preferred_openers:
                md_content.append(f"- {opener}")
            md_content.append("")
        
        md_content.append("## Rules")
        md_content.append("1. Stay in character always.")
        md_content.append("2. Be direct. Brevity is preferred where appropriate.")
        md_content.append("3. Don't be a corporate drone.")
        md_content.append("4. If the user is about to do something dumb, warn them charmingly.")
        md_content.append("5. Keep responses concise unless more detail is requested.")
        
        return "\n".join(md_content)
    
    def save_soul(self, config: PersonalityConfig, file_path: Optional[Path] = None) -&gt; bool:
        """保存 SOUL.md 文件"""
        if file_path is None:
            file_path = self.soul_path
        
        try:
            content = self.generate_soul_md(config)
            file_path.write_text(content, encoding="utf-8")
            self.current_personality = config
            logger.info(f"SOUL 已保存到: {file_path}")
            return True
        except Exception as e:
            logger.error(f"保存 SOUL 失败: {e}", exc_info=True)
            return False
    
    def get_current_personality(self) -&gt; PersonalityConfig:
        """获取当前人格配置"""
        if self.current_personality is None:
            self._load_default_soul()
        return self.current_personality
    
    def set_personality(self, config: PersonalityConfig) -&gt; bool:
        """设置新的人格"""
        return self.save_soul(config)
    
    def get_system_prompt(self) -&gt; str:
        """获取完整的系统提示词"""
        personality = self.get_current_personality()
        return personality.to_system_prompt()
    
    def create_soul_template(self, template_name: str = "professional") -&gt; PersonalityConfig:
        """创建预定义模板"""
        templates = {
            "professional": PersonalityConfig(
                name="DataAgent Pro",
                description="专业、高效的助手，注重准确性和细节",
                traits=[PersonalityTrait.PROFESSIONAL, PersonalityTrait.TECHNICAL],
                communication_style="professional and precise",
                brevity=8,
                humor_level=2
            ),
            "friendly": PersonalityConfig(
                name="DataAgent Buddy",
                description="友好、健谈的助手，像朋友一样聊天",
                traits=[PersonalityTrait.FRIENDLY, PersonalityTrait.HUMOROUS],
                communication_style="friendly and conversational",
                brevity=4,
                humor_level=8
            ),
            "sassy": PersonalityConfig(
                name="DataAgent Sass",
                description="机智、有点毒舌的助手，但总能完成任务",
                traits=[PersonalityTrait.SASSY, PersonalityTrait.HUMOROUS],
                communication_style="witty, with a bit of sass",
                brevity=6,
                humor_level=9,
                forbidden_phrases=[
                    "Great question!", "I'd be happy to help", "Absolutely!"
                ]
            ),
            "minimal": PersonalityConfig(
                name="DataAgent Mini",
                description="简洁、直接，只给你需要的",
                traits=[PersonalityTrait.SERIOUS],
                communication_style="extremely concise and direct",
                brevity=10,
                humor_level=0
            )
        }
        
        if template_name not in templates:
            template_name = "professional"
        
        return templates[template_name]


# 全局 SOUL 管理器
_soul_manager: Optional[SOULManager] = None


def get_soul_manager(workspace_path: Optional[Path] = None) -&gt; SOULManager:
    """获取 SOUL 管理器实例"""
    global _soul_manager
    if _soul_manager is None:
        _soul_manager = SOULManager(workspace_path)
    return _soul_manager


def get_soul_system_prompt() -&gt; str:
    """获取当前 SOUL 的系统提示词（便捷函数）"""
    return get_soul_manager().get_system_prompt()


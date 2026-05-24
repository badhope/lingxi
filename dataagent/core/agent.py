"""
DataAgent - Agent Framework
统一的 Agent 框架，提供基础功能和执行流程
"""
import asyncio
from abc import ABC, abstractmethod
from contextlib import asynccontextmanager
from typing import List, Optional, Dict, Any, Callable, TypeVar, Generic

from pydantic import BaseModel, Field, model_validator

from .config import config_manager
from .logging import agent_logger

# Forward references
LLM = TypeVar('LLM')
Memory = TypeVar('Memory')
Tool = TypeVar('Tool')


class AgentState:
    """Agent 状态枚举"""
    IDLE = "idle"
    RUNNING = "running"
    FINISHED = "finished"
    ERROR = "error"
    PAUSED = "paused"


class ROLE_TYPE:
    """消息角色类型"""
    USER = "user"
    SYSTEM = "system"
    ASSISTANT = "assistant"
    TOOL = "tool"


class Message(BaseModel):
    """消息模型"""
    role: str
    content: str
    base64_image: Optional[str] = None
    tool_call_id: Optional[str] = None
    timestamp: Optional[str] = None
    
    @classmethod
    def user_message(cls, content: str, **kwargs) -> 'Message':
        """创建用户消息"""
        return cls(role=ROLE_TYPE.USER, content=content, **kwargs)
    
    @classmethod
    def system_message(cls, content: str, **kwargs) -> 'Message':
        """创建系统消息"""
        return cls(role=ROLE_TYPE.SYSTEM, content=content, **kwargs)
    
    @classmethod
    def assistant_message(cls, content: str, **kwargs) -> 'Message':
        """创建助手消息"""
        return cls(role=ROLE_TYPE.ASSISTANT, content=content, **kwargs)
    
    @classmethod
    def tool_message(cls, content: str, **kwargs) -> 'Message':
        """创建工具消息"""
        return cls(role=ROLE_TYPE.TOOL, content=content, **kwargs)


class AgentMemory(BaseModel):
    """Agent 内存管理"""
    messages: List[Message] = Field(default_factory=list)
    max_messages: int = Field(100, description="最大消息数量")
    
    def add_message(self, message: Message):
        """添加消息到内存"""
        self.messages.append(message)
        
        # 保持消息数量在限制内
        if len(self.messages) > self.max_messages:
            self.messages = self.messages[-self.max_messages:]
    
    def get_messages(self, limit: Optional[int] = None) -> List[Message]:
        """获取消息列表"""
        if limit:
            return self.messages[-limit:]
        return self.messages
    
    def clear(self):
        """清空内存"""
        self.messages = []
    
    def get_last_message(self) -> Optional[Message]:
        """获取最后一条消息"""
        return self.messages[-1] if self.messages else None
    
    def get_messages_by_role(self, role: str) -> List[Message]:
        """按角色筛选消息"""
        return [m for m in self.messages if m.role == role]


class AgentConfig(BaseModel):
    """Agent 配置"""
    name: str
    description: Optional[str] = None
    max_steps: int = 10
    duplicate_threshold: int = 2
    temperature: float = 0.7
    max_tokens: int = 4096
    
    # 工具配置
    tools: List[str] = Field(default_factory=list)
    tool_config: Dict[str, Dict[str, Any]] = Field(default_factory=dict)
    
    # 内存配置
    memory_max_messages: int = 100
    
    # 执行配置
    execution_timeout: Optional[int] = None
    enable_parallel_tool_calls: bool = False


class BaseAgent(BaseModel, ABC, Generic[LLM, Memory]):
    """
    Agent 抽象基类
    
    提供 Agent 的核心功能：
    - 状态管理
    - 内存管理
    - 执行循环
    - 工具调用
    """
    
    # 核心属性
    name: str = Field(..., description="Agent 名称")
    description: Optional[str] = Field(None, description="Agent 描述")
    
    # 配置
    config: AgentConfig = Field(default_factory=AgentConfig)
    
    # 提示词
    system_prompt: Optional[str] = None
    next_step_prompt: Optional[str] = None
    
    # 依赖
    llm: Optional[LLM] = None
    memory: AgentMemory = Field(default_factory=AgentMemory)
    
    # 状态
    state: str = Field(default=AgentState.IDLE)
    current_step: int = Field(default=0)
    
    # 执行上下文
    _execution_task: Optional[asyncio.Task] = None
    _cancelled: bool = False
    
    class Config:
        arbitrary_types_allowed = True
        extra = "allow"
    
    @model_validator(mode="after")
    def initialize_agent(self) -> "BaseAgent":
        """初始化 Agent"""
        # 确保配置正确设置
        if self.config.name != self.name:
            self.config.name = self.name
        
        # 初始化内存
        if self.memory.max_messages != self.config.memory_max_messages:
            self.memory.max_messages = self.config.memory_max_messages
        
        agent_logger.info(f"Agent initialized: {self.name}")
        return self
    
    @asynccontextmanager
    async def state_context(self, new_state: str):
        """状态上下文管理器"""
        if new_state not in [AgentState.IDLE, AgentState.RUNNING, AgentState.FINISHED, 
                            AgentState.ERROR, AgentState.PAUSED]:
            raise ValueError(f"Invalid state: {new_state}")
        
        previous_state = self.state
        self.state = new_state
        
        try:
            agent_logger.debug(f"Agent {self.name} state changed: {previous_state} -> {new_state}")
            yield
        except Exception as e:
            agent_logger.error(f"Agent {self.name} error in state {new_state}: {e}")
            self.state = AgentState.ERROR
            raise
        finally:
            # 只有在正常完成时才恢复状态
            if self.state not in [AgentState.ERROR, AgentState.FINISHED]:
                self.state = previous_state
    
    def update_memory(
        self,
        role: str,
        content: str,
        base64_image: Optional[str] = None,
        **kwargs
    ) -> None:
        """添加消息到内存"""
        message_map = {
            ROLE_TYPE.USER: Message.user_message,
            ROLE_TYPE.SYSTEM: Message.system_message,
            ROLE_TYPE.ASSISTANT: Message.assistant_message,
            ROLE_TYPE.TOOL: Message.tool_message,
        }
        
        if role not in message_map:
            raise ValueError(f"Unsupported message role: {role}")
        
        msg_kwargs = {}
        if base64_image:
            msg_kwargs["base64_image"] = base64_image
        if role == ROLE_TYPE.TOOL:
            msg_kwargs.update(kwargs)
        
        self.memory.add_message(message_map[role](content, **msg_kwargs))
        agent_logger.debug(f"Message added to memory: {role} - {content[:50]}...")
    
    async def run(self, request: Optional[str] = None) -> str:
        """执行 Agent 的主循环"""
        if self.state != AgentState.IDLE:
            raise RuntimeError(f"Cannot run agent from state: {self.state}")
        
        # 重置状态
        self.current_step = 0
        self._cancelled = False
        
        # 添加初始请求
        if request:
            self.update_memory(ROLE_TYPE.USER, request)
        
        results: List[str] = []
        
        try:
            async with self.state_context(AgentState.RUNNING):
                while self.current_step < self.config.max_steps and not self._cancelled:
                    self.current_step += 1
                    agent_logger.info(f"Agent {self.name} executing step {self.current_step}/{self.config.max_steps}")
                    
                    # 检查是否卡住
                    if self.is_stuck():
                        self.handle_stuck_state()
                    
                    # 执行步骤
                    try:
                        step_result = await asyncio.wait_for(
                            self.step(),
                            timeout=self.config.execution_timeout
                        )
                        results.append(f"Step {self.current_step}: {step_result}")
                    except asyncio.TimeoutError:
                        agent_logger.warning(f"Agent {self.name} step {self.current_step} timed out")
                        results.append(f"Step {self.current_step}: Timeout")
                        break
                    
                    # 检查是否完成
                    if self.state == AgentState.FINISHED:
                        break
                
                if self.current_step >= self.config.max_steps:
                    agent_logger.info(f"Agent {self.name} reached max steps")
                    results.append(f"Terminated: Reached max steps ({self.config.max_steps})")
        
        finally:
            # 清理
            await self.cleanup()
            self.state = AgentState.IDLE
        
        return "\n".join(results) if results else "No steps executed"
    
    async def run_with_callback(self, request: str, callback: Callable[[str], None]) -> str:
        """带回调的执行方法"""
        # 此方法允许实时回调进度
        if self.state != AgentState.IDLE:
            raise RuntimeError(f"Cannot run agent from state: {self.state}")
        
        self.current_step = 0
        self._cancelled = False
        
        if request:
            self.update_memory(ROLE_TYPE.USER, request)
        
        try:
            async with self.state_context(AgentState.RUNNING):
                while self.current_step < self.config.max_steps and not self._cancelled:
                    self.current_step += 1
                    
                    if self.is_stuck():
                        self.handle_stuck_state()
                    
                    step_result = await self.step()
                    callback(f"Step {self.current_step}: {step_result}")
                    
                    if self.state == AgentState.FINISHED:
                        break
            
            return "Execution completed"
        finally:
            await self.cleanup()
            self.state = AgentState.IDLE
    
    def cancel(self):
        """取消执行"""
        self._cancelled = True
        agent_logger.info(f"Agent {self.name} execution cancelled")
    
    @abstractmethod
    async def step(self) -> str:
        """执行单步操作 - 子类必须实现"""
        pass
    
    def handle_stuck_state(self):
        """处理卡住状态"""
        stuck_prompt = "Observed repetitive responses. Please reconsider your approach and explore alternative strategies."
        self.next_step_prompt = f"{stuck_prompt}\n{self.next_step_prompt or ''}"
        agent_logger.warning(f"Agent {self.name} detected stuck state")
    
    def is_stuck(self) -> bool:
        """检查是否卡住"""
        messages = self.memory.messages
        if len(messages) < 2:
            return False
        
        last_message = messages[-1]
        if not last_message.content or last_message.role != ROLE_TYPE.ASSISTANT:
            return False
        
        duplicate_count = sum(
            1 for msg in reversed(messages[:-1])
            if msg.role == ROLE_TYPE.ASSISTANT and msg.content == last_message.content
        )
        
        return duplicate_count >= self.config.duplicate_threshold
    
    async def cleanup(self):
        """清理资源"""
        agent_logger.debug(f"Agent {self.name} cleaning up")
    
    def reset(self):
        """重置 Agent 状态"""
        self.state = AgentState.IDLE
        self.current_step = 0
        self.memory.clear()
        self._cancelled = False
        agent_logger.info(f"Agent {self.name} reset")
    
    @property
    def messages(self) -> List[Message]:
        """获取消息列表"""
        return self.memory.messages
    
    @messages.setter
    def messages(self, value: List[Message]):
        """设置消息列表"""
        self.memory.messages = value
    
    def get_system_prompt(self) -> str:
        """获取系统提示词"""
        return self.system_prompt or ""
    
    def set_system_prompt(self, prompt: str):
        """设置系统提示词"""
        self.system_prompt = prompt
        agent_logger.debug(f"Agent {self.name} system prompt updated")


class ToolCallingAgent(BaseAgent):
    """
    支持工具调用的 Agent 基类
    """
    
    tools: List[Any] = Field(default_factory=list)
    
    def register_tool(self, tool: Any):
        """注册工具"""
        self.tools.append(tool)
        agent_logger.debug(f"Tool registered: {getattr(tool, 'name', str(tool))}")
    
    def unregister_tool(self, tool_name: str):
        """注销工具"""
        self.tools = [t for t in self.tools if getattr(t, 'name', str(t)) != tool_name]
    
    def get_tools(self) -> List[Any]:
        """获取所有工具"""
        return self.tools
    
    def get_tool_by_name(self, tool_name: str) -> Optional[Any]:
        """按名称获取工具"""
        for tool in self.tools:
            if getattr(tool, 'name', None) == tool_name:
                return tool
        return None
    
    async def call_tool(self, tool_name: str, **kwargs) -> Any:
        """调用工具"""
        tool = self.get_tool_by_name(tool_name)
        if not tool:
            raise ValueError(f"Tool not found: {tool_name}")
        
        agent_logger.info(f"Calling tool: {tool_name} with args: {kwargs}")
        
        try:
            if hasattr(tool, 'async_call'):
                result = await tool.async_call(**kwargs)
            elif hasattr(tool, '__call__'):
                result = tool(**kwargs)
            else:
                result = await self._execute_tool(tool, **kwargs)
            
            agent_logger.debug(f"Tool {tool_name} returned: {str(result)[:100]}...")
            return result
        except Exception as e:
            agent_logger.error(f"Tool {tool_name} failed: {e}")
            raise
    
    async def _execute_tool(self, tool, **kwargs) -> Any:
        """执行工具的通用方法"""
        # 默认实现 - 子类可以重写
        if hasattr(tool, 'run'):
            return await tool.run(**kwargs)
        raise NotImplementedError(f"Cannot execute tool: {tool}")


class ReActAgent(ToolCallingAgent):
    """
    ReAct 风格的 Agent
    
    实现 Reason-Action 循环模式：
    1. 思考当前状态
    2. 决定下一步行动
    3. 执行行动
    4. 观察结果
    """
    
    thought_pattern: str = Field(
        default="I need to {reason}. I'll {action}.",
        description="思考模式模板"
    )
    
    async def step(self) -> str:
        """执行 ReAct 步骤"""
        # 1. 思考
        thought = await self.think()
        self.update_memory(ROLE_TYPE.ASSISTANT, f"思考: {thought}")
        
        # 2. 决定行动
        action = await self.decide_action()
        
        # 3. 执行行动
        if action.get("tool"):
            result = await self.execute_action(action)
            self.update_memory(ROLE_TYPE.TOOL, str(result))
        else:
            result = action.get("response", "")
            self.update_memory(ROLE_TYPE.ASSISTANT, result)
        
        return f"Thought: {thought}, Action: {action.get('tool', 'finish')}, Result: {str(result)[:50]}..."
    
    async def think(self) -> str:
        """生成思考内容"""
        # 子类实现具体的思考逻辑
        return "Analyzing the current situation..."
    
    async def decide_action(self) -> Dict[str, Any]:
        """决定下一步行动"""
        # 返回格式: {"tool": "tool_name", "args": {...}} 或 {"response": "直接回复"}
        return {"response": "任务已完成"}
    
    async def execute_action(self, action: Dict[str, Any]) -> Any:
        """执行行动"""
        tool_name = action.get("tool")
        args = action.get("args", {})
        return await self.call_tool(tool_name, **args)


# 便捷函数
def create_agent(agent_class: Type[BaseAgent], **kwargs) -> BaseAgent:
    """创建 Agent 实例"""
    agent = agent_class(**kwargs)
    agent_logger.info(f"Agent created: {agent.name}")
    return agent


async def run_agent(agent: BaseAgent, request: str) -> str:
    """运行 Agent"""
    try:
        return await agent.run(request)
    except Exception as e:
        agent_logger.error(f"Agent execution failed: {e}")
        raise

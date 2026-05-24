"""
DataAgent - Tool Framework
统一的工具框架，提供标准化的工具调用流程
"""
import asyncio
import inspect
import json
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Union, Callable, Type, get_type_hints

from pydantic import BaseModel, Field, ValidationError, create_model

from .config import config_manager
from .logging import tool_logger


class ToolParameter(BaseModel):
    """工具参数定义"""
    name: str = Field(..., description="参数名称")
    type: str = Field(..., description="参数类型 (string, number, integer, boolean, array, object)")
    description: str = Field("", description="参数描述")
    required: bool = Field(True, description="是否必填")
    default: Any = Field(None, description="默认值")
    enum: Optional[List[Any]] = Field(None, description="可选值列表")


class ToolSchema(BaseModel):
    """工具 Schema 定义"""
    name: str = Field(..., description="工具名称")
    description: str = Field("", description="工具描述")
    parameters: List[ToolParameter] = Field(default_factory=list, description="参数列表")
    returns: Optional[str] = Field(None, description="返回值类型描述")
    tags: List[str] = Field(default_factory=list, description="标签")


class ToolResult(BaseModel):
    """工具执行结果"""
    success: bool = Field(True, description="是否成功")
    output: Any = Field(None, description="输出结果")
    error: Optional[str] = Field(None, description="错误信息")
    base64_image: Optional[str] = Field(None, description="Base64编码的图片")
    system: Optional[str] = Field(None, description="系统消息")
    
    class Config:
        arbitrary_types_allowed = True
    
    def __bool__(self):
        return self.success
    
    def __str__(self):
        if self.error:
            return f"Error: {self.error}"
        return str(self.output) if self.output else ""
    
    @classmethod
    def success(cls, output: Any = None, **kwargs) -> 'ToolResult':
        """创建成功结果"""
        return cls(success=True, output=output, **kwargs)
    
    @classmethod
    def error(cls, message: str, **kwargs) -> 'ToolResult':
        """创建错误结果"""
        return cls(success=False, error=message, **kwargs)


class BaseTool(ABC, BaseModel):
    """
    工具抽象基类
    
    提供标准化的工具接口：
    - 工具注册
    - 参数验证
    - 执行流程
    - 结果处理
    """
    
    name: str = Field(..., description="工具名称")
    description: str = Field("", description="工具描述")
    
    class Config:
        arbitrary_types_allowed = True
    
    @abstractmethod
    async def execute(self, **kwargs) -> ToolResult:
        """执行工具 - 子类必须实现"""
        pass
    
    async def __call__(self, **kwargs) -> ToolResult:
        """调用工具"""
        tool_logger.info(f"Calling tool: {self.name}")
        
        try:
            # 参数验证
            validated_args = await self._validate_parameters(kwargs)
            
            # 执行工具
            result = await self.execute(**validated_args)
            
            # 结果处理
            if not isinstance(result, ToolResult):
                result = ToolResult.success(result)
            
            tool_logger.debug(f"Tool {self.name} executed successfully")
            return result
            
        except ValidationError as e:
            tool_logger.error(f"Tool {self.name} parameter validation failed: {e}")
            return ToolResult.error(f"参数验证失败: {e.errors()}")
        except Exception as e:
            tool_logger.error(f"Tool {self.name} execution failed: {e}", exc_info=True)
            return ToolResult.error(str(e))
    
    async def _validate_parameters(self, kwargs: Dict[str, Any]) -> Dict[str, Any]:
        """验证参数"""
        schema = self.get_schema()
        if not schema.parameters:
            return kwargs
        
        # 创建验证模型
        fields = {}
        for param in schema.parameters:
            field_type = self._get_python_type(param.type)
            if param.required:
                fields[param.name] = (field_type, Field(..., description=param.description))
            else:
                fields[param.name] = (field_type, Field(param.default, description=param.description))
        
        if fields:
            ValidationModel = create_model(f"Tool{self.name}Params", **fields)
            return ValidationModel(**kwargs).dict()
        
        return kwargs
    
    def _get_python_type(self, type_str: str) -> Type:
        """将类型字符串转换为 Python 类型"""
        type_map = {
            'string': str,
            'number': float,
            'integer': int,
            'boolean': bool,
            'array': list,
            'object': dict,
        }
        return type_map.get(type_str, str)
    
    def get_schema(self) -> ToolSchema:
        """获取工具 Schema"""
        return ToolSchema(
            name=self.name,
            description=self.description,
            parameters=[]
        )
    
    def to_openai_format(self) -> Dict[str, Any]:
        """转换为 OpenAI 函数调用格式"""
        schema = self.get_schema()
        
        properties = {}
        required = []
        
        for param in schema.parameters:
            properties[param.name] = {
                "type": param.type,
                "description": param.description
            }
            if param.enum:
                properties[param.name]["enum"] = param.enum
            if param.required:
                required.append(param.name)
        
        return {
            "type": "function",
            "function": {
                "name": schema.name,
                "description": schema.description,
                "parameters": {
                    "type": "object",
                    "properties": properties,
                    "required": required
                }
            }
        }


class ToolRegistry:
    """工具注册中心"""
    
    _instance = None
    _lock = asyncio.Lock()
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if not hasattr(self, '_initialized'):
            self._tools: Dict[str, BaseTool] = {}
            self._categories: Dict[str, List[str]] = {}
            self._initialized = True
    
    async def register_tool(self, tool: BaseTool):
        """注册工具"""
        async with self._lock:
            self._tools[tool.name] = tool
            tool_logger.info(f"Tool registered: {tool.name}")
    
    async def unregister_tool(self, tool_name: str):
        """注销工具"""
        async with self._lock:
            if tool_name in self._tools:
                del self._tools[tool_name]
                tool_logger.info(f"Tool unregistered: {tool_name}")
    
    async def get_tool(self, tool_name: str) -> Optional[BaseTool]:
        """获取工具"""
        return self._tools.get(tool_name)
    
    async def list_tools(self) -> List[BaseTool]:
        """获取所有工具"""
        return list(self._tools.values())
    
    async def list_tool_names(self) -> List[str]:
        """获取所有工具名称"""
        return list(self._tools.keys())
    
    async def get_tool_schemas(self) -> List[Dict[str, Any]]:
        """获取所有工具 Schema（OpenAI 格式）"""
        return [tool.to_openai_format() for tool in self._tools.values()]


class ToolCaller:
    """工具调用器"""
    
    def __init__(self, registry: ToolRegistry = None):
        self._registry = registry or ToolRegistry()
    
    async def call(self, tool_name: str, **kwargs) -> ToolResult:
        """调用工具"""
        tool = await self._registry.get_tool(tool_name)
        if not tool:
            tool_logger.error(f"Tool not found: {tool_name}")
            return ToolResult.error(f"工具 '{tool_name}' 不存在")
        
        tool_logger.info(f"Executing tool: {tool_name} with args: {kwargs}")
        
        try:
            result = await tool(**kwargs)
            return result
        except Exception as e:
            tool_logger.error(f"Error calling tool {tool_name}: {e}", exc_info=True)
            return ToolResult.error(str(e))
    
    async def batch_call(self, calls: List[Dict[str, Any]]) -> List[ToolResult]:
        """批量调用工具"""
        results = []
        for call in calls:
            tool_name = call.get("tool")
            args = call.get("args", {})
            result = await self.call(tool_name, **args)
            results.append(result)
        return results
    
    async def parallel_call(self, calls: List[Dict[str, Any]]) -> List[ToolResult]:
        """并行调用工具"""
        tasks = []
        for call in calls:
            tool_name = call.get("tool")
            args = call.get("args", {})
            tasks.append(self.call(tool_name, **args))
        
        return await asyncio.gather(*tasks)


class ToolDecorator:
    """工具装饰器"""
    
    @staticmethod
    def tool(name: str, description: str = "", **kwargs):
        """
        将函数装饰为工具
        
        Args:
            name: 工具名称
            description: 工具描述
            **kwargs: 其他工具属性
        """
        def decorator(func: Callable) -> Callable:
            # 提取参数信息
            sig = inspect.signature(func)
            params = []
            
            for param_name, param in sig.parameters.items():
                if param_name == 'self':
                    continue
                
                # 获取类型提示
                hints = get_type_hints(func)
                param_type = hints.get(param_name, str)
                type_str = ToolDecorator._type_to_string(param_type)
                
                # 获取默认值
                if param.default is not inspect.Parameter.empty:
                    required = False
                    default = param.default
                else:
                    required = True
                    default = None
                
                params.append({
                    "name": param_name,
                    "type": type_str,
                    "description": "",
                    "required": required,
                    "default": default
                })
            
            # 将函数转换为工具类
            class WrappedTool(BaseTool):
                _func = func
                _params = params
                
                def __init__(self):
                    super().__init__(name=name, description=description)
                
                async def execute(self, **kwargs) -> ToolResult:
                    try:
                        result = self._func(**kwargs)
                        # 处理同步和异步函数
                        if asyncio.iscoroutine(result):
                            result = await result
                        return ToolResult.success(result)
                    except Exception as e:
                        return ToolResult.error(str(e))
                
                def get_schema(self) -> ToolSchema:
                    parameters = [ToolParameter(**p) for p in self._params]
                    return ToolSchema(
                        name=self.name,
                        description=self.description,
                        parameters=parameters
                    )
            
            return WrappedTool
        
        return decorator
    
    @staticmethod
    def _type_to_string(python_type: Type) -> str:
        """将 Python 类型转换为字符串"""
        type_map = {
            str: "string",
            int: "integer",
            float: "number",
            bool: "boolean",
            list: "array",
            dict: "object",
        }
        return type_map.get(python_type, "string")


# 全局实例
tool_registry = ToolRegistry()
tool_caller = ToolCaller(tool_registry)


# 便捷函数
async def register_tool(tool: BaseTool):
    """注册工具"""
    await tool_registry.register_tool(tool)


async def call_tool(tool_name: str, **kwargs) -> ToolResult:
    """调用工具"""
    return await tool_caller.call(tool_name, **kwargs)


async def get_all_tools() -> List[BaseTool]:
    """获取所有工具"""
    return await tool_registry.list_tools()


async def get_tool_schemas() -> List[Dict[str, Any]]:
    """获取所有工具 Schema"""
    return await tool_registry.get_tool_schemas()

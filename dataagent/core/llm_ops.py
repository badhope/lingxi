"""
DataAgent - LLMOps 和 监控系统
提供模型调用追踪、性能监控、成本分析、A/B测试等功能
"""
import asyncio
import json
import time
import uuid
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field
from enum import Enum
from collections import defaultdict

from core.logging import get_logger
from core.database import db_manager

logger = get_logger("llm_ops")


class LLMProvider(str, Enum):
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    GEMINI = "gemini"
    DEEPSEEK = "deepseek"
    OLLAMA = "ollama"
    CUSTOM = "custom"


class LLMModel(str, Enum):
    # OpenAI
    GPT4 = "gpt-4"
    GPT35_TURBO = "gpt-3.5-turbo"
    GPT4O = "gpt-4o"
    # Anthropic
    CLAUDE3_SONNET = "claude-3-sonnet"
    CLAUDE3_HAIKU = "claude-3-haiku"
    # Other
    GEMINI_PRO = "gemini-pro"
    DEEPSEEK_CHAT = "deepseek-chat"


class LLMTraceStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"
    CACHED = "cached"


class LLMCallTrace(BaseModel):
    """LLM调用追踪记录"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    provider: LLMProvider
    model: str
    trace_id: Optional[str] = None
    user_id: Optional[str] = None
    prompt: str
    response: Optional[str] = None
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0
    cost: float = 0.0
    status: LLMTraceStatus = LLMTraceStatus.PENDING
    start_time: float = Field(default_factory=time.time)
    end_time: Optional[float] = None
    duration: Optional[float] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
    tags: List[str] = Field(default_factory=list)
    error: Optional[str] = None


class ModelMetrics(BaseModel):
    """模型性能指标"""
    model: str
    provider: str
    total_calls: int = 0
    success_count: int = 0
    failure_count: int = 0
    avg_latency: float = 0.0
    avg_prompt_tokens: float = 0.0
    avg_completion_tokens: float = 0.0
    total_cost: float = 0.0
    cache_hit_rate: float = 0.0
    last_call_time: Optional[float] = None


class CostConfig(BaseModel):
    """模型成本配置"""
    provider: str
    model: str
    input_cost_per_1k: float
    output_cost_per_1k: float


class CostManager:
    """成本管理器"""
    
    def __init__(self):
        self.cost_configs: Dict[str, CostConfig] = {}
        self._init_default_costs()
    
    def _init_default_costs(self):
        """初始化默认成本配置"""
        default_costs = [
            CostConfig(provider="openai", model="gpt-4", input_cost_per_1k=0.03, output_cost_per_1k=0.06),
            CostConfig(provider="openai", model="gpt-3.5-turbo", input_cost_per_1k=0.0015, output_cost_per_1k=0.002),
            CostConfig(provider="openai", model="gpt-4o", input_cost_per_1k=0.01, output_cost_per_1k=0.03),
            CostConfig(provider="anthropic", model="claude-3-sonnet", input_cost_per_1k=0.003, output_cost_per_1k=0.015),
            CostConfig(provider="anthropic", model="claude-3-haiku", input_cost_per_1k=0.00025, output_cost_per_1k=0.00125),
        ]
        for config in default_costs:
            key = f"{config.provider}:{config.model}"
            self.cost_configs[key] = config
    
    def calculate_cost(self, provider: str, model: str, prompt_tokens: int, completion_tokens: int) -> float:
        """计算调用成本"""
        key = f"{provider}:{model}"
        if key not in self.cost_configs:
            # 尝试模糊匹配
            for config_key, config in self.cost_configs.items():
                if config.provider == provider and model.startswith(config.model):
                    break
            else:
                return 0.0
        else:
            config = self.cost_configs[key]
        
        input_cost = (prompt_tokens / 1000.0) * config.input_cost_per_1k
        output_cost = (completion_tokens / 1000.0) * config.output_cost_per_1k
        return input_cost + output_cost


class LLMOps:
    """LLMOps 管理器"""
    
    def __init__(self):
        self.traces: List[LLMCallTrace] = []
        self.traces_by_id: Dict[str, LLMCallTrace] = {}
        self.metrics: Dict[str, ModelMetrics] = {}
        self.cost_manager = CostManager()
        self.cache: Dict[str, Dict[str, Any]] = {}
        self.max_cache_size = 1000
        self._init_metrics()
    
    def _init_metrics(self):
        """初始化指标"""
        # 预初始化一些常用模型的指标
        for provider in LLMProvider:
            for model in LLMModel:
                key = f"{provider}:{model}"
                self.metrics[key] = ModelMetrics(model=model, provider=provider)
    
    def start_trace(
        self,
        provider: LLMProvider,
        model: str,
        prompt: str,
        user_id: Optional[str] = None,
        tags: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None,
        trace_id: Optional[str] = None
    ) -> LLMCallTrace:
        """开始LLM调用追踪"""
        trace = LLMCallTrace(
            provider=provider,
            model=model,
            prompt=prompt,
            user_id=user_id,
            tags=tags or [],
            metadata=metadata or {},
            trace_id=trace_id or str(uuid.uuid4()),
            status=LLMTraceStatus.RUNNING,
            start_time=time.time()
        )
        self.traces.append(trace)
        self.traces_by_id[trace.id] = trace
        
        # 检查缓存
        cache_key = self._get_cache_key(provider, model, prompt)
        if cache_key in self.cache:
            cached = self.cache[cache_key]
            trace.response = cached["response"]
            trace.status = LLMTraceStatus.CACHED
            trace.end_time = time.time()
            trace.duration = 0
            self._update_metrics(trace)
            logger.info(f"缓存命中: {model}")
            return trace
        
        logger.info(f"开始LLM调用: {model}")
        return trace
    
    def end_trace(
        self,
        trace: LLMCallTrace,
        response: str,
        prompt_tokens: int = 0,
        completion_tokens: int = 0,
        success: bool = True,
        error: Optional[str] = None
    ) -> LLMCallTrace:
        """结束LLM调用追踪"""
        trace.end_time = time.time()
        trace.duration = trace.end_time - trace.start_time
        trace.response = response
        trace.prompt_tokens = prompt_tokens
        trace.completion_tokens = completion_tokens
        trace.total_tokens = prompt_tokens + completion_tokens
        
        if success and not error:
            trace.status = LLMTraceStatus.SUCCESS
            # 计算成本
            trace.cost = self.cost_manager.calculate_cost(
                trace.provider.value,
                trace.model,
                prompt_tokens,
                completion_tokens
            )
            # 缓存结果
            cache_key = self._get_cache_key(trace.provider, trace.model, trace.prompt)
            if len(self.cache) >= self.max_cache_size:
                # 简单的LRU：移除最旧的
                oldest_key = next(iter(self.cache))
                del self.cache[oldest_key]
            self.cache[cache_key] = {"response": response, "time": time.time()}
        else:
            trace.status = LLMTraceStatus.FAILED
            trace.error = error
        
        self._update_metrics(trace)
        logger.info(f"LLM调用完成: {trace.model}, 耗时: {trace.duration:.2f}s, 成本: ${trace.cost:.4f}")
        
        return trace
    
    def _get_cache_key(self, provider: LLMProvider, model: str, prompt: str) -> str:
        """生成缓存键"""
        import hashlib
        key = f"{provider}:{model}:{prompt}"
        return hashlib.md5(key.encode()).hexdigest()
    
    def _update_metrics(self, trace: LLMCallTrace):
        """更新模型指标"""
        key = f"{trace.provider}:{trace.model}"
        if key not in self.metrics:
            self.metrics[key] = ModelMetrics(
                model=trace.model,
                provider=trace.provider.value
            )
        
        metrics = self.metrics[key]
        metrics.total_calls += 1
        
        if trace.status == LLMTraceStatus.SUCCESS or trace.status == LLMTraceStatus.CACHED:
            metrics.success_count += 1
        else:
            metrics.failure_count += 1
        
        if trace.status == LLMTraceStatus.CACHED:
            total = metrics.total_calls
            metrics.cache_hit_rate = (metrics.cache_hit_rate * (total - 1) + 1) / total
        
        if trace.duration is not None:
            total = metrics.success_count
            if total > 0:
                metrics.avg_latency = (metrics.avg_latency * (total - 1) + trace.duration) / total
        
        if trace.prompt_tokens > 0:
            total = metrics.success_count
            if total > 0:
                metrics.avg_prompt_tokens = (metrics.avg_prompt_tokens * (total - 1) + trace.prompt_tokens) / total
        
        if trace.completion_tokens > 0:
            total = metrics.success_count
            if total > 0:
                metrics.avg_completion_tokens = (metrics.avg_completion_tokens * (total - 1) + trace.completion_tokens) / total
        
        metrics.total_cost += trace.cost
        metrics.last_call_time = trace.end_time or time.time()
    
    def get_model_metrics(self, provider: str, model: str) -> Optional[ModelMetrics]:
        """获取模型指标"""
        key = f"{provider}:{model}"
        return self.metrics.get(key)
    
    def get_all_metrics(self) -> List[ModelMetrics]:
        """获取所有模型指标"""
        return list(self.metrics.values())
    
    def get_traces(
        self,
        provider: Optional[str] = None,
        model: Optional[str] = None,
        user_id: Optional[str] = None,
        status: Optional[LLMTraceStatus] = None,
        start_time: Optional[float] = None,
        end_time: Optional[float] = None,
        limit: int = 100
    ) -> List[LLMCallTrace]:
        """查询追踪记录"""
        filtered = self.traces
        
        if provider:
            filtered = [t for t in filtered if t.provider.value == provider]
        if model:
            filtered = [t for t in filtered if model in t.model]
        if user_id:
            filtered = [t for t in filtered if t.user_id == user_id]
        if status:
            filtered = [t for t in filtered if t.status == status]
        if start_time:
            filtered = [t for t in filtered if t.start_time >= start_time]
        if end_time:
            filtered = [t for t in filtered if t.start_time <= end_time]
        
        return filtered[-limit:]
    
    def get_cost_summary(self, days: int = 30) -> Dict[str, Any]:
        """获取成本汇总"""
        cutoff = time.time() - (days * 24 * 3600)
        filtered_traces = [t for t in self.traces if t.start_time >= cutoff]
        
        cost_by_model = defaultdict(float)
        cost_by_provider = defaultdict(float)
        total_cost = 0.0
        total_calls = 0
        avg_duration = 0.0
        
        for trace in filtered_traces:
            if trace.cost > 0:
                key = f"{trace.provider}:{trace.model}"
                cost_by_model[key] += trace.cost
                cost_by_provider[trace.provider.value] += trace.cost
                total_cost += trace.cost
            
            if trace.duration:
                avg_duration = (avg_duration * total_calls + trace.duration) / (total_calls + 1)
                total_calls += 1
        
        return {
            "days": days,
            "total_cost": total_cost,
            "total_calls": len(filtered_traces),
            "avg_duration": avg_duration,
            "cost_by_model": dict(cost_by_model),
            "cost_by_provider": dict(cost_by_provider),
            "estimated_monthly_cost": total_cost * (30 / days)
        }
    
    def export_traces(self, format: str = "json") -> str:
        """导出追踪记录"""
        data = [
            {
                "id": t.id,
                "provider": t.provider.value,
                "model": t.model,
                "status": t.status.value,
                "prompt": t.prompt[:100],
                "prompt_tokens": t.prompt_tokens,
                "completion_tokens": t.completion_tokens,
                "total_tokens": t.total_tokens,
                "cost": t.cost,
                "duration": t.duration,
                "start_time": t.start_time,
                "user_id": t.user_id
            }
            for t in self.traces[-1000:]
        ]
        return json.dumps(data, ensure_ascii=False, indent=2)


class PromptVersion(BaseModel):
    """提示词版本"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    description: str = ""
    prompt: str
    version: str = "1.0"
    variables: List[str] = Field(default_factory=list)
    created_at: float = Field(default_factory=time.time)
    created_by: Optional[str] = None
    tags: List[str] = Field(default_factory=list)


class PromptManager:
    """提示词版本管理器"""
    
    def __init__(self):
        self.prompts: Dict[str, List[PromptVersion]] = {}
    
    def create_prompt(
        self,
        name: str,
        prompt: str,
        description: str = "",
        variables: Optional[List[str]] = None,
        created_by: Optional[str] = None,
        tags: Optional[List[str]] = None
    ) -> PromptVersion:
        """创建新提示词"""
        version = PromptVersion(
            name=name,
            description=description,
            prompt=prompt,
            variables=variables or [],
            created_by=created_by,
            tags=tags or []
        )
        
        if name not in self.prompts:
            self.prompts[name] = []
        self.prompts[name].append(version)
        
        logger.info(f"创建提示词: {name} (v{version.version})")
        return version
    
    def get_prompt(self, name: str, version: Optional[str] = None) -> Optional[PromptVersion]:
        """获取提示词"""
        if name not in self.prompts:
            return None
        
        versions = self.prompts[name]
        if version:
            for v in versions:
                if v.version == version:
                    return v
            return None
        return versions[-1]
    
    def list_prompts(self) -> List[PromptVersion]:
        """列出所有最新版本的提示词"""
        result = []
        for versions in self.prompts.values():
            if versions:
                result.append(versions[-1])
        return result


class ABTest(BaseModel):
    """A/B测试配置"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    description: str = ""
    variants: Dict[str, Dict[str, Any]]  # variant_id -> config
    traffic_split: Dict[str, float]
    metric: str = "user_satisfaction"
    start_time: float = Field(default_factory=time.time)
    end_time: Optional[float] = None
    results: Dict[str, Dict[str, Any]] = Field(default_factory=dict)


class ABTestManager:
    """A/B测试管理器"""
    
    def __init__(self, llm_ops: LLMOps):
        self.tests: Dict[str, ABTest] = {}
        self.llm_ops = llm_ops
    
    def create_test(
        self,
        name: str,
        variants: Dict[str, Dict[str, Any]],
        traffic_split: Dict[str, float],
        metric: str = "user_satisfaction"
    ) -> ABTest:
        """创建A/B测试"""
        total = sum(traffic_split.values())
        if not (0.999 <= total <= 1.001):
            raise ValueError("流量分配总和必须等于1")
        
        test = ABTest(
            name=name,
            variants=variants,
            traffic_split=traffic_split,
            metric=metric,
            results={v: {"impressions": 0, "conversions": 0, "revenue": 0} for v in variants}
        )
        self.tests[test.id] = test
        logger.info(f"创建A/B测试: {name}")
        return test
    
    def get_variant(self, test_id: str, user_id: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """获取分配的变体"""
        if test_id not in self.tests:
            return None
        
        test = self.tests[test_id]
        
        # 简单的哈希分桶
        if user_id:
            import hashlib
            hash_val = int(hashlib.md5(user_id.encode()).hexdigest(), 16)
        else:
            hash_val = int(time.time() * 1000)
        
        cumulative = 0.0
        for variant_id, weight in test.traffic_split.items():
            cumulative += weight
            if hash_val % 10000 / 10000 <= cumulative:
                test.results[variant_id]["impressions"] += 1
                return test.variants[variant_id]
        
        # 默认返回第一个
        first = next(iter(test.variants.values()))
        first_id = next(iter(test.variants.keys()))
        test.results[first_id]["impressions"] += 1
        return first
    
    def record_conversion(self, test_id: str, variant_id: str, revenue: float = 0.0):
        """记录转化"""
        if test_id in self.tests and variant_id in self.tests[test_id].results:
            self.tests[test_id].results[variant_id]["conversions"] += 1
            self.tests[test_id].results[variant_id]["revenue"] += revenue
    
    def get_test_results(self, test_id: str) -> Optional[Dict[str, Any]]:
        """获取测试结果"""
        if test_id not in self.tests:
            return None
        
        test = self.tests[test_id]
        results = {"name": test.name, "variants": {}}
        
        for variant_id, data in test.results.items():
            impressions = data["impressions"]
            conversions = data["conversions"]
            
            conversion_rate = conversions / impressions if impressions > 0 else 0
            avg_revenue = data["revenue"] / conversions if conversions > 0 else 0
            
            results["variants"][variant_id] = {
                **data,
                "conversion_rate": conversion_rate,
                "avg_revenue": avg_revenue
            }
        
        return results


# 全局实例
llm_ops = LLMOps()
prompt_manager = PromptManager()
ab_test_manager = ABTestManager(llm_ops)


__all__ = [
    "LLMProvider",
    "LLMModel",
    "LLMTraceStatus",
    "LLMCallTrace",
    "ModelMetrics",
    "LLMOps",
    "PromptManager",
    "PromptVersion",
    "ABTest",
    "ABTestManager",
    "llm_ops",
    "prompt_manager",
    "ab_test_manager"
]

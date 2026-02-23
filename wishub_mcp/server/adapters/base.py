"""
AI Model Adapter Base Class
"""
from abc import ABC, abstractmethod
from typing import Dict, Any


class BaseAIAdapter(ABC):
    """AI 模型适配器基类"""

    model_id: str

    def __init__(self, model_id: str, api_key: str):
        """初始化适配器"""
        self.model_id = model_id
        self.api_key = api_key

    @abstractmethod
    async def generate(
        self,
        prompt: str,
        context: Dict[str, Any],
        max_tokens: int,
        temperature: float
    ) -> str:
        """生成 AI 响应"""
        pass

    @abstractmethod
    async def count_tokens(self, text: str) -> int:
        """计算 Token 数量"""
        pass

    @abstractmethod
    def validate_config(self, config: Dict[str, Any]) -> bool:
        """验证配置"""
        pass


class AIAdapterRegistry:
    """AI 适配器注册表"""

    _adapters: Dict[str, BaseAIAdapter] = {}

    @classmethod
    def register(cls, model_id: str, adapter: BaseAIAdapter):
        """注册适配器"""
        cls._adapters[model_id] = adapter

    @classmethod
    def get(cls, model_id: str) -> BaseAIAdapter:
        """获取适配器"""
        if model_id not in cls._adapters:
            raise ValueError(f"Unsupported model: {model_id}")
        return cls._adapters[model_id]

    @classmethod
    def list_models(cls) -> list:
        """列出所有支持的模型"""
        return list(cls._adapters.keys())

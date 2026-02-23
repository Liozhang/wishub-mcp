"""
AI Adapter Factory
"""
from typing import Dict, Any
import logging

from wishub_mcp.monitoring.logging_config import get_logger
from .base import BaseAIAdapter, AIAdapterRegistry
from .openai import OpenAIAdapter
from .zhipu import ZhipuAdapter

logger = get_logger(__name__)


class AIAdapterFactory:
    """AI 适配器工厂"""

    # 模型 ID 到适配器类的映射
    MODEL_ADAPTERS = {
        # OpenAI 模型
        "gpt-4": OpenAIAdapter,
        "gpt-4-turbo": OpenAIAdapter,
        "gpt-4o": OpenAIAdapter,
        "gpt-3.5-turbo": OpenAIAdapter,

        # 智谱模型
        "glm-4": ZhipuAdapter,
        "glm-4-turbo": ZhipuAdapter,
        "glm-3-turbo": ZhipuAdapter,
    }

    @classmethod
    def create_adapter(cls, model_id: str, api_key: str) -> BaseAIAdapter:
        """
        创建适配器实例

        Args:
            model_id: 模型 ID
            api_key: API 密钥

        Returns:
            AI 适配器实例

        Raises:
            ValueError: 如果模型不支持
        """
        if model_id not in cls.MODEL_ADAPTERS:
            raise ValueError(f"不支持的模型: {model_id}")

        adapter_class = cls.MODEL_ADAPTERS[model_id]
        adapter = adapter_class(model_id, api_key)

        logger.info("adapter_created", model_id=model_id)

        return adapter

    @classmethod
    def register_adapter(cls, model_id: str, adapter_class: type):
        """
        注册自定义适配器

        Args:
            model_id: 模型 ID
            adapter_class: 适配器类（继承自 BaseAIAdapter）
        """
        if not issubclass(adapter_class, BaseAIAdapter):
            raise TypeError("适配器必须继承自 BaseAIAdapter")

        cls.MODEL_ADAPTERS[model_id] = adapter_class
        logger.info("adapter_registered", model_id=model_id)

    @classmethod
    def list_supported_models(cls) -> list:
        """列出所有支持的模型"""
        return list(cls.MODEL_ADAPTERS.keys())

    @classmethod
    def initialize_adapters(cls, config: Dict[str, str]) -> None:
        """
        初始化并注册所有适配器

        Args:
            config: 配置字典，包含各个 API 密钥
                {
                    "openai_api_key": "...",
                    "zhipu_api_key": "..."
                }
        """
        # OpenAI 适配器
        openai_api_key = config.get("openai_api_key") or config.get("OPENAI_API_KEY")
        if openai_api_key:
            for model_id in ["gpt-4", "gpt-4-turbo", "gpt-4o", "gpt-3.5-turbo"]:
                try:
                    adapter = cls.create_adapter(model_id, openai_api_key)
                    AIAdapterRegistry.register(model_id, adapter)
                except Exception as e:
                    logger.warning(
                        "adapter_registration_failed",
                        model_id=model_id,
                        error=str(e)
                    )

        # 智谱适配器
        zhipu_api_key = config.get("zhipu_api_key") or config.get("ZHIPU_API_KEY")
        if zhipu_api_key:
            for model_id in ["glm-4", "glm-4-turbo", "glm-3-turbo"]:
                try:
                    adapter = cls.create_adapter(model_id, zhipu_api_key)
                    AIAdapterRegistry.register(model_id, adapter)
                except Exception as e:
                    logger.warning(
                        "adapter_registration_failed",
                        model_id=model_id,
                        error=str(e)
                    )

        adapter_count = len(AIAdapterRegistry._adapters)
        logger.info("adapters_initialized", count=adapter_count)

    @classmethod
    def get_redis_client(cls):
        """
        获取 Redis 客户端（用于健康检查）

        Returns:
            Redis 客户端实例
        """
        try:
            from wishub_mcp.server.cache import get_cache_manager
            cache_manager = get_cache_manager()
            if cache_manager and cache_manager._client:
                return cache_manager._client
        except Exception as e:
            logger.warning("redis_client_get_failed", error=str(e))
        return None

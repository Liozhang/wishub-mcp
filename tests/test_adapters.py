"""
Test AI Adapters
"""
import pytest
from wishub_mcp.server.adapters import (
    AIAdapterFactory,
    AIAdapterRegistry,
    BaseAIAdapter
)
from typing import Dict, Any


class MockAdapter(BaseAIAdapter):
    """Mock 适配器用于测试"""

    async def generate(self, prompt: str, context: Dict[str, Any],
                      max_tokens: int, temperature: float) -> str:
        return f"Mock response for: {prompt}"

    async def count_tokens(self, text: str) -> int:
        return len(text.split())

    def validate_config(self, config: Dict[str, Any]) -> bool:
        return True


def test_adapter_registry():
    """测试适配器注册表"""
    # 创建 mock 适配器
    adapter = MockAdapter("mock-model", "test-key")

    # 注册适配器
    AIAdapterRegistry.register("mock-model", adapter)

    # 获取适配器
    retrieved = AIAdapterRegistry.get("mock-model")
    assert retrieved is adapter

    # 列出模型
    models = AIAdapterRegistry.list_models()
    assert "mock-model" in models


def test_adapter_factory():
    """测试适配器工厂"""
    # 列出支持的模型
    models = AIAdapterFactory.list_supported_models()

    # 验证包含已知模型
    assert "gpt-4" in models
    assert "glm-4" in models


def test_adapter_factory_custom_registration():
    """测试自定义适配器注册"""
    # 注册自定义适配器
    AIAdapterFactory.register_adapter("custom-model", MockAdapter)

    # 验证已注册
    models = AIAdapterFactory.list_supported_models()
    assert "custom-model" in models

    # 创建实例
    adapter = AIAdapterFactory.create_adapter("custom-model", "test-key")
    assert isinstance(adapter, MockAdapter)

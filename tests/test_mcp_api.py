"""
Test MCP API
"""
import pytest
from httpx import AsyncClient

from wishub_mcp.protocol.models import MCPInvokeRequest, ContextType


@pytest.mark.asyncio
async def test_mcp_invoke_success(client: AsyncClient, monkeypatch):
    """测试成功的 MCP 调用"""
    # Mock WisHub 核心客户端
    async def mock_get_context(*args, **kwargs):
        return {
            "wisunit_id": "test_001",
            "content": "这是测试上下文内容"
        }

    # Mock AI 适配器
    from wishub_mcp.server.adapters import AIAdapterRegistry, BaseAIAdapter
    from typing import Dict, Any

    class MockAdapter(BaseAIAdapter):
        async def generate(self, prompt: str, context: Dict[str, Any],
                          max_tokens: int, temperature: float) -> str:
            return "这是 AI 生成的回答"

        async def count_tokens(self, text: str) -> int:
            return len(text.split())

        def validate_config(self, config: Dict[str, Any]) -> bool:
            return True

    # 注册 mock 适配器
    mock_adapter = MockAdapter("gpt-4", "test_key")
    AIAdapterRegistry.register("gpt-4", mock_adapter)

    # 创建请求
    request = MCPInvokeRequest(
        context_id="test_001",
        model_id="gpt-4",
        prompt="测试问题",
        context_type=ContextType.WISUNIT
    )

    # 跳过 API 密钥验证
    response = await client.post(
        "/api/v1/mcp/invoke",
        json=request.model_dump(),
        headers={"X-API-Key": "test_key"}
    )

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert data["response"] == "这是 AI 生成的回答"


@pytest.mark.asyncio
async def test_mcp_invoke_unsupported_model(client: AsyncClient):
    """测试不支持的模型"""
    request = MCPInvokeRequest(
        context_id="test_001",
        model_id="unsupported-model",
        prompt="测试问题",
        context_type=ContextType.WISUNIT
    )

    response = await client.post(
        "/api/v1/mcp/invoke",
        json=request.model_dump(),
        headers={"X-API-Key": "test_key"}
    )

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "error"
    assert data["error"]["code"] == "MCP_002"


@pytest.mark.asyncio
async def test_list_models(client: AsyncClient):
    """测试列出模型"""
    response = await client.get("/api/v1/mcp/models")

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert "models" in data
    assert isinstance(data["models"], list)

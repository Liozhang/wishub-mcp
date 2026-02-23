"""
WisHub MCP Protocol Models Tests
"""
import pytest
from wishub_mcp.protocol.models import (
    ContextType,
    MCPInvokeRequest,
    MCPInvokeResponse,
    HealthCheckResponse
)


def test_context_type_enum():
    """测试 ContextType 枚举"""
    assert ContextType.WISUNIT == "wisunit"
    assert ContextType.KNOWLEDGE_GRAPH == "knowledge_graph"
    assert ContextType.WISDOM_CORE == "wisdom_core"


def test_mcp_invoke_request_valid():
    """测试有效的 MCPInvokeRequest"""
    request = MCPInvokeRequest(
        context_id="ctx_001",
        model_id="gpt-4",
        prompt="Hello, WisHub!"
    )

    assert request.context_id == "ctx_001"
    assert request.model_id == "gpt-4"
    assert request.prompt == "Hello, WisHub!"
    assert request.context_type == ContextType.WISUNIT
    assert request.max_tokens == 2000
    assert request.temperature == 0.7


def test_mcp_invoke_request_custom_params():
    """测试自定义参数的 MCPInvokeRequest"""
    request = MCPInvokeRequest(
        context_id="ctx_001",
        model_id="glm-4",
        prompt="测试提示",
        context_type=ContextType.KNOWLEDGE_GRAPH,
        max_tokens=1000,
        temperature=0.5
    )

    assert request.context_type == ContextType.KNOWLEDGE_GRAPH
    assert request.max_tokens == 1000
    assert request.temperature == 0.5


def test_mcp_invoke_request_invalid_max_tokens():
    """测试无效的 max_tokens"""
    with pytest.raises(ValueError):
        MCPInvokeRequest(
            context_id="ctx_001",
            model_id="gpt-4",
            prompt="Hello",
            max_tokens=10000  # 超过限制
        )


def test_mcp_invoke_response_success():
    """测试成功的 MCPInvokeResponse"""
    response = MCPInvokeResponse(
        status="success",
        context={"wisunit_id": "ctx_001"},
        response="Hello, user!",
        tokens_used=100
    )

    assert response.status == "success"
    assert response.context is not None
    assert response.response == "Hello, user!"
    assert response.tokens_used == 100


def test_mcp_invoke_response_error():
    """测试错误的 MCPInvokeResponse"""
    response = MCPInvokeResponse(
        status="error",
        error={
            "code": "MCP_001",
            "message": "上下文不存在"
        }
    )

    assert response.status == "error"
    assert response.error is not None
    assert response.error["code"] == "MCP_001"


def test_health_check_response():
    """测试健康检查响应"""
    response = HealthCheckResponse(
        status="healthy",
        version="0.1.0",
        dependencies={
            "redis": "ok",
            "wishub_core": "ok"
        }
    )

    assert response.status == "healthy"
    assert response.version == "0.1.0"
    assert response.dependencies["redis"] == "ok"

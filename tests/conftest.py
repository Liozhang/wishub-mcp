"""
WisHub MCP Pytest Configuration
"""
import pytest
import pytest_asyncio
from typing import AsyncGenerator
from httpx import AsyncClient, ASGITransport
from wishub_mcp.server.app import app


@pytest_asyncio.fixture
async def client() -> AsyncGenerator[AsyncClient, None]:
    """创建测试客户端"""
    transport = ASGITransport(app=app)
    async with AsyncClient(
        transport=transport,
        base_url="http://test"
    ) as ac:
        yield ac


@pytest.fixture
def sample_mcp_request():
    """示例 MCP 调用请求"""
    return {
        "context_id": "ctx_001",
        "model_id": "gpt-4",
        "prompt": "Hello, WisHub!",
        "max_tokens": 500,
        "temperature": 0.5
    }

"""
WisHub MCP Protocol Models
"""
from typing import Dict, Any, Optional
from pydantic import BaseModel, Field
from enum import Enum


class ContextType(str, Enum):
    """上下文类型"""
    WISUNIT = "wisunit"
    KNOWLEDGE_GRAPH = "knowledge_graph"
    WISDOM_CORE = "wisdom_core"


class MCPInvokeRequest(BaseModel):
    """MCP 调用请求"""
    context_id: str = Field(..., description="上下文 ID")
    model_id: str = Field(..., description="AI 模型 ID (如: gpt-4, glm-4)")
    prompt: str = Field(..., description="用户提示")
    context_type: ContextType = Field(
        default=ContextType.WISUNIT,
        description="上下文类型"
    )
    max_tokens: int = Field(
        default=2000,
        ge=1,
        le=8192,
        description="最大 Token 数"
    )
    temperature: float = Field(
        default=0.7,
        ge=0.0,
        le=2.0,
        description="温度参数"
    )


class MCPInvokeResponse(BaseModel):
    """MCP 调用响应"""
    status: str = Field(..., description="状态: success/error")
    context: Optional[Dict[str, Any]] = Field(
        default=None,
        description="上下文数据"
    )
    response: Optional[str] = Field(
        default=None,
        description="AI 响应"
    )
    tokens_used: Optional[int] = Field(
        default=None,
        description="使用的 Token 数"
    )
    message: Optional[str] = Field(
        default=None,
        description="消息"
    )
    error: Optional[Dict[str, Any]] = Field(
        default=None,
        description="错误信息"
    )


class HealthCheckResponse(BaseModel):
    """健康检查响应"""
    status: str = Field(..., description="状态: healthy/unhealthy")
    version: str = Field(..., description="版本号")
    dependencies: Dict[str, Any] = Field(
        default_factory=dict,
        description="依赖状态"
    )

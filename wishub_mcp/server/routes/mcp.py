"""
MCP Invocation Routes
"""
import logging
from typing import Dict, Any

from fastapi import APIRouter, HTTPException, status, Depends, Header
from fastapi.responses import JSONResponse

from wishub_mcp.protocol.models import (
    MCPInvokeRequest,
    MCPInvokeResponse,
    ContextType
)
from wishub_mcp.server.adapters import AIAdapterRegistry
from wishub_mcp.server.wishub_core import WisHubCoreClient
from wishub_mcp.config import settings

logger = logging.getLogger(__name__)

# 创建路由
router = APIRouter(prefix="/mcp", tags=["MCP"])

# 创建 WisHub 核心客户端
wishub_client = WisHubCoreClient()


async def verify_api_key(x_api_key: str = Header(..., alias="X-API-Key")):
    """验证 API 密钥（如果需要）"""
    if settings.AUTH_REQUIRED:
        # TODO: 实现 API 密钥验证逻辑
        # 这里暂时只检查是否为空
        if not x_api_key:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="缺少或无效的 API 密钥"
            )
    return x_api_key


@router.post(
    "/invoke",
    response_model=MCPInvokeResponse,
    summary="调用 MCP (Model Context Protocol)",
    description="使用指定的 AI 模型基于知识上下文回答问题"
)
async def invoke_mcp(
    request: MCPInvokeRequest,
    api_key: str = Depends(verify_api_key)
) -> MCPInvokeResponse:
    """
    MCP 调用端点

    从 WisHub 核心获取知识上下文，然后使用指定的 AI 模型生成回答。

    Args:
        request: MCP 调用请求
        api_key: API 密钥（从头部获取）

    Returns:
        MCP 调用响应

    Raises:
        HTTPException: 如果发生错误
    """
    try:
        # 1. 获取 AI 适配器
        try:
            adapter = AIAdapterRegistry.get(request.model_id)
        except ValueError as e:
            logger.warning(f"不支持的模型: {request.model_id}")
            return MCPInvokeResponse(
                status="error",
                message=f"不支持的模型: {request.model_id}",
                error={
                    "code": "MCP_002",
                    "details": str(e)
                }
            )

        # 2. 获取知识上下文
        context_data = None
        context_str = ""

        try:
            logger.info(f"获取上下文: {request.context_id} (类型: {request.context_type})")
            context_data = await wishub_client.get_knowledge_context(
                context_id=request.context_id,
                context_type=request.context_type.value
            )
            logger.info(f"成功获取上下文: {len(str(context_data))} 字符")

            # 构建上下文字符串用于提示
            context_str = _build_context_string(context_data)

        except RuntimeError as e:
            logger.warning(f"获取上下文失败: {e}")
            return MCPInvokeResponse(
                status="error",
                message=f"获取上下文失败: {str(e)}",
                error={
                    "code": "MCP_001",
                    "details": str(e)
                }
            )
        except Exception as e:
            logger.error(f"获取上下文时发生意外错误: {e}")
            return MCPInvokeResponse(
                status="error",
                message=f"获取上下文失败",
                error={
                    "code": "MCP_001",
                    "details": str(e)
                }
            )

        # 3. 计算 Token 数量
        try:
            prompt_tokens = await adapter.count_tokens(request.prompt)
            context_tokens = await adapter.count_tokens(context_str)
            total_input_tokens = prompt_tokens + context_tokens
        except Exception as e:
            logger.warning(f"计算 Token 数量失败: {e}")
            total_input_tokens = 0

        # 4. 检查 Token 限制
        if total_input_tokens > request.max_tokens * 0.9:  # 90% 阈值
            logger.warning(
                f"输入 Token 数量接近上限: {total_input_tokens}/{request.max_tokens}"
            )
            return MCPInvokeResponse(
                status="error",
                message=f"输入过长（Token 数量: {total_input_tokens}）",
                error={
                    "code": "MCP_003",
                    "details": f"输入 Token 数量: {total_input_tokens}, 最大限制: {request.max_tokens}"
                }
            )

        # 5. 生成 AI 响应
        try:
            logger.info(f"调用 AI 模型: {request.model_id}")
            response_text = await adapter.generate(
                prompt=request.prompt,
                context=context_data,
                max_tokens=request.max_tokens,
                temperature=request.temperature
            )

            # 计算输出 Token 数量
            output_tokens = await adapter.count_tokens(response_text)
            total_tokens = total_input_tokens + output_tokens

            logger.info(
                f"AI 响应生成成功: {output_tokens} 输出 tokens, "
                f"{total_tokens} 总 tokens"
            )

            return MCPInvokeResponse(
                status="success",
                context=context_data,
                response=response_text,
                tokens_used=total_tokens
            )

        except RuntimeError as e:
            logger.error(f"AI 模型调用失败: {e}")
            return MCPInvokeResponse(
                status="error",
                message=f"AI 模型调用失败: {str(e)}",
                error={
                    "code": "MCP_999",
                    "details": str(e)
                }
            )
        except Exception as e:
            logger.error(f"生成响应时发生意外错误: {e}")
            return MCPInvokeResponse(
                status="error",
                message="生成响应失败",
                error={
                    "code": "MCP_999",
                    "details": str(e)
                }
            )

    except Exception as e:
        logger.error(f"MCP 调用发生未处理的异常: {e}")
        return MCPInvokeResponse(
            status="error",
            message="内部服务器错误",
            error={
                "code": "MCP_999",
                "details": str(e)
            }
        )


@router.get(
    "/models",
    summary="列出所有支持的 AI 模型",
    description="返回所有可用的 AI 模型列表"
)
async def list_models() -> Dict[str, Any]:
    """列出所有支持的模型"""
    models = AIAdapterRegistry.list_models()
    return {
        "status": "success",
        "models": models,
        "count": len(models)
    }


def _build_context_string(context_data: Dict[str, Any]) -> str:
    """构建上下文字符串"""
    if not context_data:
        return ""

    parts = ["以下是相关的上下文信息：\n"]

    for key, value in context_data.items():
        if isinstance(value, (dict, list)):
            import json
            value_str = json.dumps(value, ensure_ascii=False, indent=2)
        else:
            value_str = str(value)

        parts.append(f"\n{key}:\n{value_str}")

    return "\n".join(parts)

"""
MCP Invocation Routes
"""
from typing import Dict, Any

from fastapi import APIRouter, HTTPException, status, Depends, Header

from wishub_mcp.protocol.models import (
    MCPInvokeRequest,
    MCPInvokeResponse,
    ContextType
)
from wishub_mcp.server.adapters import AIAdapterRegistry
from wishub_mcp.server.wishub_core import WisHubCoreClient
from wishub_mcp.config import settings
from wishub_mcp.monitoring.logging_config import get_logger
from wishub_mcp.monitoring.metrics import record_ai_invocation

logger = get_logger(__name__)

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
    import time

    start_time = time.time()

    try:
        # 1. 获取 AI 适配器
        try:
            adapter = AIAdapterRegistry.get(request.model_id)
        except ValueError as e:
            logger.warning("unsupported_model", model_id=request.model_id)
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
            logger.info(
                "fetching_context",
                context_id=request.context_id,
                context_type=request.context_type.value
            )
            context_data = await wishub_client.get_knowledge_context(
                context_id=request.context_id,
                context_type=request.context_type.value
            )
            context_len = len(str(context_data))
            logger.info("context_fetched", length=context_len)

            # 构建上下文字符串用于提示
            context_str = _build_context_string(context_data)

        except RuntimeError as e:
            logger.warning("context_fetch_failed", error=str(e))
            return MCPInvokeResponse(
                status="error",
                message=f"获取上下文失败: {str(e)}",
                error={
                    "code": "MCP_001",
                    "details": str(e)
                }
            )
        except Exception as e:
            logger.error("context_fetch_error", error=str(e))
            return MCPInvokeResponse(
                status="error",
                message=f"获取上下文失败",
                error={
                    "code": "MCP_001",
                    "details": str(e)
                }
            )

        # 3. 尝试从缓存获取响应（性能优化）
        try:
            from wishub_mcp.server.cache import get_cache_manager
            cache_manager = get_cache_manager()

            if cache_manager and cache_manager.enabled:
                cached_response = await cache_manager.get(
                    model_id=request.model_id,
                    prompt=request.prompt,
                    context_data=context_data,
                    temperature=request.temperature,
                    max_tokens=request.max_tokens
                )

                if cached_response:
                    logger.info("cache_hit", model_id=request.model_id)

                    # 记录指标
                    duration = time.time() - start_time
                    record_ai_invocation(
                        model=request.model_id,
                        status="cached",
                        duration=duration,
                        total_tokens=cached_response.get("tokens_used", 0)
                    )

                    return MCPInvokeResponse(
                        status="success",
                        context=context_data,
                        response=cached_response["response"],
                        tokens_used=cached_response["tokens_used"],
                        cached=True  # 标记为缓存响应
                    )
        except Exception as e:
            logger.warning("cache_check_failed", error=str(e))

        # 4. 计算 Token 数量
        try:
            prompt_tokens = await adapter.count_tokens(request.prompt)
            context_tokens = await adapter.count_tokens(context_str)
            total_input_tokens = prompt_tokens + context_tokens
        except Exception as e:
            logger.warning("token_count_failed", error=str(e))
            total_input_tokens = 0

        # 5. 检查 Token 限制
        if total_input_tokens > request.max_tokens * 0.9:  # 90% 阈值
            logger.warning(
                "input_too_long",
                total_input_tokens=total_input_tokens,
                max_tokens=request.max_tokens
            )
            return MCPInvokeResponse(
                status="error",
                message=f"输入过长（Token 数量: {total_input_tokens}）",
                error={
                    "code": "MCP_003",
                    "details": f"输入 Token 数量: {total_input_tokens}, 最大限制: {request.max_tokens}"
                }
            )

        # 6. 生成 AI 响应
        try:
            logger.info("generating_response", model_id=request.model_id)
            response_text = await adapter.generate(
                prompt=request.prompt,
                context=context_data,
                max_tokens=request.max_tokens,
                temperature=request.temperature
            )

            # 计算输出 Token 数量
            output_tokens = await adapter.count_tokens(response_text)
            total_tokens = total_input_tokens + output_tokens
            duration = time.time() - start_time

            logger.info(
                "response_generated",
                model_id=request.model_id,
                output_tokens=output_tokens,
                total_tokens=total_tokens,
                duration=f"{duration:.3f}s"
            )

            # 构建响应数据
            response_data = MCPInvokeResponse(
                status="success",
                context=context_data,
                response=response_text,
                tokens_used=total_tokens
            ).model_dump()

            # 缓存响应（性能优化）
            try:
                if cache_manager and cache_manager.enabled:
                    await cache_manager.set(
                        model_id=request.model_id,
                        prompt=request.prompt,
                        context_data=context_data,
                        temperature=request.temperature,
                        max_tokens=request.max_tokens,
                        response_data={
                            "response": response_text,
                            "tokens_used": total_tokens
                        }
                    )
            except Exception as e:
                logger.warning("cache_set_failed", error=str(e))

            # 记录指标
            record_ai_invocation(
                model=request.model_id,
                status="success",
                duration=duration,
                prompt_tokens=prompt_tokens,
                completion_tokens=output_tokens,
                total_tokens=total_tokens
            )

            return response_data

        except RuntimeError as e:
            logger.error("ai_generation_failed", error=str(e))
            record_ai_invocation(
                model=request.model_id,
                status="error",
                duration=time.time() - start_time
            )
            return MCPInvokeResponse(
                status="error",
                message=f"AI 模型调用失败: {str(e)}",
                error={
                    "code": "MCP_999",
                    "details": str(e)
                }
            )
        except Exception as e:
            logger.error("response_generation_error", error=str(e))
            record_ai_invocation(
                model=request.model_id,
                status="error",
                duration=time.time() - start_time
            )
            return MCPInvokeResponse(
                status="error",
                message="生成响应失败",
                error={
                    "code": "MCP_999",
                    "details": str(e)
                }
            )

    except Exception as e:
        logger.error("invoke_error", error=str(e))
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

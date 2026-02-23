"""
Prometheus 指标收集
"""
from prometheus_client import Counter, Histogram, Gauge, Info
from prometheus_fastapi_instrumentator import Instrumentator
from fastapi import FastAPI

# API 请求指标
http_requests_total = Counter(
    "wishub_mcp_http_requests_total",
    "Total HTTP requests",
    ["method", "endpoint", "status_code"]
)

# API 请求延迟
http_request_duration_seconds = Histogram(
    "wishub_mcp_http_request_duration_seconds",
    "HTTP request latency",
    ["method", "endpoint"]
)

# AI 调用指标
ai_invocations_total = Counter(
    "wishub_mcp_ai_invocations_total",
    "Total AI model invocations",
    ["model", "status"]
)

# AI 调用延迟
ai_invocation_duration_seconds = Histogram(
    "wishub_mcp_ai_invocation_duration_seconds",
    "AI invocation latency",
    ["model"]
)

# AI Token 使用
ai_tokens_total = Counter(
    "wishub_mcp_ai_tokens_total",
    "Total AI tokens used",
    ["model", "type"]  # type: prompt, completion, total
)

# 缓存指标
cache_operations_total = Counter(
    "wishub_mcp_cache_operations_total",
    "Total cache operations",
    ["operation", "status"]  # operation: get, set, delete; status: hit, miss
)

# Redis 连接指标
redis_connection_status = Gauge(
    "wishub_mcp_redis_connection_status",
    "Redis connection status (1=connected, 0=disconnected)"
)

# 应用信息
app_info = Info(
    "wishub_mcp_app_info",
    "Application information"
)


def setup_metrics(app: FastAPI) -> Instrumentator:
    """
    设置 Prometheus 指标收集

    Args:
        app: FastAPI 应用实例

    Returns:
        Instrumentator 实例
    """
    # 配置 FastAPI Instrumentator
    instrumentator = Instrumentator(
        should_group_status_codes=False,
        should_ignore_untemplated=True,
        should_instrument_requests_inprogress=True,
        should_instrument_requests=True,
        excluded_handlers=["/metrics", "/health", "/"],
        env_var_name="ENABLE_METRICS",
        inprogress_name="wishub_mcp_http_requests_inprogress",
        inprogress_labels=True,
    )

    instrumentator.instrument(app)

    return instrumentator


def record_ai_invocation(model: str, status: str, duration: float,
                        prompt_tokens: int = 0, completion_tokens: int = 0,
                        total_tokens: int = 0) -> None:
    """
    记录 AI 调用指标

    Args:
        model: AI 模型名称
        status: 调用状态
        duration: 调用耗时（秒）
        prompt_tokens: 提示词 Token 数
        completion_tokens: 完成 Token 数
        total_tokens: 总 Token 数
    """
    ai_invocations_total.labels(model=model, status=status).inc()
    ai_invocation_duration_seconds.labels(model=model).observe(duration)

    if prompt_tokens > 0:
        ai_tokens_total.labels(model=model, type="prompt").inc(prompt_tokens)
    if completion_tokens > 0:
        ai_tokens_total.labels(model=model, type="completion").inc(completion_tokens)
    if total_tokens > 0:
        ai_tokens_total.labels(model=model, type="total").inc(total_tokens)


def record_cache_operation(operation: str, status: str) -> None:
    """
    记录缓存操作指标

    Args:
        operation: 操作类型
        status: 操作状态
    """
    cache_operations_total.labels(operation=operation, status=status).inc()


def update_redis_connection_status(connected: bool) -> None:
    """
    更新 Redis 连接状态

    Args:
        connected: 是否连接
    """
    redis_connection_status.set(1 if connected else 0)


def set_app_info(version: str) -> None:
    """
    设置应用信息

    Args:
        version: 应用版本
    """
    app_info.info({
        "name": "wishub-mcp",
        "version": version
    })

"""
WisHub MCP Main Application
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
from contextlib import asynccontextmanager
from prometheus_client import generate_latest, CONTENT_TYPE_LATEST

from wishub_mcp.config import settings
from wishub_mcp.protocol.models import HealthCheckResponse
from wishub_mcp.server.adapters import AIAdapterFactory
from wishub_mcp.server.routes import mcp_router
from wishub_mcp.monitoring.logging_config import setup_logging, get_logger
from wishub_mcp.monitoring.metrics import setup_metrics, set_app_info
from wishub_mcp.monitoring.health import perform_health_checks, get_overall_status

# 配置结构化日志
setup_logging(
    log_level=settings.LOG_LEVEL,
    json_format=settings.APP_ENV != "development"
)
logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    # 启动
    logger.info(
        "starting",
        app_name=settings.APP_NAME,
        version=settings.APP_VERSION,
        environment=settings.APP_ENV
    )

    # 设置应用信息指标
    set_app_info(settings.APP_VERSION)

    # 初始化 AI 适配器
    try:
        logger.info("initializing_ai_adapters")
        AIAdapterFactory.initialize_adapters({
            "openai_api_key": settings.OPENAI_API_KEY,
            "zhipu_api_key": settings.ZHIPU_API_KEY
        })
        logger.info("ai_adapters_initialized")
    except Exception as e:
        logger.error("ai_adapters_initialization_failed", error=str(e))

    yield

    # 关闭
    logger.info("shutting_down", app_name=settings.APP_NAME)


# 创建 FastAPI 应用
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="WisHub MCP (Model Context Protocol) Server",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# CORS 中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 设置 Prometheus 指标
setup_metrics(app)

# 注册路由
app.include_router(mcp_router, prefix=settings.API_PREFIX)


@app.get("/", tags=["Root"])
async def root():
    """根路径"""
    return {
        "name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "status": "running"
    }


@app.get("/health", response_model=HealthCheckResponse, tags=["Health"])
async def health_check():
    """
    健康检查

    检查依赖服务的健康状态，包括：
    - Redis
    - WisHub 核心服务（如果配置）
    """
    # 获取 Redis 客户端（从适配器工厂）
    from wishub_mcp.server.adapters import AIAdapterFactory
    redis_client = AIAdapterFactory.get_redis_client()

    # 执行健康检查
    dependencies = await perform_health_checks(
        redis_client=redis_client,
        wishub_core_url=settings.WISHUB_CORE_URL
    )

    # 获取整体状态
    overall_status = get_overall_status(dependencies)

    return HealthCheckResponse(
        status=overall_status.value,
        version=settings.APP_VERSION,
        dependencies=dependencies
    )


@app.get("/metrics", tags=["Monitoring"])
async def metrics():
    """
    Prometheus 指标端点

    提供以下指标：
    - HTTP 请求计数和延迟
    - AI 调用计数、延迟和 Token 使用
    - 缓存操作统计
    - Redis 连接状态
    - 应用信息
    """
    return Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)


@app.get(f"{settings.API_PREFIX}/openapi.json", tags=["API"])
async def get_openapi():
    """获取 OpenAPI 规范"""
    return app.openapi()


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host=settings.API_HOST,
        port=settings.API_PORT,
        reload=settings.DEBUG
    )

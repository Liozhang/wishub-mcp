"""
WisHub MCP Main Application
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import logging

from wishub_mcp.config import settings
from wishub_mcp.protocol.models import HealthCheckResponse
from wishub_mcp.server.adapters import AIAdapterFactory
from wishub_mcp.server.routes import mcp_router

# 配置日志
logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    # 启动
    logger.info(f"🚀 {settings.APP_NAME} v{settings.APP_VERSION} 启动中...")

    # 初始化 AI 适配器
    try:
        logger.info("初始化 AI 适配器...")
        AIAdapterFactory.initialize_adapters({
            "openai_api_key": settings.OPENAI_API_KEY,
            "zhipu_api_key": settings.ZHIPU_API_KEY
        })
        logger.info("AI 适配器初始化完成")
    except Exception as e:
        logger.error(f"AI 适配器初始化失败: {e}")

    yield

    # 关闭
    logger.info(f"👋 {settings.APP_NAME} 已关闭")


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
    """健康检查"""
    # TODO: 实际检查依赖服务的健康状态
    return HealthCheckResponse(
        status="healthy",
        version=settings.APP_VERSION,
        dependencies={
            "redis": "ok",
            "wishub_core": "ok"
        }
    )


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

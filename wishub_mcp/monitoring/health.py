"""
健康检查模块
"""
from enum import Enum
from typing import Dict, Any
import httpx

from wishub_mcp.monitoring.metrics import update_redis_connection_status
from wishub_mcp.monitoring.logging_config import get_logger

logger = get_logger(__name__)


class HealthStatus(str, Enum):
    """健康状态"""
    HEALTHY = "healthy"
    UNHEALTHY = "unhealthy"
    DEGRADED = "degraded"


class DependencyHealth:
    """依赖服务健康状态"""

    def __init__(self, name: str, status: HealthStatus,
                 latency_ms: float = 0, message: str = ""):
        self.name = name
        self.status = status
        self.latency_ms = latency_ms
        self.message = message

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "status": self.status.value,
            "latency_ms": self.latency_ms,
            "message": self.message
        }


async def check_redis(redis_client) -> DependencyHealth:
    """
    检查 Redis 健康状态

    Args:
        redis_client: Redis 客户端

    Returns:
        DependencyHealth 实例
    """
    import time

    start_time = time.time()
    try:
        # 执行 PING 命令
        await redis_client.ping()
        latency_ms = (time.time() - start_time) * 1000

        update_redis_connection_status(True)
        logger.info("Redis health check passed", latency_ms=latency_ms)

        return DependencyHealth(
            name="redis",
            status=HealthStatus.HEALTHY,
            latency_ms=latency_ms
        )
    except Exception as e:
        update_redis_connection_status(False)
        logger.error("Redis health check failed", error=str(e))

        return DependencyHealth(
            name="redis",
            status=HealthStatus.UNHEALTHY,
            message=str(e)
        )


async def check_wishub_core(base_url: str, timeout: float = 5.0) -> DependencyHealth:
    """
    检查 WisHub 核心服务健康状态

    Args:
        base_url: WisHub 核心服务 URL
        timeout: 超时时间（秒）

    Returns:
        DependencyHealth 实例
    """
    import time

    start_time = time.time()
    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            # 尝试访问 WisHub 核心的健康检查端点
            response = await client.get(f"{base_url}/health")

            latency_ms = (time.time() - start_time) * 1000

            if response.status_code == 200:
                logger.info("WisHub Core health check passed", latency_ms=latency_ms)

                return DependencyHealth(
                    name="wishub_core",
                    status=HealthStatus.HEALTHY,
                    latency_ms=latency_ms
                )
            else:
                logger.warning("WisHub Core health check returned non-200 status",
                              status_code=response.status_code)

                return DependencyHealth(
                    name="wishub_core",
                    status=HealthStatus.UNHEALTHY,
                    message=f"Status code: {response.status_code}"
                )
    except httpx.TimeoutException:
        latency_ms = (time.time() - start_time) * 1000
        logger.error("WisHub Core health check timed out", latency_ms=latency_ms)

        return DependencyHealth(
            name="wishub_core",
            status=HealthStatus.UNHEALTHY,
            message="Connection timed out"
        )
    except Exception as e:
        latency_ms = (time.time() - start_time) * 1000
        logger.error("WisHub Core health check failed", error=str(e))

        return DependencyHealth(
            name="wishub_core",
            status=HealthStatus.UNHEALTHY,
            message=str(e)
        )


async def perform_health_checks(
    redis_client,
    wishub_core_url: str
) -> Dict[str, Dict[str, Any]]:
    """
    执行所有健康检查

    Args:
        redis_client: Redis 客户端
        wishub_core_url: WisHub 核心服务 URL

    Returns:
        健康检查结果字典
    """
    logger.info("Starting health checks")

    results = {}

    # 检查 Redis
    redis_health = await check_redis(redis_client)
    results[redis_health.name] = redis_health.to_dict()

    # 检查 WisHub 核心
    if wishub_core_url:
        core_health = await check_wishub_core(wishub_core_url)
        results[core_health.name] = core_health.to_dict()

    # 确定整体健康状态
    all_healthy = all(
        dep["status"] == HealthStatus.HEALTHY.value
        for dep in results.values()
    )

    if all_healthy:
        logger.info("All health checks passed")
    else:
        logger.warning("Some health checks failed", results=results)

    return results


def get_overall_status(dependencies: Dict[str, Dict[str, Any]]) -> HealthStatus:
    """
    获取整体健康状态

    Args:
        dependencies: 依赖服务健康检查结果

    Returns:
        整体健康状态
    """
    statuses = [dep["status"] for dep in dependencies.values()]

    if all(s == HealthStatus.HEALTHY.value for s in statuses):
        return HealthStatus.HEALTHY
    elif any(s == HealthStatus.UNHEALTHY.value for s in statuses):
        return HealthStatus.UNHEALTHY
    else:
        return HealthStatus.DEGRADED

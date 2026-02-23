"""
Redis 缓存层 - 性能优化
"""
import hashlib
import json
from typing import Any, Optional
import redis.asyncio as redis
from redis.asyncio import Redis

from wishub_mcp.monitoring.logging_config import get_logger
from wishub_mcp.monitoring.metrics import record_cache_operation

logger = get_logger(__name__)


class CacheManager:
    """缓存管理器 - 使用 Redis 缓存 AI 响应"""

    def __init__(
        self,
        redis_url: str = "redis://localhost:6379/0",
        default_ttl: int = 3600,  # 默认缓存 1 小时
        enabled: bool = True
    ):
        """
        初始化缓存管理器

        Args:
            redis_url: Redis 连接 URL
            default_ttl: 默认缓存过期时间（秒）
            enabled: 是否启用缓存
        """
        self.redis_url = redis_url
        self.default_ttl = default_ttl
        self.enabled = enabled
        self._client: Optional[Redis] = None

    async def connect(self) -> None:
        """连接到 Redis"""
        if not self.enabled:
            logger.info("cache_disabled")
            return

        try:
            self._client = redis.from_url(self.redis_url, decode_responses=True)
            # 测试连接
            await self._client.ping()
            logger.info("cache_connected", redis_url=self.redis_url)
        except Exception as e:
            logger.error("cache_connection_failed", error=str(e))
            self._client = None

    async def disconnect(self) -> None:
        """断开 Redis 连接"""
        if self._client:
            await self._client.close()
            logger.info("cache_disconnected")

    def _generate_cache_key(
        self,
        model_id: str,
        prompt: str,
        context_hash: str,
        temperature: float,
        max_tokens: int
    ) -> str:
        """
        生成缓存键

        Args:
            model_id: AI 模型 ID
            prompt: 用户提示
            context_hash: 上下文哈希值
            temperature: 温度参数
            max_tokens: 最大 Token 数

        Returns:
            缓存键
        """
        # 对提示进行哈希以避免过长的键
        prompt_hash = hashlib.sha256(prompt.encode()).hexdigest()

        # 组合键
        key_parts = [
            "wishub_mcp",
            model_id,
            prompt_hash[:16],  # 只取前 16 位
            context_hash,
            str(temperature),
            str(max_tokens)
        ]

        return ":".join(key_parts)

    def _hash_context(self, context_data: Any) -> str:
        """
        对上下文数据进行哈希

        Args:
            context_data: 上下文数据

        Returns:
            哈希值
        """
        if not context_data:
            return "empty"

        try:
            # 将上下文序列化为 JSON 并哈希
            context_str = json.dumps(context_data, sort_keys=True, ensure_ascii=False)
            return hashlib.sha256(context_str.encode()).hexdigest()
        except Exception:
            return "unhashable"

    async def get(
        self,
        model_id: str,
        prompt: str,
        context_data: Any,
        temperature: float,
        max_tokens: int
    ) -> Optional[dict]:
        """
        从缓存获取 AI 响应

        Args:
            model_id: AI 模型 ID
            prompt: 用户提示
            context_data: 上下文数据
            temperature: 温度参数
            max_tokens: 最大 Token 数

        Returns:
            缓存的响应数据，如果不存在返回 None
        """
        if not self.enabled or not self._client:
            return None

        try:
            context_hash = self._hash_context(context_data)
            cache_key = self._generate_cache_key(
                model_id, prompt, context_hash, temperature, max_tokens
            )

            # 从 Redis 获取
            cached_data = await self._client.get(cache_key)

            if cached_data:
                record_cache_operation("get", "hit")
                logger.debug("cache_hit", model_id=model_id, cache_key=cache_key)
                return json.loads(cached_data)
            else:
                record_cache_operation("get", "miss")
                logger.debug("cache_miss", model_id=model_id)
                return None

        except Exception as e:
            logger.error("cache_get_failed", error=str(e))
            record_cache_operation("get", "error")
            return None

    async def set(
        self,
        model_id: str,
        prompt: str,
        context_data: Any,
        temperature: float,
        max_tokens: int,
        response_data: dict,
        ttl: Optional[int] = None
    ) -> bool:
        """
        将 AI 响应存入缓存

        Args:
            model_id: AI 模型 ID
            prompt: 用户提示
            context_data: 上下文数据
            temperature: 温度参数
            max_tokens: 最大 Token 数
            response_data: 响应数据
            ttl: 缓存过期时间（秒），None 使用默认值

        Returns:
            是否成功
        """
        if not self.enabled or not self._client:
            return False

        try:
            context_hash = self._hash_context(context_data)
            cache_key = self._generate_cache_key(
                model_id, prompt, context_hash, temperature, max_tokens
            )

            # 序列化响应数据
            cached_value = json.dumps(response_data, ensure_ascii=False)

            # 存入 Redis
            await self._client.setex(
                cache_key,
                ttl or self.default_ttl,
                cached_value
            )

            record_cache_operation("set", "success")
            logger.debug("cache_set", model_id=model_id, cache_key=cache_key)
            return True

        except Exception as e:
            logger.error("cache_set_failed", error=str(e))
            record_cache_operation("set", "error")
            return False

    async def delete(self, cache_key: str) -> bool:
        """
        删除缓存项

        Args:
            cache_key: 缓存键

        Returns:
            是否成功
        """
        if not self.enabled or not self._client:
            return False

        try:
            await self._client.delete(cache_key)
            record_cache_operation("delete", "success")
            return True
        except Exception as e:
            logger.error("cache_delete_failed", error=str(e))
            record_cache_operation("delete", "error")
            return False

    async def clear_model_cache(self, model_id: str) -> int:
        """
        清除指定模型的所有缓存

        Args:
            model_id: 模型 ID

        Returns:
            删除的缓存数量
        """
        if not self.enabled or not self._client:
            return 0

        try:
            pattern = f"wishub_mcp:{model_id}:*"
            keys = []

            # 使用 SCAN 遍历键（避免阻塞）
            async for key in self._client.scan_iter(match=pattern, count=100):
                keys.append(key)

            if keys:
                await self._client.delete(*keys)
                logger.info("cache_cleared", model_id=model_id, count=len(keys))

            return len(keys)
        except Exception as e:
            logger.error("cache_clear_failed", error=str(e))
            return 0

    async def get_stats(self) -> dict:
        """
        获取缓存统计信息

        Returns:
            统计信息字典
        """
        if not self.enabled or not self._client:
            return {"enabled": False}

        try:
            info = await self._client.info("stats")
            return {
                "enabled": True,
                "keyspace_hits": info.get("keyspace_hits", 0),
                "keyspace_misses": info.get("keyspace_misses", 0),
                "total_keys": await self._client.dbsize()
            }
        except Exception as e:
            logger.error("cache_stats_failed", error=str(e))
            return {"enabled": True, "error": str(e)}


# 全局缓存管理器实例
_cache_manager: Optional[CacheManager] = None


def get_cache_manager() -> CacheManager:
    """获取全局缓存管理器实例"""
    global _cache_manager
    return _cache_manager


async def init_cache(redis_url: str = None, enabled: bool = True) -> None:
    """
    初始化全局缓存管理器

    Args:
        redis_url: Redis 连接 URL
        enabled: 是否启用缓存
    """
    global _cache_manager

    from wishub_mcp.config import settings

    _cache_manager = CacheManager(
        redis_url=redis_url or f"redis://{settings.REDIS_HOST}:{settings.REDIS_PORT}/{settings.REDIS_DB}",
        enabled=enabled
    )

    await _cache_manager.connect()


async def close_cache() -> None:
    """关闭全局缓存管理器"""
    global _cache_manager
    if _cache_manager:
        await _cache_manager.disconnect()

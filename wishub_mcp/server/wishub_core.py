"""
WisHub Core Integration
"""
import logging
from typing import Dict, Any, Optional
import httpx

from wishub_mcp.config import settings

logger = logging.getLogger(__name__)


class WisHubCoreClient:
    """WisHub 核心客户端"""

    def __init__(
        self,
        base_url: Optional[str] = None,
        timeout: int = 30
    ):
        """
        初始化 WisHub 核心客户端

        Args:
            base_url: WisHub 核心基础 URL
            timeout: 超时时间（秒）
        """
        self.base_url = base_url or settings.WISHUB_CORE_URL
        self.timeout = timeout
        self.client = httpx.AsyncClient(timeout=timeout)

    async def get_wisunit(
        self,
        wisunit_id: str,
        include_content: bool = True
    ) -> Dict[str, Any]:
        """
        获取 WisUnit

        Args:
            wisunit_id: WisUnit ID
            include_content: 是否包含内容

        Returns:
            WisUnit 数据
        """
        try:
            url = f"{self.base_url}/api/v1/wisunit/{wisunit_id}"
            params = {"include_content": include_content}

            response = await self.client.get(url, params=params)
            response.raise_for_status()

            return response.json()
        except httpx.HTTPError as e:
            logger.error(f"获取 WisUnit 失败: {e}")
            raise RuntimeError(f"获取 WisUnit 失败: {str(e)}")

    async def search_wisunits(
        self,
        query: str,
        limit: int = 10,
        offset: int = 0
    ) -> Dict[str, Any]:
        """
        搜索 WisUnits

        Args:
            query: 搜索查询
            limit: 返回数量限制
            offset: 偏移量

        Returns:
            WisUnits 列表
        """
        try:
            url = f"{self.base_url}/api/v1/wisunit/search"
            params = {
                "q": query,
                "limit": limit,
                "offset": offset
            }

            response = await self.client.get(url, params=params)
            response.raise_for_status()

            return response.json()
        except httpx.HTTPError as e:
            logger.error(f"搜索 WisUnits 失败: {e}")
            raise RuntimeError(f"搜索 WisUnits 失败: {str(e)}")

    async def get_knowledge_context(
        self,
        context_id: str,
        context_type: str = "wisunit"
    ) -> Dict[str, Any]:
        """
        获取知识上下文

        Args:
            context_id: 上下文 ID
            context_type: 上下文类型 (wisunit, knowledge_graph, wisdom_core)

        Returns:
            上下文数据
        """
        try:
            if context_type == "wisunit":
                return await self.get_wisunit(context_id)
            elif context_type == "knowledge_graph":
                return await self._get_knowledge_graph_context(context_id)
            elif context_type == "wisdom_core":
                return await self._get_wisdom_core_context(context_id)
            else:
                raise ValueError(f"不支持的上下文类型: {context_type}")
        except Exception as e:
            logger.error(f"获取知识上下文失败: {e}")
            raise

    async def _get_knowledge_graph_context(
        self,
        context_id: str
    ) -> Dict[str, Any]:
        """获取知识图谱上下文"""
        try:
            url = f"{self.base_url}/api/v1/knowledge_graph/node/{context_id}"
            response = await self.client.get(url)
            response.raise_for_status()

            return response.json()
        except httpx.HTTPError as e:
            logger.error(f"获取知识图谱上下文失败: {e}")
            raise RuntimeError(f"获取知识图谱上下文失败: {str(e)}")

    async def _get_wisdom_core_context(
        self,
        context_id: str
    ) -> Dict[str, Any]:
        """获取智慧核心上下文"""
        try:
            url = f"{self.base_url}/api/v1/wisdom_core/{context_id}"
            response = await self.client.get(url)
            response.raise_for_status()

            return response.json()
        except httpx.HTTPError as e:
            logger.error(f"获取智慧核心上下文失败: {e}")
            raise RuntimeError(f"获取智慧核心上下文失败: {str(e)}")

    async def health_check(self) -> bool:
        """健康检查"""
        try:
            url = f"{self.base_url}/health"
            response = await self.client.get(url)
            return response.status_code == 200
        except Exception:
            return False

    async def close(self):
        """关闭客户端"""
        await self.client.aclose()

    async def __aenter__(self):
        """异步上下文管理器入口"""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """异步上下文管理器出口"""
        await self.close()

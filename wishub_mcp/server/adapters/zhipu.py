"""
ZhipuAI GLM-4 Adapter (支持自定义 Base URL)
"""
from typing import Dict, Any, Optional
from zhipuai import ZhipuAI

from .base import BaseAIAdapter


class ZhipuAdapter(BaseAIAdapter):
    """智谱 GLM-4 适配器"""

    def __init__(
        self,
        model_id: str,
        api_key: str,
        base_url: Optional[str] = None
    ):
        """
        初始化智谱适配器

        Args:
            model_id: 模型 ID
            api_key: API 密钥
            base_url: 自定义 API 端点（默认使用智谱标准端点）
                     推荐使用 coding 端点: https://open.bigmodel.cn/api/coding/paas/v4
        """
        super().__init__(model_id, api_key)

        # 使用自定义 base_url 或默认值
        if base_url is None:
            # 默认使用智谱的 coding API 端点（与 clawd 配置一致）
            base_url = "https://open.bigmodel.cn/api/coding/paas/v4"

        self.client = ZhipuAI(api_key=api_key, base_url=base_url)
        self.base_url = base_url

    async def generate(
        self,
        prompt: str,
        context: Dict[str, Any],
        max_tokens: int,
        temperature: float
    ) -> str:
        """生成 AI 响应"""
        # 构建上下文提示
        context_str = self._build_context_prompt(context)

        # 构建完整提示
        full_prompt = f"{context_str}\n\n用户问题:\n{prompt}"

        try:
            response = self.client.chat.completions.create(
                model=self.model_id,
                messages=[
                    {
                        "role": "system",
                        "content": "你是一个有帮助的助手，基于提供的上下文信息回答问题。"
                    },
                    {
                        "role": "user",
                        "content": full_prompt
                    }
                ],
                max_tokens=max_tokens,
                temperature=temperature
            )

            return response.choices[0].message.content
        except Exception as e:
            raise RuntimeError(f"智谱 AI API 调用失败: {str(e)}")

    async def count_tokens(self, text: str) -> int:
        """计算 Token 数量 (智谱 API 提供了 token 计算方法)"""
        try:
            # 使用智谱的 token 计算方法
            response = self.client.tokens.count(
                model=self.model_id,
                prompt=text
            )
            return response.total_tokens
        except Exception:
            # 如果 API 失败，使用简单估算（中文 1.5 字符/token，英文 4 字符/token）
            char_count = len(text)
            chinese_chars = sum(1 for c in text if '\u4e00' <= c <= '\u9fff')
            english_chars = char_count - chinese_chars
            return int(chinese_chars * 1.5 + english_chars / 4)

    def validate_config(self, config: Dict[str, Any]) -> bool:
        """验证配置"""
        required_keys = ["api_key"]
        return all(key in config for key in required_keys)

    def _build_context_prompt(self, context: Dict[str, Any]) -> str:
        """构建上下文提示"""
        if not context:
            return "没有提供上下文信息。"

        prompt_parts = ["以下是相关的上下文信息："]

        for key, value in context.items():
            if isinstance(value, (dict, list)):
                import json
                value_str = json.dumps(value, ensure_ascii=False, indent=2)
            else:
                value_str = str(value)

            prompt_parts.append(f"\n{key}:\n{value_str}")

        return "\n".join(prompt_parts)

"""
OpenAI GPT-4 Adapter
"""
from typing import Dict, Any
from openai import AsyncOpenAI
import tiktoken

from .base import BaseAIAdapter


class OpenAIAdapter(BaseAIAdapter):
    """OpenAI GPT-4 适配器"""

    def __init__(self, model_id: str, api_key: str):
        """初始化 OpenAI 适配器"""
        super().__init__(model_id, api_key)
        self.client = AsyncOpenAI(api_key=api_key)

        # 获取编码器（用于计算 token 数）
        try:
            self.encoding = tiktoken.encoding_for_model(model_id)
        except KeyError:
            # 如果模型不支持，使用 cl100k_base (GPT-4 的编码器)
            self.encoding = tiktoken.get_encoding("cl100k_base")

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
            response = await self.client.chat.completions.create(
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
            raise RuntimeError(f"OpenAI API 调用失败: {str(e)}")

    async def count_tokens(self, text: str) -> int:
        """计算 Token 数量"""
        return len(self.encoding.encode(text))

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

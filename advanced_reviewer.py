"""
该模块负责在「高级模式」下，对翻译结果进行点评并提出可优化之处，然后基于这些改进点进行二次润色。
"""
from typing import Optional, Dict, Tuple
from llm_client import ZetaClient
import json

class AdvancedReviewer:
    def __init__(self, api_key: Optional[str] = None, api_base: Optional[str] = None):
        """
        初始化高级翻译审校器。
        
        参数：
            api_key: LLM服务API密钥
            api_base: LLM服务API基础URL
        """
        self.llm_client = ZetaClient(api_key=api_key, api_base=api_base)

    def comment_on_translation(self, source_text: str, translated_text: str) -> str:
        """
        让模型针对原文和译文，找出可优化之处（不需要给出评分），只需指出问题与改进建议。

        参数：
            source_text: 原文
            translated_text: 译文

        返回：
            模型给出的改进建议文本
        """
        prompt = f"""你是一位专业的译文审校员。请仔细阅读以下原文与其译文，找出可以改进的地方。

原文：
---
{source_text}
---

译文：
---
{translated_text}
---

请列出所有可以改进的地方，包括但不限于：
1. 专业术语的准确性和一致性
2. 语序的自然度和流畅性
3. 表达的地道性和优雅度
4. 文本的整体连贯性

对于每个发现的问题：
- 明确指出问题所在
- 解释为什么需要改进
- 给出具体的改进建议

请直接列出你的审校意见，不需要任何特定格式。重点是让意见清晰、具体、可操作。
"""
        response_text = self.llm_client.generate_text(
            prompt=prompt,
            stream=False,
            model="claude-3-5-sonnet-20241022"
        )
        
        return response_text.strip()

    def polish_with_comments(self, translated_text: str, comments: str) -> str:
        """
        根据审校意见，对译文进行润色/改进。

        参数：
            translated_text: 初步译文
            comments: 审校意见

        返回：
            润色后的译文
        """
        prompt = f"""作为一位专业的中文编辑，请根据以下审校意见，对译文进行修改与润色。

当前译文：
---
{translated_text}
---

审校意见：
---
{comments}
---

请根据上述审校意见优化译文。要求：
1. 保持原有的Markdown格式和结构
2. 确保专业术语的准确性和一致性
3. 使表达更加自然、地道
4. 提升文本的整体连贯性和可读性

请直接输出优化后的译文，不要包含任何解释或说明。
"""
        response_text = self.llm_client.generate_text(
            prompt=prompt,
            stream=False,
            model="claude-3-5-sonnet-20241022"
        )
        
        return response_text.strip()

    def review_and_polish(self, source_text: str, translated_text: str) -> Tuple[str, str]:
        """
        整合「点评可优化之处 + 基于改进意见润色」两步，供外部一次性调用。

        参数：
            source_text: 原文
            translated_text: 初步译文

        返回：
            (最终润色完成的译文, 审校意见)
        """
        # 1. 找出可优化之处
        comments = self.comment_on_translation(source_text, translated_text)
        
        # 2. 根据改进点对译文进行润色
        final_text = self.polish_with_comments(translated_text, comments)
        
        return final_text, comments 
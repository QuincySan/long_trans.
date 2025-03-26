"""
该模块负责在「高级模式」下，对翻译结果进行点评并提出可优化之处，然后基于这些改进点进行二次润色。
"""
from typing import Optional, Dict, Tuple, Generator, Iterator, Union
from llm_client import ZetaClient
import json

class AdvancedReviewer:
    def __init__(self, api_key: Optional[str] = None, api_base: Optional[str] = None,
                 review_model: str = "gemini-2.0-pro-exp-02-05",
                 polish_model: str = "gemini-2.0-pro-exp-02-05"):
        """
        初始化高级翻译审校器。
        
        参数：
            api_key: LLM服务API密钥
            api_base: LLM服务API基础URL
            review_model: 用于审校评论的模型名称
            polish_model: 用于润色的模型名称
        """
        self.llm_client = ZetaClient(api_key=api_key, api_base=api_base)
        self.latest_comments = None  # 存储最近一次的审校意见
        self.latest_polished_text = None  # 存储最近一次的润色结果
        self.review_model = review_model
        self.polish_model = polish_model

    def comment_on_translation(self, source_text: str, translated_text: str) -> str:
        """
        让模型针对原文和译文，找出可优化之处（不需要给出评分），只需指出问题与改进建议。

        参数：
            source_text: 原文
            translated_text: 译文

        返回：
            改进建议文本
        """
        system_prompt = """你是一位20年丰富经验专业的审校专家，精通中文和俄语，对专业术语、行业用语和文体风格都有深入研究。
你的任务是仔细审查重写内容质量，找出所有可以改进的地方，并提供专业、具体的改进建议。"""

        user_prompt = f"""请仔细阅读以下原文与其重写内容，找出可以改进的地方。

原文：
---
{source_text}
---

重写内容：
---
{translated_text}
---

请列出所有可以改进的地方，包括但不限于：
1. 专业术语的准确性和一致性
2. 语序的俄语自然度和流畅性
3. 俄语表达的地道性和优雅度
4. 文本的整体连贯性
5. markdown格式的保持

对于每个发现的问题：
- 明确指出问题所在
- 解释为什么需要改进
- 给出具体的改进建议"""

        response = self.llm_client.generate_text(
            prompt=user_prompt,
            model=self.review_model,
            system_prompt=system_prompt
        )
        
        return response.strip()

    def polish_with_comments(self, translated_text: str, comments: str) -> str:
        """
        根据审校意见，对译文进行润色/改进。

        参数：
            translated_text: 初步译文
            comments: 审校意见

        返回：
            润色后的译文
        """
        system_prompt = """你是一位有着20年丰富经验专业的俄语编辑，擅长根据审校意见优化和润色重写内容。
你的任务是在保持原意的基础上，保持原有的Markdown格式和结构，让重写内容更加准确、流畅、符合俄语语序。
注意：直接输出优化后的内容，不要添加额外的markdown代码块标记，不要输出任何解释或说明。"""

        user_prompt = f"""请根据以下审校意见，对重写内容进行修改与润色。

当前重写内容：
---
{translated_text}
---

审校意见：
---
{comments}
---

请根据上述审校意见优化重写内容。要求：
1. 保持原有的Markdown格式和结构
2. 确保专业术语的准确性和一致性
3. 使表达更加自然、地道
4. 提升文本的整体连贯性和可读性
5. 直接输出优化后的内容，不要添加额外的markdown代码块标记，不要输出任何解释或说明"""

        response = self.llm_client.generate_text(
            prompt=user_prompt,
            model=self.polish_model,
            system_prompt=system_prompt
        )
        
        return response.strip()

    def comment_and_polish(self, source_text: str, translated_text: str) -> Tuple[str, str]:
        """
        整合「点评可优化之处 + 基于改进意见润色」两步，供外部一次性调用。

        参数：
            source_text: 原文
            translated_text: 初步译文

        返回：
            元组 (最终润色完成的译文, 审校意见)
        """
        print("\n正在分析译文，寻找可优化之处...")
        comments = self.comment_on_translation(source_text, translated_text)
        print("\n审校意见：")
        print(comments)
        
        print("\n开始根据审校意见进行润色...")
        final_text = self.polish_with_comments(translated_text, comments)
        print("\n润色完成！")
        
        self.latest_comments = comments
        self.latest_polished_text = final_text
        return final_text, comments

    def get_latest_results(self) -> Tuple[Optional[str], Optional[str]]:
        """
        获取最近一次审校和润色的结果。

        返回：
            元组 (润色后的文本, 审校意见)，如果尚未执行过审校和润色，则相应位置为None
        """
        return self.latest_polished_text, self.latest_comments 
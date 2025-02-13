"""
This module handles the translation of text using LLM (Language Model).
"""
import os
from typing import List, Optional
from openai import OpenAI
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class Translator:
    def __init__(self, api_key: Optional[str] = None, api_base: Optional[str] = None):
        """
        Initialize the translator with API credentials.
        
        Args:
            api_key: Optional API key. If not provided, will try to get from environment variable.
            api_base: Optional API base URL. If not provided, will try to get from environment variable.
        """
        self.api_key = api_key or os.getenv("FIREWORKS_API_KEY")
        self.api_base = api_base or os.getenv("FIREWORKS_API_BASE", "https://api.fireworks.ai/inference/v1")
        
        if not self.api_key:
            raise ValueError("API key must be provided either directly or through environment variable FIREWORKS_API_KEY")
        
        self.client = OpenAI(api_key=self.api_key, base_url=self.api_base)

    def translate_text(self, text: str, stream: bool = True) -> str:
        """
        Translate the given text while preserving Markdown formatting.
        
        Args:
            text: The text to translate (in Markdown format)
            stream: Whether to use streaming mode
            
        Returns:
            The translated text with preserved Markdown formatting
        """
        prompt = (
            "以下内容是一段 Markdown 文本，请将其翻译成中文。注意事项：\n"
            "1. 保持原有的 Markdown 结构、格式和标记\n"
            "2. 代码块内的代码和注释要分开处理：代码保持不变，只翻译注释\n"
            "3. 保持原有的标题层级\n"
            "4. 保留原有的列表格式和缩进\n"
            "5. 链接和图片的URL保持不变，只翻译描述文本\n\n"
            "需要翻译的文本：\n\n" + text
        )

        completion = self.client.chat.completions.create(
            model="accounts/fireworks/models/deepseek-r1",
            stream=stream,
            temperature=0.6,
            messages=[
                {"role": "system", "content": ""},
                {"role": "user", "content": prompt}
            ]
        )

        if stream:
            translated_text = []
            for chunk in completion:
                if chunk.choices[0].delta.content:
                    translated_text.append(chunk.choices[0].delta.content)
            return "".join(translated_text)
        else:
            return completion.choices[0].message.content

    def translate_batch(self, texts: List[str]) -> List[str]:
        """
        Translate a batch of text segments.
        
        Args:
            texts: List of text segments to translate
            
        Returns:
            List of translated text segments
        """
        return [self.translate_text(text) for text in texts] 
"""
该模块负责使用大语言模型(LLM)进行文本翻译。
"""
import os
from typing import List, Optional
from openai import OpenAI
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

class Translator:
    def __init__(self, api_key: Optional[str] = None, api_base: Optional[str] = None):
        """
        使用API凭证初始化翻译器。
        
        参数：
            api_key: 可选的API密钥。如果未提供，将尝试从环境变量获取。
            api_base: 可选的API基础URL。如果未提供，将尝试从环境变量获取。
        """
        self.api_key = api_key or os.getenv("FIREWORKS_API_KEY")
        self.api_base = api_base or os.getenv("FIREWORKS_API_BASE", "https://api.fireworks.ai/inference/v1")
        
        if not self.api_key:
            raise ValueError("必须直接提供API密钥或通过环境变量FIREWORKS_API_KEY提供")
        
        self.client = OpenAI(api_key=self.api_key, base_url=self.api_base)

    def translate_text(self, text: str, stream: bool = True) -> str:
        """
        翻译给定的文本，同时保持Markdown格式。
        
        参数：
            text: 要翻译的文本（Markdown格式）
            stream: 是否使用流式模式
            
        返回：
            保持Markdown格式的翻译后文本
        """
        print("\n开始翻译新的文本块...")
        print("原文:\n", text[:100], "..." if len(text) > 100 else "")
        
        prompt = (
            "以下内容是一段 Markdown 文本，请将其翻译成中文。\n 要求：\n"
            "1. 保持原有的 Markdown 结构、格式和标记\n"
            "2. 代码块内的代码和注释要分开处理：代码保持不变，只翻译注释\n"
            "3. 保持原有的标题层级\n"
            "4. 保留原有的列表格式和缩进\n"
            "5. 链接和图片的URL保持不变，只翻译描述文本\n"
            "需要翻译的文本：\n\n" + f"{text}"
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
            current_think = []
            in_think_tag = False
            
            print("\n翻译进行中...")
            for chunk in completion:
                if chunk.choices[0].delta.content:
                    content = chunk.choices[0].delta.content
                    
                    # 处理思考标签
                    if "<think>" in content:
                        in_think_tag = True
                        content = content.replace("<think>", "")
                        print("\n\033[33m思考过程：", end="")
                    if "</think>" in content:
                        in_think_tag = False
                        content = content.replace("</think>", "")
                        print("\033[0m\n\n翻译结果：")
                    
                    if in_think_tag:
                        print(content, end="", flush=True)
                        current_think.append(content)
                    else:
                        if content and not content.isspace():
                            translated_text.append(content)
                            print(content, end="", flush=True)
            
            final_text = "".join(translated_text)
            print("\n\n翻译完成！")
            return final_text
        else:
            return completion.choices[0].message.content

    def translate_batch(self, texts: List[str]) -> List[str]:
        """
        批量翻译文本段落。
        
        参数：
            texts: 要翻译的文本段落列表
            
        返回：
            翻译后的文本段落列表
        """
        total = len(texts)
        results = []
        
        for i, text in enumerate(texts, 1):
            print(f"\n=== 正在翻译第 {i}/{total} 段 ===")
            result = self.translate_text(text)
            results.append(result)
            print(f"=== 第 {i}/{total} 段翻译完成 ===\n")
            
        return results 
"""
该模块负责使用大语言模型(LLM)进行文本翻译。
"""
from typing import List, Optional, Dict, Any, Tuple
from llm_client import ZetaClient
from utils.translation_logger import TranslationLogger

class Translator:
    def __init__(self, api_key: Optional[str] = None, api_base: Optional[str] = None, default_model: str = "deepseek-v3"):
        """
        使用API凭证初始化翻译器。
        
        参数：
            api_key: 可选的API密钥。如果未提供，将尝试从环境变量获取。
            api_base: 可选的API基础URL。如果未提供，将尝试从环境变量获取。
            default_model: 默认使用的模型名称。
        """
        self.llm_client = ZetaClient(api_key=api_key, api_base=api_base)
        self.logger = TranslationLogger()
        self.default_model = default_model

    def _build_translation_prompts(self, text: str, summary: Optional[str] = None) -> Tuple[str, str]:
        """
        构建翻译的system prompt和user prompt。
        
        参数：
            text: 要翻译的文本
            summary: 可选的上下文摘要
            
        返回：
            (system_prompt, user_prompt) 元组
        """
        system_prompt = (
            """你是一个专业的翻译助手。你的任务是将文本准确翻译成简体中文，同时：
    1. 保持原有的Markdown格式和结构
    2. 仅翻译文字内容，保留代码块、链接URL等不需要翻译的部分
    3. 根据上下文准确理解并翻译专业术语，在后面加括号展示专业术语英文原文
    4. 直接给出翻译内容，不要输出任何解释
    5. 完整翻译内容，不要节约篇幅"""
        )
        
        if summary:
            user_prompt = (
                f"""【背景摘要】:
{summary}

【待翻译文本】:
{text}"""

            )
        else:
            user_prompt = text
        
        return system_prompt, user_prompt

    def _process_stream_response(self, response_iterator, print_progress: bool = True) -> str:
        """
        处理流式响应。
        
        参数：
            response_iterator: 响应迭代器
            print_progress: 是否打印进度
            
        返回：
            合并后的文本
        """
        translated_text = []
        current_think = []
        in_think_tag = False
        
        if print_progress:
            print("\n翻译进行中...")
            
        for content in response_iterator:
            # 处理思考标签
            if "<think>" in content:
                in_think_tag = True
                content = content.replace("<think>", "")
                if print_progress:
                    print("\n\033[33m思考过程：", end="")
            if "</think>" in content:
                in_think_tag = False
                content = content.replace("</think>", "")
                if print_progress:
                    print("\033[0m\n\n翻译结果：")
            
            if in_think_tag:
                if print_progress:
                    print(content, end="", flush=True)
                current_think.append(content)
            else:
                if content and not content.isspace():
                    translated_text.append(content)
                    if print_progress:
                        print(content, end="", flush=True)
        
        return "".join(translated_text)

    def _get_response_format(self, model: str) -> Optional[Dict[str, Any]]:
        """
        根据模型获取响应格式。
        
        参数：
            model: 模型名称
            
        返回：
            响应格式配置或None
        """
        return {
            "type": "grammar",
            "grammar": 'root ::= "<think>\n" [^\n] (.)*'
        } if "deepseek-r1" in model.lower() else None

    def translate_text(
        self,
        text: str,
        stream: bool = True,
        model: Optional[str] = None,
        summary: Optional[str] = None
    ) -> str:
        """
        翻译给定的文本，同时保持Markdown格式。
        
        参数：
            text: 要翻译的文本（Markdown格式）
            stream: 是否使用流式模式
            model: 使用的模型名称，如果未提供则使用默认模型
            summary: 可选的上下文摘要
            
        返回：
            保持Markdown格式的翻译后文本
        """
        model = model or self.default_model
        print("\n开始翻译新的文本块...")
        print("原文:\n", text[:100], "..." if len(text) > 100 else "")
        
        system_prompt, user_prompt = self._build_translation_prompts(text, summary)
        response_format = self._get_response_format(model)

        if stream:
            response_iterator = self.llm_client.generate_text(
                prompt=user_prompt,
                stream=True,
                model=model,
                system_prompt=system_prompt,
                response_format=response_format
            )
            final_text = self._process_stream_response(response_iterator)
            print("\n\n翻译完成！")
            return final_text
        else:
            return self.llm_client.generate_text(
                prompt=user_prompt,
                stream=False,
                model=model,
                system_prompt=system_prompt,
                response_format=response_format
            )

    def translate_batch(
        self,
        texts: List[str],
        model: Optional[str] = None,
        summary: Optional[str] = None
    ) -> List[str]:
        """
        批量翻译文本段落。使用 self.translate_text。
        
        参数：
            texts: 要翻译的文本段落列表
            model: 使用的模型名称，如果未提供则使用默认模型
            summary: 可选的上下文摘要
            
        返回：
            翻译后的文本段落列表
        """
        model = model or self.default_model
        total = len(texts)
        results = []
        
        for i, text in enumerate(texts, 1):
            print(f"\n=== 正在翻译第 {i}/{total} 段 ===")
            result = self.translate_text(text, model=model, summary=summary)
            
            # 记录翻译结果
            self.logger.log_segment(
                original_text=text,
                translated_text=result,
                segment_index=i,
                total_segments=total,
                metadata={
                    "model": model,
                    "stream": True,
                    "summary": summary
                }
            )
            
            results.append(result)
            print(f"=== 第 {i}/{total} 段翻译完成 ===\n")
            
        return results

    # 移除冗余方法，使用 translate_text 和 translate_batch 的 summary 参数替代
    translate_with_summary = None
    translate_batch_with_summary = None 
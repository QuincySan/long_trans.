"""
该模块负责使用大语言模型(LLM)进行文本翻译。
"""
from typing import List, Optional
from llm_client import ZetaClient
from utils.translation_logger import TranslationLogger

class Translator:
    def __init__(self, api_key: Optional[str] = None, api_base: Optional[str] = None):
        """
        使用API凭证初始化翻译器。
        
        参数：
            api_key: 可选的API密钥。如果未提供，将尝试从环境变量获取。
            api_base: 可选的API基础URL。如果未提供，将尝试从环境变量获取。
        """
        self.llm_client = ZetaClient(api_key=api_key, api_base=api_base)
        self.logger = TranslationLogger()

    def translate_text(self, text: str, stream: bool = True, model: str = "claude-3-5-sonnet-20241022") -> str:
        """
        翻译给定的文本，同时保持Markdown格式。
        
        参数：
            text: 要翻译的文本（Markdown格式）
            stream: 是否使用流式模式
            model: 使用的模型名称
            
        返回：
            保持Markdown格式的翻译后文本
        """
        print("\n开始翻译新的文本块...")
        print("原文:\n", text[:100], "..." if len(text) > 100 else "")
        
        prompt = (
            f"""
            请尊重原意，保持原有格式不变，用简体中文重写下面的内容：

            需要翻译的文本：{text}
            """
        )

        # 只有在使用 deepseek-r1 模型时，才使用 grammar 格式
        response_format = {
            "type": "grammar",
            "grammar": 'root ::= "<think>\n" [^\n] (.)*'
        } if "deepseek-r1" in model.lower() else None

        if stream:
            translated_text = []
            current_think = []
            in_think_tag = False
            
            print("\n翻译进行中...")
            for content in self.llm_client.generate_text(
                prompt=prompt,
                stream=True,
                model=model,
                response_format=response_format
            ):
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
            return self.llm_client.generate_text(
                prompt=prompt,
                stream=False,
                model=model,
                response_format=response_format
            )

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
            
            # 记录翻译结果
            self.logger.log_segment(
                original_text=text,
                translated_text=result,
                segment_index=i,
                total_segments=total,
                metadata={
                    "model": "claude-3-5-sonnet-20241022",
                    "stream": True
                }
            )
            
            results.append(result)
            print(f"=== 第 {i}/{total} 段翻译完成 ===\n")
            
        return results

    def translate_with_summary(self, text: str, summary: str) -> str:
        """
        使用摘要作为上下文来翻译文本。
        
        参数：
            text: 要翻译的Markdown文本
            summary: 用作上下文的摘要文本
            
        返回：
            翻译后的文本
        """
        prompt = (
            "你是一个专业的翻译助手。请根据以下背景摘要，翻译给定的Markdown文本。\n\n"
            f"【背景摘要】:\n{summary}\n\n"
            "【待翻译文本】:\n"
            f"{text}\n\n"
            "请注意：\n"
            "1. 保持原有的Markdown格式和结构\n"
            "2. 仅翻译文字内容，保留代码块、链接URL等不需要翻译的部分\n"
            "3. 根据上下文准确理解并翻译专业术语\n"
            "4. 输出翻译结果："
        )
        
        # 使用流式输出进行翻译
        translated_text = []
        print("\n开始带摘要上下文的翻译...")
        for content in self.llm_client.generate_text(
            prompt=prompt,
            stream=True,
            model="claude-3-5-sonnet-20241022"
        ):
            if content and not content.isspace():
                translated_text.append(content)
                print(content, end="", flush=True)
        
        final_text = "".join(translated_text)
        # 使用正确的日志方法，并添加元数据
        self.logger.log_segment(
            original_text=text,
            translated_text=final_text,
            segment_index=1,  # 在带摘要的翻译中，每次只处理一个片段
            total_segments=1,
            metadata={
                "model": "claude-3-5-sonnet-20241022",
                "stream": True,
                "summary": summary  # 记录使用的摘要
            }
        )
        print("\n\n翻译完成！")
        return final_text.strip()

    def translate_batch_with_summary(self, chunks: List[str], summary: str) -> List[str]:
        """
        使用相同的摘要上下文批量翻译多个文本块。
        
        参数：
            chunks: 要翻译的Markdown文本块列表
            summary: 用作上下文的摘要文本
            
        返回：
            翻译后的文本块列表
        """
        total = len(chunks)
        translated_chunks = []
        
        for i, chunk in enumerate(chunks, 1):
            print(f"\n=== 正在翻译第 {i}/{total} 段（带摘要上下文）===")
            prompt = (
                "你是一个专业的翻译助手。请根据以下背景摘要，翻译给定的Markdown文本。\n\n"
                f"【背景摘要】:\n{summary}\n\n"
                "【待翻译文本】:\n"
                f"{chunk}\n\n"
                "请注意：\n"
                "1. 保持原有的Markdown格式和结构\n"
                "2. 仅翻译文字内容，保留代码块、链接URL等不需要翻译的部分\n"
                "3. 根据上下文准确理解并翻译专业术语\n"
                "4. 输出翻译结果："
            )
            
            # 使用流式输出进行翻译
            translated_text = []
            print("\n开始带摘要上下文的翻译...")
            for content in self.llm_client.generate_text(
                prompt=prompt,
                stream=True,
                model="claude-3-5-sonnet-20241022"
            ):
                if content and not content.isspace():
                    translated_text.append(content)
                    print(content, end="", flush=True)
            
            final_text = "".join(translated_text)
            # 使用正确的日志方法，并添加元数据
            self.logger.log_segment(
                original_text=chunk,
                translated_text=final_text,
                segment_index=i,
                total_segments=total,
                metadata={
                    "model": "claude-3-5-sonnet-20241022",
                    "stream": True,
                    "summary": summary  # 记录使用的摘要
                }
            )
            
            translated_chunks.append(final_text.strip())
            print(f"\n=== 第 {i}/{total} 段翻译完成 ===\n")
            
        return translated_chunks 
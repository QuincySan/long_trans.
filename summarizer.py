"""
该模块负责生成文本摘要。
"""
from typing import Optional
from llm_client import ZetaClient

class Summarizer:
    def __init__(self, api_key: Optional[str] = None, api_base: Optional[str] = None):
        """
        初始化摘要生成器。
        
        参数：
            api_key: LLM服务的API密钥
            api_base: LLM服务的API基础URL
        """
        self.llm_client = ZetaClient(api_key=api_key, api_base=api_base)

    def summarize(self, text: str) -> str:
        """
        对输入文本生成摘要。
        
        参数：
            text: 要生成摘要的Markdown文本
            
        返回：
            生成的摘要文本
        """
        prompt = (
            "请对以下文本生成一个简要的摘要。"
            "摘要应不超过500字，并使用中文输出：\n\n"
            f"{text}"
        )
        
        # 使用非流式输出，直接获取完整摘要
        summary = self.llm_client.generate_text(
            prompt=prompt,
            stream=False,
            model="claude-3-5-sonnet-20241022"
        )
        return summary.strip() 
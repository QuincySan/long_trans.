"""
该模块提供解析和格式化Markdown文本的工具。
"""
from typing import List, Dict, Any
from markdown_it import MarkdownIt

class MarkdownParser:
    def __init__(self):
        """初始化Markdown解析器。"""
        self.md = MarkdownIt()

    def parse(self, text: str) -> List[Dict[str, Any]]:
        """
        将Markdown文本解析为结构化格式。
        
        参数：
            text: Markdown格式的输入文本
            
        返回：
            包含解析后标记的字典列表
        """
        return self.md.parse(text)

    def render(self, tokens: List[Dict[str, Any]]) -> str:
        """
        将解析后的标记重新渲染为Markdown文本。
        
        参数：
            tokens: 解析后的Markdown标记列表
            
        返回：
            渲染后的Markdown文本
        """
        return self.md.renderer.render(tokens, self.md.options, {})

    def get_headers(self, text: str) -> List[Dict[str, Any]]:
        """
        从Markdown文本中提取所有标题及其层级。
        
        参数：
            text: Markdown格式的输入文本
            
        返回：
            包含标题信息的字典列表
        """
        tokens = self.parse(text)
        headers = []
        
        for token in tokens:
            if token.type == 'heading_open':
                level = int(token.tag[1])  # h1 -> 1, h2 -> 2, 等
                content = tokens[tokens.index(token) + 1].content
                headers.append({
                    'level': level,
                    'content': content,
                    'position': tokens.index(token)
                })
        
        return headers

    def get_code_blocks(self, text: str) -> List[Dict[str, str]]:
        """
        从Markdown文本中提取所有代码块。
        
        参数：
            text: Markdown格式的输入文本
            
        返回：
            包含代码块信息的字典列表
        """
        tokens = self.parse(text)
        code_blocks = []
        
        for token in tokens:
            if token.type == 'fence':
                code_blocks.append({
                    'language': token.info,
                    'content': token.content
                })
        
        return code_blocks 
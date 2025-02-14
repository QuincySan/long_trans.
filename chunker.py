"""
该模块负责将Markdown文本分割成更小的段落。
支持两级分段策略：
1. 大段（约20,000字）用于生成摘要
2. 小段（约5,000字）用于实际翻译
"""
from typing import List, Tuple
import re

class Chunker:
    def __init__(self, large_chunk_size: int = 20000, small_chunk_size: int = 5000):
        """
        使用最大块大小初始化分段器。
        
        参数：
            large_chunk_size: 大块的最大字符数（用于摘要）
            small_chunk_size: 小块的最大字符数（用于翻译）
        """
        self.large_chunk_size = large_chunk_size
        self.small_chunk_size = small_chunk_size

    def split_for_summary(self, text: str) -> List[str]:
        """
        将输入文本分割成大块（约20,000字），用于生成摘要。
        
        参数：
            text: Markdown格式的输入文本
            
        返回：
            大文本块列表
        """
        return self._split_text(text, self.large_chunk_size)

    def split_for_translation(self, text: str) -> List[str]:
        """
        将输入文本分割成小块（约5,000字），用于翻译。
        
        参数：
            text: Markdown格式的输入文本
            
        返回：
            小文本块列表
        """
        return self._split_text(text, self.small_chunk_size)

    def _split_text(self, text: str, max_size: int) -> List[str]:
        """
        将输入文本分割成块，同时保持Markdown结构。
        
        参数：
            text: Markdown格式的输入文本
            max_size: 每个块的最大字符数
            
        返回：
            文本块列表
        """
        # 首先按照标题分割
        sections = re.split(r'(#{1,6}\s[^\n]+\n)', text)
        
        chunks = []
        current_chunk = ""
        
        for section in sections:
            # 如果当前section是标题
            if re.match(r'^#{1,6}\s', section):
                if current_chunk:
                    chunks.append(current_chunk.strip())
                current_chunk = section
            else:
                # 如果添加当前section后超过最大长度，先保存当前chunk
                if len(current_chunk) + len(section) > max_size:
                    if current_chunk:
                        chunks.append(current_chunk.strip())
                    # 如果单个section超过最大长度，需要进一步分割
                    if len(section) > max_size:
                        sub_chunks = self._split_large_section(section, max_size)
                        chunks.extend(sub_chunks)
                        current_chunk = ""
                    else:
                        current_chunk = section
                else:
                    current_chunk += section
        
        # 添加最后一个chunk
        if current_chunk:
            chunks.append(current_chunk.strip())
        
        return chunks

    def _split_large_section(self, section: str, max_size: int) -> List[str]:
        """
        将大段落分割成更小的块，在段落边界处分割。
        
        参数：
            section: 要分割的大段落文本
            max_size: 每个块的最大字符数
            
        返回：
            更小的文本块列表
        """
        paragraphs = re.split(r'\n\n+', section)
        chunks = []
        current_chunk = ""
        
        for para in paragraphs:
            if len(current_chunk) + len(para) + 2 > max_size:
                if current_chunk:
                    chunks.append(current_chunk.strip())
                # 如果单个段落超过最大长度，按句子分割
                if len(para) > max_size:
                    sentences = re.split(r'([.!?。！？]\s+)', para)
                    current_chunk = ""
                    for sentence in sentences:
                        if len(current_chunk) + len(sentence) > max_size:
                            chunks.append(current_chunk.strip())
                            current_chunk = sentence
                        else:
                            current_chunk += sentence
                else:
                    current_chunk = para
            else:
                if current_chunk:
                    current_chunk += "\n\n"
                current_chunk += para
        
        if current_chunk:
            chunks.append(current_chunk.strip())
        
        return chunks 
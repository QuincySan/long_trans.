"""
This module handles the chunking of Markdown text into smaller segments.
"""
from typing import List
import re

class Chunker:
    def __init__(self, max_chunk_size: int = 5000):
        """
        Initialize the chunker with maximum chunk size.
        
        Args:
            max_chunk_size: Maximum number of characters in each chunk
        """
        self.max_chunk_size = max_chunk_size

    def split_text(self, text: str) -> List[str]:
        """
        Split the input text into chunks while preserving Markdown structure.
        
        Args:
            text: Input text in Markdown format
            
        Returns:
            List of text chunks
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
                if len(current_chunk) + len(section) > self.max_chunk_size:
                    if current_chunk:
                        chunks.append(current_chunk.strip())
                    # 如果单个section超过最大长度，需要进一步分割
                    if len(section) > self.max_chunk_size:
                        sub_chunks = self._split_large_section(section)
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

    def _split_large_section(self, section: str) -> List[str]:
        """
        Split a large section into smaller chunks at paragraph boundaries.
        
        Args:
            section: Large text section to split
            
        Returns:
            List of smaller text chunks
        """
        paragraphs = re.split(r'\n\n+', section)
        chunks = []
        current_chunk = ""
        
        for para in paragraphs:
            if len(current_chunk) + len(para) + 2 > self.max_chunk_size:
                if current_chunk:
                    chunks.append(current_chunk.strip())
                # 如果单个段落超过最大长度，按句子分割
                if len(para) > self.max_chunk_size:
                    sentences = re.split(r'([.!?。！？]\s+)', para)
                    current_chunk = ""
                    for sentence in sentences:
                        if len(current_chunk) + len(sentence) > self.max_chunk_size:
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